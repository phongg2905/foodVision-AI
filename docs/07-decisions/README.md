# 07 — Architecture Decision Records (ADR)

ADR là hồ sơ lưu các **quyết định kỹ thuật và lý do**, không viết lại toàn bộ đặc tả. Trạng thái hiện tại của các ADR là `Proposed` để nhóm/giảng viên duyệt. Khi chốt, đổi `Status: Accepted` bằng PR; khi thay đổi, tạo ADR mới và ghi `Superseded by ADR-xxx` ở bản cũ.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [ADR-001](ADR-001-web-fastapi.md) | Web React và Backend Python FastAPI riêng | Proposed |
| [ADR-002](ADR-002-supabase.md) | Supabase PostgreSQL/Auth/Storage, RLS + grants | Proposed |
| [ADR-003](ADR-003-detection-recommendation.md) | YOLO detection tách rule-based recommendation | Proposed |
| [ADR-004](ADR-004-nutrition.md) | Dinh dưỡng định tính, không ước lượng từ ảnh | Proposed |
| [ADR-005](ADR-005-yolo-licensing.md) | Kiểm tra license YOLO/dataset trước công bố | Proposed |
| [ADR-006](ADR-006-label-versioning.md) | Class index theo model version, map vào ingredient UUID | Proposed |
| [ADR-007](ADR-007-image-privacy.md) | Không lưu ảnh gốc, lịch sử kết quả opt-in | Proposed |
| [ADR-008](ADR-008-pantry-ingredients-handling.md) | Cơ chế bật/tắt gia vị nền (`category = 'pantry'`) và tác động lên thuật toán gợi ý | Proposed |
| [ADR-009](ADR-009-cooking-and-waiting-time.md) | Quy ước tính thời gian ướp/chờ/hầm bắt buộc vào `cook_minutes` và kiểm tra tính nhất quán | Proposed |
| [ADR-010](ADR-010-image-exif-and-validation-errors.md) | Tiền xử lý EXIF Orientation, xóa metadata GPS/EXIF và chuẩn hóa mã lỗi HTTP (`400`/`404`/`409`/`415`/`422`/`504`) | Proposed |
| [ADR-011](ADR-011-admin-role-inheritance.md) | Kế thừa quyền tác nhân (`Admin --\|> User`) và tách lộ trình xác thực (`FR-09a`/`FR-09b`) | Proposed |
| [ADR-012](ADR-012-feedback-uniqueness-and-context.md) | Khóa duy nhất theo ngữ cảnh (`UNIQUE NULLS NOT DISTINCT`) và `ON DELETE CASCADE` cho đánh giá gợi ý | Proposed |

**Template ADR ngắn:** Bối cảnh → Quyết định → Phương án cân nhắc → Hệ quả/rủi ro → Tiêu chí xem xét lại → Tài liệu liên quan.
