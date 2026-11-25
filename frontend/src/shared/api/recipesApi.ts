import { ApiClientError, apiGetWithFallback } from './client';
import { MOCK_RECIPES, MOCK_RECIPE_DETAILS } from './mockData';
import {
  PagedRecipes,
  RecipeDetail,
  RecipeListParams,
  USDANutritionEstimate,
} from './types';
import { normalizeVietnamese } from '../utils/vietnamese';

export const PORTION_SCALING_WARNING_VI =
  'Thời gian chế biến, mức nhiệt và lượng gia vị nêm nếm có thể không tăng/giảm tuyến tính hoàn toàn theo phép nhân khẩu phần.';

function roundTo2(value: number): number {
  return Math.round(value * 100) / 100;
}

function roundTo4(value: number): number {
  return Math.round(value * 10000) / 10000;
}

/**
 * Quy đổi tuyến tính khẩu phần (1..20) cho nhánh mock khớp 100% với backend/app/services/nutrition.py (TP 10, TP 11, DEF-09).
 */
export function scaleMockRecipeDetail(
  detail: RecipeDetail,
  requestedServings?: number
): RecipeDetail {
  const baseServings =
    typeof detail.base_servings === 'number' && detail.base_servings > 0
      ? detail.base_servings
      : 2;

  const targetServings =
    requestedServings !== undefined
      ? Math.min(Math.max(Math.round(requestedServings), 1), 20)
      : (detail.servings ?? baseServings);

  const factor = targetServings / baseServings;

  const scaledIngredients = detail.ingredients.map((item) => ({
    ...item,
    grams:
      typeof item.grams === 'number' && item.grams > 0
        ? roundTo2(item.grams * factor)
        : (item.grams ?? null),
  }));

  let scaledUsda: USDANutritionEstimate | null = null;
  if (detail.usda_nutrition != null) {
    scaledUsda = {
      kcal: roundTo2(detail.usda_nutrition.kcal * factor),
      protein_g: roundTo2(detail.usda_nutrition.protein_g * factor),
      fat_g: roundTo2(detail.usda_nutrition.fat_g * factor),
      carb_g: roundTo2(detail.usda_nutrition.carb_g * factor),
      source_urls: [...detail.usda_nutrition.source_urls],
      scaling_factor: roundTo4(factor),
      scaling_warning_vi:
        targetServings !== baseServings ? PORTION_SCALING_WARNING_VI : null,
    };
  }

  return {
    ...detail,
    base_servings: baseServings,
    servings: targetServings,
    ingredients: scaledIngredients,
    usda_nutrition: scaledUsda,
  };
}

/**
 * Bộ lọc dự phòng trên bộ dữ liệu mẫu chuẩn OpenAPI (khi Backend chưa chạy).
 */
export function filterMockRecipes(params: RecipeListParams): PagedRecipes {
  const limit = Math.min(Math.max(params.limit ?? 12, 1), 50);
  const offset = Math.max(params.offset ?? 0, 0);
  const normalizedQuery = normalizeVietnamese(params.q ?? '');

  const filtered = MOCK_RECIPES.filter((recipe) => {
    if (params.cuisine_code && recipe.cuisine_code !== params.cuisine_code) {
      return false;
    }
    if (
      typeof params.max_total_minutes === 'number' &&
      recipe.total_minutes > params.max_total_minutes
    ) {
      return false;
    }
    if (normalizedQuery) {
      const normalizedTitle = normalizeVietnamese(recipe.name_vi);
      const normalizedSlug = recipe.slug.replace(/-/g, ' ');
      return (
        normalizedTitle.includes(normalizedQuery) ||
        normalizedSlug.includes(normalizedQuery)
      );
    }
    return true;
  });

  return {
    items: filtered.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

/**
 * Gọi GET /api/v1/recipes theo đúng hợp đồng docs/03-api/openapi.yaml (FR-01, AC-01, AC-02).
 */
export async function listRecipes(
  params: RecipeListParams = {},
  signal?: AbortSignal
): Promise<PagedRecipes> {
  const limit = params.limit ?? 12;
  const offset = params.offset ?? 0;
  const trimmedQuery = params.q?.trim();

  return apiGetWithFallback<PagedRecipes>(
    '/recipes',
    {
      q: trimmedQuery && trimmedQuery.length > 0 ? trimmedQuery : undefined,
      cuisine_code: params.cuisine_code ?? undefined,
      max_total_minutes: params.max_total_minutes ?? undefined,
      limit,
      offset,
    },
    () => filterMockRecipes(params),
    signal
  );
}

/**
 * Gọi GET /api/v1/recipes/{recipe_id}?servings=... để lấy chi tiết công thức, nguyên liệu tách pantry,
 * định lượng quy đổi khẩu phần, ước tính dinh dưỡng USDA Tầng 2 và nhãn tham khảo Tầng 1 (`FR-02`, `FR-08`, `ADR-004`, `DEF-09`).
 */
export async function getRecipeById(
  recipeId: string,
  servings?: number,
  signal?: AbortSignal
): Promise<RecipeDetail> {
  const safeServings =
    typeof servings === 'number' && Number.isFinite(servings)
      ? Math.min(Math.max(Math.round(servings), 1), 20)
      : undefined;

  return apiGetWithFallback<RecipeDetail>(
    `/recipes/${encodeURIComponent(recipeId)}`,
    {
      servings: safeServings,
    },
    () => {
      const detail = MOCK_RECIPE_DETAILS[recipeId];
      if (!detail) {
        throw new ApiClientError(
          404,
          'RECIPE_NOT_FOUND',
          'Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.'
        );
      }
      return scaleMockRecipeDetail(detail, safeServings);
    },
    signal
  );
}
