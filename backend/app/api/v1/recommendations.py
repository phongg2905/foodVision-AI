"""Recommendation Endpoint (`POST /api/v1/recommendations`) — TP 04, TP 05, TP 07, TP 09, TP 14 (`ADR-013`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_optional_user_id
from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.reasoning import ReasoningInput
from app.schemas.recommendations import RecommendRequest, RecommendResponse
from app.services.mmr import rerank_with_mmr
from app.services.reasoning import filter_candidate_recipes, validate_and_resolve_ingredients
from app.services.scoring import rank_recommendations, score_recipe_unified

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations", response_model=RecommendResponse)
def recommend_recipes(
    payload: RecommendRequest,
    user_id: str | None = Depends(get_optional_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> RecommendResponse:
    """Rank and recommend published recipes from confirmed ingredients (`FR-06`, `FR-07`, `ADR-013`)."""
    # 0. Auto-load saved 3-list personalization (`user_preferences`) for authenticated users when omitted in request
    saved_prefs = repo.get_user_preferences(user_id) if user_id else None
    fields_set = payload.model_fields_set

    effective_allergic_ids = (
        payload.allergic_ingredient_ids
        if ("allergic_ingredient_ids" in fields_set or saved_prefs is None)
        else saved_prefs.allergic_ingredient_ids
    )
    effective_kitchen_spices = (
        payload.kitchen_spice_ids
        if ("kitchen_spice_ids" in fields_set or saved_prefs is None)
        else saved_prefs.kitchen_spice_ids
    )
    effective_favorite_ids = (
        payload.favorite_ingredient_ids
        if ("favorite_ingredient_ids" in fields_set or saved_prefs is None)
        else saved_prefs.favorite_ingredient_ids
    )
    effective_excluded_allergens = (
        saved_prefs.excluded_allergen_ids if saved_prefs is not None else []
    )
    effective_equipment = (
        saved_prefs.available_equipment if saved_prefs is not None else None
    )

    # 1. Validate ingredient lists and structural invariants (`TC-11`, `TC-37`)
    dedup_main, dedup_pantry, found_map = validate_and_resolve_ingredients(
        repo=repo,
        ingredient_ids=payload.ingredient_ids,
        excluded_pantry_ids=payload.excluded_pantry_ids,
        main_ingredient_ids=payload.main_ingredient_ids,
        kitchen_spice_ids=effective_kitchen_spices,
        allergic_ingredient_ids=effective_allergic_ids,
        favorite_ingredient_ids=effective_favorite_ids,
    )

    # 2. If scan_id is provided, verify ownership and sync scan_ingredients (`TC-20`, `SEC-06`)
    if payload.scan_id is not None:
        if not user_id:
            raise AppError(
                status_code=401,
                code="UNAUTHORIZED",
                message="Cần xác thực Bearer token khi đính kèm scan_id.",
                details={"scan_id": payload.scan_id},
            )
        owned = repo.verify_and_sync_scan_ingredients(
            scan_id=payload.scan_id,
            user_id=user_id,
            ingredient_ids=dedup_main,
        )
        if not owned:
            raise AppError(
                status_code=404,
                code="SCAN_NOT_OWNED",
                message="Không tìm thấy phiên quét hoặc phiên quét không thuộc quyền sở hữu của bạn.",
                details={"scan_id": payload.scan_id},
            )

    # 3. Filter feasible candidate recipes via TP 04 Open-World 3-Valued Reasoning & Hard Constraints
    reasoning_input = ReasoningInput(
        ingredient_ids=dedup_main,
        main_ingredient_ids=payload.main_ingredient_ids,
        kitchen_spice_ids=effective_kitchen_spices,
        excluded_pantry_ids=dedup_pantry,
        allergic_ingredient_ids=effective_allergic_ids,
        favorite_ingredient_ids=effective_favorite_ids,
        excluded_allergen_ids=effective_excluded_allergens,
        available_equipment=effective_equipment,
        max_total_minutes=payload.max_total_minutes,
        cuisine_codes=payload.cuisine_codes,
        include_missing=payload.include_missing,
    )
    feasible_pairs = filter_candidate_recipes(repo=repo, params=reasoning_input)

    # 4. Score each feasible recipe (`Unified MCDA C, G, T, P`) and rank (`ready` before `missing`, score DESC)
    scored_items = [
        score_recipe_unified(
            recipe=rec,
            evaluation=ev,
            ingredient_ids=dedup_main,
            main_ingredient_ids=payload.main_ingredient_ids,
            desired_hours=payload.desired_hours,
            favorite_ingredient_ids=effective_favorite_ids,
            ingredient_map=found_map,
        )
        for rec, ev in feasible_pairs
    ]
    ranked_items = rank_recommendations(scored_items)
    total = len(ranked_items)

    # 5. Optional MMR Top-K diversification (`diversify=True`, default `False` preserves pure S descending order)
    if payload.diversify and ranked_items:
        recipes_by_id = {rec.id: rec for rec, _ev in feasible_pairs}
        page_items = rerank_with_mmr(
            items=ranked_items,
            recipes_by_id=recipes_by_id,
            top_k=payload.limit,
        )
    else:
        page_items = ranked_items[: payload.limit]

    return RecommendResponse(
        items=page_items,
        total=total,
        limit=payload.limit,
    )
