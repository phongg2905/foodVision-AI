# Tasks: [GĐ1 - UI] Dựng khung Frontend React + Tailwind, Giao diện Tra cứu Công thức, Tìm kiếm Tiếng Việt & Thanh 5 Gia vị Pantry

**Input**: Design documents from `/specs/018-gd1-fe-ui/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/ui-api-contracts.md`, `quickstart.md`)
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/ui-api-contracts.md`
**Owner**: `TV3 — Tâm Minh` (`frontend/`) | **Cross-Tester**: `TV2 — Phong Phạm`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể thực hiện song song (khác file, không phụ thuộc tác vụ chưa hoàn thành)
- **[Story]**: Ánh xạ tới User Story trong `spec.md` (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Tất cả đường dẫn file đều nằm trong phạm vi `frontend/` hoặc `specs/018-gd1-fe-ui/` (tuân thủ nguyên tắc Single-Owner của `TV3`).

---

## Phase 1: Setup (Khởi tạo Dự án Frontend `frontend/`)

**Purpose**: Khởi tạo cấu trúc dự án React + TypeScript + Vite + Tailwind CSS + Vitest theo đúng `docs/02-architecture/system-architecture.md`.

- [X] T001 Khởi tạo `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, và `frontend/vite.config.ts` (kèm cấu hình proxy `/api/v1` và Vitest `jsdom`)
- [X] T002 [P] Cấu hình Tailwind CSS & PostCSS trong `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/index.html`, và `frontend/src/index.css`
- [X] T003 [P] Tạo file biến môi trường mẫu `frontend/.env.example` và cấu hình kiểm thử `frontend/src/test/setup.ts`
- [X] T004 [P] Tạo khung thư mục feature-sliced (`scan`, `search`, `recommend`, `recipes`, `auth`, `admin`) trong `frontend/src/features/` theo `system-architecture.md`

---

## Phase 2: Foundational (Hợp đồng API OpenAPI, Chuẩn hóa Tiếng Việt & Mock Fallback)

**Purpose**: Hạ tầng dùng chung bắt buộc phải hoàn tất trước khi xây dựng các màn hình User Story.

**⚠️ CRITICAL**: Hoàn tất Phase 2 trước khi bắt đầu Phase 3–6.

- [X] T005 Định nghĩa toàn bộ kiểu dữ liệu TypeScript (`Ingredient`, `PagedIngredients`, `RecipeSummary`, `PagedRecipes`, `CuisineCode`, `RecommendDraftPayload`, `ErrorResponse`) khớp 100% `docs/03-api/openapi.yaml` trong `frontend/src/shared/api/types.ts`
- [X] T006 [P] Xây dựng bộ tiện ích chuẩn hóa tiếng Việt không dấu và bảng từ đồng nghĩa vùng miền (`đậu hũ`/`đậu phụ`, `bắp`/`ngô`, `dưa leo`/`dưa chuột`, `thịt heo`/`thịt lợn`) trong `frontend/src/shared/utils/vietnamese.ts`
- [X] T007 Xây dựng bộ dữ liệu mẫu chuẩn OpenAPI (5 gia vị `pantry`: *Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*; danh sách nguyên liệu chính và danh mục công thức `VN`/`EU`/`US`) trong `frontend/src/shared/api/mockData.ts`
- [X] T008 Xây dựng HTTP API client hỗ trợ tự động fallback sang dữ liệu chuẩn khi Backend của `TV2` chưa khởi chạy trong `frontend/src/shared/api/client.ts`
- [X] T009 [P] Xây dựng dịch vụ gọi `GET /api/v1/recipes` (lọc theo `q`, `cuisine_code`, `max_total_minutes`, `limit`, `offset`) trong `frontend/src/shared/api/recipesApi.ts`
- [X] T010 [P] Xây dựng dịch vụ gọi `GET /api/v1/ingredients` (hỗ trợ `q`, `exclude_pantry=true` cho nguyên liệu chính và `category=pantry` cho 5 gia vị sẵn có, ngăn chặn gửi đồng thời gây lỗi `422`) trong `frontend/src/shared/api/ingredientsApi.ts`

**Checkpoint**: Tầng `shared/api/` và `shared/utils/` sẵn sàng phục vụ mọi User Story.

---

## Phase 3: User Story 1 - Tra cứu và Lọc Danh mục Công thức Món ăn (Priority: P1) 🎯 MVP

**Goal**: Cho phép người dùng tra cứu danh sách công thức món ăn theo từ khóa tiếng Việt (có/không dấu), lọc theo nền ẩm thực (`VN`, `EU`, `US`) và thời gian nấu tối đa (`<= 15`, `<= 30`, `<= 60` phút) kèm phân trang (`FR-01`, `AC-01`, `AC-02`).

**Independent Test**: Mở màn hình Tra cứu công thức, lọc theo `Món Việt` + `<= 15 phút` hoặc nhập `"ca chua"` không dấu; kiểm tra danh sách thẻ món ăn hiển thị đúng `name_vi`, `cuisine_code`, `total_minutes`, `cover_image_url` và nút `"Xóa bộ lọc"` khi kết quả rỗng.

### Implementation for User Story 1

- [X] T011 [P] [US1] Xây dựng thanh bộ lọc công thức (ô tìm kiếm từ khóa tiếng Việt `q`, bộ chọn `cuisine_code` Tất cả/VN/EU/US, bộ chọn `max_total_minutes` Tất cả/15/30/60 phút, nút Xóa bộ lọc) trong `frontend/src/features/recipes/components/RecipeFilterBar.tsx`
- [X] T012 [P] [US1] Xây dựng thẻ hiển thị tóm tắt món ăn (`name_vi`, nhãn `cuisine_code`, `prep_minutes`, `cook_minutes`, `total_minutes`, `cover_image_url` kèm ảnh dự phòng) trong `frontend/src/features/recipes/components/RecipeCard.tsx`
- [X] T013 [P] [US1] Xây dựng thanh điều khiển phân trang (`limit`, `offset`, `total`) trong `frontend/src/features/recipes/components/RecipePagination.tsx`
- [X] T014 [US1] Tích hợp màn hình Tra cứu công thức kết nối `recipesApi.listRecipes` kèm trạng thái đang tải (`skeleton`), trạng thái rỗng (`empty state` + nút `"Xóa bộ lọc"`) trong `frontend/src/features/recipes/RecipeCatalogView.tsx`

**Checkpoint**: User Story 1 (`FR-01`, `AC-01`, `AC-02`) hoạt động hoàn chỉnh và độc lập.

---

## Phase 4: User Story 2 - Tìm kiếm & Chọn Nguyên liệu Chính bằng Tiếng Việt Dự phòng (Priority: P1)

**Goal**: Cho phép người dùng tìm kiếm nguyên liệu chính bằng tiếng Việt có dấu, không dấu hoặc từ đồng nghĩa vùng miền (`GET /api/v1/ingredients?q=&exclude_pantry=true`), tự động khử trùng lặp UUID trong `ingredient_ids`, và khóa nút *"Gợi ý món ăn"* khi `ingredient_ids` rỗng (`FR-18`, `AC-07`, `AC-08`).

**Independent Test**: Tìm và chọn `"Đậu hũ"`, sau đó gõ `"đậu phụ"` hoặc `"dau hu"` để xác nhận hệ thống không thêm trùng UUID vào `ingredient_ids`; xóa hết nguyên liệu để xác nhận nút *"Gợi ý món ăn"* bị khóa (`disabled`).

### Implementation for User Story 2

- [X] T015 [P] [US2] Xây dựng ô tìm kiếm nguyên liệu chính (`exclude_pantry=true`) hỗ trợ gợi ý tiếng Việt có/không dấu/đồng nghĩa vùng miền và đánh dấu nguyên liệu đã chọn trong `frontend/src/features/search/components/IngredientSearchBox.tsx`
- [X] T016 [P] [US2] Xây dựng danh sách thẻ (chips) nguyên liệu chính đã chọn (`ingredient_ids` duy nhất, cho phép xóa từng món hoặc xóa tất cả) trong `frontend/src/features/search/components/SelectedIngredientsList.tsx`

**Checkpoint**: Logic tìm kiếm nguyên liệu chính, khử trùng lặp UUID (`AC-07`) và kiểm soát rỗng (`AC-08`) sẵn sàng.

---

## Phase 5: User Story 3 - Thanh Bật/Tắt 5 Gia vị Sẵn có trong Bếp (`Pantry`) (Priority: P1)

**Goal**: Hiển thị thanh 5 gia vị cơ bản (`category = 'pantry'`: *Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) mặc định được tích chọn (`excluded_pantry_ids = []`), cho phép bật/tắt từng gia vị để cập nhật mảng `excluded_pantry_ids` và kết hợp với `ingredient_ids` tạo payload gợi ý món ăn (`FR-05`, `ADR-008`).

**Independent Test**: Kiểm tra 5 gia vị pantry mặc định đều ở trạng thái bật (`excluded_pantry_ids = []`), bỏ chọn *Nước mắm* và kiểm tra UUID của *Nước mắm* xuất hiện trong `excluded_pantry_ids`.

### Implementation for User Story 3

- [X] T017 [P] [US3] Xây dựng thanh bật/tắt 5 gia vị sẵn có trong bếp (`category = 'pantry'`, mặc định `checked`, cập nhật `excluded_pantry_ids` và nút đặt lại mặc định) trong `frontend/src/features/search/components/PantryToggleBar.tsx`
- [X] T018 [US3] Tích hợp màn hình Bếp & Chọn nguyên liệu kết hợp `IngredientSearchBox`, `SelectedIngredientsList`, `PantryToggleBar` và nút hành động *"Gợi ý món ăn"* (khóa khi `ingredient_ids` rỗng theo `AC-08`, tạo payload `{ ingredient_ids, excluded_pantry_ids }` chuẩn OpenAPI khi kích hoạt) trong `frontend/src/features/search/IngredientKitchenView.tsx`

**Checkpoint**: User Story 2 & User Story 3 (`FR-18`, `FR-05`, `AC-07`, `AC-08`) hoạt động đồng bộ.

---

## Phase 6: User Story 4 - Khung Giao diện Điều hướng Đa Thiết bị Responsive (Priority: P2)

**Goal**: Hoàn thiện khung điều hướng chung (`AppLayout`, `App.tsx`) hiển thị chuẩn trên Mobile (`360px`), Tablet (`768px`), và Desktop (`1366px`), kết nối mượt mà giữa chế độ **Tra cứu công thức** và **Chọn nguyên liệu & Bếp của bạn** (`NFR-01`, `NFR-12`).

**Independent Test**: Kiểm tra giao diện trên 3 mốc viewport `360px`, `768px`, `1366px`, chuyển đổi qua lại giữa các tab mà không mất trạng thái nguyên liệu đã chọn và không bị vỡ khung ngang.

### Implementation for User Story 4

- [X] T019 [US4] Xây dựng khung bố cục điều hướng responsive (`360px`, `768px`, `1366px`) hiển thị số lượng nguyên liệu đã chọn trên thanh điều hướng trong `frontend/src/shared/components/AppLayout.tsx`
- [X] T020 [US4] Kết nối toàn bộ luồng điều hướng ứng dụng giữa `RecipeCatalogView` và `IngredientKitchenView` trong `frontend/src/App.tsx` và `frontend/src/main.tsx`

**Checkpoint**: Toàn bộ 4 User Stories được tích hợp vào ứng dụng hoàn chỉnh.

---

## Phase 7: Polish, Automated Tests & Cross-Testing Readiness

**Purpose**: Viết kiểm thử tự động xác minh toàn bộ Acceptance Criteria (`AC-01`, `AC-02`, `AC-07`, `AC-08`, `FR-05`) và kiểm tra build/typecheck sạch 100% trước khi tạo PR cho `TV2 Phong Phạm` review.

- [X] T021 [P] Viết kiểm thử tự động cho màn hình Tra cứu công thức (`AC-01`, `AC-02`: lọc theo `q`, `cuisine_code`, `max_total_minutes` và trạng thái rỗng) trong `frontend/src/features/recipes/__tests__/RecipeCatalogView.test.tsx`
- [X] T022 [P] Viết kiểm thử tự động cho màn hình Chọn nguyên liệu & Thanh 5 gia vị Pantry (`AC-07`, `AC-08`, `FR-05`: tìm kiếm tiếng Việt không dấu/đồng nghĩa vùng miền, chống trùng lặp UUID `ingredient_ids`, khóa nút *"Gợi ý món ăn"* khi rỗng, bật/tắt `excluded_pantry_ids`) trong `frontend/src/features/search/__tests__/IngredientKitchenView.test.tsx`
- [X] T023 Cài đặt dependencies (`npm install`) và chạy kiểm tra chất lượng toàn diện (`npm run typecheck`, `npm run test`, `npm run build`) tại thư mục `frontend/`

---

## Dependencies & Execution Order

1. **Setup (Phase 1: T001–T004)** → Tạo khung dự án `frontend/`.
2. **Foundational (Phase 2: T005–T010)** → Xây dựng kiểu dữ liệu OpenAPI, chuẩn hóa tiếng Việt + alias vùng miền, và API client.
3. **User Stories (Phase 3–6: T011–T020)** → Triển khai `US1` (Tra cứu công thức), `US2` (Tìm kiếm & chọn nguyên liệu chính), `US3` (Thanh 5 gia vị Pantry), và `US4` (Layout điều hướng responsive).
4. **Polish & Verification (Phase 7: T021–T023)** → Chạy kiểm thử tự động Vitest và build production.
