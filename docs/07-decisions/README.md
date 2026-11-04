# 07 — Architecture Decision Records (`1.0.0`)

Mỗi quyết định kiến trúc ghi lại lý do và đánh đổi kỹ thuật, giúp nhóm không tranh luận lặp lại khi triển khai qua 5 giai đoạn.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [ADR-001](ADR-001-web-fastapi.md) | Tách riêng Web React và Backend Python FastAPI | Accepted |
| [ADR-002](ADR-002-supabase.md) | Sử dụng Supabase PostgreSQL (`>= 15`, `unaccent`, `pg_trgm`), Auth, Storage kèm RLS + GRANT | Accepted |
| [ADR-003](ADR-003-detection-recommendation.md) | Tách tầng nhận thức (YOLO/CLIP + HITL) khỏi hệ suy luận 3 trạng thái, MCDA, MMR & Logistic Regression | Accepted |
| [ADR-004](ADR-004-nutrition.md) | Chính sách dinh dưỡng 2 tầng: nhãn định tính (`P0`) + ước tính USDA theo định lượng chuẩn (`P1`), cấm suy gram từ ảnh | Accepted |
| [ADR-005](ADR-005-yolo-licensing.md) | Kiểm soát giấy phép Ultralytics YOLO, nguồn ảnh và bản quyền công thức | Accepted |
| [ADR-006](ADR-006-label-versioning.md) | Quản lý phiên bản `class_index` qua `ai_labels`, giữ cố định `ingredients.id` UUID | Accepted |
| [ADR-007](ADR-007-image-privacy.md) | Không lưu ảnh nguyên liệu gốc; lịch sử kết quả nhận diện theo cơ chế opt-in | Accepted |
| [ADR-008](ADR-008-pantry-ingredients-handling.md) | Cơ chế bật/tắt gia vị nền (`category = 'pantry'`) và tác động lên suy luận trạng thái & chấm điểm gợi ý | Accepted |
| [ADR-009](ADR-009-cooking-and-waiting-time.md) | Quy ước tính thời gian ướp/chờ/hầm bắt buộc vào `cook_minutes` và kiểm tra tính nhất quán | Accepted |
| [ADR-010](ADR-010-image-exif-and-validation-errors.md) | Tiền xử lý EXIF Orientation, xóa metadata GPS/EXIF và chuẩn hóa mã lỗi HTTP (`400`/`404`/`409`/`415`/`422`/`504`) | Accepted |
| [ADR-011](ADR-011-admin-role-inheritance.md) | Kế thừa quyền tác nhân (`Admin --\|> User --\|> Guest`) và tách lộ trình xác thực (`FR-09a`/`FR-09b`) | Accepted |
| [ADR-012](ADR-012-feedback-uniqueness-and-context.md) | Khóa duy nhất theo ngữ cảnh (`UNIQUE NULLS NOT DISTINCT`) và `ON DELETE CASCADE` cho đánh giá gợi ý | Accepted |

**Cấu trúc ADR:** Bối cảnh → Quyết định → Phương án cân nhắc → Hệ quả / rủi ro → Tiêu chí xem xét lại → Tài liệu liên quan.
