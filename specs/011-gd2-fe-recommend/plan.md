# Implementation Plan: [GĐ2 - UI] Danh sách Gợi ý (Ready/Missing), Tùy chọn Thời gian / Nguyên liệu chính & Trang Chi tiết Công thức

**Branch**: `feat/011-gd2-fe-recommend` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)  
**Input**: Trello Card `#11` — Owner: `TV3 — Tâm Minh`

## Summary

Mở rộng ứng dụng Frontend SPA (`frontend/`) trong phạm vi `TV3` (Single-Owner) theo thiết kế chuẩn **NEWTASTE** (`#EFE6D8` Warm Almond Cream, `#E87838` Spiced Saffron, `#181512` Deep Espresso, `#1E8E6E`/`#00C48C` Herb Emerald, font `Fraunces` + `Plus Jakarta Sans`):
1. Mở rộng `features/search/` (Tủ Bếp) hỗ trợ tùy chọn không bắt buộc **nguyên liệu chính ưu tiên (`main_ingredient_ids`)** và **thời gian mong muốn (`desired_hours`)** trước khi bấm *"Gợi ý món ăn"*.
2. Xây dựng **Màn hình Kết quả Gợi ý (`features/recommend/`)** gọi `POST /api/v1/recommendations` (`v1.1.0`), phân tách rõ khu vực **"Nấu được ngay" (`ready`)** và **"Còn thiếu nguyên liệu" (`missing`)**, giải quyết UUID sang tên tiếng Việt cho badge khớp/thiếu, hiển thị điểm MCDA 4 tiêu chí (`C, G, T, P`), giải thích `explanation_vi` và bộ lọc `cuisine_codes`, `max_total_minutes`, `include_missing`, `diversify` (MMR).
3. Xây dựng **Trang Chi tiết Công thức (`features/recipes/RecipeDetailView.tsx`)** theo bố cục 2 cột `"CHICKEN PASTA"` của NEWTASTE gọi `GET /api/v1/recipes/{recipe_id}`: hiển thị `prep_minutes`, `cook_minutes` (lưu ý `BR-05`), `total_minutes`, tách nhóm `pantry` / non-pantry, các bước `steps`, nhãn dinh dưỡng định tính + `source_urls`, nguồn/bản quyền và nguyên văn tuyên bố miễn trừ `BR-03` (`TC-15`).

## Constitution Check

- [x] **I. Spec-Driven & Contract-First**: Toàn bộ DTO và request body khớp 100% [OpenAPI Contract](../../docs/03-api/openapi.yaml) và [Backend Recommendation Schemas](../../backend/app/schemas/recommendations.py) (`extra="forbid"`, không gửi trường thừa).
- [x] **II. Kiến trúc Modular Monolith & Tách biệt Trách nhiệm**: Mã nguồn tách bạch theo `features/search/`, `features/recommend/`, `features/recipes/`, `shared/api/`.
- [x] **III. An toàn Thực phẩm & Không Bịa đặt**: Không bịa công thức khi rỗng (`TC-34`), không bịa `kcal`/`gram` (`BR-03`), hiển thị nguyên văn tuyên bố miễn trừ trách nhiệm (`TC-15`).
- [x] **IV. Xử lý Tiếng Việt & Chịu lỗi**: Giao diện 100% tiếng Việt chuẩn UTF-8 (`NFR-12`), hỗ trợ chế độ fallback khi Backend chưa chạy và bắt lỗi `4xx` (`404`, `422`) hiển thị thân thiện.
- [x] **V. Phạm vi Single-Owner**: Chỉ thay đổi trong `frontend/` và `specs/011-gd2-fe-recommend/`. Tuyệt đối không sửa `backend/`, `supabase/`, `docs/`.

## Project Structure

```text
specs/011-gd2-fe-recommend/
├── spec.md
├── plan.md
├── tasks.md
├── quickstart.md
└── contracts/
    └── ui-api-contracts.md

frontend/src/
├── App.tsx
├── shared/
│   ├── api/
│   │   ├── client.ts                     # + apiPostWithFallback & dual FastAPI/ErrorResponse error parser
│   │   ├── types.ts                      # + RecommendRequest/Response, RecipeDetail, NutritionEvidence
│   │   ├── mockData.ts                   # + MOCK_RECIPE_DETAILS (8 món), nutrition_evidence & getIngredientNameById
│   │   ├── recipesApi.ts                 # + getRecipeById
│   │   └── recommendationsApi.ts         # + postRecommendations & ADR-013/MMR offline fallback
│   └── components/
│       └── AppLayout.tsx                 # + tab "Gợi ý món ăn" (desktop & mobile)
├── features/
│   ├── search/
│   │   ├── IngredientKitchenView.tsx     # + mainIngredientIds & desiredMinutes selectors + slug UUID sync
│   │   └── components/
│   │       └── SelectedIngredientsList.tsx # + toggle ★ ưu tiên món chính trên từng chip
│   ├── recommend/
│   │   ├── index.ts
│   │   ├── RecommendationResultsView.tsx
│   │   ├── components/
│   │   │   ├── RecommendationFilterBar.tsx
│   │   │   └── RecommendationCard.tsx
│   │   └── __tests__/
│   │       └── RecommendationResultsView.test.tsx
│   └── recipes/
│       ├── RecipeCatalogView.tsx         # + onSelectRecipe
│       ├── RecipeDetailView.tsx          # NEW: Hero 2 cột NEWTASTE, tách pantry/main, steps, nutrition & BR-03
│       ├── components/
│       │   └── RecipeCard.tsx            # + clickable onSelectRecipe
│       └── __tests__/
│           └── RecipeDetailView.test.tsx
└── __tests__/
    └── AppRecommendFlow.test.tsx
```
