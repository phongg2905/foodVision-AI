/**
 * Định nghĩa kiểu dữ liệu (DTOs) khớp 100% với docs/03-api/openapi.yaml (v1.1.0)
 * và backend/app/schemas/{catalog,recipes,recommendations}.py (ConfigDict extra="forbid").
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

export interface RecipeIngredientView {
  ingredient_id: string;
  name_vi: string;
  category: IngredientCategory;
  is_required: boolean;
  display_quantity: string | null;
  sort_order: number;
}

export interface RecipeStepView {
  step_no: number;
  instruction: string;
  estimated_minutes: number | null;
}

export interface NutritionTag {
  id: string;
  code: string;
  name_vi: string;
  description: string | null;
  is_active?: boolean;
}

export interface NutritionEvidence {
  tag: NutritionTag;
  source_urls: string[];
  note: string | null;
}

export interface RecipeDetail extends RecipeSummary {
  description: string | null;
  country_code: string | null;
  ingredients: RecipeIngredientView[];
  steps: RecipeStepView[];
  nutrition_evidence: NutritionEvidence[];
  source_name: string | null;
  source_url: string | null;
  content_license: string | null;
}

export interface ErrorDetail {
  field?: string;
  reason?: string;
  [key: string]: unknown;
}

export interface ErrorResponse {
  error?: {
    code: string;
    message: string;
    details?: ErrorDetail[] | Record<string, unknown>;
    trace_id: string;
  };
  code?: string;
  message?: string;
  details?: ErrorDetail[] | Record<string, unknown>;
  request_id?: string;
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
  main_ingredient_ids?: string[];
  desired_hours?: number;
  cuisine_codes?: CuisineCode[];
  max_total_minutes?: MaxDurationFilter;
}

export type AvailabilityStatus = 'ready' | 'missing';

export type ReasoningStatus = 'READY' | 'UNKNOWN' | 'MISSING_CONFIRMED';

export interface ScoreBreakdown {
  C: number;
  G: number;
  T: number;
  P: number;
}

export interface ScoreContributions {
  C: number;
  G: number;
  T: number;
  P: number;
}

export interface RecommendRequest {
  ingredient_ids: string[];
  main_ingredient_ids?: string[];
  desired_hours?: number;
  allergic_ingredient_ids?: string[];
  kitchen_spice_ids?: string[] | null;
  excluded_pantry_ids?: string[];
  favorite_ingredient_ids?: string[];
  max_total_minutes?: number | null;
  cuisine_codes?: CuisineCode[];
  include_missing?: boolean;
  diversify?: boolean;
  limit?: number;
  scan_id?: string | null;
}

export interface RecommendationItem {
  recipe: RecipeSummary;
  availability: AvailabilityStatus;
  reasoning_status: ReasoningStatus;
  score: number;
  matched_ingredient_ids: string[];
  missing_required_ingredient_ids: string[];
  missing_optional_ingredient_ids: string[];
  score_breakdown: ScoreBreakdown;
  score_contributions: ScoreContributions;
  explanation_vi: string;
}

export interface RecommendResponse {
  items: RecommendationItem[];
  total: number;
  limit: number;
}
