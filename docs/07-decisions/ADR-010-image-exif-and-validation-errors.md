# ADR-010 — Tiền xử lý EXIF Orientation, xóa metadata GPS/EXIF và chuẩn hóa mã lỗi HTTP (`400` vs `404` vs `409` vs `415` vs `422` vs `504`)

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:**
  1. Ảnh chụp từ camera điện thoại thường lưu pixel nằm ngang kèm cờ `EXIF Orientation` và tọa độ GPS nhạy cảm. Nếu đưa thẳng vào YOLO mà không xoay theo EXIF Orientation, ảnh bị nghiêng 90°/180° làm giảm độ chính xác nhận diện và lệch tọa độ `bbox` hiển thị trên trình duyệt.
  2. Hợp đồng API cần phân định nhất quán giữa lỗi định dạng MIME (`415`), lỗi dữ liệu/ngữ nghĩa đầu vào (`422`), lỗi bất biến trạng thái nghiệp vụ (`400`), lỗi xung đột định danh (`409`), lỗi quyền sở hữu lịch sử quét (`404`) và lỗi quá thời gian suy luận (`504`).
- **Decision:**
  1. **Tiền xử lý ảnh (`POST /api/v1/ai/detect`):** Sau khi kiểm tra dung lượng (`<= 5 MiB`, quá hạn trả `413 IMAGE_TOO_LARGE`) và MIME type (`JPEG/PNG/WebP`, sai trả `415 UNSUPPORTED_IMAGE_TYPE`), backend giải mã ảnh (hỏng trả `422 INVALID_IMAGE`), đọc cờ `EXIF Orientation` để xoay pixel về chiều hiển thị chuẩn (upright), và xóa sạch toàn bộ metadata EXIF/GPS trong bộ nhớ trước khi đưa vào mô hình YOLO. Mọi tọa độ `bbox` (`x1, y1, x2, y2` chuẩn hóa `[0, 1]`) được tính trên ảnh đã xoay chuẩn.
  2. **Chuẩn hóa mã trạng thái HTTP và 20 mã lỗi nghiệp vụ:**
     - `400 Bad Request`: Vi phạm bất biến trạng thái nghiệp vụ của tài nguyên (`RECIPE_NOT_PUBLISHABLE`, `INGREDIENT_IN_USE`, `MODEL_NOT_ACTIVATABLE`, `INVALID_LABEL_MAPPING`, `MODEL_IMMUTABLE`).
     - `404 Not Found`: Không tìm thấy tài nguyên hoặc `scan_id` thuộc người dùng khác (`SCAN_NOT_OWNED` thống nhất trả `404` thay vì `403` để chống dò quét UUID).
     - `409 Conflict`: Trùng khóa duy nhất khi tạo/đổi định danh (`DUPLICATE_SLUG`, `DUPLICATE_MODEL_VERSION`).
     - `422 Unprocessable Entity`: Lỗi kiểu dữ liệu, miền giá trị hoặc tham số mâu thuẫn (`VALIDATION_ERROR`, `INVALID_IMAGE`, `INVALID_INGREDIENTS`, `INVALID_QUERY_PARAMS`).
     - `503 Service Unavailable` (`MODEL_NOT_READY`) và `504 Gateway Timeout` (`INFERENCE_TIMEOUT` khi suy luận vượt ngưỡng timeout cấu hình).
- **Alternatives:** Dùng chung `400` cho mọi lỗi client hoặc trả `403` cho `SCAN_NOT_OWNED` (làm lộ sự tồn tại của `scan_id` và mâu thuẫn với chuẩn FastAPI/OpenAPI `422`).
- **Consequences:** Bảo vệ quyền riêng tư vị trí (GPS) của người dùng, đồng bộ tọa độ `bbox` giữa backend và trình duyệt, và giúp frontend/tester phân biệt rõ lỗi validation đầu vào (`422`) với lỗi điều kiện trạng thái nghiệp vụ (`400`).
- **Revisit when:** Bổ sung xử lý ảnh phía client (WebAssembly/Canvas) trước khi upload.
- **References:** [`docs/02-architecture/security-and-deployment.md`](../02-architecture/security-and-deployment.md), [`docs/03-api/api-conventions.md`](../03-api/api-conventions.md), [`docs/04-ai-model/ai-model-design.md`](../04-ai-model/ai-model-design.md).

