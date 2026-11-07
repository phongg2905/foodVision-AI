"""Ingredient Catalog Endpoint (`GET /api/v1/ingredients`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.catalog import Ingredient, PagedIngredients

router = APIRouter(tags=["Catalog & Search"])


@router.get("/ingredients", response_model=PagedIngredients)
def list_ingredients(
    response: Response,
    q: str | None = Query(default=None, description="Từ khóa tìm kiếm tên/bí danh nguyên liệu"),
    category: str | None = Query(
        default=None,
        description="Nhóm nguyên liệu (vegetable, protein, seafood, spice, pantry, other)",
    ),
    exclude_pantry: bool = Query(default=False, description="Ẩn nguyên liệu gia vị sẵn có (pantry)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> PagedIngredients:
    """List or search active ingredients (`TP 03`, `TP 13`, `TC-10`, `NFR-03`)."""
    # Rule TC-10: category == "pantry" and exclude_pantry == True is a logical contradiction
    if category is not None and category.strip().lower() == "pantry" and exclude_pantry:
        raise AppError(
            status_code=422,
            code="INVALID_QUERY_PARAMS",
            message="Tham số truy vấn mâu thuẫn: không thể vừa lọc category='pantry' vừa bật exclude_pantry=true.",
            details={"category": category, "exclude_pantry": exclude_pantry},
        )

    # Rule NFR-03: Cache-Control for static catalog listing without search query
    if not q or not q.strip():
        response.headers["Cache-Control"] = "public, max-age=300"

    records, total = repo.list_active_ingredients(
        q=q,
        category=category.strip().lower() if category else None,
        exclude_pantry=exclude_pantry,
        limit=limit,
        offset=offset,
    )
    items = [
        Ingredient(
            id=r.id,
            slug=r.slug,
            name_vi=r.name_vi,
            category=r.category,  # type: ignore[arg-type]
            is_active=r.is_active,
        )
        for r in records
    ]
    return PagedIngredients(items=items, total=total, limit=limit, offset=offset)
