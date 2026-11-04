# FoodVision AI — Bộ tài liệu dự án

> **Phiên bản tài liệu:** `1.0.0` (`Approved Baseline`)  
> **Cập nhật:** `04/11/2026`  
> **Trạng thái:** Baseline chính thức — Đã khóa đặc tả, kiến trúc 7 tầng (14 thành phần) và hợp đồng API để triển khai 5 giai đoạn  
> **Học phần:** Phát triển các hệ thống thông minh  
> **Loại sản phẩm:** Website thông minh gợi ý món ăn từ ảnh nguyên liệu

## 1. Mục đích và tư tưởng thiết kế

Thư mục `docs/` là **nguồn chuẩn (single source of truth) về yêu cầu, kiến trúc và thuật toán** của FoodVision AI. Tất cả tài liệu tại đây mô tả **thiết kế kỹ thuật và kế hoạch kiểm chứng**, không đồng nghĩa rằng chức năng đã được lập trình xong hay đã có số liệu thực nghiệm. Kể từ khi chốt baseline chính thức (`1.0.0`), mọi thay đổi về nghiệp vụ, mô hình dữ liệu, hợp đồng API và thuật toán AI/Recommendation phải đi kèm pull request cập nhật tài liệu liên quan.

**Tên đề tài đề xuất:** Xây dựng website thông minh gợi ý món ăn từ hình ảnh nguyên liệu sử dụng YOLO.

**Luồng thông minh xuyên suốt (7 tầng — 14 thành phần kỹ thuật):**

1. **Nhận thức (`01`, `02`, `14`):** người dùng tải ảnh nguyên liệu → backend tự động xoay chuẩn theo `EXIF Orientation` & xóa sạch metadata `EXIF/GPS` → YOLO phát hiện nhiều đối tượng (`01`), lớp CLIP/VLM hỗ trợ gợi ý ứng viên có kiểm soát cho vùng ảnh khó/bất định (`02`), và người dùng xác nhận/chỉnh sửa nhãn kèm bật/tắt thanh gia vị nền (`category = 'pantry'`) qua cơ chế Human-in-the-loop (`14`).
2. **Tri thức & Tìm kiếm (`03`, `10`, `13`):** chuẩn hóa tiếng Việt có dấu/không dấu, bảng từ đồng nghĩa vùng miền (`đậu hũ`/`đậu phụ`, `bắp`/`ngô`) và chỉ mục tam tự `pg_trgm` (`13`) ánh xạ về kho tri thức nguyên liệu–công thức có cấu trúc trên PostgreSQL `>= 15` (`03`) và chỉ truy xuất công thức đã kiểm duyệt (`published`) để chống ảo giác nội dung (`10`).
3. **Suy luận (`04`):** tránh giả định thế giới đóng bằng suy luận luật 3 trạng thái nguyên liệu (`confirmed_available`, `confirmed_missing`, `unknown`) kết hợp trạng thái gia vị nền (`excluded_pantry_ids`) và lọc cứng ràng buộc thời gian, ẩm thực, thiết bị, dị ứng (`BLOCKED` / `READY` / `UNKNOWN` / `MISSING_CONFIRMED`).
4. **Ra quyết định (`05`, `06`, `07`, `09`):** tính độ đầy đủ nguyên liệu có trọng số vai trò theo từng món (`05`), duy trì Tversky Similarity làm baseline toán học đối chứng (`06`), chấm điểm đa tiêu chí MCDA 5 thành phần (`07`) mở rộng từ công thức quy tắc MVP (`Scoring v1.0`), và đa dạng hóa danh sách Top-K bằng Maximal Marginal Relevance — MMR (`09`).
5. **Học hỏi cá nhân hóa (`08`):** học sở thích người dùng bằng Logistic Regression từ phản hồi tường minh (`favorites`, `recommendation_feedback` đã khử trùng theo ngữ cảnh) kết hợp cơ chế trộn điểm an toàn cho người dùng mới (`cold-start`).
6. **Kiểm chứng & Giải thích (`12`, `14`):** giải thích minh bạch đóng góp tuyến tính của từng tiêu chí điểm (Score Breakdown XAI — `14`) và đánh giá thực nghiệm độc lập hai tầng: `mAP@50`, `mAP@50:95` cho YOLO và `Precision@5`, `nDCG@5` qua 4 phiên bản đối chứng `A – B – C – D` cho hệ gợi ý (`12`).
7. **Thông tin dinh dưỡng có căn cứ (`10`, `11`):** tuyệt đối không suy đoán `gram` hay `kcal` từ ảnh RGB; hiển thị nhãn nhóm chất định tính có dẫn nguồn ở MVP (`Chế độ 1`) và hỗ trợ ước tính dinh dưỡng trên 100g theo USDA FoodData Central khi công thức có định lượng `grams` kiểm duyệt hoặc người dùng đổi khẩu phần (`Chế độ 2`).

## 2. Cấu trúc tài liệu

| Thư mục | Tài liệu chính | Mục đích |
|---|---|---|
| [01-requirements](01-requirements/README.md) | [SRS](01-requirements/SRS.md), [Use Cases](01-requirements/use-cases.md), [UML Diagram](01-requirements/use-case-diagram.puml), [User Stories & AC](01-requirements/user-stories.md), [Traceability](01-requirements/traceability-matrix.md) | Xác định **làm gì**, phân vai kiểm thử chéo và tiêu chí nghiệm thu (`FR-01`..`FR-18`, `NFR-01`..`NFR-14`, `BR-01`..`BR-12`) |
| [02-architecture](02-architecture/README.md) | [Kiến trúc 7 tầng](02-architecture/system-architecture.md), [Database & `pg_trgm`](02-architecture/database-design.md), [ERD](02-architecture/erd.mmd), [Data Dictionary](02-architecture/data-dictionary.md), [Bảo mật](02-architecture/security-and-deployment.md) | Xác định **hệ thống và cơ sở tri thức được xây như thế nào** (PostgreSQL `>= 15`, RLS + GRANT, EXIF privacy) |
| [03-api](03-api/README.md) | [Quy ước API](03-api/api-conventions.md), [OpenAPI 3.1](03-api/openapi.yaml), [Ví dụ mô phỏng](03-api/request-response-examples.md), [Postman](03-api/foodvision-ai.postman_collection.json) | Hợp đồng giao tiếp Frontend–Backend và danh mục 20 mã lỗi nghiệp vụ chuẩn |
| [04-ai-model](04-ai-model/README.md) | [Thiết kế AI & HITL](04-ai-model/ai-model-design.md), [Danh mục nhãn & Alias](04-ai-model/label-catalog.md), [Dữ liệu & `mAP@50:95`](04-ai-model/dataset-and-evaluation.md) | Thiết kế YOLO, lớp hỗ trợ CLIP/VLM, quy tắc rollback model và kiểm chứng minh bạch (`NFR-11`) |
| [05-recommendation](05-recommendation/README.md) | [Suy luận, MCDA, LR, MMR & XAI](05-recommendation/recommendation-design.md), [Dinh dưỡng USDA & Công thức](05-recommendation/nutrition-and-content.md) | Đặc tả thuật toán gợi ý (`Scoring v1.0` MVP & kiến trúc mở rộng `v1.1` 14 thành phần) và chính sách dinh dưỡng 2 tầng |
| [06-testing](06-testing/README.md) | [Kế hoạch kiểm thử](06-testing/test-plan.md), [47 TC & 10 Kịch bản bảo vệ](06-testing/test-cases.md), [Checklist nghiệm thu](06-testing/acceptance-checklist.md) | Nghiệm thu trên bằng chứng (`DEF-01`..`DEF-10`, `TC-01`..`TC-47`, `SEC`, `API`, `AI`, `UI`, `PERF`, `LEGAL`, `OPS`) |
| [07-decisions](07-decisions/README.md) | `ADR-001`…`ADR-012` | Hồ sơ quyết định kiến trúc và đánh đổi kỹ thuật |
| Chung | [Nguồn tham khảo](references.md), [Changelog](CHANGELOG.md) | Trích dẫn khoa học/kỹ thuật chính thống và lịch sử phiên bản |

## 3. Baseline kỹ thuật đề xuất

- **Client:** React + TypeScript + Vite + Tailwind CSS; Web responsive hỗ trợ trình duyệt di động, **không xây APK/iOS native ở MVP**.
- **Server:** Python + FastAPI (business API); phân tách rõ module nhận diện thị giác, chuẩn hóa tiếng Việt, suy luận/xếp hạng/cá nhân hóa và tính toán dinh dưỡng.
- **Nhận thức AI:** Ultralytics YOLO Object Detection fine-tune trên tập nhãn có bản quyền (`category != 'pantry'`) + lớp hỗ trợ ứng viên CLIP/VLM có kiểm soát cho vùng ảnh khó + cơ chế xác nhận HITL ($p_{\max} < \tau$); **chưa chốt biến thể/weights trước khi benchmark**.
- **Dữ liệu & Tri thức:** Supabase PostgreSQL (`>= 15`, bật `unaccent`, `pg_trgm` GIN index); Supabase Auth; Supabase Storage chỉ lưu ảnh minh họa công thức hợp pháp (tuyệt đối không lưu ảnh gốc của người dùng).
- **API contract:** OpenAPI 3.1, REST JSON; upload ảnh dùng `multipart/form-data`.

Thông số/giới hạn trong tài liệu được chia thành **(1) yêu cầu thiết kế**, **(2) mục tiêu kiểm thử**, **(3) kết quả thực nghiệm**. Chưa có kết quả thực nghiệm ở thời điểm phát hành tài liệu này.

## 4. Lộ trình triển khai 5 giai đoạn & Phân lớp ưu tiên (`P0` / `P1` / `P2+`)

| Giai đoạn | Thành phần kỹ thuật | Bàn giao kiểm thử & Mức ưu tiên |
|---|---|---|
| **1 — Dữ liệu & Logic nền** | `03` PostgreSQL KB, `04` Rule-based Reasoning, `10` Verified Retrieval, `13` Tiếng Việt (`pg_trgm`) | Kho công thức chuẩn, gia vị nền `pantry`, tìm kiếm có/không dấu/alias, suy luận trạng thái & lọc cứng (`P0`) |
| **2 — Bộ đề xuất cốt lõi** | `05` Weighted Coverage, `06` Tversky baseline, `07` MCDA Scoring, `09` MMR | API gợi ý (`Scoring v1.0` & mở rộng `v1.1` MCDA 5 tiêu chí + MMR) và baseline đối chứng Tversky (`P0`) |
| **3 — Thị giác, HITL & CMS** | `01` YOLO, `02` CLIP/VLM helper, `14` HITL & XAI + Admin CMS (`FR-09a`, `FR-13..15`) | Luồng ảnh (xoay EXIF & xóa GPS) → nhận diện → sửa nhãn HITL & bật/tắt gia vị → gợi ý có giải thích điểm (`P0`) |
| **4 — Cá nhân hóa & Dinh dưỡng** | `08` Logistic Regression, `11` Dinh dưỡng 2 tầng (Tags + USDA) + User Auth (`FR-09b..12`, `FR-16..17`) | Đăng nhập User, yêu thích, lịch sử opt-in, feedback upsert, học sở thích LR và ước tính USDA theo gram/khẩu phần (`P1`) |
| **5 — Kiểm chứng thực nghiệm** | `12` Đánh giá độc lập hai tầng & đối chứng `A – B – C – D` | Báo cáo `mAP@50:95` (không loại lớp yếu sau test), bảng `Precision@5` / `nDCG@5` (A/B/C/D), 47 TC & 10 kịch bản bảo vệ (`P0`/`P1`) |

**Không thực hiện (`P2+` / Ranh giới an toàn):** ước lượng khối lượng `gram` từ ảnh RGB không có vật chuẩn; tư vấn điều trị y khoa hoặc cam kết miễn trừ dị ứng lâm sàng tuyệt đối; cho LLM tự bịa nguyên liệu/bước nấu ngoài công thức kiểm duyệt; tự huấn luyện lại YOLO trực tiếp từ một lần sửa nhãn của người dùng mà không qua quy trình kiểm duyệt dữ liệu; ứng dụng mobile native.

## 5. Quy trình đóng góp và quản lý thay đổi

1. Đề xuất thay đổi ở issue/PR và nêu rõ mã yêu cầu (`FR`/`NFR`/`BR`/`UC`/`API`/`TC`/`DEF`/`ADR`) bị ảnh hưởng.
2. Cập nhật SRS nếu đổi nghiệp vụ; cập nhật ERD/Data Dictionary nếu đổi dữ liệu; cập nhật `openapi.yaml` trong cùng PR triển khai nếu mở rộng request/response; đồng bộ công thức trong `05-recommendation/`, ví dụ JSON trong `03-api/` và unit test trong `06-testing/test-cases.md`.
3. Nếu là quyết định ảnh hưởng kiến trúc hoặc thuật toán, viết/cập nhật ADR trong `07-decisions/`.
4. Thành viên phụ trách kỹ thuật và thành viên kiểm thử chéo (Cross-Tester) review độc lập trước khi merge vào nhánh chính.
5. Không commit `.env`, `service_role` secret, bộ dữ liệu ảnh vướng bản quyền, tài liệu nội bộ ngoài chuẩn hoặc file trọng số mô hình dung lượng lớn vào Git thường.
