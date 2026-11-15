"""Component 05 (TP 05) & Component 06 (TP 06): Weighted Coverage `4-2-1-0` & Tversky Baseline B (`ADR-013`).

Implements exact mathematical formulas from `docs/05-recommendation/recommendation-design.md` Section 5:
1. TP 05 — Weighted Ingredient Coverage (`4 - 2 - 1 - 0`):
   C(r, A) = (sum_{i in R_r} w_{r,i} * x_i) / (sum_{i in R_r} w_{r,i}) in [0, 1]
   where x_i = 1 if i in A (confirmed_available), else 0, and R_r contains required ingredients (`is_required = true`).
   4-tier role weight mapping (`ADR-013`):
   - core (legacy alias: primary): 4.0
   - secondary (legacy alias: essential): 2.0
   - spice (legacy aliases: seasoning, pantry): 1.0
   - optional (legacy alias: garnish, `is_required = false`): 0.0 (excluded from R_r)
2. TP 06 — Tversky Similarity (Asymmetric Mathematical Baseline B):
   T_{alpha, beta}(A, R_r) = |A n R_r| / (|A n R_r| + alpha * |A \\ R_r| + beta * |R_r \\ A|) in [0, 1]
   Default alpha = 0.3, beta = 2.0 (penalizes missing recipe ingredients more heavily than extra kitchen items).
   Academic Invariant: Tversky is strictly a standalone baseline (Variant B) and is NEVER added into the MCDA score together with C(r, A).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.core.database import RecipeRecord

ROLE_WEIGHT_MAP: dict[str, float] = {
    "core": 4.0,
    "primary": 4.0,
    "secondary": 2.0,
    "essential": 2.0,
    "spice": 1.0,
    "seasoning": 1.0,
    "pantry": 1.0,
    "optional": 0.0,
    "garnish": 0.0,
}


def get_ingredient_role_weight(
    role: str,
    explicit_weight: float | None = None,
    category: str = "",
) -> float:
    """Resolve w_{r,i} >= 0 for an ingredient in recipe r under the 4-2-1-0 scale."""
    normalized_role = role.lower().strip()
    if normalized_role in ("optional", "garnish"):
        return 0.0
    if explicit_weight is not None and explicit_weight > 0:
        return float(explicit_weight)
    if category == "pantry":
        return 1.0
    return ROLE_WEIGHT_MAP.get(normalized_role, 1.0)


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
    """Compute TP 05 Weighted Coverage directly from a RecipeRecord's required ingredients (`R_r`)."""
    weights: dict[str, float] = {}
    for ri in recipe.ingredients:
        if not ri.is_required:
            continue
        if use_role_scale:
            w = ROLE_WEIGHT_MAP.get(
                "spice" if ri.category == "pantry" else ri.role.lower().strip(),
                1.0,
            )
        else:
            w = get_ingredient_role_weight(ri.role, ri.weight, ri.category)
        if w > 0:
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
