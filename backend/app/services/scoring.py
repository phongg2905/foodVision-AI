"""Component 07 (TP 07), Component 08 (TP 08) & Component 14 (TP 14): Unified 4-Criteria MCDA Scoring, Logistic Regression Blending & Linear XAI (`ADR-013`).

Implements exact mathematical specifications from `docs/05-recommendation/recommendation-design.md` & `ADR-013`:
1. Criterion 1 — Weighted Ingredient Coverage `C(r, A) in [0, 1]` (`TP 05`, weight `0.50`):
   4-tier required weights: `core = 4`, `secondary = 2`, `spice = 1`, `optional = 0` (`is_required = false`, excluded from `R_r`).
2. Criterion 2 — Main Ingredient Role Score `G(r) in [0, 1]` (`Cách B`, weight `0.25`):
   User confirmed ingredients `U = U_main U U_sub` (`0.7 / 0.3` group split; `dish_role`: `'main' -> 1.0`, `'sub' -> 0.5`).
3. Criterion 3 — Time Score `T(r) = min(1.0, desired_hours / t_r) in (0, 1]` (weight `0.15`).
4. Criterion 4 — Ingredient Preference Score `P(r) in [0, 1]` (weight `0.10`, neutral `0.5` when `F_u = empty`).
5. Unified Score & Additive XAI Contributions (`MATH-05`):
   `S(r) = round(50*C + 25*G + 15*T + 10*P, 2) in [0, 100]`.
6. Component 08 Cold-Start Logistic Regression Personalization Blending (`MATH-05`, `DEF-08`):
   `S_final(u, r) = round((1 - lambda_pers(N_u)) * S(r) + 100 * lambda_pers(N_u) * P(like | u, r), 2)`.
   When `lambda_pers(N_u) == 0` (Guest or cold-start user), `S_final(u, r) == S(r)`.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.core.database import IngredientRecord, RecipeRecord
from app.intelligence.personalization import (
    PersonalizationConfig,
    PersonalizationEngine,
    UserModelState,
)
from app.schemas.reasoning import AvailabilityV1, RecipeReasoningEvaluation
from app.schemas.recommendations import (
    RecommendationItem,
    ScoreBreakdown,
    ScoreContributions,
)
from app.services.coverage import compute_recipe_weighted_coverage
from app.services.personalization import (
    PreparedPersonalizationContext,
    blend_personalized_score,
    resolve_recipe_personalization,
)


# THUẬT TOÁN: Chấm Điểm Vai trò Nguyên liệu Chính Tiêu chí 2 (`G(r) ∈ [0, 1]`, trọng số 0.25)
def compute_main_role_score_g(
    recipe: RecipeRecord,
    ingredient_ids: list[str],
    main_ingredient_ids: list[str] | None = None,
) -> float:
    """Compute Criterion 2 `G(r) in [0, 1]` using `Cách B` (`0.7 / 0.3` group split & `dish_role` `1.0 / 0.5 / 0.0`)."""
    u_list = list(dict.fromkeys(ingredient_ids))
    if not u_list:
        return 0.0

    dish_role_lookup: dict[str, float] = {}
    for ri in recipe.ingredients:
        dish_role_lookup[ri.ingredient_id] = 1.0 if ri.dish_role == "main" else 0.5

    selected_main_set = set(main_ingredient_ids or [])
    u_main = [iid for iid in u_list if iid in selected_main_set]
    u_sub = [iid for iid in u_list if iid not in selected_main_set]

    if not u_main or not u_sub:
        return sum(dish_role_lookup.get(iid, 0.0) for iid in u_list) / float(len(u_list))

    w_main = 0.7 / float(len(u_main))
    w_sub = 0.3 / float(len(u_sub))

    weighted_sum = sum(w_main * dish_role_lookup.get(iid, 0.0) for iid in u_main) + sum(
        w_sub * dish_role_lookup.get(iid, 0.0) for iid in u_sub
    )
    total_w = (0.7) + (0.3)
    return weighted_sum / total_w


# THUẬT TOÁN: Chấm Điểm Thời gian Chế biến Tiêu chí 3 (`T(r) = min(1, t* / t_r)`, trọng số 0.15)
def compute_time_score_t(
    total_minutes: int,
    desired_hours: float = 100.0,
) -> float:
    """Compute Criterion 3 `T(r) = min(1.0, desired_hours / t_r)` where `t_r = total_minutes / 60.0 > 0`."""
    t_r_hours = float(max(1, total_minutes)) / 60.0
    if desired_hours <= 0.0:
        return 0.0
    return min(1.0, float(desired_hours) / t_r_hours)


# THUẬT TOÁN: Chấm Điểm Sở thích Nguyên liệu Tường minh Tiêu chí 4 (`P(r) ∈ [0, 1]`, trọng số 0.10)
def compute_preference_score_p(
    recipe: RecipeRecord,
    favorite_ingredient_ids: list[str] | None = None,
) -> float:
    """Compute Criterion 4 `P(r)` with `0.5` neutral convention when `favorite_ingredient_ids` is empty."""
    fav_set = set(favorite_ingredient_ids or [])
    if not fav_set:
        return 0.5
    recipe_ing_ids = {ri.ingredient_id for ri in recipe.ingredients}
    return float(len(recipe_ing_ids & fav_set)) / float(len(fav_set))


# CONFLICT-RESOLVED: Connect TP 08 Cold-Start Logistic Regression score blending (`S_final`)
# onto TP 07 Unified 4-Criteria MCDA base score (`S(r)` per ADR-013) without altering linear XAI contributions.
# THUẬT TOÁN: Chấm Điểm MCDA 4 Tiêu chí Hợp nhất (`C, G, T, P`) & Trộn Cá nhân hóa `S_final(u, r)`
def compute_unified_mcda_score(
    c_val: float,
    g_val: float,
    t_val: float,
    p_val: float = 0.5,
    *,
    preference_prob: float | None = None,
    feedback_count: int = 0,
    lambda_pers: float | None = None,
    personalization_config: PersonalizationConfig | None = None,
) -> tuple[float, ScoreBreakdown, ScoreContributions]:
    """Compute unified 4-criteria MCDA score `S(r)` (or blended `S_final(u, r)`) and XAI breakdown (`ADR-013`, `MATH-05`)."""
    breakdown = ScoreBreakdown(
        C=round(c_val, 6),
        G=round(g_val, 6),
        T=round(t_val, 6),
        P=round(p_val, 6),
    )
    contrib_c = round(50.0 * c_val, 2)
    contrib_g = round(25.0 * g_val, 2)
    contrib_t = round(15.0 * t_val, 2)
    contrib_p = round(10.0 * p_val, 2)

    contributions = ScoreContributions(
        C=contrib_c,
        G=contrib_g,
        T=contrib_t,
        P=contrib_p,
    )
    base_score = round(contrib_c + contrib_g + contrib_t + contrib_p, 2)
    final_score = blend_personalized_score(
        base_score=base_score,
        preference_prob=preference_prob,
        feedback_count=feedback_count,
        lambda_pers=lambda_pers,
        config=personalization_config,
    )
    return final_score, breakdown, contributions


# THUẬT TOÁN: Sinh Lời giải thích Tiếng Việt Tường minh Không Hộp đen (`TP 14` XAI)
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

    matched_str = (
        ", ".join(matched_names) if matched_names else f"{len(matched_main_ids)} nguyên liệu"
    )
    if availability == "ready":
        return (
            f"Đủ nguyên liệu bắt buộc để nấu ngay ({matched_str}); "
            f"thời gian hoàn thành {recipe.total_minutes} phút."
        )
    missing_str = (
        ", ".join(missing_names) if missing_names else f"{len(missing_required_ids)} nguyên liệu"
    )
    return (
        f"Đã có {matched_str}; cần chuẩn bị hoặc mua thêm: {missing_str} "
        f"(thời gian nấu {recipe.total_minutes} phút)."
    )


# THUẬT TOÁN: Chấm Điểm Công thức Đầu-Cuối Hợp nhất MCDA 4 Tiêu chí + Trộn Điểm `S_final(u, r)` (`TP 07` + `TP 08`)
def score_recipe_unified(
    recipe: RecipeRecord,
    evaluation: RecipeReasoningEvaluation,
    ingredient_ids: list[str],
    main_ingredient_ids: list[str] | None = None,
    desired_hours: float = 100.0,
    favorite_ingredient_ids: list[str] | None = None,
    ingredient_map: Mapping[str, IngredientRecord] | None = None,
    *,
    user_id: str | UUID | None = None,
    personalization_engine: PersonalizationEngine | None = None,
    user_model_state: UserModelState | None = None,
    prepared_personalization: PreparedPersonalizationContext | None = None,
    preference_prob: float | None = None,
    feedback_count: int = 0,
    lambda_pers: float | None = None,
) -> RecommendationItem:
    """Score a feasible recipe using Unified 4-Criteria MCDA (`ADR-013`) and blend TP 08 LR score `S_final(u, r)`."""
    confirmed_available_set = set(evaluation.confirmed_available_ids)
    c_val = compute_recipe_weighted_coverage(recipe, confirmed_available_set)
    g_val = compute_main_role_score_g(recipe, ingredient_ids, main_ingredient_ids)
    t_val = compute_time_score_t(recipe.total_minutes, desired_hours=desired_hours)
    p_val = compute_preference_score_p(recipe, favorite_ingredient_ids=favorite_ingredient_ids)

    base_score, breakdown, contributions = compute_unified_mcda_score(
        c_val=c_val,
        g_val=g_val,
        t_val=t_val,
        p_val=p_val,
    )
    # Connect S_final(u, r) = (1 - lambda_pers(N_u)) * S(r) + 100 * lambda_pers(N_u) * P(like | u, r)
    score = resolve_recipe_personalization(
        recipe=recipe,
        evaluation=evaluation,
        c_val=c_val,
        g_val=g_val,
        base_score=base_score,
        user_id=user_id,
        personalization_engine=personalization_engine,
        user_model_state=user_model_state,
        prepared_context=prepared_personalization,
        preference_prob=preference_prob,
        feedback_count=feedback_count,
        lambda_pers=lambda_pers,
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
        reasoning_status=evaluation.status_v1_1,
        score=score,
        matched_ingredient_ids=evaluation.matched_main_ids,
        missing_required_ingredient_ids=evaluation.missing_required_ingredient_ids,
        missing_optional_ingredient_ids=evaluation.missing_optional_ingredient_ids,
        score_breakdown=breakdown,
        score_contributions=contributions,
        explanation_vi=explanation_vi,
    )


# THUẬT TOÁN: Khóa Phân định Hòa điểm Tất định (`-score, missing_count, total_minutes, recipe_id`)
def recommendation_tiebreak_key(item: RecommendationItem) -> tuple[float, int, int, str]:
    """Deterministic tie-breaker key shared across standard ranking and MMR selection."""
    return (
        -item.score,
        len(item.missing_required_ingredient_ids),
        item.recipe.total_minutes,
        item.recipe.id,
    )


# THUẬT TOÁN: Sắp xếp Danh sách Gợi ý Món ăn (`ready` trước `missing`, sau đó theo `recommendation_tiebreak_key`)
def rank_recommendations(items: list[RecommendationItem]) -> list[RecommendationItem]:
    """Sort recommendations: group 'ready' before 'missing', then score DESC, missing ASC, time ASC, id ASC."""
    return sorted(
        items,
        key=lambda item: (
            0 if item.availability == "ready" else 1,
            *recommendation_tiebreak_key(item),
        ),
    )
