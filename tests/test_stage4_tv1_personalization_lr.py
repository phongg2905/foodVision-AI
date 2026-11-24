"""Stage 4 TV1 (Minh Thanh) — Component 08 Logistic Regression Personalization Tests (`Card #23`).

Verifies all 4 checklist items of Trello Card #23 (`https://trello.com/c/3c7S4AUn`):
1. 18-dim deterministic feature vector `x_{u,r}` (`lr-feature-v1.0`) & sigmoid inference `P(like | u, r)`.
2. Online L2-regularized SGD updates, signal hygiene (`rating >= 4` -> 1, `rating <= 2` -> 0, `rating == 3` ignored),
   `ADR-012` latest `updated_at` deduplication, and strict per-UUID ownership isolation.
3. Cold-start blending `S_final(u, r) = (1 - lambda_pers(N_u)) * S(r) + 100 * lambda_pers(N_u) * P(like | u, r)`
   wired into `compute_unified_mcda_score` and `score_recipe_unified` in `app.services.scoring`.
4. Exact verification of `MATH-05` and end-to-end defense scenario `DEF-08` via `scoring.py` and `POST /api/v1/recommendations`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from uuid import UUID

from fastapi.testclient import TestClient
import pytest

from app.core.database import (
    InMemoryCatalogRepository,
    RecipeIngredientRecord,
    RecipeRecord,
    RecipeStepRecord,
    get_catalog_repo,
)
from app.core.seed_fixtures import (
    ING_CA_CHUA as ING_TOMATO,
    ING_DAU_AN as ING_OIL,
    ING_MUOI as ING_SALT,
    ING_NUOC_MAM as ING_FISH_SAUCE,
    ING_TRUNG_GA as ING_EGG,
    build_default_seed_ingredients,
)
from app.intelligence.personalization import (
    FEATURE_DIM_V1,
    FEATURE_NAMES_V1,
    InMemoryPersonalizationRepository,
    PersonalizationConfig,
    PersonalizationEngine,
    PersonalizationFeedback,
    RecipeFeatureInput,
    UnauthorizedPersonalizationError,
    compute_cold_start_lambda,
    deduplicate_latest_feedback,
    extract_recipe_feature_vector,
    predict_preference_prob,
    update_lr_weights_sgd,
)
from app.main import app
from app.schemas.reasoning import ReasoningInput
from app.services.reasoning import evaluate_recipe_reasoning
from app.services.scoring import (
    blend_personalized_score,
    compute_unified_mcda_score,
    rank_recommendations,
    score_recipe_unified,
)

USER_A_UUID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
USER_B_UUID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
USER_NEW_UUID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")

RECIPE_XAO_ID = "91111111-1111-4111-8111-111111111111"
RECIPE_CANH_ID = "92222222-2222-4222-8222-222222222222"


# THUẬT TOÁN: Kiểm chứng Công thức Toán học Chuẩn `MATH-05` (MCDA C,G,T,P + XAI + Logistic Regression + Cold-Start)
def test_math_05_mcda_xai_logistic_regression_and_blending() -> None:
    """Verify exact numerical targets in `docs/06-testing/test-cases.md` (`MATH-05`)."""
    # 1. Unified 4-criteria MCDA & linear XAI breakdown: C=1.0, G=0.85, T=0.5, P=0.5 -> S = 83.75
    s_base, breakdown, contribs = compute_unified_mcda_score(
        c_val=1.0,
        g_val=0.85,
        t_val=0.5,
        p_val=0.5,
    )
    assert [contribs.C, contribs.G, contribs.T, contribs.P] == [50.00, 21.25, 7.50, 5.00]
    assert s_base == 83.75
    assert breakdown.C == 1.0 and breakdown.G == 0.85

    # 2. Logistic Regression forward pass: x=[1,1,0], theta=[0.2,0.3,-0.1] -> z=0.5, p=sigma(0.5)~=0.622
    x_vec = [1.0, 1.0, 0.0]
    theta_init = [0.2, 0.3, -0.1]
    prob = predict_preference_prob(theta_init, x_vec)
    expected_prob = 1.0 / (1.0 + math.exp(-0.5))
    assert math.isclose(prob, expected_prob, abs_tol=1e-9)
    assert round(prob, 3) == 0.622

    # 3. Online SGD step with y=1, eta=0.1, l2_reg=0.0 -> theta_new = theta + 0.1 * (1 - p) * x
    theta_updated = update_lr_weights_sgd(
        theta_init,
        x_vec,
        label=1,
        learning_rate=0.1,
        l2_reg=0.0,
    )
    delta = 0.1 * (1.0 - expected_prob)
    assert math.isclose(theta_updated[0], 0.2 + delta, abs_tol=1e-6)
    assert math.isclose(theta_updated[1], 0.3 + delta, abs_tol=1e-6)
    assert math.isclose(theta_updated[2], -0.1, abs_tol=1e-6)
    assert predict_preference_prob(theta_updated, x_vec) > prob

    # 4. Cold-start blending invariant: when lambda_pers = 0, S_final == S(r) == 83.75
    assert blend_personalized_score(s_base, prob, lambda_pers=0.0) == 83.75
    s_cold, _, _ = compute_unified_mcda_score(
        c_val=1.0,
        g_val=0.85,
        t_val=0.5,
        p_val=0.5,
        preference_prob=prob,
        feedback_count=2,
    )
    assert s_cold == 83.75

    # 5. Mature blending: S_final = round((1 - 0.25)*83.75 + 100*0.25*sigma(0.5), 2) = 78.37
    s_blended, _, contribs_after = compute_unified_mcda_score(
        c_val=1.0,
        g_val=0.85,
        t_val=0.5,
        p_val=0.5,
        preference_prob=prob,
        lambda_pers=0.25,
    )
    assert s_blended == 78.37
    # Linear XAI contributions remain strictly anchored to the 4 transparent MCDA criteria
    assert [contribs_after.C, contribs_after.G, contribs_after.T, contribs_after.P] == [
        50.00,
        21.25,
        7.50,
        5.00,
    ]


# THUẬT TOÁN: Kiểm chứng Vector Đặc trưng 18 Chiều, Lọc Tín hiệu Nhiễu & Khử Trùng lặp `ADR-012`
def test_feature_vector_signal_hygiene_and_adr012_deduplication() -> None:
    """Verify 18-dim feature encoding, rating/favorite label mapping, ADR-012 dedup, and UUID isolation."""
    vec_xao = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="Xào",
            total_minutes=15,
            difficulty="Dễ",
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
        )
    )
    assert vec_xao.dimension == FEATURE_DIM_V1 == 18
    feat_map = vec_xao.to_dict()
    assert list(feat_map.keys()) == list(FEATURE_NAMES_V1)
    assert feat_map["bias"] == 1.0
    assert feat_map["cuisine_vn"] == 1.0
    assert feat_map["method_xao"] == 1.0
    assert feat_map["difficulty_norm"] == 0.20

    repo = InMemoryPersonalizationRepository()
    cfg = PersonalizationConfig(min_feedback_for_blend=5, full_maturity_feedback=15, max_blend_lambda=0.25)
    engine = PersonalizationEngine(repository=repo, config=cfg)
    recipe_uuid = UUID(RECIPE_XAO_ID)
    t0 = datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)

    # Neutral rating=3 and implicit click must be skipped safely without incrementing feedback_count
    res_neutral = engine.update_from_feedback(
        USER_A_UUID,
        vec_xao,
        PersonalizationFeedback(
            user_id=USER_A_UUID,
            recipe_id=recipe_uuid,
            signal_type="explicit_rating",
            rating=3,
            updated_at=t0,
        ),
    )
    assert res_neutral.model_state_update is not None
    assert res_neutral.model_state_update.applied is False
    assert repo.get_user_model_state(USER_A_UUID) is None

    res_click = engine.update_from_feedback(
        USER_A_UUID,
        vec_xao,
        PersonalizationFeedback(
            user_id=USER_A_UUID,
            recipe_id=recipe_uuid,
            signal_type="click",
            updated_at=t0,
        ),
    )
    assert res_click.model_state_update is not None
    assert res_click.model_state_update.applied is False

    # Positive favorite_added applies SGD update; older timestamp replay is skipped per ADR-012
    res_fav = engine.update_from_feedback(
        USER_A_UUID,
        vec_xao,
        PersonalizationFeedback(
            user_id=USER_A_UUID,
            recipe_id=recipe_uuid,
            signal_type="favorite_added",
            updated_at=t0 + timedelta(minutes=10),
        ),
    )
    assert res_fav.model_state_update is not None
    assert res_fav.model_state_update.applied is True
    assert res_fav.model_state_update.new_feedback_count == 1

    res_stale = engine.update_from_feedback(
        USER_A_UUID,
        vec_xao,
        PersonalizationFeedback(
            user_id=USER_A_UUID,
            recipe_id=recipe_uuid,
            signal_type="explicit_rating",
            rating=1,
            updated_at=t0 + timedelta(minutes=2),
        ),
    )
    assert res_stale.model_state_update is not None
    assert res_stale.model_state_update.applied is False
    assert res_stale.model_state_update.reason == "stale_feedback_timestamp_adr012"

    # Batch deduplication keeps only latest updated_at per (user_id, recipe_id)
    deduped = deduplicate_latest_feedback(
        [
            PersonalizationFeedback(USER_A_UUID, recipe_uuid, rating=2, updated_at=t0),
            PersonalizationFeedback(
                USER_A_UUID, recipe_uuid, rating=5, updated_at=t0 + timedelta(hours=1)
            ),
        ],
        authenticated_user_id=USER_A_UUID,
    )
    assert len(deduped) == 1
    assert deduped[0].rating == 5

    # Cross-user contamination must raise UnauthorizedPersonalizationError
    with pytest.raises(UnauthorizedPersonalizationError):
        engine.update_from_feedback(
            USER_A_UUID,
            vec_xao,
            PersonalizationFeedback(user_id=USER_B_UUID, recipe_id=recipe_uuid, rating=5),
        )

    assert compute_cold_start_lambda(2, config=cfg) == 0.0
    assert compute_cold_start_lambda(10, config=cfg) == 0.125
    assert compute_cold_start_lambda(20, config=cfg) == 0.25


def _build_pair_recipes() -> list[RecipeRecord]:
    """Build two symmetric READY recipes differing only in cooking_method ('xao' vs 'canh')."""
    common_ings = [
        RecipeIngredientRecord(ING_TOMATO, "Cà chua", "vegetable", True, "core", "main", 4.0),
        RecipeIngredientRecord(ING_EGG, "Trứng gà", "egg", True, "core", "main", 4.0),
        RecipeIngredientRecord(ING_OIL, "Dầu ăn", "pantry", True, "spice", "sub", 1.0),
        RecipeIngredientRecord(ING_SALT, "Muối", "pantry", True, "spice", "sub", 1.0),
    ]
    steps = [RecipeStepRecord(1, "Sơ chế và chế biến nguyên liệu.", 10)]
    return [
        RecipeRecord(
            id=RECIPE_XAO_ID,
            slug="trung-xao-ca-chua-pers",
            name_vi="Trứng xào cà chua",
            cuisine_code="VN",
            cooking_method="xao",
            prep_minutes=5,
            cook_minutes=10,
            status="published",
            ingredients=list(common_ings),
            steps=list(steps),
        ),
        RecipeRecord(
            id=RECIPE_CANH_ID,
            slug="canh-trung-ca-chua-pers",
            name_vi="Canh trứng cà chua",
            cuisine_code="VN",
            cooking_method="canh",
            prep_minutes=5,
            cook_minutes=10,
            status="published",
            ingredients=list(common_ings),
            steps=list(steps),
        ),
    ]


# THUẬT TOÁN: Kiểm chứng Kịch bản Bảo vệ Học phần `DEF-08` (2 User Lịch sử Đối lập vs Guest Cold-Start & Bất biến Dị ứng)
def test_def_08_two_users_divergent_top_k_and_cold_start_stability() -> None:
    """Verify `DEF-08` end-to-end across `scoring.py` and `POST /api/v1/recommendations`."""
    recipes = _build_pair_recipes()
    pers_repo = InMemoryPersonalizationRepository()
    pers_cfg = PersonalizationConfig(
        learning_rate=0.25,
        min_feedback_for_blend=5,
        full_maturity_feedback=10,
        max_blend_lambda=0.25,
    )
    engine = PersonalizationEngine(repository=pers_repo, config=pers_cfg)

    vec_xao = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="xao",
            total_minutes=15,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
            required_ingredient_count=4,
            step_count=1,
        ),
        config=pers_cfg,
    )
    vec_canh = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="canh",
            total_minutes=15,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
            required_ingredient_count=4,
            step_count=1,
        ),
        config=pers_cfg,
    )

    # Train User A (loves stir-fry 'xao' via favorites & 5-star ratings, dislikes soup 'canh' via 1-star ratings)
    # Train User B (loves soup 'canh' via favorites & 5-star ratings, dislikes stir-fry 'xao' via 1-star ratings)
    base_ts = datetime(2026, 11, 15, 8, 0, tzinfo=timezone.utc)
    for idx in range(5):
        r_xao_hist = UUID(f"10000000-0000-4000-8000-00000000000{idx}")
        r_canh_hist = UUID(f"20000000-0000-4000-8000-00000000000{idx}")
        ts = base_ts + timedelta(minutes=idx)

        engine.update_from_feedback(
            USER_A_UUID,
            vec_xao,
            PersonalizationFeedback(USER_A_UUID, r_xao_hist, signal_type="favorite_added", updated_at=ts),
        )
        engine.update_from_feedback(
            USER_A_UUID,
            vec_canh,
            PersonalizationFeedback(USER_A_UUID, r_canh_hist, rating=1, updated_at=ts),
        )

        engine.update_from_feedback(
            USER_B_UUID,
            vec_canh,
            PersonalizationFeedback(USER_B_UUID, r_canh_hist, rating=5, updated_at=ts),
        )
        engine.update_from_feedback(
            USER_B_UUID,
            vec_xao,
            PersonalizationFeedback(USER_B_UUID, r_xao_hist, rating=1, updated_at=ts),
        )

    # 1. Verify direct `score_recipe_unified` + `rank_recommendations` in `scoring.py`
    r_in = ReasoningInput(ingredient_ids=[ING_TOMATO, ING_EGG])
    pantry_ids = {ING_OIL, ING_SALT, ING_FISH_SAUCE}
    ev_map = {r.id: evaluate_recipe_reasoning(r, r_in, pantry_ids) for r in recipes}

    guest_items = rank_recommendations(
        [
            score_recipe_unified(
                r,
                ev_map[r.id],
                [ING_TOMATO, ING_EGG],
                user_id=None,
                personalization_engine=engine,
            )
            for r in recipes
        ]
    )
    assert [it.score for it in guest_items] == [95.0, 95.0]

    # 2. Verify end-to-end FastAPI endpoint `POST /api/v1/recommendations`
    catalog_repo = InMemoryCatalogRepository(
        ingredients=build_default_seed_ingredients(),
        recipes=recipes,
    )
    catalog_repo.set_personalization_engine(engine)
    app.dependency_overrides[get_catalog_repo] = lambda: catalog_repo
    try:
        client = TestClient(app)
        payload = {"ingredient_ids": [ING_TOMATO, ING_EGG]}

        resp_a = client.post(
            "/api/v1/recommendations",
            json=payload,
            headers={"Authorization": f"Bearer user:{USER_A_UUID}"},
        )
        resp_b = client.post(
            "/api/v1/recommendations",
            json=payload,
            headers={"Authorization": f"Bearer user:{USER_B_UUID}"},
        )
        resp_new = client.post(
            "/api/v1/recommendations",
            json=payload,
            headers={"Authorization": f"Bearer user:{USER_NEW_UUID}"},
        )

        assert resp_a.status_code == 200 and resp_b.status_code == 200 and resp_new.status_code == 200
        items_a = resp_a.json()["items"]
        items_b = resp_b.json()["items"]
        items_new = resp_new.json()["items"]

        # User A ranks 'xao' #1; User B ranks 'canh' #1; New User C keeps exact S_base = 95.0
        assert items_a[0]["recipe"]["id"] == RECIPE_XAO_ID
        assert items_a[0]["score"] > items_a[1]["score"]

        assert items_b[0]["recipe"]["id"] == RECIPE_CANH_ID
        assert items_b[0]["score"] > items_b[1]["score"]

        assert [it["score"] for it in items_new] == [95.0, 95.0]

        # Safety invariant: Allergic recipes stay strictly BLOCKED even for User A with high theta_u
        resp_allergy = client.post(
            "/api/v1/recommendations",
            json={
                "ingredient_ids": [ING_TOMATO, ING_EGG],
                "allergic_ingredient_ids": [ING_EGG],
            },
            headers={"Authorization": f"Bearer user:{USER_A_UUID}"},
        )
        assert resp_allergy.status_code == 200
        assert resp_allergy.json()["items"] == []
    finally:
        app.dependency_overrides.pop(get_catalog_repo, None)


# THUẬT TOÁN: Kiểm chứng hiệu năng suy luận cá nhân hóa trên 500 công thức xuất bản (PERF-02 < 1.0s)
def test_perf02_personalized_ranking_500_recipes_under_half_second() -> None:
    import time

    base_pair = _build_pair_recipes()
    recipes_500: list[RecipeRecord] = []
    for idx in range(500):
        proto = base_pair[idx % 2]
        recipes_500.append(
            RecipeRecord(
                id=f"99999999-1111-4111-8111-{idx:012d}",
                slug=f"pers-bench-{idx}",
                name_vi=f"{proto.name_vi} {idx}",
                cuisine_code="VN" if idx % 3 == 0 else ("EU" if idx % 3 == 1 else "US"),
                cooking_method=proto.cooking_method,
                prep_minutes=5,
                cook_minutes=10 + (idx % 20),
                status="published",
                ingredients=list(proto.ingredients),
                steps=list(proto.steps),
            )
        )

    pers_repo = InMemoryPersonalizationRepository()
    pers_cfg = PersonalizationConfig(min_feedback_for_blend=5, full_maturity_feedback=10, max_blend_lambda=0.25)
    engine = PersonalizationEngine(repository=pers_repo, config=pers_cfg)
    vec_vn_xao = extract_recipe_feature_vector(
        RecipeFeatureInput(cuisine_code="VN", cooking_method="xao", total_minutes=15, ingredient_coverage=1.0),
        config=pers_cfg,
    )
    ts0 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
    for idx in range(10):
        engine.update_from_feedback(
            USER_A_UUID,
            vec_vn_xao,
            PersonalizationFeedback(
                USER_A_UUID,
                UUID(f"30000000-0000-4000-8000-{idx:012d}"),
                rating=5,
                updated_at=ts0 + timedelta(minutes=idx),
            ),
        )

    catalog_repo = InMemoryCatalogRepository(
        ingredients=build_default_seed_ingredients(),
        recipes=recipes_500,
    )
    catalog_repo.set_personalization_engine(engine)
    app.dependency_overrides[get_catalog_repo] = lambda: catalog_repo
    try:
        client = TestClient(app)
        t_start = time.perf_counter()
        resp = client.post(
            "/api/v1/recommendations",
            json={"ingredient_ids": [ING_TOMATO, ING_EGG], "limit": 20},
            headers={"Authorization": f"Bearer user:{USER_A_UUID}"},
        )
        elapsed = time.perf_counter() - t_start
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 500
        assert data["items"][0]["recipe"]["cuisine_code"] == "VN"
        assert elapsed < 0.50, f"Personalized 500-recipe ranking took {elapsed:.3f}s"
    finally:
        app.dependency_overrides.pop(get_catalog_repo, None)
