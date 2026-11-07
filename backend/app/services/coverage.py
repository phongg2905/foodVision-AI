"""Component 05 (TP 05) & Component 06 (TP 06): Weighted Coverage & Tversky Baseline B.

Implements exact mathematical formulas from `docs/05-recommendation/recommendation-design.md` Section 5:
1. TP 05 — Weighted Ingredient Coverage:
   C(r, A) = (sum_{i in R_r} w_{r,i} * x_i) / (sum_{i in R_r} w_{r,i}) in [0, 1]
   where x_i = 1 if i in A (confirmed_available), else 0.
   Role weight mapping (when explicit role weights are used):
   - primary: 4.0
   - essential: 3.0
   - secondary / seasoning / garnish / pantry: 1.0
2. TP 06 — Tversky Similarity (Asymmetric Mathematical Baseline B):
   T_{alpha, beta}(A, R_r) = |A n R_r| / (|A n R_r| + alpha * |A \\ R_r| + beta * |R_r \\ A|) in [0, 1]
   Default alpha = 0.3, beta = 2.0 (penalizes missing recipe ingredients more heavily than extra kitchen items).
   Academic Invariant: Tversky is strictly a standalone baseline (Variant B) and is NEVER added into the MCDA score together with C(r, A).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.core.database import RecipeRecord

ROLE_WEIGHT_MAP: dict[str, float] = {
    "primary": 4.0,
    "essential": 3.0,
    "secondary": 1.0,
    "seasoning": 1.0,
    "garnish": 1.0,
}


def get_ingredient_role_weight(role: str, explicit_weight: float | None = None, category: str = "") -> float:
    """Resolve w_{r,i} > 0 for an ingredient in recipe r."""
    if explicit_weight is not None and explicit_weight > 0:
        return float(explicit_weight)
    if category == "pantry":
        return 1.0
    return ROLE_WEIGHT_MAP.get(role.lower().strip(), 1.0)


def compute_weighted_coverage(
    weights: Mapping[str, float],
    confirmed_available_ids: set[str],
) -> float:
    """Compute TP 05 Weighted Ingredient Coverage C(r, A) in [0.0, 1.0] (`MATH-03`).

    Formula:
        C(r, A) = sum_{i in R_r, i in A} w_{r,i} / sum_{i in R_r} w_{r,i}
    """
    if not weights:
        return 0.0
    total_weight = sum(w for w in weights.values() if w > 0)
    if total_weight <= 0.0:
        return 0.0
    matched_weight = sum(
        w for ing_id, w in weights.items() if w > 0 and ing_id in confirmed_available_ids
    )
    return matched_weight / total_weight


def compute_recipe_weighted_coverage(
    recipe: RecipeRecord,
    confirmed_available_ids: set[str],
    use_role_scale: bool = False,
) -> float:
    """Compute TP 05 Weighted Coverage directly from a RecipeRecord's required ingredients."""
    weights: dict[str, float] = {}
    for ri in recipe.ingredients:
        if not ri.is_required:
            continue
        if use_role_scale:
            w = ROLE_WEIGHT_MAP.get(
                "secondary" if ri.category == "pantry" else ri.role.lower().strip(),
                1.0,
            )
        else:
            w = get_ingredient_role_weight(ri.role, ri.weight, ri.category)
        weights[ri.ingredient_id] = w
    return compute_weighted_coverage(weights, confirmed_available_ids)


def compute_tversky_similarity(
    available_ids: Iterable[str],
    recipe_required_ids: Iterable[str],
    alpha: float = 0.3,
    beta: float = 2.0,
) -> float:
    """Compute TP 06 Tversky Similarity T_{alpha, beta}(A, R_r) in [0.0, 1.0] (`MATH-04`).

    Formula:
        T_{alpha, beta}(A, R_r) = |A n R_r| / (|A n R_r| + alpha * |A - R_r| + beta * |R_r - A|)
    """
    a_set = set(available_ids)
    r_set = set(recipe_required_ids)
    intersection_count = len(a_set & r_set)
    if intersection_count == 0:
        return 0.0
    extra_in_a = len(a_set - r_set)
    missing_in_r = len(r_set - a_set)
    denominator = intersection_count + (alpha * extra_in_a) + (beta * missing_in_r)
    if denominator <= 0.0:
        return 0.0
    return intersection_count / denominator

