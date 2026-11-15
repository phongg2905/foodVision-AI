# Quickstart Guide: [GĐ1 - UI] Frontend Shell, Recipe Catalog & Vietnamese Ingredient Search

**Feature Branch**: `feat/018-gd1-fe-ui`  
**Owner**: `TV3 — Tâm Minh` (`frontend/`)

---

## 1. Yêu cầu Môi trường

- **Node.js**: `>= 20.x` (khuyến nghị LTS)
- **Trình quản lý gói**: `npm` (`>= 10.x`)

---

## 2. Cài đặt & Chạy Ứng dụng Frontend

```powershell
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt dependencies
npm install

# 3. Khởi chạy máy chủ phát triển (Vite Dev Server tại http://localhost:5173)
npm run dev
```

### Cấu hình Biến môi trường (`frontend/.env.example`)

```ini
# URL gốc của Backend API (mặc định dùng proxy /api/v1 sang http://localhost:8000)
VITE_API_BASE_URL=/api/v1

# Chế độ fallback dữ liệu mẫu khi Backend của TV2 chưa bật ('auto' | 'true' | 'false')
# - 'auto' (mặc định): Gọi API thật trước; nếu mất kết nối mạng/backend chưa chạy thì tự động dùng bộ dữ liệu chuẩn OpenAPI
# - 'true': Luôn dùng bộ dữ liệu mẫu nội bộ để demo/test UI độc lập
# - 'false': Chỉ gọi API thật
VITE_API_MOCK_MODE=auto
```

---

## 3. Kiểm thử & Kiểm tra Chất lượng (Cross-Testing & CI Check)

```powershell
cd frontend

# Chạy toàn bộ Unit & Integration Tests (Vitest + React Testing Library)
npm run test

# Kiểm tra kiểu tĩnh TypeScript
npm run typecheck

# Build bản production để xác nhận không có lỗi đóng gói
npm run build
```

---

## 4. Kịch bản Kiểm thử Nghiệm thu Thủ công (Dành cho TV2 Phong Phạm Review PR)

1. **Kiểm tra Responsive Layout (`NFR-01`, `NFR-12`)**:
   - Mở `http://localhost:5173` trên trình duyệt, bật DevTools Device Toolbar ở 3 kích thước `360px` (Mobile), `768px` (Tablet) và `1366px` (Desktop).
   - Xác nhận không có thanh cuộn ngang (`horizontal overflow`) và thanh điều hướng chuyển đổi mượt giữa hai chế độ **Tra cứu công thức** và **Chọn nguyên liệu & Bếp của bạn**.
2. **Kiểm tra Tra cứu & Lọc Công thức (`FR-01`, `AC-01`, `AC-02`)**:
   - Tại tab **Tra cứu công thức**, thử lọc theo nền ẩm thực (`Món Việt`, `Món Âu`, `Món Mỹ`) và thời gian nấu tối đa (`<= 15 phút`, `<= 30 phút`, `<= 60 phút`).
   - Nhập từ khóa không dấu như `"ca chua"` hoặc `"bo luc lac"` vào ô tìm kiếm để kiểm tra kết quả khớp và nút `"Xóa bộ lọc"` khi không có món phù hợp.
3. **Kiểm tra Tìm kiếm Tiếng Việt, Đồng nghĩa Vùng miền & Chống trùng lặp (`FR-18`, `AC-07`, `AC-08`)**:
   - Chuyển sang tab **Chọn nguyên liệu (Bếp của bạn)**. Quan sát nút **"Gợi ý món ăn"** đang bị khóa (`disabled`) khi chưa chọn nguyên liệu nào.
   - Gõ `"đậu hũ"` và chọn nguyên liệu **Đậu hũ**. Nút **"Gợi ý món ăn"** lập tức được mở khóa.
   - Gõ tiếp từ đồng nghĩa vùng miền `"đậu phụ"` hoặc không dấu `"dau hu"`: hệ thống nhận diện cùng 1 nguyên liệu **Đậu hũ** (`Đã chọn`) và không tạo bản sao thứ hai trong mảng `ingredient_ids`.
   - Thử thêm với `"ngô"` → khớp **Bắp**, `"dưa chuột"` → khớp **Dưa leo**, `"thịt lợn"` → khớp **Thịt heo**.
4. **Kiểm tra Thanh 5 Gia vị Sẵn có (`FR-05`, `ADR-008`)**:
   - Quan sát thanh **5 Gia vị sẵn có trong bếp** (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) mặc định đều được bật (`excluded_pantry_ids = []`).
   - Bỏ chọn *Nước mắm* và *Hạt tiêu*, xác nhận UUID của 2 gia vị này được đưa vào danh sách loại trừ `excluded_pantry_ids` khi bấm **"Gợi ý món ăn"**.
