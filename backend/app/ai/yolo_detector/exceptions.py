"""Domain & configuration exceptions for YOLO ingredient detection."""

from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode

# ==============================================================================
# Domain & Configuration Exceptions (mapped automatically to OpenAPI ErrorResponse)
# ==============================================================================
class DetectorConfigurationError(AppError):
    """Raised when detector configuration, mapping, or runtime backend is invalid."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=503,
            code=ErrorCode.MODEL_NOT_READY,
            message=message,
            details=details,
        )


class ModelWeightsNotFoundError(DetectorConfigurationError):
    """Raised when configured YOLO model weights file is missing or empty."""


class InvalidClassMappingError(AppError):
    """Raised when configured class mapping violates FoodVision AI label rules."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code=ErrorCode.INVALID_LABEL_MAPPING,
            message=message,
            details=details,
        )


class ImageValidationError(AppError):
    """Base exception for invalid, oversized, unsupported, or unreadable images."""


class ImageTooLargeError(ImageValidationError):
    """Raised when image payload exceeds configured maximum byte limit (`413`)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=413,
            code=ErrorCode.IMAGE_TOO_LARGE,
            message=message,
            details=details,
        )


class UnsupportedImageFormatError(ImageValidationError):
    """Raised when binary magic bytes are not JPEG, PNG, or WebP (`415`)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=415,
            code=ErrorCode.UNSUPPORTED_IMAGE_TYPE,
            message=message,
            details=details,
        )


class ImageDecodeError(ImageValidationError):
    """Raised when image stream fails decoding or violates pixel bounds (`422`)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message=message,
            details=details,
        )


class ImagePathNotAllowedError(ImageValidationError):
    """Raised when an image file path is outside configured `allowed_image_dirs`."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message=message,
            details=details,
        )


class DetectorInferenceTimeoutError(AppError):
    """Raised when YOLO inference exceeds configured timeout ceiling (`504`)."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            status_code=504,
            code=ErrorCode.INFERENCE_TIMEOUT,
            message=message,
            details=details,
        )
