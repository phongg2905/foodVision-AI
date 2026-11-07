"""Recipe summary and detail schemas matching OpenAPI 3.1.0 contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.catalog import IngredientCategory, NutritionTag

CuisineCode = Literal["VN", "EU", "US"]


class RecipeIngredientView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: str
    name_vi: str
    category: IngredientCategory
    is_required: bool
    display_quantity: str | None
    sort_order: int


class RecipeStepView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_no: int
    instruction: str
    estimated_minutes: int | None


class NutritionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: NutritionTag
    source_urls: list[str]
    note: str | None


class RecipeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    name_vi: str
    cuisine_code: CuisineCode
    prep_minutes: int
    cook_minutes: int
    total_minutes: int
    cover_image_url: str | None


class PagedRecipes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecipeSummary]
    total: int
    limit: int
    offset: int


class RecipeDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    name_vi: str
    cuisine_code: CuisineCode
    prep_minutes: int
    cook_minutes: int
    total_minutes: int
    cover_image_url: str | None
    description: str | None
    country_code: str | None
    ingredients: list[RecipeIngredientView]
    steps: list[RecipeStepView]
    nutrition_evidence: list[NutritionEvidence]
    source_name: str | None
    source_url: str | None
    content_license: str | None

