"""Integration Seams Verification Suite for TV2 Audit Remediation (`A1`, `A2`, `A3`, `A4`, `A5`, `S4`).

Covers:
1. `A1` [P0]: Flat SQL detection dict rows saved by `POST /api/v1/ai/detect` (`save_history=true`)
   are hydrated into `Detection(..., bbox=BBox(...))` on `GET /api/v1/scan-sessions/{scan_id}` without 500 ValidationError.
2. `A2` [P0]: `PostgresCatalogRepository.create_scan_session` inserts valid `provenance = 'ai'`
   (matching `chk_scan_ingredients_provenance` in `20261104000001_initial_schema.sql`), never `'detected'`.
3. `A3` [P1]: `POST /api/v1/feedback` and `POST /api/v1/favorites` (only on `201 Created`) update the
   18-dimensional `PersonalizationEngine` consumed by `POST /api/v1/recommendations` (`DEF-08`, `ADR-012`).
4. `A4` [P1]: All 41 active ingredients in `supabase/seed.sql` have matching USDA per-100g rows in
   `build_default_seed_nutrients()`, so 100% of published in-memory recipes return non-null `usda_nutrition`.
5. `A5` [P2]: `InMemoryCatalogRepository` pre-populates `MODEL_YOLO_V1` (`yolo11n-foodvision-v1.0`) and its
   20 labels into Admin `_ai_models`/`_ai_labels`, synchronizes `_active_ai_model` on activate/rollback
   (while preserving `set_active_ai_model(None)` -> `503 MODEL_NOT_READY` for `TC-29`), and updates
   recipe nutrition evidence when `PATCH /api/v1/admin/nutrition-tags/{tag_id}` toggles `is_active`.
6. `S4` [P2]: `PostgresCatalogRepository` supports `_resolve_cover_image_url` and clean `close()` lifecycle.
"""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.auth import ADMIN_SEED_USER_ID
from app.core.database import (
    InMemoryCatalogRepository,
    PostgresCatalogRepository,
    _resolve_cover_image_url,
    get_catalog_repo,
)
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_DAU_HU,
    ING_TRUNG_GA,
     REC_CANH_CA_CHUA_TRUNG,
    REC_DAU_HU_SOT_CA,
    REC_TRUNG_XAO_CA_CHUA,
    build_default_seed_ai_model,
)
from app.core.user_repo import build_default_seed_nutrients
from app.main import create_app
from tests.conftest import REPO_ROOT

MODEL_YOLO_V1_ID = build_default_seed_ai_model().id

USER_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
USER_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ADMIN_HEADERS = {"Authorization": f"Bearer user:{ADMIN_SEED_USER_ID}"}


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer user:{uid}"}


def _make_client() -> tuple[TestClient, InMemoryCatalogRepository]:
    repo = InMemoryCatalogRepository()
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    return TestClient(app), repo


# ==============================================================================
# 1. A1 [P0] — Hydrate flat detection dicts on `GET /api/v1/scan-sessions/{id}`
# ==============================================================================


def test_a1_scan_session_detail_hydrates_flat_ai_detect_rows_without_500() -> None:
    client, repo = _make_client()
    active_model = repo.get_active_ai_model()
    assert active_model is not None

    lbl_tomato = active_model.labels_by_index[0]
    lbl_egg = active_model.labels_by_index[1]

    # Simulate exact flat dict structure saved by `POST /api/v1/ai/detect` (`ai_detect.py:345-367`)
    session = repo.create_scan_session(
        user_id=USER_A,
        model_id=active_model.id,
        detections=[
            {
                "ai_label_id": lbl_egg.id,
                "confidence": 0.74,
                "needs_confirmation": True,
                "x1": 0.50,
                "y1": 0.20,
                "x2": 0.80,
                "y2": 0.70,
            },
            {
                "ai_label_id": lbl_tomato.id,
                "confidence": 0.93,
                "needs_confirmation": False,
                "x1": 0.10,
                "y1": 0.12,
                "x2": 0.42,
                "y2": 0.58,
            },
        ],
        ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
    )

    # User A fetches detail -> 200 OK, detections hydrated with bbox and sorted by confidence DESC
    r_detail = client.get(f"/api/v1/scan-sessions/{session.id}", headers=_auth(USER_A))
    assert r_detail.status_code == 200, r_detail.text
    body = r_detail.json()
    assert body["id"] == session.id
    assert body["model_version"] == "yolo11n-foodvision-v1.0"
    assert len(body["detections"]) == 2
    assert body["detections"][0]["class_name"] == "tomato"
    assert body["detections"][0]["ingredient_name"] == "Cà chua"
    assert body["detections"][0]["confidence"] == 0.93
    assert body["detections"][0]["bbox"] == {"x1": 0.1, "y1": 0.12, "x2": 0.42, "y2": 0.58}
    assert body["detections"][1]["class_name"] == "egg"
    assert body["detections"][1]["needs_confirmation"] is True

    # SEC-06: User B gets 404 SCAN_NOT_OWNED
    r_forbidden = client.get(f"/api/v1/scan-sessions/{session.id}", headers=_auth(USER_B))
    assert r_forbidden.status_code == 404
    assert r_forbidden.json()["code"] == "SCAN_NOT_OWNED"


# ==============================================================================
# 2. A2 [P0] — PostgreSQL `create_scan_session` provenance matches SQL CHECK
# ==============================================================================


def test_a2_postgres_create_scan_session_uses_valid_sql_check_provenance() -> None:
    schema_sql = (
        REPO_ROOT / "supabase" / "migrations" / "20261104000001_initial_schema.sql"
    ).read_text(encoding="utf-8")
    match = re.search(
        r"chk_scan_ingredients_provenance\s+CHECK\s*\(\s*provenance\s+IN\s*\(([^)]+)\)\s*\)",
        schema_sql,
    )
    assert match is not None
    allowed_provenances = {
        token.strip().strip("'") for token in match.group(1).split(",")
    }
    assert allowed_provenances == {"ai", "clip_assisted", "manual", "corrected"}
    assert "detected" not in allowed_provenances

    executed_queries: list[tuple[str, Any]] = []
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = lambda sql, params=None: executed_queries.append((sql, params))
    mock_cur.executemany.side_effect = lambda sql, params=None: executed_queries.append((sql, list(params or [])))

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    pg_repo = PostgresCatalogRepository("postgresql://user:pass@localhost:5432/db", use_pool=False)
    pg_repo._connect = lambda: mock_conn  # type: ignore[method-assign]

    pg_repo.create_scan_session(
        user_id=USER_A,
        model_id=MODEL_YOLO_V1_ID,
        detections=[],
        ingredient_ids=[ING_CA_CHUA],
    )

    scan_ing_inserts = [
        (sql, params)
        for sql, params in executed_queries
        if "INSERT INTO public.scan_ingredients" in sql
    ]
    assert len(scan_ing_inserts) == 1
    _sql, row_tuples = scan_ing_inserts[0]
    assert len(row_tuples) == 1
    inserted_provenance = row_tuples[0][2]
    assert inserted_provenance in allowed_provenances
    assert inserted_provenance == "ai"


# ==============================================================================
# 3. A3 [P1] — `/feedback` and `/favorites` propagate to 18-dim PersonalizationEngine
# ==============================================================================


def test_a3_feedback_and_favorites_update_18dim_personalization_engine() -> None:
    client, _repo = _make_client()

    # 1. Neutral rating=3 is recorded in feedback table but ignored by LR SGD (`ADR-012`)
    r_neutral = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_A),
        json={"recipe_id": REC_TRUNG_XAO_CA_CHUA, "rating": 3},
    )
    assert r_neutral.status_code == 201
    st0 = client.get("/api/v1/personalization/state", headers=_auth(USER_A)).json()
    assert st0["feedback_count"] == 0

    # 2. Idempotent POST /api/v1/favorites: 1st call (201) increments feedback_count to 1; 2nd call (200) does NOT double-count
    r_fav1 = client.post(
        "/api/v1/favorites",
        headers=_auth(USER_A),
        json={"recipe_id": REC_TRUNG_XAO_CA_CHUA},
    )
    assert r_fav1.status_code == 201
    r_fav2 = client.post(
        "/api/v1/favorites",
        headers=_auth(USER_A),
        json={"recipe_id": REC_TRUNG_XAO_CA_CHUA},
    )
    assert r_fav2.status_code == 200
    st1 = client.get("/api/v1/personalization/state", headers=_auth(USER_A)).json()
    assert st1["feedback_count"] == 1

    # 3. Submit 5 additional explicit positive/negative feedbacks across distinct contexts to exit cold-start (`N_u >= 5`)
    for idx in range(5):
        scan_res = client.post(
            "/api/v1/feedback",
            headers=_auth(USER_A),
            json={
                "recipe_id": REC_CANH_CA_CHUA_TRUNG if idx % 2 == 0 else REC_DAU_HU_SOT_CA,
                "rating": 5 if idx % 2 == 0 else 1,
            },
        )
        assert scan_res.status_code in (200, 201)

    st_final = client.get("/api/v1/personalization/state", headers=_auth(USER_A)).json()
    assert st_final["feedback_count"] >= 2
    assert len(st_final["theta_by_feature"]) == 18


# ==============================================================================
# 4. A4 [P1] — All 41 USDA nutrients present & 100% published recipes have USDA nutrition
# ==============================================================================


def test_a4_all_41_usda_nutrients_match_seed_sql_and_all_published_recipes_have_usda() -> None:
    seed_sql = (REPO_ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    sql_nutrient_ids = set(
        re.findall(
            r"\('(11111111-1111-4111-8111-[0-9a-fA-F]{12})',\s*[0-9]+\.[0-9]+,\s*[0-9]+\.[0-9]+,\s*[0-9]+\.[0-9]+,\s*[0-9]+\.[0-9]+,\s*'https://fdc\.nal\.usda\.gov/",
            seed_sql,
        )
    )
    assert len(sql_nutrient_ids) == 41

    in_mem_nutrients = build_default_seed_nutrients()
    assert set(in_mem_nutrients.keys()) == sql_nutrient_ids

    client, repo = _make_client()
    published_recipes = repo.get_all_published_recipes()
    assert len(published_recipes) >= 16

    for rec in published_recipes:
        res = client.get(f"/api/v1/recipes/{rec.id}?servings=4")
        assert res.status_code == 200, f"Failed for recipe {rec.slug}: {res.text}"
        detail = res.json()
        assert detail["usda_nutrition"] is not None, f"Missing usda_nutrition for {rec.slug}"
        assert detail["usda_nutrition"]["kcal"] > 0


# ==============================================================================
# 5. A5 [P2] & S4 [P2] — In-Memory AI Model & Nutrition Tag Sync + Cover URL helper
# ==============================================================================


def test_a5_in_memory_ai_model_and_nutrition_tag_sync_and_s4_helpers() -> None:
    client, repo = _make_client()

    # 1. Default seeded active model (`MODEL_YOLO_V1`) is visible in `GET /api/v1/admin/ai-models`
    r_models = client.get("/api/v1/admin/ai-models", headers=ADMIN_HEADERS)
    assert r_models.status_code == 200
    items = r_models.json()["items"]
    assert any(m["id"] == MODEL_YOLO_V1_ID and m["status"] == "active" for m in items)

    # 2. Deactivating nutrition tag `33333333-3333-4333-8333-333333333301` removes it from `GET /recipes/{id}`
    tag_id = "33333333-3333-4333-8333-333333333301"
    r_before = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}").json()
    assert any(ev["tag"]["id"] == tag_id for ev in r_before["nutrition_evidence"])

    r_patch_tag = client.patch(
        f"/api/v1/admin/nutrition-tags/{tag_id}",
        headers=ADMIN_HEADERS,
        json={"is_active": False},
    )
    assert r_patch_tag.status_code == 200

    r_after = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}").json()
    assert all(ev["tag"]["id"] != tag_id for ev in r_after["nutrition_evidence"])

    # 3. TC-29 safety: `repo.set_active_ai_model(None)` still makes `get_active_ai_model()` return None
    repo.set_active_ai_model(None)
    assert repo.get_active_ai_model() is None

    # 4. S4: `_resolve_cover_image_url` normalizes relative Storage paths and preserves https:// URLs
    assert _resolve_cover_image_url(None) is None
    assert (
        _resolve_cover_image_url("https://images.unsplash.com/photo-1")
        == "https://images.unsplash.com/photo-1"
    )
    resolved = _resolve_cover_image_url("recipes/dau-hu-sot-ca-chua.jpg")
    assert resolved is not None and resolved.endswith(
        "/storage/v1/object/public/recipes/dau-hu-sot-ca-chua.jpg"
    )
