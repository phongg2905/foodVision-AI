"""Regression tests for TV1 Security (S1, S2), Config (S3, B3), Seed/Covers (F4), Weights (B2) & Perf."""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.ai.clip_fallback import (  # noqa: E402
    CLIPCosineProvider,
    CallableEmbeddingProvider,
    FallbackResult,
    FallbackStatus,
    KBCandidateIngredient,
)
from app.ai.yolo_detector import (  # noqa: E402
    BoundingBox,
    DetectedIngredientItem,
    DetectorConfig,
    IngredientDetectionResult,
    RawBoxPrediction,
)
from app.api.v1.ai_detect import (  # noqa: E402
    get_clip_service,
    get_detector_factory,
)
from app.core.auth import ADMIN_SEED_USER_ID  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402
from app.core.database import (  # noqa: E402
    InMemoryCatalogRepository,
    get_catalog_repo,
    resolve_cover_image_url,
)
from app.core.seed_fixtures import (  # noqa: E402
    ING_CA_CHUA,
    REC_BAP_NGOT_KHOAI_TAY_DUT_LO_US,
    REC_BONG_CAI_XANH_NAM_BO_TOI,
    REC_BURGER_BO_PHO_MAI_US,
    REC_MI_Y_SOT_CA_CHUA,
    RECIPE_COVER_IMAGE_URLS,
)
from app.intelligence.personalization import RecipeFeatureInput  # noqa: E402
from app.main import create_app  # noqa: E402
from app.schemas.ai import SuggestedIngredient  # noqa: E402
from scripts.yolo_weights_registry import (  # noqa: E402
    DEFAULT_WEIGHTS_PATH,
    LEGACY_WEIGHTS_PATH,
    write_yolo_artifact_manifest,
)

ADMIN_HEADER = {"Authorization": f"Bearer user:{ADMIN_SEED_USER_ID}"}
USER_HEADER = {"Authorization": "Bearer user:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}


def _make_jpeg_bytes(width: int = 128, height: int = 128) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (width, height), color=(210, 60, 40)).save(buf, format="JPEG")
    return buf.getvalue()


# THUẬT TOÁN: Kiểm chứng Khóa Bảo mật `POST /api/v1/personalization/demo-seed` (`S1`, `SEC-01`, `SEC-03`)
# Cơ chế: Kiểm tra ma trận quyền Guest (401) -> User thường (403) -> Admin dev (200) -> Admin prod (403).
# Độ phức tạp: Time O(1), Space O(1).
def test_s1_personalization_demo_seed_rbac_and_production_guard() -> None:
    app = create_app()
    repo = InMemoryCatalogRepository()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    app.dependency_overrides[get_settings] = lambda: Settings(app_env="development")

    client = TestClient(app)

    # 1. Guest without Bearer token -> 401 UNAUTHORIZED
    res_guest = client.post("/api/v1/personalization/demo-seed")
    assert res_guest.status_code == 401
    assert res_guest.json()["code"] == "UNAUTHORIZED"

    # 2. Regular authenticated user -> 403 FORBIDDEN
    res_user = client.post("/api/v1/personalization/demo-seed", headers=USER_HEADER)
    assert res_user.status_code == 403
    assert res_user.json()["code"] == "FORBIDDEN"

    # 3. Admin in development -> 200 OK
    res_admin_dev = client.post("/api/v1/personalization/demo-seed", headers=ADMIN_HEADER)
    assert res_admin_dev.status_code == 200
    payload = res_admin_dev.json()
    assert payload["seeded"] is True
    assert payload["adr012_stale_replay_check"]["applied"] is False

    # 4. Admin in production -> strictly blocked with 403 FORBIDDEN
    app.dependency_overrides[get_settings] = lambda: Settings(app_env="production")
    res_admin_prod = client.post("/api/v1/personalization/demo-seed", headers=ADMIN_HEADER)
    assert res_admin_prod.status_code == 403
    assert res_admin_prod.json()["code"] == "FORBIDDEN"


# THUẬT TOÁN: Kiểm chứng Graceful Degradation cho nhánh phụ CLIP/VLM trong `/api/v1/ai/detect` (`S2`, `PERF-01`)
# Cơ chế: Giả lập `clip_service.suggest` bị treo 1.5s trong khi ngân sách timeout là 0.35s;
#         xác minh `/ai/detect` trả 200 OK đúng SLA và giữ nguyên kết quả YOLO hợp lệ.
# Độ phức tạp: Time O(1), Space O(1).
def test_s2_detect_clip_fallback_timeout_degrades_gracefully_preserving_yolo() -> None:
    app = create_app()
    repo = InMemoryCatalogRepository()

    class _FastUncertainDetector:
        def detect(self, _rgb: np.ndarray) -> IngredientDetectionResult:
            return IngredientDetectionResult(
                model_version="yolo11n-foodvision-v1.0",
                detections=[
                    DetectedIngredientItem(
                        class_id=0,
                        label="tomato",
                        confidence=0.65,
                        calibrated_confidence=0.65,
                        is_calibrated=False,
                        bounding_box=BoundingBox(x1=0.1, y1=0.1, x2=0.5, y2=0.5),
                        model_version="yolo11n-foodvision-v1.0",
                        needs_confirmation=True,
                        confirmation_status="needs_confirmation",
                        ingredient_id=UUID(ING_CA_CHUA),
                        ingredient_name_vi="Cà chua",
                    )
                ],
                suggested_ingredients=[
                    SuggestedIngredient(
                        ingredient_id=UUID(ING_CA_CHUA),
                        name_vi="Cà chua",
                        max_confidence=0.65,
                    )
                ],
                image_width=128,
                image_height=128,
                mime_type="image/jpeg",
                calibration_method="identity",
                unmapped_class_ids=[],
                requires_user_confirmation=True,
            )

    @contextmanager
    def _fake_factory(_model: Any, _cfg: Settings):
        yield _FastUncertainDetector()

    class _SlowClipService:
        def suggest(self, *_args: Any, **_kwargs: Any) -> FallbackResult:
            time.sleep(1.5)
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source="slow-mock",
            )

    app.dependency_overrides[get_catalog_repo] = lambda: repo
    app.dependency_overrides[get_detector_factory] = lambda: _fake_factory
    app.dependency_overrides[get_clip_service] = lambda: _SlowClipService()
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_env="development",
        enable_clip_fallback=True,
        inference_timeout_seconds=0.35,
        max_concurrent_inferences=2,
    )

    with TestClient(app) as client:
        t0 = time.perf_counter()
        res = client.post(
            "/api/v1/ai/detect",
            files={"file": ("tomato.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
        elapsed = time.perf_counter() - t0
    assert res.status_code == 200, res.text
    assert elapsed < 1.0, f"Detect waited too long for timed-out CLIP fallback ({elapsed:.2f}s)"
    body = res.json()
    assert len(body["detections"]) == 1
    assert body["detections"][0]["ingredient_id"] == ING_CA_CHUA
    assert len(body["uncertain_ingredients"]) == 1


# THUẬT TOÁN: Kiểm chứng Bảo mật & Timeout cho `POST /api/v1/ai/vlm-suggest` (`S2`, `SEC-03`, `OPS-03`)
# Cơ chế: Kiểm tra phân quyền Guest (401), User (403), Admin prod (403), và 504 INFERENCE_TIMEOUT khi treo.
# Độ phức tạp: Time O(1), Space O(1).
def test_s2_vlm_suggest_requires_admin_blocks_prod_and_enforces_timeout() -> None:
    app = create_app()
    repo = InMemoryCatalogRepository()

    class _HealthyClipService:
        def suggest(self, *_args: Any, **_kwargs: Any) -> FallbackResult:
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source="mock-vlm",
            )

    class _TimeoutClipService:
        def suggest(self, *_args: Any, **_kwargs: Any) -> FallbackResult:
            time.sleep(1.2)
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source="mock-vlm-slow",
            )

    app.dependency_overrides[get_catalog_repo] = lambda: repo
    app.dependency_overrides[get_clip_service] = lambda: _HealthyClipService()
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_env="development",
        inference_timeout_seconds=0.2,
        max_concurrent_inferences=1,
    )

    client = TestClient(app)
    img_bytes = _make_jpeg_bytes()

    # Guest -> 401
    res_guest = client.post(
        "/api/v1/ai/vlm-suggest",
        files={"file": ("t.jpg", img_bytes, "image/jpeg")},
    )
    assert res_guest.status_code == 401

    # Regular User -> 403
    res_user = client.post(
        "/api/v1/ai/vlm-suggest",
        headers=USER_HEADER,
        files={"file": ("t.jpg", img_bytes, "image/jpeg")},
    )
    assert res_user.status_code == 403

    # Admin in dev -> 200
    res_ok = client.post(
        "/api/v1/ai/vlm-suggest",
        headers=ADMIN_HEADER,
        files={"file": ("t.jpg", img_bytes, "image/jpeg")},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["model_source"] == "mock-vlm"

    # Admin in dev with timeout -> 504 INFERENCE_TIMEOUT
    app.dependency_overrides[get_clip_service] = lambda: _TimeoutClipService()
    with TestClient(app) as timeout_client:
        res_timeout = timeout_client.post(
            "/api/v1/ai/vlm-suggest",
            headers=ADMIN_HEADER,
            files={"file": ("t.jpg", img_bytes, "image/jpeg")},
        )
    assert res_timeout.status_code == 504
    assert res_timeout.json()["code"] == "INFERENCE_TIMEOUT"

    # Admin in production -> 403 FORBIDDEN
    app.dependency_overrides[get_settings] = lambda: Settings(app_env="production")
    res_prod = client.post(
        "/api/v1/ai/vlm-suggest",
        headers=ADMIN_HEADER,
        files={"file": ("t.jpg", img_bytes, "image/jpeg")},
    )
    assert res_prod.status_code == 403
    assert res_prod.json()["code"] == "FORBIDDEN"


# THUẬT TOÁN: Kiểm chứng Cấu hình Mẫu `.env.example` (`S3`) và Quy tắc `.gitignore` (`B3`)
# Cơ chế: Phân tích khóa-giá trị trong `.env.example` và xác nhận khớp đường dẫn trọng số chuẩn.
# Độ phức tạp: Time O(L_file), Space O(L_file).
def test_s3_env_example_and_b3_gitignore_hygiene() -> None:
    env_text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    env_map: dict[str, str] = {}
    for line in env_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, v = stripped.split("=", 1)
        env_map[k.strip()] = v.strip().strip('"').strip("'")

    assert env_map["MODEL_ARTIFACT_PATH"] == "weights/yolo/ingredients_best.pt"
    assert (REPO_ROOT / "backend" / env_map["MODEL_ARTIFACT_PATH"]).resolve() == DEFAULT_WEIGHTS_PATH.resolve()
    assert env_map["ENABLE_CLIP_FALLBACK"] == "false"
    assert env_map["USE_IN_MEMORY_CATALOG"] == "false"
    assert env_map["VITE_API_MOCK_MODE"] == "false"

    gitignore_lines = [
        ln.strip() for ln in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    ]
    assert "/agent/" in gitignore_lines


# THUẬT TOÁN: Kiểm chứng Đồng bộ 20/20 Công thức, Ảnh bìa (`F4`) & Bộ giải URL Supabase Storage
# Cơ chế: Đối chiếu 1:1 giữa API `/api/v1/recipes`, `seed_fixtures.py` và `supabase/seed.sql`.
# Độ phức tạp: Time O(R), Space O(R).
def test_f4_seed_20_recipes_cover_images_and_storage_url_resolver(client: TestClient) -> None:
    res = client.get("/api/v1/recipes?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 20
    items = data["items"]
    assert len(items) == 20

    ids = {it["id"] for it in items}
    for expected_id in (
        REC_MI_Y_SOT_CA_CHUA,
        REC_BONG_CAI_XANH_NAM_BO_TOI,
        REC_BURGER_BO_PHO_MAI_US,
        REC_BAP_NGOT_KHOAI_TAY_DUT_LO_US,
    ):
        assert expected_id in ids

    cuisines = {it["cuisine_code"] for it in items}
    assert cuisines == {"VN", "EU", "US"}
    for it in items:
        url = it["cover_image_url"]
        assert isinstance(url, str) and url.startswith("https://")
        assert url == RECIPE_COVER_IMAGE_URLS[it["id"]]

    # Verify exact 20/20 cover_image_path parity in supabase/seed.sql
    seed_sql = (REPO_ROOT / "supabase" / "seed.sql").read_text(encoding="utf-8")
    sql_urls = dict(
        re.findall(
            r"\(\s*'(22222222-2222-4222-8222-2222222222\d{2})'[^\n]*'(https://images\.unsplash\.com/[^']+)'",
            seed_sql,
        )
    )
    assert sql_urls == RECIPE_COVER_IMAGE_URLS

    # Verify resolve_cover_image_url for None, blank, absolute URL, and relative Storage path
    assert resolve_cover_image_url(None) is None
    assert resolve_cover_image_url("   ") is None
    abs_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
    assert resolve_cover_image_url(abs_url) == abs_url
    rel_resolved = resolve_cover_image_url("recipe-covers/pho-bo.jpg")
    assert rel_resolved is not None
    assert rel_resolved.endswith("/storage/v1/object/public/recipe-covers/pho-bo.jpg")


# THUẬT TOÁN: Kiểm chứng Không nhân bản Trọng số Legacy (`B2`), Bộ nhớ `slots=True` & LRU Đa luồng
# Cơ chế: Chạy `write_yolo_artifact_manifest` trong thư mục tạm, kiểm tra `__slots__` trên DTO,
#         và xác minh `CLIPCosineProvider` loại bỏ đúng 1 mục cũ nhất (LRU) dưới đa luồng.
# Độ phức tạp: Time O(T * C), Space O(max_cache_entries).
def test_b2_no_legacy_weight_mirror_and_tv1_memory_concurrency_optimizations() -> None:
    cache_dir = REPO_ROOT / ".pytest_cache"
    cache_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache_dir) as tmp_dir:
        tmp_path = Path(tmp_dir)
        dummy_pt = tmp_path / "dummy.pt"
        dummy_pt.write_bytes(b"foodvision-weights-test")
        manifest_out = tmp_path / "manifest.json"

        legacy_existed_before = LEGACY_WEIGHTS_PATH.exists()
        manifest = write_yolo_artifact_manifest(
            weights_path=dummy_pt,
            artifact_manifest_path=manifest_out,
            hyperparameters={"model_family": "yolo11n"},
            training_metrics={"val_map50": 0.9},
            training_backend="test",
            sync_repo_seeds=False,
        )
        assert len(manifest["weights_sha256"]) == 64
        assert LEGACY_WEIGHTS_PATH.exists() == legacy_existed_before

    # Verify slots=True memory optimization on TV1 dataclasses
    for cls in (DetectorConfig, RawBoxPrediction, KBCandidateIngredient, RecipeFeatureInput):
        assert hasattr(cls, "__slots__")

    # Verify thread-safe LRU eviction in CLIPCosineProvider (evicts only oldest, not clear-all)
    encode_calls: list[list[str]] = []

    def _encode_texts(texts: Any) -> np.ndarray:
        text_list = list(texts)
        encode_calls.append(text_list)
        return np.array([[float(len(t)), 1.0] for t in text_list], dtype=np.float64)

    provider = CLIPCosineProvider(
        CallableEmbeddingProvider(
            image_encoder=lambda _img: np.array([1.0, 1.0], dtype=np.float64),
            text_encoder=_encode_texts,
            model_source="test-lru",
        ),
        max_cache_entries=2,
    )
    provider._encode_prompts_cached(["a", "bb"])
    provider._encode_prompts_cached(["ccc"])  # evicts only "a", keeps "bb" and "ccc"
    assert list(provider._text_cache.keys()) == ["bb", "ccc"]

    # Concurrent calls must not raise dictionary mutation RuntimeError
    errors: list[Exception] = []

    def _worker(idx: int) -> None:
        try:
            for j in range(10):
                provider._encode_prompts_cached([f"p{idx}_{j}", "bb"])
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert errors == []
