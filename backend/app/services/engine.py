"""
FoodVision AI - Core Business Logic Services:
1. Weighted Recipe Recommendation Engine (Content-Based)
2. Qualitative Nutrient Lookup Service (Evidence-Based with Source Attribution)
"""
from typing import List, Dict, Any

NUTRITION_DISCLAIMER = (
    "Thông tin dinh dưỡng chỉ mang tính định tính tham khảo từ thành phần nguyên liệu của công thức, "
    "không phải phép đo khối lượng hay ước tính năng lượng (kcal/gram) trực tiếp từ hình ảnh."
)


def compute_recipe_recommendations(
    confirmed_ingredient_ids: List[int],
    recipes: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Tính điểm phù hợp nguyên liệu theo công thức có trọng số:
    Score(I, R) = 100 * sum(w(r) for r in I ∩ R) / sum(w(r) for r in R_required)
    """
    user_set = set(confirmed_ingredient_ids)
    ranked = []

    for recipe in recipes:
        req_items = [item for item in recipe.get("ingredients", []) if not item.get("is_optional", False)]
        opt_items = [item for item in recipe.get("ingredients", []) if item.get("is_optional", False)]

        if not req_items:
            continue

        total_weight = sum(item.get("importance", 2) for item in req_items)
        matched_weight = 0
        matched_list = []
        missing_list = []

        for item in req_items:
            ing_id = item["ingredient_id"]
            if ing_id in user_set:
                matched_weight += item.get("importance", 2)
                matched_list.append(item)
            else:
                missing_list.append(item)

        if matched_weight == 0:
            continue

        score = round((matched_weight / total_weight) * 100.0, 1)
        optional_missing = [item for item in opt_items if item["ingredient_id"] not in user_set]

        ranked.append({
            "recipe_id": recipe["id"],
            "name": recipe["name"],
            "description": recipe.get("description", ""),
            "cooking_time": recipe.get("cooking_time", 20),
            "score": score,
            "matched_count": len(matched_list),
            "required_count": len(req_items),
            "matched_ingredients": matched_list,
            "missing_ingredients": missing_list,
            "optional_missing": optional_missing,
        })

    # Sắp xếp giảm dần theo điểm -> ưu tiên ít nguyên liệu thiếu hơn -> thời gian nấu nhanh hơn
    ranked.sort(
        key=lambda x: (-x["score"], len(x["missing_ingredients"]), x["cooking_time"])
    )
    return ranked[:top_k]


def aggregate_recipe_nutrients(
    recipe: Dict[str, Any],
    ingredient_nutrient_rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tổng hợp danh sách chất dinh dưỡng định tính không trùng lặp từ các nguyên liệu của món ăn.
    Đảm bảo 5 quy tắc kiểm thử dinh dưỡng (Mục 8.5):
    - Gộp chất trùng giữa nhiều nguyên liệu (ví dụ 2 nguyên liệu cùng chứa Vitamin C hoặc Protein)
    - Nêu rõ nguyên liệu làm căn cứ và nguồn tham khảo
    - Báo rõ các nguyên liệu chưa có hồ sơ dinh dưỡng ('chưa có thông tin'), không tự suy đoán
    """
    recipe_ingredients = recipe.get("ingredients", [])
    mapped_ing_ids = set()
    aggregated: Dict[int, Dict[str, Any]] = {}

    for row in ingredient_nutrient_rows:
        ing_id = row["ingredient_id"]
        mapped_ing_ids.add(ing_id)
        nutr_id = row["nutrient_id"]

        if nutr_id not in aggregated:
            aggregated[nutr_id] = {
                "nutrient_id": nutr_id,
                "code": row["nutrient_code"],
                "name": row["nutrient_name"],
                "nutrient_group": row["nutrient_group"],
                "display_statement": f"Có thể cung cấp {row['nutrient_name']}",
                "derived_from_ingredients": []
            }

        aggregated[nutr_id]["derived_from_ingredients"].append({
            "ingredient_id": ing_id,
            "ingredient_name": row["ingredient_name"],
            "food_form": row.get("food_form", "sống/tươi"),
            "source_title": row["source_title"],
            "source_publisher": row["source_publisher"],
            "source_reference": row["source_reference"],
        })

    unmapped_ingredients = []
    for item in recipe_ingredients:
        if item["ingredient_id"] not in mapped_ing_ids:
            unmapped_ingredients.append({
                "ingredient_id": item["ingredient_id"],
                "ingredient_name": item["name"],
                "status": "Chưa có dữ liệu dinh dưỡng đáng tin cậy trong hệ thống"
            })

    return {
        "recipe_id": recipe["id"],
        "recipe_name": recipe["name"],
        "disclaimer": NUTRITION_DISCLAIMER,
        "nutrients": list(aggregated.values()),
        "unmapped_ingredients": unmapped_ingredients
    }

