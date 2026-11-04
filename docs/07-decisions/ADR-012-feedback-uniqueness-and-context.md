# ADR-012 — Khóa duy nhất theo ngữ cảnh (`UNIQUE NULLS NOT DISTINCT`) và cơ chế xóa lan truyền (`ON DELETE CASCADE`) cho đánh giá gợi ý

- **Status:** Accepted
- **Date:** 03/11/2026
- **Context:**
  1. Bảng `recommendation_feedback` lưu đánh giá mức độ hữu ích (`1..5`) của người dùng đối với công thức được gợi ý, có thể gắn với một phiên quét cụ thể (`scan_session_id` khác `NULL`) hoặc khi duyệt tự do (`scan_session_id IS NULL`). Trong chuẩn SQL thông thường, ràng buộc `UNIQUE (user_id, recipe_id, scan_session_id)` coi các giá trị `NULL` là khác nhau, dẫn đến một người dùng có thể gửi trùng lặp vô hạn đánh giá khi `scan_session_id IS NULL`.
  2. Nếu khóa ngoại `scan_session_id` dùng `ON DELETE SET NULL`, khi một người dùng đã có đánh giá ở ngữ cảnh `scan_session_id IS NULL` và một đánh giá khác ở phiên quét `S1`, việc xóa phiên quét `S1` (`DELETE /api/v1/scan-sessions/{scan_id}`) sẽ chuyển `S1 -> NULL` và gây lỗi xung đột khóa duy nhất (`23505 unique_violation`).
- **Decision:**
  1. Yêu cầu **PostgreSQL `>= 15`** (mặc định trên Supabase hiện hành) và khai báo ràng buộc:
     ```sql
     UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)
     ```
     kèm cột `updated_at timestamptz not null default now()`.
  2. Khai báo hành vi upsert cho `POST /api/v1/feedback`: tạo mới trong ngữ cảnh `(user_id, recipe_id, scan_session_id)` trả `201 Created`; gửi lại trong cùng ngữ cảnh sẽ cập nhật `rating`, `note`, `updated_at = now()` và trả `200 OK`.
  3. Khai báo khóa ngoại `scan_session_id uuid references public.scan_sessions(id) on delete cascade`. Khi người dùng xóa một phiên quét lịch sử, các đánh giá gắn với phiên quét đó được xóa theo trong cùng giao dịch, không bao giờ gây lỗi xung đột với bản ghi có `scan_session_id IS NULL`. Giao diện hiển thị cảnh báo rõ trước khi người dùng xác nhận xóa phiên quét.
  4. Khi tổng hợp thống kê chất lượng gợi ý (ngoài phạm vi MVP), truy vấn chỉ lấy **1 bản ghi có `updated_at` mới nhất trên mỗi cặp `(user_id, recipe_id)`** để tránh lệch trọng số nếu một người dùng đánh giá cùng một món ở nhiều phiên quét.
- **Alternatives:**
  - Dùng hai partial unique index tách biệt + `ON DELETE SET NULL` kèm trigger thủ công xử lý va chạm khi xóa `scan_session` (phức tạp hơn và dễ phát sinh lỗi ngầm).
- **Consequences:** Bảo đảm thao tác `POST /api/v1/feedback` và `DELETE /api/v1/scan-sessions/{scan_id}` luôn an toàn, idempotent, không phát sinh lỗi `500` do va chạm khóa duy nhất. Đổi lại, đánh giá gắn với phiên quét đã bị người dùng chủ động xóa sẽ không còn được lưu giữ.
- **Revisit when:** Cần giữ lại dữ liệu đánh giá ẩn danh phục vụ phân tích dài hạn sau khi người dùng xóa lịch sử quét.
- **References:** [`docs/02-architecture/database-design.md`](../02-architecture/database-design.md), [`docs/02-architecture/data-dictionary.md`](../02-architecture/data-dictionary.md), [`docs/05-recommendation/recommendation-design.md`](../05-recommendation/recommendation-design.md).

