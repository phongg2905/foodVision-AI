"""Ultralytics YOLO ingredient detector service, calibration, and HITL gating."""

from app.schemas.ai import BBox

from .backend import UltralyticsYOLOBackend, _CallableBackendAdapter
from .calibration import (
    IdentityCalibrator,
    PlattScalingCalibrator,
    TemperatureScalingCalibrator,
    build_calibrator_from_env,
)
from .config import DetectorConfig
from .exceptions import (
    DetectorConfigurationError,
    DetectorInferenceTimeoutError,
    ImageDecodeError,
    ImagePathNotAllowedError,
    ImageTooLargeError,
    ImageValidationError,
    InvalidClassMappingError,
    ModelWeightsNotFoundError,
    UnsupportedImageFormatError,
)
from .mapping import (
    load_class_mapping_from_json_file,
    normalize_class_mapping,
)
from .models import (
    BoundingBox,
    ClassMappingInput,
    ConfidenceCalibrator,
    ConfirmationStatus,
    DetectedIngredientItem,
    ImageSource,
    IngredientDetectionResult,
    IngredientDetectorProtocol,
    LabelMappingEntry,
    RawBoxPrediction,
    SuggestedIngredient,
    YOLOInferenceBackend,
)
from .nms import (
    aggregate_suggested_ingredients,
    apply_classwise_nms,
    compute_iou,
    needs_hitl_review,
    split_clear_and_uncertain_ingredients,
)
from .service import YOLODetector, get_yolo_detector, reset_detector_cache

__all__ = [
    "BBox",
    "BoundingBox",
    "ClassMappingInput",
    "ConfidenceCalibrator",
    "ConfirmationStatus",
    "DetectedIngredientItem",
    "DetectorConfig",
    "DetectorConfigurationError",
    "DetectorInferenceTimeoutError",
    "IdentityCalibrator",
    "ImageDecodeError",
    "ImagePathNotAllowedError",
    "ImageSource",
    "ImageTooLargeError",
    "ImageValidationError",
    "IngredientDetectionResult",
    "IngredientDetectorProtocol",
    "InvalidClassMappingError",
    "LabelMappingEntry",
    "ModelWeightsNotFoundError",
    "PlattScalingCalibrator",
    "RawBoxPrediction",
    "SuggestedIngredient",
    "TemperatureScalingCalibrator",
    "UltralyticsYOLOBackend",
    "UnsupportedImageFormatError",
    "YOLODetector",
    "YOLOInferenceBackend",
    "aggregate_suggested_ingredients",
    "apply_classwise_nms",
    "build_calibrator_from_env",
    "compute_iou",
    "get_yolo_detector",
    "load_class_mapping_from_json_file",
    "needs_hitl_review",
    "normalize_class_mapping",
    "reset_detector_cache",
    "split_clear_and_uncertain_ingredients",
]
