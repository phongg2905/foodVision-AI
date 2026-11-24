"""User features & Tier-2 USDA Nutrition schemas matching `docs/03-api/openapi.yaml` (`FR-10`..`FR-12`, `TP 10`, `TP 11`)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.recipes import RecipeSummary


def _validate_uuid_str(v: str) -> str:
    stripped = v.strip()
    try:
        uuid.UUID(stripped)
    except Exception as exc:
        raise ValueError("Giá trị bắt buộc là UUID hợp lệ.") from exc
    return stripped


# ==============================================================================
# 1. Favorites (`FR-10`, `TC-17`, `TC-18`)
# ==============================================================================


class FavoriteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = Field(..., min_length=1)

    @field_validator("recipe_id")
    @classmethod
    def check_uuid(cls, v: str) -> str:
        return _validate_uuid_str(v)


class FavoriteView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    created_at: datetime
    recipe: RecipeSummary


class PagedFavorites(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FavoriteView]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=50)
    offset: int = Field(..., ge=0)


# ==============================================================================
# 2. Recommendation Feedback (`FR-11`, `ADR-012`, `TC-19`, `TC-45`)
# ==============================================================================


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = Field(..., min_length=1)
    scan_id: str | None = None
    rating: int = Field(..., ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("recipe_id")
    @classmethod
    def check_recipe_uuid(cls, v: str) -> str:
        return _validate_uuid_str(v)

    @field_validator("scan_id")
    @classmethod
    def check_optional_scan_uuid(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_uuid_str(v)


class FeedbackView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    recipe_id: str
    rating: int = Field(..., ge=1, le=5)
    created_at: datetime


# ==============================================================================
# 3. Opt-in Scan History (`FR-12`, `TC-20`, `TC-28`, `TC-47`)
# ==============================================================================


class BBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x1: float = Field(..., ge=0.0, le=1.0)
    y1: float = Field(..., ge=0.0, le=1.0)
    x2: float = Field(..., ge=0.0, le=1.0)
    y2: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_bbox_bounds(self) -> BBox:
        if self.x1 >= self.x2 or self.y1 >= self.y2:
            raise ValueError("Tọa độ bbox bắt buộc thỏa mãn 0 <= x1 < x2 <= 1 và 0 <= y1 < y2 <= 1.")
        return self


class Detection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_index: int = Field(..., ge=0)
    class_name: str
    ingredient_id: str | None
    ingredient_name: str | None
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_confirmation: bool = False
    bbox: BBox


class ScanSessionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    model_version: str
    created_at: datetime
    ingredients_count: int = Field(..., ge=0)


class PagedScanSessions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ScanSessionSummary]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=50)
    offset: int = Field(..., ge=0)


class ScanSessionDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    model_version: str
    created_at: datetime
    detections: list[Detection]
    confirmed_ingredient_ids: list[str]
