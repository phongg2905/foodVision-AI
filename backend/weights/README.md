# Model Weights Directory

Thư mục lưu trữ cục bộ tệp trọng số mô hình thị giác máy tính (ví dụ: `ingredients_best.pt`).

## Quy tắc quản lý
1. **Không đẩy tệp nhị phân lớn lên Git:** Các tệp `.pt`, `.pth`, `.onnx`, `.engine` đã được loại trừ trong `.gitignore`.
2. **Kiểm chứng toàn vẹn:** Mỗi phiên bản trọng số đưa vào sử dụng phải khớp `version`, `artifact_ref` trong bảng `ai_models` và có mã băm `SHA-256` đối chiếu trong nhật ký huấn luyện.
3. **Phạm vi nhãn:** Chỉ huấn luyện và ánh xạ các nguyên liệu có hình khối (`category != 'pantry'`).

