"""Recommendation Endpoint (`POST /api/v1/recommendations`) — TP 04, TP 05, TP 07, TP 09, TP 14."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_optional_user_id
from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.schemas.reasoning import ReasoningInput
from app.schemas.recommendations import RecommendRequest, RecommendResponse
from app.services.reasoning import filter_candidate_recipes, validate_and_resolve_ingredients
from app.services.scoring import rank_recommendations_v1_0, score_recipe_v1_0

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations", response_model=RecommendResponse)
def recommend_recipes(
    payload: RecommendRequest,
    user_id: str | None = Depends(get_optional_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> RecommendResponse:
    """Rank and recommend published recipes from confirmed ingredients (`FR-06`, `FR-07`, `TC-10`..`TC-14`, `TC-32`..`TC-37`, `SEC-06`)."""
    # 1. Validate ingredient_ids (main) and excluded_pantry_ids (pantry) (`TC-37`)
    dedup_main, dedup_pantry, found_map = validate_and_resolve_ingredients(
        repo=repo,
        ingredient_ids=payload.ingredient_ids,
        excluded_pantry_ids=payload.excluded_pantry_ids,
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
        excluded_pantry_ids=dedup_pantry,
        max_total_minutes=payload.max_total_minutes,
        cuisine_codes=payload.cuisine_codes,
        preferred_cuisine_codes=payload.preferred_cuisine_codes,
        include_missing=payload.include_missing,
    )
    feasible_pairs = filter_candidate_recipes(repo=repo, params=reasoning_input)

    # 4. Score each feasible recipe (`Scoring v1.0`) and rank (`ready` before `missing`, score DESC)
    scored_items = [
        score_recipe_v1_0(
            recipe=rec,
            evaluation=ev,
            preferred_cuisine_codes=payload.preferred_cuisine_codes,
            ingredient_map=found_map,
        )
        for rec, ev in feasible_pairs
    ]
    ranked_items = rank_recommendations_v1_0(scored_items)

    total = len(ranked_items)
    return RecommendResponse(
        items=ranked_items[: payload.limit],
        total=total,
        limit=payload.limit,
    )
