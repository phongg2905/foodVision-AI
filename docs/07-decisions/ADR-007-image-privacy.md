# ADR-007 — Quyền riêng tư ảnh đầu vào và lịch sử

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** ảnh tại nhà có thể chứa người hoặc vật dụng riêng tư; lưu ảnh không thiết yếu cho luồng gợi ý.
- **Decision:** ảnh upload chỉ được xử lý tạm thời, dọn tệp spool nếu có và không lưu ảnh gốc trong MVP; guest không lưu scan. User bật `save_history=true` mới lưu metadata dự đoán và ingredient IDs, không lưu ảnh; User có quyền xem và xóa lịch sử này qua API có xác thực. Không dùng ảnh cho train khi chưa có đồng ý riêng.
- **Alternatives:** lưu ảnh để debug/retrain (rủi ro riêng tư và cần quyền/retention); không có lịch sử (đơn giản hơn nhưng thiếu phản hồi phiên).
- **Consequences:** không xem lại ảnh cũ, khó debug bằng ảnh production; có thể debug bằng bộ test nội bộ không có thông tin cá nhân.
- **Revisit when:** nhóm thiết kế luồng xin đồng ý riêng, công cụ xóa dữ liệu, retention, mục đích và căn cứ pháp lý rõ ràng.
- **References:** `docs/02-architecture/security-and-deployment.md`, `docs/01-requirements/SRS.md`.
