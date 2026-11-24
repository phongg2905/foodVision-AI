"""Recipe summary, detail, and two-tier USDA nutrition schemas matching OpenAPI 3.1.0 contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import IngredientCategory, NutritionTag

CuisineCode = Literal["VN", "EU", "US"]

NUTRITION_DISCLAIMER_VI = (
    "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế "
    "phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng "
    "và không cam kết miễn trừ dị ứng tuyệt đối."
)

PORTION_SCALING_WARNING_VI = (
    "Thời gian chế biến, mức nhiệt và lượng gia vị nêm nếm có thể không tăng/giảm tuyến tính hoàn toàn "
    "theo phép nhân khẩu phần."
)


class USDANutritionEstimate(BaseModel):
    """Tier-2 quantitative nutrition estimate per recipe/servings (`TP 11`, `ADR-004`)."""

    model_config = ConfigDict(extra="forbid")

    kcal: float = Field(..., ge=0.0)
    protein_g: float = Field(..., ge=0.0)
    fat_g: float = Field(..., ge=0.0)
    carb_g: float = Field(..., ge=0.0)
    source_urls: list[str]
    scaling_factor: float = Field(..., gt=0.0)
    scaling_warning_vi: str | None = None


class RecipeIngredientView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: str
    name_vi: str
    category: IngredientCategory
    is_required: bool
    grams: float | None = None
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
    base_servings: int = Field(default=2, ge=1)
    servings: int = Field(default=2, ge=1)
    ingredients: list[RecipeIngredientView]
    steps: list[RecipeStepView]
    nutrition_evidence: list[NutritionEvidence]
    usda_nutrition: USDANutritionEstimate | None = None
    nutrition_disclaimer_vi: str = NUTRITION_DISCLAIMER_VI
    source_name: str | None
    source_url: str | None
    content_license: str | None
