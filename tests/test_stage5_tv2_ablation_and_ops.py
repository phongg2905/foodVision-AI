"""Stage 5 Verification Suite — Ranker Ablation (A/B/C/D), Observability, PERF-02 & TV1 Cross-Test (`Thẻ #14`).

Covers:
- `AI-04` & `DEF-07`: 4-variant reproducible ablation (`A`, `B`, `C`, `D`) over `N = 120` (`>= 100`) scenarios with strict temporal split.
- `OPS-01`: `GET /api/v1/health` (`ok` / `degraded`), `X-Request-Id` correlation, structured JSON logs, and zero secret/token leakage.
- `OPS-02` & `PERF-02`: Ordered Supabase SQL migrations + idempotent seed + `p95` latency on `520` published recipes (`<= 1000ms` / `<= 500ms`).
- `CrossTest-AI` (`TC-05`, `TC-06`, `TC-43`): Automated cross-test harness for TV1's `POST /api/v1/ai/detect` (skips cleanly until TV1 merges `/ai/detect`).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import settings
from app.core.database import InMemoryCatalogRepository, get_catalog_repo
from app.main import create_app
from app.services.evaluation_ablation import evaluate_all_variants
from backend.scripts.run_ranker_ablation import run_perf02_benchmark


def test_ranker_ablation_4_variants_ai04_def07() -> None:
    metrics_run1 = evaluate_all_variants(seed=20261115, num_scenarios=120, top_k=5)
    metrics_run2 = evaluate_all_variants(seed=20261115, num_scenarios=120, top_k=5)

    # 100% deterministic reproducibility
    assert metrics_run1 == metrics_run2

    by_var = {m.variant: m for m in metrics_run1}
    assert set(by_var.keys()) == {"A", "B", "C", "D"}
    for m in metrics_run1:
        assert m.scenario_count >= 100

    a, b, c, d = by_var["A"], by_var["B"], by_var["C"], by_var["D"]

    # Hard constraint safety gate (`TP 04`): C & D must achieve 0% CVR@5, whereas unguarded A & B violate constraints
    assert a.cvr_at_5 > 0.10
    assert b.cvr_at_5 > 0.10
    assert c.cvr_at_5 == 0.0
    assert d.cvr_at_5 == 0.0

    # Strict monotonic improvement in graded ranking quality nDCG@5: A < B < C < D
    assert a.ndcg_at_5 < b.ndcg_at_5 < c.ndcg_at_5 < d.ndcg_at_5
    assert d.ndcg_at_5 > 0.90

    # Precision@5 progression: A < B < C, and D remains high (>= 0.75)
    assert a.precision_at_5 < b.precision_at_5 < c.precision_at_5
    assert d.precision_at_5 >= 0.75

    # Intra-list diversity via MMR (`TP 09`): C & D improve diversity over standalone Tversky B
    assert c.ild_at_5 > b.ild_at_5
    assert d.ild_at_5 > b.ild_at_5
    assert d.ild_at_5 >= 0.70


def test_observability_health_and_secret_redaction_ops01(caplog: pytest.LogCaptureFixture) -> None:
    repo = InMemoryCatalogRepository()
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    client = TestClient(app)

    # 1. Healthy status (`ok`) + correlation header
    with caplog.at_level(logging.INFO, logger="foodvision.api"):
        r_ok = client.get("/api/v1/health", headers={"X-Request-Id": "stage5-health-001"})
    assert r_ok.status_code == 200
    assert r_ok.json() == {"status": "ok"}
    assert r_ok.headers["X-Request-Id"] == "stage5-health-001"

    # 2. Degraded status when DB health probe fails (`OPS-01`)
    repo.check_health = lambda: False  # type: ignore[method-assign]
    r_deg = client.get("/api/v1/health")
    assert r_deg.status_code == 200
    assert r_deg.json() == {"status": "degraded"}
    repo.check_health = lambda: True  # type: ignore[method-assign]

    # 3. Authenticated request: structured JSON log emitted WITHOUT leaking Bearer token or JWT secret
    caplog.clear()
    secret_bearer = "user:11111111-1111-4111-8111-111111111101"
    with caplog.at_level(logging.INFO, logger="foodvision.api"):
        r_auth = client.get(
            "/api/v1/favorites",
            headers={
                "Authorization": f"Bearer {secret_bearer}",
                "X-Request-Id": "stage5-sec-redaction-002",
            },
        )
    assert r_auth.status_code == 200

    api_logs = [rec.message for rec in caplog.records if rec.name == "foodvision.api"]
    assert len(api_logs) >= 1
    parsed = json.loads(api_logs[-1])
    assert parsed["event"] == "http_request"
    assert parsed["request_id"] == "stage5-sec-redaction-002"
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/api/v1/favorites"
    assert parsed["status_code"] == 200
    assert isinstance(parsed["latency_ms"], (int, float))

    raw_joined = "\n".join(api_logs)
    assert secret_bearer not in raw_joined
    assert "Authorization" not in raw_joined
    if settings.supabase_jwt_secret:
        assert settings.supabase_jwt_secret not in raw_joined


def test_migrations_seed_and_perf02_benchmark_ops02_perf02() -> None:
    # OPS-02: Verify ordered SQL migrations and idempotent seed script exist and contain required invariants
    migrations_dir = REPO_ROOT / "supabase" / "migrations"
    sql_files = sorted(p.name for p in migrations_dir.glob("*.sql"))
    assert len(sql_files) >= 3
    assert sql_files[0].startswith("20261104000001_")
    assert sql_files[1].startswith("20261104000002_")
    assert sql_files[2].startswith("20261115000003_")

    seed_sql = (REPO_ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    assert "ON CONFLICT" in seed_sql

    # PERF-02: 520 published recipes (>= 500 per NFR-02), p95 <= 1000ms (/recommendations) and <= 500ms (/recipes)
    perf = run_perf02_benchmark(num_recipes=520, num_requests=30)
    assert perf["recommendations"]["recipes_pool"] >= 500
    assert perf["recommendations"]["p95_ms"] <= 1000.0
    assert perf["recipes_search"]["p95_ms"] <= 500.0


def test_crosstest_tv1_ai_detect_security_and_contract_tc05_tc06_tc43() -> None:
    """Cross-test harness by TV2 for TV1's `POST /api/v1/ai/detect` (`TC-05`, `TC-06`, `TC-43`)."""
    app = create_app()
    mounted_paths = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }
    if ("POST", "/api/v1/ai/detect") not in mounted_paths:
        pytest.skip(
            "Chờ TV1 merge router `POST /api/v1/ai/detect` để kích hoạt kiểm thử chéo tự động TC-05/TC-06/TC-43."
        )

    client = TestClient(app)

    # TC-05: Unsupported MIME (`text/plain`) -> 415 UNSUPPORTED_IMAGE_TYPE
    r_mime = client.post(
        "/api/v1/ai/detect",
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )
    assert r_mime.status_code == 415
    assert r_mime.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"

    # TC-06: Corrupt image bytes claiming image/jpeg -> 422 INVALID_IMAGE
    r_corrupt = client.post(
        "/api/v1/ai/detect",
        files={"file": ("broken.jpg", b"\xff\xd8\xff\x00corrupt-stream", "image/jpeg")},
    )
    assert r_corrupt.status_code == 422
    assert r_corrupt.json()["code"] == "INVALID_IMAGE"

    # TC-05 / BR-09: Payload > 5 MiB -> 413 IMAGE_TOO_LARGE
    oversized = b"\x00" * (10 * 1024 * 1024 + 1024)
    r_large = client.post(
        "/api/v1/ai/detect",
        files={"file": ("huge.jpg", oversized, "image/jpeg")},
    )
    assert r_large.status_code == 413
    assert r_large.json()["code"] == "IMAGE_TOO_LARGE"
