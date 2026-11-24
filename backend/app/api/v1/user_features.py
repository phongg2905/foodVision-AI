"""Stage 4 User Endpoints (`/favorites`, `/feedback`, `/scan-sessions`) (`FR-10`..`FR-12`, `TC-17`..`TC-20`, `TC-28`, `TC-45`, `TC-47`)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.auth import get_required_user_id
from app.core.database import get_catalog_repo
from app.schemas.user_features import (
    FavoriteCreate,
    FavoriteView,
    FeedbackCreate,
    FeedbackView,
    PagedFavorites,
    PagedScanSessions,
    ScanSessionDetail,
)

router = APIRouter()


# ==============================================================================
# 1. Favorites (`FR-10`, `TC-17`, `TC-18`, `SEC-01`)
# ==============================================================================


@router.get("/favorites", tags=["Favorites"], response_model=PagedFavorites)
def list_favorites(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedFavorites:
    items, total = repo.list_user_favorites(user_id=user_id, limit=limit, offset=offset)
    return PagedFavorites(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/favorites",
    tags=["Favorites"],
    response_model=FavoriteView,
    responses={
        201: {"model": FavoriteView, "description": "Tạo mới"},
        200: {"model": FavoriteView, "description": "Đã có sẵn (idempotent)"},
    },
)
def add_favorite(
    payload: FavoriteCreate,
    response: Response,
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> FavoriteView:
    fav, is_created = repo.add_user_favorite(user_id=user_id, recipe_id=payload.recipe_id)
    response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return fav


@router.delete(
    "/favorites/{recipe_id}",
    tags=["Favorites"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_favorite(
    recipe_id: UUID = Path(..., description="UUID công thức món ăn"),
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> Response:
    repo.remove_user_favorite(user_id=user_id, recipe_id=str(recipe_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# 2. Recommendation Feedback Upsert (`FR-11`, `ADR-012`, `TC-19`, `TC-45`, `SEC-06`)
# ==============================================================================


@router.post(
    "/feedback",
    tags=["Feedback"],
    response_model=FeedbackView,
    responses={
        201: {"model": FeedbackView, "description": "Tạo mới đánh giá"},
        200: {
            "model": FeedbackView,
            "description": "Cập nhật đánh giá hiện có trong cùng ngữ cảnh (user_id, recipe_id, scan_id)",
        },
    },
)
def submit_feedback(
    payload: FeedbackCreate,
    response: Response,
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> FeedbackView:
    fb, is_created = repo.upsert_user_feedback(user_id=user_id, payload=payload)
    response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return fb


# ==============================================================================
# 3. Opt-in Scan History (`FR-12`, `TC-20`, `TC-28`, `TC-47`, `SEC-06`)
# ==============================================================================


@router.get("/scan-sessions", tags=["ScanHistory"], response_model=PagedScanSessions)
def list_scan_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> PagedScanSessions:
    items, total = repo.list_user_scan_sessions(user_id=user_id, limit=limit, offset=offset)
    return PagedScanSessions(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/scan-sessions/{scan_id}",
    tags=["ScanHistory"],
    response_model=ScanSessionDetail,
)
def get_scan_session(
    scan_id: UUID = Path(..., description="UUID phiên quét đã lưu"),
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> ScanSessionDetail:
    return repo.get_user_scan_session_detail(user_id=user_id, scan_id=str(scan_id))


@router.delete(
    "/scan-sessions/{scan_id}",
    tags=["ScanHistory"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_scan_session(
    scan_id: UUID = Path(..., description="UUID phiên quét cần xóa"),
    user_id: str = Depends(get_required_user_id),
    repo: Any = Depends(get_catalog_repo),
) -> Response:
    repo.delete_user_scan_session(user_id=user_id, scan_id=str(scan_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
