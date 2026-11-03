# ADR-002 — Sử dụng Supabase PostgreSQL/Auth/Storage

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** dữ liệu nguyên liệu–công thức có nhiều quan hệ N–N, cần auth đơn giản, không muốn tự xây hệ mật khẩu.
- **Decision:** dùng PostgreSQL + Supabase Auth + Storage (chỉ ảnh cover được cấp quyền). Dùng RLS **kèm GRANT/REVOKE** cho schema có Data API; FastAPI phải kiểm tra quyền riêng nếu dùng secret/service role.
- **Alternatives:** MySQL + backend auth tự viết; MongoDB; Firebase (document data khác mô hình quan hệ).
- **Consequences:** ít công xây auth, thuận tiện SQL/FK; phải quản lý schema migration, bảo vệ secret và thiết kế RLS.
- **Revisit when:** hạ tầng/chi phí hoặc policy dữ liệu đòi host DB riêng.
- **References:** `docs/02-architecture/database-design.md`, https://supabase.com/docs/guides/database/postgres/row-level-security.
