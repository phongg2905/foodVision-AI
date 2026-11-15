# Implementation Plan: [GĐ1 - UI] Dựng khung Frontend React + Tailwind, Giao diện Tra cứu Công thức, Tìm kiếm Tiếng Việt & Thanh 5 Gia vị Pantry

**Branch**: `feat/018-gd1-fe-ui` | **Date**: 2026-04-11 | **Spec**: [specs/018-gd1-fe-ui/spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-gd1-fe-ui/spec.md` (Trello Card `#18` — Owner: `TV3 Tâm Minh`)

## Summary

Khởi tạo ứng dụng Frontend SPA (`frontend/`) sử dụng **React 18 + TypeScript 5 + Vite + Tailwind CSS** theo đúng cấu trúc kiến trúc đã khóa trong [`docs/02-architecture/system-architecture.md`](../../docs/02-architecture/system-architecture.md) và hợp đồng API [`docs/03-api/openapi.yaml`](../../docs/03-api/openapi.yaml). Bản giao bao gồm:
1. Khung ứng dụng responsive trên 3 mốc viewport (`360px`, `768px`, `1366px` — `NFR-01`, `NFR-12`) và tầng HTTP client có định kiểu (`shared/api/`) kèm chế độ fallback dữ liệu chuẩn OpenAPI khi Backend của `TV2` chưa khởi chạy.
2. Màn hình **Tra cứu công thức (`features/recipes/`)** kết nối `GET /api/v1/recipes` với bộ lọc từ khóa tiếng Việt `q` (có/không dấu), nền ẩm thực `cuisine_code` (`VN`, `EU`, `US`), thời gian tối đa `max_total_minutes` (`<= 15`, `<= 30`, `<= 60` phút) và phân trang (`limit`, `offset`, `total`) (`FR-01`, `AC-01`, `AC-02`).
3. Khu vực **Tìm kiếm & chọn nguyên liệu chính thủ công dự phòng (`features/search/`)** kết nối `GET /api/v1/ingredients?q=&exclude_pantry=true`, hỗ trợ tiếng Việt có dấu/không dấu và từ đồng nghĩa vùng miền (`đậu hũ`/`đậu phụ`, `bắp`/`ngô`, `dưa leo`/`dưa chuột`, `thịt heo`/`thịt lợn`), tự động khử trùng lặp UUID trong `ingredient_ids`, và khóa nút *"Gợi ý món ăn"* khi `ingredient_ids` rỗng (`FR-18`, `AC-07`, `AC-08`).
4. **Thanh bật/tắt 5 gia vị sẵn có trong bếp (`category = 'pantry'`)** (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) mặc định `checked` (`excluded_pantry_ids = []`) và tự động cập nhật mảng UUID `excluded_pantry_ids` khi người dùng bỏ chọn/chọn lại (`FR-05`, `ADR-008`).

## Technical Context

**Language/Version**: TypeScript `5.x`, Node.js `>= 20.x`, React `18.3+`  
**Primary Dependencies**: `react`, `react-dom`, `lucide-react` (icons), `tailwindcss`, `postcss`, `autoprefixer`, `vite`  
**Storage**: N/A ở tầng DB (Frontend SPA quản lý state bằng React hooks; gọi REST API `/api/v1/recipes` và `/api/v1/ingredients`)  
**Testing**: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`  
**Target Platform**: Trình duyệt Web trên Mobile (`360px`), Tablet (`768px`), và Desktop (`1366px`)  
**Project Type**: Single-Page Web Application (`frontend/`) trong kho mã nguồn Monorepo  
**Performance Goals**: Debounce tìm kiếm `250ms`, phản hồi tương tác lọc/chọn nguyên liệu tức thời, hỗ trợ luồng hoàn tất dưới 3 phút (`NFR-02`)  
**Constraints**: Chỉ làm việc trong phạm vi `frontend/` và `specs/018-gd1-fe-ui/` (quyền sở hữu của `TV3`); tuyệt đối không chỉnh sửa `backend/` hoặc `supabase/`; tuân thủ 100% tên trường schema của `docs/03-api/openapi.yaml` (`name_vi`, `cover_image_url`, `cuisine_code`, `prep_minutes`, `cook_minutes`, `total_minutes`, `ingredient_ids`, `excluded_pantry_ids`).  
**Scale/Scope**: 4 User Stories (`US1`–`US4`), 9 Functional Requirements (`FR-01.1`..`FR-05.2`), 12–15 React components/modules và bộ kiểm thử tự động Vitest bao phủ toàn bộ Acceptance Criteria (`AC-01`, `AC-02`, `AC-07`, `AC-08`, `FR-05`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Spec-Driven & Contract-First**: Toàn bộ DTO (`Ingredient`, `PagedIngredients`, `RecipeSummary`, `PagedRecipes`, `ErrorResponse`) và query params (`q`, `cuisine_code`, `max_total_minutes`, `category`, `exclude_pantry`, `limit`, `offset`) bám sát 100% [`docs/03-api/openapi.yaml`](../../docs/03-api/openapi.yaml).
- [x] **II. Kiến trúc Modular Monolith & Tách biệt Trách nhiệm**: Đặt toàn bộ mã nguồn UI trong `frontend/src/` với phân tách rõ `features/*` và `shared/api/*` theo đúng [`docs/02-architecture/system-architecture.md`](../../docs/02-architecture/system-architecture.md).
- [x] **III. An toàn Thực phẩm & Không Bịa đặt**: Hiển thị chính xác dữ liệu từ điển nguyên liệu và công thức chuẩn; chỉ tính đúng 5 gia vị `pantry` (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu* — không tính nước lọc theo `BR-04`/`ADR-008`).
- [x] **IV. Xử lý Ngôn ngữ Tiếng Việt & Khả năng Chịu lỗi**: Hỗ trợ tìm kiếm có dấu, không dấu, đồng nghĩa vùng miền, khử trùng lặp UUID trong `ingredient_ids` và khóa nút *"Gợi ý món ăn"* khi `ingredient_ids` rỗng (`AC-07`, `AC-08`).
- [x] **V. Quy ước Nhánh, Phạm vi File (Single-Owner) & Kiểm thử Chéo**: Nhánh `feat/018-gd1-fe-ui` do `TV3 (Tâm Minh)` sở hữu, chỉ chạm vào `frontend/` và `specs/018-gd1-fe-ui/`, sẵn sàng để `TV2 (Phong Phạm)` review và kiểm thử chéo.

## Project Structure

### Documentation (this feature)

```text
specs/018-gd1-fe-ui/
├── spec.md                      # Đặc tả yêu cầu tính năng (US1 - US4)
├── plan.md                      # Kế hoạch triển khai kỹ thuật (file này)
├── research.md                  # Quyết định công nghệ & chiến lược xử lý tiếng Việt/fallback
├── data-model.md                # Mô hình dữ liệu TypeScript khớp OpenAPI 3.1
├── quickstart.md                # Hướng dẫn cài đặt, chạy dev/test và kịch bản kiểm thử chéo
├── checklists/
│   └── requirements.md          # Checklist kiểm định chất lượng đặc tả (16/16 pass)
├── contracts/
│   └── ui-api-contracts.md      # Hợp đồng giao tiếp UI <-> REST API (/recipes, /ingredients)
└── tasks.md                     # Danh sách tác vụ triển khai theo thứ tự phụ thuộc
```

### Source Code (repository root)

```text
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── test/
    │   └── setup.ts
    ├── shared/
    │   ├── api/
    │   │   ├── types.ts              # DTOs khớp docs/03-api/openapi.yaml
    │   │   ├── client.ts             # HTTP client + fallback tự động khi Backend chưa bật
    │   │   ├── mockData.ts           # Dữ liệu mẫu chuẩn (5 pantry, alias vùng miền, công thức VN/EU/US)
    │   │   ├── recipesApi.ts         # GET /api/v1/recipes
    │   │   └── ingredientsApi.ts     # GET /api/v1/ingredients
    │   ├── components/
    │   │   └── AppLayout.tsx         # Header, điều hướng responsive 360px/768px/1366px
    │   └── utils/
    │       └── vietnamese.ts         # Chuẩn hóa không dấu & tra cứu alias vùng miền
    └── features/
        ├── recipes/
        │   ├── components/
        │   │   ├── RecipeFilterBar.tsx
        │   │   ├── RecipeCard.tsx
        │   │   └── RecipePagination.tsx
        │   ├── RecipeCatalogView.tsx
        │   └── __tests__/
        │       └── RecipeCatalogView.test.tsx
        ├── search/
        │   ├── components/
        │   │   ├── IngredientSearchBox.tsx
        │   │   ├── SelectedIngredientsList.tsx
        │   │   └── PantryToggleBar.tsx
        │   ├── IngredientKitchenView.tsx
        │   └── __tests__/
        │       └── IngredientKitchenView.test.tsx
        ├── scan/                     # Khung thư mục chờ Thẻ #19 (GĐ2)
        ├── recommend/                # Khung thư mục chờ Thẻ #19 (GĐ2)
        ├── auth/                     # Khung thư mục chờ Thẻ #20 (GĐ3)
        └── admin/                    # Khung thư mục chờ Thẻ #21 (GĐ4)
```

**Structure Decision**: Chọn cấu trúc Web Application tách riêng trong `frontend/` với tổ chức `src/features/{scan,search,recommend,recipes,auth,admin}` và `src/shared/api` đúng nguyên bản Mục 2.3 của [`docs/02-architecture/system-architecture.md`](../../docs/02-architecture/system-architecture.md).

## Complexity Tracking

> Không có bất kỳ vi phạm nào đối với Hiến pháp Dự án (`.specify/memory/constitution.md`). Không cần bảng giải trình ngoại lệ.
