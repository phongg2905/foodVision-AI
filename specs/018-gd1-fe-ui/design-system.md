# FoodVision AI — Shared UI/UX Design System (GĐ1 - Card `#18`)

**Branch**: `feat/018-gd1-fe-ui`  
**Owner**: `TV3 — Tâm Minh`  
**Status**: Locked & Approved (`7/7` Components)

---

## 1. Tổng quan Nguồn Tham khảo Thực tế Đã Chốt (`7/7` Thành phần)

Toàn bộ Design System của dự án **FoodVision AI** được xây dựng dựa trên các bản thiết kế Website Desktop & UI Kit thực tế đã được duyệt và lưu trữ tại [`specs/018-gd1-fe-ui/references/`](./references/):

| Hạng mục | Thành phần Giao diện | File Tham khảo Đã Chốt | Nguồn gốc Thiết kế |
| :--- | :--- | :--- | :--- |
| **Mục `1A`** | **Website Header / Top Navbar** (`AppLayout.tsx`) | [web-header-1-dribbble-food-header.png](./references/web-header-1-dribbble-food-header.png) | [Dribbble — Fodium Food Web Header](https://dribbble.com/shots/20443391-Website-UI-Food-web-header) |
| **Mục `1B`** | **Website Footer** (`AppLayout.tsx`) | [web-footer-6-dribbble-clean-web-footer.png](./references/web-footer-6-dribbble-clean-web-footer.png) | [Dribbble — Editorial Two-Tier Clean Footer](https://cdn.dribbble.com/userupload/14150766/file/original-bd874805e7d4d57c348b151c5d205c96.png?resize=1600x1200) |
| **Mục `2`** | **Bảng màu, Font chữ & Card Món ăn** (`RecipeCard.tsx`) | [web-6-newtaste-recipe-website.jpg](./references/web-6-newtaste-recipe-website.jpg) | [Dribbble — New Taste Recipe Website UI](https://dribbble.com/) |
| **Mục `3`** | **Thanh Bộ lọc & Tìm kiếm Công thức** (`RecipeFilterBar.tsx`) | [muc3-filter-3-dribbble-search-website.jpg](./references/muc3-filter-3-dribbble-search-website.jpg) | [Dribbble — Seatwave Search & Filter Website UI](https://dribbble.com/shots/27856567-Search-UI-Website-Design) |
| **Mục `4`** | **Thanh Phân trang** (`RecipePagination.tsx`) | [muc4-page-1-dribbble-pagination-ui.jpg](./references/muc4-page-1-dribbble-pagination-ui.jpg) *(Hàng thứ 5)* | [Dribbble — Pagination UI Design](https://dribbble.com/shots/22435344-Pagination-UI) |
| **Mục `5`** | **Ô Tìm kiếm Nguyên liệu & Bố cục Bếp 2 Khối Hợp Nhất** (`IngredientSearchBox.tsx`, `IngredientKitchenView.tsx`) | [supercook-web-2.png](./references/supercook-web-2.png) & [pin-web-4-3.png](./references/pin-web-4-3.png) | SuperCook Pantry Search + Unified 2-Panel Kitchen Layout |
| **Mục `6`** | **Danh sách Tag Nguyên liệu Đã chọn** (`SelectedIngredientsList.tsx`) | [muc6-tags-2-dribbble-react-chips-kit.png](./references/muc6-tags-2-dribbble-react-chips-kit.png) | [Dribbble — Figma React Design System Chips Kit](https://dribbble.com/shots/13386103-Figma-React-design-system-UI-kit-Chips-design-components) |
| **Mục `7`** | **Thanh 5 Gia vị Pantry** (`PantryToggleBar.tsx`) | [muc7-pantry-9-pinterest-checkbox-cards-kit.jpg](./references/muc7-pantry-9-pinterest-checkbox-cards-kit.jpg) | [Pinterest — Checkboxes & ON/OFF Switches Kit](https://www.pinterest.ca/pin/4925880833385318/) |

---

## 2. Design Tokens (Màu sắc, Typography, Bo góc & Đổ bóng)

### 2.1. Bảng màu Chủ đạo (`web-6-newtaste-recipe-website.jpg` — *New Taste*)
- **Nền trang chính (`bg-canvas`)**: `#EFE6D8` (Warm Almond Cream / Kem Hạnh Nhân Ấm).
- **Bề mặt khối phụ / Highlight (`bg-blush`)**: `#F5EFE6` / `#FAF7F2` (Warm Cream Surface).
- **Bề mặt thẻ (`bg-surface`)**: `#FFFFFF` (Trắng tinh khiết) đi kèm viền `#DFD3C3`.
- **Màu nhấn chính (`primary` / Spiced Saffron Orange)**:
  - Default: `#E87838`
  - Hover / Active: `#D16426`
- **Màu trạng thái Có sẵn / Thảo mộc (`herb` / Emerald — dùng cho `muc7-pantry-9`)**:
  - Checked / ON: `#00C48C`
  - Text Checked: `#1E8E6E`
- **Màu chữ (`text`)**:
  - Primary Heading: `#181512` (Deep Espresso Charcoal)
  - Body / Secondary: `#6E655C` (Warm Taupe)
  - Muted / Caption: `#8C8277`

### 2.2. Typography
- **Font tiêu đề thương hiệu & điểm nhấn (`font-serif`)**: `'Playfair Display', Georgia, Cambria, serif` (áp dụng cho Logo `FoodVision AI`, tiêu đề trang và tiêu đề món ăn trên thẻ `RecipeCard`).
- **Font giao diện & nội dung tiếng Việt (`font-sans`)**: `'Plus Jakarta Sans', 'Inter', system-ui, sans-serif` (hỗ trợ đầy đủ dấu tiếng Việt, dễ đọc trên cả 360px, 768px và 1366px).

---

## 3. Đặc tả Chi tiết Từng Thành phần (`1` → `7`)

1. **Mục `1A` — Header (`Fodium` Style)**:
   - Bên trái: Logo `FoodVision` kiểu chữ Serif đậm màu Cam Nghệ Tây (`#E87838`) kèm hậu tố `AI`.
   - Chính giữa: Thanh điều hướng chữ in hoa giãn cách chữ rộng (`tracking-widest uppercase text-xs font-bold`).
   - Bên phải: Cụm nút chuyển nhanh trạng thái Bếp (`Chọn nguyên liệu & Bếp` kèm số đếm) và nút icon vuông màu Cam (`bg-[#E87838] text-white rounded-lg`).
2. **Mục `1B` — Footer (`Editorial Two-Tier` Style)**:
   - Đặt trong khung thẻ trắng bo góc lớn (`rounded-3xl border border-[#DFD3C3] bg-white p-8 shadow-sm`) chia làm 3 tầng bằng đường kẻ ngang mảnh.
3. **Mục `2` — Card Món ăn (`New Taste` Style — `web-6-newtaste-recipe-website.jpg`)**:
   - Đĩa món ăn tròn lớn (`h-32 w-32 rounded-full`) đặt chính giữa phía trên, nhô ra khỏi cạnh trên của thẻ trắng (`pt-16`).
   - Thẻ trắng bo góc bất đối xứng (`rounded-tl-[26px] rounded-tr-[54px] rounded-bl-[54px] rounded-br-[26px]`), tiêu đề món ăn Serif căn giữa, mô tả ngắn 3 dòng căn giữa, cùng hàng thông số thời gian nấu & nền ẩm thực ở đáy thẻ.
4. **Mục `3` — Thanh Bộ lọc & Tìm kiếm Công thức (`Seatwave` Style)**:
   - Khung ngang 4 cột: `[Ô nhập từ khóa | Chọn nền ẩm thực (VN, EU, US) | Chọn thời gian tối đa (15, 30, 60 phút) | Nút Tìm kiếm]`, không có hàng nút lọc lặp lại bên dưới.
5. **Mục `4` — Thanh Phân trang (Hàng thứ 5 của `muc4-page-1`)**:
   - Nút chữ `< Trang trước` và `Trang sau >` hai đầu; ở giữa là dãy nút số trang hình vuông bo góc (`h-10 w-10 rounded-lg`).
6. **Mục `5` & Bố cục Bếp — Unified 2-Panel Kitchen (`Phương án 1`)**:
   - **Khối Trái (`8/12`)**: 1 Bàn Chọn Nguyên Liệu hợp nhất gồm Ô Search Box gọn gàng ở đầu bảng (chỉ xổ dropdown gợi ý khi gõ từ khóa), hàng Pill chuyển nhóm nhanh (`Tất cả nhóm`, `Đạm & Thịt`, `Rau củ tươi`, `Hải sản`, `Rau thơm & Gia vị`), và danh sách các nhóm nguyên liệu ngăn cách bằng đường kẻ mảnh.
   - **Khối Phải (`4/12`, Sticky)**: 1 Phiếu Bếp hợp nhất chia 3 ngăn bằng đường nét đứt (`Nguyên liệu đã chọn` → `5 Gia vị sẵn có trong bếp` → `Nút Gợi ý món ăn`).
7. **Mục `6` (`muc6-tags-2`) & Mục `7` (`muc7-pantry-9`)**:
   - Chip nguyên liệu (`muc6-tags-2`): Chưa chọn nền `#EAECEE` chữ `#374151`; Đã chọn nền `#6E7781` chữ trắng kèm dấu `✓` bên trái.
   - 5 Gia vị cơ bản (`muc7-pantry-9`): Checkbox vuông bo góc `rounded-[6px]`, trạng thái Checked màu xanh ngọc `#00C48C` với chữ `#1E8E6E`.
