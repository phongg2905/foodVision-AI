# Research & Technical Decisions: [GĐ1 - UI] Frontend Shell, Recipe Catalog, Vietnamese Ingredient Search & 5-Pantry Bar

**Feature Branch**: `feat/018-gd1-fe-ui`  
**Date**: 2026-04-11  
**Owner**: `TV3 — Tâm Minh` (FE / HITL / QA Lead)

---

## 1. Frontend Build Tooling & Styling Stack

- **Decision**: Sử dụng **React 18 + TypeScript 5 + Vite 5/6 + Tailwind CSS v3/v4** trong thư mục độc lập `frontend/`.
- **Rationale**:
  - Tuân thủ tuyệt đối `docs/02-architecture/system-architecture.md` (§2.1 Frontend Web Client — React + TypeScript + Vite + Tailwind CSS) và `.specify/memory/constitution.md` (§II Kiến trúc Modular Monolith & §V Quy ước Nhánh & Phạm vi File).
  - Vite cung cấp tốc độ khởi chạy dev server tức thời và hỗ trợ cấu hình proxy `/api/v1` sang `http://localhost:8000` (FastAPI Backend của `TV2`) mà không gặp lỗi CORS khi chạy local.
  - Tailwind CSS hỗ trợ mobile-first breakpoints (`360px` base, `md: 768px`, `xl: 1280px/1366px`) đáp ứng trực tiếp `NFR-01` và `NFR-12`.
- **Alternatives Considered**:
  - *Next.js SSR*: Bị loại vì kiến trúc dự án (`system-architecture.md`) quy định SPA tĩnh triển khai trên Vercel/Cloudflare Pages kết nối REST API `/api/v1`.

---

## 2. Cấu trúc Thư mục Feature-Sliced (`frontend/src/`)

- **Decision**: Tổ chức `frontend/src/` theo đúng cấu trúc đã khóa trong `docs/02-architecture/system-architecture.md` (§2.3):
  - `src/features/recipes/`: Trang và thành phần Tra cứu công thức (`FR-01`, `AC-01`, `AC-02`).
  - `src/features/search/`: Ô tìm kiếm & chọn nguyên liệu chính thủ công dự phòng + Thanh bật/tắt 5 gia vị sẵn có (`FR-18`, `FR-05`, `AC-07`, `AC-08`).
  - `src/features/scan/`, `src/features/recommend/`, `src/features/auth/`, `src/features/admin/`: Khởi tạo sẵn khung thư mục/placeholder điều hướng để các thẻ GĐ2–GĐ4 (`#19`, `#20`, `#21`) mở rộng không gây xung đột.
  - `src/shared/api/`: HTTP client, định nghĩa kiểu dữ liệu khớp `docs/03-api/openapi.yaml`, và cơ chế fallback dữ liệu mẫu (mock mode) khi Backend của `TV2` chưa bật.
- **Rationale**: Giữ đúng ranh giới Single-Owner cho `TV3` và chuẩn bị sẵn điểm gắn kết (`RecommendDraftPayload`: `{ ingredient_ids, excluded_pantry_ids }`) cho Thẻ `#19` (`POST /api/v1/recipes/recommend`).

---

## 3. Xử lý Tiếng Việt Không Dấu, Đồng Nghĩa Vùng Miền & Chống Trùng Lặp (`FR-18`, `ADR-004`)

- **Decision**:
  1. **Primary path**: Gọi `GET /api/v1/ingredients?q=<keyword>&exclude_pantry=true&limit=20&offset=0` với debounce `250ms` để tận dụng hàm `f_unaccent()` + `ingredient_aliases` + `pg_trgm` ở tầng PostgreSQL (`ADR-004`).
  2. **Standalone Fallback / Mock path**: Khi chạy độc lập (chưa bật Backend `TV2` hoặc cấu hình `VITE_API_MOCK=true`), bộ lọc client-side trong `shared/api/mockData.ts` sử dụng chuẩn hóa Unicode NFD (`normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd')`) kết hợp bảng alias vùng miền chuẩn của `ADR-004`:
     - `đậu hũ` (`dau-hu`) ↔ `đậu phụ`, `tàu hũ`
     - `bắp` (`bap`) ↔ `ngô`, `bắp mỹ`
     - `dưa leo` (`dua-leo`) ↔ `dưa chuột`
     - `thịt heo` (`thit-heo`) ↔ `thịt lợn`, `thịt ba chỉ`
     - `hành lá` (`hanh-la`) ↔ `hành hoa`
     - `thơm` (`thom`) ↔ `dứa`, `khóm`
  3. **Chống trùng lặp UUID (`ingredient_ids`)**: Sử dụng `Map<string, Ingredient>` hoặc kiểm tra `selectedIngredients.some(item => item.id === candidate.id)` trước khi thêm. Nếu người dùng gõ `"đậu phụ"` trong khi `"Đậu hũ"` (cùng UUID `11111111-1111-4111-8111-000000000001`) đã có trong danh sách đã chọn, UI đánh dấu trạng thái *"Đã chọn"* và không thêm bản sao thứ hai.
- **Rationale**: Đảm bảo `AC-07` và `AC-08` luôn kiểm thử được 100% cả khi chạy unit/integration test độc lập của `TV3` lẫn khi tích hợp E2E với Backend của `TV2` và Database của `TV1`.

---

## 4. Quản lý Trạng thái Thanh 5 Gia vị Sẵn có (`category = 'pantry'`, `FR-05`, `ADR-008`)

- **Decision**:
  - Tải danh sách 5 gia vị pantry từ `GET /api/v1/ingredients?category=pantry&limit=10&offset=0` (gồm: *Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*; tuyệt đối không có Nước lọc theo `BR-04`).
  - Lưu trạng thái dưới dạng `excludedPantryIds: string[]`, mặc định khởi tạo là mảng rỗng `[]` (tức cả 5 gia vị đều ở trạng thái `checked = true`).
  - Khi người dùng bỏ chọn một gia vị có `id`, thêm `id` vào `excludedPantryIds`. Khi bật lại, loại bỏ `id` khỏi `excludedPantryIds`.
- **Rationale**: Khớp trực tiếp với cấu trúc request body `RecommendRequest` trong `docs/03-api/openapi.yaml` (`ingredient_ids: UUID[]`, `excluded_pantry_ids: UUID[]`).

---

## 5. Chiến lược Kiểm thử Tự động (`Vitest` + `@testing-library/react`)

- **Decision**: Cấu hình `Vitest` + `jsdom` + `@testing-library/react` + `@testing-library/user-event` trong `frontend/` để kiểm thử tự động toàn bộ tiêu chí nghiệm thu của Thẻ `#18`:
  - `AC-01`, `AC-02`: Hiển thị danh sách công thức, lọc theo `q`, `cuisine_code` (`VN`, `EU`, `US`), `max_total_minutes` (`15`, `30`, `60`), và trạng thái rỗng.
  - `AC-07`: Tìm kiếm nguyên liệu có dấu/không dấu/đồng nghĩa vùng miền (`đậu phụ` → `Đậu hũ`, `ngô` → `Bắp`) và chống trùng lặp UUID trong `ingredient_ids`.
  - `AC-08`: Nút *"Gợi ý món ăn"* bị `disabled` khi `ingredient_ids.length === 0` và mở khóa ngay khi có ít nhất 1 nguyên liệu.
  - `FR-05`: Thanh 5 gia vị pantry mặc định `checked` (`excluded_pantry_ids = []`) và cập nhật đúng mảng `excluded_pantry_ids` khi bật/tắt.
