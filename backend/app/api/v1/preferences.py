"""User Preferences Endpoints (`GET /api/v1/preferences`, `PUT /api/v1/preferences` — `ADR-013`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_required_user_id
from app.core.database import CatalogRepository, UserPreferencesRecord, get_catalog_repo
from app.core.errors import AppError
from app.schemas.preferences import UserPreferencesUpdate, UserPreferencesView

router = APIRouter(tags=["Preferences"])


def _validate_preference_ingredient_lists(
    repo: CatalogRepository,
    allergic_ids: list[str],
    kitchen_spice_ids: list[str],
    favorite_ids: list[str],
) -> None:
    """Validate that all ingredient UUIDs exist & are active, and `kitchen_spice_ids` strictly belong to `category == 'pantry'`."""
    all_ids = list(dict.fromkeys(allergic_ids + kitchen_spice_ids + favorite_ids))
    if not all_ids:
        return
    found_map = repo.get_ingredients_by_ids(all_ids)
    invalid_ids: list[str] = []
    reason: str | None = None

    def _mark(iid: str, r: str) -> None:
        nonlocal reason
        if iid not in invalid_ids:
            invalid_ids.append(iid)
        if reason is None:
            reason = r

    for iid in allergic_ids:
        rec = found_map.get(iid)
        if rec is None or not rec.is_active:
            _mark(iid, "unknown_or_inactive_id")

    for sid in kitchen_spice_ids:
        rec = found_map.get(sid)
        if rec is None or not rec.is_active:
            _mark(sid, "unknown_or_inactive_id")
        elif rec.category != "pantry":
            _mark(sid, "non_pantry_in_kitchen_spices")

    for fid in favorite_ids:
        rec = found_map.get(fid)
        if rec is None or not rec.is_active:
            _mark(fid, "unknown_or_inactive_id")

    if invalid_ids:
        raise AppError(
            status_code=422,
            code="INVALID_INGREDIENTS",
            message="Một hoặc nhiều UUID nguyên liệu cá nhân hóa không tồn tại, đang ngưng hoạt động hoặc sai phân nhóm gia vị nền.",
            details={
                "invalid_ids": invalid_ids,
                "invalid_ingredient_ids": invalid_ids,
                "reason": reason or "unknown_or_inactive_id",
            },
        )


@router.get("/preferences", response_model=UserPreferencesView)
def get_my_preferences(
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> UserPreferencesView:
    """Retrieve the authenticated user's 3-list ingredient personalization profile (`ADR-013`)."""
    existing = repo.get_user_preferences(user_id)
    if existing is None:
        default_spices = sorted(repo.get_active_pantry_ingredients().keys())
        return UserPreferencesView(
            user_id=user_id,
            allergic_ingredient_ids=[],
            kitchen_spice_ids=default_spices,
            favorite_ingredient_ids=[],
            updated_at=None,
        )
    return UserPreferencesView(
        user_id=existing.user_id,
        allergic_ingredient_ids=list(existing.allergic_ingredient_ids),
        kitchen_spice_ids=list(existing.kitchen_spice_ids),
        favorite_ingredient_ids=list(existing.favorite_ingredient_ids),
        updated_at=existing.updated_at,
    )


@router.put("/preferences", response_model=UserPreferencesView)
def update_my_preferences(
    payload: UserPreferencesUpdate,
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> UserPreferencesView:
    """Create or update the authenticated user's 3-list ingredient personalization profile (`ADR-013`)."""
    existing = repo.get_user_preferences(user_id)
    default_spices = sorted(repo.get_active_pantry_ingredients().keys())

    next_allergic = (
        list(payload.allergic_ingredient_ids)
        if payload.allergic_ingredient_ids is not None
        else (list(existing.allergic_ingredient_ids) if existing is not None else [])
    )
    next_spices = (
        list(payload.kitchen_spice_ids)
        if payload.kitchen_spice_ids is not None
        else (list(existing.kitchen_spice_ids) if existing is not None else default_spices)
    )
    next_favorites = (
        list(payload.favorite_ingredient_ids)
        if payload.favorite_ingredient_ids is not None
        else (list(existing.favorite_ingredient_ids) if existing is not None else [])
    )

    _validate_preference_ingredient_lists(
        repo=repo,
        allergic_ids=next_allergic,
        kitchen_spice_ids=next_spices,
        favorite_ids=next_favorites,
    )

    saved = repo.upsert_user_preferences(
        UserPreferencesRecord(
            user_id=user_id,
            allergic_ingredient_ids=next_allergic,
            kitchen_spice_ids=next_spices,
            favorite_ingredient_ids=next_favorites,
            excluded_allergen_ids=list(existing.excluded_allergen_ids) if existing else [],
            available_equipment=existing.available_equipment if existing else None,
        )
    )
    return UserPreferencesView(
        user_id=saved.user_id,
        allergic_ingredient_ids=list(saved.allergic_ingredient_ids),
        kitchen_spice_ids=list(saved.kitchen_spice_ids),
        favorite_ingredient_ids=list(saved.favorite_ingredient_ids),
        updated_at=saved.updated_at,
    )
