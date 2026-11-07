"""Component 07 (TP 07) & Component 14 (TP 14): Rule-Based Scoring v1.0, MCDA v1.1 & Score Breakdown XAI.

Implements exact specifications from `docs/05-recommendation/recommendation-design.md`:
1. Section 3 — MVP Contract Scoring (`Scoring v1.0`):
   - E(r, U, X) = |R_main n U| / (|R_main| + |M_pantry|)
   - C(r, U, X) = (|R_main n U| + 0.5 * |O_main n U|) / (|R_main| + 0.5 * |O_main| + |M_pantry|)
   - T(r) = max(0.0, min(1.0, (60.0 - t) / 45.0))
   - P(r) = 1.0 if preferred_cuisine_codes is empty or r.cuisine_code in preferred_cuisine_codes else 0.0
   - S(r, U, X) = round(100.0 * (0.55 * C + 0.25 * E + 0.10 * T + 0.10 * P), 1)
   - Ranking order: availability == 'ready' first, then score DESC, len(missing_required_ingredient_ids) ASC,
     total_minutes ASC, recipe_id ASC.
2. Section 6 — Multi-Criteria Decision Analysis (`Scoring v1.1` MCDA 5 criteria & XAI Breakdown):
   - S_base(r) = 100 * (0.50 * C + 0.25 * G + 0.15 * T + 0.05 * P + 0.05 * Q)
   - Contributions_k = round(100 * w_k * f_k, 2), sum(Contributions_k) == S_base(r) (`MATH-05`).
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.database import IngredientRecord, RecipeRecord
from app.schemas.reasoning import AvailabilityV1, RecipeReasoningEvaluation
from app.schemas.recommendations import (
    MCDAContributions,
    MCDAEvaluation,
    MCDAFeatures,
    RecommendationItem,
    ScoreBreakdown,
)
from app.schemas.recipes import CuisineCode
from app.services.coverage import compute_weighted_coverage


def compute_mvp_score_components(
    required_main_count: int,
    matched_required_main_count: int,
    optional_main_count: int,
    matched_optional_main_count: int,
    missing_pantry_count: int,
    total_minutes: int,
    cuisine_code: str,
    preferred_cuisine_codes: list[str] | None = None,
) -> tuple[float, ScoreBreakdown]:
    """Compute exact MVP Scoring v1.0 components (C, E, T, P) and total score S in [0, 100]."""
    denom_e = float(required_main_count + missing_pantry_count)
    e_val = (float(matched_required_main_count) / denom_e) if denom_e > 0.0 else 0.0

    denom_c = (
        float(required_main_count)
        + (0.5 * float(optional_main_count))
        + float(missing_pantry_count)
    )
    num_c = float(matched_required_main_count) + (0.5 * float(matched_optional_main_count))
    c_val = (num_c / denom_c) if denom_c > 0.0 else 0.0

    t_val = max(0.0, min(1.0, (60.0 - float(total_minutes)) / 45.0))
    p_val = 1.0 if (not preferred_cuisine_codes or cuisine_code in preferred_cuisine_codes) else 0.0

    raw_score = 100.0 * (0.55 * c_val + 0.25 * e_val + 0.10 * t_val + 0.10 * p_val)
    total_score = round(raw_score, 1)

    breakdown = ScoreBreakdown(
        C=round(c_val, 4),
        E=round(e_val, 4),
        T=round(t_val, 4),
        P=round(p_val, 4),
    )
    return total_score, breakdown


def build_explanation_vi(
    recipe: RecipeRecord,
    availability: AvailabilityV1,
    matched_main_ids: list[str],
    missing_required_ids: list[str],
    ingredient_map: Mapping[str, IngredientRecord] | None = None,
) -> str:
    """Generate human-readable Vietnamese explanation (`explanation_vi`) for XAI."""
    name_lookup: dict[str, str] = {}
    if ingredient_map:
        for iid, rec in ingredient_map.items():
            name_lookup[iid] = rec.name_vi
    for ri in recipe.ingredients:
        name_lookup.setdefault(ri.ingredient_id, ri.name_vi)

    matched_names = [name_lookup.get(iid, iid) for iid in matched_main_ids]
    missing_names = [name_lookup.get(iid, iid) for iid in missing_required_ids]

    matched_str = ", ".join(matched_names) if matched_names else f"{len(matched_main_ids)} nguyên liệu"
    if availability == "ready":
        return (
            f"Đủ nguyên liệu bắt buộc để nấu ngay ({matched_str}); "
            f"thời gian hoàn thành {recipe.total_minutes} phút."
        )
    missing_str = ", ".join(missing_names) if missing_names else f"{len(missing_required_ids)} nguyên liệu"
    return (
        f"Đã có {matched_str}; cần chuẩn bị hoặc mua thêm: {missing_str} "
        f"(thời gian nấu {recipe.total_minutes} phút)."
    )


def score_recipe_v1_0(
    recipe: RecipeRecord,
    evaluation: RecipeReasoningEvaluation,
    preferred_cuisine_codes: list[CuisineCode] | None = None,
    ingredient_map: Mapping[str, IngredientRecord] | None = None,
) -> RecommendationItem:
    """Score a feasible recipe using MVP Contract Scoring v1.0 and return a RecommendationItem."""
    r_main = [ri for ri in recipe.ingredients if ri.category != "pantry" and ri.is_required]
    o_main = [ri for ri in recipe.ingredients if ri.category != "pantry" and not ri.is_required]

    matched_req_main_count = len(r_main) - len(evaluation.missing_required_main_ids)
    matched_opt_main_count = len(evaluation.matched_optional_main_ids)
    missing_pantry_count = len(evaluation.missing_pantry_ids)

    score, breakdown = compute_mvp_score_components(
        required_main_count=len(r_main),
        matched_required_main_count=matched_req_main_count,
        optional_main_count=len(o_main),
        matched_optional_main_count=matched_opt_main_count,
        missing_pantry_count=missing_pantry_count,
        total_minutes=recipe.total_minutes,
        cuisine_code=recipe.cuisine_code,
        preferred_cuisine_codes=list(preferred_cuisine_codes or []),
    )

    availability: AvailabilityV1 = (
        "ready" if len(evaluation.missing_required_ingredient_ids) == 0 else "missing"
    )
    explanation_vi = build_explanation_vi(
        recipe=recipe,
        availability=availability,
        matched_main_ids=evaluation.matched_main_ids,
        missing_required_ids=evaluation.missing_required_ingredient_ids,
        ingredient_map=ingredient_map,
    )

    return RecommendationItem(
        recipe=recipe.to_summary(),
        availability=availability,
        score=score,
        matched_ingredient_ids=evaluation.matched_main_ids,
        missing_required_ingredient_ids=evaluation.missing_required_ingredient_ids,
        missing_optional_ingredient_ids=evaluation.missing_optional_ingredient_ids,
        score_breakdown=breakdown,
        explanation_vi=explanation_vi,
    )


def recommendation_tiebreak_key(item: RecommendationItem) -> tuple[float, int, int, str]:
    """Deterministic tie-breaker key shared across standard ranking and MMR selection:
    (-score, len(missing_required_ingredient_ids), total_minutes, recipe_id).
    """
    return (
        -item.score,
        len(item.missing_required_ingredient_ids),
        item.recipe.total_minutes,
        item.recipe.id,
    )


def rank_recommendations_v1_0(items: list[RecommendationItem]) -> list[RecommendationItem]:
    """Sort recommendations per Section 3 of `docs/05-recommendation/recommendation-design.md`:
    1. Group "ready" before "missing"
    2. score DESC
    3. len(missing_required_ingredient_ids) ASC
    4. total_minutes ASC
    5. recipe.id ASC
    """
    return sorted(
        items,
        key=lambda item: (
            0 if item.availability == "ready" else 1,
            *recommendation_tiebreak_key(item),
        ),
    )


def compute_mcda_v1_1_from_features(
    c_val: float,
    g_val: float,
    t_val: float,
    p_val: float = 0.5,
    q_val: float = 1.0,
) -> tuple[float, MCDAFeatures, MCDAContributions]:
    """Compute TP 07 & TP 14 5-criteria MCDA score and linear XAI breakdown (`MATH-05`)."""
    features = MCDAFeatures(
        C=round(c_val, 6),
        G=round(g_val, 6),
        T=round(t_val, 6),
        P=round(p_val, 6),
        Q=round(q_val, 6),
    )
    contrib_c = round(100.0 * 0.50 * c_val, 2)
    contrib_g = round(100.0 * 0.25 * g_val, 2)
    contrib_t = round(100.0 * 0.15 * t_val, 2)
    contrib_p = round(100.0 * 0.05 * p_val, 2)
    contrib_q = round(100.0 * 0.05 * q_val, 2)

    contributions = MCDAContributions(
        C=contrib_c,
        G=contrib_g,
        T=contrib_t,
        P=contrib_p,
        Q=contrib_q,
    )
    score_base = round(contrib_c + contrib_g + contrib_t + contrib_p + contrib_q, 2)
    return score_base, features, contributions


def score_recipe_mcda_v1_1(
    recipe: RecipeRecord,
    evaluation: RecipeReasoningEvaluation,
    confirmed_available_ids: set[str],
    focus_ids: set[str] | None = None,
    preferred_cuisine_codes: list[str] | None = None,
    ref_minutes: int = 15,
) -> MCDAEvaluation:
    """Evaluate a recipe using Scoring v1.1 (TP 05 Weighted Coverage + TP 07 MCDA + TP 14 XAI)."""
    weights: dict[str, float] = {
        ri.ingredient_id: float(ri.weight)
        for ri in recipe.ingredients
        if ri.is_required
    }
    c_val = compute_weighted_coverage(weights, confirmed_available_ids)

    focus = focus_ids if focus_ids is not None else set(evaluation.matched_main_ids)
    primary_ids = {
        ri.ingredient_id for ri in recipe.ingredients if ri.role.lower() == "primary"
    }
    essential_ids = {
        ri.ingredient_id
        for ri in recipe.ingredients
        if ri.role.lower() in ("primary", "essential") and ri.category != "pantry"
    }
    if primary_ids & focus:
        g_val = 1.0
    elif essential_ids & focus:
        g_val = 0.5
    else:
        g_val = 0.0

    total_min = max(1, recipe.total_minutes)
    t_val = min(1.0, float(ref_minutes) / float(total_min))

    if not preferred_cuisine_codes:
        p_val = 0.5
    elif recipe.cuisine_code in preferred_cuisine_codes:
        p_val = 1.0
    else:
        p_val = 0.0

    q_val = max(0.0, min(1.0, float(recipe.quality_score)))
    score_base, features, contributions = compute_mcda_v1_1_from_features(
        c_val=c_val,
        g_val=g_val,
        t_val=t_val,
        p_val=p_val,
        q_val=q_val,
    )
    return MCDAEvaluation(
        recipe_id=recipe.id,
        state=evaluation.status_v1_1,
        score_base=score_base,
        features=features,
        contributions=contributions,
    )
