"""Runtime configuration resolver for YOLO detector instances."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

from app.core.config import Settings, get_settings
from .exceptions import DetectorConfigurationError, InvalidClassMappingError
from .mapping import (
    _resolve_artifact_path,
    load_class_mapping_from_json_file,
    normalize_class_mapping,
)
from .models import ClassMappingInput, LabelMappingEntry

# ==============================================================================
# Configuration Object (DI & Environment Settings Integration — Zero Hardcoding)
# ==============================================================================
@dataclass(frozen=True)
class DetectorConfig:
    """Typed, immutable runtime configuration injected into `YOLODetector`."""

    artifact_path: Path | None
    model_version: str
    confidence_threshold: float
    review_threshold: float
    timeout_ms: int
    max_upload_bytes: int
    max_image_pixels: int
    min_image_dimension: int = 1
    max_image_dimension: int | None = None
    nms_iou_threshold: float | None = None
    allowed_image_dirs: tuple[Path, ...] = field(default_factory=tuple)
    class_mapping: Mapping[int, LabelMappingEntry] = field(default_factory=dict)

    # ==========================================================================
    # THUẬT TOÁN: Hợp nhất Cấu hình Detector Đa nguồn có Thứ tự Ưu tiên
    # - Ưu tiên tham số truyền trực tiếp -> `MODEL_CONFIG` (JSON inline / file) -> `Settings`.
    # - Chuẩn hóa danh sách thư mục ảnh an toàn (`allowed_image_dirs`) và bảng ánh xạ nhãn.
    # ==========================================================================
    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
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
    ) -> DetectorConfig:
        """Build `DetectorConfig` from `Settings` + optional environment/DI overrides."""
        cfg = settings or get_settings()

        raw_model_path = (
            str(artifact_path).strip()
            if artifact_path is not None
            else cfg.model_artifact_path.strip()
        )
        resolved_model_path = (
            _resolve_artifact_path(raw_model_path) if raw_model_path else None
        )

        resolved_dirs: list[Path] = []
        if allowed_image_dirs is not None:
            resolved_dirs = [
                Path(p).expanduser().resolve(strict=False)
                for p in allowed_image_dirs
                if str(p).strip()
            ]
        else:
            env_dirs = os.getenv("ALLOWED_IMAGE_DIRS", "").strip()
            if env_dirs:
                sep = os.pathsep if os.pathsep in env_dirs else ","
                resolved_dirs = [
                    Path(part.strip()).expanduser().resolve(strict=False)
                    for part in env_dirs.split(sep)
                    if part.strip()
                ]

        if class_mapping is not None:
            resolved_mapping = normalize_class_mapping(class_mapping, strict=True)
        elif class_mapping_path is not None:
            resolved_mapping = load_class_mapping_from_json_file(class_mapping_path)
        else:
            env_mapping_json = os.getenv("MODEL_CLASS_MAPPING_JSON", "").strip()
            env_mapping_path = os.getenv("MODEL_CLASS_MAPPING_PATH", "").strip()
            if env_mapping_json:
                try:
                    parsed_json = json.loads(env_mapping_json)
                except json.JSONDecodeError as exc:
                    raise DetectorConfigurationError(
                        "Biến môi trường MODEL_CLASS_MAPPING_JSON không đúng định dạng JSON.",
                        details={"reason": "invalid_model_class_mapping_env"},
                    ) from exc
                resolved_mapping = normalize_class_mapping(parsed_json, strict=True)
            elif env_mapping_path:
                resolved_mapping = load_class_mapping_from_json_file(env_mapping_path)
            else:
                resolved_mapping = {}

        env_min_dim = os.getenv("MIN_IMAGE_DIMENSION", "").strip()
        resolved_min_dim = (
            min_image_dimension
            if min_image_dimension is not None
            else (int(env_min_dim) if env_min_dim else 1)
        )
        env_max_dim = os.getenv("MAX_IMAGE_DIMENSION", "").strip()
        resolved_max_dim = (
            max_image_dimension
            if max_image_dimension is not None
            else (int(env_max_dim) if env_max_dim else None)
        )
        env_nms = os.getenv("NMS_IOU_THRESHOLD", "").strip()
        resolved_nms = (
            nms_iou_threshold
            if nms_iou_threshold is not None
            else (float(env_nms) if env_nms else None)
        )

        return cls(
            artifact_path=resolved_model_path,
            model_version=(
                model_version.strip()
                if model_version is not None
                else cfg.active_model_version.strip()
            ),
            confidence_threshold=(
                float(confidence_threshold)
                if confidence_threshold is not None
                else float(cfg.default_confidence_threshold)
            ),
            review_threshold=(
                float(review_threshold)
                if review_threshold is not None
                else float(cfg.default_review_threshold)
            ),
            timeout_ms=(
                int(timeout_ms)
                if timeout_ms is not None
                else int(cfg.inference_timeout_ms)
            ),
            max_upload_bytes=(
                int(max_upload_bytes)
                if max_upload_bytes is not None
                else int(cfg.max_upload_bytes)
            ),
            max_image_pixels=(
                int(max_image_pixels)
                if max_image_pixels is not None
                else int(cfg.max_image_pixels)
            ),
            min_image_dimension=resolved_min_dim,
            max_image_dimension=resolved_max_dim,
            nms_iou_threshold=resolved_nms,
            allowed_image_dirs=tuple(resolved_dirs),
            class_mapping=resolved_mapping,
        )
