# Data Model (Frontend Domain & API DTOs): [GĐ1 - UI]

**Feature Branch**: `feat/018-gd1-fe-ui`  
**Date**: 2026-04-11  
**Source of Truth**: [`docs/03-api/openapi.yaml`](../../docs/03-api/openapi.yaml) (`v0.9.1-draft`)

---

## 1. Core API Entities (`frontend/src/shared/api/types.ts`)

### 1.1 `IngredientCategory` & `Ingredient`

Khớp chính xác với `components.schemas.Ingredient` trong `docs/03-api/openapi.yaml`:

```ts
export type IngredientCategory =
  | 'vegetable'
  | 'protein'
  | 'seafood'
  | 'spice'
  | 'pantry'
  | 'other';

export interface Ingredient {
  /** UUID v4 của nguyên liệu chuẩn (canonical ingredient) */
  id: string;
  /** Slug không dấu duy nhất, ví dụ: 'dau-hu', 'thit-heo', 'muoi' */
  slug: string;
  /** Tên hiển thị tiếng Việt chuẩn, ví dụ: 'Đậu hũ', 'Thịt heo', 'Muối' */
  name_vi: string;
  /** Nhóm phân loại nguyên liệu */
  category: IngredientCategory;
  /** Trạng thái kích hoạt trong từ điển */
  is_active: boolean;
}

export interface PagedIngredients {
  items: Ingredient[];
  total: number;
  limit: number;
  offset: number;
}
```

### 1.2 `CuisineCode` & `RecipeSummary`

Khớp chính xác với `components.schemas.RecipeSummary` và `PagedRecipes` trong `docs/03-api/openapi.yaml`:

```ts
export type CuisineCode = 'VN' | 'EU' | 'US';

export interface RecipeSummary {
  /** UUID v4 của công thức món ăn */
  id: string;
  /** Slug duy nhất của món ăn, ví dụ: 'canh-ca-chua-trung' */
  slug: string;
  /** Tên món ăn tiếng Việt */
  name_vi: string;
  /** Mã nền ẩm thực: Món Việt (VN), Món Âu (EU), Món Mỹ (US) */
  cuisine_code: CuisineCode;
  /** Thời gian sơ chế (phút, >= 0) */
  prep_minutes: number;
  /** Thời gian nấu (phút, >= 0) */
  cook_minutes: number;
  /** Tổng thời gian thực hiện (phút = prep_minutes + cook_minutes) */
  total_minutes: number;
  /** Đường dẫn ảnh bìa món ăn (có thể null) */
  cover_image_url: string | null;
}

export interface PagedRecipes {
  items: RecipeSummary[];
  total: number;
  limit: number;
  offset: number;
}
```

### 1.3 `ErrorResponse`

Khớp chính xác với `components.schemas.ErrorResponse` trong `docs/03-api/openapi.yaml`:

```ts
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
```

---

## 2. Frontend Filter & Selection State Models

### 2.1 `RecipeCatalogFilterState` (`features/recipes`)

Quản lý trạng thái bộ lọc và phân trang cho màn hình **Tra cứu công thức (`FR-01`)**:

```ts
export type MaxDurationFilter = 15 | 30 | 60 | null;

export interface RecipeCatalogFilterState {
  /** Từ khóa tìm kiếm tên món ăn (hỗ trợ có dấu / không dấu) */
  q: string;
  /** Bộ lọc nền ẩm thực ('VN' | 'EU' | 'US' | null cho Tất cả) */
  cuisine_code: CuisineCode | null;
  /** Thời gian nấu tối đa (15, 30, 60 phút hoặc null cho Tất cả) */
  max_total_minutes: MaxDurationFilter;
  /** Số bản ghi mỗi trang (mặc định 12, trong khoảng 1..50) */
  limit: number;
  /** Vị trí bắt đầu phân trang (mặc định 0, >= 0) */
  offset: number;
}
```

### 2.2 `IngredientSelectionState` & `RecommendDraftPayload` (`features/search`)

Quản lý trạng thái chọn nguyên liệu chính (`FR-18`) và 5 gia vị sẵn có (`FR-05`), sẵn sàng truyền sang luồng Gợi ý món ăn (`POST /api/v1/recipes/recommend` ở Thẻ `#19`):

```ts
export interface IngredientSelectionState {
  /** Danh sách nguyên liệu chính đã chọn (không trùng lặp id, category !== 'pantry') */
  selectedIngredients: Ingredient[];
  /** Danh sách 5 gia vị cơ bản trong bếp (category === 'pantry') */
  pantryItems: Ingredient[];
  /** Danh sách UUID của các gia vị pantry bị người dùng bỏ chọn (mặc định []) */
  excludedPantryIds: string[];
}

export interface RecommendDraftPayload {
  /** Mảng UUID nguyên liệu chính (minItems: 1, uniqueItems: true) */
  ingredient_ids: string[];
  /** Mảng UUID gia vị pantry bị loại trừ (mặc định: []) */
  excluded_pantry_ids: string[];
  /** Bộ lọc tùy chọn kèm theo khi gọi gợi ý */
  cuisine_code?: CuisineCode;
  max_total_minutes?: number;
}
```

---

## 3. Validation & Business Rules Invariants

1. **Quy tắc chống trùng lặp nguyên liệu chính (`AC-07`)**:
   - Mọi thao tác thêm nguyên liệu vào `selectedIngredients` đều kiểm tra theo `ingredient.id` (UUID chuẩn).
   - Dù người dùng tìm bằng tên chính (`"Đậu hũ"`), không dấu (`"dau hu"`), hay từ đồng nghĩa vùng miền (`"đậu phụ"`), kết quả trả về cùng một `id` nên mảng `ingredient_ids` luôn đảm bảo `new Set(ingredient_ids).size === ingredient_ids.length`.
2. **Quy tắc tách biệt Nguyên liệu chính và Gia vị Pantry (`FR-05`, `ADR-008`)**:
   - Ô tìm kiếm nguyên liệu chính luôn gửi `exclude_pantry=true`, đảm bảo 5 gia vị cơ bản (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) không bị trộn vào `ingredient_ids`.
   - Thanh 5 gia vị sẵn có luôn tải với `category=pantry` (không gửi `exclude_pantry=true` để tránh lỗi `422 INVALID_QUERY_PARAMS`).
3. **Quy tắc khóa nút Gợi ý món ăn (`AC-08`)**:
   - Nút *"Gợi ý món ăn"* chỉ được kích hoạt (`disabled = false`) khi `selectedIngredients.length >= 1`.
   - Việc bật/tắt các gia vị trên thanh Pantry không thể mở khóa nút *"Gợi ý món ăn"* nếu `selectedIngredients.length === 0`.
