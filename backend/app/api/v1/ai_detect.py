"""Vision AI Detection Endpoint (`POST /api/v1/ai/detect`) — TP 01, TP 02, TP 14 (`ADR-010`, `ADR-013`).

Implements Card #20 (`[GD3 - TP01, TP02, TP14]`):
- Validates upload size (`413 IMAGE_TOO_LARGE`), binary magic bytes (`415 UNSUPPORTED_IMAGE_TYPE`),
  minimum dimensions `< 64x64` / corrupt stream (`422 INVALID_IMAGE`).
- Enforces `save_history=true` authentication (`401 UNAUTHORIZED` for Guest, `SEC-02`, `TC-20`).
- Auto-rotates pixels via `EXIF Orientation` and strips all `EXIF/GPS` metadata in RAM (`TC-43`).
- Runs YOLO detection + Class-wise NMS (`MATH-01`) + `ai_labels` mapping (`category != 'pantry'`),
  bounded by `asyncio.Semaphore(MAX_CONCURRENT_INFERENCES)` and `INFERENCE_TIMEOUT_SECONDS` (`504`).
- Deduplicates `suggested_ingredients` by `max_confidence` (`TC-07`) and splits into
  `clear_ingredients` (`confidence >= 0.80`) and `uncertain_ingredients` (`confidence < 0.80`)
  per `PR #11` (`ADR-013` `v1.1.0`).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
import threading
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.ai.clip_fallback import (
    FallbackStatus,
    KBCandidateIngredient,
    get_clip_fallback_service,
)
from app.ai.image_processor import ProcessedImage, preprocess_uploaded_image
from app.ai.yolo_detector import (
    IngredientDetectionResult,
    LabelMappingEntry,
    YOLODetector,
)
from app.core.auth import get_optional_user_id
from app.core.config import Settings, get_settings
from app.core.database import AIModelRecord, CatalogRepository, get_catalog_repo
from app.core.errors import AppError, ErrorCode
from app.schemas.ai import DetectResponse, SuggestedIngredient

router = APIRouter(tags=["AI"])

_inference_semaphore: asyncio.Semaphore | None = None
_semaphore_limit: int | None = None
_detector_cache_lock = threading.Lock()
_cached_detector_key: tuple[Any, ...] | None = None
_cached_detector: YOLODetector | None = None


# THUẬT TOÁN: Giới hạn số lượng tác vụ suy luận AI đồng thời bằng Semaphore (`OPS-03`, `NFR-14`)
def _get_inference_semaphore(max_concurrent: int) -> asyncio.Semaphore:
    global _inference_semaphore, _semaphore_limit
    limit = max(1, int(max_concurrent))
    if _inference_semaphore is None or _semaphore_limit != limit:
        _inference_semaphore = asyncio.Semaphore(limit)
        _semaphore_limit = limit
    return _inference_semaphore


# THUẬT TOÁN: Bộ nhớ đệm đối tượng YOLODetector ấm đa luồng (Warm Model Singleton Cache)
# - Khóa bộ đệm theo tổ hợp (model_id, version, artifact_path, mtime_ns, ngưỡng conf/review, bảng nhãn).
# - Tránh nạp lại trọng số `.pt` từ đĩa và khởi tạo lại ThreadPoolExecutor trên từng HTTP request (`PERF-01`).
# - Khi Admin kích hoạt/rollback phiên bản model mới hoặc tệp trọng số thay đổi, tự động đóng an toàn
#   detector cũ trước khi hoán đổi sang detector mới (`TC-29`, `BR-02`, `BR-12`).
@contextmanager
def default_detector_context(
    active_model: AIModelRecord,
    cfg: Settings,
) -> Iterator[YOLODetector]:
    global _cached_detector_key, _cached_detector

    mapping: dict[int, LabelMappingEntry] = {}
    mapping_sig: list[tuple[int, str, str, str]] = []
    for idx, lbl in sorted(active_model.labels_by_index.items()):
        if lbl.category == "pantry" or not lbl.is_active:
            continue
        mapping[idx] = LabelMappingEntry(
            class_index=idx,
            class_name=lbl.class_name,
            ingredient_id=UUID(lbl.ingredient_id),
            ingredient_name_vi=lbl.ingredient_name_vi,
            is_pantry=False,
            is_active=True,
            category=lbl.category,
        )
        mapping_sig.append((idx, lbl.class_name, lbl.ingredient_id, lbl.category))

    if not mapping:
        raise AppError(
            status_code=503,
            code=ErrorCode.MODEL_NOT_READY,
            message="Mô hình AI active chưa có bảng ánh xạ nhãn hợp lệ.",
            details={"reason": "empty_valid_label_mapping"},
        )

    artifact_raw = active_model.artifact_ref or cfg.model_artifact_path
    artifact_mtime_ns = 0
    if artifact_raw:
        cand_path = Path(str(artifact_raw))
        if not cand_path.is_absolute():
            backend_rel = Path(__file__).resolve().parents[3] / cand_path
            if backend_rel.exists():
                cand_path = backend_rel
        if cand_path.exists():
            artifact_mtime_ns = cand_path.stat().st_mtime_ns

    timeout_ms = max(100, int(cfg.inference_timeout_seconds * 1000))
    cache_key = (
        active_model.id,
        active_model.version,
        str(artifact_raw),
        artifact_mtime_ns,
        round(float(active_model.confidence_threshold), 6),
        round(float(active_model.review_threshold), 6),
        timeout_ms,
        int(cfg.min_image_dimension),
        tuple(mapping_sig),
    )

    old_detector: YOLODetector | None = None
    with _detector_cache_lock:
        if _cached_detector is None or _cached_detector_key != cache_key:
            new_detector = YOLODetector(
                artifact_path=artifact_raw,
                model_version=active_model.version,
                confidence_threshold=active_model.confidence_threshold,
                review_threshold=active_model.review_threshold,
                timeout_ms=timeout_ms,
                min_image_dimension=cfg.min_image_dimension,
                nms_iou_threshold=0.50,
                class_mapping=mapping,
            )
            old_detector = _cached_detector
            _cached_detector = new_detector
            _cached_detector_key = cache_key
        detector = _cached_detector

    if old_detector is not None:
        old_detector.close()

    yield detector


DetectorFactory = Callable[[AIModelRecord, Settings], Any]


def get_detector_factory() -> DetectorFactory:
    """Dependency returning the context-manager factory for `YOLODetector`."""
    return default_detector_context


def get_clip_service() -> Any:
    """Dependency returning the controlled CLIP fallback service."""
    return get_clip_fallback_service()


def _build_kb_candidates(repo: CatalogRepository) -> list[KBCandidateIngredient]:
    active_ings, _ = repo.list_active_ingredients(
        exclude_pantry=True, limit=200, offset=0
    )
    en_by_ing_id: dict[str, str] = {}
    active_model = repo.get_active_ai_model()
    if active_model is not None:
        for lbl in active_model.labels_by_index.values():
            en_by_ing_id[str(lbl.ingredient_id)] = lbl.class_name.replace("_", " ")

    candidates: list[KBCandidateIngredient] = []
    for ing in active_ings:
        en_name = en_by_ing_id.get(str(ing.id))
        prompts: tuple[str, ...] = ()
        if en_name:
            prompts = (
                f"a photo of fresh {en_name} food ingredient",
                f"raw {en_name} in kitchen",
                en_name,
                ing.name_vi,
            )
        candidates.append(
            KBCandidateIngredient(
                ingredient_id=UUID(ing.id),
                name_vi=ing.name_vi,
                slug=ing.slug,
                name_en=en_name,
                category=ing.category,
                is_active=ing.is_active,
                aliases=tuple(ing.aliases),
                prompts=prompts,
            )
        )
    return candidates


# THUẬT TOÁN: Kích hoạt có kiểm soát nhánh phụ CLIP/VLM cho vùng ảnh khó (`TP 02`, `MATH-01`)
# - Chỉ đánh giá trên tập ứng viên nguyên liệu chính đang hoạt động (`category != 'pantry'`, `is_active = True`).
# - Khi YOLO không có nguyên liệu chắc chắn (`clear_ingredients` rỗng) hoặc phát hiện rỗng, gọi 1 lượt đánh giá
#   toàn ảnh và hợp nhất ứng viên gợi ý vào `suggested_ingredients` với độ tin cậy kẹp `< review_threshold`
#   để luôn rơi vào `uncertain_ingredients` (`needs_confirmation = True`, bảo toàn `ADR-013`).
def run_clip_fallback_if_enabled(
    clip_service: Any,
    processed: ProcessedImage,
    result: IngredientDetectionResult,
    repo: CatalogRepository,
    *,
    review_threshold: float = 0.80,
) -> list[Any]:
    candidates = _build_kb_candidates(repo)
    if not candidates:
        return []

    has_confident_yolo = any(
        s.max_confidence >= review_threshold for s in result.suggested_ingredients
    )
    if has_confident_yolo and not any(d.needs_confirmation for d in result.detections):
        return []

    fb_res = clip_service.suggest(
        processed,
        candidates=candidates,
        requested_by_backend=True,
        review_threshold=review_threshold,
    )
    if fb_res.status == FallbackStatus.SUGGESTED and fb_res.candidates:
        merged_by_id: dict[UUID, SuggestedIngredient] = {
            item.ingredient_id: item for item in result.suggested_ingredients
        }
        capped_ceiling = round(max(0.01, review_threshold - 0.01), 4)
        for cand in fb_res.candidates:
            safe_score = min(round(max(0.01, float(cand.similarity)), 4), capped_ceiling)
            existing = merged_by_id.get(cand.ingredient_id)
            if existing is None or safe_score > existing.max_confidence:
                merged_by_id[cand.ingredient_id] = SuggestedIngredient(
                    ingredient_id=cand.ingredient_id,
                    name_vi=cand.name_vi,
                    max_confidence=safe_score,
                )
        result.suggested_ingredients = sorted(
            merged_by_id.values(),
            key=lambda s: (-s.max_confidence, s.name_vi, str(s.ingredient_id)),
        )
        result.requires_user_confirmation = True
    return [fb_res]


# THUẬT TOÁN: Quy trình Nhận diện Ảnh Đa Nguyên liệu, Xoay EXIF & Phân tách HITL (`FR-03`, `FR-04`, `ADR-013`)
# 1. Kiểm tra quyền lưu lịch sử (`save_history=true` bắt buộc có Bearer JWT -> `401 UNAUTHORIZED`).
# 2. Đọc luồng byte có trần dung lượng, xác thực magic bytes, tự xoay ảnh theo `EXIF Orientation`
#    và xóa sạch mọi metadata `EXIF/GPS` trong RAM (`preprocess_uploaded_image`).
# 3. Kiểm tra kích thước tối thiểu `>= 64x64` (`422 INVALID_IMAGE` nếu ảnh quá nhỏ).
# 4. Kiểm tra mô hình AI active (`503 MODEL_NOT_READY` nếu chưa kích hoạt).
# 5. Thực thi suy luận dưới `Semaphore` và `asyncio.wait_for` (`504 INFERENCE_TIMEOUT` khi quá hạn).
# 6. Khử trùng `suggested_ingredients` theo `max_confidence` và tách thành `clear_ingredients` (>= 0.80)
#    cùng `uncertain_ingredients` (< 0.80); giải phóng toàn bộ buffer ảnh trong khối `finally`.
@router.post("/ai/detect", response_model=DetectResponse)
async def detect_ingredients(
    file: Annotated[UploadFile, File(...)],
    save_history: Annotated[bool, Form()] = False,
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
    cfg: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
    repo: Annotated[CatalogRepository, Depends(get_catalog_repo)] = None,  # type: ignore[assignment]
    detector_factory: Annotated[DetectorFactory, Depends(get_detector_factory)] = None,  # type: ignore[assignment]
    clip_service: Annotated[Any, Depends(get_clip_service)] = None,
) -> DetectResponse:
    """Detect multiple non-pantry food ingredients from a single uploaded image."""
    if save_history and not user_id:
        raise AppError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Cần đăng nhập (Bearer token) để lưu lịch sử nhận diện (save_history=true).",
            details={"save_history": True},
        )

    raw_bytes = b""
    processed: ProcessedImage | None = None
    try:
        raw_bytes = await file.read(cfg.max_upload_bytes + 1)
        processed = preprocess_uploaded_image(
            raw_bytes,
            max_upload_bytes=cfg.max_upload_bytes,
            max_image_pixels=cfg.max_image_pixels,
        )
        if (
            processed.width < cfg.min_image_dimension
            or processed.height < cfg.min_image_dimension
        ):
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message=(
                    f"Kích thước ảnh sau khi xoay EXIF ({processed.width}x{processed.height}) "
                    f"nhỏ hơn ngưỡng tối thiểu {cfg.min_image_dimension}x{cfg.min_image_dimension}px."
                ),
                details={
                    "reason": "image_dimensions_too_small",
                    "width": processed.width,
                    "height": processed.height,
                    "min_dimension": cfg.min_image_dimension,
                },
            )

        active_model = repo.get_active_ai_model()
        if active_model is None or not active_model.labels_by_index:
            raise AppError(
                status_code=503,
                code=ErrorCode.MODEL_NOT_READY,
                message="Chưa có mô hình nhận diện AI ở trạng thái active.",
                details={"reason": "no_active_ai_model"},
            )

        semaphore = _get_inference_semaphore(cfg.max_concurrent_inferences)
        rgb_array = processed.rgb_array

        def _sync_infer() -> IngredientDetectionResult:
            with detector_factory(active_model, cfg) as detector:
                return detector.detect(rgb_array)

        async with semaphore:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(_sync_infer),
                    timeout=cfg.inference_timeout_seconds,
                )
            except TimeoutError as exc:
                raise AppError(
                    status_code=504,
                    code=ErrorCode.INFERENCE_TIMEOUT,
                    message="Quá thời gian chờ suy luận ảnh từ dịch vụ AI.",
                    details={"timeout_seconds": cfg.inference_timeout_seconds},
                ) from exc

        if cfg.enable_clip_fallback and clip_service is not None:
            await asyncio.to_thread(
                run_clip_fallback_if_enabled,
                clip_service,
                processed,
                result,
                repo,
                review_threshold=active_model.review_threshold,
            )

        scan_uuid: UUID | None = None
        if save_history and user_id is not None:
            det_rows: list[dict[str, Any]] = []
            for d in result.detections:
                lbl = active_model.labels_by_index.get(d.class_id)
                if lbl is None:
                    continue
                det_rows.append(
                    {
                        "ai_label_id": lbl.id,
                        "confidence": d.calibrated_confidence,
                        "needs_confirmation": d.needs_confirmation,
                        "x1": d.bounding_box.x1,
                        "y1": d.bounding_box.y1,
                        "x2": d.bounding_box.x2,
                        "y2": d.bounding_box.y2,
                    }
                )
            suggested_ids = [str(s.ingredient_id) for s in result.suggested_ingredients]
            session = repo.create_scan_session(
                user_id=user_id,
                model_id=active_model.id,
                detections=det_rows,
                ingredient_ids=suggested_ids,
            )
            scan_uuid = UUID(session.id)

        return result.to_detect_response(
            scan_id=scan_uuid,
            review_threshold=active_model.review_threshold,
        )
    finally:
        del processed
        del raw_bytes
        await file.close()


# THUẬT TOÁN: Endpoint Kiểm thử Trực tiếp Nhánh phụ Đa phương thức CLIP/VLM (`TP 02` Diagnostics)
# - Cho phép tải ảnh lên từ Swagger UI `/docs` để kiểm chứng độc lập `CLIPFallbackService`
#   (Ollama Cloud / OpenAI-compatible VLM / OpenCLIP) trên tập đóng nguyên liệu KB (`category != 'pantry'`).
@router.post("/ai/vlm-suggest")
async def suggest_ingredients_vlm(
    file: Annotated[UploadFile, File(...)],
    top_k: Annotated[int, Form()] = 5,
    min_similarity: Annotated[float, Form()] = 0.25,
    cfg: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
    repo: Annotated[CatalogRepository, Depends(get_catalog_repo)] = None,  # type: ignore[assignment]
    clip_service: Annotated[Any, Depends(get_clip_service)] = None,
) -> dict[str, Any]:
    """Run standalone CLIP/VLM closed-set KB candidate assessment on an uploaded image."""
    raw_bytes = b""
    processed: ProcessedImage | None = None
    try:
        raw_bytes = await file.read(cfg.max_upload_bytes + 1)
        processed = preprocess_uploaded_image(
            raw_bytes,
            max_upload_bytes=cfg.max_upload_bytes,
            max_image_pixels=cfg.max_image_pixels,
        )
        if (
            processed.width < cfg.min_image_dimension
            or processed.height < cfg.min_image_dimension
        ):
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message=(
                    f"Kích thước ảnh sau khi xoay EXIF ({processed.width}x{processed.height}) "
                    f"nhỏ hơn ngưỡng tối thiểu {cfg.min_image_dimension}x{cfg.min_image_dimension}px."
                ),
                details={
                    "reason": "image_dimensions_too_small",
                    "width": processed.width,
                    "height": processed.height,
                },
            )

        candidates = _build_kb_candidates(repo)
        fb_result = await asyncio.to_thread(
            clip_service.suggest,
            processed,
            candidates=candidates,
            requested_by_backend=True,
            top_k=max(1, min(20, int(top_k))),
            min_similarity=float(min_similarity),
        )
        return fb_result.to_dict()
    finally:
        del processed
        del raw_bytes
        await file.close()
