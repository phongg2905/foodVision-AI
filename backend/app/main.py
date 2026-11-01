"""
FoodVision AI - FastAPI Backend Entrypoint (6 Endpoints MVP)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import time

from app.services.engine import compute_recipe_recommendations, aggregate_recipe_nutrients

app = FastAPI(
    title="FoodVision AI API",
    description="API Nhận diện nguyên liệu (YOLO), Khuyến nghị món ăn (Weighted Matching) & Tra cứu dinh dưỡng định tính có nguồn.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


class RecommendationRequest(BaseModel):
    session_id: Optional[str] = None
    confirmed_ingredient_ids: List[int]


class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    recipe_id: int
    rating: int
    comment: Optional[str] = None


# Danh mục mẫu dùng khi chưa kết nối trực tiếp Supabase (phục vụ phát triển song song Tuần 1)
SAMPLE_INGREDIENTS = [
    {"id": 1, "name": "Cà chua", "normalized_name": "ca_chua", "yolo_class": "tomato"},
    {"id": 2, "name": "Cà rốt", "normalized_name": "ca_rot", "yolo_class": "carrot"},
    {"id": 3, "name": "Khoai tây", "normalized_name": "khoai_tay", "yolo_class": "potato"},
    {"id": 4, "name": "Hành tây", "normalized_name": "hanh_tay", "yolo_class": "onion"},
    {"id": 5, "name": "Dưa leo", "normalized_name": "dua_leo", "yolo_class": "cucumber"},
    {"id": 6, "name": "Trứng gà (nguyên vỏ)", "normalized_name": "trung_ga", "yolo_class": "egg"},
    {"id": 7, "name": "Bắp cải", "normalized_name": "bap_cai", "yolo_class": "cabbage"},
    {"id": 8, "name": "Ớt chuông", "normalized_name": "ot_chuong", "yolo_class": "bell_pepper"},
    {"id": 9, "name": "Bí đỏ", "normalized_name": "bi_do", "yolo_class": "pumpkin"},
    {"id": 10, "name": "Tỏi", "normalized_name": "toi", "yolo_class": "garlic"},
    {"id": 11, "name": "Hành lá", "normalized_name": "hanh_la", "yolo_class": "green_onion"},
    {"id": 12, "name": "Chanh", "normalized_name": "chanh", "yolo_class": "lemon"},
]

SAMPLE_RECIPES = [
    {
        "id": 1,
        "name": "Trứng xào cà chua (Canh trứng cà chua)",
        "description": "Món ăn gia đình nhanh gọn, kết hợp vị chua dịu của cà chua và vị béo mềm của trứng gà.",
        "cooking_time": 10,
        "instructions": "1. Đập trứng ra bát, đánh tan.\n2. Cà chua rửa sạch, bổ múi cau.\n3. Xào mềm cà chua, đổ trứng vào đảo đều đến khi chín tới, rắc hành lá.",
        "ingredients": [
            {"ingredient_id": 6, "name": "Trứng gà (nguyên vỏ)", "amount": "2", "unit": "quả", "importance": 3, "is_optional": False},
            {"ingredient_id": 1, "name": "Cà chua", "amount": "2", "unit": "quả", "importance": 3, "is_optional": False},
            {"ingredient_id": 11, "name": "Hành lá", "amount": "2", "unit": "nhánh", "importance": 1, "is_optional": True},
        ]
    },
    {
        "id": 2,
        "name": "Trứng chiên hành tây",
        "description": "Trứng chiên vàng ươm dậy mùi thơm ngọt tự nhiên từ hành tây cắt lát.",
        "cooking_time": 10,
        "instructions": "1. Hành tây thái lát mỏng.\n2. Đánh tan trứng gà.\n3. Xào sơ hành tây rồi đổ trứng vào chiên vàng đều hai mặt.",
        "ingredients": [
            {"ingredient_id": 6, "name": "Trứng gà (nguyên vỏ)", "amount": "3", "unit": "quả", "importance": 3, "is_optional": False},
            {"ingredient_id": 4, "name": "Hành tây", "amount": "1/2", "unit": "củ", "importance": 3, "is_optional": False},
            {"ingredient_id": 11, "name": "Hành lá", "amount": "1", "unit": "nhánh", "importance": 1, "is_optional": True},
        ]
    },
    {
        "id": 3,
        "name": "Canh cà rốt khoai tây",
        "description": "Món canh thanh ngọt tự nhiên từ củ quả.",
        "cooking_time": 25,
        "instructions": "1. Khoai tây, cà rốt gọt vỏ, cắt miếng vừa ăn.\n2. Hầm cà rốt và khoai tây đến khi chín mềm, rắc hành lá.",
        "ingredients": [
            {"ingredient_id": 2, "name": "Cà rốt", "amount": "1", "unit": "củ", "importance": 3, "is_optional": False},
            {"ingredient_id": 3, "name": "Khoai tây", "amount": "2", "unit": "củ", "importance": 3, "is_optional": False},
            {"ingredient_id": 11, "name": "Hành lá", "amount": "2", "unit": "nhánh", "importance": 1, "is_optional": True},
        ]
    }
]

SAMPLE_NUTRIENT_MAPPINGS = [
    {
        "ingredient_id": 6, "ingredient_name": "Trứng gà (nguyên vỏ)",
        "nutrient_id": 1, "nutrient_code": "PROTEIN", "nutrient_name": "Protein (Chất đạm)", "nutrient_group": "Chất đa lượng",
        "food_form": "trứng gà nguyên quả",
        "source_title": "Bảng thành phần thực phẩm Việt Nam", "source_publisher": "Viện Dinh dưỡng Quốc gia - Bộ Y tế", "source_reference": "https://viendinhduong.vn"
    },
    {
        "ingredient_id": 6, "ingredient_name": "Trứng gà (nguyên vỏ)",
        "nutrient_id": 2, "nutrient_code": "LIPID", "nutrient_name": "Chất béo (Lipid)", "nutrient_group": "Chất đa lượng",
        "food_form": "trứng gà nguyên quả",
        "source_title": "Bảng thành phần thực phẩm Việt Nam", "source_publisher": "Viện Dinh dưỡng Quốc gia - Bộ Y tế", "source_reference": "https://viendinhduong.vn"
    },
    {
        "ingredient_id": 6, "ingredient_name": "Trứng gà (nguyên vỏ)",
        "nutrient_id": 7, "nutrient_code": "VIT_B12", "nutrient_name": "Vitamin B12", "nutrient_group": "Vitamin",
        "food_form": "trứng gà nguyên quả",
        "source_title": "USDA FoodData Central", "source_publisher": "U.S. Department of Agriculture", "source_reference": "https://fdc.nal.usda.gov"
    },
    {
        "ingredient_id": 1, "ingredient_name": "Cà chua",
        "nutrient_id": 6, "nutrient_code": "VIT_C", "nutrient_name": "Vitamin C", "nutrient_group": "Vitamin",
        "food_form": "quả tươi",
        "source_title": "Bảng thành phần thực phẩm Việt Nam", "source_publisher": "Viện Dinh dưỡng Quốc gia - Bộ Y tế", "source_reference": "https://viendinhduong.vn"
    },
    {
        "ingredient_id": 1, "ingredient_name": "Cà chua",
        "nutrient_id": 8, "nutrient_code": "POTASSIUM", "nutrient_name": "Kali (Potassium)", "nutrient_group": "Khoáng chất",
        "food_form": "quả tươi",
        "source_title": "USDA FoodData Central", "source_publisher": "U.S. Department of Agriculture", "source_reference": "https://fdc.nal.usda.gov"
    },
    {
        "ingredient_id": 1, "ingredient_name": "Cà chua",
        "nutrient_id": 4, "nutrient_code": "FIBER", "nutrient_name": "Chất xơ", "nutrient_group": "Chất xơ",
        "food_form": "quả tươi",
        "source_title": "Bảng thành phần thực phẩm Việt Nam", "source_publisher": "Viện Dinh dưỡng Quốc gia - Bộ Y tế", "source_reference": "https://viendinhduong.vn"
    },
    {
        "ingredient_id": 11, "ingredient_name": "Hành lá",
        "nutrient_id": 6, "nutrient_code": "VIT_C", "nutrient_name": "Vitamin C", "nutrient_group": "Vitamin",
        "food_form": "lá tươi",
        "source_title": "Bảng thành phần thực phẩm Việt Nam", "source_publisher": "Viện Dinh dưỡng Quốc gia - Bộ Y tế", "source_reference": "https://viendinhduong.vn"
    }
]


@app.get("/api/ingredients")
def get_ingredients():
    """FR-04: Lấy danh mục nguyên liệu chuẩn."""
    return {"ingredients": SAMPLE_INGREDIENTS}


@app.post("/api/inference")
async def run_inference(file: UploadFile = File(...)):
    """FR-01 & FR-02: Kiểm tra ảnh đầu vào và trả về kết quả phát hiện nguyên liệu."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Định dạng tệp không hỗ trợ. Vui lòng tải ảnh JPG hoặc PNG hợp lệ."
        )
    start_ts = time.time()
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Tệp ảnh rỗng hoặc bị hỏng.")

    # Mock / Placeholder YOLO inference (sẽ thay bằng model YOLO thật ở Tuần 2)
    elapsed_ms = int((time.time() - start_ts) * 1000) + 45
    return {
        "session_id": str(uuid.uuid4()),
        "model_version": "yolov8n-foodvision-v1",
        "processing_time_ms": elapsed_ms,
        "detections": [
            {"ingredient_id": 1, "yolo_class": "tomato", "name": "Cà chua", "confidence": 0.91, "bbox": [110, 80, 250, 215]},
            {"ingredient_id": 6, "yolo_class": "egg", "name": "Trứng gà (nguyên vỏ)", "confidence": 0.89, "bbox": [290, 105, 390, 220]},
        ]
    }


@app.post("/api/recommendations")
def get_recommendations(payload: RecommendationRequest):
    """FR-05 & FR-06: Tính điểm phù hợp và trả về Top 5 món ăn."""
    if not payload.confirmed_ingredient_ids:
        raise HTTPException(
            status_code=400,
            detail="Danh sách nguyên liệu xác nhận đang trống. Vui lòng chọn ít nhất 1 nguyên liệu."
        )
    top_recipes = compute_recipe_recommendations(
        confirmed_ingredient_ids=payload.confirmed_ingredient_ids,
        recipes=SAMPLE_RECIPES,
        top_k=5
    )
    return {"top_recipes": top_recipes}


@app.get("/api/recipes/{recipe_id}")
def get_recipe_detail(recipe_id: int):
    """FR-07: Xem chi tiết công thức và hướng dẫn nấu."""
    recipe = next((r for r in SAMPLE_RECIPES if r["id"] == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Không tìm thấy công thức món ăn.")
    return recipe


@app.get("/api/recipes/{recipe_id}/nutrients")
def get_recipe_nutrients(recipe_id: int):
    """FR-10 & FR-11: Tra cứu thành phần dinh dưỡng định tính có nguồn theo công thức món ăn."""
    recipe = next((r for r in SAMPLE_RECIPES if r["id"] == recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Không tìm thấy công thức món ăn.")

    recipe_ing_ids = {item["ingredient_id"] for item in recipe.get("ingredients", [])}
    relevant_rows = [row for row in SAMPLE_NUTRIENT_MAPPINGS if row["ingredient_id"] in recipe_ing_ids]

    return aggregate_recipe_nutrients(recipe=recipe, ingredient_nutrient_rows=relevant_rows)


@app.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest):
    """FR-12 (Bổ sung): Lưu phản hồi về gợi ý món ăn."""
    return {"status": "recorded", "recipe_id": payload.recipe_id, "rating": payload.rating}

