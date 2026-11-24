"""Admin CMS schemas matching `docs/03-api/openapi.yaml` (`FR-13`..`FR-17`, `ADR-013`)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.catalog import IngredientCategory
from app.schemas.recipes import CuisineCode, RecipeDetail

RecipeStatus = Literal["draft", "published", "archived"]
IngredientRole = Literal["core", "secondary", "spice", "optional"]
DishRole = Literal["main", "sub"]
AIModelStatus = Literal["draft", "active", "archived"]
AuditEntityType = Literal["recipes", "ingredients", "ai_models", "ai_labels", "nutrition_tags"]

_HTTP_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
_SENSITIVE_KEY_SUBSTRINGS = (
    "secret",
    "token",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "service_role",
    "jwt",
)


def scrub_audit_payload(data: Any) -> Any:
    """Recursively strip secrets/tokens before persisting into `audit_logs` (`FR-17`, `BR-10`)."""
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            key_lower = str(k).lower()
            if any(s in key_lower for s in _SENSITIVE_KEY_SUBSTRINGS):
                continue
            cleaned[str(k)] = scrub_audit_payload(v)
        return cleaned
    if isinstance(data, list):
        return [scrub_audit_payload(item) for item in data]
    if isinstance(data, datetime):
        return data.isoformat()
    return data


# ==============================================================================
# 1. Admin Recipes (`FR-13`, `BR-01`, `BR-05`, `ADR-013`)
# ==============================================================================


class RecipeIngredientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: str = Field(..., min_length=1)
    is_required: bool
    role: IngredientRole | None = None
    dish_role: DishRole | None = None
    weight: float | None = Field(default=None, ge=0.0)
    grams: float | None = Field(default=None, gt=0.0)
    display_quantity: str | None = None
    sort_order: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_role_weight_consistency(self) -> RecipeIngredientInput:
        if self.is_required:
            if self.role == "optional":
                raise ValueError("Nguyên liệu bắt buộc (is_required=true) không được đặt role='optional'.")
            if self.weight is not None and self.weight <= 0:
                raise ValueError("Nguyên liệu bắt buộc (is_required=true) phải có weight > 0.")
        else:
            if self.role is not None and self.role != "optional":
                raise ValueError("Nguyên liệu tùy chọn (is_required=false) phải có role='optional'.")
        return self


class RecipeStepInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_no: int = Field(..., ge=1)
    instruction: str = Field(..., min_length=1)
    estimated_minutes: int | None = Field(default=None, ge=0)

    @field_validator("instruction")
    @classmethod
    def check_nonblank_instruction(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Hướng dẫn bước nấu không được để trống.")
        return v.strip()


class RecipeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., min_length=1)
    name_vi: str = Field(..., min_length=1)
    description: str | None = None
    cuisine_code: CuisineCode
    country_code: str | None = None
    prep_minutes: int = Field(..., ge=0)
    cook_minutes: int = Field(..., ge=0)
    cover_image_path: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    content_license: str | None = None
    ingredients: list[RecipeIngredientInput]
    steps: list[RecipeStepInput]

    @field_validator("slug", "name_vi")
    @classmethod
    def check_nonblank_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Trường văn bản bắt buộc không được để trống.")
        return v.strip()

    @model_validator(mode="after")
    def validate_recipe_invariants(self) -> RecipeCreate:
        if self.prep_minutes + self.cook_minutes <= 0:
            raise ValueError("Tổng thời gian chế biến (prep_minutes + cook_minutes) bắt buộc > 0 (ADR-013).")
        ing_ids = [it.ingredient_id for it in self.ingredients]
        if len(ing_ids) != len(set(ing_ids)):
            raise ValueError("Danh sách ingredients không được lặp lại cùng một ingredient_id.")
        step_nos = [st.step_no for st in self.steps]
        if len(step_nos) != len(set(step_nos)):
            raise ValueError("Danh sách steps không được trùng lặp step_no.")
        return self


class RecipePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = Field(default=None, min_length=1)
    name_vi: str | None = Field(default=None, min_length=1)
    description: str | None = None
    cuisine_code: CuisineCode | None = None
    country_code: str | None = None
    prep_minutes: int | None = Field(default=None, ge=0)
    cook_minutes: int | None = Field(default=None, ge=0)
    cover_image_path: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    content_license: str | None = None
    ingredients: list[RecipeIngredientInput] | None = None
    steps: list[RecipeStepInput] | None = None

    @field_validator("slug", "name_vi")
    @classmethod
    def check_optional_nonblank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Trường văn bản không được chỉ chứa khoảng trắng.")
        return v.strip() if v is not None else None

    @model_validator(mode="after")
    def validate_sublists(self) -> RecipePatch:
        if self.ingredients is not None:
            ing_ids = [it.ingredient_id for it in self.ingredients]
            if len(ing_ids) != len(set(ing_ids)):
                raise ValueError("Danh sách ingredients không được lặp lại cùng một ingredient_id.")
        if self.steps is not None:
            step_nos = [st.step_no for st in self.steps]
            if len(step_nos) != len(set(step_nos)):
                raise ValueError("Danh sách steps không được trùng lặp step_no.")
        return self


class RecipeStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RecipeStatus


class AdminRecipeView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    name_vi: str
    status: RecipeStatus
    updated_at: datetime


class PagedAdminRecipes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AdminRecipeView]
    total: int
    limit: int
    offset: int


class AdminRecipeDetail(RecipeDetail):
    model_config = ConfigDict(extra="forbid")

    status: RecipeStatus
    author_id: str
    updated_at: datetime


# ==============================================================================
# 2. Admin Ingredients (`FR-14`, `BR-04`)
# ==============================================================================


class IngredientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., min_length=1)
    name_vi: str = Field(..., min_length=1)
    category: IngredientCategory
    is_active: bool = True
    aliases: list[str] = Field(default_factory=list)

    @field_validator("slug", "name_vi")
    @classmethod
    def check_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("slug và name_vi không được để trống.")
        return v.strip()

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        for alias in v:
            stripped = alias.strip()
            if not stripped:
                raise ValueError("Alias nguyên liệu không được để chuỗi rỗng.")
            if stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned


class IngredientPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = Field(default=None, min_length=1)
    name_vi: str | None = Field(default=None, min_length=1)
    category: IngredientCategory | None = None
    is_active: bool | None = None
    aliases: list[str] | None = None

    @field_validator("slug", "name_vi")
    @classmethod
    def check_optional_nonblank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("slug và name_vi không được để trống.")
        return v.strip() if v is not None else None

    @field_validator("aliases")
    @classmethod
    def clean_optional_aliases(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned: list[str] = []
        for alias in v:
            stripped = alias.strip()
            if not stripped:
                raise ValueError("Alias nguyên liệu không được để chuỗi rỗng.")
            if stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned


# ==============================================================================
# 3. Admin Nutrition Tags (`FR-16`, `BR-03`)
# ==============================================================================


class NutritionTagCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    name_vi: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    is_active: bool = True

    @field_validator("code", "name_vi", "description")
    @classmethod
    def check_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code, name_vi, description không được để trống.")
        return v.strip()


class NutritionTagPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_vi: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None

    @field_validator("name_vi", "description")
    @classmethod
    def check_optional_nonblank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Trường văn bản không được để trống.")
        return v.strip() if v is not None else None


class IngredientTagMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nutrition_tag_id: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    note: str | None = None

    @field_validator("source_url")
    @classmethod
    def validate_http_source_url(cls, v: str) -> str:
        stripped = v.strip()
        if not _HTTP_URL_RE.match(stripped):
            raise ValueError("source_url bắt buộc là đường dẫn HTTP/HTTPS hợp lệ (FR-16, BR-03).")
        return stripped


class IngredientTagMapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[IngredientTagMapping]

    @model_validator(mode="after")
    def check_unique_tag_ids(self) -> IngredientTagMapRequest:
        tag_ids = [t.nutrition_tag_id for t in self.tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise ValueError("Danh sách tags không được lặp lại cùng một nutrition_tag_id.")
        return self


# ==============================================================================
# 4. Admin AI Models & Labels (`FR-15`, `BR-02`, `BR-12`)
# ==============================================================================


class AIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    family: str
    dataset_version: str
    status: AIModelStatus
    confidence_threshold: float


class AIModelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., min_length=1)
    family: str = Field(..., min_length=1)
    dataset_version: str = Field(..., min_length=1)
    artifact_ref: str = Field(..., min_length=1)
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    class_count: int = Field(default=20, ge=1, le=200)

    @field_validator("version", "family", "dataset_version", "artifact_ref")
    @classmethod
    def check_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Metadata mô hình AI không được để trống.")
        return v.strip()


class AIModelStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AIModelStatus


class PagedAIModels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AIModel]
    total: int
    limit: int
    offset: int


class AILabel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    model_id: str
    class_index: int
    class_name: str
    ingredient_id: str


class AILabelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(..., min_length=1)
    class_index: int = Field(..., ge=0)
    class_name: str = Field(..., min_length=1)
    ingredient_id: str = Field(..., min_length=1)

    @field_validator("class_name")
    @classmethod
    def check_nonblank_class_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("class_name không được để trống.")
        return v.strip()


class AILabelPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingredient_id: str = Field(..., min_length=1)


class PagedAILabels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AILabel]
    total: int
    limit: int
    offset: int


# ==============================================================================
# 5. Admin Audit Logs (`FR-17`, `BR-10`)
# ==============================================================================


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime


class PagedAuditLogs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AuditLog]
    total: int
    limit: int
    offset: int
