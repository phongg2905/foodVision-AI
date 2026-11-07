"""Recipe Catalog Endpoints (`GET /api/v1/recipes`, `GET /api/v1/recipes/{recipe_id}`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.catalog import NutritionTag
from app.schemas.recipes import (
    NutritionEvidence,
    PagedRecipes,
    RecipeDetail,
    RecipeIngredientView,
    RecipeStepView,
    RecipeSummary,
)

router = APIRouter(tags=["Recipes"])


@router.get("/recipes", response_model=PagedRecipes)
def list_recipes(
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm tên công thức"),
    cuisine_code: str | None = Query(default=None, description="Mã ẩm thực (VN, EU, US)"),
    max_total_minutes: int | None = Query(
        default=None, ge=1, le=720, description="Thời gian chế biến tối đa (phút)"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> PagedRecipes:
    """Search and filter published recipes (`TP 03`, `TP 13`, `TC-01`, `TC-03`)."""
    records, total = repo.list_published_recipes(
        q=q,
        cuisine_code=cuisine_code.strip().upper() if cuisine_code else None,
        max_total_minutes=max_total_minutes,
        limit=limit,
        offset=offset,
    )
    items = [
        RecipeSummary(
            id=r.id,
            slug=r.slug,
            name_vi=r.name_vi,
            cuisine_code=r.cuisine_code,  # type: ignore[arg-type]
            prep_minutes=r.prep_minutes,
            cook_minutes=r.cook_minutes,
            total_minutes=r.total_minutes,
            cover_image_url=r.cover_image_url,
        )
        for r in records
    ]
    return PagedRecipes(items=items, total=total, limit=limit, offset=offset)


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe_detail(
    recipe_id: UUID = Path(..., description="UUID công thức món ăn"),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> RecipeDetail:
    """Retrieve full details of a published recipe (`TC-02`, `TC-04`)."""
    rec = repo.get_published_recipe_by_id(str(recipe_id))
    if rec is None:
        raise AppError(
            status_code=404,
            code="RECIPE_NOT_FOUND",
            message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
            details={"recipe_id": str(recipe_id)},
        )

    return RecipeDetail(
        id=rec.id,
        slug=rec.slug,
        name_vi=rec.name_vi,
        cuisine_code=rec.cuisine_code,  # type: ignore[arg-type]
        prep_minutes=rec.prep_minutes,
        cook_minutes=rec.cook_minutes,
        total_minutes=rec.total_minutes,
        cover_image_url=rec.cover_image_url,
        description=rec.description,
        country_code=rec.country_code,
        ingredients=[
            RecipeIngredientView(
                ingredient_id=ing.ingredient_id,
                name_vi=ing.name_vi,
                category=ing.category,  # type: ignore[arg-type]
                is_required=ing.is_required,
                display_quantity=ing.display_quantity,
                sort_order=ing.sort_order,
            )
            for ing in rec.ingredients
        ],
        steps=[
            RecipeStepView(
                step_no=st.step_no,
                instruction=st.instruction,
                estimated_minutes=st.estimated_minutes,
            )
            for st in rec.steps
        ],
        nutrition_evidence=[
            NutritionEvidence(
                tag=NutritionTag(
                    id=ne.tag_id,
                    code=ne.tag_code,
                    name_vi=ne.tag_name_vi,
                    description=ne.tag_description,
                    is_active=ne.tag_is_active,
                ),
                source_urls=ne.source_urls,
                note=ne.note,
            )
            for ne in rec.nutrition_evidence
        ],
        source_name=rec.source_name,
        source_url=rec.source_url,
        content_license=rec.content_license,
    )
