"""Vision AI detection, HITL bounding box, and model registry schemas (`v1.1.0` `ADR-013`).

# CONFLICT-RESOLVED: Synchronized `Detection` (`needs_confirmation`) and `DetectResponse`
# (`clear_ingredients` for confidence >= 0.80, `uncertain_ingredients` for confidence < 0.80)
# with `docs/03-api/openapi.yaml` (`PR #11` / `ADR-013` v1.1.0).
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import StrictSchema

ModelStatus = Literal["draft", "active", "archived"]
REVIEW_CONFIDENCE_THRESHOLD = 0.80


class BBox(StrictSchema):
    """Normalized [0, 1] bounding box coordinates (`x1 < x2`, `y1 < y2`)."""

    x1: float = Field(ge=0.0, le=1.0)
    y1: float = Field(ge=0.0, le=1.0)
    x2: float = Field(ge=0.0, le=1.0)
    y2: float = Field(ge=0.0, le=1.0)

    # THUẬT TOÁN: Kiểm tra bất biến hình học hộp giới hạn chuẩn hóa [0, 1] (`x1 < x2`, `y1 < y2`)
    @model_validator(mode="after")
    def validate_bounds(self) -> BBox:
        if self.x1 >= self.x2 or self.y1 >= self.y2:
            raise ValueError("Invalid bbox coordinates: expected x1 < x2 and y1 < y2")
        return self


class Detection(StrictSchema):
    """Single bounding-box detection mapped via `ai_labels` (`openapi.yaml`)."""

    class_index: int = Field(ge=0)
    class_name: str
    ingredient_id: UUID | None = None
    ingredient_name: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool = False
    bbox: BBox


class SuggestedIngredient(StrictSchema):
    """Deduplicated non-pantry ingredient suggestion aggregated by `max_confidence`."""

    ingredient_id: UUID
    name_vi: str
    max_confidence: float = Field(ge=0.0, le=1.0)


class DetectResponse(StrictSchema):
    """Response payload for `POST /api/v1/ai/detect` (`openapi.yaml` v1.1.0)."""

    scan_id: UUID | None = None
    model_version: str
    detections: list[Detection]
    suggested_ingredients: list[SuggestedIngredient]
    clear_ingredients: list[SuggestedIngredient] = Field(default_factory=list)
    uncertain_ingredients: list[SuggestedIngredient] = Field(default_factory=list)

    # THUẬT TOÁN: Phân tách danh sách nguyên liệu gợi ý theo ngưỡng HITL tau = 0.80 (`ADR-013` v1.1.0)
    # - `clear_ingredients`: các nguyên liệu có `max_confidence >= 0.80` (`needs_confirmation = false`).
    # - `uncertain_ingredients`: các nguyên liệu có `max_confidence < 0.80` (`needs_confirmation = true`).
    @model_validator(mode="after")
    def populate_confidence_tiers(self) -> DetectResponse:
        if (
            self.suggested_ingredients
            and not self.clear_ingredients
            and not self.uncertain_ingredients
        ):
            self.clear_ingredients = [
                item
                for item in self.suggested_ingredients
                if item.max_confidence >= REVIEW_CONFIDENCE_THRESHOLD
            ]
            self.uncertain_ingredients = [
                item
                for item in self.suggested_ingredients
                if item.max_confidence < REVIEW_CONFIDENCE_THRESHOLD
            ]
        return self


class AIModelOut(StrictSchema):
    id: UUID
    version: str
    family: str
    dataset_version: str
    status: ModelStatus
    confidence_threshold: float = Field(ge=0.0, le=1.0)


class AIModelCreate(StrictSchema):
    version: str = Field(min_length=1)
    family: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    artifact_ref: str = Field(min_length=1)
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)


class AIModelStatusPatch(StrictSchema):
    status: ModelStatus


class PagedAIModels(StrictSchema):
    items: list[AIModelOut]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)


class AILabelOut(StrictSchema):
    id: UUID
    model_id: UUID
    class_index: int = Field(ge=0)
    class_name: str
    ingredient_id: UUID


class AILabelCreate(StrictSchema):
    model_id: UUID
    class_index: int = Field(ge=0)
    class_name: str = Field(min_length=1)
    ingredient_id: UUID


class AILabelPatch(StrictSchema):
    ingredient_id: UUID


class PagedAILabels(StrictSchema):
    items: list[AILabelOut]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)
