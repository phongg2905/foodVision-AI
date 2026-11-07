"""Stage 2 Automated Verification Suite for TV2 (Phong Phạm).

Covers:
- Card 1 (`[GĐ2 - TP05, TP06, TP07]`):
  - MVP Rule-Based Scoring v1.0 (`C, E, T, P, S`) — all 7 canonical math cases from Table E.1 in `test-cases.md`
    (`S = 89.0`, `S = 68.1`, `S = 100.0`, `S = 54.5`, `C = 0`, `max_total_minutes`, `preferred_cuisine_codes`)
  - TP 05 Weighted Ingredient Coverage (`MATH-03`: `6/9 ≈ 0.667` and `5/9 ≈ 0.556`)
  - TP 06 Tversky Similarity Baseline B (`MATH-04`: `T_{0.3, 2.0} = 0.60`)
  - TP 07 & TP 14 MCDA 5-Criteria Scoring v1.1 & Linear XAI Breakdown (`MATH-05`: `[33.33, 25.00, 15.00, 2.50, 5.00] -> 80.83`)
- Card 2 (`[GĐ2 - TP09]`):
  - TP 09 Maximal Marginal Relevance (MMR) Top-K Diversification (`MATH-06`: `0.412 < 0.556`)
  - `POST /api/v1/recommendations` contract (`TC-10`..`TC-14`, `TC-32`..`TC-35`, `TC-37`)
  - `scan_id` ownership verification & `scan_ingredients` sync (`TC-20`, `SEC-06`: `404 SCAN_NOT_OWNED`, `401 UNAUTHORIZED`)
  - `PERF-02` / `NFR-03` latency benchmark (`< 1.0s` on `>= 500` published recipes)
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core.database import (
    InMemoryCatalogRepository,
    RecipeIngredientRecord,
    RecipeRecord,
    RecipeStepRecord,
    ScanSessionRecord,
    _default_seed_ingredients,
    _default_seed_recipes,
    get_catalog_repo,
)
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_HANH_LA,
    ING_INACTIVE,
    ING_MUOI,
    ING_NUOC_MAM,
    ING_THIT_BA_CHI,
    ING_TRUNG_GA,
    REC_CANH_CA_CHUA_TRUNG,
    REC_THIT_KHO_TRUNG,
    REC_TRUNG_XAO_CA_CHUA,
)
from app.main import create_app
from app.schemas.reasoning import ReasoningInput
from app.schemas.recipes import CuisineCode, RecipeSummary
from app.schemas.recommendations import RecommendationItem, ScoreBreakdown
from app.services.coverage import (
    compute_tversky_similarity,
    compute_weighted_coverage,
)
from app.services.mmr import compute_mmr_score, rerank_with_mmr
from app.services.reasoning import evaluate_recipe_reasoning
from app.services.scoring import (
    compute_mcda_v1_1_from_features,
    compute_mvp_score_components,
    score_recipe_mcda_v1_1,
    score_recipe_v1_0,
)


# ==============================================================================
# 1. MVP Contract Scoring v1.0 — Table E.1 (All 7 Mathematical Test Cases)
# ==============================================================================


def test_scoring_v1_0_all_7_canonical_cases_table_e1(
    repo: InMemoryCatalogRepository,
) -> None:
    """Verify all 7 canonical cases in Table E.1 of `docs/06-testing/test-cases.md`."""
    pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    trung_xao = repo.get_published_recipe_by_id(REC_TRUNG_XAO_CA_CHUA)
    assert trung_xao is not None

    # Case 1: 2/2 required main (Trứng gà, Cà chua), 0/1 optional main (Hành lá), X=[], 13m -> S = 89.0, ready
    ev1 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    item1 = score_recipe_v1_0(trung_xao, ev1)
    assert item1.availability == "ready"
    assert item1.score == 89.0
    assert item1.score_breakdown.C == 0.8
    assert item1.score_breakdown.E == 1.0
    assert item1.score_breakdown.T == 1.0
    assert item1.score_breakdown.P == 1.0

    # Case 2: 2/2 required main, 0/1 optional main, X=[ING_NUOC_MAM], 13m -> S = 68.1, missing
    ev2 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
            excluded_pantry_ids=[ING_NUOC_MAM],
        ),
        pantry_ids,
    )
    item2 = score_recipe_v1_0(trung_xao, ev2)
    assert item2.availability == "missing"
    assert item2.score == 68.1
    assert item2.missing_required_ingredient_ids == [ING_NUOC_MAM]
    assert round(item2.score_breakdown.C, 3) == 0.571
    assert round(item2.score_breakdown.E, 3) == 0.667

    # Case 3: All 3 main ingredients (Cà chua, Trứng gà, Hành lá), X=[], 13m -> S = 100.0, ready
    ev3 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA, ING_HANH_LA],
            excluded_pantry_ids=[],
        ),
        pantry_ids,
    )
    item3 = score_recipe_v1_0(trung_xao, ev3)
    assert item3.availability == "ready"
    assert item3.score == 100.0
    assert item3.score_breakdown.C == 1.0
    assert item3.score_breakdown.E == 1.0

    # Case 4: Only 1/2 required main (Cà chua), 0/1 optional main, X=[], 13m -> S = 54.5, missing
    ev4 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_CA_CHUA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    item4 = score_recipe_v1_0(trung_xao, ev4)
    assert item4.availability == "missing"
    assert item4.score == 54.5
    assert item4.score_breakdown.C == 0.4
    assert item4.score_breakdown.E == 0.5

    # Case 5: No required/optional main ingredient in U (only Thịt ba chỉ for Trứng xào cà chua) -> BLOCKED
    ev5 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_THIT_BA_CHI], excluded_pantry_ids=[]),
        pantry_ids,
    )
    assert ev5.status_v1_1 == "BLOCKED"
    assert "no_matched_main_ingredient" in ev5.blocked_reasons

    # Case 6: 60-minute recipe (Thịt kho trứng) with max_total_minutes=15 -> BLOCKED before scoring
    thit_kho = repo.get_published_recipe_by_id(REC_THIT_KHO_TRUNG)
    assert thit_kho is not None
    ev6 = evaluate_recipe_reasoning(
        thit_kho,
        ReasoningInput(
            ingredient_ids=[ING_THIT_BA_CHI, ING_TRUNG_GA],
            max_total_minutes=15,
        ),
        pantry_ids,
    )
    assert ev6.status_v1_1 == "BLOCKED"
    assert "exceeds_max_total_minutes" in ev6.blocked_reasons

    # Case 7: Soft preference mismatch (`P = 0.0`) reduces total score by exactly 10.0 points
    score_p1, _ = compute_mvp_score_components(
        required_main_count=2,
        matched_required_main_count=2,
        optional_main_count=1,
        matched_optional_main_count=0,
        missing_pantry_count=0,
        total_minutes=13,
        cuisine_code="US",
        preferred_cuisine_codes=[],
    )
    score_p0, br_p0 = compute_mvp_score_components(
        required_main_count=2,
        matched_required_main_count=2,
        optional_main_count=1,
        matched_optional_main_count=0,
        missing_pantry_count=0,
        total_minutes=13,
        cuisine_code="US",
        preferred_cuisine_codes=["VN"],
    )
    assert br_p0.P == 0.0
    assert round(score_p1 - score_p0, 1) == 10.0


# ==============================================================================
# 2. TP 05 Weighted Coverage (`MATH-03`) & TP 06 Tversky Baseline B (`MATH-04`)
# ==============================================================================


def test_tp05_weighted_coverage_math03() -> None:
    """MATH-03: weights={ca_chua:4, trung:3, dau:1, muoi:1}, available={ca_chua, dau, muoi} -> C = 6/9."""
    weights = {"ca_chua": 4.0, "trung": 3.0, "dau": 1.0, "muoi": 1.0}
    c_val = compute_weighted_coverage(weights, {"ca_chua", "dau", "muoi"})
    assert round(c_val, 3) == 0.667
    assert abs(c_val - (6.0 / 9.0)) < 1e-9

    # When muoi is excluded in X -> confirmed_available = {ca_chua, dau} -> C = 5/9 ≈ 0.556
    c_val_no_salt = compute_weighted_coverage(weights, {"ca_chua", "dau"})
    assert round(c_val_no_salt, 3) == 0.556


def test_tp06_tversky_similarity_baseline_b_math04() -> None:
    """MATH-04: A={ca_chua, dau, muoi}, R={ca_chua, trung, dau, muoi}, alpha=0.3, beta=2.0 -> 0.60."""
    sim = compute_tversky_similarity(
        available_ids={"ca_chua", "dau", "muoi"},
        recipe_required_ids={"ca_chua", "trung", "dau", "muoi"},
        alpha=0.3,
        beta=2.0,
    )
    assert sim == pytest.approx(0.60, abs=1e-9)


# ==============================================================================
# 3. TP 07 & TP 14 MCDA 5-Criteria Scoring v1.1 & Linear XAI Breakdown (`MATH-05`)
# ==============================================================================


def test_tp07_and_tp14_mcda_v1_1_and_xai_breakdown_math05(
    repo: InMemoryCatalogRepository,
) -> None:
    """MATH-05: C=6/9, G=1, T=1, P=0.5, Q=1 -> [33.33, 25.00, 15.00, 2.50, 5.00] -> S_base = 80.83."""
    score_base, _feats, contribs = compute_mcda_v1_1_from_features(
        c_val=6.0 / 9.0,
        g_val=1.0,
        t_val=1.0,
        p_val=0.5,
        q_val=1.0,
    )
    assert contribs.C == 33.33
    assert contribs.G == 25.00
    assert contribs.T == 15.00
    assert contribs.P == 2.50
    assert contribs.Q == 5.00
    assert score_base == 80.83

    # Also verify end-to-end on Trứng xào cà chua with U={Cà chua}, X=[]
    pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    trung_xao = repo.get_published_recipe_by_id(REC_TRUNG_XAO_CA_CHUA)
    assert trung_xao is not None
    ev = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_CA_CHUA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    confirmed_avail = {ING_CA_CHUA} | pantry_ids
    mcda_eval = score_recipe_mcda_v1_1(
        recipe=trung_xao,
        evaluation=ev,
        confirmed_available_ids=confirmed_avail,
        focus_ids={ING_CA_CHUA},
        preferred_cuisine_codes=[],
        ref_minutes=15,
    )
    assert mcda_eval.state == "UNKNOWN"
    assert mcda_eval.score_base == 80.83


# ==============================================================================
# 4. TP 09 Maximal Marginal Relevance (MMR) Top-K Diversification (`MATH-06`)
# ==============================================================================


def test_tp09_mmr_diversification_math06() -> None:
    """MATH-06: lambda_mmr=0.7; Variant Soup (Rel=0.91, Sim=0.75 -> 0.412) vs Spaghetti (Rel=0.88, Sim=0.20 -> 0.556)."""
    mmr_soup_variant = compute_mmr_score(rel_score=0.91, max_similarity_to_selected=0.75, lambda_mmr=0.7)
    mmr_spaghetti = compute_mmr_score(rel_score=0.88, max_similarity_to_selected=0.20, lambda_mmr=0.7)
    assert mmr_soup_variant == pytest.approx(0.412, abs=1e-6)
    assert mmr_spaghetti == pytest.approx(0.556, abs=1e-6)
    assert mmr_spaghetti > mmr_soup_variant

    def _make_item(rec_id: str, slug: str, name: str, score: float) -> RecommendationItem:
        return RecommendationItem(
            recipe=RecipeSummary(
                id=rec_id,
                slug=slug,
                name_vi=name,
                cuisine_code="VN",
                prep_minutes=5,
                cook_minutes=10,
                total_minutes=15,
                cover_image_url=None,
            ),
            availability="ready",
            score=score,
            matched_ingredient_ids=[ING_CA_CHUA],
            missing_required_ingredient_ids=[],
            missing_optional_ingredient_ids=[],
            score_breakdown=ScoreBreakdown(C=1.0, E=1.0, T=1.0, P=1.0),
            explanation_vi="OK",
        )

    item_canh_goc = _make_item("r1", "canh-ca-chua", "Canh cà chua", 95.0)
    item_canh_bien_the = _make_item("r2", "canh-ca-chua-2", "Canh cà chua biến thể", 91.0)
    item_mi_y = _make_item("r3", "mi-y-sot-ca", "Mì Ý sốt cà chua", 88.0)

    sim_matrix = {
        ("r2", "r1"): 0.75,
        ("r1", "r2"): 0.75,
        ("r3", "r1"): 0.20,
        ("r1", "r3"): 0.20,
        ("r2", "r3"): 0.20,
        ("r3", "r2"): 0.20,
    }
    reranked = rerank_with_mmr(
        items=[item_canh_goc, item_canh_bien_the, item_mi_y],
        recipes_by_id={},
        top_k=3,
        lambda_mmr=0.7,
        similarity_fn=lambda a, b: sim_matrix.get((a, b), 0.0),
    )
    assert [it.recipe.id for it in reranked] == ["r1", "r3", "r2"]


# ==============================================================================
# 5. API Endpoint `POST /api/v1/recommendations` (`TC-10`..`TC-14`, `TC-32`..`TC-37`)
# ==============================================================================


def test_post_recommendations_endpoint_contract_and_filters(client: TestClient) -> None:
    # TC-10 & TC-12: Have Cà chua & Trứng gà, X=[] -> Canh cà chua trứng (100.0, ready) & Trứng xào cà chua (89.0, ready)
    # appear before Đậu hũ sốt cà chua (missing Đậu hũ) and Thịt kho trứng (missing Thịt ba chỉ)
    res = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "excluded_pantry_ids": [],
            "include_missing": True,
            "limit": 20,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    items = data["items"]
    availabilities = [it["availability"] for it in items]
    # All "ready" items must come strictly before "missing" items
    assert availabilities == ["ready", "ready", "missing", "missing"]

    by_id = {it["recipe"]["id"]: it for it in items}
    assert by_id[REC_TRUNG_XAO_CA_CHUA]["score"] == 89.0
    assert by_id[REC_TRUNG_XAO_CA_CHUA]["availability"] == "ready"
    assert by_id[REC_CANH_CA_CHUA_TRUNG]["score"] == 100.0
    assert by_id[REC_CANH_CA_CHUA_TRUNG]["availability"] == "ready"

    # TC-32: Exclude Nước mắm (`X=[ING_NUOC_MAM]`) -> Trứng xào cà chua drops to 68.1 and "missing"
    res_excl = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "excluded_pantry_ids": [ING_NUOC_MAM],
        },
    )
    assert res_excl.status_code == 200
    by_id_excl = {it["recipe"]["id"]: it for it in res_excl.json()["items"]}
    tx = by_id_excl[REC_TRUNG_XAO_CA_CHUA]
    assert tx["score"] == 68.1
    assert tx["availability"] == "missing"
    assert tx["missing_required_ingredient_ids"] == [ING_NUOC_MAM]

    # TC-33: include_missing=False -> returns ONLY "ready" recipes
    res_ready_only = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "excluded_pantry_ids": [ING_NUOC_MAM],
            "include_missing": False,
        },
    )
    assert res_ready_only.status_code == 200
    ready_items = res_ready_only.json()["items"]
    assert all(it["availability"] == "ready" for it in ready_items)
    assert [it["recipe"]["id"] for it in ready_items] == [REC_CANH_CA_CHUA_TRUNG]

    # TC-13: Hard filter `cuisine_codes=["US"]` excludes VN recipes (`items=[]`)
    res_cuisine_hard = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "cuisine_codes": ["US"],
        },
    )
    assert res_cuisine_hard.status_code == 200
    assert res_cuisine_hard.json()["total"] == 0

    # TC-35: Soft preference `preferred_cuisine_codes=["US"]` keeps VN recipes but sets P=0.0 (-10.0 pts)
    res_pref = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "preferred_cuisine_codes": ["US"],
        },
    )
    assert res_pref.status_code == 200
    by_id_pref = {it["recipe"]["id"]: it for it in res_pref.json()["items"]}
    assert by_id_pref[REC_TRUNG_XAO_CA_CHUA]["score_breakdown"]["P"] == 0.0
    assert by_id_pref[REC_TRUNG_XAO_CA_CHUA]["score"] == 79.0  # 89.0 - 10.0

    # TC-34: No recipe matches both main ingredient and max_total_minutes=15 -> 200 OK with items=[]
    res_empty = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_THIT_BA_CHI],
            "max_total_minutes": 15,
        },
    )
    assert res_empty.status_code == 200
    assert res_empty.json() == {"items": [], "total": 0, "limit": 20}

    # TC-37(1): Passing pantry UUID in ingredient_ids -> 422 INVALID_INGREDIENTS (`pantry_in_main_list`)
    res_invalid_1 = client.post(
        "/api/v1/recommendations",
        json={"ingredient_ids": [ING_MUOI]},
    )
    assert res_invalid_1.status_code == 422
    err1 = res_invalid_1.json()
    assert err1["code"] == "INVALID_INGREDIENTS"
    assert err1["details"]["invalid_ids"] == [ING_MUOI]
    assert err1["details"]["reason"] == "pantry_in_main_list"

    # TC-37(2): Passing main ingredient UUID in excluded_pantry_ids -> 422 INVALID_INGREDIENTS (`non_pantry_in_excluded_list`)
    res_invalid_2 = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_TRUNG_GA],
            "excluded_pantry_ids": [ING_CA_CHUA],
        },
    )
    assert res_invalid_2.status_code == 422
    err2 = res_invalid_2.json()
    assert err2["code"] == "INVALID_INGREDIENTS"
    assert err2["details"]["invalid_ids"] == [ING_CA_CHUA]
    assert err2["details"]["reason"] == "non_pantry_in_excluded_list"

    # TC-37(3): Passing unknown or inactive UUID -> 422 INVALID_INGREDIENTS (`unknown_or_inactive_id`)
    res_invalid_3 = client.post(
        "/api/v1/recommendations",
        json={"ingredient_ids": [ING_INACTIVE]},
    )
    assert res_invalid_3.status_code == 422
    err3 = res_invalid_3.json()
    assert err3["code"] == "INVALID_INGREDIENTS"
    assert err3["details"]["invalid_ids"] == [ING_INACTIVE]
    assert err3["details"]["reason"] == "unknown_or_inactive_id"


# ==============================================================================
# 6. `scan_id` Ownership & Sync (`TC-20`, `SEC-06`) + Latency Benchmark (`PERF-02`)
# ==============================================================================


def test_post_recommendations_scan_id_ownership_tc20_sec06(
    repo: InMemoryCatalogRepository,
    client: TestClient,
) -> None:
    scan_uuid = "44444444-4444-4444-8444-444444444401"
    user_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    user_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    repo.register_scan_session(
        ScanSessionRecord(
            id=scan_uuid,
            user_id=user_a,
            model_id="55555555-5555-4555-8555-555555555501",
            ingredient_ids=[],
        )
    )

    # 1. Missing Authorization header when scan_id is provided -> 401 UNAUTHORIZED
    res_unauth = client.post(
        "/api/v1/recommendations",
        json={"ingredient_ids": [ING_CA_CHUA], "scan_id": scan_uuid},
    )
    assert res_unauth.status_code == 401
    assert res_unauth.json()["code"] == "UNAUTHORIZED"

    # 2. User B tries to use User A's scan_id -> 404 SCAN_NOT_OWNED (SEC-06)
    res_wrong_owner = client.post(
        "/api/v1/recommendations",
        headers={"Authorization": f"Bearer user:{user_b}"},
        json={"ingredient_ids": [ING_CA_CHUA], "scan_id": scan_uuid},
    )
    assert res_wrong_owner.status_code == 404
    assert res_wrong_owner.json()["code"] == "SCAN_NOT_OWNED"

    # 3. User A uses their own scan_id -> 200 OK & scan_ingredients synced (TC-20)
    res_ok = client.post(
        "/api/v1/recommendations",
        headers={"Authorization": f"Bearer user:{user_a}"},
        json={"ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA], "scan_id": scan_uuid},
    )
    assert res_ok.status_code == 200
    saved_session = repo.get_scan_session(scan_uuid)
    assert saved_session is not None
    assert saved_session.ingredient_ids == [ING_CA_CHUA, ING_TRUNG_GA]


def test_perf02_recommendations_latency_under_1s_for_500_published_recipes() -> None:
    """PERF-02 / NFR-03: p95 latency <= 1.0s on >= 500 published recipes."""
    base_recipes = _default_seed_recipes()
    synthetic_recipes: list[RecipeRecord] = list(base_recipes)
    methods = ["stir_fry", "boil", "braise", "steam", "grill"]
    cuisines: list[CuisineCode] = ["VN", "EU", "US"]

    for i in range(520):
        synthetic_recipes.append(
            RecipeRecord(
                id=f"99999999-9999-4999-8999-{i:012d}",
                slug=f"mon-thu-nghiem-{i}",
                name_vi=f"Món thử nghiệm hiệu năng số {i}",
                cuisine_code=cuisines[i % len(cuisines)],
                prep_minutes=5 + (i % 15),
                cook_minutes=10 + (i % 25),
                status="published",
                cooking_method=methods[i % len(methods)],
                ingredients=[
                    RecipeIngredientRecord(
                        ingredient_id=ING_CA_CHUA if i % 2 == 0 else ING_TRUNG_GA,
                        name_vi="Cà chua" if i % 2 == 0 else "Trứng gà",
                        category="vegetable" if i % 2 == 0 else "protein",
                        is_required=True,
                        role="primary",
                        weight=4.0,
                        sort_order=1,
                    ),
                    RecipeIngredientRecord(
                        ingredient_id=ING_MUOI,
                        name_vi="Muối",
                        category="pantry",
                        is_required=True,
                        role="secondary",
                        weight=1.0,
                        sort_order=2,
                    ),
                ],
                steps=[
                    RecipeStepRecord(step_no=1, instruction="Bước 1", estimated_minutes=10)
                ],
            )
        )

    perf_repo = InMemoryCatalogRepository(
        ingredients=_default_seed_ingredients(),
        recipes=synthetic_recipes,
    )
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: perf_repo
    perf_client = TestClient(app)

    start = time.perf_counter()
    res = perf_client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "excluded_pantry_ids": [],
            "limit": 20,
        },
    )
    elapsed_sec = time.perf_counter() - start
    assert res.status_code == 200
    assert res.json()["total"] >= 500
    assert len(res.json()["items"]) == 20
    assert elapsed_sec < 1.0, f"Expected latency < 1.0s on 520 recipes, got {elapsed_sec:.3f}s"
