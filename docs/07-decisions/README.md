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

**Template ADR ngắn:** Bối cảnh → Quyết định → Phương án cân nhắc → Hệ quả/rủi ro → Tiêu chí xem xét lại → Tài liệu liên quan.
