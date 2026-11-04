# Documentation changelog

## [0.9.1-draft] — 03/11/2026 (Đồng bộ kiến trúc thông minh 14 thành phần trên nền `0.9.0-draft`)

- **Kiến trúc 7 tầng & Tích hợp hệ thống thông minh (`README.md`, `docs/README.md`, `02-architecture/`):**
  - Hợp nhất kiến trúc 7 tầng — 14 thành phần thông minh (Nhận thức YOLO + CLIP/VLM hỗ trợ + HITL → Tìm kiếm tiếng Việt `pg_trgm` & Kho tri thức PostgreSQL → Suy luận luật 3 trạng thái → Xếp hạng Weighted Coverage + MCDA 5 tiêu chí + MMR → Cá nhân hóa Logistic Regression → Kiểm chứng A/B/C/D & Giải thích XAI → Dinh dưỡng 2 tầng Tags + USDA) với toàn bộ quy tắc quản trị, bảo mật và hợp đồng của `0.9.0-draft`.
  - Mở rộng thiết kế tri thức trong `database-design.md` và `data-dictionary.md`: bổ sung cơ sở ma trận nhị phân mở rộng thuộc tính (`role`, `weight` $w_{r,i}$, `grams`, `base_servings`, `cooking_method`, `required_equipment`, `quality_score`), bảng mở rộng Giai đoạn 2–4 (`allergens`, `ingredient_allergens`, `ingredient_nutrients` chuẩn USDA, `user_preferences`), và quy trình tìm kiếm tiếng Việt 4 tầng (`unaccent` + Unicode NFD + `ingredient_aliases` + `pg_trgm` GIN index `gin_trgm_ops`), đồng thời giữ nguyên yêu cầu PostgreSQL `>= 15`, `category = 'pantry'`, `UNIQUE NULLS NOT DISTINCT` và `ON DELETE CASCADE`.
- **Nhận thức Thị giác & Human-in-the-loop (`04-ai-model/`, `ADR-003`):**
  - Bổ sung công thức `IoU(B_p, B_g)` và `mAP@50:95` trên 10 ngưỡng IoU (`0.50..0.95`), lớp hỗ trợ ứng viên tương đồng Cosine CLIP/VLM cho vùng ảnh khó (`tofu`, `cucumber`/`zucchini`), và quy tắc cảnh báo xác nhận HITL $\text{Review}(x) = \mathbb{1}[p_{\max}(x) < \tau]$ ($\tau = 0.80$, hiệu chỉnh xác suất theo Guo et al., 2017) kết hợp tiền xử lý xoay `EXIF Orientation` & xóa `EXIF/GPS` (`ADR-010`) và quy tắc bất biến/rollback model (`NFR-11`).
  - Làm rõ ranh giới kỹ thuật: thao tác người dùng sửa nhãn trên UI áp dụng ngay cho phiên gợi ý hiện tại nhưng không tự động cập nhật tức thời trọng số mô hình YOLO.
- **Suy luận, Xếp hạng, Cá nhân hóa & Dinh dưỡng (`05-recommendation/`, `03-api/`, `ADR-004`, `ADR-008`):**
  - Thống nhất phân lớp thuật toán giữa hợp đồng MVP hiện hành (`Scoring v1.0` khớp `openapi.yaml`, ví dụ `89.0` / `68.1` với `excluded_pantry_ids`) và kiến trúc thông minh mở rộng (`Scoring v1.1` — Giai đoạn 2–4): suy luận thế giới mở 3 trạng thái (`READY`, `UNKNOWN`, `MISSING_CONFIRMED`) + lọc cứng `BLOCKED` ($\text{Feasible} = \text{Ready} \land \text{EquipOK} \land \text{DietOK}$), Weighted Coverage $C(r, A)$, Tversky Similarity ($\alpha=0.3, \beta=2.0 \implies 0.60$) làm Baseline B đối chứng, MCDA 5 tiêu chí ($S_{\text{base}} = 80.83$) kèm phân rã tuyến tính XAI ($\sum \text{Contribution}_k = S_{\text{base}}$), cá nhân hóa Logistic Regression có trộn cold-start ($\lambda_{\text{pers}}$), và đa dạng hóa Top-K bằng MMR ($\lambda_{\text{mmr}} = 0.7$).
  - Chuẩn hóa chính sách dinh dưỡng hai tầng (`ADR-004`, `nutrition-and-content.md`): tuyệt đối cấm suy đoán `gram`/`kcal` từ ảnh RGB; mặc định hiển thị `nutrition_tags` định tính có `source_url` (MVP `P0`) và hỗ trợ ước tính theo USDA FoodData Central $N_k(r) = \sum (m_i/100)V_{i,k}$ cùng quy đổi khẩu phần $q_i^{\text{new}} = q_i^{\text{base}}(n_{\text{new}}/n_{\text{base}})$ khi công thức có định lượng `grams` kiểm duyệt (`P1`).
- **Yêu cầu, Kiểm thử thực nghiệm & Tài liệu tham khảo (`01-requirements/`, `06-testing/`, `references.md`):**
  - Đồng bộ `SRS.md`, `use-cases.md`, `user-stories.md`, `traceability-matrix.md` với lộ trình 5 giai đoạn mà vẫn giữ nguyên cấu trúc IEEE 830, tách `FR-09a`/`FR-09b`, kế thừa `Admin --|> User --|> Guest`, 30 kịch bản Gherkin nguyên tử (`AC-01`..`AC-28`) và 20 mã lỗi nghiệp vụ.
  - Bổ sung thiết kế đối chứng thực nghiệm 4 phiên bản Ranker (`A – B – C – D` trên $\ge 100$ tình huống độc lập bằng `Precision@5`, `nDCG@5`, chia tập theo thời gian cho phiên bản D), bộ 10 kịch bản bảo vệ học phần (`DEF-01`..`DEF-10`) song hành cùng 47 ca kiểm thử chức năng (`TC-01`..`TC-47`), unit tests toán học và 18 nguồn tham khảo khoa học/kỹ thuật chuẩn.

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

- `0.9.x-draft`: chỉnh sửa theo góp ý rà soát và đồng bộ thiết kế thuật toán trước khi ký duyệt baseline.
- `1.0.0-baseline`: phiên bản baseline chính thức sau khi nhóm và Giảng viên hướng dẫn phê duyệt.
- `1.x.0`: mở rộng thành phần thông minh theo lộ trình giai đoạn, thêm yêu cầu/field không phá tương thích hoặc nâng cấp thuật toán có chủ đích (`Scoring v1.1`).
- `2.0.0`: thay đổi breaking đối với API contract, schema cốt lõi hoặc luồng nghiệp vụ chính, bắt buộc rà soát lại RTM và ADR.
