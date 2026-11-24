"""Stage 5 Empirical Ablation & Operations Benchmark Engine (`TP 12`, `AI-04`, `DEF-07`, `PERF-02`).

Compares 4 Ranker Variants across >= 100 independent evaluation scenarios (`N = 120`, seed = 20261115):
- Variant A (`Uniform Match Count`): Raw uniform ingredient overlap count `|A n Ing(r)|` (no `4-2-1-0` role weights, no `TP 04` hard constraint gate, no MMR).
- Variant B (`Tversky Similarity — TP 06`): Asymmetric Tversky `T_{alpha=0.3, beta=2.0}(A, R_r)` standalone mathematical baseline.
- Variant C (`3-State + Weighted 4-2-1-0 + MCDA C,G,T,P + MMR — TP 04, 05, 07, 09`): Full core FoodVision AI engine (`ADR-013`).
- Variant D (`Variant C + Logistic Regression — TP 08`): Blends learned user preference `theta_u` trained strictly on past interactions (`t_train < t_eval`, temporal split) before MMR Top-K diversification.

Metrics reported (`k = 5`):
- `Precision@5` (`rel >= 2`)
- `nDCG@5` (`gain = (2^rel - 1) / log2(rank + 1)`)
- `Constraint Violation Rate` (`CVR@5`, exact `0.0` for Variants C & D)
- `Intra-list Diversity` (`ILD@5 = mean_{i < j} (1 - Sim(r_i, r_j))`)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.core.database import (
    IngredientRecord,
    InMemoryCatalogRepository,
    RecipeIngredientRecord,
    RecipeRecord,
    RecipeStepRecord,
)
from app.schemas.reasoning import ReasoningInput
from app.schemas.recommendations import RecommendationItem
from app.services.coverage import compute_recipe_weighted_coverage, compute_tversky_similarity
from app.services.mmr import compute_recipe_similarity, rerank_with_mmr
from app.services.personalization_lr import (
    FeedbackSample,
    adaptive_lambda_pers,
    blend_personalized_score,
    extract_recipe_feature_vector,
    fit_user_lr_weights,
    predict_preference_prob,
)
from app.services.reasoning import evaluate_recipe_reasoning
from app.services.scoring import (
    compute_main_role_score_g,
    compute_time_score_t,
    rank_recommendations,
    score_recipe_unified,
)

VariantCode = Literal["A", "B", "C", "D"]


@dataclass(frozen=True)
class UserPersona:
    user_id: str
    name: str
    preferred_cuisines: tuple[str, ...]
    preferred_methods: tuple[str, ...]
    prefers_quick_15m: bool
    allergic_ingredient_ids: tuple[str, ...] = ()
    favorite_ingredient_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AblationScenario:
    scenario_id: str
    user_id: str
    eval_timestamp: datetime
    ingredient_ids: list[str]
    main_ingredient_ids: list[str]
    excluded_pantry_ids: list[str]
    allergic_ingredient_ids: list[str]
    favorite_ingredient_ids: list[str]
    cuisine_codes: list[str]
    max_total_minutes: int | None
    desired_hours: float
    relevance_by_recipe: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class VariantMetrics:
    variant: VariantCode
    label: str
    scenario_count: int
    precision_at_5: float
    ndcg_at_5: float
    cvr_at_5: float
    ild_at_5: float


def compute_precision_at_k(
    ranked_ids: list[str],
    relevance_map: dict[str, int],
    k: int = 5,
    rel_threshold: int = 2,
) -> float:
    top = ranked_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for rid in top if relevance_map.get(rid, 0) >= rel_threshold)
    return hits / float(k)


def compute_ndcg_at_k(
    ranked_ids: list[str],
    relevance_map: dict[str, int],
    k: int = 5,
) -> float:
    top = ranked_ids[:k]
    if not top:
        return 0.0
    dcg = 0.0
    for idx, rid in enumerate(top):
        rel = max(0, int(relevance_map.get(rid, 0)))
        dcg += float((1 << rel) - 1) / math.log2(float(idx + 2))

    ideal_rels = sorted((max(0, int(v)) for v in relevance_map.values()), reverse=True)[:k]
    idcg = sum(
        float((1 << rel) - 1) / math.log2(float(idx + 2))
        for idx, rel in enumerate(ideal_rels)
        if rel > 0
    )
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def has_hard_constraint_violation(recipe: RecipeRecord, scenario: AblationScenario) -> bool:
    """Return True if `recipe` violates any active hard safety/filter constraint of `scenario`."""
    rec_ing_ids = {ri.ingredient_id for ri in recipe.ingredients}
    if set(scenario.allergic_ingredient_ids) & rec_ing_ids:
        return True
    if scenario.cuisine_codes and recipe.cuisine_code not in scenario.cuisine_codes:
        return True
    if scenario.max_total_minutes is not None and recipe.total_minutes > scenario.max_total_minutes:
        return True
    non_pantry_ids = {ri.ingredient_id for ri in recipe.ingredients if ri.category != "pantry"}
    if not (non_pantry_ids & set(scenario.ingredient_ids)):
        return True
    return False


def compute_cvr_at_k(
    ranked_ids: list[str],
    recipes_by_id: dict[str, RecipeRecord],
    scenario: AblationScenario,
    k: int = 5,
) -> float:
    top = ranked_ids[:k]
    if not top:
        return 0.0
    violations = sum(
        1
        for rid in top
        if rid in recipes_by_id and has_hard_constraint_violation(recipes_by_id[rid], scenario)
    )
    return violations / float(len(top))


def compute_ild_at_k(
    ranked_ids: list[str],
    recipes_by_id: dict[str, RecipeRecord],
    k: int = 5,
) -> float:
    top = [rid for rid in ranked_ids[:k] if rid in recipes_by_id]
    n = len(top)
    if n < 2:
        return 0.0
    pair_sum = 0.0
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_recipe_similarity(recipes_by_id[top[i]], recipes_by_id[top[j]])
            pair_sum += 1.0 - sim
            pair_count += 1
    return pair_sum / float(pair_count) if pair_count > 0 else 0.0


def build_benchmark_catalog() -> tuple[list[IngredientRecord], list[RecipeRecord]]:
    """Construct a rich, deterministic 24-recipe (`VN`/`EU`/`US`) + 17-ingredient catalog for ablation."""
    ings = [
        IngredientRecord("11111111-1111-4111-8111-111111111101", "ca-chua", "Cà chua", "vegetable"),
        IngredientRecord("11111111-1111-4111-8111-111111111102", "trung-ga", "Trứng gà", "protein", allergen_ids=["egg"]),
        IngredientRecord("11111111-1111-4111-8111-111111111103", "dau-hu", "Đậu hũ", "protein", allergen_ids=["soy"]),
        IngredientRecord("11111111-1111-4111-8111-111111111104", "thit-ba-chi", "Thịt ba chỉ", "protein"),
        IngredientRecord("11111111-1111-4111-8111-111111111105", "hanh-la", "Hành lá", "spice"),
        IngredientRecord("11111111-1111-4111-8111-111111111202", "khoai-tay", "Khoai tây", "vegetable"),
        IngredientRecord("11111111-1111-4111-8111-111111111204", "hanh-tay", "Hành tây", "vegetable"),
        IngredientRecord("11111111-1111-4111-8111-111111111205", "toi", "Tỏi", "spice"),
        IngredientRecord("11111111-1111-4111-8111-111111111209", "bong-cai-xanh", "Bông cải xanh", "vegetable"),
        IngredientRecord("11111111-1111-4111-8111-111111111210", "nam", "Nấm tươi", "vegetable"),
        IngredientRecord("11111111-1111-4111-8111-111111111212", "uc-ga", "Ức gà", "protein"),
        IngredientRecord("11111111-1111-4111-8111-111111111301", "thit-bo", "Thịt bò", "protein"),
        # Exact 5 pantry spices
        IngredientRecord("11111111-1111-4111-8111-111111111106", "muoi", "Muối", "pantry"),
        IngredientRecord("11111111-1111-4111-8111-111111111107", "nuoc-mam", "Nước mắm", "pantry", allergen_ids=["fish"]),
        IngredientRecord("11111111-1111-4111-8111-111111111108", "dau-an", "Dầu ăn", "pantry"),
        IngredientRecord("11111111-1111-4111-8111-111111111109", "duong", "Đường", "pantry"),
        IngredientRecord("11111111-1111-4111-8111-111111111110", "tieu-xay", "Tiêu xay", "pantry"),
    ]
    ing_by_slug = {i.slug: i for i in ings}

    def _ri(slug: str, role: str, dish_role: str = "sub", req: bool = True) -> RecipeIngredientRecord:
        ing = ing_by_slug[slug]
        w = {"core": 4.0, "secondary": 2.0, "spice": 1.0, "optional": 0.0}[role]
        return RecipeIngredientRecord(
            ingredient_id=ing.id,
            name_vi=ing.name_vi,
            category=ing.category,
            is_required=req,
            role=role,
            dish_role=dish_role,
            weight=w,
            grams=100.0,
        )

    specs: list[tuple[str, str, str, str, int, int, list[RecipeIngredientRecord]]] = [
        # Tomato + Egg cluster (diverse methods & times; includes stir-fry clones for MMR test)
        ("trung-xao-ca-chua", "Trứng xào cà chua", "VN", "stir_fry", 5, 10, [_ri("ca-chua", "core", "main"), _ri("trung-ga", "core", "main"), _ri("hanh-la", "optional", "sub", False), _ri("dau-an", "spice"), _ri("nuoc-mam", "spice")]),
        ("trung-bac-ca-chua", "Trứng bác cà chua hành lá", "VN", "stir_fry", 4, 8, [_ri("trung-ga", "core", "main"), _ri("ca-chua", "secondary", "sub"), _ri("hanh-la", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice")]),
        ("canh-ca-chua-trung", "Canh cà chua trứng", "VN", "boil", 5, 10, [_ri("ca-chua", "core", "main"), _ri("trung-ga", "core", "main"), _ri("muoi", "spice"), _ri("dau-an", "spice")]),
        ("omelet-ca-chua-kieu-phap", "Trứng cuộn cà chua kiểu Âu", "EU", "pan_fry", 5, 8, [_ri("trung-ga", "core", "main"), _ri("ca-chua", "secondary", "sub"), _ri("hanh-tay", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        # Tofu cluster
        ("dau-hu-sot-ca-chua", "Đậu hũ sốt cà chua", "VN", "braise", 10, 20, [_ri("dau-hu", "core", "main"), _ri("ca-chua", "secondary", "sub"), _ri("hanh-la", "optional", "sub", False), _ri("muoi", "spice"), _ri("dau-an", "spice")]),
        ("dau-hu-chien-sa-toi", "Đậu hũ áp chảo tỏi tiêu", "VN", "pan_fry", 5, 10, [_ri("dau-hu", "core", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("canh-dau-hu-nam", "Canh đậu hũ nấm tươi", "VN", "boil", 5, 10, [_ri("dau-hu", "core", "main"), _ri("nam", "secondary", "main"), _ri("hanh-la", "optional", "sub", False), _ri("muoi", "spice")]),
        ("dau-hu-kho-nam-tieu", "Đậu hũ kho nấm tiêu đen", "VN", "braise", 10, 25, [_ri("dau-hu", "core", "main"), _ri("nam", "core", "main"), _ri("duong", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        # Pork cluster
        ("thit-kho-trung", "Thịt ba chỉ kho trứng", "VN", "braise", 15, 45, [_ri("thit-ba-chi", "core", "main"), _ri("trung-ga", "secondary", "sub"), _ri("nuoc-mam", "spice"), _ri("duong", "spice"), _ri("tieu-xay", "spice")]),
        ("thit-ba-chi-rang-chay-canh", "Thịt ba chỉ rang cháy cạnh", "VN", "stir_fry", 5, 10, [_ri("thit-ba-chi", "core", "main"), _ri("hanh-la", "spice"), _ri("nuoc-mam", "spice"), _ri("duong", "spice")]),
        ("canh-khoai-tay-thit-bam", "Canh khoai tây thịt heo", "VN", "boil", 10, 20, [_ri("khoai-tay", "core", "main"), _ri("thit-ba-chi", "secondary", "main"), _ri("hanh-la", "optional", "sub", False), _ri("muoi", "spice")]),
        ("ca-chua-nhoi-thit", "Cà chua nhồi thịt sốt đậm đà", "VN", "braise", 10, 20, [_ri("ca-chua", "core", "main"), _ri("thit-ba-chi", "core", "main"), _ri("nuoc-mam", "spice"), _ri("dau-an", "spice"), _ri("tieu-xay", "spice")]),
        # Chicken & Broccoli / Mushroom cluster (VN / EU / US)
        ("uc-ga-ap-chao-toi", "Ức gà áp chảo tỏi tiêu kiểu Mỹ", "US", "pan_fry", 5, 10, [_ri("uc-ga", "core", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("ga-xao-bong-cai-xanh", "Ức gà xào bông cải xanh", "VN", "stir_fry", 5, 9, [_ri("uc-ga", "core", "main"), _ri("bong-cai-xanh", "core", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice")]),
        ("ga-xao-nam-hanh-tay", "Ức gà xào nấm hành tây", "VN", "stir_fry", 6, 9, [_ri("uc-ga", "core", "main"), _ri("nam", "secondary", "sub"), _ri("hanh-tay", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice")]),
        ("ga-dut-lo-khoai-tay", "Ức gà đút lò khoai tây thảo mộc", "EU", "bake", 10, 35, [_ri("uc-ga", "core", "main"), _ri("khoai-tay", "core", "main"), _ri("hanh-tay", "secondary", "sub"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("sup-ga-khoai-tay-kieu-au", "Súp gà khoai tây kiểu Âu", "EU", "boil", 10, 25, [_ri("uc-ga", "core", "main"), _ri("khoai-tay", "secondary", "sub"), _ri("hanh-tay", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        # Beef cluster (VN / EU / US)
        ("bo-xao-bong-cai", "Thịt bò xào bông cải tỏi", "VN", "stir_fry", 5, 8, [_ri("thit-bo", "core", "main"), _ri("bong-cai-xanh", "core", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("bo-luc-lac-khoai-tay", "Bò lúc lắc hành tây khoai tây", "VN", "stir_fry", 10, 12, [_ri("thit-bo", "core", "main"), _ri("khoai-tay", "secondary", "sub"), _ri("hanh-tay", "spice"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("bo-ham-khoai-tay-ca-chua", "Bò hầm khoai tây cà chua kiểu Âu", "EU", "braise", 15, 45, [_ri("thit-bo", "core", "main"), _ri("khoai-tay", "core", "main"), _ri("ca-chua", "secondary", "sub"), _ri("hanh-tay", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("beef-steak-khoai-tay-nghien", "Bít tết bò áp chảo khoai tây kiểu Mỹ", "US", "pan_fry", 5, 10, [_ri("thit-bo", "core", "main"), _ri("khoai-tay", "secondary", "sub"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        # Vegetable-centric cluster
        ("bong-cai-nam-xao-toi", "Bông cải xanh xào nấm tỏi", "EU", "stir_fry", 5, 8, [_ri("bong-cai-xanh", "core", "main"), _ri("nam", "secondary", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice")]),
        ("khoai-tay-dut-lo-toi", "Khoai tây đút lò tỏi tiêu kiểu Mỹ", "US", "bake", 10, 30, [_ri("khoai-tay", "core", "main"), _ri("toi", "spice"), _ri("dau-an", "spice"), _ri("muoi", "spice"), _ri("tieu-xay", "spice")]),
        ("canh-nam-ca-chua-thanh-mat", "Canh nấm cà chua thanh đạm", "VN", "boil", 5, 9, [_ri("nam", "core", "main"), _ri("ca-chua", "secondary", "sub"), _ri("hanh-la", "optional", "sub", False), _ri("muoi", "spice")]),
    ]

    recipes: list[RecipeRecord] = []
    for idx, (slug, name_vi, cuisine, method, prep_m, cook_m, r_ings) in enumerate(specs, start=1):
        flat_allergens: list[str] = []
        for ri in r_ings:
            ing_obj = next(i for i in ings if i.id == ri.ingredient_id)
            for al in ing_obj.allergen_ids:
                if al not in flat_allergens:
                    flat_allergens.append(al)

        recipes.append(
            RecipeRecord(
                id=f"22222222-2222-4222-8222-{idx:012d}",
                slug=slug,
                name_vi=name_vi,
                cuisine_code=cuisine,  # type: ignore[arg-type]
                prep_minutes=prep_m,
                cook_minutes=cook_m,
                status="published",
                cooking_method=method,
                base_servings=2,
                allergen_ids=flat_allergens,
                ingredients=r_ings,
                steps=[RecipeStepRecord(step_no=1, instruction="Chế biến chín đều.", estimated_minutes=cook_m)],
            )
        )
    return ings, recipes


def _rubric_relevance(
    recipe: RecipeRecord,
    scenario: AblationScenario,
    persona: UserPersona,
    active_pantry_ids: set[str],
) -> int:
    """Assign objective graded relevance rel in {0, 1, 2, 3} BEFORE running any ranker (`test-plan.md` §3.2)."""
    if has_hard_constraint_violation(recipe, scenario):
        return 0

    available = set(scenario.ingredient_ids) | (active_pantry_ids - set(scenario.excluded_pantry_ids))
    c_val = compute_recipe_weighted_coverage(recipe, available)
    if c_val < 0.50:
        return 0

    g_val = compute_main_role_score_g(recipe, scenario.ingredient_ids, scenario.main_ingredient_ids)
    t_val = compute_time_score_t(recipe.total_minutes, scenario.desired_hours)

    persona_match = (
        recipe.cuisine_code in persona.preferred_cuisines
        and (recipe.cooking_method or "") in persona.preferred_methods
        and (not persona.prefers_quick_15m or recipe.total_minutes <= 15)
    )
    utility = (0.55 * c_val + 0.25 * g_val + 0.20 * t_val) + (0.15 if persona_match else 0.0)

    if utility >= 0.88 and c_val >= 0.75:
        return 3
    if utility >= 0.72 and c_val >= 0.60:
        return 2
    return 1


def generate_ablation_dataset(
    seed: int = 20261115,
    num_scenarios: int = 120,
) -> tuple[
    InMemoryCatalogRepository,
    list[AblationScenario],
    dict[str, list[FeedbackSample]],
]:
    """Generate `num_scenarios` (`>= 100`) deterministic scenarios + strictly earlier training feedback (`temporal split`)."""
    rng = random.Random(seed)
    ings, recipes = build_benchmark_catalog()
    repo = InMemoryCatalogRepository(ingredients=ings, recipes=recipes)
    active_pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    non_pantry = [i for i in ings if i.category != "pantry" and i.is_active]
    ing_by_slug = {i.slug: i.id for i in ings}

    personas = [
        UserPersona(
            user_id="00000000-0000-4000-8000-000000000101",
            name="Quick VN Stir-Fry & Soup Lover (Egg-Free)",
            preferred_cuisines=("VN",),
            preferred_methods=("stir_fry", "boil"),
            prefers_quick_15m=True,
            allergic_ingredient_ids=(ing_by_slug["trung-ga"],),
            favorite_ingredient_ids=(ing_by_slug["dau-hu"], ing_by_slug["bong-cai-xanh"]),
        ),
        UserPersona(
            user_id="00000000-0000-4000-8000-000000000102",
            name="Western Pan-Fry & Bake Enthusiast (Soy-Free)",
            preferred_cuisines=("EU", "US"),
            preferred_methods=("pan_fry", "bake"),
            prefers_quick_15m=False,
            allergic_ingredient_ids=(ing_by_slug["dau-hu"],),
            favorite_ingredient_ids=(ing_by_slug["thit-bo"], ing_by_slug["khoai-tay"]),
        ),
        UserPersona(
            user_id="00000000-0000-4000-8000-000000000103",
            name="Traditional Slow-Braise Comfort Cook",
            preferred_cuisines=("VN", "EU"),
            preferred_methods=("braise",),
            prefers_quick_15m=False,
            allergic_ingredient_ids=(),
            favorite_ingredient_ids=(ing_by_slug["thit-ba-chi"], ing_by_slug["ca-chua"]),
        ),
        UserPersona(
            user_id="00000000-0000-4000-8000-000000000104",
            name="High-Protein Quick Gym Cook",
            preferred_cuisines=("US", "VN"),
            preferred_methods=("pan_fry", "stir_fry"),
            prefers_quick_15m=True,
            allergic_ingredient_ids=(),
            favorite_ingredient_ids=(ing_by_slug["uc-ga"], ing_by_slug["thit-bo"]),
        ),
    ]

    # Temporal split boundary: training interactions strictly in [T0 - 14d, T0 - 1d]; evaluation in [T0, T0 + 5d]
    t0 = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    past_feedback_by_user: dict[str, list[FeedbackSample]] = {}
    for p in personas:
        samples: list[FeedbackSample] = []
        for idx, rec in enumerate(recipes):
            # Disjoint recipe subset (even indices) rated in the past so LR generalizes via features, not memorization!
            if idx % 2 != 0:
                continue
            if set(p.allergic_ingredient_ids) & {ri.ingredient_id for ri in rec.ingredients}:
                continue
            likes = (
                rec.cuisine_code in p.preferred_cuisines
                and (rec.cooking_method or "") in p.preferred_methods
                and (not p.prefers_quick_15m or rec.total_minutes <= 15)
            )
            rating = 5 if likes else 1
            samples.append(
                FeedbackSample(
                    user_id=p.user_id,
                    recipe_id=rec.id,
                    rating=rating,
                    updated_at=t0 - timedelta(days=10, hours=idx),
                )
            )
        past_feedback_by_user[p.user_id] = samples

    basket_templates = [
        ["ca-chua", "trung-ga", "dau-hu"],
        ["uc-ga", "bong-cai-xanh", "khoai-tay", "toi"],
        ["thit-bo", "khoai-tay", "ca-chua", "hanh-tay", "toi"],
        ["dau-hu", "nam", "ca-chua", "toi"],
        ["thit-ba-chi", "ca-chua", "khoai-tay", "hanh-la"],
        ["uc-ga", "nam", "hanh-tay", "toi"],
        ["thit-bo", "bong-cai-xanh", "khoai-tay", "toi"],
        ["ca-chua", "nam", "dau-hu", "hanh-la"],
    ]

    scenarios: list[AblationScenario] = []
    pantry_list = sorted(active_pantry_ids)

    for i in range(num_scenarios):
        persona = personas[i % len(personas)]
        base_slugs = list(basket_templates[i % len(basket_templates)])
        # Add 1 deterministic random extra non-pantry item for diversity across all 120 scenarios
        extra_cand = rng.choice(non_pantry)
        if extra_cand.slug not in base_slugs and extra_cand.id not in persona.allergic_ingredient_ids:
            base_slugs.append(extra_cand.slug)

        # Ensure basket does not contain the user's own allergic ingredient
        u_ids = [
            ing_by_slug[s]
            for s in base_slugs
            if ing_by_slug[s] not in persona.allergic_ingredient_ids
        ]
        if not u_ids:
            u_ids = [ing_by_slug["ca-chua"]]

        main_ids = [u_ids[0]] if (i % 2 == 0) else []
        excluded_pantry = [pantry_list[i % len(pantry_list)]] if (i % 4 == 0) else []
        max_mins = 20 if (persona.prefers_quick_15m and i % 3 == 0) else None
        cuisine_filter = list(persona.preferred_cuisines) if (i % 5 == 0) else []
        desired_h = 0.25 if persona.prefers_quick_15m else 0.75

        scen = AblationScenario(
            scenario_id=f"SCEN-{i + 1:03d}",
            user_id=persona.user_id,
            eval_timestamp=t0 + timedelta(hours=i),
            ingredient_ids=u_ids,
            main_ingredient_ids=main_ids,
            excluded_pantry_ids=excluded_pantry,
            allergic_ingredient_ids=list(persona.allergic_ingredient_ids),
            favorite_ingredient_ids=list(persona.favorite_ingredient_ids),
            cuisine_codes=cuisine_filter,
            max_total_minutes=max_mins,
            desired_hours=desired_h,
        )
        rel_map = {
            rec.id: _rubric_relevance(rec, scen, persona, active_pantry_ids)
            for rec in recipes
        }
        scenarios.append(
            AblationScenario(
                **{**scen.__dict__, "relevance_by_recipe": rel_map}
            )
        )

    return repo, scenarios, past_feedback_by_user


def run_variant_ranking(
    variant: VariantCode,
    repo: InMemoryCatalogRepository,
    scenario: AblationScenario,
    learned_thetas: dict[str, tuple[list[float], int]],
    top_k: int = 5,
) -> list[str]:
    """Execute exact ranking pipeline for Variant `A`, `B`, `C`, or `D` and return Top-K recipe IDs."""
    recipes = repo.get_all_published_recipes()
    recipes_by_id = {r.id: r for r in recipes}
    active_pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    available_set = set(scenario.ingredient_ids) | (active_pantry_ids - set(scenario.excluded_pantry_ids))

    if variant == "A":
        # Variant A: Uniform ingredient overlap count (no role weights, no TP 04 hard constraint filter, no MMR)
        scored_a: list[tuple[int, int, str]] = []
        for rec in recipes:
            rec_ings = {ri.ingredient_id for ri in rec.ingredients}
            overlap = len(rec_ings & available_set)
            if overlap > 0:
                scored_a.append((-overlap, rec.total_minutes, rec.id))
        scored_a.sort()
        return [rid for _neg_ov, _mins, rid in scored_a[:top_k]]

    if variant == "B":
        # Variant B: Asymmetric Tversky Similarity (alpha=0.3, beta=2.0 — TP 06 standalone baseline)
        scored_b: list[tuple[float, int, str]] = []
        for rec in recipes:
            req_ids = [ri.ingredient_id for ri in rec.ingredients if ri.is_required]
            tv = compute_tversky_similarity(available_set, req_ids, alpha=0.3, beta=2.0)
            if tv > 0.0:
                scored_b.append((-round(tv, 6), rec.total_minutes, rec.id))
        scored_b.sort()
        return [rid for _neg_tv, _mins, rid in scored_b[:top_k]]

    # Variants C & D: Pass through TP 04 3-State Open-World Reasoning & Hard Constraint Gate (`BLOCKED` filtered!)
    r_input = ReasoningInput(
        ingredient_ids=scenario.ingredient_ids,
        main_ingredient_ids=scenario.main_ingredient_ids,
        excluded_pantry_ids=scenario.excluded_pantry_ids,
        allergic_ingredient_ids=scenario.allergic_ingredient_ids,
        favorite_ingredient_ids=scenario.favorite_ingredient_ids,
        cuisine_codes=scenario.cuisine_codes,  # type: ignore[arg-type]
        max_total_minutes=scenario.max_total_minutes,
        include_missing=True,
    )

    items: list[RecommendationItem] = []
    theta_u, sample_count = learned_thetas.get(scenario.user_id, ([], 0))
    lam_pers = adaptive_lambda_pers(sample_count, max_lambda=0.12, min_samples=3) if variant == "D" else 0.0

    for rec in recipes:
        ev = evaluate_recipe_reasoning(rec, r_input, active_pantry_ids)
        if ev.status_v1_1 == "BLOCKED":
            continue
        item = score_recipe_unified(
            recipe=rec,
            evaluation=ev,
            ingredient_ids=scenario.ingredient_ids,
            main_ingredient_ids=scenario.main_ingredient_ids,
            desired_hours=scenario.desired_hours,
            favorite_ingredient_ids=scenario.favorite_ingredient_ids,
        )
        if variant == "D" and lam_pers > 0.0 and theta_u and compute_recipe_weighted_coverage(rec, available_set) >= 0.60:
            x_vec = extract_recipe_feature_vector(rec)
            prob = predict_preference_prob(x_vec, theta_u)
            blended = blend_personalized_score(item.score, prob, lambda_pers=lam_pers)
            item = item.model_copy(update={"score": blended})
        items.append(item)

    ranked = rank_recommendations(items)
    diversified = rerank_with_mmr(ranked, recipes_by_id=recipes_by_id, top_k=top_k, lambda_mmr=0.7)
    return [it.recipe.id for it in diversified[:top_k]]


def evaluate_all_variants(
    seed: int = 20261115,
    num_scenarios: int = 120,
    top_k: int = 5,
) -> list[VariantMetrics]:
    """Run full reproducible A/B/C/D ablation experiment and return summary metrics (`AI-04`, `DEF-07`)."""
    repo, scenarios, past_feedback_by_user = generate_ablation_dataset(
        seed=seed, num_scenarios=num_scenarios
    )
    recipes_by_id = {r.id: r for r in repo.get_all_published_recipes()}

    # Fit LR weights strictly on past interactions (`eval_timestamp > all feedback.updated_at`)
    learned_thetas: dict[str, tuple[list[float], int]] = {}
    min_eval_ts = min(s.eval_timestamp for s in scenarios)
    for uid, samples in past_feedback_by_user.items():
        assert all(fb.updated_at < min_eval_ts for fb in samples), "Temporal split violated!"
        learned_thetas[uid] = fit_user_lr_weights(recipes_by_id, samples)

    labels: dict[VariantCode, str] = {
        "A": "Uniform Overlap Count (No Role Weights / No Hard Filter)",
        "B": "Tversky Similarity Baseline (alpha=0.3, beta=2.0 — TP 06)",
        "C": "3-State Reasoning + Weighted 4-2-1-0 + MCDA (C,G,T,P) + MMR",
        "D": "Variant C + Logistic Regression Personalization (Temporal Split — TP 08)",
    }

    results: list[VariantMetrics] = []
    for var in ("A", "B", "C", "D"):
        v_code: VariantCode = var  # type: ignore[assignment]
        p_sum = 0.0
        ndcg_sum = 0.0
        cvr_sum = 0.0
        ild_sum = 0.0

        for scen in scenarios:
            ranked_ids = run_variant_ranking(
                variant=v_code,
                repo=repo,
                scenario=scen,
                learned_thetas=learned_thetas,
                top_k=top_k,
            )
            p_sum += compute_precision_at_k(ranked_ids, scen.relevance_by_recipe, k=top_k)
            ndcg_sum += compute_ndcg_at_k(ranked_ids, scen.relevance_by_recipe, k=top_k)
            cvr_sum += compute_cvr_at_k(ranked_ids, recipes_by_id, scen, k=top_k)
            ild_sum += compute_ild_at_k(ranked_ids, recipes_by_id, k=top_k)

        n = float(len(scenarios))
        results.append(
            VariantMetrics(
                variant=v_code,
                label=labels[v_code],
                scenario_count=len(scenarios),
                precision_at_5=round(p_sum / n, 4),
                ndcg_at_5=round(ndcg_sum / n, 4),
                cvr_at_5=round(cvr_sum / n, 4),
                ild_at_5=round(ild_sum / n, 4),
            )
        )
    return results
