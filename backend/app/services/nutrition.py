"""Two-Tier Nutrition Policy & Portion Scaling Service (`TP 10`, `TP 11`, `ADR-004`, `MATH-07`, `DEF-09`).

Safety Invariants (`NFR-07`, `BR-03`):
1. NEVER infer grams or kcal from 2D RGB bounding boxes or object counts.
2. Tier 1 (Qualitative tags + source URLs + medical/allergy disclaimer) is always active.
3. Tier 2 (USDA FoodData Central per-100g quantitative estimate) ONLY activates when all required
   ingredients have curated `grams > 0` and verified `ingredient_nutrients` mappings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.schemas.recipes import PORTION_SCALING_WARNING_VI, USDANutritionEstimate


@dataclass(frozen=True)
class IngredientNutrient100g:
    ingredient_id: str
    kcal_100g: float
    protein_100g: float
    fat_100g: float
    carb_100g: float
    source_url: str


@dataclass(frozen=True)
class PortionIngredientInput:
    ingredient_id: str
    is_required: bool
    base_grams: float | None


def scale_portion_grams(base_grams: float, base_servings: int, target_servings: int) -> float:
    """Linear portion scaling: q_new = q_base * (n_new / n_base) (`TP 10`, `MATH-07`)."""
    if base_servings <= 0 or target_servings <= 0:
        raise ValueError("Số khẩu phần (servings) bắt buộc > 0.")
    if base_grams <= 0:
        raise ValueError("Khối lượng nguyên liệu (grams) bắt buộc > 0.")
    return round(float(base_grams) * (float(target_servings) / float(base_servings)), 2)


def estimate_usda_nutrition(
    ingredients: Sequence[PortionIngredientInput],
    nutrient_map: dict[str, IngredientNutrient100g],
    base_servings: int = 2,
    target_servings: int | None = None,
) -> USDANutritionEstimate | None:
    """Compute Tier-2 USDA nutrition estimate N_k(r) = sum_i (m_i / 100) * V_{i,k} (`TP 11`, `MATH-07`).

    Returns `None` (falling back safely to Tier-1 qualitative tags) if the recipe has no ingredients,
    any required ingredient lacks `base_grams > 0` or a verified USDA `IngredientNutrient100g` entry,
    or any optional ingredient with `base_grams > 0` lacks a USDA entry.
    """
    if not ingredients or base_servings <= 0:
        return None

    eff_servings = base_servings if target_servings is None else target_servings
    if eff_servings <= 0:
        raise ValueError("Số khẩu phần (servings) bắt buộc > 0.")

    scaling_factor = float(eff_servings) / float(base_servings)

    total_kcal = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carb = 0.0
    source_urls: list[str] = []
    seen_urls: set[str] = set()
    counted_any = False

    for item in ingredients:
        if item.base_grams is None or item.base_grams <= 0:
            if item.is_required:
                return None
            continue

        nutr = nutrient_map.get(item.ingredient_id)
        if nutr is None:
            return None

        scaled_grams = float(item.base_grams) * scaling_factor
        ratio = scaled_grams / 100.0
        total_kcal += ratio * float(nutr.kcal_100g)
        total_protein += ratio * float(nutr.protein_100g)
        total_fat += ratio * float(nutr.fat_100g)
        total_carb += ratio * float(nutr.carb_100g)
        counted_any = True

        if nutr.source_url and nutr.source_url not in seen_urls:
            seen_urls.add(nutr.source_url)
            source_urls.append(nutr.source_url)

    if not counted_any:
        return None

    return USDANutritionEstimate(
        kcal=round(total_kcal, 2),
        protein_g=round(total_protein, 2),
        fat_g=round(total_fat, 2),
        carb_g=round(total_carb, 2),
        source_urls=source_urls,
        scaling_factor=round(scaling_factor, 4),
        scaling_warning_vi=PORTION_SCALING_WARNING_VI if eff_servings != base_servings else None,
    )
