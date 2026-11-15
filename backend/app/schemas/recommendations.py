"""Schemas for Recommendation Engine & POST /api/v1/recommendations (`openapi.yaml` & `ADR-013`)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.reasoning import AvailabilityV1, RecipeReasoningStatus
from app.schemas.recipes import CuisineCode, RecipeSummary


class RecommendRequest(BaseModel):
    """Request payload for POST /api/v1/recommendations (`openapi.yaml` v1.1.0)."""

    model_config = ConfigDict(extra="forbid")

    ingredient_ids: list[str] = Field(min_length=1)
    main_ingredient_ids: list[str] = Field(default_factory=list)
    desired_hours: float = Field(default=100.0, gt=0.0)
    allergic_ingredient_ids: list[str] = Field(default_factory=list)
    kitchen_spice_ids: list[str] | None = None
    excluded_pantry_ids: list[str] = Field(default_factory=list)
    favorite_ingredient_ids: list[str] = Field(default_factory=list)
    max_total_minutes: int | None = Field(default=None, ge=1, le=720)
    cuisine_codes: list[CuisineCode] = Field(default_factory=list)
    include_missing: bool = True
    diversify: bool = False
    limit: int = Field(default=20, ge=1, le=50)
    scan_id: str | None = None

    @field_validator(
        "ingredient_ids",
        "main_ingredient_ids",
        "allergic_ingredient_ids",
        "excluded_pantry_ids",
        "favorite_ingredient_ids",
    )
    @classmethod
    def check_unique_items(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("Danh sách UUID không được chứa phần tử trùng lặp (uniqueItems: true).")
        return v

    @field_validator("kitchen_spice_ids")
    @classmethod
    def check_unique_optional_items(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Danh sách UUID không được chứa phần tử trùng lặp (uniqueItems: true).")
        return v


class ScoreBreakdown(BaseModel):
    """4 normalized criteria in [0, 1] for unified MCDA (`C, G, T, P` — `ADR-013`)."""

    model_config = ConfigDict(extra="forbid")

    C: float = Field(ge=0.0, le=1.0)
    G: float = Field(ge=0.0, le=1.0)
    T: float = Field(ge=0.0, le=1.0)
    P: float = Field(ge=0.0, le=1.0)


class ScoreContributions(BaseModel):
    """Exact additive XAI point contributions summing to score (`50*C + 25*G + 15*T + 10*P`)."""

    model_config = ConfigDict(extra="forbid")

    C: float = Field(ge=0.0, le=50.0)
    G: float = Field(ge=0.0, le=25.0)
    T: float = Field(ge=0.0, le=15.0)
    P: float = Field(ge=0.0, le=10.0)


class RecommendationItem(BaseModel):
    """Ranked recommendation item (`openapi.yaml` v1.1.0)."""

    model_config = ConfigDict(extra="forbid")

    recipe: RecipeSummary
    availability: AvailabilityV1
    reasoning_status: RecipeReasoningStatus = "READY"
    score: float = Field(ge=0.0, le=100.0)
    matched_ingredient_ids: list[str]
    missing_required_ingredient_ids: list[str]
    missing_optional_ingredient_ids: list[str]
    score_breakdown: ScoreBreakdown
    score_contributions: ScoreContributions
    explanation_vi: str


class RecommendResponse(BaseModel):
    """Response envelope for POST /api/v1/recommendations."""

    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=50)
