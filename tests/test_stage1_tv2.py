"""Stage 1 Automated Verification Suite for TV2 (Phong Phạm).

Covers:
- Card #6 (`[GĐ1 - TP03, TP13]`):
  - Supabase PostgreSQL >= 15 DDL & RLS migrations (`20261104000001_initial_schema.sql`, `20261104000002_rls_and_grants.sql`)
  - PgBouncer DSN sanitization (`sanitize_psycopg_dsn`)
  - Vietnamese normalization (`norm_vi`) & 4-tier trigram search (`TP 13`)
  - FastAPI endpoints: `GET /api/v1/health` (`OPS-01`), `GET /api/v1/ingredients` (`TC-10`, `NFR-03`),
    `GET /api/v1/recipes` (`TC-01`, `TC-03`), `GET /api/v1/recipes/{id}` (`TC-02`, `TC-04`)
- Card #8 (`[GĐ1 - TP04]`):
  - Open-World 3-Valued Ingredient State Validation (`TC-11`: `422 INVALID_INGREDIENTS` on pantry/main mismatch)
  - 4-Group Recipe Reasoning (`BLOCKED`, `READY`, `UNKNOWN`, `MISSING_CONFIRMED` -> `"ready"` / `"missing"`, `TC-13`)
  - Hard Constraints (`published`, `C > 0`, `cuisine_codes`, `max_total_minutes`, `DietOK`, `EquipOK`)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure `backend` is on sys.path so `from app....` imports resolve cleanly
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import (  # noqa: E402
    InMemoryCatalogRepository,
    get_catalog_repo,
    sanitize_psycopg_dsn,
)
from app.core.errors import AppError  # noqa: E402
from app.main import create_app  # noqa: E402
from app.schemas.reasoning import ReasoningInput  # noqa: E402
from app.services.reasoning import (  # noqa: E402
    evaluate_recipe_reasoning,
    filter_candidate_recipes,
    validate_and_resolve_ingredients,
)
from app.services.vietnamese_search import (  # noqa: E402
    norm_vi,
    rank_ingredient_candidates,
    trigram_similarity,
)

# Deterministic seed UUIDs from InMemoryCatalogRepository
ING_CA_CHUA = "11111111-1111-4111-8111-111111111101"
ING_TRUNG_GA = "11111111-1111-4111-8111-111111111102"
ING_DAU_HU = "11111111-1111-4111-8111-111111111103"
ING_THIT_BA_CHI = "11111111-1111-4111-8111-111111111104"
ING_HANH_LA = "11111111-1111-4111-8111-111111111105"
ING_MUOI = "11111111-1111-4111-8111-111111111106"  # pantry
ING_NUOC_MAM = "11111111-1111-4111-8111-111111111107"  # pantry
ING_DAU_AN = "11111111-1111-4111-8111-111111111108"  # pantry

REC_DAU_HU_SOT_CA = "22222222-2222-4222-8222-222222222201"  # published
REC_CANH_CA_CHUA_TRUNG = "22222222-2222-4222-8222-222222222202"  # published
REC_THIT_KHO_TRUNG = "22222222-2222-4222-8222-222222222203"  # published
REC_DRAFT = "22222222-2222-4222-8222-222222222299"  # draft


@pytest.fixture()
def repo() -> InMemoryCatalogRepository:
    return InMemoryCatalogRepository()


@pytest.fixture()
def client(repo: InMemoryCatalogRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_catalog_repo] = lambda: repo
    return TestClient(app)


# ==============================================================================
# 1. TP 03 — Migration SQL & Supabase Pooler Verification
# ==============================================================================


def test_supabase_migration_files_contain_all_required_schema_objects() -> None:
    schema_sql = (
        REPO_ROOT / "supabase" / "migrations" / "20261104000001_initial_schema.sql"
    ).read_text(encoding="utf-8")
    rls_sql = (
        REPO_ROOT / "supabase" / "migrations" / "20261104000002_rls_and_grants.sql"
    ).read_text(encoding="utf-8")

    # PostgreSQL >= 15 check & extensions
    assert "server_version_num" in schema_sql
    assert "150000" in schema_sql
    assert "CREATE EXTENSION IF NOT EXISTS unaccent" in schema_sql
    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in schema_sql
    assert "CREATE OR REPLACE FUNCTION public.norm_vi(input_text text)" in schema_sql

    # 16 Core tables + 4 Extended tables = 20 tables
    expected_tables = [
        "profiles",
        "ingredients",
        "ingredient_aliases",
        "ai_models",
        "ai_labels",
        "recipes",
        "recipe_ingredients",
        "recipe_steps",
        "nutrition_tags",
        "ingredient_nutrition_tags",
        "scan_sessions",
        "scan_detections",
        "scan_ingredients",
        "favorites",
        "recommendation_feedback",
        "audit_logs",
        "allergens",
        "ingredient_allergens",
        "ingredient_nutrients",
        "user_preferences",
    ]
    for tbl in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS public.{tbl}" in schema_sql
        assert f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY" in rls_sql

    # View, Partial Unique Index, NULLS NOT DISTINCT, Atomic RPC
    assert "CREATE OR REPLACE VIEW public.recipe_allergens" in schema_sql
    assert "idx_ai_models_single_active" in schema_sql
    assert "UNIQUE NULLS NOT DISTINCT" in schema_sql
    assert "CREATE OR REPLACE FUNCTION public.activate_ai_model" in schema_sql

    # Storage bucket `scan-images`
    assert "scan-images" in rls_sql


def test_sanitize_psycopg_dsn_strips_pgbouncer_param() -> None:
    raw = "postgresql://postgres.aqjeztwtqkhvjjxnsijs:secret@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true"
    cleaned = sanitize_psycopg_dsn(raw)
    assert "pgbouncer" not in cleaned
    assert cleaned.startswith("postgresql://postgres.aqjeztwtqkhvjjxnsijs:secret@")
    assert cleaned.endswith(":6543/postgres")


# ==============================================================================
# 2. TP 13 — Vietnamese Normalization (`norm_vi`) & 4-Tier Trigram Search
# ==============================================================================


def test_norm_vi_removes_diacritics_and_normalizes_d_bar() -> None:
    assert norm_vi("Đậu hũ / Đậu phụ") == "dau hu / dau phu"
    assert norm_vi("  Cà   Chua  ") == "ca chua"
    assert norm_vi("Nước mắm Phú Quốc") == "nuoc mam phu quoc"


def test_vietnamese_search_4_tier_ranking_and_alias_matching(
    repo: InMemoryCatalogRepository,
) -> None:
    # Exact/Alias match on "dau phu" -> returns "Đậu hũ" via alias
    items, total = repo.list_active_ingredients(q="dau phu")
    assert total >= 1
    assert items[0].id == ING_DAU_HU
    assert items[0].name_vi == "Đậu hũ"

    # Unaccented search on "ca chua" -> returns "Cà chua" first
    items_cc, total_cc = repo.list_active_ingredients(q="ca chua")
    assert total_cc >= 1
    assert items_cc[0].id == ING_CA_CHUA

    # Typo tolerance via pg_trgm similarity ("ca chuaa")
    sim = trigram_similarity("Cà chua", "ca chuaa")
    assert sim >= 0.30
    ranked = rank_ingredient_candidates("ca chuaa", items_cc, threshold=0.30)
    assert len(ranked) == 1
    assert ranked[0][1] == 3  # Tier 3 trigram match


# ==============================================================================
# 3. TP 03 & TP 13 — FastAPI Endpoints (`health`, `ingredients`, `recipes`)
# ==============================================================================


def test_health_endpoint_returns_ok_and_request_id(client: TestClient) -> None:
    res = client.get("/api/v1/health", headers={"X-Request-Id": "req-test-001"})
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert res.headers.get("X-Request-Id") == "req-test-001"


def test_ingredients_endpoint_contradiction_returns_422_tc10(client: TestClient) -> None:
    """TC-10: category=pantry & exclude_pantry=true must return 422 INVALID_QUERY_PARAMS."""
    res = client.get("/api/v1/ingredients?category=pantry&exclude_pantry=true")
    assert res.status_code == 422
    payload = res.json()
    assert payload["code"] == "INVALID_QUERY_PARAMS"


def test_ingredients_endpoint_cache_control_and_exclude_pantry(client: TestClient) -> None:
    # Without `q`, Cache-Control header is set (`NFR-03`)
    res = client.get("/api/v1/ingredients?exclude_pantry=true")
    assert res.status_code == 200
    assert res.headers.get("Cache-Control") == "public, max-age=300"
    data = res.json()
    assert all(item["category"] != "pantry" for item in data["items"])


def test_recipes_list_and_detail_endpoints_tc01_to_tc04(client: TestClient) -> None:
    # TC-01: Search published recipes by unaccented keyword "dau hu"
    res = client.get("/api/v1/recipes?q=dau hu")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == REC_DAU_HU_SOT_CA

    # TC-03: Filter by max_total_minutes=15 -> only Canh cà chua trứng (15m)
    res_fast = client.get("/api/v1/recipes?max_total_minutes=15")
    assert res_fast.status_code == 200
    fast_ids = {item["id"] for item in res_fast.json()["items"]}
    assert REC_CANH_CA_CHUA_TRUNG in fast_ids
    assert REC_THIT_KHO_TRUNG not in fast_ids

    # TC-02: Get published recipe detail
    res_detail = client.get(f"/api/v1/recipes/{REC_DAU_HU_SOT_CA}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["name_vi"] == "Đậu hũ sốt cà chua"
    assert len(detail["ingredients"]) >= 3
    assert len(detail["steps"]) >= 2

    # TC-04: Draft recipe or non-existent UUID returns 404 RECIPE_NOT_FOUND
    res_draft = client.get(f"/api/v1/recipes/{REC_DRAFT}")
    assert res_draft.status_code == 404
    assert res_draft.json()["code"] == "RECIPE_NOT_FOUND"


# ==============================================================================
# 4. TP 04 — Open-World 3-Valued Reasoning & Hard Constraints (`TC-11`, `TC-13`)
# ==============================================================================


def test_validate_and_resolve_ingredients_rejects_pantry_mismatch_tc11(
    repo: InMemoryCatalogRepository,
) -> None:
    """TC-11: Passing a pantry UUID in `ingredient_ids` or a main UUID in `excluded_pantry_ids` raises 422 INVALID_INGREDIENTS."""
    # Case 1: Pantry ingredient (`ING_MUOI`) passed in `ingredient_ids`
    with pytest.raises(AppError) as exc_info:
        validate_and_resolve_ingredients(
            repo=repo,
            ingredient_ids=[ING_CA_CHUA, ING_MUOI],
            excluded_pantry_ids=[],
        )
    err = exc_info.value
    assert err.status_code == 422
    assert err.code == "INVALID_INGREDIENTS"
    assert ING_MUOI in err.details["invalid_ingredient_ids"]

    # Case 2: Main ingredient (`ING_CA_CHUA`) passed in `excluded_pantry_ids`
    with pytest.raises(AppError) as exc_info_2:
        validate_and_resolve_ingredients(
            repo=repo,
            ingredient_ids=[ING_DAU_HU],
            excluded_pantry_ids=[ING_CA_CHUA],
        )
    err2 = exc_info_2.value
    assert err2.status_code == 422
    assert err2.code == "INVALID_INGREDIENTS"
    assert ING_CA_CHUA in err2.details["invalid_ingredient_ids"]


def test_open_world_3_state_reasoning_groups_and_hard_constraints_tc13(
    repo: InMemoryCatalogRepository,
) -> None:
    """TC-13: Verify Open-World 3-Valued classification (`READY`, `UNKNOWN`, `MISSING_CONFIRMED`, `BLOCKED`)."""
    active_pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    dau_hu_recipe = repo.get_published_recipe_by_id(REC_DAU_HU_SOT_CA)
    assert dau_hu_recipe is not None

    # Scenario A: User has BOTH Cà chua & Đậu hũ, no excluded pantry -> Đậu hũ sốt cà chua is READY ("ready")
    eval_ready = evaluate_recipe_reasoning(
        recipe=dau_hu_recipe,
        params=ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_DAU_HU],
            excluded_pantry_ids=[],
        ),
        active_pantry_ids=active_pantry_ids,
    )
    assert eval_ready.status_v1_1 == "READY"
    assert eval_ready.availability_v1_0 == "ready"
    assert len(eval_ready.matched_main_ids) == 2
    assert len(eval_ready.missing_required_ingredient_ids) == 0

    # Scenario B: User only has Cà chua (Đậu hũ is unknown) -> Đậu hũ sốt cà chua is UNKNOWN ("missing")
    eval_unknown = evaluate_recipe_reasoning(
        recipe=dau_hu_recipe,
        params=ReasoningInput(
            ingredient_ids=[ING_CA_CHUA],
            excluded_pantry_ids=[],
        ),
        active_pantry_ids=active_pantry_ids,
    )
    assert eval_unknown.status_v1_1 == "UNKNOWN"
    assert eval_unknown.availability_v1_0 == "missing"
    assert eval_unknown.missing_required_main_ids == [ING_DAU_HU]
    assert eval_unknown.ingredient_states[ING_DAU_HU] == "unknown"

    # Scenario C: User has Cà chua & Đậu hũ, but explicitly excludes Muối (`ING_MUOI` in X) -> MISSING_CONFIRMED ("missing")
    eval_missing_pantry = evaluate_recipe_reasoning(
        recipe=dau_hu_recipe,
        params=ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_DAU_HU],
            excluded_pantry_ids=[ING_MUOI],
        ),
        active_pantry_ids=active_pantry_ids,
    )
    assert eval_missing_pantry.status_v1_1 == "MISSING_CONFIRMED"
    assert eval_missing_pantry.availability_v1_0 == "missing"
    assert ING_MUOI in eval_missing_pantry.missing_pantry_ids
    assert eval_missing_pantry.ingredient_states[ING_MUOI] == "confirmed_missing"

    # Scenario D: Filter candidate recipes with allergy & dietary constraints
    # User has Cà chua & Trứng gà, allergic to `egg` -> Canh cà chua trứng & Thịt kho trứng are BLOCKED, only Đậu hũ sốt cà chua remains!
    candidates = filter_candidate_recipes(
        repo=repo,
        params=ReasoningInput(
            ingredient_ids=[ING_CA_CHUA, ING_TRUNG_GA],
            excluded_pantry_ids=[],
            excluded_allergen_ids=["egg"],
        ),
    )
    candidate_ids = [rec.id for rec, _ev in candidates]
    assert candidate_ids == [REC_DAU_HU_SOT_CA]
