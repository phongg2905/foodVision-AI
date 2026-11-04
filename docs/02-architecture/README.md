# 02 — System Architecture (`1.0.0`)

- [system-architecture.md](system-architecture.md): kiến trúc 7 tầng thông minh (tích hợp 14 thành phần kỹ thuật), sơ đồ thành phần, luồng tuần tự xử lý ảnh EXIF → YOLO/CLIP → HITL → suy luận/xếp hạng và phân tách module FE/BE/AI/DB theo lộ trình 5 giai đoạn.
- [architecture.mmd](architecture.mmd): nguồn Mermaid sơ đồ kiến trúc tổng quan để chỉnh sửa.
- [database-design.md](database-design.md): biểu diễn cơ sở tri thức nguyên liệu–công thức (Thành phần 03), tìm kiếm tiếng Việt `unaccent` + `pg_trgm` (Thành phần 13), ERD cốt lõi & mở rộng, ràng buộc toàn vẹn (`CHECK`, `UNIQUE NULLS NOT DISTINCT`, `ON DELETE`) và quy tắc bảo vệ dữ liệu đang `published`.
- [erd.mmd](erd.mmd): nguồn Mermaid ERD cốt lõi MVP (16 bảng).
- [data-dictionary.md](data-dictionary.md): từ điển dữ liệu PostgreSQL `>= 15` (cốt lõi MVP bao gồm `category = 'pantry'`, quy ước `cook_minutes`, `recommendation_feedback` upsert + các thuộc tính/bảng mở rộng Giai đoạn 2–4 cho trọng số vai trò $w_{r,i}$, dị ứng, dinh dưỡng USDA và hồ sơ cá nhân hóa) kèm checklist migration/seed.
- [security-and-deployment.md](security-and-deployment.md): mô hình mối đe dọa, kế thừa quyền `Admin --|> User --|> Guest`, RLS + GRANT/REVOKE, tự xoay EXIF Orientation & xóa metadata GPS, đăng xuất theo phạm vi `local`, tuân thủ Luật BV DLCN số 91/2025/QH15 và quản lý biến môi trường.

**Lưu ý:** đây là thiết kế kiến trúc và dữ liệu chuẩn ở phiên bản `1.0.0`, **chưa phải SQL migration đang chạy**. Khi triển khai thực tế, các script DDL/seed phải được tạo trong `supabase/migrations/` (yêu cầu PostgreSQL `>= 15` trên Supabase) và đồng bộ với tài liệu này trong cùng PR.
