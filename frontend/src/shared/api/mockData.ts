import {
  Ingredient,
  RecipeDetail,
  RecipeSummary,
} from './types';

/**
 * Danh mục 5 gia vị sẵn có trong bếp (category = 'pantry') đồng bộ 1-1 với backend/app/core/seed_fixtures.py & supabase/seed.sql:
 * Muối, Nước mắm, Dầu ăn, Đường, Tiêu xay (BR-04 & ADR-008).
 */
export const MOCK_PANTRY_INGREDIENTS: Ingredient[] = [
  {
    "id": "11111111-1111-4111-8111-111111111106",
    "slug": "muoi",
    "name_vi": "Muối",
    "category": "pantry",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111107",
    "slug": "nuoc-mam",
    "name_vi": "Nước mắm",
    "category": "pantry",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111108",
    "slug": "dau-an",
    "name_vi": "Dầu ăn",
    "category": "pantry",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111109",
    "slug": "duong",
    "name_vi": "Đường",
    "category": "pantry",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111110",
    "slug": "tieu-xay",
    "name_vi": "Tiêu xay",
    "category": "pantry",
    "is_active": true
  }
];

/**
 * Danh mục 36 nguyên liệu chính chuẩn (category != 'pantry') đồng bộ 1-1 UUID & slug với Backend.
 */
export const MOCK_MAIN_INGREDIENTS: Ingredient[] = [
  {
    "id": "11111111-1111-4111-8111-111111111101",
    "slug": "ca-chua",
    "name_vi": "Cà chua",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111102",
    "slug": "trung-ga",
    "name_vi": "Trứng gà",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111103",
    "slug": "dau-hu",
    "name_vi": "Đậu hũ",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111104",
    "slug": "thit-ba-chi",
    "name_vi": "Thịt ba chỉ",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111105",
    "slug": "hanh-la",
    "name_vi": "Hành lá",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111202",
    "slug": "khoai-tay",
    "name_vi": "Khoai tây",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111203",
    "slug": "ca-rot",
    "name_vi": "Cà rốt",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111204",
    "slug": "hanh-tay",
    "name_vi": "Hành tây",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111205",
    "slug": "toi",
    "name_vi": "Tỏi",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111206",
    "slug": "ot",
    "name_vi": "Ớt",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111207",
    "slug": "dua-leo",
    "name_vi": "Dưa leo",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111208",
    "slug": "bap-cai",
    "name_vi": "Bắp cải",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111209",
    "slug": "bong-cai-xanh",
    "name_vi": "Bông cải xanh",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111210",
    "slug": "nam",
    "name_vi": "Nấm",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111212",
    "slug": "thit-ga-song",
    "name_vi": "Thịt gà sống",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111213",
    "slug": "thit-heo-song",
    "name_vi": "Thịt heo sống",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111214",
    "slug": "tom",
    "name_vi": "Tôm tươi",
    "category": "seafood",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111215",
    "slug": "ca-nguyen-con",
    "name_vi": "Cá nguyên con",
    "category": "seafood",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111216",
    "slug": "gung",
    "name_vi": "Gừng",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111218",
    "slug": "ot-chuong",
    "name_vi": "Ớt chuông",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111219",
    "slug": "bap-ngot",
    "name_vi": "Bắp ngọt",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111301",
    "slug": "thit-bo",
    "name_vi": "Thịt bò",
    "category": "protein",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111302",
    "slug": "mi-y",
    "name_vi": "Mì Ý",
    "category": "other",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111303",
    "slug": "bo-lat",
    "name_vi": "Bơ lạt",
    "category": "other",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111304",
    "slug": "pho-mai-cheddar",
    "name_vi": "Phô mai Cheddar",
    "category": "other",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111305",
    "slug": "banh-mi-burger",
    "name_vi": "Vỏ bánh Burger",
    "category": "other",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111306",
    "slug": "xa-lach",
    "name_vi": "Rau xà lách",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111307",
    "slug": "sa",
    "name_vi": "Sả",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111308",
    "slug": "nghe",
    "name_vi": "Nghệ tươi",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111309",
    "slug": "la-chanh",
    "name_vi": "Lá chanh",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111310",
    "slug": "hanh-tim",
    "name_vi": "Hành tím",
    "category": "spice",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111311",
    "slug": "chanh",
    "name_vi": "Chanh tươi",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111312",
    "slug": "rau-muong",
    "name_vi": "Rau muống",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111313",
    "slug": "cai-thia",
    "name_vi": "Cải thìa",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111314",
    "slug": "bi-do",
    "name_vi": "Bí đỏ",
    "category": "vegetable",
    "is_active": true
  },
  {
    "id": "11111111-1111-4111-8111-111111111315",
    "slug": "muc-tuoi",
    "name_vi": "Mực tươi",
    "category": "seafood",
    "is_active": true
  }
];

export const MOCK_ALL_INGREDIENTS: Ingredient[] = [
  ...MOCK_MAIN_INGREDIENTS,
  ...MOCK_PANTRY_INGREDIENTS,
];

/**
 * Danh sách 20 công thức món ăn chuẩn đồng bộ 1-1 UUID & slug với Backend & seed.sql.
 */
export const MOCK_RECIPES: RecipeSummary[] = [
  {
    "id": "22222222-2222-4222-8222-222222222201",
    "slug": "dau-hu-sot-ca-chua",
    "name_vi": "Đậu hũ sốt cà chua",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222202",
    "slug": "canh-ca-chua-trung",
    "name_vi": "Canh cà chua trứng",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222203",
    "slug": "thit-kho-trung",
    "name_vi": "Thịt kho trứng",
    "cuisine_code": "VN",
    "prep_minutes": 15,
    "cook_minutes": 45,
    "total_minutes": 60,
    "cover_image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222204",
    "slug": "trung-xao-ca-chua",
    "name_vi": "Trứng xào cà chua",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222205",
    "slug": "mi-y-sot-ca-chua-thit-bam",
    "name_vi": "Mì Ý sốt cà chua thịt băm",
    "cuisine_code": "EU",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222206",
    "slug": "bong-cai-xanh-nam-ap-chao-bo-toi",
    "name_vi": "Bông cải xanh và nấm áp chảo bơ tỏi",
    "cuisine_code": "EU",
    "prep_minutes": 5,
    "cook_minutes": 8,
    "total_minutes": 13,
    "cover_image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222207",
    "slug": "burger-bo-pho-mai-kieu-my",
    "name_vi": "Burger bò phô mai kiểu Mỹ",
    "cuisine_code": "US",
    "prep_minutes": 10,
    "cook_minutes": 12,
    "total_minutes": 22,
    "cover_image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222208",
    "slug": "bap-ngot-khoai-tay-dut-lo-bo-toi",
    "name_vi": "Bắp ngọt và khoai tây đút lò bơ tỏi",
    "cuisine_code": "US",
    "prep_minutes": 10,
    "cook_minutes": 25,
    "total_minutes": 35,
    "cover_image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222209",
    "slug": "ga-hap-sa",
    "name_vi": "Gà hấp sả",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222210",
    "slug": "ga-kho-sa-nghe",
    "name_vi": "Gà kho sả nghệ",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 25,
    "total_minutes": 35,
    "cover_image_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222211",
    "slug": "ga-xao-sa-ot",
    "name_vi": "Gà xào sả ớt",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 12,
    "total_minutes": 22,
    "cover_image_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222212",
    "slug": "tom-rang-hanh-toi",
    "name_vi": "Tôm rang hành tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 8,
    "cook_minutes": 10,
    "total_minutes": 18,
    "cover_image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222213",
    "slug": "ca-kho-gung",
    "name_vi": "Cá kho gừng",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 30,
    "total_minutes": 40,
    "cover_image_url": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222214",
    "slug": "thit-heo-ham-khoai-tay-ca-rot",
    "name_vi": "Thịt heo hầm khoai tây cà rốt",
    "cuisine_code": "VN",
    "prep_minutes": 15,
    "cook_minutes": 30,
    "total_minutes": 45,
    "cover_image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222215",
    "slug": "bo-xao-bong-cai-xanh-nam",
    "name_vi": "Thịt bò xào bông cải xanh nấm",
    "cuisine_code": "VN",
    "prep_minutes": 8,
    "cook_minutes": 10,
    "total_minutes": 18,
    "cover_image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222216",
    "slug": "bap-cai-xao-nam-toi",
    "name_vi": "Bắp cải xào nấm tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 6,
    "cook_minutes": 8,
    "total_minutes": 14,
    "cover_image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222217",
    "slug": "dua-leo-tron-toi-ot",
    "name_vi": "Dưa leo trộn tỏi ớt",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 0,
    "total_minutes": 10,
    "cover_image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222218",
    "slug": "bo-xao-ot-chuong-hanh-tay",
    "name_vi": "Thịt bò xào ớt chuông hành tây kiểu Âu",
    "cuisine_code": "EU",
    "prep_minutes": 8,
    "cook_minutes": 12,
    "total_minutes": 20,
    "cover_image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222219",
    "slug": "bap-ngot-ap-chao-bo-toi-kieu-my",
    "name_vi": "Bắp ngọt áp chảo bơ tỏi kiểu Mỹ",
    "cuisine_code": "US",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80"
  },
  {
    "id": "22222222-2222-4222-8222-222222222220",
    "slug": "rau-muong-xao-toi",
    "name_vi": "Rau muống xào tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 7,
    "total_minutes": 12,
    "cover_image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80"
  }
];

export type MockIngredientRole = 'core' | 'secondary' | 'spice' | 'optional';
export type MockDishRole = 'main' | 'sub';

export interface MockRecipeScoringMeta {
  cookingMethod: string;
  rolesByIngredientId: Record<
    string,
    {
      role: MockIngredientRole;
      dishRole: MockDishRole;
      weight: number;
    }
  >;
}

export const MOCK_RECIPE_SCORING_META: Record<string, MockRecipeScoringMeta> = {
  "22222222-2222-4222-8222-222222222201": {
    "cookingMethod": "braise",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111103": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111101": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222202": {
    "cookingMethod": "boil",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111101": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111102": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222203": {
    "cookingMethod": "braise",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111104": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111102": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222204": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111101": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111102": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222205": {
    "cookingMethod": "simmer",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111302": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111301": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111101": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222206": {
    "cookingMethod": "pan_sear",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111209": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111210": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111303": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222207": {
    "cookingMethod": "grill",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111305": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111301": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111304": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111306": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111101": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222208": {
    "cookingMethod": "bake",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111219": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111202": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111303": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222209": {
    "cookingMethod": "steam",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111212": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111307": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111309": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111216": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222210": {
    "cookingMethod": "braise",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111212": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111307": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111308": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111109": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222211": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111212": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111307": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111206": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222212": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111214": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111109": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222213": {
    "cookingMethod": "braise",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111215": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111216": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111206": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111109": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222214": {
    "cookingMethod": "simmer",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111213": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111202": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111203": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111204": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222215": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111301": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111209": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111210": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222216": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111208": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111210": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222217": {
    "cookingMethod": "mix",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111207": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111206": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111311": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111109": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222218": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111301": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111218": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111204": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111303": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222219": {
    "cookingMethod": "pan_sear",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111219": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111303": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111105": {
        "role": "optional",
        "dishRole": "sub",
        "weight": 0
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111110": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  },
  "22222222-2222-4222-8222-222222222220": {
    "cookingMethod": "stir_fry",
    "rolesByIngredientId": {
      "11111111-1111-4111-8111-111111111312": {
        "role": "core",
        "dishRole": "main",
        "weight": 4
      },
      "11111111-1111-4111-8111-111111111205": {
        "role": "secondary",
        "dishRole": "sub",
        "weight": 2
      },
      "11111111-1111-4111-8111-111111111108": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111106": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      },
      "11111111-1111-4111-8111-111111111107": {
        "role": "spice",
        "dishRole": "sub",
        "weight": 1
      }
    }
  }
};

export const MOCK_RECIPE_DETAILS: Record<string, RecipeDetail> = {
  "22222222-2222-4222-8222-222222222201": {
    "id": "22222222-2222-4222-8222-222222222201",
    "slug": "dau-hu-sot-ca-chua",
    "name_vi": "Đậu hũ sốt cà chua",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
    "description": "Món đậu hũ sốt cà chua thanh đạm, đưa cơm.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111103",
        "name_vi": "Đậu hũ",
        "category": "protein",
        "is_required": true,
        "grams": 200,
        "display_quantity": "2 bìa",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111101",
        "name_vi": "Cà chua",
        "category": "vegetable",
        "is_required": true,
        "grams": 150,
        "display_quantity": "2 quả",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": false,
        "grams": 15,
        "display_quantity": "2 nhánh",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 5,
        "display_quantity": "1 muỗng cà phê",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Cắt đậu hũ thành miếng vuông vừa ăn, chiên vàng đều các mặt.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Băm nhỏ cà chua, xào nhừ với muối rồi cho đậu hũ vào rim 20 phút.",
        "estimated_minutes": 20
      }
    ],
    "nutrition_evidence": [
      {
        "tag": {
          "id": "33333333-3333-4333-8333-333333333301",
          "code": "HIGH_PROTEIN_PLANT",
          "name_vi": "Giàu đạm thực vật",
          "description": "Cung cấp protein thực vật lành mạnh từ đậu nành.",
          "is_active": true
        },
        "source_urls": [
          "https://fdc.nal.usda.gov/"
        ],
        "note": "Đậu hũ và cà chua cung cấp lycopene và đạm thực vật."
      }
    ],
    "usda_nutrition": {
      "kcal": 316.4,
      "protein_g": 17.75,
      "fat_g": 24.89,
      "carb_g": 10.68,
      "source_urls": [
        "https://fdc.nal.usda.gov/food-details/172475/nutrients",
        "https://fdc.nal.usda.gov/food-details/170457/nutrients",
        "https://fdc.nal.usda.gov/food-details/170005/nutrients",
        "https://fdc.nal.usda.gov/food-details/173468/nutrients",
        "https://fdc.nal.usda.gov/food-details/171028/nutrients"
      ],
      "scaling_factor": 1,
      "scaling_warning_vi": null
    },
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/dau-hu-sot-ca-chua",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222202": {
    "id": "22222222-2222-4222-8222-222222222202",
    "slug": "canh-ca-chua-trung",
    "name_vi": "Canh cà chua trứng",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80",
    "description": "Canh trứng cà chua thanh mát nấu nhanh trong 15 phút.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111101",
        "name_vi": "Cà chua",
        "category": "vegetable",
        "is_required": true,
        "grams": 150,
        "display_quantity": "2 quả",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111102",
        "name_vi": "Trứng gà",
        "category": "protein",
        "is_required": true,
        "grams": 100,
        "display_quantity": "2 quả",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 5,
        "display_quantity": "1 muỗng cà phê",
        "sort_order": 3
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Xào cà chua với chút muối rồi thêm 500ml nước đun sôi.",
        "estimated_minutes": 5
      },
      {
        "step_no": 2,
        "instruction": "Đánh tan trứng gà, đổ từ từ vào nồi nước sôi và khuấy nhẹ tạo vân mây.",
        "estimated_minutes": 5
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": {
      "kcal": 171,
      "protein_g": 13.88,
      "fat_g": 9.81,
      "carb_g": 6.55,
      "source_urls": [
        "https://fdc.nal.usda.gov/food-details/170457/nutrients",
        "https://fdc.nal.usda.gov/food-details/171287/nutrients",
        "https://fdc.nal.usda.gov/food-details/173468/nutrients"
      ],
      "scaling_factor": 1,
      "scaling_warning_vi": null
    },
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": null,
    "source_url": null,
    "content_license": null
  },
  "22222222-2222-4222-8222-222222222203": {
    "id": "22222222-2222-4222-8222-222222222203",
    "slug": "thit-kho-trung",
    "name_vi": "Thịt kho trứng",
    "cuisine_code": "VN",
    "prep_minutes": 15,
    "cook_minutes": 45,
    "total_minutes": 60,
    "cover_image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt ba chỉ kho trứng gà đậm đà truyền thống.",
    "country_code": "VN",
    "base_servings": 4,
    "servings": 4,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111104",
        "name_vi": "Thịt ba chỉ",
        "category": "protein",
        "is_required": true,
        "grams": 300,
        "display_quantity": "300g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111102",
        "name_vi": "Trứng gà",
        "category": "protein",
        "is_required": true,
        "grams": 150,
        "display_quantity": "3 quả",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 30,
        "display_quantity": "2 muỗng canh",
        "sort_order": 3
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Ướp thịt ba chỉ với nước mắm trong 15 phút.",
        "estimated_minutes": 15
      },
      {
        "step_no": 2,
        "instruction": "Kho thịt và trứng đã luộc trên lửa nhỏ trong 45 phút đến khi mềm.",
        "estimated_minutes": 45
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": {
      "kcal": 1780.5,
      "protein_g": 48.38,
      "fat_g": 173.3,
      "carb_g": 2.17,
      "source_urls": [
        "https://fdc.nal.usda.gov/food-details/167814/nutrients",
        "https://fdc.nal.usda.gov/food-details/171287/nutrients",
        "https://fdc.nal.usda.gov/food-details/172235/nutrients"
      ],
      "scaling_factor": 1,
      "scaling_warning_vi": null
    },
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": null,
    "source_url": null,
    "content_license": null
  },
  "22222222-2222-4222-8222-222222222204": {
    "id": "22222222-2222-4222-8222-222222222204",
    "slug": "trung-xao-ca-chua",
    "name_vi": "Trứng xào cà chua",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=800&q=80",
    "description": "Trứng gà xào cà chua mềm mọng hoàn thành trong 15 phút.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111101",
        "name_vi": "Cà chua",
        "category": "vegetable",
        "is_required": true,
        "grams": 150,
        "display_quantity": "2 quả",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111102",
        "name_vi": "Trứng gà",
        "category": "protein",
        "is_required": true,
        "grams": 100,
        "display_quantity": "2 quả",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": false,
        "grams": 15,
        "display_quantity": "2 nhánh",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "1 muỗng canh",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Phi thơm hành, xào chín mềm cà chua với chút nước mắm.",
        "estimated_minutes": 5
      },
      {
        "step_no": 2,
        "instruction": "Đổ trứng gà đã đánh tan vào đảo đều trên lửa vừa rồi rắc hành lá.",
        "estimated_minutes": 10
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": {
      "kcal": 311.9,
      "protein_g": 14.66,
      "fat_g": 24.84,
      "carb_g": 8.02,
      "source_urls": [
        "https://fdc.nal.usda.gov/food-details/170457/nutrients",
        "https://fdc.nal.usda.gov/food-details/171287/nutrients",
        "https://fdc.nal.usda.gov/food-details/170005/nutrients",
        "https://fdc.nal.usda.gov/food-details/171028/nutrients",
        "https://fdc.nal.usda.gov/food-details/172235/nutrients"
      ],
      "scaling_factor": 1,
      "scaling_warning_vi": null
    },
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": null,
    "source_url": null,
    "content_license": null
  },
  "22222222-2222-4222-8222-222222222205": {
    "id": "22222222-2222-4222-8222-222222222205",
    "slug": "mi-y-sot-ca-chua-thit-bam",
    "name_vi": "Mì Ý sốt cà chua thịt băm",
    "cuisine_code": "EU",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80",
    "description": "Mì Spaghetti sốt cà chua thịt bò băm đậm vị kiểu Âu.",
    "country_code": "IT",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111302",
        "name_vi": "Mì Ý",
        "category": "other",
        "is_required": true,
        "grams": 200,
        "display_quantity": "200g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111301",
        "name_vi": "Thịt bò",
        "category": "protein",
        "is_required": true,
        "grams": 150,
        "display_quantity": "150g",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111101",
        "name_vi": "Cà chua",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "2 quả",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": false,
        "grams": 10,
        "display_quantity": "3 tép",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 4,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Luộc mì Ý trong nước sôi có pha chút muối cho vừa chín tới rồi để ráo.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm tỏi với dầu ăn, xào săn thịt bò băm rồi cho cà chua băm nhuyễn vào nấu sánh sốt.",
        "estimated_minutes": 15
      },
      {
        "step_no": 3,
        "instruction": "Trộn mì Ý với sốt cà chua thịt băm nóng và thưởng thức.",
        "estimated_minutes": 5
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/mi-y-sot-ca-chua-thit-bam",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222206": {
    "id": "22222222-2222-4222-8222-222222222206",
    "slug": "bong-cai-xanh-nam-ap-chao-bo-toi",
    "name_vi": "Bông cải xanh và nấm áp chảo bơ tỏi",
    "cuisine_code": "EU",
    "prep_minutes": 5,
    "cook_minutes": 8,
    "total_minutes": 13,
    "cover_image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
    "description": "Món rau củ kiểu Âu nhanh gọn trong 13 phút dậy mùi bơ tỏi.",
    "country_code": "FR",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111209",
        "name_vi": "Bông cải xanh",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "200g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111210",
        "name_vi": "Nấm",
        "category": "vegetable",
        "is_required": true,
        "grams": 120,
        "display_quantity": "120g",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111303",
        "name_vi": "Bơ lạt",
        "category": "other",
        "is_required": true,
        "grams": 20,
        "display_quantity": "20g",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "3 tép",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Rửa sạch bông cải xanh và nấm, cắt miếng vừa ăn để ráo.",
        "estimated_minutes": 5
      },
      {
        "step_no": 2,
        "instruction": "Đun chảy bơ lạt với tỏi băm, áp chảo lửa vừa bông cải xanh và nấm cùng chút muối.",
        "estimated_minutes": 8
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bong-cai-xanh-nam-ap-chao-bo-toi",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222207": {
    "id": "22222222-2222-4222-8222-222222222207",
    "slug": "burger-bo-pho-mai-kieu-my",
    "name_vi": "Burger bò phô mai kiểu Mỹ",
    "cuisine_code": "US",
    "prep_minutes": 10,
    "cook_minutes": 12,
    "total_minutes": 22,
    "cover_image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
    "description": "Bánh burger nhân bò áp chảo kèm phô mai Cheddar, xà lách và cà chua tươi.",
    "country_code": "US",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111305",
        "name_vi": "Vỏ bánh Burger",
        "category": "other",
        "is_required": true,
        "grams": 120,
        "display_quantity": "2 vỏ bánh",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111301",
        "name_vi": "Thịt bò",
        "category": "protein",
        "is_required": true,
        "grams": 220,
        "display_quantity": "220g băm",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111304",
        "name_vi": "Phô mai Cheddar",
        "category": "other",
        "is_required": true,
        "grams": 40,
        "display_quantity": "2 lát",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111306",
        "name_vi": "Rau xà lách",
        "category": "vegetable",
        "is_required": false,
        "grams": 30,
        "display_quantity": "4 lá",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111101",
        "name_vi": "Cà chua",
        "category": "vegetable",
        "is_required": false,
        "grams": 60,
        "display_quantity": "4 lát",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 7
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Ướp thịt bò băm với muối, tiêu xay rồi nặn thành 2 miếng tròn dẹt.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Áp chảo thịt bò chín mọng, đặt phô mai Cheddar lên mặt cho tan chảy rồi kẹp vào vỏ bánh cùng xà lách và cà chua.",
        "estimated_minutes": 12
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/burger-bo-pho-mai-kieu-my",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222208": {
    "id": "22222222-2222-4222-8222-222222222208",
    "slug": "bap-ngot-khoai-tay-dut-lo-bo-toi",
    "name_vi": "Bắp ngọt và khoai tây đút lò bơ tỏi",
    "cuisine_code": "US",
    "prep_minutes": 10,
    "cook_minutes": 25,
    "total_minutes": 35,
    "cover_image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
    "description": "Khoai tây và bắp ngọt trộn bơ tỏi nướng vàng thơm lừng kiểu Mỹ.",
    "country_code": "US",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111219",
        "name_vi": "Bắp ngọt",
        "category": "vegetable",
        "is_required": true,
        "grams": 150,
        "display_quantity": "150g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111202",
        "name_vi": "Khoai tây",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "2 củ",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111303",
        "name_vi": "Bơ lạt",
        "category": "other",
        "is_required": true,
        "grams": 25,
        "display_quantity": "25g",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "3 tép",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Cắt khoai tây múi cau, tách hạt bắp ngọt và trộn đều với bơ lạt đun chảy, tỏi băm và muối.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Đút lò ở 200°C cho khoai tây chín bùi và vàng xém cạnh.",
        "estimated_minutes": 25
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bap-ngot-khoai-tay-dut-lo-bo-toi",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222209": {
    "id": "22222222-2222-4222-8222-222222222209",
    "slug": "ga-hap-sa",
    "name_vi": "Gà hấp sả",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 20,
    "total_minutes": 30,
    "cover_image_url": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt gà hấp cùng sả đập dập thơm thanh, giữ trọn vị ngọt tự nhiên.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111212",
        "name_vi": "Thịt gà sống",
        "category": "protein",
        "is_required": true,
        "grams": 350,
        "display_quantity": "350 g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111307",
        "name_vi": "Sả",
        "category": "spice",
        "is_required": true,
        "grams": 40,
        "display_quantity": "2 củ đập dập",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111309",
        "name_vi": "Lá chanh",
        "category": "spice",
        "is_required": false,
        "grams": 5,
        "display_quantity": "4 lá",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111216",
        "name_vi": "Gừng",
        "category": "spice",
        "is_required": false,
        "grams": 10,
        "display_quantity": "3 lát mỏng",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 4,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Xát muối rửa sạch thịt gà, ướp với chút muối và tiêu xay 10 phút; đập dập sả lót đáy nồi.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Đặt gà lên lớp sả, rắc lá chanh và gừng nếu có rồi hấp cách thủy lửa vừa 20 phút cho chín kỹ.",
        "estimated_minutes": 20
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/ga-hap-sa",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222210": {
    "id": "22222222-2222-4222-8222-222222222210",
    "slug": "ga-kho-sa-nghe",
    "name_vi": "Gà kho sả nghệ",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 25,
    "total_minutes": 35,
    "cover_image_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt gà kho đậm đà với sả băm và nghệ tươi vàng ươm đưa cơm.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111212",
        "name_vi": "Thịt gà sống",
        "category": "protein",
        "is_required": true,
        "grams": 350,
        "display_quantity": "350 g chặt miếng",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111307",
        "name_vi": "Sả",
        "category": "spice",
        "is_required": true,
        "grams": 30,
        "display_quantity": "2 củ băm nhỏ",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111308",
        "name_vi": "Nghệ tươi",
        "category": "spice",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 nhánh giã nhuyễn",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111109",
        "name_vi": "Đường",
        "category": "pantry",
        "is_required": true,
        "grams": 5,
        "display_quantity": "1 muỗng cà phê",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Ướp thịt gà chặt miếng cùng nghệ tươi giã nhuyễn, nửa phần sả băm, nước mắm và đường 10 phút.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm phần sả còn lại với dầu ăn, cho gà vào đảo săn rồi rim lửa nhỏ 25 phút đến khi sánh vị.",
        "estimated_minutes": 25
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/ga-kho-sa-nghe",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222211": {
    "id": "22222222-2222-4222-8222-222222222211",
    "slug": "ga-xao-sa-ot",
    "name_vi": "Gà xào sả ớt",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 12,
    "total_minutes": 22,
    "cover_image_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt gà xào sả ớt thơm nồng, cay ấm chuẩn cơm gia đình Việt.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111212",
        "name_vi": "Thịt gà sống",
        "category": "protein",
        "is_required": true,
        "grams": 300,
        "display_quantity": "300 g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111307",
        "name_vi": "Sả",
        "category": "spice",
        "is_required": true,
        "grams": 30,
        "display_quantity": "2 củ băm",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111206",
        "name_vi": "Ớt",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "1 quả cắt lát",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 tép băm",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Cắt thịt gà miếng vừa ăn, ướp nhanh với nước mắm; băm nhỏ sả, tỏi và cắt lát ớt.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm sả, tỏi và ớt trong dầu nóng rồi xào gà lửa lớn 12 phút cho săn vàng thơm.",
        "estimated_minutes": 12
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/ga-xao-sa-ot",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222212": {
    "id": "22222222-2222-4222-8222-222222222212",
    "slug": "tom-rang-hanh-toi",
    "name_vi": "Tôm rang hành tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 8,
    "cook_minutes": 10,
    "total_minutes": 18,
    "cover_image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80",
    "description": "Tôm tươi rang mặn ngọt bóng đẹp cùng tỏi phi và hành lá thơm lừng.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111214",
        "name_vi": "Tôm tươi",
        "category": "seafood",
        "is_required": true,
        "grams": 250,
        "display_quantity": "250 g",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 12,
        "display_quantity": "3 tép băm",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": true,
        "grams": 15,
        "display_quantity": "2 nhánh",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 12,
        "display_quantity": "1 muỗng canh",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111109",
        "name_vi": "Đường",
        "category": "pantry",
        "is_required": true,
        "grams": 8,
        "display_quantity": "1.5 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 7
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Cắt râu, rút chỉ lưng tôm tươi, rửa sạch để ráo; băm tỏi và cắt khúc hành lá.",
        "estimated_minutes": 8
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm tỏi với dầu ăn, đảo tôm săn đỏ rồi nêm nước mắm, đường rim cạn sốt, rắc hành tiêu.",
        "estimated_minutes": 10
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/tom-rang-hanh-toi",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222213": {
    "id": "22222222-2222-4222-8222-222222222213",
    "slug": "ca-kho-gung",
    "name_vi": "Cá kho gừng",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 30,
    "total_minutes": 40,
    "cover_image_url": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=80",
    "description": "Cá tươi kho gừng thái sợi ấm bụng, khử tanh và đậm đà vị mắm tiêu.",
    "country_code": "VN",
    "base_servings": 3,
    "servings": 3,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111215",
        "name_vi": "Cá nguyên con",
        "category": "seafood",
        "is_required": true,
        "grams": 400,
        "display_quantity": "1 con làm sạch cắt khúc",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111216",
        "name_vi": "Gừng",
        "category": "spice",
        "is_required": true,
        "grams": 25,
        "display_quantity": "1 củ thái sợi",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111206",
        "name_vi": "Ớt",
        "category": "spice",
        "is_required": false,
        "grams": 8,
        "display_quantity": "1 quả",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": false,
        "grams": 15,
        "display_quantity": "2 nhánh",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 25,
        "display_quantity": "2 muỗng canh",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111109",
        "name_vi": "Đường",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 7
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 8
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Làm sạch cá cắt khúc, ướp với nước mắm, tiêu và nửa phần gừng thái sợi trong 10 phút.",
        "estimated_minutes": 10
      },
      {
        "step_no": 2,
        "instruction": "Thắng nhẹ đường với dầu ăn tạo màu cánh gián, xếp cá và phần gừng còn lại kho lửa nhỏ 30 phút.",
        "estimated_minutes": 30
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/ca-kho-gung",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222214": {
    "id": "22222222-2222-4222-8222-222222222214",
    "slug": "thit-heo-ham-khoai-tay-ca-rot",
    "name_vi": "Thịt heo hầm khoai tây cà rốt",
    "cuisine_code": "VN",
    "prep_minutes": 15,
    "cook_minutes": 30,
    "total_minutes": 45,
    "cover_image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80",
    "description": "Canh hầm thịt heo mềm ngọt kết hợp khoai tây bùi béo và cà rốt thanh mát.",
    "country_code": "VN",
    "base_servings": 3,
    "servings": 3,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111213",
        "name_vi": "Thịt heo sống",
        "category": "protein",
        "is_required": true,
        "grams": 300,
        "display_quantity": "300 g cắt khối",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111202",
        "name_vi": "Khoai tây",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "2 củ cắt khối",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111203",
        "name_vi": "Cà rốt",
        "category": "vegetable",
        "is_required": true,
        "grams": 120,
        "display_quantity": "1 củ cắt khoanh",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111204",
        "name_vi": "Hành tây",
        "category": "vegetable",
        "is_required": true,
        "grams": 60,
        "display_quantity": "1/2 củ bổ múi",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": false,
        "grams": 15,
        "display_quantity": "2 nhánh",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 5,
        "display_quantity": "1 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "1 muỗng canh",
        "sort_order": 7
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 8
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Sơ chế thịt heo, gọt vỏ cắt khối khoai tây, cà rốt và hành tây; chần sơ thịt cho trong nước.",
        "estimated_minutes": 15
      },
      {
        "step_no": 2,
        "instruction": "Hầm thịt heo 15 phút rồi thêm khoai tây, cà rốt, hành tây nấu mềm thêm 15 phút, nêm muối mắm tiêu.",
        "estimated_minutes": 30
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/thit-heo-ham-khoai-tay-ca-rot",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222215": {
    "id": "22222222-2222-4222-8222-222222222215",
    "slug": "bo-xao-bong-cai-xanh-nam",
    "name_vi": "Thịt bò xào bông cải xanh nấm",
    "cuisine_code": "VN",
    "prep_minutes": 8,
    "cook_minutes": 10,
    "total_minutes": 18,
    "cover_image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt bò xào mềm cùng bông cải xanh giòn ngọt và nấm tươi giàu dinh dưỡng.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111301",
        "name_vi": "Thịt bò",
        "category": "protein",
        "is_required": true,
        "grams": 200,
        "display_quantity": "200 g thái mỏng",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111209",
        "name_vi": "Bông cải xanh",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "1 bông tách nhánh",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111210",
        "name_vi": "Nấm",
        "category": "vegetable",
        "is_required": true,
        "grams": 100,
        "display_quantity": "100 g thái lát",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 tép băm",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 12,
        "display_quantity": "1 muỗng canh",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 4,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 7
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Ướp thịt bò thái mỏng với chút tỏi băm, muối tiêu; chần nhanh bông cải xanh 2 phút giữ màu xanh.",
        "estimated_minutes": 8
      },
      {
        "step_no": 2,
        "instruction": "Xào nhanh thịt bò lửa lớn rồi trút riêng; xào nấm và bông cải xanh chín tới rồi đảo đều cùng bò.",
        "estimated_minutes": 10
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bo-xao-bong-cai-xanh-nam",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222216": {
    "id": "22222222-2222-4222-8222-222222222216",
    "slug": "bap-cai-xao-nam-toi",
    "name_vi": "Bắp cải xào nấm tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 6,
    "cook_minutes": 8,
    "total_minutes": 14,
    "cover_image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
    "description": "Bắp cải xào giòn ngọt cùng nấm tươi và tỏi phi thanh đạm hoàn tất trong 14 phút.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111208",
        "name_vi": "Bắp cải",
        "category": "vegetable",
        "is_required": true,
        "grams": 250,
        "display_quantity": "1/4 bắp thái sợi",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111210",
        "name_vi": "Nấm",
        "category": "vegetable",
        "is_required": true,
        "grams": 100,
        "display_quantity": "100 g thái lát",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 tép đập dập",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 muỗng cà phê",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 4,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Thái sợi bắp cải, rửa sạch nấm và đập dập tỏi.",
        "estimated_minutes": 6
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm tỏi với dầu ăn, cho nấm và bắp cải vào xào nhanh lửa lớn 8 phút, nêm muối vừa ăn.",
        "estimated_minutes": 8
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bap-cai-xao-nam-toi",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222217": {
    "id": "22222222-2222-4222-8222-222222222217",
    "slug": "dua-leo-tron-toi-ot",
    "name_vi": "Dưa leo trộn tỏi ớt",
    "cuisine_code": "VN",
    "prep_minutes": 10,
    "cook_minutes": 0,
    "total_minutes": 10,
    "cover_image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
    "description": "Dưa leo đập dập trộn tỏi ớt chua ngọt giòn rụm giải ngấy trong 10 phút.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111207",
        "name_vi": "Dưa leo",
        "category": "vegetable",
        "is_required": true,
        "grams": 250,
        "display_quantity": "2 quả đập dập",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 tép băm",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111206",
        "name_vi": "Ớt",
        "category": "spice",
        "is_required": true,
        "grams": 8,
        "display_quantity": "1 quả băm",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111311",
        "name_vi": "Chanh tươi",
        "category": "vegetable",
        "is_required": false,
        "grams": 20,
        "display_quantity": "1/2 quả vắt nước",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111109",
        "name_vi": "Đường",
        "category": "pantry",
        "is_required": true,
        "grams": 8,
        "display_quantity": "1.5 muỗng cà phê",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Rửa sạch dưa leo, đập dập cắt khúc vừa ăn rồi trộn đều cùng tỏi ớt băm, muối, đường và nước cốt chanh.",
        "estimated_minutes": 10
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/dua-leo-tron-toi-ot",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222218": {
    "id": "22222222-2222-4222-8222-222222222218",
    "slug": "bo-xao-ot-chuong-hanh-tay",
    "name_vi": "Thịt bò xào ớt chuông hành tây kiểu Âu",
    "cuisine_code": "EU",
    "prep_minutes": 8,
    "cook_minutes": 12,
    "total_minutes": 20,
    "cover_image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
    "description": "Thịt bò áp chảo bơ tỏi cùng ớt chuông giòn ngọt và hành tây kiểu Âu.",
    "country_code": "FR",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111301",
        "name_vi": "Thịt bò",
        "category": "protein",
        "is_required": true,
        "grams": 220,
        "display_quantity": "220 g cắt khối",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111218",
        "name_vi": "Ớt chuông",
        "category": "vegetable",
        "is_required": true,
        "grams": 160,
        "display_quantity": "1 quả cắt miếng vuông",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111204",
        "name_vi": "Hành tây",
        "category": "vegetable",
        "is_required": true,
        "grams": 80,
        "display_quantity": "1/2 củ cắt múi",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 10,
        "display_quantity": "2 tép băm",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111303",
        "name_vi": "Bơ lạt",
        "category": "other",
        "is_required": true,
        "grams": 15,
        "display_quantity": "1 muỗng canh",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 4,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 6
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 7
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Cắt thịt bò, ớt chuông và hành tây thành miếng vuông đồng đều; ướp thịt bò với muối và tiêu xay.",
        "estimated_minutes": 8
      },
      {
        "step_no": 2,
        "instruction": "Đun chảy bơ lạt với tỏi băm, áp chảo thịt bò săn mặt rồi đảo nhanh cùng ớt chuông và hành tây.",
        "estimated_minutes": 12
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bo-xao-ot-chuong-hanh-tay",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222219": {
    "id": "22222222-2222-4222-8222-222222222219",
    "slug": "bap-ngot-ap-chao-bo-toi-kieu-my",
    "name_vi": "Bắp ngọt áp chảo bơ tỏi kiểu Mỹ",
    "cuisine_code": "US",
    "prep_minutes": 5,
    "cook_minutes": 10,
    "total_minutes": 15,
    "cover_image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
    "description": "Bắp ngọt tách hạt áp chảo thơm ngậy bơ lạt và tỏi phi kiểu Mỹ trong 15 phút.",
    "country_code": "US",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111219",
        "name_vi": "Bắp ngọt",
        "category": "vegetable",
        "is_required": true,
        "grams": 200,
        "display_quantity": "1 trái tách hạt",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111303",
        "name_vi": "Bơ lạt",
        "category": "other",
        "is_required": true,
        "grams": 20,
        "display_quantity": "1.5 muỗng canh",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 8,
        "display_quantity": "2 tép băm",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111105",
        "name_vi": "Hành lá",
        "category": "spice",
        "is_required": false,
        "grams": 10,
        "display_quantity": "1 nhánh cắt nhỏ",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 5
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111110",
        "name_vi": "Tiêu xay",
        "category": "pantry",
        "is_required": true,
        "grams": 2,
        "display_quantity": "1/3 muỗng cà phê",
        "sort_order": 6
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Tách hạt bắp ngọt, rửa sạch để ráo; băm nhỏ tỏi và cắt nhỏ hành lá.",
        "estimated_minutes": 5
      },
      {
        "step_no": 2,
        "instruction": "Đun chảy bơ lạt, phi thơm tỏi rồi áp chảo bắp ngọt lửa vừa 10 phút với muối tiêu, rắc hành lá.",
        "estimated_minutes": 10
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/bap-ngot-ap-chao-bo-toi-kieu-my",
    "content_license": "CC-BY-4.0"
  },
  "22222222-2222-4222-8222-222222222220": {
    "id": "22222222-2222-4222-8222-222222222220",
    "slug": "rau-muong-xao-toi",
    "name_vi": "Rau muống xào tỏi",
    "cuisine_code": "VN",
    "prep_minutes": 5,
    "cook_minutes": 7,
    "total_minutes": 12,
    "cover_image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
    "description": "Rau muống xào tỏi xanh giòn chuẩn bữa cơm gia đình Việt trong 12 phút.",
    "country_code": "VN",
    "base_servings": 2,
    "servings": 2,
    "ingredients": [
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111312",
        "name_vi": "Rau muống",
        "category": "vegetable",
        "is_required": true,
        "grams": 300,
        "display_quantity": "1 bó nhặt sạch",
        "sort_order": 1
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111205",
        "name_vi": "Tỏi",
        "category": "spice",
        "is_required": true,
        "grams": 15,
        "display_quantity": "4 tép đập dập",
        "sort_order": 2
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111108",
        "name_vi": "Dầu ăn",
        "category": "pantry",
        "is_required": true,
        "grams": 12,
        "display_quantity": "1 muỗng canh",
        "sort_order": 3
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111106",
        "name_vi": "Muối",
        "category": "pantry",
        "is_required": true,
        "grams": 3,
        "display_quantity": "1/2 muỗng cà phê",
        "sort_order": 4
      },
      {
        "ingredient_id": "11111111-1111-4111-8111-111111111107",
        "name_vi": "Nước mắm",
        "category": "pantry",
        "is_required": true,
        "grams": 8,
        "display_quantity": "1.5 muỗng cà phê",
        "sort_order": 5
      }
    ],
    "steps": [
      {
        "step_no": 1,
        "instruction": "Nhặt sạch rau muống, rửa ráo và đập dập tỏi.",
        "estimated_minutes": 5
      },
      {
        "step_no": 2,
        "instruction": "Phi thơm nửa phần tỏi, xào rau muống trên lửa lớn 7 phút với muối, nước mắm rồi thêm phần tỏi còn lại.",
        "estimated_minutes": 7
      }
    ],
    "nutrition_evidence": [],
    "usda_nutrition": null,
    "nutrition_disclaimer_vi": "Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối.",
    "source_name": "FoodVision Editorial",
    "source_url": "https://foodvision.local/recipes/rau-muong-xao-toi",
    "content_license": "CC-BY-4.0"
  }
};

const FALLBACK_ING_BY_ID = new Map(
  MOCK_ALL_INGREDIENTS.map((item) => [item.id, item.name_vi] as const)
);

export function getIngredientNameById(
  ingredientId: string,
  knownIngredients?: Ingredient[]
): string {
  if (knownIngredients && knownIngredients.length > 0) {
    const found = knownIngredients.find((item) => item.id === ingredientId);
    if (found) return found.name_vi;
  }
  return (
    FALLBACK_ING_BY_ID.get(ingredientId) ??
    `Nguyên liệu (${ingredientId.slice(0, 6)})`
  );
}
