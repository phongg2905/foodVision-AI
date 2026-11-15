r"""Component 07 (TP 07) & Component 14 (TP 14): Unified 4-Criteria MCDA Scoring & Linear XAI Breakdown (`ADR-013`).

Implements exact mathematical specifications from `docs/05-recommendation/recommendation-design.md` & `ADR-013`:
1. Criterion 1 — Weighted Ingredient Coverage `C(r, A) in [0, 1]` (`TP 05`, weight `0.50`):
   4-tier required weights: `core = 4`, `secondary = 2`, `spice = 1`, `optional = 0` (`is_required = false`, excluded from `R_r`).
   `A = U U S_bep` (confirmed non-pantry ingredients + available kitchen spices).
2. Criterion 2 — Main Ingredient Role Score `G(r) in [0, 1]` (`Cách B`, weight `0.25`):
   - Recipe ingredient role `g(i, r)`: `dish_role == 'main' -> 1.0`, `'sub' -> 0.5`, absent -> `0.0`.
   - User confirmed ingredients `U = U_main U U_sub`:
     Total weight `0.7` split across `U_main` (`w_i = 0.7 / |U_main|`), total weight `0.3` split across `U_sub` (`w_i = 0.3 / |U_sub|`).
     `G(r) = (sum_{i in U} w_i * g(i, r)) / (sum_{i in U} w_i)`.
     When `U_main = empty` (user skips selecting main ingredients) or `U_sub = empty`, reduces cleanly to `(1 / |U|) * sum_{i in U} g(i, r)`.
3. Criterion 3 — Time Score `T(r) in (0, 1]` (weight `0.15`):
   - `t_r = max(1, prep_minutes + cook_minutes) / 60.0` (hours, `> 0`).
   - `T(r) = min(1.0, desired_hours / t_r)`, default `desired_hours = 100.0` (`T(r) = 1.0`).
4. Criterion 4 — Ingredient Preference Score `P(r) in [0, 1]` (weight `0.10`):
   - Neutral convention when `|F_u| = 0` (`favorite_ingredient_ids = []` or Guest): `P(r) = 0.5`.
   - Otherwise: `P(r) = |Ing(r) n F_u| / |F_u|`.
5. Unified Score & Additive XAI Contributions (`MATH-05`):
   - `contrib_C = round(50.0 * C, 2)`, `contrib_G = round(25.0 * G, 2)`,
     `contrib_T = round(15.0 * T, 2)`, `contrib_P = round(10.0 * P, 2)`.
   - `S(r) = round(contrib_C + contrib_G + contrib_T + contrib_P, 2) in [0, 100]`.
6. Ranking Order:
   - Group `"ready"` before `"missing"`, then `score DESC`, `len(missing_required_ingredient_ids) ASC`,
     `total_minutes ASC`, `recipe.id ASC`.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.database import IngredientRecord, RecipeRecord
from app.schemas.reasoning import AvailabilityV1, RecipeReasoningEvaluation
from app.schemas.recommendations import (
    RecommendationItem,
    ScoreBreakdown,
    ScoreContributions,
)
from app.services.coverage import compute_recipe_weighted_coverage


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


def compute_time_score_t(
    total_minutes: int,
    desired_hours: float = 100.0,
) -> float:
    """Compute Criterion 3 `T(r) = min(1.0, desired_hours / t_r)` where `t_r = total_minutes / 60.0 > 0`."""
    t_r_hours = float(max(1, total_minutes)) / 60.0
    if desired_hours <= 0.0:
        return 0.0
    return min(1.0, float(desired_hours) / t_r_hours)


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


def compute_unified_mcda_score(
    c_val: float,
    g_val: float,
    t_val: float,
    p_val: float = 0.5,
) -> tuple[float, ScoreBreakdown, ScoreContributions]:
    """Compute unified 4-criteria MCDA score `S(r)` and additive XAI breakdown (`ADR-013`, `MATH-05`)."""
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
    total_score = round(contrib_c + contrib_g + contrib_t + contrib_p, 2)
    return total_score, breakdown, contributions


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


def score_recipe_unified(
    recipe: RecipeRecord,
    evaluation: RecipeReasoningEvaluation,
    ingredient_ids: list[str],
    main_ingredient_ids: list[str] | None = None,
    desired_hours: float = 100.0,
    favorite_ingredient_ids: list[str] | None = None,
    ingredient_map: Mapping[str, IngredientRecord] | None = None,
) -> RecommendationItem:
    """Score a feasible recipe using Unified 4-Criteria MCDA (`ADR-013`) and return a `RecommendationItem`."""
    confirmed_available_set = set(evaluation.confirmed_available_ids)
    c_val = compute_recipe_weighted_coverage(recipe, confirmed_available_set)
    g_val = compute_main_role_score_g(recipe, ingredient_ids, main_ingredient_ids)
    t_val = compute_time_score_t(recipe.total_minutes, desired_hours=desired_hours)
    p_val = compute_preference_score_p(recipe, favorite_ingredient_ids=favorite_ingredient_ids)

    score, breakdown, contributions = compute_unified_mcda_score(
        c_val=c_val,
        g_val=g_val,
        t_val=t_val,
        p_val=p_val,
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


def rank_recommendations(items: list[RecommendationItem]) -> list[RecommendationItem]:
    """Sort recommendations per `docs/05-recommendation/recommendation-design.md`:
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
