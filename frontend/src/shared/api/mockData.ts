import {
  Ingredient,
  RecipeDetail,
  RecipeIngredientView,
  RecipeSummary,
} from './types';

/**
 * Danh sách 5 gia vị sẵn có trong bếp (category = 'pantry') theo đúng BR-04 & ADR-008:
 * Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu (Tuyệt đối không tính Nước lọc).
 */
export const MOCK_PANTRY_INGREDIENTS: Ingredient[] = [
  {
    id: '22222222-2222-4222-8222-000000000001',
    slug: 'muoi',
    name_vi: 'Muối',
    category: 'pantry',
    is_active: true,
  },
  {
    id: '22222222-2222-4222-8222-000000000002',
    slug: 'duong',
    name_vi: 'Đường',
    category: 'pantry',
    is_active: true,
  },
  {
    id: '22222222-2222-4222-8222-000000000003',
    slug: 'nuoc-mam',
    name_vi: 'Nước mắm',
    category: 'pantry',
    is_active: true,
  },
  {
    id: '22222222-2222-4222-8222-000000000004',
    slug: 'dau-an',
    name_vi: 'Dầu ăn',
    category: 'pantry',
    is_active: true,
  },
  {
    id: '22222222-2222-4222-8222-000000000005',
    slug: 'hat-tieu',
    name_vi: 'Hạt tiêu',
    category: 'pantry',
    is_active: true,
  },
];

/**
 * Danh sách nguyên liệu chính chuẩn trong từ điển (category != 'pantry').
 */
export const MOCK_MAIN_INGREDIENTS: Ingredient[] = [
  {
    id: '11111111-1111-4111-8111-000000000001',
    slug: 'dau-hu',
    name_vi: 'Đậu hũ',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000002',
    slug: 'ca-chua',
    name_vi: 'Cà chua',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000003',
    slug: 'trung-ga',
    name_vi: 'Trứng gà',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000004',
    slug: 'thit-heo',
    name_vi: 'Thịt heo',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000005',
    slug: 'bap',
    name_vi: 'Bắp',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000006',
    slug: 'dua-leo',
    name_vi: 'Dưa leo',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000007',
    slug: 'hanh-la',
    name_vi: 'Hành lá',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000008',
    slug: 'hanh-tay',
    name_vi: 'Hành tây',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000009',
    slug: 'toi',
    name_vi: 'Tỏi',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000010',
    slug: 'thit-bo',
    name_vi: 'Thịt bò',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000011',
    slug: 'uc-ga',
    name_vi: 'Ức gà',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000012',
    slug: 'tom-tuoi',
    name_vi: 'Tôm tươi',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000013',
    slug: 'bong-cai-xanh',
    name_vi: 'Bông cải xanh',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000014',
    slug: 'thom',
    name_vi: 'Thơm',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000015',
    slug: 'ca-hoi',
    name_vi: 'Cá hồi',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000016',
    slug: 'muc-tuoi',
    name_vi: 'Mực tươi',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000017',
    slug: 'gung',
    name_vi: 'Gừng',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000018',
    slug: 'ot-sung',
    name_vi: 'Ớt sừng',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000019',
    slug: 'suon-heo',
    name_vi: 'Sườn heo',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000020',
    slug: 'thit-ga-ta',
    name_vi: 'Thịt gà ta',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000021',
    slug: 'trung-cut',
    name_vi: 'Trứng cút',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000022',
    slug: 'cha-lua',
    name_vi: 'Chả lụa',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000023',
    slug: 'ca-rot',
    name_vi: 'Cà rốt',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000024',
    slug: 'khoai-tay',
    name_vi: 'Khoai tây',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000025',
    slug: 'rau-muong',
    name_vi: 'Rau muống',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000026',
    slug: 'nam-huong',
    name_vi: 'Nấm hương',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000027',
    slug: 'ca-basa',
    name_vi: 'Cá basa',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000028',
    slug: 'ngheu-tuoi',
    name_vi: 'Nghêu (Ngao)',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000029',
    slug: 'cua-bien',
    name_vi: 'Cua biển',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000030',
    slug: 'sa-cay',
    name_vi: 'Sả cây',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000031',
    slug: 'hanh-tim',
    name_vi: 'Hành tím',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000032',
    slug: 'ngo-ri',
    name_vi: 'Ngò rí (Rau mùi)',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000033',
    slug: 'cai-thia',
    name_vi: 'Cải thìa',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000034',
    slug: 'bap-cai',
    name_vi: 'Bắp cải',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000035',
    slug: 'xa-lach',
    name_vi: 'Xà lách',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000036',
    slug: 'nam-kim-cham',
    name_vi: 'Nấm kim châm',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000037',
    slug: 'thit-ba-chi',
    name_vi: 'Thịt ba chỉ',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000038',
    slug: 'thit-bam',
    name_vi: 'Thịt heo bằm',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000039',
    slug: 'thit-vit',
    name_vi: 'Thịt vịt',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000040',
    slug: 'ca-thu',
    name_vi: 'Cá thu',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000041',
    slug: 'cha-ca',
    name_vi: 'Chả cá',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000042',
    slug: 'oc-buou',
    name_vi: 'Ốc bươu',
    category: 'seafood',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000043',
    slug: 'trung-vit',
    name_vi: 'Trứng vịt',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000044',
    slug: 'dau-hu-non',
    name_vi: 'Đậu hũ non',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000045',
    slug: 'tau-hu-ky',
    name_vi: 'Tàu hũ ky (Váng đậu)',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000046',
    slug: 'trung-muoi',
    name_vi: 'Trứng muối',
    category: 'protein',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000047',
    slug: 'rau-ngot',
    name_vi: 'Rau ngót',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000048',
    slug: 'cai-ngot',
    name_vi: 'Cải ngọt',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000049',
    slug: 'rau-mong-toi',
    name_vi: 'Rau mồng tơi',
    category: 'vegetable',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000050',
    slug: 'la-chanh',
    name_vi: 'Lá chanh',
    category: 'spice',
    is_active: true,
  },
  {
    id: '11111111-1111-4111-8111-000000000051',
    slug: 'rau-ram',
    name_vi: 'Rau răm',
    category: 'spice',
    is_active: true,
  },
];

export const MOCK_ALL_INGREDIENTS: Ingredient[] = [
  ...MOCK_MAIN_INGREDIENTS,
  ...MOCK_PANTRY_INGREDIENTS,
];

/**
 * Danh sách công thức món ăn mẫu chuẩn OpenAPI (bao phủ VN, EU, US và các mốc thời gian <=15, <=30, <=60 phút).
 */
export const MOCK_RECIPES: RecipeSummary[] = [
  {
    id: 'a1111111-1111-4111-8111-000000000001',
    slug: 'canh-ca-chua-trung',
    name_vi: 'Canh cà chua trứng (Canh mây)',
    cuisine_code: 'VN',
    prep_minutes: 5,
    cook_minutes: 10,
    total_minutes: 15,
    cover_image_url:
      'https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000002',
    slug: 'dau-hu-sot-ca-chua',
    name_vi: 'Đậu hũ sốt cà chua',
    cuisine_code: 'VN',
    prep_minutes: 10,
    cook_minutes: 15,
    total_minutes: 25,
    cover_image_url:
      'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000003',
    slug: 'thit-heo-kho-trung',
    name_vi: 'Thịt heo kho trứng cút đậm đà',
    cuisine_code: 'VN',
    prep_minutes: 15,
    cook_minutes: 35,
    total_minutes: 50,
    cover_image_url:
      'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000004',
    slug: 'bo-luc-lac-hanh-tay',
    name_vi: 'Bò lúc lắc xào hành tây',
    cuisine_code: 'VN',
    prep_minutes: 15,
    cook_minutes: 10,
    total_minutes: 25,
    cover_image_url:
      'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000005',
    slug: 'salad-dua-leo-ca-chua-kieu-au',
    name_vi: 'Salad dưa leo cà chua kiểu Âu',
    cuisine_code: 'EU',
    prep_minutes: 10,
    cook_minutes: 2,
    total_minutes: 12,
    cover_image_url:
      'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000006',
    slug: 'uc-ga-ap-chao-bo-toi',
    name_vi: 'Ức gà áp chảo sốt bơ tỏi',
    cuisine_code: 'EU',
    prep_minutes: 10,
    cook_minutes: 15,
    total_minutes: 25,
    cover_image_url:
      'https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000007',
    slug: 'bap-xao-bo-toi-kieu-my',
    name_vi: 'Bắp ngọt xào bơ tỏi kiểu Mỹ',
    cuisine_code: 'US',
    prep_minutes: 5,
    cook_minutes: 10,
    total_minutes: 15,
    cover_image_url:
      'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 'a1111111-1111-4111-8111-000000000008',
    slug: 'tom-xao-bong-cai-xanh',
    name_vi: 'Tôm tươi xào bông cải xanh',
    cuisine_code: 'US',
    prep_minutes: 10,
    cook_minutes: 12,
    total_minutes: 22,
    cover_image_url:
      'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80',
  },
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

const ING_BY_ID = new Map(
  MOCK_ALL_INGREDIENTS.map((item) => [item.id, item] as const)
);

function buildMockRecipeIngredient(
  ingredientId: string,
  isRequired: boolean,
  displayQuantity: string | null,
  sortOrder: number
): RecipeIngredientView {
  const ing = ING_BY_ID.get(ingredientId);
  if (!ing) {
    throw new Error(`Unknown mock ingredient id: ${ingredientId}`);
  }
  return {
    ingredient_id: ing.id,
    name_vi: ing.name_vi,
    category: ing.category,
    is_required: isRequired,
    display_quantity: displayQuantity,
    sort_order: sortOrder,
  };
}

/**
 * Tra cứu nhanh tên nguyên liệu tiếng Việt từ UUID (dùng cho badge matched/missing).
 */
export function getIngredientNameById(
  ingredientId: string,
  extraIngredients: Ingredient[] = []
): string {
  const fromExtra = extraIngredients.find((item) => item.id === ingredientId);
  if (fromExtra) {
    return fromExtra.name_vi;
  }
  const fromMock = ING_BY_ID.get(ingredientId);
  if (fromMock) {
    return fromMock.name_vi;
  }
  return `Nguyên liệu (${ingredientId.slice(0, 6)})`;
}

const RECIPE_BY_ID = new Map(
  MOCK_RECIPES.map((recipe) => [recipe.id, recipe] as const)
);

function summaryOrThrow(id: string): RecipeSummary {
  const found = RECIPE_BY_ID.get(id);
  if (!found) {
    throw new Error(`Missing mock recipe summary: ${id}`);
  }
  return found;
}

/**
 * Chi tiết 8 công thức mẫu chuẩn OpenAPI v1.1.0 (chế độ dự phòng khi Backend chưa chạy).
 * Bao phủ đầy đủ `category === 'pantry'` tách riêng, `nutrition_evidence` có/không có tag (`TC-15`)
 * và mô tả ướp/chờ trong `cook_minutes` (`BR-05`).
 */
export const MOCK_RECIPE_DETAILS: Record<string, RecipeDetail> = {
  'a1111111-1111-4111-8111-000000000001': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000001'),
    description:
      'Món canh trứng cà chua thanh mát nấu nhanh trong 15 phút, vị chua dịu nhẹ rất đưa cơm gia đình Việt.',
    country_code: 'VN',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000002',
        true,
        '2 quả chín',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000003',
        true,
        '2 quả',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000007',
        false,
        '2 nhánh thái nhỏ',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1 muỗng cà phê',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000003',
        true,
        '1 muỗng cà phê',
        5
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '1 muỗng canh',
        6
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Rửa sạch cà chua, cắt múi cau; đánh tan trứng gà trong bát với chút nước mắm.',
        estimated_minutes: 5,
      },
      {
        step_no: 2,
        instruction:
          'Làm nóng dầu ăn, xào cà chua với muối đến khi ra màu đẹp rồi thêm 500ml nước đun sôi.',
        estimated_minutes: 6,
      },
      {
        step_no: 3,
        instruction:
          'Đổ từ từ trứng vào nồi nước sôi theo vòng tròn và khuấy nhẹ tạo vân mây, rắc hành lá trước khi tắt bếp.',
        estimated_minutes: 4,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000001',
          code: 'HIGH_VITAMIN_C_LYCOPENE',
          name_vi: 'Giàu Lycopene & Vitamin tự nhiên',
          description:
            'Cà chua cung cấp lycopene và vitamin A, C hỗ trợ chống oxy hóa ở mức nguyên liệu.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: 'Thích hợp cho bữa cơm nhẹ, chế biến ít dầu mỡ.',
      },
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000002',
          code: 'QUICK_BALANCED_MEAL',
          name_vi: 'Món canh thanh nhẹ dễ tiêu',
          description: 'Kết hợp đạm từ trứng gà và rau quả nấu chín nhanh.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: null,
      },
    ],
    source_name: 'FoodVision Culinary Archive',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000002': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000002'),
    description:
      'Đậu hũ chiên vàng ngoài giòn trong mềm quyện cùng sốt cà chua sánh đậm, thích hợp cho cả bữa chay và mặn.',
    country_code: 'VN',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000001',
        true,
        '2 bìa vừa',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000002',
        true,
        '2 quả chín',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000007',
        false,
        '2 nhánh',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1 muỗng cà phê',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '2 muỗng canh',
        5
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Thấm khô đậu hũ, cắt miếng vuông vừa ăn rồi áp chảo vàng đều hai mặt với dầu ăn.',
        estimated_minutes: 10,
      },
      {
        step_no: 2,
        instruction:
          'Băm nhỏ cà chua, xào nhừ với chút muối và 3 muỗng nước lọc tạo sốt sánh.',
        estimated_minutes: 8,
      },
      {
        step_no: 3,
        instruction:
          'Cho đậu hũ vào rim lửa nhỏ cho thấm vị rồi rắc hành lá thái nhỏ.',
        estimated_minutes: 7,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000003',
          code: 'HIGH_PROTEIN_PLANT',
          name_vi: 'Giàu đạm thực vật',
          description:
            'Nguồn đạm thực vật lành mạnh từ đậu nành kết hợp lycopene từ cà chua.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: 'Phù hợp thực đơn ít chất béo bão hòa.',
      },
    ],
    source_name: 'FoodVision Culinary Archive',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000003': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000003'),
    description:
      'Thịt heo kho mềm cùng trứng cút thấm vị mặn ngọt hài hòa; thời gian nấu bao gồm cả bước ướp thịt nghỉ ngấm gia vị.',
    country_code: 'VN',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000004',
        true,
        '1 phần vừa ăn',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000021',
        true,
        '10 quả luộc bóc vỏ',
        2
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000003',
        true,
        '2 muỗng canh',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000002',
        true,
        '1.5 muỗng canh',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000005',
        true,
        '1/2 muỗng cà phê',
        5
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Chần sơ thịt heo rồi ướp cùng nước mắm, đường và hạt tiêu khoảng 10 phút cho thấm.',
        estimated_minutes: 15,
      },
      {
        step_no: 2,
        instruction:
          'Thắng đường tạo màu cánh gián, đảo săn thịt rồi thêm nước xâm xấp kho lửa liu riu.',
        estimated_minutes: 20,
      },
      {
        step_no: 3,
        instruction:
          'Thả trứng cút đã luộc vào kho thêm cho nước sánh nhẹ và rắc hạt tiêu.',
        estimated_minutes: 15,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000004',
          code: 'HIGH_PROTEIN_SAVORY',
          name_vi: 'Giàu đạm động vật truyền thống',
          description:
            'Cung cấp nguồn đạm kết hợp từ thịt heo và trứng phục vụ bữa chính.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: null,
      },
    ],
    source_name: 'FoodVision Culinary Archive',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000004': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000004'),
    description:
      'Thịt bò thái vuông áp chảo lửa lớn giữ độ mềm mọng, xào nhanh cùng hành tây giòn ngọt thơm lừng tỏi tiêu.',
    country_code: 'VN',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000010',
        true,
        '1 phần thái khối vuông',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000008',
        true,
        '1 củ bổ múi cau',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000009',
        false,
        '3 tép băm',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '2 muỗng canh',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1/2 muỗng cà phê',
        5
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000005',
        true,
        '1/2 muỗng cà phê',
        6
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Ướp thịt bò thái khối với dầu ăn, chút muối, hạt tiêu và tỏi băm trong 10 phút.',
        estimated_minutes: 15,
      },
      {
        step_no: 2,
        instruction:
          'Xào nhanh thịt bò trên chảo nóng lửa lớn 3 phút rồi trút riêng.',
        estimated_minutes: 5,
      },
      {
        step_no: 3,
        instruction:
          'Đảo hành tây vừa chín tới, cho thịt bò vào xóc đều rồi tắt bếp ngay.',
        estimated_minutes: 5,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000005',
          code: 'HIGH_IRON_PROTEIN',
          name_vi: 'Giàu sắt & Đạm thịt đỏ',
          description:
            'Thịt bò là nguồn cung cấp sắt heme và protein chất lượng cao.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: null,
      },
    ],
    source_name: 'FoodVision Culinary Archive',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000005': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000005'),
    description:
      'Món salad tươi mát trộn nhanh chuẩn vị Âu từ dưa leo giòn, cà chua mọng nước và xốt dầu hạt tiêu thanh nhẹ.',
    country_code: 'EU',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000006',
        true,
        '1 quả thái lát',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000002',
        true,
        '2 quả cắt múi nhỏ',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000035',
        false,
        '1 nắm nhỏ',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '1 muỗng canh',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1/3 muỗng cà phê',
        5
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000005',
        true,
        '1/3 muỗng cà phê',
        6
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Rửa sạch dưa leo, cà chua, xà lách; để ráo hoàn toàn trước khi cắt miếng vừa ăn.',
        estimated_minutes: 10,
      },
      {
        step_no: 2,
        instruction:
          'Trộn nhẹ các loại rau quả với dầu ăn, muối và hạt tiêu xay trước khi dọn.',
        estimated_minutes: 2,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000006',
          code: 'HIGH_FIBER_FRESH',
          name_vi: 'Giàu chất xơ & Rau tươi',
          description:
            'Giữ trọn vitamin nhạy nhiệt nhờ chế biến lạnh không qua đun nấu.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: null,
      },
    ],
    source_name: 'FoodVision Editorial EU',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000006': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000006'),
    description:
      'Ức gà áp chảo vàng cạnh mềm ẩm bên trong, phủ hương tỏi thơm và tiêu xay theo phong cách bếp Âu hiện đại.',
    country_code: 'EU',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000011',
        true,
        '1 miếng phi lê',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000009',
        true,
        '4 tép đập dập',
        2
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1/2 muỗng cà phê',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000005',
        true,
        '1/2 muỗng cà phê',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '1 muỗng canh',
        5
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Thấm khô ức gà, khía nhẹ mặt ngoài và ướp muối, hạt tiêu trong 10 phút.',
        estimated_minutes: 10,
      },
      {
        step_no: 2,
        instruction:
          'Áp chảo ức gà với dầu ăn và tỏi đập dập mỗi mặt 6 phút lửa vừa đến khi chín đều.',
        estimated_minutes: 15,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000007',
          code: 'LEAN_HIGH_PROTEIN',
          name_vi: 'Giàu đạm nạc ít béo',
          description:
            'Ức gà bỏ da là nguồn protein nạc phổ biến cho chế độ cân bằng.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: null,
      },
    ],
    source_name: 'FoodVision Editorial EU',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000007': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000007'),
    description:
      'Hạt bắp ngọt giòn xào nhanh cùng tỏi thơm dịu và chút đường muối, hoàn thiện gọn gàng chỉ trong 15 phút.',
    country_code: 'US',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000005',
        true,
        '1 trái tách hạt',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000009',
        true,
        '2 tép băm',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000007',
        false,
        '1 nhánh',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '1 muỗng canh',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1/3 muỗng cà phê',
        5
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000002',
        true,
        '1/2 muỗng cà phê',
        6
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Tách hạt bắp ngọt, rửa sạch và chần nhanh qua nước sôi cho bắp căng mọng.',
        estimated_minutes: 5,
      },
      {
        step_no: 2,
        instruction:
          'Phi thơm tỏi với dầu ăn, cho bắp vào đảo lửa vừa với muối và đường rồi rắc hành lá.',
        estimated_minutes: 10,
      },
    ],
    nutrition_evidence: [],
    source_name: 'FoodVision Editorial US',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
  'a1111111-1111-4111-8111-000000000008': {
    ...summaryOrThrow('a1111111-1111-4111-8111-000000000008'),
    description:
      'Tôm tươi săn chắc ngọt thịt kết hợp bông cải xanh giòn sật, chế biến nhanh giữ màu xanh tự nhiên.',
    country_code: 'US',
    ingredients: [
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000012',
        true,
        '1 phần bóc vỏ',
        1
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000013',
        true,
        '1/2 bông cắt nhỏ',
        2
      ),
      buildMockRecipeIngredient(
        '11111111-1111-4111-8111-000000000009',
        false,
        '2 tép băm',
        3
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000004',
        true,
        '1 muỗng canh',
        4
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000001',
        true,
        '1/2 muỗng cà phê',
        5
      ),
      buildMockRecipeIngredient(
        '22222222-2222-4222-8222-000000000005',
        true,
        '1/3 muỗng cà phê',
        6
      ),
    ],
    steps: [
      {
        step_no: 1,
        instruction:
          'Bóc vỏ rút chỉ tôm tươi; cắt bông cải xanh thành từng nhánh vừa ăn và trụng sơ.',
        estimated_minutes: 10,
      },
      {
        step_no: 2,
        instruction:
          'Phi thơm tỏi, xào săn tôm tươi trước rồi thả bông cải xanh vào đảo đều tay với muối và hạt tiêu.',
        estimated_minutes: 12,
      },
    ],
    nutrition_evidence: [
      {
        tag: {
          id: '33333333-3333-4333-8333-000000000008',
          code: 'HIGH_FIBER_SEAFOOD',
          name_vi: 'Đạm hải sản & Chất xơ xanh',
          description:
            'Kết hợp đạm dễ tiêu từ tôm tươi cùng vitamin K, C và chất xơ của bông cải xanh.',
          is_active: true,
        },
        source_urls: ['https://fdc.nal.usda.gov/'],
        note: 'Lưu ý: có thành phần hải sản (tôm).',
      },
    ],
    source_name: 'FoodVision Editorial US',
    source_url: 'https://fdc.nal.usda.gov/',
    content_license: 'CC-BY-4.0',
  },
};

export const MOCK_RECIPE_SCORING_META: Record<string, MockRecipeScoringMeta> = {
  'a1111111-1111-4111-8111-000000000001': {
    cookingMethod: 'boil',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000002': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000003': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000007': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000003': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000002': {
    cookingMethod: 'braise',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000001': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000002': {
        role: 'secondary',
        dishRole: 'sub',
        weight: 2,
      },
      '11111111-1111-4111-8111-000000000007': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000003': {
    cookingMethod: 'braise',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000004': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000021': {
        role: 'secondary',
        dishRole: 'main',
        weight: 2,
      },
      '22222222-2222-4222-8222-000000000003': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000002': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000005': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000004': {
    cookingMethod: 'stir_fry',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000010': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000008': {
        role: 'secondary',
        dishRole: 'sub',
        weight: 2,
      },
      '11111111-1111-4111-8111-000000000009': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000005': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000005': {
    cookingMethod: 'salad',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000006': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000002': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000035': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000005': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000006': {
    cookingMethod: 'pan_sear',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000011': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000009': {
        role: 'secondary',
        dishRole: 'sub',
        weight: 2,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000005': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000007': {
    cookingMethod: 'stir_fry',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000005': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000009': {
        role: 'secondary',
        dishRole: 'sub',
        weight: 2,
      },
      '11111111-1111-4111-8111-000000000007': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000002': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
  'a1111111-1111-4111-8111-000000000008': {
    cookingMethod: 'stir_fry',
    rolesByIngredientId: {
      '11111111-1111-4111-8111-000000000012': {
        role: 'core',
        dishRole: 'main',
        weight: 4,
      },
      '11111111-1111-4111-8111-000000000013': {
        role: 'secondary',
        dishRole: 'sub',
        weight: 2,
      },
      '11111111-1111-4111-8111-000000000009': {
        role: 'optional',
        dishRole: 'sub',
        weight: 0,
      },
      '22222222-2222-4222-8222-000000000004': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000001': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
      '22222222-2222-4222-8222-000000000005': {
        role: 'spice',
        dishRole: 'sub',
        weight: 1,
      },
    },
  },
};
