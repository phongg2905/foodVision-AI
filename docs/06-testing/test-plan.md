# Test Plan — Kế hoạch Kiểm thử & Kiểm định Thực nghiệm

**Mã:** `FV-TEST-001` · **Phiên bản:** `1.0.0` · **Trạng thái thực thi:** `Planned` · **Đối chiếu:** [SRS](../01-requirements/SRS.md), [Traceability Matrix](../01-requirements/traceability-matrix.md), [Dataset & Evaluation](../04-ai-model/dataset-and-evaluation.md).

## 1. Mục tiêu, 5 trục kiểm thử độc lập và Kiểm thử chéo

Hệ thống được kiểm định trên **5 trục độc lập**:

1. **Functional / HITL / UI:** tải ảnh (tự xoay EXIF Orientation), cảnh báo xác nhận HITL khi $\text{confidence} < \tau$, chỉnh sửa nguyên liệu chính, bật/tắt thanh gia vị nền (`excluded_pantry_ids`), tìm kiếm tiếng Việt (`unaccent` + `pg_trgm` + alias), gợi ý món, lọc thời gian/ẩm thực, xem công thức, Auth/Favorites/Feedback, Admin CMS.
2. **API / Database:** hợp đồng OpenAPI 3.1 (`openapi.yaml`), danh mục 20 mã lỗi chuẩn, ràng buộc `PK`/`FK`/`CHECK`, `UNIQUE NULLS NOT DISTINCT` (PostgreSQL `>= 15`), `ON DELETE CASCADE`, tính nhất quán transaction.
3. **AI Thị giác:** đo `Precision`, `Recall`, `F1`, `mAP@50` và `mAP@50:95` trên tập `test` giữ cố định (chia theo `scene/session`), tuân thủ nghiêm ngặt `NFR-11` (chốt danh sách lớp trước khi chạy test, **nghiêm cấm loại bỏ lớp có kết quả thấp sau khi chạy test để nâng khống `mean mAP50`**).
4. **Thực nghiệm Hệ gợi ý & Cá nhân hóa (Giai đoạn 5 — `AI-04`):** đo `Precision@5`, `nDCG@5`, `Constraint Violation Rate` và `Intra-list Diversity` trên tập $\ge 100$ tình huống độc lập để đối chứng **4 biến thể Ranker: A (Truy xuất đơn giản) – B (Tversky) – C (Weighted Coverage + MCDA + MMR) – D (Cá nhân hóa Logistic Regression)**.
5. **Security / Privacy / Performance:** phân quyền `Admin --|> User --|> Guest`, `RLS` + `GRANT`/`REVOKE`, không lưu ảnh gốc, xóa sạch metadata EXIF/GPS trong RAM, lịch sử `opt-in`, độ trễ `p50/p95`.

> **Nguyên tắc kiểm thử chéo (Cross-Testing — bắt buộc theo Mục 1.3 `SRS.md`):** Thành viên lập trình một mô-đun không được tự đánh dấu `Pass` nghiệm thu cuối cùng cho mô-đun đó; kết quả phải do thành viên giữ vai trò kiểm thử chéo độc lập thực thi và ký xác nhận bằng chứng. Một luồng demo chạy mượt không thay thế báo cáo số liệu thực nghiệm; ngược lại, `mAP` của YOLO cao cũng không tự chứng minh hệ gợi ý xếp hạng tốt.

## 2. Loại kiểm thử và công cụ

| Loại kiểm thử | Công cụ đề xuất | Bằng chứng thu thập |
|---|---|---|
| Backend & Math unit tests | `pytest` | Kết quả kiểm tra `Scoring v1.0` (`89.0`, `68.1`) và `MATH-01`..`MATH-07` (`IoU`, `CLIP`, `Coverage`, `Tversky`, `MCDA/XAI 80.83`, `LR`, `MMR`, `USDA 104.5 kcal`) |
| Contract / API | `pytest` + `HTTPX` / OpenAPI schema validator | Snapshot request/response, báo cáo khớp `/openapi.json` và 20 mã lỗi |
| Database, RLS & `pg_trgm` | Supabase SQL tests + script `anon`/User A/B/Admin | Log allow/deny RLS, kết quả tìm kiếm alias (`đậu hũ`/`đậu phụ`), migration hash |
| AI Vision Evaluation | `Ultralytics val` (`metrics.box.map`, `map50`) | Bảng `mAP@50`, `mAP@50:95`, per-class `AP50`/`Recall`/`N_test`, confusion matrix |
| Ranker Ablation (A/B/C/D) | `scikit-learn` (`ndcg_score`) + script benchmark | Bảng so sánh `Precision@5`, `nDCG@5`, `Constraint Violation Rate`, `ILD@5` |
| Frontend & E2E browser | Vitest / Playwright (nếu nhóm chọn) | Ảnh màn hình `360px`/`768px`/`1366px`, trace/log (ẩn dữ liệu nhạy cảm) |
| Performance | `locust` / `k6` hoặc script đo tải ổn định | Báo cáo `p50`/`p95`, CPU/RAM, `MAX_CONCURRENT_INFERENCES` |

## 3. Môi trường và dữ liệu mẫu tối thiểu

**Local:** Frontend Vite (`localhost:5173`), Backend FastAPI (`localhost:8000`), Supabase project dev (PostgreSQL `>= 15`), model weights hợp lệ. **Staging/Demo:** dữ liệu kiểm thử không chứa PII thật, không commit `.env`. Khi báo cáo kết quả phải ghi rõ OS, trình duyệt, `model_version`, `dataset_version`, phần cứng CPU/GPU và `commit SHA`.

### 3.1. Dữ liệu mẫu kiểm thử chức năng

- Tối thiểu 10 công thức `published` phủ cả 3 nhóm `VN` / `EU` / `US`, có món $\le 15$ phút và $> 15$ phút, có cả nguyên liệu bắt buộc/tùy chọn và nhiều phương pháp chế biến (`canh`, `xao`, `kho`, `salad`...) để kiểm thử bộ lọc và MMR.
- Một công thức `draft` và một công thức `archived` để kiểm thử ẩn khỏi API công khai (`404 RECIPE_NOT_FOUND`).
- Danh mục nguyên liệu gồm đầy đủ 5 gia vị nền `category = 'pantry'` (muối, đường, nước mắm, dầu ăn, tiêu xay), `>= 8` nguyên liệu chính được ánh xạ nhãn YOLO và các cặp từ đồng nghĩa vùng miền (`đậu hũ` / `đậu phụ`, `bắp` / `ngô`, `dưa leo` / `dưa chuột`).
- Tài khoản `User A`, `User B` và `Admin` riêng biệt; phiên `Guest` không gửi token.
- Bộ ảnh kiểm thử độc lập: ảnh rõ 1–3 nguyên liệu, ảnh chụp dọc có cờ `EXIF Orientation != 1` kèm tọa độ GPS mẫu, ảnh mờ/ngoài danh mục (`detections=[]`), file `> 5 MiB`, file sai định dạng (`.pdf`, `.tiff`) và file `.jpg` giả bị hỏng byte.

### 3.2. Thiết kế thực nghiệm đối chứng Ranker (`AI-04` — Giai đoạn 5)

- Xây dựng bộ **$\ge 100$ tình huống đầu vào** (tập nguyên liệu xác nhận, gia vị báo thiếu, ràng buộc thời gian/ẩm thực/dị ứng) được người chấm độc lập gán nhãn mức độ phù hợp $\text{rel} \in \{0, 1, 2, 3\}$ theo rubric thống nhất trước khi chạy thuật toán.
- Chạy cùng dữ liệu cho 4 biến thể **A, B ($\alpha=0.3, \beta=2.0$), C, D**; đối với biến thể **D (Logistic Regression)**, bắt buộc chia tập tương tác theo thời gian (*temporal split*) để tránh rò rỉ dữ liệu tương lai vào quá trình học $\theta_u$.

## 4. Kế hoạch kiểm thử theo 5 giai đoạn triển khai

| Giai đoạn | Hạng mục triển khai | Trọng tâm kiểm thử nghiệm thu |
|---|---|---|
| **Giai đoạn 1 (`P0` MVP)** | PostgreSQL >= 15, tìm kiếm `pg_trgm`, YOLO + EXIF, HITL + thanh `pantry`, `Scoring v1.0`, dinh dưỡng Tầng 1, Admin CMS | Toàn bộ `TC-01`..`TC-47` cốt lõi, 20 mã lỗi API, `SEC-01`..`07`, unit test `Scoring v1.0` (`89.0`, `68.1`) |
| **Giai đoạn 2 (`Scoring v1.1`)** | Suy luận 3 trạng thái (`READY`/`UNKNOWN`/`MISSING_CONFIRMED`), lọc cứng `BLOCKED`, Weighted Coverage, MCDA 5 tiêu chí, HITL $\tau$, XAI | `DEF-02`..`DEF-05`, `DEF-10`, unit test `MATH-02`..`MATH-05` (`80.83`, `0%` lọt dị ứng) |
| **Giai đoạn 3 (Khẩu phần & USDA)** | Quy đổi khẩu phần tuyến tính $n_{\text{new}}/n_{\text{base}}$ & dinh dưỡng Tầng 2 USDA per-100g | `DEF-09`, unit test `MATH-07` (`104.5 kcal` → `209.0 kcal`), kiểm tra ẩn Tầng 2 khi thiếu `grams` |
| **Giai đoạn 4 (Học sở thích, MMR & CLIP)** | Logistic Regression ($\theta_u$, cold-start $\lambda_{\text{pers}}$), tái xếp hạng MMR, nhánh phụ CLIP tùy chọn | `DEF-08`, unit test `MATH-01`, `MATH-05`, `MATH-06` (`0.412 < 0.556`) |
| **Giai đoạn 5 (Thực nghiệm & Bảo vệ)** | Đánh giá độc lập YOLO + đối chứng 4 biến thể Ranker A/B/C/D + diễn tập demo | `AI-01`..`AI-04`, `DEF-01`..`DEF-10`, `PERF-01`..`02`, `LEGAL-01`, kiểm thử chéo ký duyệt |

## 5. Điều kiện vào / ra (Entry & Exit Criteria)

- **Entry:** Hoàn tất review SRS, RTM, `openapi.yaml`, script migration + seed chạy sạch trên DB trống (`OPS-02`), chốt danh sách lớp `dataset_ready` và cấu hình biến môi trường an toàn.
- **Exit MVP (`P0`):**
  - Không còn lỗi mức `Blocker` hoặc `Critical` trên chuỗi `ảnh/nhập tay → HITL & pantry → gợi ý → chi tiết công thức`.
  - 100% ca kiểm thử thuộc `FR` nhóm `P0` đạt qua kiểm thử chéo; các hạng mục `P1` chưa triển khai phải ghi rõ trạng thái thực tế.
  - Đạt toàn bộ `SEC-01`..`SEC-07`, `API-01`..`API-04` và `LEGAL-01`; không lưu ảnh gốc, xóa sạch EXIF/GPS.
  - Có báo cáo đo lường thật cho YOLO (`Precision`, `Recall`, `mAP@50`, `mAP@50:95`, per-class `AP50`/`N_test`) và độ trễ `p50`/`p95` trên máy demo (tuyệt đối không ghi số mục tiêu thành số đo).
- **Exit Mở rộng (`P1` — Bảo vệ đầy đủ 14 thành phần):** Hoàn thành thêm `DEF-01`..`DEF-10`, `MATH-01`..`MATH-07` và bảng đối chứng `AI-04` (A/B/C/D).

## 6. Phân loại mức độ nghiêm trọng lỗi & Mẫu ghi kết quả

| Mức độ | Diễn giải | Ví dụ |
|---|---|---|
| **Blocker** | Chặn đứng luồng chính hoặc lộ dữ liệu trái phép | `/recommendations` luôn lỗi `500`, vượt quyền Admin hoặc lộ dữ liệu giữa User A và User B |
| **Critical** | Sai logic cốt lõi hoặc gợi ý gây hiểu nhầm nghiêm trọng | Món thiếu nguyên liệu bắt buộc lại gắn `ready`, lọt món chứa dị ứng đã lọc, tự suy `kcal` từ ảnh |
| **Major** | Hỏng tính năng `P1` hoặc lỗi bố cục trên mobile | Lưu `favorites` lỗi với JWT hợp lệ, vỡ giao diện ở khung nhìn `360px` |
| **Minor** | Lỗi trình bày/nhãn văn bản nhỏ không sai nghiệp vụ | Lệch căn lề nhẹ, thông báo chưa đồng nhất thuật ngữ |

**Mẫu bản ghi thực thi kiểm thử:** `Test ID` · `Build Commit SHA` (không ghi `latest`) · `Environment (OS/Browser/PG/Model Version)` · `Input Fixture` · `Expected` · `Actual` · `Status (Not run / Pass / Fail / Blocked)` · `Evidence Link` · `Cross-Tester & Timestamp`.
