# Quickstart: Kiểm thử Thẻ #22 (Upload/Camera, HITL & XAI)

```bash
cd frontend
npm install
npm run typecheck
npm run test
npm run dev
```

1. Mở `http://127.0.0.1:5173/?tab=kitchen`, bấm nút **`Quét ảnh AI`** trên thanh tủ bếp.
2. Tải ảnh thật từ máy / camera điện thoại hoặc bấm một trong 3 **Ảnh mẫu thử nhanh** (Ảnh rổ nguyên liệu có vùng `< 80%`, Ảnh dọc điện thoại có cờ `EXIF Orientation = 6`, Ảnh mờ không rõ vật thể).
3. Kiểm tra hộp giới hạn `bbox`, xác nhận hoặc đổi nhãn ở mục **`Cần kiểm tra lại (< 80%)`**, bấm **`Áp dụng vào tủ bếp`** và đối chiếu thanh phân rã điểm **XAI 4 tiêu chí** trên từng thẻ món gợi ý.
