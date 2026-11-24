"""Reproducible CLI Benchmark for Stage 5 Ranker Ablation (A/B/C/D) & PERF-02 Latency (`AI-04`, `DEF-07`, `PERF-02`).

Usage (from `foodVision AI` root):
    python backend/scripts/run_ranker_ablation.py
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient

from app.core.database import (
    InMemoryCatalogRepository,
    RecipeIngredientRecord,
    RecipeRecord,
    RecipeStepRecord,
    get_catalog_repo,
)
from app.main import create_app
from app.services.evaluation_ablation import build_benchmark_catalog, evaluate_all_variants


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, max(0, int(round((pct / 100.0) * (len(sorted_vals) - 1)))))
    return round(sorted_vals[idx], 2)


def run_perf02_benchmark(num_recipes: int = 520, num_requests: int = 40) -> dict[str, dict[str, float]]:
    """Measure p50/p95 latency on >= 500 published recipes for `/recommendations` and `/recipes` (`PERF-02`)."""
    ings, base_recipes = build_benchmark_catalog()
    expanded_recipes: list[RecipeRecord] = []
    for i in range(num_recipes):
        template = base_recipes[i % len(base_recipes)]
        expanded_recipes.append(
            RecipeRecord(
                id=f"99999999-9999-4999-8999-{i + 1:012d}",
                slug=f"{template.slug}-v{i + 1}",
                name_vi=f"{template.name_vi} #{i + 1}",
                cuisine_code=template.cuisine_code,
                prep_minutes=template.prep_minutes,
                cook_minutes=template.cook_minutes + (i % 15),
                status="published",
                cooking_method=template.cooking_method,
                base_servings=2,
                allergen_ids=list(template.allergen_ids),
                ingredients=[
                    RecipeIngredientRecord(
                        ingredient_id=ri.ingredient_id,
                        name_vi=ri.name_vi,
                        category=ri.category,
                        is_required=ri.is_required,
                        role=ri.role,
                        dish_role=ri.dish_role,
                        weight=ri.weight,
                        grams=ri.grams,
                    )
                    for ri in template.ingredients
                ],
                steps=[RecipeStepRecord(step_no=1, instruction="Chế biến.", estimated_minutes=10)],
            )
        )

    repo = InMemoryCatalogRepository(ingredients=ings, recipes=expanded_recipes)
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    client = TestClient(app)

    ing_by_slug = {ing.slug: ing.id for ing in ings}
    rec_payload = {
        "ingredient_ids": [ing_by_slug["ca-chua"], ing_by_slug["trung-ga"], ing_by_slug["dau-hu"]],
        "main_ingredient_ids": [ing_by_slug["ca-chua"]],
        "desired_hours": 0.5,
        "diversify": True,
        "limit": 10,
    }

    # Warmup
    client.post("/api/v1/recommendations", json=rec_payload)
    client.get("/api/v1/recipes?q=ca chua&limit=20")

    rec_latencies_ms: list[float] = []
    search_latencies_ms: list[float] = []

    for i in range(num_requests):
        t0 = time.perf_counter()
        r1 = client.post("/api/v1/recommendations", json=rec_payload)
        rec_latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        assert r1.status_code == 200

        q_term = "ca chua" if i % 2 == 0 else "dau hu"
        t1 = time.perf_counter()
        r2 = client.get(f"/api/v1/recipes?q={q_term}&limit=20")
        search_latencies_ms.append((time.perf_counter() - t1) * 1000.0)
        assert r2.status_code == 200

    rec_sorted = sorted(rec_latencies_ms)
    search_sorted = sorted(search_latencies_ms)

    return {
        "recommendations": {
            "recipes_pool": num_recipes,
            "requests": num_requests,
            "mean_ms": round(statistics.mean(rec_sorted), 2),
            "p50_ms": _percentile(rec_sorted, 50.0),
            "p95_ms": _percentile(rec_sorted, 95.0),
            "target_p95_ms": 1000.0,
        },
        "recipes_search": {
            "recipes_pool": num_recipes,
            "requests": num_requests,
            "mean_ms": round(statistics.mean(search_sorted), 2),
            "p50_ms": _percentile(search_sorted, 50.0),
            "p95_ms": _percentile(search_sorted, 95.0),
            "target_p95_ms": 500.0,
        },
    }


def main() -> None:
    metrics = evaluate_all_variants(seed=20261115, num_scenarios=120, top_k=5)
    perf = run_perf02_benchmark(num_recipes=520, num_requests=40)

    print("=" * 92)
    print("FOODVISION AI — STAGE 5 RANKER ABLATION REPORT (N = 120 SCENARIOS, SEED = 20261115)")
    print(f"Environment: Python {platform.python_version()} | OS: {platform.system()} {platform.release()}")
    print("=" * 92)
    print(f"{'Variant':<9} | {'Precision@5':>11} | {'nDCG@5':>8} | {'CVR@5':>8} | {'ILD@5':>8} | Description")
    print("-" * 92)
    for m in metrics:
        print(
            f"{m.variant:<9} | {m.precision_at_5:>11.4f} | {m.ndcg_at_5:>8.4f} | "
            f"{m.cvr_at_5 * 100:>7.2f}% | {m.ild_at_5:>8.4f} | {m.label}"
        )
    print("-" * 92)
    print("\nPERF-02 LATENCY BENCHMARK (520 PUBLISHED RECIPES, 40 REQUESTS):")
    print(json.dumps(perf, indent=2))


if __name__ == "__main__":
    main()
