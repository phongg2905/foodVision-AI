"""Schemas for Open-World 3-Valued Reasoning & Hard Constraints (TP 04)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipes import CuisineCode

IngredientTriState = Literal["confirmed_available", "confirmed_missing", "unknown"]
RecipeReasoningStatus = Literal["BLOCKED", "READY", "UNKNOWN", "MISSING_CONFIRMED"]
AvailabilityV1 = Literal["ready", "missing"]


class ReasoningInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_ids: list[str] = Field(min_length=1)
    excluded_pantry_ids: list[str] = Field(default_factory=list)
    missing_ingredient_ids: list[str] = Field(default_factory=list)
    max_total_minutes: int | None = Field(default=None, ge=1, le=720)
    cuisine_codes: list[CuisineCode] = Field(default_factory=list)
    preferred_cuisine_codes: list[CuisineCode] = Field(default_factory=list)
    excluded_allergen_ids: list[str] = Field(default_factory=list)
    available_equipment: list[str] | None = None
    include_missing: bool = True


class RecipeReasoningEvaluation(BaseModel):
    """Result of evaluating a published recipe under TP 04 Open-World 3-State Reasoning."""

    recipe_id: str
    status_v1_1: RecipeReasoningStatus
    availability_v1_0: AvailabilityV1 | None
    diet_ok: bool
    equip_ok: bool
    time_ok: bool
    cuisine_ok: bool
    has_main_overlap: bool
    matched_main_ids: list[str]
    matched_optional_main_ids: list[str]
    missing_required_main_ids: list[str]
    missing_pantry_ids: list[str]
    missing_required_ingredient_ids: list[str]
    missing_optional_ingredient_ids: list[str]
    ingredient_states: dict[str, IngredientTriState]
    blocked_reasons: list[str]

