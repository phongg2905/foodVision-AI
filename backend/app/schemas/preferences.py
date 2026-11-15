"""Schemas for 3-list Ingredient Personalization Profile (`user_preferences` — `ADR-013`)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserPreferencesView(BaseModel):
    """Response payload for GET / PUT /api/v1/preferences."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    allergic_ingredient_ids: list[str] = Field(default_factory=list)
    kitchen_spice_ids: list[str] = Field(default_factory=list)
    favorite_ingredient_ids: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class UserPreferencesUpdate(BaseModel):
    """Request payload for PUT /api/v1/preferences (`ADR-013`)."""

    model_config = ConfigDict(extra="forbid")

    allergic_ingredient_ids: list[str] | None = None
    kitchen_spice_ids: list[str] | None = None
    favorite_ingredient_ids: list[str] | None = None

    @field_validator(
        "allergic_ingredient_ids",
        "kitchen_spice_ids",
        "favorite_ingredient_ids",
    )
    @classmethod
    def check_unique_items(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Danh sách UUID không được chứa phần tử trùng lặp (uniqueItems: true).")
        return v
