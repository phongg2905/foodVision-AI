# ADR-003 — Tách YOLO Detector và Recommendation Engine

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** mục tiêu môn học cần phân hệ thông minh có thể giải thích. YOLO chỉ phát hiện vật thể, không tự chứa công thức hoặc logic tính món.
- **Decision:** YOLO trả detections→ ingredient ID; User sửa xác nhận; recommender dùng dữ liệu món + công thức tính điểm C/E/T/P minh bạch.
- **Alternatives:** dùng LLM tự sinh công thức hoặc end-to-end multimodal; luật search-only không nhận diện ảnh.
- **Consequences:** giải thích gợi ý dễ, kiểm thử độc lập; cần cơ sở dữ liệu recipe curate và cân nhắc trọng số qua thử nghiệm.
- **Revisit when:** có đủ lịch sử phản hồi/nhãn relevance để xây mô hình học xếp hạng thực nghiệm.
- **References:** `docs/04-ai-model/ai-model-design.md`, `docs/05-recommendation/recommendation-design.md`.
