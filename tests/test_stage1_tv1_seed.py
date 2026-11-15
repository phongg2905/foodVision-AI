"""Stage 1 Automated Verification Suite for TV1 (Minh Thanh — Card #7 Seed Data).

Validates `supabase/seed.sql` against:
- Card #7 (`[GD1 - TP03, TP10]`):
  1. >= 20 main non-pantry ingredients aligned 1-to-1 with `class_index (0..19)` in `docs/04-ai-model/label-catalog.md` + VN/EU/US culinary extras.
  2. Exact 5 pantry spices (`category = 'pantry'`: Muoi, Duong, Nuoc mam, Dau an, Hat tieu) with NO water record (`BR-04`, `BR-12`, `ADR-008`) + regional synonyms in `ingredient_aliases`.
  3. Published sample recipes across all 3 cuisines (`VN`, `EU`, `US`) satisfying all 4 `BR-01` conditions, including canonical benchmark dishes `"Cà chua nhồi thịt sốt trứng"` and `"Trứng xào cà chua"` (`MATH-01..07`, `S=89.0` / `S=68.1`).
  4. Tier-1 qualitative `nutrition_tags` + `ingredient_nutrition_tags` and Tier-2 USDA per-100g `ingredient_nutrients` with valid `https://` `source_url` (`BR-03`, `ADR-004`).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import (  # noqa: E402
    IngredientRecord,
    InMemoryCatalogRepository,
    RecipeIngredientRecord,
    RecipeRecord,
    RecipeStepRecord,
)
from app.schemas.reasoning import ReasoningInput  # noqa: E402
from app.services.reasoning import (  # noqa: E402
    evaluate_recipe_reasoning,
    validate_and_resolve_ingredients,
)
from app.services.vietnamese_search import norm_vi  # noqa: E402

SEED_SQL_PATH = REPO_ROOT / "supabase" / "seed.sql"

EXPECTED_YOLO_CLASSES: dict[int, tuple[str, str]] = {
    0: ("tomato", "ca-chua"),
    1: ("egg", "trung-ga"),
    2: ("potato", "khoai-tay"),
    3: ("carrot", "ca-rot"),
    4: ("onion", "hanh-tay"),
    5: ("garlic", "toi"),
    6: ("chili_pepper", "ot"),
    7: ("cucumber", "dua-leo"),
    8: ("cabbage", "bap-cai"),
    9: ("broccoli", "bong-cai-xanh"),
    10: ("mushroom", "nam"),
    11: ("tofu", "dau-hu"),
    12: ("raw_chicken", "thit-ga-song"),
    13: ("raw_pork", "thit-heo-song"),
    14: ("raw_shrimp", "tom"),
    15: ("whole_fish", "ca-nguyen-con"),
    16: ("ginger", "gung"),
    17: ("scallion", "hanh-la"),
    18: ("bell_pepper", "ot-chuong"),
    19: ("sweet_corn", "bap-ngot"),
}


# THUẬT TOÁN: Trích xuất khối câu lệnh INSERT INTO public.<table> ... ON CONFLICT/SEMICOLON
# từ tệp SQL chuẩn để kiểm tra ràng buộc toàn vẹn khóa ngoại và miền giá trị độc lập.
def _extract_insert_block(sql_text: str, table_name: str) -> str:
    pattern = re.compile(
        rf"INSERT INTO public\.{re.escape(table_name)}\b(.*?)ON CONFLICT",
        re.DOTALL,
    )
    match = pattern.search(sql_text)
    assert match is not None, f"Missing INSERT block for public.{table_name}"
    return match.group(1)


# THUẬT TOÁN: Phân tích các bộ giá trị nguyên liệu trong seed.sql thành bảng ánh xạ UUID
# phục vụ đối chiếu chéo với ai_labels, ingredient_nutrients và recipe_ingredients.
def _parse_seed_ingredients(sql_text: str) -> dict[str, dict[str, str]]:
    block = _extract_insert_block(sql_text, "ingredients")
    row_pattern = re.compile(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*(true|false)\s*\)"
    )
    parsed: dict[str, dict[str, str]] = {}
    for m in row_pattern.finditer(block):
        ing_id, slug, name_vi, category, fdc_id, is_active = m.groups()
        parsed[ing_id] = {
            "id": ing_id,
            "slug": slug,
            "name_vi": name_vi,
            "category": category,
            "fdc_id": fdc_id,
            "is_active": is_active,
        }
    return parsed


def test_seed_sql_exists_and_is_transactional_idempotent() -> None:
    assert SEED_SQL_PATH.exists(), "supabase/seed.sql must exist"
    sql_text = SEED_SQL_PATH.read_text(encoding="utf-8")
    assert "BEGIN;" in sql_text and "COMMIT;" in sql_text
    assert "ON CONFLICT" in sql_text
    assert "[YOUR-PASSWORD]" not in sql_text


def test_seed_ingredients_cover_20_yolo_classes_and_exact_5_pantry_items() -> None:
    sql_text = SEED_SQL_PATH.read_text(encoding="utf-8")
    ingredients = _parse_seed_ingredients(sql_text)

    non_pantry = [i for i in ingredients.values() if i["category"] != "pantry"]
    pantry = [i for i in ingredients.values() if i["category"] == "pantry"]

    assert len(non_pantry) >= 25
    assert len(pantry) == 5
    pantry_slugs = {p["slug"] for p in pantry}
    assert pantry_slugs == {"muoi", "duong", "nuoc-mam", "dau-an", "hat-tieu"}

    # Strictly forbid water in ingredients / pantry (BR-04, ADR-008)
    for item in ingredients.values():
        assert item["slug"] not in {"nuoc", "nuoc-loc", "water"}
        assert norm_vi(item["name_vi"]) not in {"nuoc", "nuoc loc"}

    # Verify all 20 YOLO classes (0..19) map to active non-pantry ingredients (BR-12)
    labels_block = _extract_insert_block(sql_text, "ai_labels")
    label_rows = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*(\d+)\s*,\s*'([^']+)'\s*,\s*'([0-9a-f-]{36})'\s*\)",
        labels_block,
    )
    assert len(label_rows) == 20
    seen_indices: set[int] = set()
    for _model_id, idx_str, class_name, ing_id in label_rows:
        idx = int(idx_str)
        seen_indices.add(idx)
        expected_name, expected_slug = EXPECTED_YOLO_CLASSES[idx]
        assert class_name == expected_name
        assert ing_id in ingredients
        assert ingredients[ing_id]["slug"] == expected_slug
        assert ingredients[ing_id]["category"] != "pantry"
        assert ingredients[ing_id]["is_active"] == "true"
    assert seen_indices == set(range(20))


def test_seed_regional_aliases_and_two_tier_usda_nutrition_have_valid_sources() -> None:
    sql_text = SEED_SQL_PATH.read_text(encoding="utf-8")
    ingredients = _parse_seed_ingredients(sql_text)

    aliases_block = _extract_insert_block(sql_text, "ingredient_aliases")
    alias_pairs = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*'([^']+)'\s*,\s*public\.norm_vi\('([^']+)'\)\s*,\s*'(vi|en)'\s*\)",
        aliases_block,
    )
    assert len(alias_pairs) >= 30
    alias_texts = {alias for _iid, alias, _norm, _loc in alias_pairs}
    for required_synonym in ("đậu phụ", "tàu hũ", "ngô ngọt", "dưa chuột", "thịt lợn", "súp lơ xanh"):
        assert required_synonym in alias_texts

    # Verify Tier-1 qualitative nutrition tags & source URLs
    ing_tag_block = _extract_insert_block(sql_text, "ingredient_nutrition_tags")
    ing_tag_urls = re.findall(r"'(https://[^']+)'", ing_tag_block)
    assert len(ing_tag_urls) >= 8
    assert all(url.startswith("https://fdc.nal.usda.gov/") for url in ing_tag_urls)

    # Verify Tier-2 USDA per-100g nutrients & MATH-07 reference values
    nutr_block = _extract_insert_block(sql_text, "ingredient_nutrients")
    nutr_rows = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*'(https://[^']+)'",
        nutr_block,
    )
    assert len(nutr_rows) == len(ingredients)
    nutr_by_id = {row[0]: (float(row[1]), row[5]) for row in nutr_rows}
    # MATH-07: 100g tomato (18 kcal) + 60g egg (144 * 0.6 = 86.4 kcal) = 104.4 kcal
    tomato_kcal = nutr_by_id["11111111-1111-4111-8111-111111111101"][0]
    egg_kcal = nutr_by_id["11111111-1111-4111-8111-111111111102"][0]
    assert round(tomato_kcal * 1.0 + egg_kcal * 0.6, 1) == 104.4


def test_seed_recipes_satisfy_br01_across_vn_eu_us_and_reasoning_engine() -> None:
    sql_text = SEED_SQL_PATH.read_text(encoding="utf-8")
    ingredients = _parse_seed_ingredients(sql_text)

    recipes_block = _extract_insert_block(sql_text, "recipes")
    recipe_rows = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'(VN|EU|US)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*ARRAY\[([^\]]*)\]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
        recipes_block,
    )
    assert len(recipe_rows) >= 6
    cuisines = {r[4] for r in recipe_rows}
    assert cuisines == {"VN", "EU", "US"}
    recipe_names = {r[2] for r in recipe_rows}
    assert "Cà chua nhồi thịt sốt trứng" in recipe_names
    assert "Trứng xào cà chua" in recipe_names

    rec_ing_block = _extract_insert_block(sql_text, "recipe_ingredients")
    rec_ing_rows = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*'([0-9a-f-]{36})'\s*,\s*(true|false)\s*,\s*'(primary|essential|secondary)'\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*'([^']+)'\s*,\s*(\d+)\s*\)",
        rec_ing_block,
    )
    steps_block = _extract_insert_block(sql_text, "recipe_steps")
    step_rows = re.findall(
        r"\(\s*'([0-9a-f-]{36})'\s*,\s*(\d+)\s*,\s*'([^']+)'\s*,\s*(\d+)\s*\)",
        steps_block,
    )

    # Verify BR-01 & BR-05 on every seeded recipe and run Stage 1 Reasoning Engine
    ing_records = [
        IngredientRecord(
            id=v["id"],
            slug=v["slug"],
            name_vi=v["name_vi"],
            category=v["category"],
            is_active=(v["is_active"] == "true"),
            fdc_id=v["fdc_id"],
        )
        for v in ingredients.values()
    ]
    rec_records: list[RecipeRecord] = []
    for rid, slug, name_vi, desc, cuisine, country, method, _eq, servings, prep, cook in recipe_rows:
        total_min = int(prep) + int(cook)
        r_ings = [
            RecipeIngredientRecord(
                ingredient_id=iid,
                name_vi=ingredients[iid]["name_vi"],
                category=ingredients[iid]["category"],
                is_required=(req == "true"),
                role=role,
                weight=float(w),
                grams=float(g),
                display_quantity=qty,
                sort_order=int(order),
            )
            for r_id, iid, req, role, w, g, qty, order in rec_ing_rows
            if r_id == rid
        ]
        r_steps = [
            RecipeStepRecord(step_no=int(sno), instruction=inst, estimated_minutes=int(est))
            for r_id, sno, inst, est in step_rows
            if r_id == rid
        ]
        assert any(ri.is_required and ri.category != "pantry" for ri in r_ings)
        assert len(r_steps) >= 1
        assert all((st.estimated_minutes or 0) <= total_min for st in r_steps)
        rec_records.append(
            RecipeRecord(
                id=rid,
                slug=slug,
                name_vi=name_vi,
                cuisine_code=cuisine,
                country_code=country,
                cooking_method=method,
                base_servings=int(servings),
                prep_minutes=int(prep),
                cook_minutes=int(cook),
                description=desc,
                ingredients=r_ings,
                steps=r_steps,
            )
        )

    repo = InMemoryCatalogRepository(ingredients=ing_records, recipes=rec_records)
    dedup_main, dedup_pantry, _found = validate_and_resolve_ingredients(
        repo=repo,
        ingredient_ids=[
            "11111111-1111-4111-8111-111111111101",  # Cà chua
            "11111111-1111-4111-8111-111111111213",  # Thịt heo sống
            "11111111-1111-4111-8111-111111111102",  # Trứng gà
        ],
        excluded_pantry_ids=[],
    )
    target = next(r for r in rec_records if r.slug == "ca-chua-nhoi-thit-sot-trung")
    outcome = evaluate_recipe_reasoning(
        recipe=target,
        params=ReasoningInput(ingredient_ids=dedup_main, excluded_pantry_ids=dedup_pantry),
        active_pantry_ids=set(repo.get_active_pantry_ingredients().keys()),
    )
    assert outcome.status_v1_1 == "READY"
    assert outcome.availability_v1_0 == "ready"
    assert outcome.missing_required_ingredient_ids == []

    # Excluding Nước mắm flips availability from "ready" -> "missing" (TC-14 / DEF-05)
    outcome_missing_pantry = evaluate_recipe_reasoning(
        recipe=target,
        params=ReasoningInput(
            ingredient_ids=dedup_main,
            excluded_pantry_ids=["11111111-1111-4111-8111-111111111107"],
        ),
        active_pantry_ids=set(repo.get_active_pantry_ingredients().keys()),
    )
    assert outcome_missing_pantry.status_v1_1 == "MISSING_CONFIRMED"
    assert outcome_missing_pantry.availability_v1_0 == "missing"
    assert outcome_missing_pantry.missing_required_ingredient_ids == [
        "11111111-1111-4111-8111-111111111107"
    ]
