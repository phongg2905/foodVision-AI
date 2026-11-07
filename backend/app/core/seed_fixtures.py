"""Canonical baseline seed fixtures for InMemoryCatalogRepository (testing & dev fallback)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.database import IngredientRecord, RecipeRecord

ING_CA_CHUA = "11111111-1111-4111-8111-111111111101"
ING_TRUNG_GA = "11111111-1111-4111-8111-111111111102"
ING_DAU_HU = "11111111-1111-4111-8111-111111111103"
ING_THIT_BA_CHI = "11111111-1111-4111-8111-111111111104"
ING_HANH_LA = "11111111-1111-4111-8111-111111111105"
ING_MUOI = "11111111-1111-4111-8111-111111111106"
ING_NUOC_MAM = "11111111-1111-4111-8111-111111111107"
ING_DAU_AN = "11111111-1111-4111-8111-111111111108"
ING_DUONG = "11111111-1111-4111-8111-111111111109"
ING_TIEU_XAY = "11111111-1111-4111-8111-111111111110"
ING_INACTIVE = "11111111-1111-4111-8111-111111111199"

REC_DAU_HU_SOT_CA = "22222222-2222-4222-8222-222222222201"
REC_CANH_CA_CHUA_TRUNG = "22222222-2222-4222-8222-222222222202"
REC_THIT_KHO_TRUNG = "22222222-2222-4222-8222-222222222203"
REC_TRUNG_XAO_CA_CHUA = "22222222-2222-4222-8222-222222222204"
REC_DRAFT = "22222222-2222-4222-8222-222222222299"


def build_default_seed_ingredients() -> list[IngredientRecord]:
    from app.core.database import IngredientRecord

    return [
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111101",
            slug="ca-chua",
            name_vi="Cà chua",
            category="vegetable",
            is_active=True,
            aliases=["cà chua đỏ", "tomato"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111102",
            slug="trung-ga",
            name_vi="Trứng gà",
            category="protein",
            is_active=True,
            aliases=["trứng", "hột gà"],
            allergen_ids=["egg"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111103",
            slug="dau-hu",
            name_vi="Đậu hũ",
            category="protein",
            is_active=True,
            aliases=["đậu phụ", "tàu hũ", "đậu khuôn"],
            allergen_ids=["soy"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111104",
            slug="thit-ba-chi",
            name_vi="Thịt ba chỉ",
            category="protein",
            is_active=True,
            aliases=["thịt ba rọi", "thịt heo ba chỉ"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111105",
            slug="hanh-la",
            name_vi="Hành lá",
            category="spice",
            is_active=True,
            aliases=["hành hoa"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111106",
            slug="muoi",
            name_vi="Muối",
            category="pantry",
            is_active=True,
            aliases=["muối ăn", "muối tinh"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111107",
            slug="nuoc-mam",
            name_vi="Nước mắm",
            category="pantry",
            is_active=True,
            aliases=["nước mắm truyền thống"],
            allergen_ids=["fish"],
        ),
        IngredientRecord(
            id="11111111-1111-4111-8111-111111111108",
            slug="dau-an",
            name_vi="Dầu ăn",
            category="pantry",
            is_active=True,
            aliases=["dầu thực vật"],
        ),
        IngredientRecord(
            id=ING_DUONG,
            slug="duong",
            name_vi="Đường",
            category="pantry",
            is_active=True,
            aliases=["đường cát", "đường trắng"],
        ),
        IngredientRecord(
            id=ING_TIEU_XAY,
            slug="tieu-xay",
            name_vi="Tiêu xay",
            category="pantry",
            is_active=True,
            aliases=["hạt tiêu", "tiêu đen"],
        ),
        IngredientRecord(
            id=ING_INACTIVE,
            slug="nguyen-lieu-ngung-dung",
            name_vi="Nguyên liệu ngưng dùng",
            category="other",
            is_active=False,
            aliases=[],
        ),
    ]


def build_default_seed_recipes() -> list[RecipeRecord]:
    from app.core.database import (
        NutritionEvidenceRecord,
        RecipeIngredientRecord,
        RecipeRecord,
        RecipeStepRecord,
    )

    return [
        RecipeRecord(
            id="22222222-2222-4222-8222-222222222201",
            slug="dau-hu-sot-ca-chua",
            name_vi="Đậu hũ sốt cà chua",
            cuisine_code="VN",
            prep_minutes=10,
            cook_minutes=15,
            status="published",
            description="Món đậu hũ sốt cà chua thanh đạm, đưa cơm.",
            country_code="VN",
            cooking_method="braise",
            required_equipment=["pan", "stove"],
            base_servings=2,
            quality_score=0.95,
            source_name="FoodVision Editorial",
            source_url="https://foodvision.local/recipes/dau-hu-sot-ca-chua",
            content_license="CC-BY-4.0",
            allergen_ids=["soy"],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111103",
                    name_vi="Đậu hũ",
                    category="protein",
                    is_required=True,
                    role="essential",
                    weight=1.0,
                    grams=200.0,
                    display_quantity="2 bìa",
                    sort_order=1,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111101",
                    name_vi="Cà chua",
                    category="vegetable",
                    is_required=True,
                    role="essential",
                    weight=0.9,
                    grams=150.0,
                    display_quantity="2 quả",
                    sort_order=2,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111105",
                    name_vi="Hành lá",
                    category="spice",
                    is_required=False,
                    role="garnish",
                    weight=0.2,
                    grams=15.0,
                    display_quantity="2 nhánh",
                    sort_order=3,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111106",
                    name_vi="Muối",
                    category="pantry",
                    is_required=True,
                    role="seasoning",
                    weight=0.1,
                    grams=5.0,
                    display_quantity="1 muỗng cà phê",
                    sort_order=4,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111108",
                    name_vi="Dầu ăn",
                    category="pantry",
                    is_required=True,
                    role="seasoning",
                    weight=0.1,
                    grams=15.0,
                    display_quantity="1 muỗng canh",
                    sort_order=5,
                ),
            ],
            steps=[
                RecipeStepRecord(
                    step_no=1,
                    instruction="Cắt đậu hũ thành miếng vuông vừa ăn, chiên vàng đều các mặt.",
                    estimated_minutes=7,
                ),
                RecipeStepRecord(
                    step_no=2,
                    instruction="Băm nhỏ cà chua, xào nhừ với muối rồi cho đậu hũ vào rim 8 phút.",
                    estimated_minutes=8,
                ),
            ],
            nutrition_evidence=[
                NutritionEvidenceRecord(
                    tag_id="33333333-3333-4333-8333-333333333301",
                    tag_code="HIGH_PROTEIN_PLANT",
                    tag_name_vi="Giàu đạm thực vật",
                    tag_description="Cung cấp protein thực vật lành mạnh từ đậu nành.",
                    tag_is_active=True,
                    source_urls=["https://fdc.nal.usda.gov/"],
                    note="Đậu hũ và cà chua cung cấp lycopene và đạm thực vật.",
                )
            ],
        ),
        RecipeRecord(
            id="22222222-2222-4222-8222-222222222202",
            slug="canh-ca-chua-trung",
            name_vi="Canh cà chua trứng",
            cuisine_code="VN",
            prep_minutes=5,
            cook_minutes=10,
            status="published",
            description="Canh trứng cà chua thanh mát nấu nhanh trong 15 phút.",
            country_code="VN",
            cooking_method="boil",
            required_equipment=["pot", "stove"],
            base_servings=2,
            quality_score=0.92,
            allergen_ids=["egg"],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111101",
                    name_vi="Cà chua",
                    category="vegetable",
                    is_required=True,
                    role="essential",
                    weight=0.9,
                    grams=150.0,
                    display_quantity="2 quả",
                    sort_order=1,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111102",
                    name_vi="Trứng gà",
                    category="protein",
                    is_required=True,
                    role="essential",
                    weight=1.0,
                    grams=100.0,
                    display_quantity="2 quả",
                    sort_order=2,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111106",
                    name_vi="Muối",
                    category="pantry",
                    is_required=True,
                    role="seasoning",
                    weight=0.1,
                    grams=5.0,
                    display_quantity="1 muỗng cà phê",
                    sort_order=3,
                ),
            ],
            steps=[
                RecipeStepRecord(
                    step_no=1,
                    instruction="Xào cà chua với chút muối rồi thêm 500ml nước đun sôi.",
                    estimated_minutes=5,
                ),
                RecipeStepRecord(
                    step_no=2,
                    instruction="Đánh tan trứng gà, đổ từ từ vào nồi nước sôi và khuấy nhẹ tạo vân mây.",
                    estimated_minutes=5,
                ),
            ],
        ),
        RecipeRecord(
            id="22222222-2222-4222-8222-222222222203",
            slug="thit-kho-trung",
            name_vi="Thịt kho trứng",
            cuisine_code="VN",
            prep_minutes=15,
            cook_minutes=45,
            status="published",
            description="Thịt ba chỉ kho trứng gà đậm đà truyền thống.",
            country_code="VN",
            cooking_method="braise",
            required_equipment=["pot", "stove"],
            base_servings=4,
            quality_score=0.96,
            allergen_ids=["egg", "fish"],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111104",
                    name_vi="Thịt ba chỉ",
                    category="protein",
                    is_required=True,
                    role="essential",
                    weight=1.0,
                    grams=300.0,
                    display_quantity="300g",
                    sort_order=1,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111102",
                    name_vi="Trứng gà",
                    category="protein",
                    is_required=True,
                    role="essential",
                    weight=0.8,
                    grams=150.0,
                    display_quantity="3 quả",
                    sort_order=2,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111107",
                    name_vi="Nước mắm",
                    category="pantry",
                    is_required=True,
                    role="seasoning",
                    weight=0.2,
                    grams=30.0,
                    display_quantity="2 muỗng canh",
                    sort_order=3,
                ),
            ],
            steps=[
                RecipeStepRecord(
                    step_no=1,
                    instruction="Ướp thịt ba chỉ với nước mắm trong 15 phút.",
                    estimated_minutes=15,
                ),
                RecipeStepRecord(
                    step_no=2,
                    instruction="Kho thịt và trứng đã luộc trên lửa nhỏ trong 45 phút đến khi mềm.",
                    estimated_minutes=45,
                ),
            ],
        ),
        RecipeRecord(
            id="22222222-2222-4222-8222-222222222204",
            slug="trung-xao-ca-chua",
            name_vi="Trứng xào cà chua",
            cuisine_code="VN",
            prep_minutes=5,
            cook_minutes=8,
            status="published",
            description="Trứng gà xào cà chua mềm mọng hoàn thành trong 13 phút.",
            country_code="VN",
            cooking_method="stir_fry",
            required_equipment=["pan", "stove"],
            base_servings=2,
            quality_score=1.0,
            allergen_ids=["egg", "fish"],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111101",
                    name_vi="Cà chua",
                    category="vegetable",
                    is_required=True,
                    role="primary",
                    weight=4.0,
                    grams=150.0,
                    display_quantity="2 quả",
                    sort_order=1,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111102",
                    name_vi="Trứng gà",
                    category="protein",
                    is_required=True,
                    role="essential",
                    weight=3.0,
                    grams=100.0,
                    display_quantity="2 quả",
                    sort_order=2,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111105",
                    name_vi="Hành lá",
                    category="spice",
                    is_required=False,
                    role="secondary",
                    weight=1.0,
                    grams=15.0,
                    display_quantity="2 nhánh",
                    sort_order=3,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111108",
                    name_vi="Dầu ăn",
                    category="pantry",
                    is_required=True,
                    role="secondary",
                    weight=1.0,
                    grams=15.0,
                    display_quantity="1 muỗng canh",
                    sort_order=4,
                ),
                RecipeIngredientRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111107",
                    name_vi="Nước mắm",
                    category="pantry",
                    is_required=True,
                    role="secondary",
                    weight=1.0,
                    grams=10.0,
                    display_quantity="1 muỗng canh",
                    sort_order=5,
                ),
            ],
            steps=[
                RecipeStepRecord(
                    step_no=1,
                    instruction="Phi thơm hành, xào chín mềm cà chua với chút nước mắm.",
                    estimated_minutes=5,
                ),
                RecipeStepRecord(
                    step_no=2,
                    instruction="Đổ trứng gà đã đánh tan vào đảo đều trên lửa vừa rồi rắc hành lá.",
                    estimated_minutes=8,
                ),
            ],
        ),
        RecipeRecord(
            id="22222222-2222-4222-8222-222222222299",
            slug="mon-nhap-chua-duyet",
            name_vi="Món nháp chưa duyệt",
            cuisine_code="VN",
            prep_minutes=10,
            cook_minutes=10,
            status="draft",
            ingredients=[],
            steps=[],
        ),
    ]
