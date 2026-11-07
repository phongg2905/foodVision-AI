"""Component 09 (TP 09): Maximal Marginal Relevance (MMR) Top-K Diversification.

Implements Section 7.2 of `docs/05-recommendation/recommendation-design.md`:
1. MMR(r) = lambda_mmr * Rel(r) - (1 - lambda_mmr) * max_{s in D} Sim(r, s)
   with Rel(r) = S_final(u, r) / 100 in [0, 1], default lambda_mmr = 0.7 (`MATH-06`).
2. Recipe similarity Sim(r, s) in [0, 1] combines:
   - Cooking method similarity (0.40)
   - Cuisine code similarity (0.20)
   - Main ingredient Jaccard similarity (0.40)
3. Safety Invariant:
   - MMR only re-orders feasible candidates within the same availability tier ("ready" stays before "missing").
   - MMR NEVER re-introduces BLOCKED recipes.
"""

from __future__ import annotations

from collections.abc import Callable

from app.core.database import RecipeRecord
from app.schemas.recommendations import RecommendationItem
from app.services.scoring import recommendation_tiebreak_key


def compute_mmr_score(
    rel_score: float,
    max_similarity_to_selected: float,
    lambda_mmr: float = 0.7,
) -> float:
    """Compute exact MMR value for a candidate given its relevance Rel(r) in [0, 1]
    and maximum similarity max_{s in D} Sim(r, s) in [0, 1] (`MATH-06`).
    """
    return round((lambda_mmr * rel_score) - ((1.0 - lambda_mmr) * max_similarity_to_selected), 6)


def compute_recipe_similarity(rec_a: RecipeRecord, rec_b: RecipeRecord) -> float:
    """Compute similarity Sim(r_a, r_b) in [0.0, 1.0] between two RecipeRecords."""
    if rec_a.id == rec_b.id:
        return 1.0

    method_sim = (
        1.0
        if (
            rec_a.cooking_method
            and rec_b.cooking_method
            and rec_a.cooking_method.lower() == rec_b.cooking_method.lower()
        )
        else 0.0
    )
    cuisine_sim = 1.0 if rec_a.cuisine_code == rec_b.cuisine_code else 0.0

    main_a = {ri.ingredient_id for ri in rec_a.ingredients if ri.category != "pantry"}
    main_b = {ri.ingredient_id for ri in rec_b.ingredients if ri.category != "pantry"}
    union_len = len(main_a | main_b)
    ing_sim = (len(main_a & main_b) / union_len) if union_len > 0 else 0.0

    return round((0.40 * method_sim) + (0.20 * cuisine_sim) + (0.40 * ing_sim), 4)


def rerank_with_mmr(
    items: list[RecommendationItem],
    recipes_by_id: dict[str, RecipeRecord],
    top_k: int = 20,
    lambda_mmr: float = 0.7,
    similarity_fn: Callable[[str, str], float] | None = None,
) -> list[RecommendationItem]:
    """Diversify Top-K recommendations using MMR while preserving 'ready' before 'missing'.

    Safety invariant: Only operates on already-filtered feasible items (never resurrects BLOCKED recipes),
    and strictly keeps 'ready' items ahead of 'missing' items.
    """
    if not items or top_k <= 0:
        return []

    def _sim(id_a: str, id_b: str) -> float:
        if similarity_fn is not None:
            return similarity_fn(id_a, id_b)
        ra = recipes_by_id.get(id_a)
        rb = recipes_by_id.get(id_b)
        if ra is None or rb is None:
            return 0.0
        return compute_recipe_similarity(ra, rb)

    ready_pool = [it for it in items if it.availability == "ready"]
    missing_pool = [it for it in items if it.availability == "missing"]

    def _greedy_mmr_select(pool: list[RecommendationItem], k_limit: int) -> list[RecommendationItem]:
        if not pool or k_limit <= 0:
            return []
        remaining = sorted(pool, key=recommendation_tiebreak_key)
        selected: list[RecommendationItem] = [remaining.pop(0)]

        def _mmr_candidate_key(cand: RecommendationItem) -> tuple[float, float, int, int, str]:
            max_sim = max(_sim(cand.recipe.id, sel.recipe.id) for sel in selected)
            mmr_val = compute_mmr_score(cand.score / 100.0, max_sim, lambda_mmr=lambda_mmr)
            return (-mmr_val, *recommendation_tiebreak_key(cand))

        while remaining and len(selected) < k_limit:
            best_cand = min(remaining, key=_mmr_candidate_key)
            remaining.remove(best_cand)
            selected.append(best_cand)
        return selected

    selected_ready = _greedy_mmr_select(ready_pool, top_k)
    remaining_slots = top_k - len(selected_ready)
    selected_missing = _greedy_mmr_select(missing_pool, remaining_slots) if remaining_slots > 0 else []
    return selected_ready + selected_missing
