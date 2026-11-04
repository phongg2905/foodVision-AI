# FoodVision AI Constitution

## Core Principles

### I. Docs-as-Single-Source-of-Truth & Traceability
Thư mục `docs/` (phiên bản `0.9.1-draft` tiến tới `1.0.0-baseline`) là nguồn chân lý chuẩn (Single Source of Truth) về yêu cầu, kiến trúc, hợp đồng dữ liệu và thuật toán của dự án.
- Mọi tính năng, kế hoạch (`plan.md`) và danh sách công việc (`tasks.md`) sinh ra qua Spec Kit **PHẢI** tham chiếu trực tiếp đến các mã định danh trong `docs/`: `FR-01`..`FR-18`, `NFR-01`..`NFR-14`, `BR-01`..`BR-12`, `UC-01`..`UC-10`, `US-01`..`US-14`, `AC-01`..`AC-28`, `TC-01`..`TC-47`, `MATH-01`..`MATH-07`, `DEF-01`..`DEF-10` và `ADR-001`..`ADR-012`.
- Không sao chép dư thừa hoặc tự ý thay đổi công thức toán học, cấu trúc bảng hay quy tắc nghiệp vụ trong `specs/` trái với `docs/`. Nếu cần thay đổi thiết kế, **PHẢI** cập nhật đồng bộ tài liệu tương ứng trong `docs/` và ghi nhận ADR mới nếu ảnh hưởng kiến trúc.

### II. Decoupled 7-Layer Intelligence Architecture
Hệ thống **PHẢI** duy trì sự phân tách rõ ràng giữa 7 tầng thông minh (14 thành phần kỹ thuật — `TP 01`..`TP 14`) theo `ADR-001` và `ADR-003`:
- **Tầng Nhận thức (`TP 01` YOLO, `TP 02` CLIP/VLM helper, `TP 14` HITL):** Chỉ phụ trách tiền xử lý ảnh, phát hiện đối tượng, gợi ý ứng viên vùng khó và nhận xác nhận từ người dùng (`Human-in-the-loop` khi $\text{confidence} < \tau = 0.80$). Tuyệt đối không trộn lẫn logic xếp hạng món ăn vào module thị giác.
- **Tầng Tri thức & Suy luận (`TP 03` PostgreSQL KB, `TP 04` 3-valued Rule Reasoning, `TP 10` Verified Retrieval, `TP 13` Vietnamese Search `unaccent` + `pg_trgm`):** Chuẩn hóa tiếng Việt có/không dấu, từ đồng nghĩa vùng miền, suy luận 3 trạng thái (`confirmed_available`, `confirmed_missing`, `unknown`) kết hợp 5 gia vị nền (`category = 'pantry'`, `ADR-008`) và lọc cứng ràng buộc (`BLOCKED` / `READY` / `UNKNOWN` / `MISSING_CONFIRMED`).
- **Tầng Ra quyết định, Cá nhân hóa & Giải thích (`TP 05` Weighted Coverage, `TP 06` Tversky baseline, `TP 07` MCDA 5 tiêu chí, `TP 08` Logistic Regression, `TP 09` MMR, `TP 11` Dinh dưỡng 2 tầng, `TP 14` XAI Score Breakdown):** Độc lập, vượt qua 100% bài kiểm thử toán học `MATH-01`..`MATH-07` và thực nghiệm đối chứng `A – B – C – D` (`TP 12`).

### III. Safety, Privacy & Non-Hallucination Guardrails (NON-NEGOTIABLE)
Các ranh giới an toàn sau đây là bất khả xâm phạm trong mọi dòng code:
- **Quyền riêng tư ảnh (`ADR-007`, `ADR-010`, `BR-09`):** Backend **PHẢI** tự động xoay chuẩn theo `EXIF Orientation` và xóa sạch toàn bộ metadata `EXIF/GPS` ngay trên RAM trước khi suy luận, giải phóng bộ nhớ trong khối `finally`; **TUYỆT ĐỐI KHÔNG** lưu ảnh nguyên liệu gốc của người dùng xuống đĩa hay Supabase Storage. Lịch sử nhận diện chỉ lưu metadata khi người dùng đã đăng nhập và bật `save_history = true`.
- **Chống ảo giác công thức (`TP 10`, `BR-05`):** Chỉ truy xuất các công thức có `status = 'published'` đã kiểm duyệt trong PostgreSQL; **TUYỆT ĐỐI KHÔNG** dùng LLM tự sinh nguyên liệu, liều lượng hay bước nấu ngoài cơ sở tri thức.
- **Chính sách dinh dưỡng có căn cứ (`ADR-004`, `BR-03`, `BR-06`):** **TUYỆT ĐỐI KHÔNG** suy đoán khối lượng (`gram`) hay năng lượng (`kcal`) trực tiếp từ ảnh RGB. Chỉ hiển thị nhãn định tính có `source_url` ở Tầng 1 (`P0`) và ước tính dinh dưỡng trên 100g theo chuẩn USDA FoodData Central khi công thức có định lượng `grams` kiểm duyệt ở Tầng 2 (`P1`).
- **Kiểm soát nhãn & mô hình (`ADR-005`, `ADR-006`, `BR-12`):** Giữ cố định `ingredients.id` (UUID), ánh xạ qua `ai_labels.class_index` (`0..19`) theo phiên bản model; tuyệt đối không gán nhãn YOLO vào nhóm gia vị nền (`category = 'pantry'`).

### IV. Contract-First API & Database Integrity
- **API Contract (`docs/03-api/openapi.yaml`, `ADR-010`):** Mọi endpoint giữa Frontend và Backend **PHẢI** tuân thủ đúng schema OpenAPI 3.1 (25 paths / 33 operations), cấu trúc envelope chuẩn và danh mục 20 mã lỗi nghiệp vụ (`400`, `403`, `404`, `409`, `413`, `415`, `422`, `503`, `504`).
- **Database & Security (`docs/02-architecture/database-design.md`, `ADR-002`, `ADR-011`, `ADR-012`):** Sử dụng PostgreSQL `>= 15` trên Supabase (16 bảng cốt lõi `v1.0` + 4 bảng mở rộng `v1.1`) với `pgcrypto`, `unaccent`, chỉ mục GIN `pg_trgm`, unique partial index `idx_ai_models_single_active` và khóa `UNIQUE NULLS NOT DISTINCT` kèm `ON DELETE CASCADE` trên `recommendation_feedback`. Mọi bảng **PHẢI** bật Row Level Security (RLS) đi kèm `GRANT`/`REVOKE` tối thiểu theo phân quyền kế thừa `Admin --|> User --|> Guest`. Không bao giờ để lộ `SUPABASE_SERVICE_ROLE_KEY` ở phía client hoặc commit `.env` vào Git.

### V. Single-Owner Accountability & Cross-Testing (NON-NEGOTIABLE)
Dự án vận hành theo nguyên tắc **Đơn trách nhiệm (`1 Thẻ Trello = 1 Thành viên duy nhất`)** kết hợp **Kiểm thử chéo bắt buộc (`Cross-Testing`)**:
- **TV1 — Minh Thành (`@minhthanh4` — AI, ML & Data Content Lead — 6 thẻ):**
  - *Sở hữu:* `#7` (Seed Data `TP 03, 10`, Pantry, Alias, USDA), `#19` (Dataset YOLO 20 lớp `TP 01`), `#20` (Train YOLO, EXIF/GPS privacy, CLIP helper `TP 02` & `POST /api/v1/ai/detect`), `#23` (`TP 08` Logistic Regression + Cold-start $\lambda_{\text{pers}}$), `#13` (`TP 12a` Benchmark YOLO `mAP@50:95` & per-class `NFR-11`), `#15` (Kiểm thử chéo Backend/RLS/`MATH-01..07` & viết Chương AI).
  - *Kiểm thử chéo:* Kiểm thử độc lập toàn bộ API Backend, RLS & 7 bài toán học do **Phong (`TV2`)** lập trình.
- **TV2 — Phong Phạm (`@phongphm2` — Backend, DB, Reasoning & Recommendation Lead — 7 thẻ):**
  - *Sở hữu:* `#6` (PostgreSQL `>= 15`, 16+4 bảng, RLS, RPC & API `/recipes`, `/ingredients` `pg_trgm` `TP 03, 10, 13`), `#8` (`TP 04` Suy luận 3 trạng thái & Bộ lọc cứng), `#9` (`TP 05..07` Scoring `v1.0`, Weighted Coverage, Tversky, MCDA `v1.1`), `#10` (`TP 09` MMR & `POST /api/v1/recommendations`), `#21` (Cụm API Admin CMS `FR-09a`, `FR-13..17`), `#24` (Cụm API User `FR-10..12` & Engine Dinh dưỡng USDA/Khẩu phần `TP 11`), `#14` (`TP 12b` Thực nghiệm Ablation `A – B – C – D`, `OPS-01..03` & Kiểm thử chéo mô-đun AI).
  - *Kiểm thử chéo:* Kiểm thử độc lập mô-đun suy luận AI, EXIF privacy và Dataset do **Thành (`TV1`)** lập trình.
- **TV3 — Tâm Minh (`@tamminh6` — Frontend, HITL/XAI & QA Lead — 6 thẻ):**
  - *Sở hữu:* `#18` (Khung React + TS + Tailwind, UI Tra cứu, Tìm kiếm Tiếng Việt & Thanh 5 gia vị Pantry), `#11` (UI Danh sách Gợi ý `ready`/`missing`, Bộ lọc `<= 15p` & Chi tiết món), `#22` (`TP 14` UI Upload/BBox, Cảnh báo HITL $\text{conf} < \tau$ & Giải thích XAI), `#26` (UI Admin CMS), `#25` (UI Auth User `FR-09b`, Favorites, History kèm cảnh báo xóa cascade `ADR-012`, Feedback & Khẩu phần USDA), `#27` (Kiểm thử E2E 47 TC, 10 kịch bản `DEF-01..10`, `UI-01..04`, Đóng gói Demo & Báo cáo 7 Chương).
  - *Kiểm thử chéo:* Thực thi kiểm thử End-to-End và nghiệm thu giao diện/tích hợp trên toàn hệ thống.
- **Quy tắc nghiệm thu:** Người lập trình một chức năng **TUYỆT ĐỐI KHÔNG** tự đánh dấu `Pass` cuối cùng cho chức năng đó; bắt buộc phải do người kiểm thử chéo thực thi và ký xác nhận bằng chứng vào `docs/06-testing/acceptance-checklist.md`.

## 5-Stage Roadmap & Spec Kit Workflow Mapping

Bảng quản trị tiến độ chính thức tại Trello (`https://trello.com/b/DxNLNPlP/foodvision-ai`) chia dự án thành 5 giai đoạn với 19 thẻ đơn trách nhiệm:

1. **Giai đoạn 1 — Dữ liệu, Tri thức & Suy luận nền (`P0` — 4 thẻ):** Thẻ `#6` (`TV2`), Thẻ `#7` (`TV1`), Thẻ `#8` (`TV2`), Thẻ `#18` (`TV3`).
2. **Giai đoạn 2 — Bộ đề xuất cốt lõi Coverage, Tversky, MCDA & MMR (`P0` — 3 thẻ):** Thẻ `#9` (`TV2`), Thẻ `#10` (`TV2`), Thẻ `#11` (`TV3`).
3. **Giai đoạn 3 — Thị giác YOLO/CLIP, HITL, XAI & Admin CMS (`P0` — 5 thẻ):** Thẻ `#19` (`TV1`), Thẻ `#20` (`TV1`), Thẻ `#21` (`TV2`), Thẻ `#22` (`TV3`), Thẻ `#26` (`TV3`).
4. **Giai đoạn 4 — Cá nhân hóa LR, Dinh dưỡng 2 tầng USDA & User Auth (`P1` — 3 thẻ):** Thẻ `#23` (`TV1`), Thẻ `#24` (`TV2`), Thẻ `#25` (`TV3`).
5. **Giai đoạn 5 — Kiểm chứng thực nghiệm 2 tầng, 47 TC & Báo cáo (`P0`/`P1` — 4 thẻ):** Thẻ `#13` (`TV1`), Thẻ `#14` (`TV2`), Thẻ `#15` (`TV1`), Thẻ `#27` (`TV3`).

Khi một thành viên sử dụng các lệnh `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` và `/speckit-implement` cho thẻ Trello của mình:
- Đặt tên nhánh/gói đặc tả gắn với mã thẻ hoặc giai đoạn (ví dụ: `006-gd1-db-api`, `007-gd1-seed-data`, `018-gd1-fe-ui`) để không trùng số thứ tự khi merge giữa 3 thành viên.
- AI Agent **PHẢI** tự động nạp ngữ cảnh từ các tài liệu gốc trong `docs/` được liệt kê ở mục *Tài liệu tham chiếu* của thẻ Trello tương ứng.

## Governance

- Hiến pháp này (`constitution.md`) cùng bộ tài liệu `docs/` là kim chỉ nam cao nhất cho mọi quy trình phát triển tự động và thủ công trên kho mã nguồn `foodVision-AI`.
- Mọi bản kế hoạch (`plan.md`) và danh sách task (`tasks.md`) sinh ra qua Spec Kit **PHẢI** vượt qua bước kiểm tra *Constitution Check* dựa trên 5 nguyên tắc cốt lõi ở trên trước khi viết code.
- Mọi sửa đổi đối với Hiến pháp phải cập nhật phiên bản theo chuẩn Semantic Versioning (`MAJOR.MINOR.PATCH`) và đồng bộ với `docs/CHANGELOG.md`.

**Version**: 1.0.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-04
