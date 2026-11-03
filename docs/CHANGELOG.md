# Documentation changelog

## [0.9.0-draft] — 03/11/2026 (Rà soát & đồng bộ toàn diện chờ duyệt `1.0.0-baseline`)

- **Phiên bản & Quản trị yêu cầu (`01-requirements/`):**
  - Chuyển nhãn phiên bản tài liệu sang `0.9.0-draft` (Proposed, chờ duyệt lên `1.0.0-baseline`), bổ sung bảng Lịch sử sửa đổi, Glossary, bảng Giả định & Rủi ro (`AR-01`..`AR-04`), và bảng Phân vai trách nhiệm (`PM / Content Lead`, `BE / DB Lead`, `AI Lead`, `FE / QA Lead`) kèm nguyên tắc **kiểm thử chéo (Cross-Testing)**.
  - Tách `FR-09` thành `FR-09a` (Admin Auth, `P0`) và `FR-09b` (User Auth, `P1`), nâng `FR-15` (Quản trị model AI & nhãn) lên `P0` để khép kín luồng MVP.
  - Chuẩn hóa 10 Use Case (`UC-01`..`UC-10`), thiết lập quan hệ `UC-02 <<extend>> UC-03` tại điểm mở rộng `EP_InitFromImage`, bỏ phụ thuộc cứng `UC-04 ..> UC-03 <<include>>`, và đồng bộ kế thừa quyền `Admin --|> User --|> Guest`.
  - Mở rộng lên 14 User Stories (`US-01`..`US-14`), bổ sung Definition of Done (DoD) và 30 kịch bản Gherkin nguyên tử (`AC-01`..`AC-28`, tách `AC-19a`/`AC-19b` và `AC-22a`/`AC-22b`, mỗi AC đúng 1 mệnh đề `When`).
  - Mở rộng `NFR-01`..`NFR-14` và `BR-01`..`BR-12`; cập nhật ma trận truy vết (`traceability-matrix.md`) phủ 100% `FR`, `NFR`, `UC`, `US/AC`, `API` và `TC-01`..`TC-47`.
- **Kiến trúc, Cơ sở dữ liệu & Bảo mật (`02-architecture/`):**
  - Bổ sung phân loại gia vị nền `category = 'pantry'` (muối, đường, nước mắm, dầu ăn, tiêu xay; loại nước lọc khỏi bảng `ingredients`).
  - Yêu cầu PostgreSQL `>= 15`, bổ sung `updated_at`, `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)` và `ON DELETE CASCADE` trên `recommendation_feedback.scan_session_id` (đồng bộ `erd.mmd`, `database-design.md`, `data-dictionary.md`).
  - Quy định tiền xử lý tự xoay ảnh theo cờ `EXIF Orientation` và xóa sạch metadata `EXIF/GPS` trong RAM trước khi suy luận; chuẩn hóa `signOut({ scope: 'local' })`, ẩn danh hóa lỗi quyền sở hữu `404 SCAN_NOT_OWNED`, và cập nhật tham chiếu **Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15**.
- **Hợp đồng API (`03-api/`):**
  - Chuẩn hóa bảng phân biệt `400` vs `404` vs `409` vs `415` vs `422` vs `504` và danh mục 20 mã lỗi nghiệp vụ kèm schema `details` trong `api-conventions.md`.
  - Cập nhật `openapi.yaml`, `request-response-examples.md` và `foodvision-ai.postman_collection.json`: bổ sung `category` và `exclude_pantry` trên `GET /ingredients`, `excluded_pantry_ids` trên `POST /recommendations`, `category` trên `RecipeIngredientView`, `200 OK` (upsert) trên `POST /feedback`, `504` trên `POST /ai/detect`, và `400` trên các endpoint quản trị công thức/nguyên liệu/model/nhãn AI.
- **Mô hình AI & Hệ gợi ý (`04-ai-model/`, `05-recommendation/`):**
  - Bổ sung quy tắc bất biến & điều kiện kích hoạt/rollback model (`archived -> active` kiểm tra `invalid_mapped_class_indices`), cấm gán `ai_labels` vào `pantry`/`inactive`, và quy tắc minh bạch đánh giá `NFR-11` (cấm loại lớp yếu sau khi chạy test, bắt buộc công bố per-class `AP50`, `Recall`, `N_test`).
  - Cập nhật công thức chấm điểm `E`, `C`, `S` với tập gia vị nền báo thiếu `M_pantry = R_pantry ∩ X` (ví dụ cơ sở `X = [] -> S = 89.0, ready`; khi tắt Nước mắm `X = [nuoc_mam] -> S = 68.1, missing`) và quy ước `cook_minutes` bao gồm thời gian ướp/chờ/hầm bắt buộc (`BR-05`).
- **Kiểm thử & Quyết định kiến trúc (`06-testing/`, `07-decisions/`):**
  - Mở rộng `test-cases.md` lên 47 ca kiểm thử chức năng (`TC-01`..`TC-47`) cùng đầy đủ nhóm `SEC`, `API`, `AI`, `UI`, `PERF`, `LEGAL`, `OPS` và bảng unit test thuật toán.
  - Bổ sung 5 Architecture Decision Records mới (`ADR-008`..`ADR-012`) và cập nhật mục lục `07-decisions/README.md`.

## [0.1.0-draft] — 03/11/2026 (Khởi tạo ban đầu, nguyên gắn nhãn `1.0.0`)

- Tạo bộ tài liệu theo cấu trúc 7 thư mục `docs/` của FoodVision AI.
- SRS có FR-01…FR-18, NFR-01…NFR-12, BR, User Stories và Use Cases, traceability.
- Kiến trúc có Mermaid diagrams, Use Case PlantUML, ERD 16 bảng, Data Dictionary, security.
- API contract OpenAPI 3.1.0 (33 operations: public/User/Admin) và khung Postman; dữ liệu ví dụ không phải server đang chạy.
- AI thiết kế 20 candidate labels, protocol dataset/evaluation, metrics/giấy phép.
- Scoring v1 có công thức C/E/T/P, quy tắc ready/missing và ví dụ S=89.0.
- Kế hoạch test + các test case/acceptance đều khởi tạo `Not run`.
- 7 Architecture Decision Records ở trạng thái `Proposed`.

## Quy ước phiên bản tiếp theo

- `0.9.x-draft`: chỉnh sửa theo góp ý rà soát trước khi ký duyệt baseline.
- `1.0.0-baseline`: phiên bản baseline chính thức sau khi nhóm và Giảng viên hướng dẫn phê duyệt.
- `1.x.0`: thêm yêu cầu/tính năng/field không phá tương thích hoặc thay thuật toán có chủ đích.
- `2.0.0`: thay breaking API/schema/luồng nghiệp vụ, phải review lại RTM/ADR.
