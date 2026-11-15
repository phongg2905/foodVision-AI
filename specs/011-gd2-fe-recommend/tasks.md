# Tasks: [GĐ2 - UI] Danh sách Gợi ý (Ready/Missing), Tùy chọn Thời gian / Nguyên liệu chính & Chi tiết Công thức

- [x] **T01** Tạo nhánh `feat/011-gd2-fe-recommend` từ `main` (`1fde35c`)
- [x] **T02** Khởi tạo bộ tài liệu Spec Kit tại `specs/011-gd2-fe-recommend/`
- [x] **T03** Mở rộng `frontend/src/shared/api/types.ts` và `client.ts` (`RecommendRequest/Response`, `RecipeDetail`, `NutritionEvidence`, `apiPostWithFallback`)
- [x] **T04** Bổ sung dữ liệu chi tiết `MOCK_RECIPE_DETAILS`, `getRecipeById` và `recommendationsApi.ts` chuẩn `ADR-013` + `MMR`
- [x] **T05** Nâng cấp `SelectedIngredientsList.tsx` & `IngredientKitchenView.tsx` hỗ trợ chọn tùy chọn món chính ưu tiên & thời gian mong muốn
- [x] **T06** Xây dựng `features/recommend/` (`RecommendationResultsView`, `RecommendationFilterBar`, `RecommendationCard`) theo thiết kế NEWTASTE
- [x] **T07** Xây dựng `RecipeDetailView.tsx` (bố cục `CHICKEN PASTA`), tách nhóm nguyên liệu/gia vị, nhãn dinh dưỡng + `source_urls` và tuyên bố miễn trừ `BR-03`
- [x] **T08** Kết nối điều hướng `App.tsx`, `AppLayout.tsx`, `RecipeCatalogView.tsx`, `RecipeCard.tsx`
- [x] **T09** Viết và chạy vượt qua bộ kiểm thử Vitest (`RecommendationResultsView.test.tsx`, `RecipeDetailView.test.tsx`, `AppRecommendFlow.test.tsx`) + `typecheck` + `build`
