/**
 * Định nghĩa kiểu dữ liệu (DTOs) khớp 100% với docs/03-api/openapi.yaml (v0.9.1-draft)
 */

export type IngredientCategory =
  | 'vegetable'
  | 'protein'
  | 'seafood'
  | 'spice'
  | 'pantry'
  | 'other';

export interface Ingredient {
  id: string;
  slug: string;
  name_vi: string;
  category: IngredientCategory;
  is_active: boolean;
}

export interface PagedIngredients {
  items: Ingredient[];
  total: number;
  limit: number;
  offset: number;
}

export type CuisineCode = 'VN' | 'EU' | 'US';

export interface RecipeSummary {
  id: string;
  slug: string;
  name_vi: string;
  cuisine_code: CuisineCode;
  prep_minutes: number;
  cook_minutes: number;
  total_minutes: number;
  cover_image_url: string | null;
}

export interface PagedRecipes {
  items: RecipeSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ErrorDetail {
  field: string;
  reason: string;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ErrorDetail[];
    trace_id: string;
  };
}

export type MaxDurationFilter = 15 | 30 | 60 | null;

export interface RecipeListParams {
  q?: string;
  cuisine_code?: CuisineCode | null;
  max_total_minutes?: MaxDurationFilter;
  limit?: number;
  offset?: number;
}

export interface IngredientListParams {
  q?: string;
  category?: IngredientCategory;
  exclude_pantry?: boolean;
  limit?: number;
  offset?: number;
}

export interface RecommendDraftPayload {
  ingredient_ids: string[];
  excluded_pantry_ids: string[];
  cuisine_code?: CuisineCode;
  max_total_minutes?: number;
}
