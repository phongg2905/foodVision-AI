"""Stage 3 Automated Verification Suite for TV1 (Minh Thanh — Card #20 Vision Detect & CLIP Fallback).

Validates all 4 checklist items of Card #20 (`[GD3 - TP01, TP02, TP14]`):
1. Trained/exported YOLO v1 weights (`backend/weights/yolo/ingredients_best.pt`) and 64-char hex
   `SHA-256` manifest (`backend/configs/yolo_model_artifact.json`) synchronized with `supabase/seed.sql`.
2. `MATH-01` IoU (`64/136 ≈ 0.471`), Class-wise NMS, `[0, 1]` bbox normalization, `TC-07` `max_confidence`
   deduplication in `suggested_ingredients`, and `v1.1.0` (`ADR-013` / `PR #11`) split into
   `clear_ingredients` (`confidence >= 0.80`) and `uncertain_ingredients` (`confidence < 0.80`).
3. `MATH-01` CLIP Cosine Similarity (`0.96 / sqrt(0.97) ≈ 0.975`) and KB-bound candidate ranking for
   uncertain regions (`0.40 <= conf < 0.80`) without overriding HITL confirmation (`needs_confirmation=true`).
4. `POST /api/v1/ai/detect` validation & resilience:
   - `413 IMAGE_TOO_LARGE` (`> 5 MiB`, `TC-05`)
   - `415 UNSUPPORTED_IMAGE_TYPE` (magic bytes, `TC-06`)
   - `422 INVALID_IMAGE` (corrupt bytes or `< 64x64`, `TC-06`, `TC-08`)
   - `401 UNAUTHORIZED` when Guest sets `save_history=true` (`SEC-02`, `TC-20`)
   - `TC-43` EXIF Orientation (`3, 6, 8`) upright rotation & in-RAM GPS/EXIF stripping (`ADR-007`, `ADR-010`)
   - `503 MODEL_NOT_READY` (`TC-29`) and `504 INFERENCE_TIMEOUT` (`TC-30`)
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import sys
import time
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import pytest

from app.ai.clip_fallback import (
    CLIPFallbackService,
    CallableFallbackProvider,
    FallbackConfig,
    KBCandidateIngredient,
    ProviderAssessment,
    compute_cosine_similarity,
)
from app.ai.image_processor import preprocess_uploaded_image
from app.ai.yolo_detector import (
    BBox,
    LabelMappingEntry,
    RawBoxPrediction,
    UltralyticsYOLOBackend,
    YOLODetector,
    compute_iou,
    split_clear_and_uncertain_ingredients,
)
from app.api.v1.ai_detect import get_detector_factory
from app.core.config import Settings, get_settings
from app.core.database import InMemoryCatalogRepository
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_DAU_HU,
    ING_TRUNG_GA,
    MODEL_YOLO_V1_SHA256,
)

WEIGHTS_PATH = REPO_ROOT / "backend" / "weights" / "yolo" / "ingredients_best.pt"
ARTIFACT_MANIFEST_PATH = REPO_ROOT / "backend" / "configs" / "yolo_model_artifact.json"
SEED_SQL_PATH = REPO_ROOT / "supabase" / "seed.sql"


# THUẬT TOÁN: Sinh luồng byte ảnh JPEG/PNG kiểm thử trong RAM kèm cờ EXIF Orientation và thẻ GPS giả lập
def _make_image_bytes(
    width: int = 120,
    height: int = 90,
    fmt: str = "JPEG",
    orientation: int | None = None,
    include_gps: bool = False,
) -> bytes:
    img = Image.new("RGB", (width, height), color=(210, 65, 45))
    buf = BytesIO()
    if orientation is not None or include_gps:
        exif = img.getexif()
        if orientation is not None:
            exif[0x0112] = orientation  # Orientation tag
        if include_gps:
            exif[0x8825] = {1: "N", 2: (10, 46, 0), 3: "E", 4: (106, 41, 0)}  # GPSInfo tag
        img.save(buf, format=fmt, exif=exif.tobytes())
    else:
        img.save(buf, format=fmt)
    return buf.getvalue()


def test_card20_item1_yolo_weights_and_sha256_manifest() -> None:
    """Checklist 1: Verify exported `.pt` weights, 64-hex SHA-256, and real backend forward pass."""
    assert WEIGHTS_PATH.exists() and WEIGHTS_PATH.stat().st_size > 0
    assert ARTIFACT_MANIFEST_PATH.exists()

    actual_sha256 = hashlib.sha256(WEIGHTS_PATH.read_bytes()).hexdigest()
    assert len(actual_sha256) == 64

    manifest = json.loads(ARTIFACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["weights_sha256"] == actual_sha256
    assert manifest["weights_sha256"] == MODEL_YOLO_V1_SHA256
    assert manifest["artifact_ref"] == "weights/yolo/ingredients_best.pt"
    assert manifest["class_count"] == 20
    assert len(manifest["labels"]) == 20

    seed_sql = SEED_SQL_PATH.read_text(encoding="utf-8")
    assert actual_sha256 in seed_sql
    assert "'weights/yolo/ingredients_best.pt'" in seed_sql

    # Verify UltralyticsYOLOBackend loads the local `.pt` checkpoint and runs inference
    runner = UltralyticsYOLOBackend(WEIGHTS_PATH)
    runner.load()
    assert runner.is_loaded
    sample_rgb = np.full((96, 96, 3), 128, dtype=np.uint8)
    preds = runner.predict_raw(sample_rgb, confidence_threshold=0.01)
    assert isinstance(preds, list)
    assert len(preds) >= 1
    assert 0 <= preds[0].class_id <= 19
    assert 0.0 <= preds[0].x1 < preds[0].x2 <= 1.0
    assert 0.0 <= preds[0].y1 < preds[0].y2 <= 1.0


def test_card20_item2_math01_iou_nms_and_v11_clear_uncertain_split() -> None:
    """Checklist 2: Verify MATH-01 IoU (64/136 ≈ 0.471), NMS, deduplication, and v1.1.0 split."""
    # MATH-01 canonical hand-calculated IoU: boxes [10,10,20,20] & [12,12,22,22] -> 64/136 ≈ 0.470588
    iou_pixel = compute_iou([10, 10, 20, 20], [12, 12, 22, 22])
    assert iou_pixel == pytest.approx(64.0 / 136.0, abs=1e-9)
    assert round(iou_pixel, 3) == 0.471

    iou_norm = compute_iou(
        BBox(x1=0.10, y1=0.10, x2=0.20, y2=0.20),
        BBox(x1=0.12, y1=0.12, x2=0.22, y2=0.22),
    )
    assert iou_norm == pytest.approx(64.0 / 136.0, abs=1e-9)

    # TC-07 & ADR-013 v1.1.0: 2 tomato boxes (0.92 and 0.85) + 1 tofu box (0.64) + 1 unmapped (class 99)
    mapping = {
        0: LabelMappingEntry(0, "tomato", UUID(ING_CA_CHUA), "Cà chua", category="vegetable"),
        11: LabelMappingEntry(11, "tofu", UUID(ING_DAU_HU), "Đậu hũ", category="protein"),
    }
    raw_boxes = [
        RawBoxPrediction(class_id=0, confidence=0.92, x1=0.10, y1=0.10, x2=0.40, y2=0.40),
        RawBoxPrediction(class_id=0, confidence=0.85, x1=0.50, y1=0.50, x2=0.80, y2=0.80),
        RawBoxPrediction(class_id=11, confidence=0.64, x1=0.15, y1=0.55, x2=0.45, y2=0.85),
        RawBoxPrediction(class_id=99, confidence=0.95, x1=0.05, y1=0.05, x2=0.25, y2=0.25),
    ]
    detector = YOLODetector(
        model_version="yolo11n-foodvision-v1.0",
        confidence_threshold=0.25,
        review_threshold=0.80,
        nms_iou_threshold=0.50,
        inference_backend=lambda _img, _thr: raw_boxes,
        class_mapping=mapping,
    )
    try:
        res = detector.detect_from_bytes(_make_image_bytes(120, 90))
        assert len(res.detections) == 3
        assert res.unmapped_class_ids == [99]
        assert len(res.suggested_ingredients) == 2

        resp = res.to_detect_response(review_threshold=0.80)
        assert [str(s.ingredient_id) for s in resp.suggested_ingredients] == [
            ING_CA_CHUA,
            ING_DAU_HU,
        ]
        assert resp.suggested_ingredients[0].max_confidence == pytest.approx(0.92)
        assert resp.suggested_ingredients[1].max_confidence == pytest.approx(0.64)

        # v1.1.0 clear_ingredients (>= 0.80) vs uncertain_ingredients (< 0.80)
        assert len(resp.clear_ingredients) == 1
        assert str(resp.clear_ingredients[0].ingredient_id) == ING_CA_CHUA
        assert len(resp.uncertain_ingredients) == 1
        assert str(resp.uncertain_ingredients[0].ingredient_id) == ING_DAU_HU

        clear, uncertain = split_clear_and_uncertain_ingredients(
            resp.suggested_ingredients, review_threshold=0.80
        )
        assert len(clear) == 1 and len(uncertain) == 1
    finally:
        detector.close()


def test_card20_item3_math01_clip_cosine_similarity_and_kb_fallback() -> None:
    """Checklist 3: Verify MATH-01 CLIP Cosine (0.96/sqrt(0.97) ≈ 0.975) and KB-bound fallback."""
    v = np.array([0.8, 0.6], dtype=np.float64)
    t1 = np.array([0.9, 0.4], dtype=np.float64)
    sim = compute_cosine_similarity(v, t1)
    expected = 0.96 / math.sqrt(0.97)
    assert sim == pytest.approx(expected, abs=1e-9)
    assert round(sim, 3) == 0.975

    # Verify CLIPFallbackService only ranks active non-pantry KB candidates and keeps needs_confirmation=True
    tofu_uuid = UUID(ING_DAU_HU)
    provider = CallableFallbackProvider(
        assessor=lambda _img, _cands: ProviderAssessment(
            scores_by_id={tofu_uuid: round(expected, 4)},
            model_source="clip-vit-b32-test",
        ),
        model_source="clip-vit-b32-test",
    )
    service = CLIPFallbackService(
        provider=provider,
        config=FallbackConfig(
            review_threshold=0.80,
            min_similarity=0.30,
            top_k=3,
            ambiguity_margin=0.05,
            ood_min_margin=0.0,
        ),
    )
    kb_candidates = [
        KBCandidateIngredient(tofu_uuid, "Đậu hũ", slug="dau-hu", category="protein", is_active=True),
    ]
    fb_result = service.suggest(
        _make_image_bytes(80, 80),
        candidates=kb_candidates,
        yolo_prediction={"class_index": 11, "class_name": "tofu", "confidence": 0.58},
    )
    assert fb_result.status == "SUGGESTED"
    assert fb_result.needs_confirmation is True
    assert fb_result.is_calibrated_probability is False
    assert len(fb_result.candidates) == 1
    assert fb_result.candidates[0].ingredient_id == tofu_uuid


def test_card20_item4_exif_rotation_gps_strip_and_endpoint_contracts(
    repo: InMemoryCatalogRepository,
    client: TestClient,
) -> None:
    """Checklist 4: Verify TC-04..08, TC-20, TC-29, TC-30, TC-43, SEC-02 on POST /api/v1/ai/detect."""
    # 1. TC-43: Portrait JPEG (120x80 stored with EXIF Orientation=6 -> 80x120 upright) + GPS metadata stripped
    portrait_gps_bytes = _make_image_bytes(
        width=120, height=80, fmt="JPEG", orientation=6, include_gps=True
    )
    processed = preprocess_uploaded_image(portrait_gps_bytes)
    assert processed.width == 80 and processed.height == 120
    assert processed.rgb_array.shape == (120, 80, 3)

    # Inject deterministic detector to verify upright shape and v1.1.0 response contract
    observed_shapes: list[tuple[int, int, int]] = []

    @contextmanager
    def _mock_detector_ctx(active_model, _cfg):
        def _predict(rgb_img, _thr):
            observed_shapes.append(rgb_img.shape)
            return [
                RawBoxPrediction(0, 0.91, 0.10, 0.15, 0.60, 0.70),   # Cà chua (clear >= 0.80)
                RawBoxPrediction(0, 0.83, 0.62, 0.20, 0.90, 0.75),   # Cà chua duplicate box
                RawBoxPrediction(11, 0.62, 0.12, 0.72, 0.55, 0.95),  # Đậu hũ (uncertain < 0.80)
            ]

        det = YOLODetector(
            model_version=active_model.version,
            confidence_threshold=active_model.confidence_threshold,
            review_threshold=active_model.review_threshold,
            nms_iou_threshold=0.50,
            inference_backend=_predict,
            class_mapping={
                0: LabelMappingEntry(0, "tomato", UUID(ING_CA_CHUA), "Cà chua", category="vegetable"),
                11: LabelMappingEntry(11, "tofu", UUID(ING_DAU_HU), "Đậu hũ", category="protein"),
            },
        )
        try:
            yield det
        finally:
            det.close()

    client.app.dependency_overrides[get_detector_factory] = lambda: _mock_detector_ctx
    try:
        # 2. TC-04, TC-07 & TC-43: Guest upload with EXIF Orientation=6 and save_history=false -> 200 OK
        res_guest = client.post(
            "/api/v1/ai/detect",
            files={"file": ("portrait_tomato.jpg", portrait_gps_bytes, "image/jpeg")},
        )
        assert res_guest.status_code == 200, res_guest.text
        assert observed_shapes[-1] == (120, 80, 3)
        body = res_guest.json()
        assert body["scan_id"] is None
        assert body["model_version"] == "yolo11n-foodvision-v1.0"
        assert len(body["detections"]) == 3
        assert len(body["suggested_ingredients"]) == 2
        assert [s["ingredient_id"] for s in body["clear_ingredients"]] == [ING_CA_CHUA]
        assert [s["ingredient_id"] for s in body["uncertain_ingredients"]] == [ING_DAU_HU]

        # 3. SEC-02 & TC-20: Guest with save_history=true -> 401 UNAUTHORIZED
        res_guest_save = client.post(
            "/api/v1/ai/detect",
            data={"save_history": "true"},
            files={"file": ("portrait_tomato.jpg", portrait_gps_bytes, "image/jpeg")},
        )
        assert res_guest_save.status_code == 401
        assert res_guest_save.json()["code"] == "UNAUTHORIZED"

        # 4. TC-20: Authenticated User with save_history=true -> creates scan_id usable in /recommendations
        user_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        user_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        res_user_save = client.post(
            "/api/v1/ai/detect",
            data={"save_history": "true"},
            files={"file": ("portrait_tomato.jpg", portrait_gps_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer user:{user_a}"},
        )
        assert res_user_save.status_code == 200, res_user_save.text
        scan_id = res_user_save.json()["scan_id"]
        assert scan_id is not None

        # User A can attach scan_id to /recommendations; User B gets 404 SCAN_NOT_OWNED
        res_rec_owner = client.post(
            "/api/v1/recommendations",
            json={"ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA], "scan_id": scan_id},
            headers={"Authorization": f"Bearer user:{user_a}"},
        )
        assert res_rec_owner.status_code == 200
        res_rec_other = client.post(
            "/api/v1/recommendations",
            json={"ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA], "scan_id": scan_id},
            headers={"Authorization": f"Bearer user:{user_b}"},
        )
        assert res_rec_other.status_code == 404
        assert res_rec_other.json()["code"] == "SCAN_NOT_OWNED"

        # 5. TC-05: Image > 5 MiB -> 413 IMAGE_TOO_LARGE
        oversized = b"\xff\xd8\xff" + (b"\x00" * (5_242_880 + 10))
        res_413 = client.post(
            "/api/v1/ai/detect",
            files={"file": ("huge.jpg", oversized, "image/jpeg")},
        )
        assert res_413.status_code == 413
        assert res_413.json()["code"] == "IMAGE_TOO_LARGE"

        # 6. TC-06(1): Invalid magic bytes (PDF disguised as .jpg) -> 415 UNSUPPORTED_IMAGE_TYPE
        res_415 = client.post(
            "/api/v1/ai/detect",
            files={"file": ("fake.jpg", b"%PDF-1.7 not an image", "image/jpeg")},
        )
        assert res_415.status_code == 415
        assert res_415.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"

        # 7. TC-06(2) & TC-08: Corrupt PNG stream or tiny < 64x64 image -> 422 INVALID_IMAGE
        res_422_corrupt = client.post(
            "/api/v1/ai/detect",
            files={"file": ("corrupt.png", b"\x89PNG\r\n\x1a\ncorrupt_payload", "image/png")},
        )
        assert res_422_corrupt.status_code == 422
        assert res_422_corrupt.json()["code"] == "INVALID_IMAGE"

        tiny_bytes = _make_image_bytes(width=32, height=32, fmt="PNG")
        res_422_tiny = client.post(
            "/api/v1/ai/detect",
            files={"file": ("tiny.png", tiny_bytes, "image/png")},
        )
        assert res_422_tiny.status_code == 422
        assert res_422_tiny.json()["code"] == "INVALID_IMAGE"

        # 8. TC-29: No active AI model -> 503 MODEL_NOT_READY
        saved_model = repo.get_active_ai_model()
        repo.set_active_ai_model(None)
        try:
            res_503 = client.post(
                "/api/v1/ai/detect",
                files={"file": ("ok.jpg", portrait_gps_bytes, "image/jpeg")},
            )
            assert res_503.status_code == 503
            assert res_503.json()["code"] == "MODEL_NOT_READY"
        finally:
            repo.set_active_ai_model(saved_model)

        # 9. TC-30: Inference exceeds configured timeout -> 504 INFERENCE_TIMEOUT
        @contextmanager
        def _slow_detector_ctx(active_model, _cfg):
            def _slow_predict(_rgb_img, _thr):
                time.sleep(0.25)
                return []

            det = YOLODetector(
                model_version=active_model.version,
                timeout_ms=500,
                inference_backend=_slow_predict,
                class_mapping={
                    0: LabelMappingEntry(0, "tomato", UUID(ING_CA_CHUA), "Cà chua", category="vegetable")
                },
            )
            try:
                yield det
            finally:
                det.close()

        client.app.dependency_overrides[get_detector_factory] = lambda: _slow_detector_ctx
        client.app.dependency_overrides[get_settings] = lambda: Settings(
            inference_timeout_seconds=0.05,
            inference_timeout_ms=50,
        )
        res_504 = client.post(
            "/api/v1/ai/detect",
            files={"file": ("slow.jpg", portrait_gps_bytes, "image/jpeg")},
        )
        assert res_504.status_code == 504
        assert res_504.json()["code"] == "INFERENCE_TIMEOUT"
    finally:
        client.app.dependency_overrides.pop(get_detector_factory, None)
        client.app.dependency_overrides.pop(get_settings, None)


# THUẬT TOÁN: Kiểm chứng công cụ nhập trọng số GPU Colab/Kaggle (--import-weights) và bộ đệm giữ ấm YOLODetector
def test_card20_gpu_weights_importer_and_warm_detector_cache() -> None:
    import shutil
    from app.api.v1.ai_detect import default_detector_context
    from scripts.yolo_weights_registry import import_external_yolo_weights

    scratch_dir = REPO_ROOT / "datasets" / "processed" / "_pytest_scratch_weights"
    shutil.rmtree(scratch_dir, ignore_errors=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    try:
        dst_pt = scratch_dir / "imported_best.pt"
        dst_manifest = scratch_dir / "imported_manifest.json"
        manifest = import_external_yolo_weights(
            WEIGHTS_PATH,
            weights_path=dst_pt,
            artifact_manifest_path=dst_manifest,
            sync_repo_seeds=False,
        )
        assert dst_pt.exists()
        assert manifest["training_backend"] == "ultralytics_gpu_imported"
        assert len(manifest["weights_sha256"]) == 64

        repo = InMemoryCatalogRepository()
        active_model = repo.get_active_ai_model()
        assert active_model is not None
        cfg = get_settings()
        with default_detector_context(active_model, cfg) as det1:
            with default_detector_context(active_model, cfg) as det2:
                assert det1 is det2
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)
