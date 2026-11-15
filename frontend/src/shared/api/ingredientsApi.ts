import { apiGetWithFallback, ApiClientError } from './client';
import {
  MOCK_ALL_INGREDIENTS,
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from './mockData';
import { IngredientListParams, PagedIngredients } from './types';
import { matchesIngredientQuery } from '../utils/vietnamese';

/**
 * Bộ lọc dự phòng cho GET /api/v1/ingredients hỗ trợ tiếng Việt có dấu, không dấu
 * và từ đồng nghĩa vùng miền (ADR-004, FR-18, AC-07).
 */
export function filterMockIngredients(
  params: IngredientListParams
): PagedIngredients {
  if (params.category === 'pantry' && params.exclude_pantry === true) {
    throw new ApiClientError(
      422,
      'INVALID_QUERY_PARAMS',
      'Không thể kết hợp đồng thời category=pantry và exclude_pantry=true.'
    );
  }

  const limit = Math.min(Math.max(params.limit ?? 20, 1), 50);
  const offset = Math.max(params.offset ?? 0, 0);

  let pool = MOCK_ALL_INGREDIENTS;
  if (params.exclude_pantry) {
    pool = MOCK_MAIN_INGREDIENTS;
  } else if (params.category) {
    pool = MOCK_ALL_INGREDIENTS.filter(
      (item) => item.category === params.category
    );
  }

  const query = params.q?.trim() ?? '';
  const filtered = query
    ? pool.filter((item) => matchesIngredientQuery(item, query))
    : pool;

  return {
    items: filtered.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

/**
 * Tìm kiếm nguyên liệu chính (luôn gửi exclude_pantry=true theo FR-18 & AC-07).
 */
export async function searchMainIngredients(
  query: string,
  limit = 20,
  offset = 0
): Promise<PagedIngredients> {
  const trimmed = query.trim();
  return apiGetWithFallback<PagedIngredients>(
    '/ingredients',
    {
      q: trimmed.length > 0 ? trimmed : undefined,
      exclude_pantry: true,
      limit,
      offset,
    },
    () =>
      filterMockIngredients({
        q: trimmed,
        exclude_pantry: true,
        limit,
        offset,
      })
  );
}

/**
 * Tải danh sách 5 gia vị sẵn có trong bếp (category=pantry, KHÔNG gửi exclude_pantry=true)
 * theo FR-05 & ADR-008.
 */
export async function listPantryIngredients(): Promise<PagedIngredients> {
  return apiGetWithFallback<PagedIngredients>(
    '/ingredients',
    {
      category: 'pantry',
      limit: 10,
      offset: 0,
    },
    () => ({
      items: MOCK_PANTRY_INGREDIENTS,
      total: MOCK_PANTRY_INGREDIENTS.length,
      limit: 10,
      offset: 0,
    })
  );
}
