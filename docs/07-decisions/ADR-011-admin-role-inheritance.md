# ADR-011 — Kế thừa quyền tác nhân (`Admin --|> User --|> Guest`) và lộ trình triển khai xác thực (`FR-09a` / `FR-09b`)

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:**
  1. Các công cụ quản trị (`FR-13`..`FR-15`) thuộc mức ưu tiên `P0` (bắt buộc có trong MVP để nhập công thức, nguyên liệu và kích hoạt model AI), nhưng tính năng quản lý tài khoản trước đây (`FR-09`) lại được xếp ở mức `P1`, gây phụ thuộc ngược (Admin không thể đăng nhập ở giai đoạn P0 nếu chưa có xác thực).
  2. Trong biểu đồ Use Case và kiểm tra phân quyền, cần làm rõ tài khoản `Admin` có được phép sử dụng các tính năng của `User` (lưu yêu thích, lưu lịch sử quét, gửi đánh giá) để kiểm thử tích hợp trên môi trường thật hay không.
- **Decision:**
  1. **Tách `FR-09` thành hai yêu cầu con theo lộ trình ưu tiên:**
     - `FR-09a` (**P0 — MVP**): Xác thực Quản trị viên (`Admin` đăng nhập qua Supabase Auth, kiểm tra `profiles.role = 'admin'`, khôi phục mật khẩu và đăng xuất cục bộ `signOut({ scope: 'local' })`). Tài khoản Admin đầu tiên được khởi tạo qua Supabase Dashboard/seed script và gán quyền trong DB.
     - `FR-09b` (**P1**): Đăng ký, đăng nhập, khôi phục mật khẩu và đăng xuất cho Người dùng đã đăng ký (`User`).
  2. **Kế thừa quyền tác nhân (`Admin --|> User --|> Guest`):** Thiết lập quan hệ kế thừa `Admin --|> User` và `User --|> Guest` trong UML Use Case Diagram, RLS policies (`auth.uid() = user_id`) và dependency xác thực của FastAPI. Một tài khoản có `profiles.role = 'admin'` mặc định có đầy đủ quyền của `User` trên các tài nguyên cá nhân của chính tài khoản đó, cộng thêm quyền truy cập nhóm `/api/v1/admin/*`.
- **Alternatives:** Tách hoàn toàn `Admin` không cho gọi API của `User` (buộc quản trị viên phải duy trì 2 tài khoản riêng biệt khi vừa biên tập công thức vừa kiểm thử luồng gợi ý/lưu lịch sử).
- **Consequences:** Giải quyết triệt để phụ thuộc ngược giữa `FR-09` và `FR-13..15` mà không làm phình phạm vi MVP, đồng thời giúp sơ đồ Use Case, chính sách RLS và kiểm thử phân quyền nhất quán.
- **Revisit when:** Hệ thống tách cổng quản trị nội bộ sang miền định danh riêng (Enterprise SSO) sau MVP.
- **References:** [`docs/01-requirements/SRS.md`](../01-requirements/SRS.md), [`docs/01-requirements/use-case-diagram.puml`](../01-requirements/use-case-diagram.puml), [`docs/02-architecture/security-and-deployment.md`](../02-architecture/security-and-deployment.md).

