"""Schemas for Recommendation Engine & POST /api/v1/recommendations (`openapi.yaml` & `FV-REC-001`)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.reasoning import AvailabilityV1, RecipeReasoningStatus
from app.schemas.recipes import CuisineCode, RecipeSummary


class RecommendRequest(BaseModel):
    """Request payload for POST /api/v1/recommendations (`openapi.yaml` lines 1822-1869)."""

    model_config = ConfigDict(extra="forbid")

    ingredient_ids: list[str] = Field(min_length=1)
    excluded_pantry_ids: list[str] = Field(default_factory=list)
    max_total_minutes: int | None = Field(default=None, ge=1, le=720)
    cuisine_codes: list[CuisineCode] = Field(default_factory=list)
    preferred_cuisine_codes: list[CuisineCode] = Field(default_factory=list)
    include_missing: bool = True
    limit: int = Field(default=20, ge=1, le=50)
    scan_id: str | None = None

    @field_validator("ingredient_ids", "excluded_pantry_ids")
    @classmethod
    def check_unique_items(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("Danh sách UUID không được chứa phần tử trùng lặp (uniqueItems: true).")
        return v


class ScoreBreakdown(BaseModel):
    """4-component linear breakdown for MVP Scoring v1.0 (`openapi.yaml` lines 1870-1894)."""

    model_config = ConfigDict(extra="forbid")

    C: float = Field(ge=0.0, le=1.0)
    E: float = Field(ge=0.0, le=1.0)
    T: float = Field(ge=0.0, le=1.0)
    P: float = Field(ge=0.0, le=1.0)


class RecommendationItem(BaseModel):
    """Ranked recommendation item (`openapi.yaml` lines 1895-1930)."""

    model_config = ConfigDict(extra="forbid")

    recipe: RecipeSummary
    availability: AvailabilityV1
    score: float = Field(ge=0.0, le=100.0)
    matched_ingredient_ids: list[str]
    missing_required_ingredient_ids: list[str]
    missing_optional_ingredient_ids: list[str]
    score_breakdown: ScoreBreakdown
    explanation_vi: str


class RecommendResponse(BaseModel):
    """Response envelope for POST /api/v1/recommendations (`openapi.yaml` lines 1931-1950)."""

    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=50)


class MCDAFeatures(BaseModel):
    """5 normalized features in [0, 1] for Scoring v1.1 MCDA (`TP 07`)."""

    model_config = ConfigDict(extra="forbid")

    C: float = Field(ge=0.0, le=1.0)
    G: float = Field(ge=0.0, le=1.0)
    T: float = Field(ge=0.0, le=1.0)
    P: float = Field(ge=0.0, le=1.0)
    Q: float = Field(ge=0.0, le=1.0)


class MCDAContributions(BaseModel):
    """Exact additive point contributions summing to score_base (`TP 14` XAI)."""

    model_config = ConfigDict(extra="forbid")

    C: float
    G: float
    T: float
    P: float
    Q: float


class MCDAEvaluation(BaseModel):
    """Extended Scoring v1.1 evaluation output (`TP 05`, `TP 07`, `TP 14`)."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    state: RecipeReasoningStatus
    score_base: float
    features: MCDAFeatures
    contributions: MCDAContributions

