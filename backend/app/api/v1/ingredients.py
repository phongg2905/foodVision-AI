"""Ingredient Catalog Endpoint (`GET /api/v1/ingredients`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.catalog import IngredientCategory, PagedIngredients

router = APIRouter(tags=["Catalog"])


@router.get("/ingredients", response_model=PagedIngredients)
def list_ingredients(
    response: Response,
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm tên/bí danh nguyên liệu"),
    category: IngredientCategory | None = Query(
        default=None,
        description="Nhóm nguyên liệu (vegetable, protein, seafood, spice, pantry, other)",
    ),
    exclude_pantry: bool = Query(default=False, description="Ẩn nguyên liệu gia vị sẵn có (pantry)"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> PagedIngredients:
    """List or search active ingredients (`TP 03`, `TP 13`, `TC-10`, `TC-36`, `NFR-03`)."""
    # Rule TC-10 & TC-36(4): category == "pantry" and exclude_pantry == True is a logical contradiction
    if category == "pantry" and exclude_pantry:
        raise AppError(
            status_code=422,
            code="INVALID_QUERY_PARAMS",
            message="Tham số truy vấn mâu thuẫn: không thể vừa lọc category='pantry' vừa bật exclude_pantry=true.",
            details={
                "params": ["category", "exclude_pantry"],
                "reason": "conflicting_pantry_filters",
                "category": category,
                "exclude_pantry": exclude_pantry,
            },
        )

    # Rule NFR-03 & TC-36(1..2): Cache-Control public max-age=300 without `q`, no-store when `q` is present
    if not q or not q.strip():
        response.headers["Cache-Control"] = "public, max-age=300"
    else:
        response.headers["Cache-Control"] = "no-store"

    records, total = repo.list_active_ingredients(
        q=q,
        category=category,
        exclude_pantry=exclude_pantry,
        limit=limit,
        offset=offset,
    )
    items = [r.to_schema() for r in records]
    return PagedIngredients(items=items, total=total, limit=limit, offset=offset)
