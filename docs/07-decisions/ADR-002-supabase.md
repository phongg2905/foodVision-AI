# ADR-002 — Sử dụng Supabase PostgreSQL (`>= 15`), `pg_trgm`, Auth và Storage

- **Status:** Accepted
- **Date:** 03/11/2026
- **Context:** Dữ liệu nguyên liệu–công thức có nhiều quan hệ N–N kèm trọng số vai trò, bảng bí danh tiếng Việt vùng miền (`đậu hũ`/`đậu phụ`), tác nhân dị ứng và đánh giá theo ngữ cảnh; dự án cần xác thực đơn giản, không tự xây hệ mật khẩu từ đầu.
- **Decision:** Sử dụng **PostgreSQL `>= 15`** trên Supabase (hỗ trợ `UNIQUE NULLS NOT DISTINCT` cho `recommendation_feedback` và bật extension `unaccent`, `pg_trgm` GIN index `gin_trgm_ops` phục vụ tìm kiếm nguyên liệu tiếng Việt gần đúng) + Supabase Auth + Supabase Storage (chỉ lưu ảnh minh họa công thức hợp pháp). Áp dụng **RLS kết hợp `GRANT`/`REVOKE`** tối thiểu cho mọi bảng trong schema `public`; FastAPI phải tự kiểm tra quyền và quan hệ sở hữu nếu sử dụng `service_role`.
- **Alternatives:** MySQL + backend auth tự viết; MongoDB/Firebase (mô hình tài liệu kém phù hợp cho ràng buộc toàn vẹn N–N và truy vấn đa điều kiện nguyên liệu–công thức).
- **Consequences:** Giảm chi phí xây xác thực, đảm bảo toàn vẹn khóa ngoại và tìm kiếm tiếng Việt nhanh ngay trong DB; đổi lại phải quản trị chặt script migration, bảo vệ secret key và kiểm thử chính sách RLS.
- **Revisit when:** Hạ tầng, chi phí hoặc chính sách dữ liệu yêu cầu tự vận hành cụm PostgreSQL độc lập.
- **References:** [`docs/02-architecture/database-design.md`](../02-architecture/database-design.md), [`ADR-012`](ADR-012-feedback-uniqueness-and-context.md), https://supabase.com/docs/guides/database/postgres/row-level-security.
