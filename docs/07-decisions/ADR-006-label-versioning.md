# ADR-006 — Version class YOLO, không dùng class_index làm ID nguyên liệu

- **Status:** Accepted
- **Date:** 03/11/2026
- **Context:** khi thêm lớp, thứ tự class index trong model có thể thay đổi, gây sai recipe nếu dùng index để JOIN.
- **Decision:** `ingredients.id UUID` bất biến; mỗi model có `ai_models.id`; `ai_labels` ánh xạ `(model_id,class_index)` → ingredient_id. Chỉ cho active khi đủ mapping. Không chỉnh mapping của model `active` tại chỗ; tạo phiên bản model draft mới rồi kích hoạt để giữ tính đúng lịch sử.
- **Alternatives:** dùng tên class làm khóa/đặt class index cố định mãi (khó kiểm soát đổi tên và tái huấn luyện).
- **Consequences:** cần admin UI và thêm bảng, nhưng có rollback và mở rộng lớp không làm hỏng recipes/favorites.
- **Revisit when:** thay nhận diện đa mô hình hoặc thêm cấp phân loại phân cấp (object/super-category).
- **References:** `docs/02-architecture/database-design.md`, `docs/04-ai-model/label-catalog.md`.
