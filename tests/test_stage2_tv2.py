"""Stage 2 Automated Verification Suite for TV2 (Phong Phạm) — Unified MCDA (`ADR-013`).

Covers:
- Card 1 (`[GĐ2 - TP05, TP06, TP07, TP14]`):
  - Unified 4-Criteria MCDA (`C, G, T, P, S`) — all 7 canonical math cases from Table E.1 in `test-cases.md`
    (`S = 95.0`, `S = 100.0`, `S = 90.0`, `S = 75.0`, `S = 83.75`, `C = 0` BLOCKED, `allergic_ingredient_ids` BLOCKED)
  - TP 05 Weighted Ingredient Coverage `4-2-1-0` (`MATH-03`: `6/8 = 0.75`)
  - TP 06 Tversky Similarity Baseline B (`MATH-04`: `T_{0.3, 2.0} = 0.60`)
  - TP 07 & TP 14 Linear XAI Breakdown (`MATH-05`: `[50.00, 21.25, 7.50, 5.00] -> 83.75`)
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
    ING_DAU_AN,
    ING_DAU_HU,
    ING_DUONG,
    ING_HANH_LA,
    ING_INACTIVE,
    ING_MUOI,
    ING_NUOC_MAM,
    ING_THIT_BA_CHI,
    ING_TIEU_XAY,
    ING_TRUNG_GA,
    REC_CANH_CA_CHUA_TRUNG,
    REC_DAU_HU_SOT_CA,
    REC_THIT_KHO_TRUNG,
    REC_TRUNG_XAO_CA_CHUA,
)
from app.main import create_app
from app.schemas.reasoning import ReasoningInput
from app.schemas.recipes import CuisineCode, RecipeSummary
from app.schemas.recommendations import (
    RecommendationItem,
    ScoreBreakdown,
    ScoreContributions,
)
from app.services.coverage import (
    compute_tversky_similarity,
    compute_weighted_coverage,
)
from app.services.mmr import compute_mmr_score, rerank_with_mmr
from app.services.reasoning import evaluate_recipe_reasoning
from app.services.scoring import (
    compute_main_role_score_g,
    compute_unified_mcda_score,
    score_recipe_unified,
)


# ==============================================================================
# 1. Unified 4-Criteria MCDA (`ADR-013`) — Table E.1 (All 7 Canonical Cases)
# ==============================================================================


def test_unified_mcda_all_7_canonical_cases_table_e1(
    repo: InMemoryCatalogRepository,
) -> None:
    """Verify all 7 canonical cases in Table E.1 of `docs/06-testing/test-cases.md`."""
    pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    trung_xao = repo.get_published_recipe_by_id(REC_TRUNG_XAO_CA_CHUA)
    dau_hu = repo.get_published_recipe_by_id(REC_DAU_HU_SOT_CA)
    assert trung_xao is not None
    assert dau_hu is not None

    # Case 1: Enough Cà chua + Trứng gà (w=4+4), all kitchen spices (w=1+1), skip main=[], desired_hours=100.0, Guest F_u=[] -> S = 95.0
    ev1 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    item1 = score_recipe_unified(
        trung_xao,
        ev1,
        ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
        main_ingredient_ids=[],
        desired_hours=100.0,
        favorite_ingredient_ids=[],
    )
    assert item1.availability == "ready"
    assert item1.reasoning_status == "READY"
    assert item1.score == 95.0
    assert item1.score_breakdown == ScoreBreakdown(C=1.0, G=1.0, T=1.0, P=0.5)
    assert item1.score_contributions == ScoreContributions(C=50.0, G=25.0, T=15.0, P=5.0)
    # Adding optional garnish Hành lá (`w=0`) keeps C=1.0 and G ignores nothing or adjusts cleanly; verify optional is in missing_optional_ingredient_ids
    assert item1.missing_optional_ingredient_ids == [ING_HANH_LA]

    # Case 2: Same + full match on favorite_ingredient_ids=[Cà chua, Trứng gà] -> P=1.0, S = 100.0
    item2 = score_recipe_unified(
        trung_xao,
        ev1,
        ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
        favorite_ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
    )
    assert item2.score == 100.0
    assert item2.score_breakdown.P == 1.0
    assert item2.score_contributions.P == 10.0

    # Case 3: Exclude Nước mắm (`X=[ING_NUOC_MAM]`, w=1/10) -> C=0.9, S = 90.0, MISSING_CONFIRMED ("missing")
    ev3 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
            excluded_pantry_ids=[ING_NUOC_MAM],
        ),
        pantry_ids,
    )
    item3 = score_recipe_unified(
        trung_xao,
        ev3,
        ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
    )
    assert item3.availability == "missing"
    assert item3.reasoning_status == "MISSING_CONFIRMED"
    assert item3.score == 90.0
    assert item3.score_breakdown.C == 0.9
    assert item3.missing_required_ingredient_ids == [ING_NUOC_MAM]

    # Case 4: Only 1 scanned ingredient `U=[ING_CA_CHUA]` (`w=4` + spices `2` = `6/10`) -> C=0.6, S = 75.0, UNKNOWN ("missing")
    ev4 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_CA_CHUA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    item4 = score_recipe_unified(
        trung_xao,
        ev4,
        ingredient_ids=[ING_CA_CHUA],
    )
    assert item4.availability == "missing"
    assert item4.reasoning_status == "UNKNOWN"
    assert item4.score == 75.0
    assert item4.score_breakdown.C == 0.6
    assert item4.missing_required_ingredient_ids == [ING_TRUNG_GA]

    # Case 5: Đậu hũ sốt cà chua (30m = 0.50h), U=[Đậu hũ, Cà chua], main=[Đậu hũ], desired_hours=0.25, F_u=[Đậu hũ, Thịt ba chỉ]
    # -> C=1.0, G=0.85, T=0.5, P=0.5 -> [50.0, 21.25, 7.5, 5.0] -> S = 83.75
    ev5 = evaluate_recipe_reasoning(
        dau_hu,
        ReasoningInput(ingredient_ids=[ING_DAU_HU, ING_CA_CHUA], excluded_pantry_ids=[]),
        pantry_ids,
    )
    item5 = score_recipe_unified(
        dau_hu,
        ev5,
        ingredient_ids=[ING_DAU_HU, ING_CA_CHUA],
        main_ingredient_ids=[ING_DAU_HU],
        desired_hours=0.25,
        favorite_ingredient_ids=[ING_DAU_HU, ING_THIT_BA_CHI],
    )
    assert item5.availability == "ready"
    assert item5.score == 83.75
    assert item5.score_breakdown == ScoreBreakdown(C=1.0, G=0.85, T=0.5, P=0.5)
    assert item5.score_contributions == ScoreContributions(C=50.0, G=21.25, T=7.5, P=5.0)

    # Also verify Cách B G(r) sensitivity when skipping main vs choosing sub ingredient as main
    assert compute_main_role_score_g(dau_hu, [ING_DAU_HU, ING_CA_CHUA], []) == pytest.approx(0.75)
    assert compute_main_role_score_g(
        dau_hu, [ING_DAU_HU, ING_CA_CHUA], [ING_CA_CHUA]
    ) == pytest.approx(0.65)

    # Case 6: No matched non-pantry ingredient in U (only Thịt ba chỉ for Trứng xào cà chua) -> BLOCKED
    ev6 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(ingredient_ids=[ING_THIT_BA_CHI], excluded_pantry_ids=[]),
        pantry_ids,
    )
    assert ev6.status_v1_1 == "BLOCKED"
    assert "no_matched_main_ingredient" in ev6.blocked_reasons

    # Case 7: Recipe contains an ingredient in `allergic_ingredient_ids` -> BLOCKED before scoring
    ev7 = evaluate_recipe_reasoning(
        trung_xao,
        ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
            allergic_ingredient_ids=[ING_TRUNG_GA],
        ),
        pantry_ids,
    )
    assert ev7.status_v1_1 == "BLOCKED"
    assert "allergen_violation" in ev7.blocked_reasons


# ==============================================================================
# 2. TP 05 Weighted Coverage `4-2-1-0` (`MATH-03`) & TP 06 Tversky Baseline B (`MATH-04`)
# ==============================================================================


def test_tp05_weighted_coverage_math03() -> None:
    """MATH-03: weights={dau_hu:4, ca_chua:2, dau:1, muoi:1}, available={dau_hu, dau, muoi} -> C = 6/8 = 0.75."""
    weights = {"dau_hu": 4.0, "ca_chua": 2.0, "dau": 1.0, "muoi": 1.0}
    c_val = compute_weighted_coverage(weights, {"dau_hu", "dau", "muoi"})
    assert c_val == pytest.approx(0.75, abs=1e-9)

    # When muoi is excluded -> confirmed_available = {dau_hu, dau} -> C = 5/8 = 0.625
    c_val_no_salt = compute_weighted_coverage(weights, {"dau_hu", "dau"})
    assert c_val_no_salt == pytest.approx(0.625, abs=1e-9)


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
# 3. TP 07 & TP 14 Unified MCDA & Linear XAI Breakdown (`MATH-05`)
# ==============================================================================


def test_tp07_and_tp14_unified_mcda_and_xai_breakdown_math05() -> None:
    """MATH-05: C=1.0, G=0.85, T=0.5, P=0.5 -> [50.00, 21.25, 7.50, 5.00] -> S = 83.75."""
    score, breakdown, contribs = compute_unified_mcda_score(
        c_val=1.0,
        g_val=0.85,
        t_val=0.5,
        p_val=0.5,
    )
    assert breakdown == ScoreBreakdown(C=1.0, G=0.85, T=0.5, P=0.5)
    assert contribs.C == 50.00
    assert contribs.G == 21.25
    assert contribs.T == 7.50
    assert contribs.P == 5.00
    assert score == 83.75
    assert round(contribs.C + contribs.G + contribs.T + contribs.P, 2) == score


# ==============================================================================
# 4. TP 09 Maximal Marginal Relevance (MMR) Top-K Diversification (`MATH-06`)
# ==============================================================================


def test_tp09_mmr_diversification_math06() -> None:
    """MATH-06: lambda_mmr=0.7; Variant Soup (Rel=0.91, Sim=0.75 -> 0.412) vs Spaghetti (Rel=0.88, Sim=0.20 -> 0.556)."""
    mmr_soup_variant = compute_mmr_score(
        rel_score=0.91, max_similarity_to_selected=0.75, lambda_mmr=0.7
    )
    mmr_spaghetti = compute_mmr_score(
        rel_score=0.88, max_similarity_to_selected=0.20, lambda_mmr=0.7
    )
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
            reasoning_status="READY",
            score=score,
            matched_ingredient_ids=[ING_CA_CHUA],
            missing_required_ingredient_ids=[],
            missing_optional_ingredient_ids=[],
            score_breakdown=ScoreBreakdown(C=1.0, G=1.0, T=1.0, P=0.5),
            score_contributions=ScoreContributions(C=50.0, G=25.0, T=15.0, P=5.0),
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
    # TC-10 & TC-12: Have Cà chua & Trứng gà, default Guest payload -> Canh cà chua trứng (95.0, ready) & Trứng xào cà chua (95.0, ready)
    # appear strictly before Đậu hũ sốt cà chua (missing Đậu hũ) and Thịt kho trứng (missing Thịt ba chỉ)
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
    # CONFLICT-RESOLVED: Synced seed_fixtures with all 20 seed.sql recipes (added EU/US 2205..2208);
    # both READY tomato-egg recipes remain strictly ranked ahead of all missing recipes.
    assert data["total"] >= 4
    items = data["items"]
    availabilities = [it["availability"] for it in items]
    assert availabilities[:2] == ["ready", "ready"]
    assert all(av == "missing" for av in availabilities[2:])

    by_id = {it["recipe"]["id"]: it for it in items}
    assert by_id[REC_TRUNG_XAO_CA_CHUA]["score"] == 95.0
    assert by_id[REC_TRUNG_XAO_CA_CHUA]["availability"] == "ready"
    assert by_id[REC_TRUNG_XAO_CA_CHUA]["reasoning_status"] == "READY"
    assert by_id[REC_CANH_CA_CHUA_TRUNG]["score"] == 95.0
    assert by_id[REC_CANH_CA_CHUA_TRUNG]["availability"] == "ready"

    # TC-32: Exclude Nước mắm (`X=[ING_NUOC_MAM]`) -> Trứng xào cà chua drops to 90.0 and "missing" (`MISSING_CONFIRMED`)
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
    assert tx["score"] == 90.0
    assert tx["availability"] == "missing"
    assert tx["reasoning_status"] == "MISSING_CONFIRMED"
    assert tx["missing_required_ingredient_ids"] == [ING_NUOC_MAM]

    # Explicit `kitchen_spice_ids` (only Dầu ăn & Muối, no Nước mắm) also marks Nước mắm as confirmed missing
    res_kitchen = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "kitchen_spice_ids": [ING_DAU_AN, ING_MUOI],
        },
    )
    assert res_kitchen.status_code == 200
    by_id_kitchen = {it["recipe"]["id"]: it for it in res_kitchen.json()["items"]}
    assert by_id_kitchen[REC_TRUNG_XAO_CA_CHUA]["score"] == 90.0
    assert by_id_kitchen[REC_TRUNG_XAO_CA_CHUA]["reasoning_status"] == "MISSING_CONFIRMED"
    assert by_id_kitchen[REC_CANH_CA_CHUA_TRUNG]["availability"] == "ready"

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

    # TC-13: Hard filter `cuisine_codes=["US"]` strictly excludes VN/EU recipes
    # CONFLICT-RESOLVED: Synced US Burger (2207, contains tomato) into seed_fixtures; verify only US
    # recipes can pass `cuisine_codes=["US"]` and tofu-only US query returns `total == 0`.
    res_cuisine_hard = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "cuisine_codes": ["US"],
        },
    )
    assert res_cuisine_hard.status_code == 200
    us_items = res_cuisine_hard.json()["items"]
    assert all(it["recipe"]["cuisine_code"] == "US" for it in us_items)

    res_cuisine_empty = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_DAU_HU],
            "cuisine_codes": ["US"],
        },
    )
    assert res_cuisine_empty.status_code == 200
    assert res_cuisine_empty.json()["total"] == 0

    # TC-35: Personalization fields (`main_ingredient_ids`, `desired_hours`, `favorite_ingredient_ids`) -> S = 83.75
    res_pers = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_DAU_HU, ING_CA_CHUA],
            "main_ingredient_ids": [ING_DAU_HU],
            "desired_hours": 0.25,
            "favorite_ingredient_ids": [ING_DAU_HU, ING_THIT_BA_CHI],
            "allergic_ingredient_ids": [ING_TRUNG_GA],
        },
    )
    assert res_pers.status_code == 200
    pers_items = res_pers.json()["items"]
    # Egg recipes are hard-blocked by allergic_ingredient_ids=[ING_TRUNG_GA]; Đậu hũ sốt cà chua ranks #1 (READY, S=83.75)
    assert len(pers_items) >= 1
    pers_ids = {it["recipe"]["id"] for it in pers_items}
    assert REC_CANH_CA_CHUA_TRUNG not in pers_ids
    assert REC_THIT_KHO_TRUNG not in pers_ids
    assert REC_TRUNG_XAO_CA_CHUA not in pers_ids
    assert pers_items[0]["recipe"]["id"] == REC_DAU_HU_SOT_CA
    assert pers_items[0]["score"] == 83.75
    assert pers_items[0]["score_contributions"] == {
        "C": 50.0,
        "G": 21.25,
        "T": 7.5,
        "P": 5.0,
    }

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

    # TC-37(4): `main_ingredient_ids` not a subset of `ingredient_ids` -> 422 INVALID_INGREDIENTS (`main_not_in_ingredient_ids`)
    res_invalid_4 = client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_CA_CHUA],
            "main_ingredient_ids": [ING_TRUNG_GA],
        },
    )
    assert res_invalid_4.status_code == 422
    assert res_invalid_4.json()["details"]["reason"] == "main_not_in_ingredient_ids"


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
                        role="core",
                        dish_role="main",
                        weight=4.0,
                        sort_order=1,
                    ),
                    RecipeIngredientRecord(
                        ingredient_id=ING_MUOI,
                        name_vi="Muối",
                        category="pantry",
                        is_required=True,
                        role="spice",
                        dish_role="sub",
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


# ==============================================================================
# 7. User Preferences API, Saved Profile Fallback, `diversify` Flag & OpenAPI Sync
# ==============================================================================


def test_preferences_crud_and_pantry_only_validation(client: TestClient) -> None:
    user_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    user_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    # 1. Unauthenticated access -> 401 UNAUTHORIZED
    assert client.get("/api/v1/preferences").status_code == 401
    assert (
        client.put(
            "/api/v1/preferences",
            json={
                "allergic_ingredient_ids": [],
                "kitchen_spice_ids": [],
                "favorite_ingredient_ids": [],
            },
        ).status_code
        == 401
    )

    # 2. Fresh user GET -> defaults to all 5 active pantry seasonings, empty allergies & favorites
    res_get_default = client.get(
        "/api/v1/preferences",
        headers={"Authorization": f"Bearer user:{user_a}"},
    )
    assert res_get_default.status_code == 200
    body_default = res_get_default.json()
    assert body_default["user_id"] == user_a
    assert body_default["allergic_ingredient_ids"] == []
    assert body_default["favorite_ingredient_ids"] == []
    assert set(body_default["kitchen_spice_ids"]) == {
        ING_MUOI,
        ING_NUOC_MAM,
        ING_DAU_AN,
        ING_DUONG,
        ING_TIEU_XAY,
    }
    assert body_default["updated_at"] is None

    # 3. Passing category='spice' (Hành lá) or category='vegetable' (Cà chua) into kitchen_spice_ids -> 422
    res_non_pantry = client.put(
        "/api/v1/preferences",
        headers={"Authorization": f"Bearer user:{user_a}"},
        json={
            "allergic_ingredient_ids": [],
            "kitchen_spice_ids": [ING_MUOI, ING_HANH_LA],
            "favorite_ingredient_ids": [],
        },
    )
    assert res_non_pantry.status_code == 422
    assert res_non_pantry.json()["code"] == "INVALID_INGREDIENTS"
    assert res_non_pantry.json()["details"]["reason"] == "non_pantry_in_kitchen_spices"
    assert res_non_pantry.json()["details"]["invalid_ids"] == [ING_HANH_LA]

    # 4. Valid PUT persists User A profile without leaking to User B
    res_put_ok = client.put(
        "/api/v1/preferences",
        headers={"Authorization": f"Bearer user:{user_a}"},
        json={
            "allergic_ingredient_ids": [ING_DAU_HU],
            "kitchen_spice_ids": [ING_MUOI, ING_DAU_AN, ING_DUONG, ING_TIEU_XAY],
            "favorite_ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
        },
    )
    assert res_put_ok.status_code == 200
    saved_a = res_put_ok.json()
    assert saved_a["allergic_ingredient_ids"] == [ING_DAU_HU]
    assert saved_a["kitchen_spice_ids"] == [ING_MUOI, ING_DAU_AN, ING_DUONG, ING_TIEU_XAY]
    assert saved_a["favorite_ingredient_ids"] == [ING_CA_CHUA, ING_TRUNG_GA]
    assert saved_a["updated_at"] is not None

    res_user_b = client.get(
        "/api/v1/preferences",
        headers={"Authorization": f"Bearer user:{user_b}"},
    )
    assert res_user_b.status_code == 200
    assert res_user_b.json()["allergic_ingredient_ids"] == []
    assert len(res_user_b.json()["kitchen_spice_ids"]) == 5


def test_recommendations_autoload_saved_preferences_and_explicit_override(
    client: TestClient,
) -> None:
    user_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    headers = {"Authorization": f"Bearer user:{user_a}"}

    # Save User A profile: allergic to Đậu hũ, missing Nước mắm from kitchen, loves Cà chua + Trứng gà
    put_res = client.put(
        "/api/v1/preferences",
        headers=headers,
        json={
            "allergic_ingredient_ids": [ING_DAU_HU],
            "kitchen_spice_ids": [ING_MUOI, ING_DAU_AN, ING_DUONG, ING_TIEU_XAY],
            "favorite_ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
        },
    )
    assert put_res.status_code == 200

    # 1. Authenticated POST omitting personalization fields -> auto-loads saved profile:
    #    - Đậu hũ sốt cà chua is BLOCKED by saved allergic_ingredient_ids=[ING_DAU_HU]
    #    - Trứng xào cà chua gets P=1.0 (+10.0), C=0.9 (45.0, missing Nước mắm), G=2/3 (16.67 over 3 input ingredients) -> S=86.67!
    res_auto = client.post(
        "/api/v1/recommendations",
        headers=headers,
        json={"ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA, ING_DAU_HU]},
    )
    assert res_auto.status_code == 200
    auto_items = res_auto.json()["items"]
    returned_ids = [it["recipe"]["id"] for it in auto_items]
    assert REC_DAU_HU_SOT_CA not in returned_ids
    trung_xao = next(it for it in auto_items if it["recipe"]["id"] == REC_TRUNG_XAO_CA_CHUA)
    assert trung_xao["reasoning_status"] == "MISSING_CONFIRMED"
    assert trung_xao["missing_required_ingredient_ids"] == [ING_NUOC_MAM]
    assert trung_xao["score_breakdown"]["P"] == 1.0
    assert trung_xao["score"] == 86.67  # 45.0 (C=0.9) + 16.67 (G=2/3) + 15.0 (T=1.0) + 10.0 (P=1.0)

    # 2. Explicit override in request (`allergic_ingredient_ids=[]`, `favorite_ingredient_ids=[]`) overrides saved profile
    res_override = client.post(
        "/api/v1/recommendations",
        headers=headers,
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA],
            "allergic_ingredient_ids": [],
            "favorite_ingredient_ids": [],
            "kitchen_spice_ids": [
                ING_MUOI,
                ING_NUOC_MAM,
                ING_DAU_AN,
                ING_DUONG,
                ING_TIEU_XAY,
            ],
        },
    )
    assert res_override.status_code == 200
    override_items = res_override.json()["items"]
    trung_xao_ov = next(it for it in override_items if it["recipe"]["id"] == REC_TRUNG_XAO_CA_CHUA)
    assert trung_xao_ov["reasoning_status"] == "READY"
    assert trung_xao_ov["score_breakdown"]["P"] == 0.5
    assert trung_xao_ov["score"] == 95.0  # 50.0 (C=1.0) + 25.0 (G=1.0) + 15.0 (T=1.0) + 5.0 (P=0.5)

    # Also verify Đậu hũ sốt cà chua is no longer blocked when allergic_ingredient_ids=[] is explicitly sent
    res_unblock_dau_hu = client.post(
        "/api/v1/recommendations",
        headers=headers,
        json={
            "ingredient_ids": [ING_CA_CHUA, ING_DAU_HU],
            "allergic_ingredient_ids": [],
        },
    )
    assert res_unblock_dau_hu.status_code == 200
    assert REC_DAU_HU_SOT_CA in [it["recipe"]["id"] for it in res_unblock_dau_hu.json()["items"]]


def test_recommendations_diversify_false_vs_true() -> None:
    """Verify default `diversify=False` preserves pure S order while `diversify=True` applies MMR."""
    rec_1 = RecipeRecord(
        id="88888888-8888-4888-8888-888888888801",
        slug="trung-chien-1",
        name_vi="Trứng chiên kiểu 1",
        cuisine_code="VN",
        prep_minutes=5,
        cook_minutes=10,
        status="published",
        cooking_method="fry",
        ingredients=[
            RecipeIngredientRecord(
                ingredient_id=ING_TRUNG_GA,
                name_vi="Trứng gà",
                category="protein",
                is_required=True,
                role="core",
                dish_role="main",
                weight=4.0,
                sort_order=1,
            ),
            RecipeIngredientRecord(
                ingredient_id=ING_CA_CHUA,
                name_vi="Cà chua",
                category="vegetable",
                is_required=True,
                role="core",
                dish_role="main",
                weight=4.0,
                sort_order=2,
            ),
            RecipeIngredientRecord(
                ingredient_id=ING_MUOI,
                name_vi="Muối",
                category="pantry",
                is_required=True,
                role="spice",
                dish_role="sub",
                weight=1.0,
                sort_order=3,
            ),
        ],
    )
    # Near-duplicate of rec_1 (same ingredients & same cooking_method="fry"), slightly slower so S is slightly lower when desired_hours=0.25
    rec_2_clone = RecipeRecord(
        id="88888888-8888-4888-8888-888888888802",
        slug="trung-chien-2",
        name_vi="Trứng chiên kiểu 2",
        cuisine_code="VN",
        prep_minutes=6,
        cook_minutes=10,  # 16 mins -> T = 15/16 = 0.9375 -> S = 94.06
        status="published",
        cooking_method="fry",
        ingredients=list(rec_1.ingredients),
    )
    # Diverse dish (different ingredients & cooking_method="boil"), slightly slower (18 mins -> T = 15/18 = 0.8333 -> S = 92.5)
    rec_3_diverse = RecipeRecord(
        id="88888888-8888-4888-8888-888888888803",
        slug="canh-dau-hu-luoc",
        name_vi="Đậu hũ luộc thanh đạm",
        cuisine_code="VN",
        prep_minutes=8,
        cook_minutes=10,  # 18 mins -> S = 92.5
        status="published",
        cooking_method="boil",
        ingredients=[
            RecipeIngredientRecord(
                ingredient_id=ING_DAU_HU,
                name_vi="Đậu hũ",
                category="protein",
                is_required=True,
                role="core",
                dish_role="main",
                weight=4.0,
                sort_order=1,
            ),
            RecipeIngredientRecord(
                ingredient_id=ING_DUONG,
                name_vi="Đường",
                category="pantry",
                is_required=True,
                role="spice",
                dish_role="sub",
                weight=1.0,
                sort_order=2,
            ),
        ],
    )

    custom_repo = InMemoryCatalogRepository(
        ingredients=_default_seed_ingredients(),
        recipes=[rec_1, rec_2_clone, rec_3_diverse],
    )
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: custom_repo
    custom_client = TestClient(app)

    # 1. Default (`diversify` omitted -> False): pure descending S -> [rec_1 (95.0), rec_2_clone (94.06), rec_3_diverse (92.5)]
    res_pure = custom_client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_TRUNG_GA, ING_CA_CHUA, ING_DAU_HU],
            "desired_hours": 0.25,
        },
    )
    assert res_pure.status_code == 200
    pure_ids = [it["recipe"]["id"] for it in res_pure.json()["items"]]
    assert pure_ids == [rec_1.id, rec_2_clone.id, rec_3_diverse.id]

    # 2. `diversify=True`: MMR penalizes near-duplicate `rec_2_clone` and promotes `rec_3_diverse` to rank #2!
    res_mmr = custom_client.post(
        "/api/v1/recommendations",
        json={
            "ingredient_ids": [ING_TRUNG_GA, ING_CA_CHUA, ING_DAU_HU],
            "desired_hours": 0.25,
            "diversify": True,
        },
    )
    assert res_mmr.status_code == 200
    mmr_ids = [it["recipe"]["id"] for it in res_mmr.json()["items"]]
    assert mmr_ids == [rec_1.id, rec_3_diverse.id, rec_2_clone.id]


def test_openapi_yaml_and_postman_contract_v1_1_0_sync() -> None:
    """Verify docs/03-api/openapi.yaml & postman collection stay synchronized with v1.1.0."""
    import json
    from pathlib import Path
    import yaml

    repo_root = Path(__file__).resolve().parents[1]
    openapi_doc = yaml.safe_load(
        (repo_root / "docs" / "03-api" / "openapi.yaml").read_text(encoding="utf-8")
    )
    postman_doc = json.loads(
        (repo_root / "docs" / "03-api" / "foodvision-ai.postman_collection.json").read_text(
            encoding="utf-8"
        )
    )

    assert openapi_doc["info"]["version"] == "1.1.0"
    paths = openapi_doc["paths"]
    assert len(paths) == 26
    http_methods = {"get", "post", "put", "patch", "delete"}
    op_count = sum(
        1 for methods in paths.values() for m in methods.keys() if m.lower() in http_methods
    )
    assert op_count == 35
    assert "/preferences" in paths
    assert {"get", "put"} <= set(paths["/preferences"].keys())

    rec_req_props = openapi_doc["components"]["schemas"]["RecommendRequest"]["properties"]
    assert rec_req_props["diversify"]["default"] is False

    ing_in_props = openapi_doc["components"]["schemas"]["RecipeIngredientInput"]["properties"]
    assert set(ing_in_props["role"]["enum"]) == {"core", "secondary", "spice", "optional"}
    assert set(ing_in_props["dish_role"]["enum"]) == {"main", "sub"}
    assert "weight" in ing_in_props
    assert "grams" in ing_in_props

    assert len(postman_doc["item"]) == 35

