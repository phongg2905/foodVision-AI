# 02 — Architecture & Database

- [system-architecture.md](system-architecture.md): sơ đồ thành phần, luồng xử lý, nhiệm vụ FE/BE/AI/DB.
- [architecture.mmd](architecture.mmd): nguồn Mermaid sơ đồ kiến trúc để chỉnh sửa.
- [database-design.md](database-design.md): ERD và ràng buộc dữ liệu.
- [erd.mmd](erd.mmd): nguồn Mermaid ERD.
- [data-dictionary.md](data-dictionary.md): kiểu dữ liệu, PK/FK, nullable, kiểm tra hợp lệ của các bảng.
- [security-and-deployment.md](security-and-deployment.md): phân quyền, triển khai và quản lý bí mật.

**Lưu ý:** đây là thiết kế dữ liệu, **chưa phải SQL migration đang chạy**. Khi triển khai, migration thực tế nằm trong `supabase/migrations/` và cập nhật tài liệu này trong cùng PR.
