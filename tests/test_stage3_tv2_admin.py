"""Stage 3 Automated Verification Suite for TV2 (Phong Phạm) — Card #21 Admin CMS Backend.

Covers:
- `FR-09a`, `NFR-04`, `SEC-03`, `TC-16`: Server-side `profiles.role == 'admin'` guard (`401` / `403`) & `Admin --|> User` inheritance
- `FR-13`, `BR-01`, `BR-05`, `ADR-013`, `TC-21`, `TC-22`, `TC-38`: Admin Recipes CRUD + 4 publishability guards on both `status -> published` and `PATCH` of an already `published` recipe
- `FR-14`, `BR-04`, `TC-23`, `TC-39`: Admin Ingredients CRUD, regional alias normalization (`norm_vi`), `409 DUPLICATE_SLUG`, and `400 INGREDIENT_IN_USE`
- `FR-15`, `BR-02`, `BR-12`, `TC-24`, `TC-41`, `TC-42`, `TC-44`: Admin AI Models & Labels lifecycle, `400 MODEL_IMMUTABLE`, `400 INVALID_LABEL_MAPPING`, `400 MODEL_NOT_ACTIVATABLE`, atomic single-active transition & rollback (`archived -> active`)
- `FR-16`, `FR-17`, `BR-03`, `BR-10`, `TC-25`, `TC-26`: Public & Admin Nutrition Tags (`source_url` validation) and scrubbed Audit Logs
"""

from __future__ import annotations

import base64
import json
import time

from fastapi.testclient import TestClient

from app.core.auth import ADMIN_SEED_USER_ID
from app.core.database import InMemoryCatalogRepository
from app.core.seed_fixtures import (
    ING_CA_CHUA,
    ING_DAU_HU,
    ING_INACTIVE,
    ING_MUOI,
    ING_TRUNG_GA,
    REC_DAU_HU_SOT_CA,
    REC_TRUNG_XAO_CA_CHUA,
)
from app.schemas.admin import scrub_audit_payload

ADMIN_HEADERS = {"Authorization": f"Bearer user:{ADMIN_SEED_USER_ID}"}
USER_A_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
USER_HEADERS = {"Authorization": f"Bearer user:{USER_A_ID}"}


def _make_unsigned_jwt(payload: dict) -> str:
    hdr = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    bdy = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{hdr}.{bdy}.fakesig"


# ==============================================================================
# 1. Admin Auth Middleware (`FR-09a`, `SEC-03`, `TC-16`)
# ==============================================================================


def test_admin_auth_middleware_sec03_and_role_inheritance_tc16(
    client: TestClient,
    repo: InMemoryCatalogRepository,
) -> None:
    # 1. Missing token -> 401 UNAUTHORIZED
    r_no_auth = client.get("/api/v1/admin/recipes")
    assert r_no_auth.status_code == 401
    assert r_no_auth.json()["code"] == "UNAUTHORIZED"

    # 2. Expired JWT -> 401 UNAUTHORIZED
    expired_jwt = _make_unsigned_jwt({"sub": ADMIN_SEED_USER_ID, "exp": int(time.time()) - 60})
    r_expired = client.get(
        "/api/v1/admin/recipes",
        headers={"Authorization": f"Bearer {expired_jwt}"},
    )
    assert r_expired.status_code == 401

    # 3. SEC-03: Normal user attempting POST /admin/recipes OR spoofing `"role": "admin"` inside JWT claim -> 403 FORBIDDEN
    spoofed_jwt = _make_unsigned_jwt(
        {"sub": USER_A_ID, "role": "admin", "exp": int(time.time()) + 3600}
    )
    for hdrs in (USER_HEADERS, {"Authorization": f"Bearer {spoofed_jwt}"}):
        r_forbid = client.post(
            "/api/v1/admin/recipes",
            headers=hdrs,
            json={
                "slug": "mon-gia-mao",
                "name_vi": "Món giả mạo",
                "cuisine_code": "VN",
                "prep_minutes": 5,
                "cook_minutes": 10,
                "ingredients": [{"ingredient_id": ING_CA_CHUA, "is_required": True}],
                "steps": [{"step_no": 1, "instruction": "Xào nhanh."}],
            },
        )
        assert r_forbid.status_code == 403
        assert r_forbid.json()["code"] == "FORBIDDEN"

    # Verify zero audit logs were recorded from forbidden attempts
    logs, total_logs = repo.admin_list_audit_logs()
    assert total_logs == 0
    assert logs == []

    # 4. TC-16: Admin account succeeds on `/admin/*` AND inherits User access (`GET /preferences`)
    assert client.get("/api/v1/admin/recipes", headers=ADMIN_HEADERS).status_code == 200
    assert client.get("/api/v1/preferences", headers=ADMIN_HEADERS).status_code == 200


# ==============================================================================
# 2. Admin Recipes & 4 Publishability Guards (`FR-13`, `BR-01`, `TC-21`, `TC-22`, `TC-38`)
# ==============================================================================


def test_admin_recipes_lifecycle_and_br01_guards_tc21_tc22_tc38(
    client: TestClient,
) -> None:
    # Duplicate slug -> 409 DUPLICATE_SLUG
    r_dup = client.post(
        "/api/v1/admin/recipes",
        headers=ADMIN_HEADERS,
        json={
            "slug": "trung-xao-ca-chua",
            "name_vi": "Trứng xào trùng",
            "cuisine_code": "VN",
            "prep_minutes": 5,
            "cook_minutes": 10,
            "ingredients": [{"ingredient_id": ING_CA_CHUA, "is_required": True}],
            "steps": [{"step_no": 1, "instruction": "Bước 1"}],
        },
    )
    assert r_dup.status_code == 409
    assert r_dup.json()["code"] == "DUPLICATE_SLUG"

    # ADR-013: prep_minutes + cook_minutes == 0 -> 422 VALIDATION_ERROR
    r_zero_time = client.post(
        "/api/v1/admin/recipes",
        headers=ADMIN_HEADERS,
        json={
            "slug": "mon-khong-thoi-gian",
            "name_vi": "Món 0 phút",
            "cuisine_code": "VN",
            "prep_minutes": 0,
            "cook_minutes": 0,
            "ingredients": [{"ingredient_id": ING_CA_CHUA, "is_required": True}],
            "steps": [{"step_no": 1, "instruction": "Bước 1"}],
        },
    )
    assert r_zero_time.status_code == 422
    assert r_zero_time.json()["code"] == "VALIDATION_ERROR"

    # TC-21: Create draft recipe (initially missing steps to test TC-22)
    r_create = client.post(
        "/api/v1/admin/recipes",
        headers=ADMIN_HEADERS,
        json={
            "slug": "dau-hu-chien-sa",
            "name_vi": "Đậu hũ chiên giòn",
            "cuisine_code": "VN",
            "prep_minutes": 10,
            "cook_minutes": 15,
            "ingredients": [
                {
                    "ingredient_id": ING_DAU_HU,
                    "is_required": True,
                    "role": "core",
                    "dish_role": "main",
                    "weight": 4.0,
                    "grams": 200.0,
                },
                {
                    "ingredient_id": ING_MUOI,
                    "is_required": True,
                    "role": "spice",
                    "dish_role": "sub",
                    "weight": 1.0,
                },
            ],
            "steps": [],
        },
    )
    assert r_create.status_code == 201
    created = r_create.json()
    rec_id = created["id"]
    assert created["status"] == "draft"

    # Hidden on public GET /recipes/{id}, visible on GET /admin/recipes/{id}
    assert client.get(f"/api/v1/recipes/{rec_id}").status_code == 404
    r_adm_detail = client.get(f"/api/v1/admin/recipes/{rec_id}", headers=ADMIN_HEADERS)
    assert r_adm_detail.status_code == 200
    assert r_adm_detail.json()["status"] == "draft"
    assert r_adm_detail.json()["author_id"] == ADMIN_SEED_USER_ID

    # TC-22: Publish recipe missing steps -> 400 RECIPE_NOT_PUBLISHABLE (`missing_steps`)
    r_pub_no_steps = client.patch(
        f"/api/v1/admin/recipes/{rec_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )
    assert r_pub_no_steps.status_code == 400
    assert r_pub_no_steps.json()["code"] == "RECIPE_NOT_PUBLISHABLE"
    assert "missing_steps" in r_pub_no_steps.json()["details"]["reasons"]

    # TC-38(1): Patch draft to have ONLY pantry ingredients + valid step, then publish -> `missing_required_main_ingredient`
    assert (
        client.patch(
            f"/api/v1/admin/recipes/{rec_id}",
            headers=ADMIN_HEADERS,
            json={
                "ingredients": [{"ingredient_id": ING_MUOI, "is_required": True}],
                "steps": [{"step_no": 1, "instruction": "Hòa muối.", "estimated_minutes": 5}],
            },
        ).status_code
        == 200
    )
    r_pub_pantry_only = client.patch(
        f"/api/v1/admin/recipes/{rec_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )
    assert r_pub_pantry_only.status_code == 400
    assert "missing_required_main_ingredient" in r_pub_pantry_only.json()["details"]["reasons"]

    # TC-38(2): Patch draft with an inactive ingredient -> `inactive_ingredient`
    assert (
        client.patch(
            f"/api/v1/admin/recipes/{rec_id}",
            headers=ADMIN_HEADERS,
            json={
                "ingredients": [
                    {"ingredient_id": ING_DAU_HU, "is_required": True},
                    {"ingredient_id": ING_INACTIVE, "is_required": False},
                ],
            },
        ).status_code
        == 200
    )
    r_pub_inactive = client.patch(
        f"/api/v1/admin/recipes/{rec_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )
    assert r_pub_inactive.status_code == 400
    assert "inactive_ingredient" in r_pub_inactive.json()["details"]["reasons"]

    # TC-38(3): Patch draft with valid ingredients but step estimated_minutes=30 > total_minutes=25 -> `step_exceeds_total_minutes`
    assert (
        client.patch(
            f"/api/v1/admin/recipes/{rec_id}",
            headers=ADMIN_HEADERS,
            json={
                "ingredients": [
                    {"ingredient_id": ING_DAU_HU, "is_required": True},
                    {"ingredient_id": ING_MUOI, "is_required": True},
                ],
                "steps": [{"step_no": 1, "instruction": "Chiên quá giờ.", "estimated_minutes": 30}],
            },
        ).status_code
        == 200
    )
    r_pub_exceed_step = client.patch(
        f"/api/v1/admin/recipes/{rec_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )
    assert r_pub_exceed_step.status_code == 400
    assert "step_exceeds_total_minutes" in r_pub_exceed_step.json()["details"]["reasons"]

    # Fix step time -> Publish succeeds (200 OK)!
    assert (
        client.patch(
            f"/api/v1/admin/recipes/{rec_id}",
            headers=ADMIN_HEADERS,
            json={
                "steps": [{"step_no": 1, "instruction": "Chiên giòn 15 phút.", "estimated_minutes": 15}],
            },
        ).status_code
        == 200
    )
    r_pub_ok = client.patch(
        f"/api/v1/admin/recipes/{rec_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "published"},
    )
    assert r_pub_ok.status_code == 200
    assert r_pub_ok.json()["status"] == "published"
    assert client.get(f"/api/v1/recipes/{rec_id}").status_code == 200

    # TC-38(4): Attempting `PATCH /admin/recipes/{id}` on an ALREADY `published` recipe that violates BR-01 is rejected!
    r_patch_violate = client.patch(
        f"/api/v1/admin/recipes/{rec_id}",
        headers=ADMIN_HEADERS,
        json={"steps": []},
    )
    assert r_patch_violate.status_code == 400
    assert r_patch_violate.json()["code"] == "RECIPE_NOT_PUBLISHABLE"
    assert "missing_steps" in r_patch_violate.json()["details"]["reasons"]

    # Previous valid published steps remain intact!
    intact = client.get(f"/api/v1/recipes/{rec_id}").json()
    assert len(intact["steps"]) == 1
    assert intact["steps"][0]["estimated_minutes"] == 15


# ==============================================================================
# 3. Admin Ingredients, Aliases & `INGREDIENT_IN_USE` (`FR-14`, `TC-23`, `TC-39`)
# ==============================================================================


def test_admin_ingredients_aliases_and_in_use_guards_tc23_tc39(
    client: TestClient,
) -> None:
    # TC-23(1): Duplicate slug -> 409 DUPLICATE_SLUG
    r_dup = client.post(
        "/api/v1/admin/ingredients",
        headers=ADMIN_HEADERS,
        json={"slug": "dau-hu", "name_vi": "Đậu hũ trùng", "category": "protein"},
    )
    assert r_dup.status_code == 409
    assert r_dup.json()["code"] == "DUPLICATE_SLUG"

    # TC-23(2): Create new ingredient with regional synonyms (`bắp non`, `ngô bao tử`) and search unaccented
    r_new_ing = client.post(
        "/api/v1/admin/ingredients",
        headers=ADMIN_HEADERS,
        json={
            "slug": "bap-non",
            "name_vi": "Bắp non",
            "category": "vegetable",
            "is_active": True,
            "aliases": ["ngô bao tử", "bắp bao tử"],
        },
    )
    assert r_new_ing.status_code == 201
    new_ing_id = r_new_ing.json()["id"]

    r_search = client.get("/api/v1/ingredients?q=ngo bao tu")
    assert r_search.status_code == 200
    assert r_search.json()["items"][0]["id"] == new_ing_id

    # Admin list includes inactive ingredients (`ING_INACTIVE`)
    r_admin_list = client.get("/api/v1/admin/ingredients?limit=50", headers=ADMIN_HEADERS)
    assert r_admin_list.status_code == 200
    assert any(it["id"] == ING_INACTIVE for it in r_admin_list.json()["items"])

    # TC-39(1): Cannot deactivate or change category of ingredient used in a `published` recipe (`ING_CA_CHUA`)
    for bad_patch in ({"is_active": False}, {"category": "pantry"}):
        r_in_use_rec = client.patch(
            f"/api/v1/admin/ingredients/{ING_CA_CHUA}",
            headers=ADMIN_HEADERS,
            json=bad_patch,
        )
        assert r_in_use_rec.status_code == 400
        assert r_in_use_rec.json()["code"] == "INGREDIENT_IN_USE"
        assert REC_TRUNG_XAO_CA_CHUA in r_in_use_rec.json()["details"]["affected_published_recipe_ids"]

    # TC-39(2): Cannot deactivate or change category to `pantry` when mapped in `ai_labels` of a `draft` model
    draft_model = client.post(
        "/api/v1/admin/ai-models",
        headers=ADMIN_HEADERS,
        json={
            "version": "yolo-draft-tc39",
            "family": "yolov8n",
            "dataset_version": "v1.0",
            "artifact_ref": "weights/v1.pt",
            "class_count": 1,
        },
    ).json()
    assert (
        client.post(
            "/api/v1/admin/ai-labels",
            headers=ADMIN_HEADERS,
            json={
                "model_id": draft_model["id"],
                "class_index": 0,
                "class_name": "baby_corn",
                "ingredient_id": new_ing_id,
            },
        ).status_code
        == 201
    )

    r_in_use_model = client.patch(
        f"/api/v1/admin/ingredients/{new_ing_id}",
        headers=ADMIN_HEADERS,
        json={"category": "pantry"},
    )
    assert r_in_use_model.status_code == 400
    assert r_in_use_model.json()["code"] == "INGREDIENT_IN_USE"
    assert draft_model["id"] in r_in_use_model.json()["details"]["affected_active_or_draft_model_ids"]


# ==============================================================================
# 4. Admin AI Models, Labels & Rollback (`FR-15`, `TC-24`, `TC-41`, `TC-42`, `TC-44`)
# ==============================================================================


def test_admin_ai_models_immutability_and_rollback_tc24_tc41_tc42_tc44(
    client: TestClient,
) -> None:
    # Create an isolated ingredient for archived rollback failure test (`TC-41(2)`)
    ing_only_m1 = client.post(
        "/api/v1/admin/ingredients",
        headers=ADMIN_HEADERS,
        json={"slug": "cu-sen-test", "name_vi": "Củ sen", "category": "vegetable"},
    ).json()["id"]

    # Register Model v1 (`class_count = 2`)
    m1 = client.post(
        "/api/v1/admin/ai-models",
        headers=ADMIN_HEADERS,
        json={
            "version": "food-yolo-v1",
            "family": "yolov8s",
            "dataset_version": "ds-v1",
            "artifact_ref": "models/food-yolo-v1.pt",
            "confidence_threshold": 0.25,
            "class_count": 2,
        },
    ).json()
    assert m1["status"] == "draft"

    # TC-44: Mapping to `pantry` (`ING_MUOI`) or `inactive` (`ING_INACTIVE`) -> 400 INVALID_LABEL_MAPPING
    for bad_ing in (ING_MUOI, ING_INACTIVE):
        r_bad_lbl = client.post(
            "/api/v1/admin/ai-labels",
            headers=ADMIN_HEADERS,
            json={
                "model_id": m1["id"],
                "class_index": 0,
                "class_name": "bad_cls",
                "ingredient_id": bad_ing,
            },
        )
        assert r_bad_lbl.status_code == 400
        assert r_bad_lbl.json()["code"] == "INVALID_LABEL_MAPPING"

    # Map class 0 -> ING_CA_CHUA; leave class 1 unmapped first (`TC-24`)
    lbl0 = client.post(
        "/api/v1/admin/ai-labels",
        headers=ADMIN_HEADERS,
        json={
            "model_id": m1["id"],
            "class_index": 0,
            "class_name": "tomato",
            "ingredient_id": ING_CA_CHUA,
        },
    ).json()

    r_incomplete = client.patch(
        f"/api/v1/admin/ai-models/{m1['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert r_incomplete.status_code == 400
    assert r_incomplete.json()["code"] == "MODEL_NOT_ACTIVATABLE"
    assert r_incomplete.json()["details"]["unmapped_class_indices"] == [1]

    # Map class 1 -> ing_only_m1, then activate m1 -> 200 OK (`active`)
    assert (
        client.post(
            "/api/v1/admin/ai-labels",
            headers=ADMIN_HEADERS,
            json={
                "model_id": m1["id"],
                "class_index": 1,
                "class_name": "lotus_root",
                "ingredient_id": ing_only_m1,
            },
        ).status_code
        == 201
    )
    r_act_m1 = client.patch(
        f"/api/v1/admin/ai-models/{m1['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert r_act_m1.status_code == 200
    assert r_act_m1.json()["status"] == "active"

    # TC-42: `active` model labels are immutable (`POST` & `PATCH` -> 400 MODEL_IMMUTABLE)
    assert (
        client.patch(
            f"/api/v1/admin/ai-labels/{lbl0['id']}",
            headers=ADMIN_HEADERS,
            json={"ingredient_id": ING_TRUNG_GA},
        ).status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/v1/admin/ai-labels/{lbl0['id']}",
            headers=ADMIN_HEADERS,
            json={"ingredient_id": ING_TRUNG_GA},
        ).json()["code"]
        == "MODEL_IMMUTABLE"
    )

    # Register & activate Model v2 -> m1 atomically becomes `archived` (`TC-24`)
    m2 = client.post(
        "/api/v1/admin/ai-models",
        headers=ADMIN_HEADERS,
        json={
            "version": "food-yolo-v2",
            "family": "yolov8s",
            "dataset_version": "ds-v2",
            "artifact_ref": "models/food-yolo-v2.pt",
            "class_count": 1,
        },
    ).json()
    assert (
        client.post(
            "/api/v1/admin/ai-labels",
            headers=ADMIN_HEADERS,
            json={
                "model_id": m2["id"],
                "class_index": 0,
                "class_name": "egg",
                "ingredient_id": ING_TRUNG_GA,
            },
        ).status_code
        == 201
    )
    assert (
        client.patch(
            f"/api/v1/admin/ai-models/{m2['id']}/status",
            headers=ADMIN_HEADERS,
            json={"status": "active"},
        ).status_code
        == 200
    )

    models_list = client.get("/api/v1/admin/ai-models", headers=ADMIN_HEADERS).json()["items"]
    status_by_id = {m["id"]: m["status"] for m in models_list}
    assert status_by_id[m2["id"]] == "active"
    assert status_by_id[m1["id"]] == "archived"

    # TC-42 on `archived` model: still immutable!
    r_imm_arch = client.patch(
        f"/api/v1/admin/ai-labels/{lbl0['id']}",
        headers=ADMIN_HEADERS,
        json={"ingredient_id": ING_TRUNG_GA},
    )
    assert r_imm_arch.status_code == 400
    assert r_imm_arch.json()["code"] == "MODEL_IMMUTABLE"

    # TC-41(1): Successful rollback `m1` (`archived -> active`) while `ing_only_m1` is still valid
    r_rb_ok = client.patch(
        f"/api/v1/admin/ai-models/{m1['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert r_rb_ok.status_code == 200
    assert r_rb_ok.json()["status"] == "active"

    # Switch back to `m2` (`active`) so `m1` returns to `archived`
    assert (
        client.patch(
            f"/api/v1/admin/ai-models/{m2['id']}/status",
            headers=ADMIN_HEADERS,
            json={"status": "active"},
        ).status_code
        == 200
    )

    # TC-41(2): Change `ing_only_m1` (used ONLY in `archived` m1) to `category='pantry'` -> 200 OK!
    r_cat_pantry = client.patch(
        f"/api/v1/admin/ingredients/{ing_only_m1}",
        headers=ADMIN_HEADERS,
        json={"category": "pantry"},
    )
    assert r_cat_pantry.status_code == 200

    # Now rollback `m1` (`archived -> active`) MUST be blocked with 400 MODEL_NOT_ACTIVATABLE!
    r_rb_fail = client.patch(
        f"/api/v1/admin/ai-models/{m1['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert r_rb_fail.status_code == 400
    assert r_rb_fail.json()["code"] == "MODEL_NOT_ACTIVATABLE"
    assert r_rb_fail.json()["details"]["invalid_mapped_class_indices"] == [1]


# ==============================================================================
# 5. Nutrition Tags & Audit Logs (`FR-16`, `FR-17`, `TC-25`, `TC-26`)
# ==============================================================================


def test_admin_nutrition_tags_and_audit_logs_tc25_tc26(client: TestClient) -> None:
    # Public /nutrition-tags only returns active tags, whereas /admin/nutrition-tags returns inactive too
    pub_tags = client.get("/api/v1/nutrition-tags").json()
    adm_tags = client.get("/api/v1/admin/nutrition-tags", headers=ADMIN_HEADERS).json()
    assert all(t["is_active"] is True for t in pub_tags)
    assert len(adm_tags) > len(pub_tags)

    # Create a new nutrition tag
    r_tag = client.post(
        "/api/v1/admin/nutrition-tags",
        headers=ADMIN_HEADERS,
        json={
            "code": "LOW_CARB_FRIENDLY",
            "name_vi": "Ít tinh bột",
            "description": "Phù hợp thực đơn giảm tinh bột.",
            "is_active": True,
        },
    )
    assert r_tag.status_code == 201
    tag_id = r_tag.json()["id"]

    # TC-25: Invalid or missing `source_url` -> 422 VALIDATION_ERROR
    for bad_url in ("", "ftp://invalid.example.com/ref", "not-a-url"):
        r_bad = client.put(
            f"/api/v1/admin/ingredients/{ING_DAU_HU}/nutrition-tags",
            headers=ADMIN_HEADERS,
            json={"tags": [{"nutrition_tag_id": tag_id, "source_url": bad_url}]},
        )
        assert r_bad.status_code == 422
        assert r_bad.json()["code"] == "VALIDATION_ERROR"

    # TC-25: Valid `https://` source_url -> 200 OK & reflected in public recipe detail!
    r_ok = client.put(
        f"/api/v1/admin/ingredients/{ING_DAU_HU}/nutrition-tags",
        headers=ADMIN_HEADERS,
        json={
            "tags": [
                {
                    "nutrition_tag_id": tag_id,
                    "source_url": "https://fdc.nal.usda.gov/fdc-app.html#/food-details/172475/nutrients",
                    "note": "Nguồn tham khảo USDA cho đậu hũ.",
                }
            ]
        },
    )
    assert r_ok.status_code == 200
    assert r_ok.json()[0]["tag"]["code"] == "LOW_CARB_FRIENDLY"

    rec_detail = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}").json()
    assert any(
        ev["tag"]["code"] == "LOW_CARB_FRIENDLY" for ev in rec_detail["nutrition_evidence"]
    )

    # TC-26: Audit logs recorded with actor_id, action, entity_type, entity_id, created_at & secret scrubbing
    r_logs = client.get("/api/v1/admin/audit-logs?limit=20", headers=ADMIN_HEADERS)
    assert r_logs.status_code == 200
    log_items = r_logs.json()["items"]
    assert len(log_items) >= 2
    assert all(it["actor_id"] == ADMIN_SEED_USER_ID for it in log_items)

    scrubbed = scrub_audit_payload(
        {
            "slug": "test",
            "access_token": "secret-jwt",
            "supabase_service_role_key": "never-log",
            "nested": {"password": "123", "safe_field": "ok"},
        }
    )
    assert scrubbed == {"slug": "test", "nested": {"safe_field": "ok"}}
