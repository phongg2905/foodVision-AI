"""Typed data structures and protocols for YOLO detection & calibration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable
from uuid import UUID

import numpy as np
from pydantic import Field, model_validator

from app.schemas.ai import (
    REVIEW_CONFIDENCE_THRESHOLD,
    BBox,
    DetectResponse,
    Detection,
    SuggestedIngredient,
)
from app.schemas.common import StrictSchema

ConfirmationStatus = Literal["confident", "needs_confirmation"]
ImageSource = bytes | bytearray | memoryview | str | Path | np.ndarray


@dataclass(frozen=True)
class LabelMappingEntry:
    """In-memory representation of a validated `ai_labels` food class mapping."""

    class_index: int
    class_name: str
    ingredient_id: UUID | None = None
    ingredient_name_vi: str | None = None
    is_pantry: bool = False
    is_active: bool = True
    category: str | None = None

    @property
    def class_id(self) -> int:
        return self.class_index

    @property
    def label(self) -> str:
        return self.class_name


@dataclass(frozen=True)
class RawBoxPrediction:
    """Backend-agnostic raw bounding box emitted by an object detection runner."""

    class_id: int
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    normalized: bool = True


class BoundingBox(StrictSchema):
    """Normalized `[0, 1]` bounding box on an EXIF-upright RGB image."""

    x1: float = Field(ge=0.0, le=1.0)
    y1: float = Field(ge=0.0, le=1.0)
    x2: float = Field(ge=0.0, le=1.0)
    y2: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> BoundingBox:
        if self.x1 >= self.x2 or self.y1 >= self.y2:
            raise ValueError("Invalid bounding_box: expected x1 < x2 and y1 < y2")
        return self

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_schema_bbox(self) -> BBox:
        """Convert to `app.schemas.ai.BBox`."""
        return BBox(x1=self.x1, y1=self.y1, x2=self.x2, y2=self.y2)

    def to_pixel_xyxy(
        self, image_width: int, image_height: int
    ) -> tuple[int, int, int, int]:
        """Project normalized coordinates onto integer pixel bounds."""
        if image_width <= 0 or image_height <= 0:
            raise ValueError("Image dimensions must be positive")
        px1 = max(0, min(image_width - 1, int(round(self.x1 * image_width))))
        py1 = max(0, min(image_height - 1, int(round(self.y1 * image_height))))
        px2 = max(px1 + 1, min(image_width, int(round(self.x2 * image_width))))
        py2 = max(py1 + 1, min(image_height, int(round(self.y2 * image_height))))
        return (px1, py1, px2, py2)


class DetectedIngredientItem(StrictSchema):
    """Single mapped ingredient detection with raw vs calibrated probability."""

    class_id: int = Field(ge=0)
    label: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    calibrated_confidence: float = Field(ge=0.0, le=1.0)
    is_calibrated: bool = False
    bounding_box: BoundingBox
    model_version: str = Field(min_length=1)
    needs_confirmation: bool
    confirmation_status: ConfirmationStatus
    ingredient_id: UUID | None = None
    ingredient_name_vi: str | None = None

    def to_schema_detection(
        self, *, use_calibrated_confidence: bool = False
    ) -> Detection:
        """Convert to OpenAPI `Detection` contract (`app.schemas.ai.Detection`)."""
        score = (
            self.calibrated_confidence
            if use_calibrated_confidence
            else self.confidence
        )
        return Detection(
            class_index=self.class_id,
            class_name=self.label,
            ingredient_id=self.ingredient_id,
            ingredient_name=self.ingredient_name_vi,
            confidence=score,
            needs_confirmation=self.needs_confirmation,
            bbox=self.bounding_box.to_schema_bbox(),
        )


class IngredientDetectionResult(StrictSchema):
    """Multi-ingredient detection output ready for `/api/v1/ai/detect`."""

    model_version: str = Field(min_length=1)
    detections: list[DetectedIngredientItem]
    suggested_ingredients: list[SuggestedIngredient]
    image_width: int = Field(ge=1)
    image_height: int = Field(ge=1)
    mime_type: str | None = None
    calibration_method: str = Field(min_length=1)
    unmapped_class_ids: list[int] = Field(default_factory=list)
    requires_user_confirmation: bool

    # THUẬT TOÁN: Chuyển đổi kết quả nhận diện sang khung DetectResponse (`v1.1.0` `ADR-013`)
    # - Tách `suggested_ingredients` thành `clear_ingredients` (`max_confidence >= review_threshold`)
    #   và `uncertain_ingredients` (`max_confidence < review_threshold`).
    def to_detect_response(
        self,
        *,
        scan_id: UUID | None = None,
        review_threshold: float = REVIEW_CONFIDENCE_THRESHOLD,
    ) -> DetectResponse:
        """Convert to `DetectResponse` envelope (`app.schemas.ai.DetectResponse`)."""
        clear = [
            item
            for item in self.suggested_ingredients
            if item.max_confidence >= review_threshold
        ]
        uncertain = [
            item
            for item in self.suggested_ingredients
            if item.max_confidence < review_threshold
        ]
        return DetectResponse(
            scan_id=scan_id,
            model_version=self.model_version,
            detections=[item.to_schema_detection() for item in self.detections],
            suggested_ingredients=self.suggested_ingredients,
            clear_ingredients=clear,
            uncertain_ingredients=uncertain,
        )


@runtime_checkable
class ConfidenceCalibrator(Protocol):
    """Post-hoc probability calibrator separating raw score from true accuracy."""

    @property
    def method_name(self) -> str: ...

    @property
    def is_calibrated(self) -> bool: ...

    def calibrate(
        self, raw_confidence: float, class_id: int | None = None
    ) -> float: ...


@runtime_checkable
class YOLOInferenceBackend(Protocol):
    """Low-level object detector runner interface (easy to mock in unit tests)."""

    def load(self) -> None: ...

    def predict_raw(
        self,
        rgb_image: np.ndarray,
        *,
        confidence_threshold: float,
    ) -> Sequence[RawBoxPrediction]: ...


@runtime_checkable
class IngredientDetectorProtocol(Protocol):
    """Service-level contract callable by FastAPI routers."""

    @property
    def model_version(self) -> str: ...

    def detect(
        self,
        image_source: ImageSource,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult: ...

    def detect_from_bytes(
        self,
        image_bytes: bytes | bytearray | memoryview,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult: ...

    def detect_from_path(
        self,
        image_path: str | Path,
        *,
        class_mapping: ClassMappingInput | None = None,
    ) -> IngredientDetectionResult: ...


ClassMappingInput = (
    Mapping[int, LabelMappingEntry]
    | Mapping[int, str]
    | Mapping[int, Mapping[str, Any]]
    | Mapping[str, Any]
    | Sequence[LabelMappingEntry | Mapping[str, Any]]
)
