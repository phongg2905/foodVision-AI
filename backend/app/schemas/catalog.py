"""Catalog schemas (Ingredients, NutritionTags)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

IngredientCategory = Literal["vegetable", "protein", "seafood", "spice", "pantry", "other"]


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    name_vi: str
    category: IngredientCategory
    is_active: bool


class PagedIngredients(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Ingredient]
    total: int
    limit: int
    offset: int


class NutritionTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    code: str
    name_vi: str
    description: str
    is_active: bool

