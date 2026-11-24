"""In-memory image validation, EXIF upright transpose, GPS stripper, and bbox cropper.

Aligned with `docs/04-ai-model/ai-model-design.md` (Sections 2 & 3) and `ADR-010`:
- Rejects payloads exceeding configured upload ceiling (`413 IMAGE_TOO_LARGE`).
- Verifies binary magic bytes for JPEG/PNG/WebP (`415 UNSUPPORTED_IMAGE_TYPE`).
- Transposes pixels via EXIF Orientation, converts to clean RGB, and strips ALL
  EXIF/GPS/device metadata in RAM without persisting raw user images.
- Validates normalized `[0, 1]` bounding boxes and crops regions safely for
  multimodal CLIP/VLM fallback processing.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
from typing import Any, TypeAlias

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.schemas.ai import BBox

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]


@dataclass(frozen=True)
class ProcessedImage:
    """Clean upright RGB image array stripped of all EXIF/GPS metadata."""

    rgb_array: np.ndarray
    width: int
    height: int
    mime_type: str


@dataclass(frozen=True)
class CroppedRegion:
    """Validated RGB region prepared for multimodal CLIP/VLM candidate ranking."""

    rgb_array: np.ndarray
    width: int
    height: int
    was_cropped: bool
    bbox_valid: bool | None
    pixel_box: tuple[int, int, int, int] | None = None
    normalized_bbox: BBox | None = None


ImageInput: TypeAlias = (
    bytes | bytearray | memoryview | ProcessedImage | np.ndarray | Image.Image
)
BBoxInput: TypeAlias = (
    BBox | tuple[float, float, float, float] | list[float] | Mapping[str, Any]
)


def _resolve_limits(
    max_upload_bytes: int | None,
    max_image_pixels: int | None,
) -> tuple[int, int]:
    """Resolve byte and pixel ceilings from runtime settings when omitted."""
    settings = get_settings()
    resolved_bytes = (
        settings.max_upload_bytes if max_upload_bytes is None else int(max_upload_bytes)
    )
    resolved_pixels = (
        settings.max_image_pixels if max_image_pixels is None else int(max_image_pixels)
    )
    return resolved_bytes, resolved_pixels
