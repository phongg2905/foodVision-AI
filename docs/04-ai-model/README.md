# 04 — AI Model Design (`1.0.0` — Nhận thức Thị giác & HITL)

- [ai-model-design.md](ai-model-design.md): kiến trúc nhận diện YOLO (Thành phần 01), tiền xử lý `EXIF Orientation` & xóa `EXIF/GPS` ([`ADR-010`](../07-decisions/ADR-010-image-exif-and-validation-errors.md)), lớp hỗ trợ ứng viên CLIP/VLM cho vùng ảnh khó (Thành phần 02), cơ chế cảnh báo xác nhận Human-in-the-loop (Thành phần 14), quy tắc bất biến & rollback model version.
- [label-catalog.md](label-catalog.md): bộ nhãn đề xuất ban đầu 20 lớp (`category != 'pantry'`), liên kết chuẩn hóa tiếng Việt/`pg_trgm`/alias (Thành phần 13) và vòng đời nghiệm thu nhãn.
- [dataset-and-evaluation.md](dataset-and-evaluation.md): kế hoạch thu thập/gán nhãn, chia tập `70/15/15` chống rò rỉ cảnh chụp, công thức `IoU` và `mAP@50:95` (Thành phần 12), quy tắc minh bạch `NFR-11` (cấm loại lớp yếu sau test) và kiểm soát giấy phép.

**Trạng thái:** chưa huấn luyện, chưa đo độ chính xác thực tế, chưa kiểm tra dữ liệu tập ảnh; các mục tiêu là **đề xuất kỹ thuật chờ nhóm và Giảng viên hướng dẫn phê duyệt**. Không suy ra YOLO pretrained đã nhận diện được toàn bộ nguyên liệu tiếng Việt, và không khẳng định mô hình YOLO tự cập nhật trọng số tức thời sau một lần người dùng sửa nhãn trên giao diện.
