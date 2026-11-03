# 02 — Architecture & Database

- [system-architecture.md](system-architecture.md): sơ đồ thành phần, luồng xử lý, nhiệm vụ FE/BE/AI/DB.
- [architecture.mmd](architecture.mmd): nguồn Mermaid sơ đồ kiến trúc để chỉnh sửa.
- [database-design.md](database-design.md): ERD, ràng buộc toàn vẹn (`CHECK`, `UNIQUE NULLS NOT DISTINCT`, `ON DELETE`) và quy tắc bảo vệ dữ liệu đang công bố.
- [erd.mmd](erd.mmd): nguồn Mermaid ERD (16 bảng).
- [data-dictionary.md](data-dictionary.md): kiểu dữ liệu, PK/FK, nullable, kiểm tra hợp lệ của các bảng (bao gồm phân nhóm `pantry` và quy ước `cook_minutes`) kèm checklist migration/seed.
- [security-and-deployment.md](security-and-deployment.md): phân quyền, xử lý xóa metadata EXIF/GPS, đăng xuất theo phạm vi phiên và quản lý bí mật.

**Lưu ý:** đây là thiết kế dữ liệu ở phiên bản `0.9.0-draft`, **chưa phải SQL migration đang chạy**. Khi triển khai thực tế, các script DDL/seed phải được tạo trong `supabase/migrations/` (yêu cầu PostgreSQL >= 15 trên Supabase) và đồng bộ với tài liệu này trong cùng PR.
