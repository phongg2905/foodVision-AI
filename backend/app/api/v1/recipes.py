"""Recipe Catalog & Two-Tier USDA Nutrition Endpoints (`GET /api/v1/recipes`, `GET /api/v1/recipes/{recipe_id}`)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.recipes import CuisineCode, PagedRecipes, RecipeDetail

router = APIRouter(tags=["Recipes"])


@router.get("/recipes", response_model=PagedRecipes)
def list_recipes(
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm tên công thức"),
    cuisine_code: CuisineCode | None = Query(default=None, description="Mã ẩm thực (VN, EU, US)"),
    max_total_minutes: int | None = Query(
        default=None, ge=1, le=720, description="Thời gian chế biến tối đa (phút)"
    ),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> PagedRecipes:
    """Search and filter published recipes (`TP 03`, `TP 13`, `TC-01`, `TC-02`)."""
    records, total = repo.list_published_recipes(
        q=q,
        cuisine_code=cuisine_code,
        max_total_minutes=max_total_minutes,
        limit=limit,
        offset=offset,
    )
    items = [r.to_summary() for r in records]
    return PagedRecipes(items=items, total=total, limit=limit, offset=offset)


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe_detail(
    recipe_id: UUID = Path(..., description="UUID công thức món ăn"),
    servings: int | None = Query(
        default=None,
        ge=1,
        le=50,
        description="Số khẩu phần muốn quy đổi (mặc định giữ khẩu phần gốc base_servings của món)",
    ),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> RecipeDetail:
    """Retrieve full details of a published recipe with Tier-1 tags & Tier-2 USDA estimate (`TC-03`, `TC-15`, `DEF-09`)."""
    rec = repo.get_published_recipe_by_id(str(recipe_id))
    if rec is None:
        raise AppError(
            status_code=404,
            code="RECIPE_NOT_FOUND",
            message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
            details={"recipe_id": str(recipe_id)},
        )
    ing_ids = [ri.ingredient_id for ri in rec.ingredients]
    nutrient_map = repo.get_ingredient_nutrients_by_ids(ing_ids)
    return rec.to_detail(servings=servings, nutrient_map=nutrient_map)
