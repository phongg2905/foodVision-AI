# Feature Specification: Giao diện Upload/Camera, Cảnh báo xác nhận HITL (conf < τ) & Giải thích đóng góp điểm XAI (GĐ3 - TP14)

**Feature Branch**: `feat/022-gd3-fe-hitl-xai`  
**Created**: 2026-11-17  
**Status**: In Implementation (`1.1.0` — `ADR-010`, `ADR-013`)  
**Owner**: `TV3 — Tâm Minh` (`@tamminh6`) · **Cross-Tester**: `TV1 — Minh Thành`  
**Input**: Trello Card `#22` (`[GĐ3 - TP14]`): *"Xây dựng Giao diện Upload/Camera, Cảnh báo xác nhận HITL (conf < τ) & Giải thích đóng góp điểm XAI"* đồng bộ thẩm mỹ **NEWTASTE Calm Editorial** (Phương án A, chống AI-slop).

**Authoritative References (`docs/`)**:
- [SRS](../../docs/01-requirements/SRS.md): `FR-03`, `FR-04`, `FR-05`, `FR-06`, `FR-18`, `BR-03`, `BR-09`, `BR-12`, `NFR-01`, `NFR-02`, `NFR-12`
- [AI Model Design](../../docs/04-ai-model/ai-model-design.md): Pipeline EXIF Orientation, xóa EXIF/GPS, NMS `bbox` `[0, 1]`, ngưỡng cảnh báo xác nhận HITL $\tau = 0.80$, xử lý lỗi `413` / `415` / `422` / `503` / `504`
- [Recommendation Design](../../docs/05-recommendation/recommendation-design.md): Mục 4.5 — Giải thích đóng góp tuyến tính XAI (`50*C + 25*G + 15*T + 10*P = S`)
- [OpenAPI Contract](../../docs/03-api/openapi.yaml): `POST /api/v1/ai/detect`, `POST /api/v1/recommendations` (`scan_id`)
- [Test Cases](../../docs/06-testing/test-cases.md): `TC-04`..`TC-09`, `TC-12`, `TC-20`, `TC-27`, `TC-29`..`TC-31`, `TC-43`, `AI-03`, `UI-01`..`UI-03`, `DEF-01`, `DEF-02`, `DEF-10`

---

## User Scenarios & Testing

### User Story 1 - Tải ảnh / Chụp ảnh & Vẽ Bounding Box Khớp Chiều EXIF (`FR-03`, `FR-04`, `TC-04..07`, `TC-43`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn tải ảnh hoặc chụp ảnh nguyên liệu trực tiếp từ khu vực **`Quét ảnh AI`** trên thanh tủ bếp, được kiểm tra nhanh định dạng (`JPEG`/`PNG`/`WebP`) và dung lượng (`<= 5 MiB`) ngay trên trình duyệt, và nhìn thấy các hộp giới hạn (`bbox`) hiển thị khớp chính xác trên cả ảnh ngang lẫn ảnh chụp dọc điện thoại có cờ `EXIF Orientation`.

**Acceptance Scenarios**:
1. **Given** người dùng chọn tệp vượt quá `5 MiB` (`TC-05`), sai định dạng `.pdf`/`.tiff` (`TC-06a`) hoặc tệp giả mạo `.jpg` bị hỏng byte (`TC-06b`), **When** kiểm tra trước/sau khi gửi, **Then** giao diện hiển thị thông báo tiếng Việt rõ ràng tương ứng (`IMAGE_TOO_LARGE`, `UNSUPPORTED_IMAGE_TYPE`, `INVALID_IMAGE`) kèm nút chuyển sang nhập tay mà không làm treo trang.
2. **Given** người dùng tải ảnh hợp lệ (kể cả ảnh chụp dọc có cờ `EXIF Orientation != 1`, `TC-43`, `DEF-01`), **When** `POST /api/v1/ai/detect` trả về `detections[]` với `bbox` chuẩn hóa `[0, 1]`, **Then** khung ảnh tự căn đúng chiều thẳng đứng (`image-orientation: from-image`) và lớp phủ `bbox` bám khít `100%` khung pixel thực tế của ảnh không bị lệch do viền đệm (`letterbox`).

---

### User Story 2 - Luồng Xác nhận HITL Phân tách Rõ (`>= 0.80`) & Cần Kiểm Tra (`< 0.80`) (`TP 14`, `FR-05`, `ADR-013`) (Priority: P1)

Là người dùng, sau khi AI quét ảnh, tôi muốn nhóm `clear_ingredients` (`confidence >= 0.80`) được tích chọn sẵn, còn nhóm `uncertain_ingredients` (`confidence < 0.80`) được gắn huy hiệu cảnh báo **`Cần kiểm tra lại`** (không tự động chốt nhãn mù quáng) để tôi chủ động tích xác nhận, đổi sang nguyên liệu đúng hoặc bỏ qua trước khi áp dụng vào tủ bếp.

**Acceptance Scenarios**:
1. **Given** kết quả nhận diện có cả nguyên liệu `>= 0.80` và nguyên liệu `< 0.80` (`AI-03`, `DEF-02`), **When** hiển thị bảng xác nhận HITL, **Then** nhóm `clear_ingredients` được tích sẵn, còn nhóm `uncertain_ingredients` hiển thị nổi bật cảnh báo HITL kèm tùy chọn xác nhận hoặc đổi nhãn sang nguyên liệu khác trong danh mục (`category != 'pantry'`).
2. **Given** ảnh có nhiều `bbox` cùng loại nguyên liệu hoặc người dùng sửa nhãn trùng với nguyên liệu đã có (`TC-07`, `TC-08`), **When** bấm **`Áp dụng vào tủ bếp`**, **Then** danh sách `ingredient_ids` gửi tới `/api/v1/recommendations` được khử trùng lặp UUID tuyệt đối và truyền kèm `scan_id` (nếu có).

---

### User Story 3 - Chuyển tiếp Dự phòng Mượt mà sang Nhập Thủ công (`FR-18`, `TC-27`, `TC-29`, `TC-30`, `UI-02`) (Priority: P1)

Là người dùng, khi ảnh không phát hiện được nguyên liệu nào (`detections = []`) hoặc dịch vụ AI tạm bận / quá hạn (`503 MODEL_NOT_READY`, `504 INFERENCE_TIMEOUT`), tôi muốn nhận thông báo rõ ràng bằng tiếng Việt cùng nút **Thử lại** và lối tắt **Chuyển sang nhập thủ công** để tìm kiếm nguyên liệu tiếng Việt ngay lập tức mà không bị gián đoạn.

**Acceptance Scenarios**:
1. **Given** API trả `200 OK` với `detections = []` (`TC-27`) hoặc trả lỗi `503` / `504` (`TC-29`, `TC-30`, `UI-02`), **When** người dùng bấm **`Chuyển sang nhập thủ công`**, **Then** khay quét ảnh thu gọn, `scan_id` đặt về `null` và con trỏ tự động đặt vào ô tìm kiếm tiếng Việt.

---

### User Story 4 - Hiển thị Trực quan Đóng góp Điểm XAI (`50*C + 25*G + 15*T + 10*P`) (`TP 14`, `DEF-10`) (Priority: P1)

Là người dùng (và hội đồng đánh giá), trên từng thẻ món ăn gợi ý và trong trang chi tiết món, tôi muốn nhìn thấy trực quan thanh tỷ lệ đóng góp điểm **XAI 4 tiêu chí** (`Độ phủ 50·C`, `Món chính 25·G`, `Thời gian 15·T`, `Khẩu vị 10·P`) khớp tổng điểm `S` cùng lời giải thích tiếng Việt (`explanation_vi`), trình bày tinh gọn theo đúng bảng màu ấm NEWTASTE (không dùng màu cầu vồng rối mắt).
