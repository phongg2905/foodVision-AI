"""Admin CMS Endpoints (`FR-09a`, `FR-13`..`FR-17`, `TC-21`..`TC-26`, `TC-38`, `TC-39`, `TC-41`, `TC-42`, `TC-44`)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.auth import get_required_admin_id
from app.core.database import get_catalog_repo
from app.schemas.admin import (
    AILabel,
    AILabelCreate,
    AILabelPatch,
    AIModel,
    AIModelCreate,
    AIModelStatusPatch,
    AdminRecipeDetail,
    AdminRecipeView,
    IngredientCreate,
    IngredientPatch,
    IngredientTagMapRequest,
    NutritionTagCreate,
    NutritionTagPatch,
    PagedAILabels,
    PagedAIModels,
    PagedAdminRecipes,
    PagedAuditLogs,
    RecipeCreate,
    RecipePatch,
    RecipeStatus,
    RecipeStatusPatch,
)
from app.schemas.catalog import Ingredient, IngredientCategory, NutritionTag, PagedIngredients
from app.schemas.recipes import NutritionEvidence

router = APIRouter()


# ==============================================================================
# 1. Admin Recipes (`FR-13`, `BR-01`, `BR-05`, `ADR-013`)
# ==============================================================================


@router.post(
    "/admin/recipes",
    response_model=AdminRecipeView,
    status_code=201,
    tags=["AdminRecipes"],
)
def create_admin_recipe(
    payload: RecipeCreate,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AdminRecipeView:
    """Create a new recipe in `draft` status (`TC-21`)."""
    return repo.admin_create_recipe(payload=payload, actor_id=admin_id)


@router.get(
    "/admin/recipes",
    response_model=PagedAdminRecipes,
    tags=["AdminRecipes"],
)
def list_admin_recipes(
    status: RecipeStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedAdminRecipes:
    """List recipes across all statuses (`draft`, `published`, `archived`)."""
    items, total = repo.admin_list_recipes(status=status, limit=limit, offset=offset)
    return PagedAdminRecipes(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/admin/recipes/{recipe_id}",
    response_model=AdminRecipeDetail,
    tags=["AdminRecipes"],
)
def get_admin_recipe(
    recipe_id: str,
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AdminRecipeDetail:
    """Retrieve full recipe detail including `draft` / `archived` status and `author_id`."""
    return repo.admin_get_recipe(recipe_id=recipe_id)


@router.patch(
    "/admin/recipes/{recipe_id}",
    response_model=AdminRecipeView,
    tags=["AdminRecipes"],
)
def patch_admin_recipe(
    recipe_id: str,
    payload: RecipePatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AdminRecipeView:
    """Update recipe fields/sublists atomically; enforces `BR-01` if currently `published` (`TC-38`)."""
    return repo.admin_patch_recipe(recipe_id=recipe_id, payload=payload, actor_id=admin_id)


@router.patch(
    "/admin/recipes/{recipe_id}/status",
    response_model=AdminRecipeView,
    tags=["AdminRecipes"],
)
def set_admin_recipe_status(
    recipe_id: str,
    payload: RecipeStatusPatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AdminRecipeView:
    """Publish, archive, or revert a recipe; enforces all 4 `BR-01` conditions when publishing (`TC-22`, `TC-38`)."""
    return repo.admin_set_recipe_status(
        recipe_id=recipe_id, target_status=payload.status, actor_id=admin_id
    )


# ==============================================================================
# 2. Admin Ingredients (`FR-14`, `BR-04`)
# ==============================================================================


@router.get(
    "/admin/ingredients",
    response_model=PagedIngredients,
    tags=["AdminIngredients"],
)
def list_admin_ingredients(
    q: str | None = Query(default=None),
    category: IngredientCategory | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedIngredients:
    """List all ingredients including `is_active = false`."""
    items, total = repo.admin_list_ingredients(
        q=q, category=category, limit=limit, offset=offset
    )
    return PagedIngredients(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/admin/ingredients",
    response_model=Ingredient,
    status_code=201,
    tags=["AdminIngredients"],
)
def create_admin_ingredient(
    payload: IngredientCreate,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> Ingredient:
    """Create a canonical ingredient and normalized Vietnamese aliases (`TC-23`)."""
    return repo.admin_create_ingredient(payload=payload, actor_id=admin_id)


@router.patch(
    "/admin/ingredients/{ingredient_id}",
    response_model=Ingredient,
    tags=["AdminIngredients"],
)
def patch_admin_ingredient(
    ingredient_id: str,
    payload: IngredientPatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> Ingredient:
    """Update ingredient & aliases; blocks deactivation/category changes when in use (`400 INGREDIENT_IN_USE`, `TC-39`)."""
    return repo.admin_patch_ingredient(
        ingredient_id=ingredient_id, payload=payload, actor_id=admin_id
    )


# ==============================================================================
# 3. Admin Nutrition Tags (`FR-16`, `BR-03`)
# ==============================================================================


@router.put(
    "/admin/ingredients/{ingredient_id}/nutrition-tags",
    response_model=list[NutritionEvidence],
    tags=["AdminNutrition"],
)
def set_ingredient_nutrition_tags(
    ingredient_id: str,
    payload: IngredientTagMapRequest,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> list[NutritionEvidence]:
    """Replace all qualitative nutrition tag mappings with mandatory `source_url` (`TC-25`)."""
    return repo.admin_set_ingredient_nutrition_tags(
        ingredient_id=ingredient_id, payload=payload, actor_id=admin_id
    )


@router.get(
    "/admin/nutrition-tags",
    response_model=list[NutritionTag],
    tags=["AdminNutrition"],
)
def list_admin_nutrition_tags(
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> list[NutritionTag]:
    """List all qualitative nutrition tags including `inactive`."""
    return repo.admin_list_nutrition_tags()


@router.post(
    "/admin/nutrition-tags",
    response_model=NutritionTag,
    status_code=201,
    tags=["AdminNutrition"],
)
def create_admin_nutrition_tag(
    payload: NutritionTagCreate,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> NutritionTag:
    """Create a qualitative nutrition tag."""
    return repo.admin_create_nutrition_tag(payload=payload, actor_id=admin_id)


@router.patch(
    "/admin/nutrition-tags/{tag_id}",
    response_model=NutritionTag,
    tags=["AdminNutrition"],
)
def patch_admin_nutrition_tag(
    tag_id: str,
    payload: NutritionTagPatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> NutritionTag:
    """Update a qualitative nutrition tag."""
    return repo.admin_patch_nutrition_tag(
        tag_id=tag_id, payload=payload, actor_id=admin_id
    )


# ==============================================================================
# 4. Admin AI Models & Labels (`FR-15`, `BR-02`, `BR-12`)
# ==============================================================================


@router.get(
    "/admin/ai-models",
    response_model=PagedAIModels,
    tags=["AdminAI"],
)
def list_admin_ai_models(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedAIModels:
    """List registered AI model versions."""
    items, total = repo.admin_list_ai_models(limit=limit, offset=offset)
    return PagedAIModels(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/admin/ai-models",
    response_model=AIModel,
    status_code=201,
    tags=["AdminAI"],
)
def register_admin_ai_model(
    payload: AIModelCreate,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AIModel:
    """Register metadata for a new `draft` AI model (`TC-24`)."""
    return repo.admin_register_ai_model(payload=payload, actor_id=admin_id)


@router.patch(
    "/admin/ai-models/{model_id}/status",
    response_model=AIModel,
    tags=["AdminAI"],
)
def set_admin_ai_model_status(
    model_id: str,
    payload: AIModelStatusPatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AIModel:
    """Activate (`draft` -> `active`) or rollback (`archived` -> `active`) atomically (`TC-24`, `TC-41`)."""
    return repo.admin_set_ai_model_status(
        model_id=model_id, target_status=payload.status, actor_id=admin_id
    )


@router.get(
    "/admin/ai-labels",
    response_model=PagedAILabels,
    tags=["AdminAI"],
)
def list_admin_ai_labels(
    model_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedAILabels:
    """List AI class-to-ingredient mappings."""
    items, total = repo.admin_list_ai_labels(model_id=model_id, limit=limit, offset=offset)
    return PagedAILabels(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/admin/ai-labels",
    response_model=AILabel,
    status_code=201,
    tags=["AdminAI"],
)
def create_admin_ai_label(
    payload: AILabelCreate,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AILabel:
    """Create class-to-ingredient mapping on a `draft` model (`TC-42`, `TC-44`)."""
    return repo.admin_create_ai_label(payload=payload, actor_id=admin_id)


@router.patch(
    "/admin/ai-labels/{label_id}",
    response_model=AILabel,
    tags=["AdminAI"],
)
def patch_admin_ai_label(
    label_id: str,
    payload: AILabelPatch,
    admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> AILabel:
    """Update ingredient mapping on a `draft` model (`TC-42`, `TC-44`)."""
    return repo.admin_patch_ai_label(
        label_id=label_id, payload=payload, actor_id=admin_id
    )


# ==============================================================================
# 5. Admin Audit Logs (`FR-17`, `BR-10`)
# ==============================================================================


@router.get(
    "/admin/audit-logs",
    response_model=PagedAuditLogs,
    tags=["AdminAudit"],
)
def list_admin_audit_logs(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    _admin_id: str = Depends(get_required_admin_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedAuditLogs:
    """List Admin CMS mutation audit logs without secrets/tokens (`TC-26`)."""
    items, total = repo.admin_list_audit_logs(limit=limit, offset=offset)
    return PagedAuditLogs(items=items, total=total, limit=limit, offset=offset)
