"""Primary thread-safe YOLODetector service and cached DI provider."""

from __future__ import annotations

from .exceptions import ImageDecodeError
from .mapping import normalize_class_mapping
import os

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import logging
from pathlib import Path
import threading
from typing import Annotated, Any

from fastapi import Depends
import numpy as np

from app.ai.image_processor import ProcessedImage
from app.core.config import Settings, get_settings
from .backend import UltralyticsYOLOBackend, _CallableBackendAdapter
from .calibration import build_calibrator_from_env
from .config import DetectorConfig
from .exceptions import (
    DetectorConfigurationError,
    DetectorInferenceTimeoutError,
    InvalidClassMappingError,
)
from .input_guard import _DetectorInputGuardMixin
from .postprocess import _DetectorPostprocessMixin
from .models import (
    BoundingBox,
    ClassMappingInput,
    ConfidenceCalibrator,
    ConfirmationStatus,
    DetectedIngredientItem,
    ImageSource,
    IngredientDetectionResult,
    LabelMappingEntry,
    RawBoxPrediction,
    YOLOInferenceBackend,
)
from .nms import (
    aggregate_suggested_ingredients,
    apply_classwise_nms,
    needs_hitl_review,
)

logger = logging.getLogger(__name__)


class YOLODetector(_DetectorInputGuardMixin, _DetectorPostprocessMixin):
    """Lazy-loaded, configurable YOLO ingredient detector service."""

    def __init__(
        self,
        *,
        config: DetectorConfig | None = None,
        settings: Settings | None = None,
        artifact_path: str | Path | None = None,
        model_version: str | None = None,
        confidence_threshold: float | None = None,
        review_threshold: float | None = None,
        timeout_ms: int | None = None,
        max_upload_bytes: int | None = None,
        max_image_pixels: int | None = None,
        min_image_dimension: int | None = None,
        max_image_dimension: int | None = None,
        nms_iou_threshold: float | None = None,
        allowed_image_dirs: Sequence[str | Path] | None = None,
        class_mapping: ClassMappingInput | None = None,
        class_mapping_path: str | Path | None = None,
        calibrator: ConfidenceCalibrator | None = None,
        inference_backend: (
            YOLOInferenceBackend
            | Callable[[np.ndarray, float], Sequence[RawBoxPrediction]]
            | None
        ) = None,
    ) -> None:
        resolved_cfg = config or DetectorConfig.from_settings(
            settings,
            artifact_path=artifact_path,
            model_version=model_version,
            confidence_threshold=confidence_threshold,
            review_threshold=review_threshold,
            timeout_ms=timeout_ms,
            max_upload_bytes=max_upload_bytes,
            max_image_pixels=max_image_pixels,
            min_image_dimension=min_image_dimension,
            max_image_dimension=max_image_dimension,
            nms_iou_threshold=nms_iou_threshold,
            allowed_image_dirs=allowed_image_dirs,
            class_mapping=class_mapping,
            class_mapping_path=class_mapping_path,
        )
        self._validate_scalar_config(resolved_cfg)
        self._config = resolved_cfg
        self.artifact_path = resolved_cfg.artifact_path
        self.model_version = resolved_cfg.model_version
        self.confidence_threshold = resolved_cfg.confidence_threshold
        self.review_threshold = resolved_cfg.review_threshold
        self.timeout_ms = resolved_cfg.timeout_ms
        self._calibrator: ConfidenceCalibrator = (
            calibrator if calibrator is not None else build_calibrator_from_env()
        )
        self._backend = self._init_backend(inference_backend, resolved_cfg.artifact_path)
        self._loaded = False
        self._load_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="yolo-detector"
        )

    @staticmethod
    def _init_backend(
        backend: (
            YOLOInferenceBackend
            | Callable[[np.ndarray, float], Sequence[RawBoxPrediction]]
            | None
        ),
        artifact_path: Path | None,
    ) -> YOLOInferenceBackend:
        if backend is None:
            return UltralyticsYOLOBackend(artifact_path)
        if callable(backend) and not hasattr(backend, "predict_raw"):
            return _CallableBackendAdapter(backend)
        return backend  # type: ignore[return-value]

    @property
    def config(self) -> DetectorConfig:
        return self._config

    @property
    def calibrator(self) -> ConfidenceCalibrator:
        return self._calibrator

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Lazily initialize the underlying inference backend on first demand."""
        if self._loaded:
            return
        with self._load_lock:
            if self._loaded:
                return
            self._backend.load()
            self._loaded = True

    def close(self) -> None:
        """Release worker executor resources cleanly."""
        self._executor.shutdown(wait=False, cancel_futures=True)


    def _run_service_detection(
        self,
        processed: ProcessedImage,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult:
        effective_mapping = self._resolve_required_mapping(class_mapping)
        raw_preds = self._execute_bounded_inference(processed.rgb_array)
        items, unmapped_ids = self._postprocess_predictions(
            raw_preds,
            image_width=processed.width,
            image_height=processed.height,
            effective_mapping=effective_mapping,
        )
        suggestions = aggregate_suggested_ingredients(items)
        requires_confirmation = (not items) or any(
            item.needs_confirmation for item in items
        )
        return IngredientDetectionResult(
            model_version=self.model_version,
            detections=items,
            suggested_ingredients=suggestions,
            image_width=processed.width,
            image_height=processed.height,
            mime_type=processed.mime_type,
            calibration_method=self._calibrator.method_name,
            unmapped_class_ids=unmapped_ids,
            requires_user_confirmation=requires_confirmation,
        )

    def detect_from_bytes(
        self,
        image_bytes: bytes | bytearray | memoryview,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult:
        """Validate raw image bytes, lazy-load YOLO, and detect multiple ingredients."""
        processed = self._decode_and_validate_bytes(image_bytes)
        return self._run_service_detection(processed, class_mapping=class_mapping)

    def detect_from_path(
        self,
        image_path: str | Path,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult:
        """Read an image from a permitted directory and detect multiple ingredients."""
        processed = self._read_allowed_path(image_path)
        return self._run_service_detection(processed, class_mapping=class_mapping)

    def detect(
        self,
        image_source: ImageSource,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult:
        """Detect multiple ingredients from `bytes`, an allowed `Path`, or RGB `ndarray`."""
        if isinstance(image_source, (bytes, bytearray, memoryview)):
            return self.detect_from_bytes(image_source, class_mapping=class_mapping)
        if isinstance(image_source, (str, Path)):
            return self.detect_from_path(image_source, class_mapping=class_mapping)
        if isinstance(image_source, np.ndarray):
            processed = self._validate_rgb_ndarray(image_source)
            return self._run_service_detection(processed, class_mapping=class_mapping)
        raise ImageDecodeError(
            "Nguồn ảnh đầu vào không được hỗ trợ (chỉ nhận bytes, đường dẫn hợp lệ hoặc mảng RGB).",
            details={"reason": "unsupported_image_source_type"},
        )

    def predict(
        self,
        rgb_image: np.ndarray,
        label_map: Mapping[int, LabelMappingEntry] | None = None,
    ) -> list[Detection]:
        """Backward-compatible adapter returning `app.schemas.ai.Detection` items.

        Never falls back to raw YOLO/COCO `model.names`; unmapped class indices
        and pantry/inactive entries are filtered out safely.
        """
        processed = self._validate_rgb_ndarray(rgb_image)
        effective_mapping = (
            normalize_class_mapping(label_map, strict=False)
            if label_map
            else self._config.class_mapping
        )
        raw_preds = self._execute_bounded_inference(processed.rgb_array)
        items, _ = self._postprocess_predictions(
            raw_preds,
            image_width=processed.width,
            image_height=processed.height,
            effective_mapping=effective_mapping,
        )
        return [item.to_schema_detection() for item in items]


# ==============================================================================
# THUẬT TOÁN: Quản lý Bộ nhớ đệm Detector theo Chữ ký Cấu hình (Signature Cache)
# - Tái sử dụng thực thể `YOLODetector` khi bộ tham số cấu hình không đổi, tự động đóng
#   thread-pool cũ khi cấu hình thay đổi để tránh rò rỉ tài nguyên.
# ==============================================================================
_detector_cache_lock = threading.Lock()
_cached_detector: YOLODetector | None = None
_cached_signature: tuple[Any, ...] | None = None


def reset_detector_cache() -> None:
    """Clear cached detector instance (intended for isolated unit/integration tests)."""
    global _cached_detector, _cached_signature
    with _detector_cache_lock:
        if _cached_detector is not None:
            _cached_detector.close()
        _cached_detector = None
        _cached_signature = None


def get_yolo_detector(
    settings: Annotated[Settings, Depends(get_settings)],
) -> YOLODetector:
    """FastAPI dependency returning a lazy-loaded `YOLODetector` bound to `Settings`."""
    global _cached_detector, _cached_signature
    cfg = DetectorConfig.from_settings(settings)
    signature = (
        cfg.artifact_path,
        cfg.model_version,
        cfg.confidence_threshold,
        cfg.review_threshold,
        cfg.timeout_ms,
        cfg.max_upload_bytes,
        cfg.max_image_pixels,
        cfg.min_image_dimension,
        cfg.max_image_dimension,
        cfg.nms_iou_threshold,
        cfg.allowed_image_dirs,
        tuple(sorted(cfg.class_mapping.items())),
        os.getenv("CALIBRATION_METHOD", ""),
        os.getenv("CALIBRATION_TEMPERATURE", ""),
        os.getenv("CALIBRATION_PLATT_A", ""),
        os.getenv("CALIBRATION_PLATT_B", ""),
    )
    with _detector_cache_lock:
        if _cached_detector is None or _cached_signature != signature:
            if _cached_detector is not None:
                _cached_detector.close()
            _cached_detector = YOLODetector(config=cfg)
            _cached_signature = signature
        return _cached_detector
