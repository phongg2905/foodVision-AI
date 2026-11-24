# Quickstart & Cross-Testing Guide: Thẻ #11 (`[GĐ2 - UI]`)

**Chủ sở hữu:** `TV3 — Tâm Minh`  
**Kiểm thử chéo:** `TV1 — Minh Thành`

## 1. Cài đặt & Chạy Tự động (`frontend/`)

```bash
cd frontend
npm install
npm run typecheck
npm run test
npm run build
npm run dev
```

Mặc định khi chạy độc lập không có Backend, HTTP client tự fallback sang dữ liệu chuẩn OpenAPI (`mockData.ts`). Để kết nối trực tiếp Backend FastAPI (TV2) chạy tại `http://localhost:8000`:
- Bật proxy Vite (đã cấu hình `/api/v1`) hoặc cấu hình `VITE_API_BASE_URL=http://localhost:8000/api/v1` và `VITE_API_MOCK_MODE=false`.

## 2. Kịch bản Kiểm thử Chéo (`TV1 — Minh Thành`)

1. **`TC-09` & `TC-10` — Gợi ý "Nấu được ngay" (`ready`)**:
   - Mở tab **Chọn nguyên liệu & Bếp**, bấm chọn *Đậu hũ* và *Cà chua* → bấm **Gợi ý món ăn**.
   - Kiểm tra mục **"Nấu được ngay"** hiển thị món *Đậu hũ sốt cà chua* ở trên, kèm điểm số và badge nguyên liệu đã khớp.
2. **`TC-11` & `TC-32` — Phân tách "Còn thiếu nguyên liệu" (`missing`) & Tắt gia vị Pantry**:
   - Quay lại Tủ bếp, bỏ tích **Nước mắm** hoặc **Muối**, giữ nguyên *Cà chua* → bấm **Gợi ý món ăn**.
   - Kiểm tra các món yêu cầu gia vị vừa tắt chuyển xuống nhóm **"Còn thiếu nguyên liệu"** và gắn badge cảnh báo đúng tên nguyên liệu/gia vị cần mua thêm.
3. **`TC-12` & `TC-35` — Tùy chọn Món chính (`main_ingredient_ids`) & Thời gian mong muốn (`desired_hours`)**:
   - Đánh dấu `★` ưu tiên *Đậu hũ* làm món chính và chọn thời gian mong muốn **15 phút** (gửi `desired_hours: 0.25`).
   - Kiểm tra phần phân rã điểm XAI (`C, G, T, P`) cập nhật lại ngay trên thẻ kết quả.
4. **`TC-13`, `TC-14`, `TC-33`, `DEF-10` — Bộ lọc Kết quả Gợi ý**:
   - Lọc ẩm thực `Món Việt (VN)`, lọc `≤ 15 phút`, bật **Chỉ hiện món nấu được ngay** (`include_missing = false`) và **Đa dạng hóa thực đơn (MMR)** (`diversify = true`).
5. **`TC-03` & `TC-15` — Chi tiết Công thức & Dinh dưỡng An toàn**:
   - Bấm mở chi tiết món *Đậu hũ sốt cà chua* và món *Bắp ngọt xào bơ tỏi kiểu Mỹ* (không có tag dinh dưỡng).
   - Xác minh: (a) hiển thị `Sơ chế`, `Nấu & chờ` (kèm chú thích `BR-05`), `Tổng cộng`; (b) tách riêng **Nguyên liệu** và **Gia vị cần chuẩn bị**; (c) hiển thị các bước đánh số; (d) link `source_urls` hợp lệ; (e) **không có con số `kcal`/`gram` suy diễn từ ảnh**; (f) luôn hiển thị nguyên văn tuyên bố miễn trừ `BR-03`.
6. **`UI-01` & `UI-03` — Responsive `360px / 768px / 1366px` & Tiếng Việt 100%**:
   - Kiểm tra 3 độ rộng trên DevTools: không vỡ bố cục, không tràn ngang.
