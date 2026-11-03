# Documentation changelog

## [1.0.0] — 03/11/2026

- Tạo bộ tài liệu theo cấu trúc 7 thư mục `docs/` của FoodVision AI.
- SRS có FR-01…FR-18, NFR-01…NFR-12, BR, User Stories và Use Cases, traceability.
- Kiến trúc có Mermaid diagrams, Use Case PlantUML, ERD 16 bảng, Data Dictionary, security.
- API contract OpenAPI 3.1.0 (33 operations: public/User/Admin) và khung Postman; dữ liệu ví dụ không phải server đang chạy.
- AI thiết kế 20 candidate labels, protocol dataset/evaluation, metrics/giấy phép.
- Scoring v1 có công thức C/E/T/P, quy tắc ready/missing và ví dụ S=89.0.
- Kế hoạch test + các test case/acceptance đều khởi tạo `Not run`.
- 7 Architecture Decision Records ở trạng thái `Proposed`.

## Quy ước phiên bản tiếp theo

- `1.0.x`: sửa lỗi nội dung, link, minh họa **không đổi** contract.
- `1.x.0`: thêm yêu cầu/tính năng/field không phá tương thích hoặc thay thuật toán có chủ đích.
- `2.0.0`: thay breaking API/schema/luồng nghiệp vụ, phải review lại RTM/ADR.
