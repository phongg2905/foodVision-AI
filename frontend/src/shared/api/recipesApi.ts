import { ApiClientError, apiGetWithFallback } from './client';
import { MOCK_RECIPES, MOCK_RECIPE_DETAILS } from './mockData';
import { PagedRecipes, RecipeDetail, RecipeListParams } from './types';
import { normalizeVietnamese } from '../utils/vietnamese';

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
  params: RecipeListParams = {}
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
    () => filterMockRecipes(params)
  );
}

/**
 * Gọi GET /api/v1/recipes/{recipe_id} để lấy chi tiết công thức, nguyên liệu tách pantry,
 * các bước nấu và nhãn dinh dưỡng tham khảo (`FR-02`, `FR-08`, `TC-03`, `TC-15`).
 */
export async function getRecipeById(recipeId: string): Promise<RecipeDetail> {
  return apiGetWithFallback<RecipeDetail>(
    `/recipes/${encodeURIComponent(recipeId)}`,
    {},
    () => {
      const detail = MOCK_RECIPE_DETAILS[recipeId];
      if (!detail) {
        throw new ApiClientError(
          404,
          'RECIPE_NOT_FOUND',
          'Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.'
        );
      }
      return detail;
    }
  );
}
