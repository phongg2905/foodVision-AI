"""Stage 4 Automated Verification Suite for TV2 (Phong Phạm) — Card #24 User APIs, USDA Tier-2 & LR (`TP 08`, `TP 10`, `TP 11`).

Covers:
- `FR-10`, `TC-17`, `TC-18`, `SEC-01`: Idempotent `/favorites` (`201`/`200`/`204`) & strict per-user isolation
- `FR-11`, `ADR-012`, `TC-19`, `TC-45`, `SEC-06`: Context-aware `/feedback` upsert (`UNIQUE NULLS NOT DISTINCT`) & scan ownership guard
- `FR-12`, `TC-20`, `TC-28`, `TC-47`, `SEC-06`: Opt-in `/scan-sessions` CRUD & cascade deletion without colliding with `scan_id=null` feedback
- `TP 10`, `TP 11`, `ADR-004`, `MATH-07`, `DEF-09`: Linear portion scaling & USDA FoodData Central per-100g quantitative nutrition
- `TP 08`, `MATH-05`, `DEF-08`: Logistic Regression preference learning, `ADR-012` latest feedback deduplication, and cold-start safe blending
"""

from __future__ import annotations

import math

from fastapi.testclient import TestClient

from app.core.database import InMemoryCatalogRepository, get_catalog_repo
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_DAU_HU,
    ING_TRUNG_GA,
    REC_CANH_CA_CHUA_TRUNG,
    REC_DAU_HU_SOT_CA,
    REC_DRAFT,
    REC_TRUNG_XAO_CA_CHUA,
)
from app.main import create_app
from app.schemas.user_features import BBox, Detection
from app.services.nutrition import (
    PortionIngredientInput,
    estimate_usda_nutrition,
    scale_portion_grams,
)
from app.services.personalization_lr import (
    adaptive_lambda_pers,
    blend_personalized_score,
    extract_recipe_feature_vector,
    fit_user_lr_weights,
    predict_preference_prob,
    sgd_update_theta,
)

USER_A = "00000000-0000-4000-8000-000000000011"
USER_B = "00000000-0000-4000-8000-000000000022"


def _make_client() -> tuple[TestClient, InMemoryCatalogRepository]:
    repo = InMemoryCatalogRepository()
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    return TestClient(app), repo


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer user:{uid}"}


def test_favorites_idempotent_and_user_isolation_tc17_tc18_sec01() -> None:
    client, _repo = _make_client()

    # Guest rejected with 401
    assert client.get("/api/v1/favorites").status_code == 401

    # Draft / unknown recipe -> 404 RECIPE_NOT_FOUND
    r_draft = client.post(
        "/api/v1/favorites",
        headers=_auth(USER_A),
        json={"recipe_id": REC_DRAFT},
    )
    assert r_draft.status_code == 404
    assert r_draft.json()["code"] == "RECIPE_NOT_FOUND"

    # TC-17: User A adds favorite twice -> 1st 201 Created, 2nd 200 OK idempotent
    r1 = client.post(
        "/api/v1/favorites",
        headers=_auth(USER_A),
        json={"recipe_id": REC_TRUNG_XAO_CA_CHUA},
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["recipe"]["slug"] == "trung-xao-ca-chua"

    r2 = client.post(
        "/api/v1/favorites",
        headers=_auth(USER_A),
        json={"recipe_id": REC_TRUNG_XAO_CA_CHUA},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["created_at"] == r1.json()["created_at"]

    list_a = client.get("/api/v1/favorites", headers=_auth(USER_A))
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1

    # SEC-01: User B cannot see User A's favorites
    list_b = client.get("/api/v1/favorites", headers=_auth(USER_B))
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0

    # TC-18: User A removes favorite -> 204 No Content (idempotent on repeat)
    d1 = client.delete(f"/api/v1/favorites/{REC_TRUNG_XAO_CA_CHUA}", headers=_auth(USER_A))
    assert d1.status_code == 204
    d2 = client.delete(f"/api/v1/favorites/{REC_TRUNG_XAO_CA_CHUA}", headers=_auth(USER_A))
    assert d2.status_code == 204

    assert client.get("/api/v1/favorites", headers=_auth(USER_A)).json()["total"] == 0


def test_feedback_upsert_validation_and_ownership_tc19_tc45_sec06() -> None:
    client, repo = _make_client()

    # TC-19: rating=6 -> 422 VALIDATION_ERROR; rating=3 -> 201 Created
    r_bad = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_A),
        json={"recipe_id": REC_DAU_HU_SOT_CA, "rating": 6},
    )
    assert r_bad.status_code == 422
    assert r_bad.json()["code"] == "VALIDATION_ERROR"

    # TC-45(1): scan_id=null -> 1st call 201, 2nd call 200 updating same record
    fb1 = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_A),
        json={"recipe_id": REC_DAU_HU_SOT_CA, "scan_id": None, "rating": 3, "note": "Tạm ổn"},
    )
    assert fb1.status_code == 201, fb1.text
    fb1_id = fb1.json()["id"]

    fb2 = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_A),
        json={"recipe_id": REC_DAU_HU_SOT_CA, "scan_id": None, "rating": 5, "note": "Rất ngon!"},
    )
    assert fb2.status_code == 200, fb2.text
    assert fb2.json()["id"] == fb1_id
    assert fb2.json()["rating"] == 5

    # TC-45(2): Same recipe_id WITH valid scan_id S1 -> creates distinct row (201 Created)
    active_model_id = "44444444-4444-4444-8444-444444444401"
    scan_s1 = repo.create_scan_session_with_detections(
        user_id=USER_A,
        model_id=active_model_id,
        confirmed_ingredient_ids=[ING_DAU_HU, ING_CA_CHUA],
    )
    fb_s1 = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_A),
        json={"recipe_id": REC_DAU_HU_SOT_CA, "scan_id": scan_s1, "rating": 4},
    )
    assert fb_s1.status_code == 201, fb_s1.text
    assert fb_s1.json()["id"] != fb1_id

    # SEC-06: User B attempting feedback with User A's scan_id -> 404 SCAN_NOT_OWNED
    fb_hijack = client.post(
        "/api/v1/feedback",
        headers=_auth(USER_B),
        json={"recipe_id": REC_DAU_HU_SOT_CA, "scan_id": scan_s1, "rating": 1},
    )
    assert fb_hijack.status_code == 404
    assert fb_hijack.json()["code"] == "SCAN_NOT_OWNED"


def test_scan_sessions_history_ownership_and_cascade_delete_tc20_tc28_tc47() -> None:
    client, repo = _make_client()
    active_model_id = "44444444-4444-4444-8444-444444444401"

    det_tomato = Detection(
        class_index=0,
        class_name="tomato",
        ingredient_id=ING_CA_CHUA,
        ingredient_name="Cà chua",
        confidence=0.93,
        needs_confirmation=False,
        bbox=BBox(x1=0.1, y1=0.1, x2=0.4, y2=0.4),
    )
    scan_s1 = repo.create_scan_session_with_detections(
        user_id=USER_A,
        model_id=active_model_id,
        detections=[det_tomato],
    )

    # TC-20: Sync HITL-confirmed ingredients via /recommendations with scan_id
    rec_res = client.post(
        "/api/v1/recommendations",
        headers=_auth(USER_A),
        json={"scan_id": scan_s1, "ingredient_ids": [ING_CA_CHUA, ING_TRUNG_GA]},
    )
    assert rec_res.status_code == 200

    # List & Detail for owner User A
    list_res = client.get("/api/v1/scan-sessions", headers=_auth(USER_A))
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["ingredients_count"] == 2

    det_res = client.get(f"/api/v1/scan-sessions/{scan_s1}", headers=_auth(USER_A))
    assert det_res.status_code == 200
    assert det_res.json()["confirmed_ingredient_ids"] == [ING_CA_CHUA, ING_TRUNG_GA]
    assert len(det_res.json()["detections"]) == 1

    # TC-28 & SEC-06: User B gets 404 SCAN_NOT_OWNED on GET and DELETE
    assert client.get(f"/api/v1/scan-sessions/{scan_s1}", headers=_auth(USER_B)).status_code == 404
    assert client.delete(f"/api/v1/scan-sessions/{scan_s1}", headers=_auth(USER_B)).status_code == 404

    # TC-47: User A has both scan_id=null feedback AND scan_id=S1 feedback on same recipe;
    # deleting S1 returns 204, cascades S1 feedback, and preserves scan_id=null feedback!
    assert (
        client.post(
            "/api/v1/feedback",
            headers=_auth(USER_A),
            json={"recipe_id": REC_TRUNG_XAO_CA_CHUA, "scan_id": None, "rating": 5},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/feedback",
            headers=_auth(USER_A),
            json={"recipe_id": REC_TRUNG_XAO_CA_CHUA, "scan_id": scan_s1, "rating": 2},
        ).status_code
        == 201
    )
    assert len(repo.get_user_feedback_samples(USER_A)) == 2

    del_res = client.delete(f"/api/v1/scan-sessions/{scan_s1}", headers=_auth(USER_A))
    assert del_res.status_code == 204
    assert client.get("/api/v1/scan-sessions", headers=_auth(USER_A)).json()["total"] == 0

    remaining_fb = repo.get_user_feedback_samples(USER_A)
    assert len(remaining_fb) == 1
    assert remaining_fb[0].rating == 5


def test_usda_two_tier_nutrition_and_portion_scaling_math07_def09() -> None:
    client, repo = _make_client()
    nutr_map = repo.get_ingredient_nutrients_by_ids([ING_CA_CHUA, ING_TRUNG_GA])

    # 1. Exact MATH-07 unit test: 100g tomato (18 kcal/100g) + 60g egg (144 kcal/100g)
    items_math07 = [
        PortionIngredientInput(ingredient_id=ING_CA_CHUA, is_required=True, base_grams=100.0),
        PortionIngredientInput(ingredient_id=ING_TRUNG_GA, is_required=True, base_grams=60.0),
    ]
    est_base = estimate_usda_nutrition(items_math07, nutr_map, base_servings=2, target_servings=2)
    assert est_base is not None
    assert est_base.kcal == 104.4
    assert est_base.scaling_warning_vi is None

    est_double = estimate_usda_nutrition(items_math07, nutr_map, base_servings=2, target_servings=4)
    assert est_double is not None
    assert est_double.kcal == 208.8
    assert scale_portion_grams(100.0, 2, 4) == 200.0
    assert est_double.scaling_warning_vi is not None

    # 2. Safety policy (ADR-004): missing grams on required ingredient -> returns None (no guessing!)
    est_missing_grams = estimate_usda_nutrition(
        [PortionIngredientInput(ingredient_id=ING_CA_CHUA, is_required=True, base_grams=None)],
        nutr_map,
        base_servings=2,
        target_servings=2,
    )
    assert est_missing_grams is None

    # 3. DEF-09 API integration: GET /api/v1/recipes/{id} vs ?servings=4
    r_base = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}")
    assert r_base.status_code == 200
    d_base = r_base.json()
    assert d_base["base_servings"] == 2
    assert d_base["servings"] == 2
    assert d_base["usda_nutrition"] is not None
    assert "không thay thế tư vấn y tế" in d_base["nutrition_disclaimer_vi"]

    r_scaled = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}?servings=4")
    assert r_scaled.status_code == 200
    d_scaled = r_scaled.json()
    assert d_scaled["servings"] == 4
    assert d_scaled["usda_nutrition"]["kcal"] == round(d_base["usda_nutrition"]["kcal"] * 2.0, 2)
    assert d_scaled["usda_nutrition"]["scaling_warning_vi"] is not None
    assert d_scaled["ingredients"][0]["grams"] == round(d_base["ingredients"][0]["grams"] * 2.0, 2)


def test_logistic_regression_preference_learning_math05_def08() -> None:
    # 1. Exact MATH-05 verification: x=[1,1,0], theta=[0.2, 0.3, -0.1], y=1, eta=0.1
    x = [1.0, 1.0, 0.0]
    theta = [0.2, 0.3, -0.1]
    p = predict_preference_prob(x, theta)
    assert math.isclose(p, 1.0 / (1.0 + math.exp(-0.5)), rel_tol=1e-9)
    assert round(p, 3) == 0.622

    # Cold-start lambda_pers=0 -> S_final == S exact
    assert blend_personalized_score(83.75, p, lambda_pers=0.0) == 83.75

    theta_next = sgd_update_theta(x, theta, y=1, learning_rate=0.1)
    assert theta_next[0] > theta[0]
    assert theta_next[1] > theta[1]
    assert theta_next[2] == theta[2]

    # 2. DEF-08: Two users with opposite feedback histories get divergent personalized rankings
    client, repo = _make_client()
    recipes_by_id = {r.id: r for r in repo.get_all_published_recipes()}

    # User A loves quick stir-fry/soup (Trứng xào cà chua, Canh cà chua trứng), dislikes braised dishes
    client.post("/api/v1/feedback", headers=_auth(USER_A), json={"recipe_id": REC_TRUNG_XAO_CA_CHUA, "rating": 5})
    client.post("/api/v1/feedback", headers=_auth(USER_A), json={"recipe_id": REC_CANH_CA_CHUA_TRUNG, "rating": 5})
    client.post("/api/v1/feedback", headers=_auth(USER_A), json={"recipe_id": REC_DAU_HU_SOT_CA, "rating": 1})

    # User B loves braised dishes (Đậu hũ sốt cà chua), dislikes quick stir-fry/soup
    client.post("/api/v1/feedback", headers=_auth(USER_B), json={"recipe_id": REC_DAU_HU_SOT_CA, "rating": 5})
    client.post("/api/v1/feedback", headers=_auth(USER_B), json={"recipe_id": REC_TRUNG_XAO_CA_CHUA, "rating": 1})
    client.post("/api/v1/feedback", headers=_auth(USER_B), json={"recipe_id": REC_CANH_CA_CHUA_TRUNG, "rating": 1})

    theta_a, n_a = fit_user_lr_weights(recipes_by_id, repo.get_user_feedback_samples(USER_A))
    theta_b, n_b = fit_user_lr_weights(recipes_by_id, repo.get_user_feedback_samples(USER_B))
    assert n_a == 3 and n_b == 3
    assert adaptive_lambda_pers(0) == 0.0
    lam = adaptive_lambda_pers(n_a)
    assert lam > 0.0

    x_stir = extract_recipe_feature_vector(recipes_by_id[REC_TRUNG_XAO_CA_CHUA])
    x_braise = extract_recipe_feature_vector(recipes_by_id[REC_DAU_HU_SOT_CA])

    s_a_stir = blend_personalized_score(85.0, predict_preference_prob(x_stir, theta_a), lam)
    s_a_braise = blend_personalized_score(85.0, predict_preference_prob(x_braise, theta_a), lam)
    s_b_stir = blend_personalized_score(85.0, predict_preference_prob(x_stir, theta_b), lam)
    s_b_braise = blend_personalized_score(85.0, predict_preference_prob(x_braise, theta_b), lam)

    assert s_a_stir > s_a_braise
    assert s_b_braise > s_b_stir
