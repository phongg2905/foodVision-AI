# Ma trận Truy vết Yêu cầu (Requirement Traceability Matrix — RTM)

**Phiên bản:** `0.9.0-draft` · **Trạng thái:** `Planned` (chưa đánh dấu `Pass` cho tới khi có bằng chứng thực nghiệm và kiểm thử chéo).  
**Đối chiếu:** [SRS](SRS.md) · [Use Cases](use-cases.md) · [User Stories & AC](user-stories.md) · [OpenAPI 3.1](../03-api/openapi.yaml) · [Test Cases](../06-testing/test-cases.md)

> **Quy tắc phân quyền sở hữu (`Primary Owner`):** Mỗi yêu cầu chỉ gắn **một vai trò chịu trách nhiệm chính** (`PM / Content Lead`, `BE / DB Lead`, `AI Lead`, hoặc `FE / QA Lead`) để rõ đầu mối giải trình. Việc nghiệm thu tuân thủ nguyên tắc **kiểm thử chéo (Cross-Testing)** quy định tại Mục 1.3 của [`SRS.md`](SRS.md).

---

## 1. Truy vết Yêu cầu Chức năng (`FR-01`..`FR-18` ↔ `UC` ↔ `US/AC` ↔ `API/SDK` ↔ `TC`)

Tất cả đường dẫn REST API bên dưới được hiểu theo tiền tố `/api/v1` (trừ các lệnh gọi trực tiếp Supabase Auth SDK).

| Mã FR | Ưu tiên | Use Case | User Story & Gherkin AC | API Endpoint / SDK phụ trách | Test Cases (`06-testing/test-cases.md`) | Primary Owner | Trạng thái |
|---|---|---|---|---|---|---|---|
| **FR-01** | P0 | `UC-01` | `US-01` (`AC-01`, `AC-02`) | `GET /recipes` | `TC-01`, `TC-02` | `BE / DB Lead` | Planned |
| **FR-02** | P0 | `UC-01` | `US-02` (`AC-03`) | `GET /recipes/{recipe_id}` | `TC-03` | `BE / DB Lead` | Planned |
| **FR-03** | P0 | `UC-02` | `US-03` (`AC-04`, `AC-06`) | `POST /ai/detect` | `TC-04`, `TC-05`, `TC-06`, `TC-43`, `SEC-05`, `API-03` | `AI Lead` | Planned |
| **FR-04** | P0 | `UC-02` | `US-03` (`AC-05`, `AC-06`) | `POST /ai/detect` | `TC-07`, `TC-29`, `TC-30`, `AI-01`, `AI-02`, `AI-03` | `AI Lead` | Planned |
| **FR-05** | P0 | `UC-03` | `US-04` (`AC-07`, `AC-08`, `AC-09`) | `GET /ingredients`; Client state → `POST /recommendations` | `TC-08`, `TC-09`, `TC-31`, `TC-36`, `TC-37`, `API-04` | `FE / QA Lead` | Planned |
| **FR-06** | P0 | `UC-04` | `US-05` (`AC-09`, `AC-10`, `AC-11`, `AC-12`) | `POST /recommendations` | `TC-10`, `TC-11`, `TC-12`, `TC-32`, `TC-33`, `TC-34`, `TC-37` | `BE / DB Lead` | Planned |
| **FR-07** | P0 | `UC-04` | `US-06` (`AC-13`) | `POST /recommendations`; `GET /recipes` | `TC-13`, `TC-14`, `TC-35` | `BE / DB Lead` | Planned |
| **FR-08** | P0 | `UC-05` | `US-07` (`AC-14`) | `GET /recipes/{recipe_id}`; `GET /nutrition-tags` | `TC-15` | `PM / Content Lead` | Planned |
| **FR-09a** | P0 | `UC-06` | `US-08` (`AC-15`, `AC-16`, `AC-17`) | Supabase Auth SDK (`signInWithPassword`, `resetPasswordForEmail`, `signOut({ scope: 'local' })`) | `TC-16`, `TC-40`, `TC-46`, `SEC-03` | `BE / DB Lead` | Planned |
| **FR-09b** | P1 | `UC-06` | `US-08` (`AC-15`, `AC-16`, `AC-17`) | Supabase Auth SDK (`signUp`, `signInWithPassword`, `resetPasswordForEmail`, `signOut({ scope: 'local' })`) | `TC-16`, `TC-40`, `TC-46`, `SEC-07` | `FE / QA Lead` | Planned |
| **FR-10** | P1 | `UC-06` | `US-09` (`AC-18`) | `GET /favorites`; `POST /favorites`; `DELETE /favorites/{recipe_id}` | `TC-17`, `TC-18`, `SEC-01`, `SEC-04` | `BE / DB Lead` | Planned |
| **FR-11** | P1 | `UC-07` | `US-10` (`AC-20`) | `POST /feedback` | `TC-19`, `TC-45`, `TC-47`, `SEC-06` | `BE / DB Lead` | Planned |
| **FR-12** | P1 | `UC-07` | `US-11` (`AC-19a`, `AC-19b`) | `POST /ai/detect` (`save_history`); `GET /scan-sessions`; `GET /scan-sessions/{scan_id}`; `DELETE /scan-sessions/{scan_id}` | `TC-20`, `TC-28`, `TC-47`, `SEC-02`, `SEC-04`, `SEC-06`, `UI-04` | `BE / DB Lead` | Planned |
| **FR-13** | P0 | `UC-08` | `US-12` (`AC-21`, `AC-22a`, `AC-22b`) | `POST /admin/recipes`; `GET /admin/recipes`; `GET /admin/recipes/{recipe_id}`; `PATCH /admin/recipes/{recipe_id}`; `PATCH /admin/recipes/{recipe_id}/status` | `TC-21`, `TC-22`, `TC-38`, `SEC-03` | `PM / Content Lead` | Planned |
| **FR-14** | P0 | `UC-08` | `US-13` (`AC-23`, `AC-24`) | `GET /admin/ingredients`; `POST /admin/ingredients`; `PATCH /admin/ingredients/{ingredient_id}` | `TC-23`, `TC-39` | `PM / Content Lead` | Planned |
| **FR-15** | P0 | `UC-09` | `US-14` (`AC-25`, `AC-26`) | `GET /admin/ai-models`; `POST /admin/ai-models`; `PATCH /admin/ai-models/{model_id}/status`; `GET /admin/ai-labels`; `POST /admin/ai-labels`; `PATCH /admin/ai-labels/{label_id}` | `TC-24`, `TC-41`, `TC-42`, `TC-44`, `AI-03` | `AI Lead` | Planned |
| **FR-16** | P1 | `UC-09` | `US-14` (`AC-27`) | `GET /admin/nutrition-tags`; `POST /admin/nutrition-tags`; `PATCH /admin/nutrition-tags/{tag_id}`; `PUT /admin/ingredients/{ingredient_id}/nutrition-tags` | `TC-25` | `PM / Content Lead` | Planned |
| **FR-17** | P1 | `UC-10` | `US-14` (`AC-28`) | `GET /admin/audit-logs` | `TC-26` | `BE / DB Lead` | Planned |
| **FR-18** | P0 | `UC-02`, `UC-03` | `US-04` (`AC-08`) | `GET /ingredients`; `POST /recommendations` (`scan_id=null`) | `TC-27`, `TC-09`, `UI-02` | `FE / QA Lead` | Planned |

---

## 2. Truy vết Yêu cầu Phi chức năng (`NFR-01`..`NFR-14` ↔ Thiết kế ↔ Kiểm thử)

| Mã NFR | Nhóm chất lượng | Tài liệu thiết kế chuẩn | Mã kịch bản kiểm thử (`06-testing/test-cases.md`) | Primary Owner | Trạng thái |
|---|---|---|---|---|---|
| **NFR-01** | Khả dụng & Tương thích trình duyệt (`360px`/`768px`/`1366px`) | [`system-architecture.md`](../02-architecture/system-architecture.md) | `UI-01`, `UI-02`, `UI-04` | `FE / QA Lead` | Planned |
| **NFR-02** | Hiệu năng suy luận AI (`p95 <= 10.0s` CPU / `<= 3.0s` GPU) | [`ai-model-design.md`](../04-ai-model/ai-model-design.md) | `PERF-01`, `TC-30` | `AI Lead` | Planned |
| **NFR-03** | Hiệu năng API gợi ý (`p95 <= 1.0s`) & tra cứu (`<= 500ms`) | [`recommendation-design.md`](../05-recommendation/recommendation-design.md), [`api-conventions.md`](../03-api/api-conventions.md) | `PERF-02`, `TC-36` | `BE / DB Lead` | Planned |
| **NFR-04** | Xác thực JWT, bảo vệ vai trò Admin & kế thừa `Admin --\|> User` | [`security-and-deployment.md`](../02-architecture/security-and-deployment.md), [`ADR-011`](../07-decisions/ADR-011-admin-role-inheritance.md) | `SEC-01`, `SEC-03`, `SEC-07`, `TC-16`, `TC-46` | `BE / DB Lead` | Planned |
| **NFR-05** | Bảo mật dữ liệu cấp dòng (`RLS` + `GRANT`/`REVOKE`) | [`database-design.md`](../02-architecture/database-design.md), [`ADR-002`](../07-decisions/ADR-002-supabase.md) | `SEC-01`, `SEC-04`, `SEC-06`, `TC-28` | `BE / DB Lead` | Planned |
| **NFR-06** | Quyền riêng tư ảnh (không lưu ảnh gốc, xoay EXIF, xóa GPS) | [`security-and-deployment.md`](../02-architecture/security-and-deployment.md), [`ADR-007`](../07-decisions/ADR-007-image-privacy.md), [`ADR-010`](../07-decisions/ADR-010-image-exif-and-validation-errors.md) | `SEC-02`, `TC-20`, `TC-43` | `AI Lead` | Planned |
| **NFR-07** | An toàn thông tin dinh dưỡng (định tính có nguồn, miễn trừ dị ứng) | [`nutrition-and-content.md`](../05-recommendation/nutrition-and-content.md), [`ADR-004`](../07-decisions/ADR-004-nutrition.md) | `TC-15`, `TC-25` | `PM / Content Lead` | Planned |
| **NFR-08** | Chuẩn hóa 20 mã lỗi, `X-Request-Id`, `/health` & structured log | [`api-conventions.md`](../03-api/api-conventions.md), [`ADR-010`](../07-decisions/ADR-010-image-exif-and-validation-errors.md) | `API-01`, `OPS-01` | `BE / DB Lead` | Planned |
| **NFR-09** | Toàn vẹn CSDL (PG `>= 15`) & khả năng tái lập migration/seed | [`database-design.md`](../02-architecture/database-design.md), [`data-dictionary.md`](../02-architecture/data-dictionary.md), [`ADR-012`](../07-decisions/ADR-012-feedback-uniqueness-and-context.md) | `OPS-02`, `TC-38`, `TC-39`, `TC-45`, `TC-47` | `BE / DB Lead` | Planned |
| **NFR-10** | Đồng bộ hợp đồng OpenAPI 3.1 với ứng dụng FastAPI | [`openapi.yaml`](../03-api/openapi.yaml) | `API-02` | `BE / DB Lead` | Planned |
| **NFR-11** | Minh bạch đánh giá AI (cấm loại lớp yếu sau test, công bố per-class `AP50`, `Recall`, `N_test`) | [`dataset-and-evaluation.md`](../04-ai-model/dataset-and-evaluation.md), [`label-catalog.md`](../04-ai-model/label-catalog.md) | `AI-01`, `AI-02`, `AI-03` | `AI Lead` | Planned |
| **NFR-12** | Ngôn ngữ hiển thị tiếng Việt UTF-8 & tìm kiếm có dấu/không dấu | [`SRS.md`](SRS.md) | `UI-03`, `TC-01`, `TC-36` | `FE / QA Lead` | Planned |
| **NFR-13** | Bản quyền nội dung/model & tuân thủ Luật BV DLCN số 91/2025/QH15 | [`security-and-deployment.md`](../02-architecture/security-and-deployment.md), [`ADR-005`](../07-decisions/ADR-005-yolo-licensing.md) | `LEGAL-01`, `SEC-02`, `TC-28` | `PM / Content Lead` | Planned |
| **NFR-14** | Bảo vệ tài nguyên, kiểm tra magic bytes, rate limit & concurrency | [`security-and-deployment.md`](../02-architecture/security-and-deployment.md), [`api-conventions.md`](../03-api/api-conventions.md) | `SEC-05`, `API-03`, `API-04`, `OPS-03`, `TC-05`, `TC-06`, `TC-30` | `BE / DB Lead` | Planned |

---

## 3. Tóm tắt độ phủ kiểm thử (Coverage Summary)

- **Yêu cầu chức năng (`FR`):** 19/19 mục (`FR-01`..`FR-18`, tách `FR-09a` và `FR-09b`) đều có Use Case, User Story, Gherkin AC, API/SDK và Test Case.
- **Yêu cầu phi chức năng (`NFR`):** 14/14 mục (`NFR-01`..`NFR-14`) đều được ánh xạ tới tài liệu thiết kế và kịch bản kiểm thử chuyên biệt (`UI`, `PERF`, `SEC`, `API`, `AI`, `LEGAL`, `OPS`).
- **Quy tắc nghiệp vụ (`BR`):** 12/12 quy tắc (`BR-01`..`BR-12`) được bao phủ trực tiếp bởi bộ 30 kịch bản Gherkin (`AC-01`..`AC-28`, gồm `AC-19a/b`, `AC-22a/b`) và 47 ca kiểm thử chức năng (`TC-01`..`TC-47`).
