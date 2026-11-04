# Test Cases — Danh sách Kiểm thử Chi tiết & Bộ Kịch bản Bảo vệ Học phần

**Phiên bản:** `0.9.1-draft` · **Trạng thái mặc định tất cả case:** `Not run`.  
**Tiền điều kiện chung:** API/Frontend chạy trên môi trường test, dữ liệu migration + seed khớp mô tả, người kiểm thử chéo ghi rõ `commit SHA`.  
**Mã phân nhóm:** `DEF` (10 kịch bản bảo vệ học phần cho kiến trúc 14 thành phần), `TC` (47 ca kiểm thử chức năng theo `FR`), `SEC` (bảo mật/quyền riêng tư), `API` (hợp đồng), `AI` (thị giác & thực nghiệm gợi ý), `UI` (giao diện), `PERF` (hiệu năng), `LEGAL` (pháp lý/bản quyền), `OPS` (vận hành), `MATH` (unit test công thức toán học).

---

## A. Bộ 10 Kịch bản Bảo vệ Học phần (`DEF-01`..`DEF-10`)

| Mã kịch bản | Thành phần kiểm chứng | Tình huống kiểm thử | Kết quả bắt buộc đạt | Liên kết chi tiết |
|---|---|---|---|---|
| **DEF-01** | TP 01, 14 | **Nhận diện đúng:** tải ảnh rõ quả cà chua (bao gồm ảnh chụp dọc điện thoại) | Tự xoay chuẩn EXIF, trả `bbox` chuẩn hóa và nhãn `Cà chua` ở trạng thái cho phép người dùng xác nhận | `TC-07`, `TC-43`, `AI-01` |
| **DEF-02** | TP 01, 02, 14 | **Ảnh mờ / vật thể ngoài danh mục:** tải ảnh rung mờ hoặc vật thể lạ | Hệ thống không tự chốt nhãn sai; trả `detections=[]` hoặc bật cảnh báo xác nhận HITL ($\text{conf} < \tau$) và cho sửa/nhập tay | `TC-27`, `AI-03` |
| **DEF-03** | TP 04, 14 | **Chưa biết (Open-World — `Scoring v1.1`):** chỉ xác nhận có cà chua (kèm dầu, muối), chưa khai báo trứng | Trạng thái trứng = `unknown`; món *"Cà chua xào trứng"* có `availability = "unknown"`, không gắn *"Nấu ngay"* | `MATH-02` |
| **DEF-04** | TP 04 | **Xác nhận thiếu thật:** người dùng báo thiếu nguyên liệu chính hoặc tắt gia vị nền bắt buộc (`excluded_pantry_ids`) | Món chuyển sang nhóm thiếu (`missing` ở `v1.0` / `missing_confirmed` ở `v1.1`), liệt kê chính xác nguyên liệu/gia vị cần mua thêm | `TC-11`, `TC-31`, `TC-32` |
| **DEF-05** | TP 03, 04 | **Lọc cứng an toàn dị ứng (`Scoring v1.1`):** người dùng khai báo dị ứng trứng (`egg`) | Mọi món chứa thành phần mang tác nhân `egg` (theo `ingredient_allergens` đã kiểm duyệt) bị `BLOCKED` trước xếp hạng và `0%` xuất hiện lại sau MMR | `MATH-02` |
| **DEF-06** | TP 13 | **Tìm kiếm tiếng Việt & đồng nghĩa:** nhập `ca chua`, `cà chua`, `dau hu`, `đậu phụ` | Cả 4 chuỗi đều ánh xạ chính xác về đúng mã `ingredient_id` chuẩn của *Cà chua* và *Đậu hũ* qua chuẩn hóa Unicode + `pg_trgm` | `TC-23`, `TC-36`, `MATH-07` |
| **DEF-07** | TP 05, 06, 12 | **Thực nghiệm đối chứng Ranker:** chạy trên tập $\ge 100$ tình huống chấm độc lập | Xuất bảng so sánh khách quan `nDCG@5` và `Precision@5` giữa các biến thể **A – B (Tversky) – C (Weighted + MCDA + MMR) – D (LR)** | `AI-04` |
| **DEF-08** | TP 08 | **Cá nhân hóa Logistic Regression:** cùng nguyên liệu đầu vào, 2 User có lịch sử `favorites`/`feedback` khác nhau | Thứ tự Top-K thay đổi phù hợp xu hướng sở thích đã học ($\theta_u$), đồng thời người dùng mới ($\lambda_{\text{pers}}=0$) vẫn nhận kết quả ổn định từ $S_{\text{base}}$ | `TC-17`, `TC-45`, `MATH-05` |
| **DEF-09** | TP 10, 11 | **Quy đổi khẩu phần & Dinh dưỡng hai tầng:** xem món ở Tầng 1 (`P0`) và đổi khẩu phần từ `2` lên `4` người ở món có đủ `grams` Tầng 2 (`P1`) | Tầng 1 chỉ hiện nhãn định tính kèm nguồn; Tầng 2 tính `kcal` theo USDA tăng tỷ lệ đúng công thức $\sum (m_i/100)V_{i,k}$ kèm cảnh báo; tuyệt đối không đoán `gram` từ ảnh | `TC-03`, `TC-15`, `MATH-07` |
| **DEF-10** | TP 07, 09, 14 | **Giải thích XAI & Đa dạng hóa MMR:** kiểm tra bảng phân rã điểm và danh sách Top-K | Ở `v1.0` điểm khớp `89.0`/`68.1`; ở `v1.1` tổng 5 điểm thành phần khớp khít điểm MCDA (`33.33+25.00+15.00+2.50+5.00 = 80.83`) và MMR giảm trùng lặp món cùng kiểu nấu | `TC-12`, `MATH-05`, `MATH-06` |

---

## B. Functional Test Cases (`TC-01`..`TC-47` — Hợp đồng `FR-01`..`FR-18`)

| ID | FR | Dữ liệu / Thao tác | Kết quả mong đợi |
|---|---|---|---|
| TC-01 | FR-01 | `GET /recipes?q=trung` (có dấu và không dấu) | Chỉ món `published` có từ khóa phù hợp, phân trang đúng (`limit`, `offset`, `total`) |
| TC-02 | FR-01 | `GET /recipes?cuisine_code=VN&max_total_minutes=15` | Chỉ món `VN` có `prep_minutes + cook_minutes <= 15` |
| TC-03 | FR-02 | `GET /recipes/{id}` món `published` / `draft` | `published` trả detail/steps và danh sách nguyên liệu có `category` (tách riêng `pantry`); `draft` trả `404 RECIPE_NOT_FOUND` với Guest |
| TC-04 | FR-03 | Upload ảnh JPEG `1 MB` hợp lệ | `200 OK` và JSON đúng schema (có thể `detections=[]`) |
| TC-05 | FR-03 | Upload file `> 5 MiB` | `413 IMAGE_TOO_LARGE`, không chạy suy luận |
| TC-06 | FR-03 | (1) Upload file sai MIME (`.pdf`, `.tiff`); (2) Upload file giả `.jpg` chứa nội dung text hỏng | (1) `415 UNSUPPORTED_IMAGE_TYPE`; (2) `422 INVALID_IMAGE`; không crash, không lưu file |
| TC-07 | FR-04 | Ảnh 2+ lớp từ test fixture | JSON có nhiều `bbox` chuẩn hóa `[0, 1]`, `suggested_ingredients` gộp trùng theo `ingredient_id` với `max_confidence` |
| TC-08 | FR-05 | AI trả 2 cà chua và 1 trứng; user gộp/sửa trên giao diện HITL | Request recommendation chỉ gồm ID nguyên liệu chính đã xác nhận, không trùng |
| TC-09 | FR-05 | User xóa tất cả `ingredient_ids` chính | UI ngăn gửi recommend; có hướng dẫn thêm tay tối thiểu 1 nguyên liệu chính |
| TC-10 | FR-06 | Recipe cần trứng+cà chua đều có, gia vị nền mặc định đủ (`excluded_pantry_ids=[]`) | `availability="ready"`, `missing_required_ingredient_ids=[]` |
| TC-11 | FR-06 | Recipe cần gà+cà chua, user chỉ có cà chua | `availability="missing"`, gà nằm trong `missing_required_ingredient_ids` |
| TC-12 | FR-06 | Cùng dữ liệu, so điểm tính tay và API | Khớp công thức `Scoring v1.0` `S = round(100*(0.55*C + 0.25*E + 0.10*T + 0.10*P), 1)`, xếp nhóm `ready` trước `missing` |
| TC-13 | FR-07 | `cuisine_codes=["VN"]` | Chỉ trả món thuộc `VN`, không có món `EU`/`US` |
| TC-14 | FR-07 | `max_total_minutes=15`, món `5+10` và `15+20` | Chỉ có món 15 phút; món 35 phút bị loại trước khi chấm điểm |
| TC-15 | FR-08 | Xem recipe có tag / không tag dinh dưỡng | Tag có `source_url` + tuyên bố miễn trừ định lượng/dị ứng; không có `kcal`/`gram` suy ra từ ảnh |
| TC-16 | FR-09a, FR-09b | Đăng ký (User) và đăng nhập (User/Admin) với Supabase Auth | Có session JWT hợp lệ; tài khoản Admin kế thừa quyền User (`Admin --\|> User`) gọi được các API của User |
| TC-17 | FR-10 | User A lưu món yêu thích 2 lần (`POST /favorites`) | Lần 1 trả `201`, lần 2 trả `200` idempotent; `GET /favorites` chỉ có 1 bản ghi |
| TC-18 | FR-10 | User A bỏ favorite (`DELETE /favorites/{recipe_id}`) | Trả `204 No Content`; danh sách yêu thích không còn món |
| TC-19 | FR-11 | User gửi `rating=3` và `rating=6` | `rating=3` → `201 Created`, `rating=6` → `422 VALIDATION_ERROR` |
| TC-20 | FR-12 | User detect `save_history=false` và `save_history=true` | `false`: `scan_id=null`, không lưu DB; `true`: tạo `scan_id`, lưu metadata và `scan_ingredients` khi gọi recommend kèm `scan_id` |
| TC-21 | FR-13 | Admin tạo recipe `draft` đủ dữ liệu | `201 Created`; recipe ở trạng thái `draft`, chưa hiện trên public API trước khi publish |
| TC-22 | FR-13 | Publish recipe thiếu `steps` (`steps=[]`) | `400 RECIPE_NOT_PUBLISHABLE` (`reason="missing_steps"`); không công bố |
| TC-23 | FR-14 | Admin tạo ingredient `slug` trùng; thêm alias hợp lệ (`đậu phụ` cho `đậu hũ`) | Trùng `slug` trả `409 DUPLICATE_SLUG`; thêm alias hợp lệ thành công, tìm kiếm có dấu/không dấu (`dau phu`, `dau hu`) qua `pg_trgm` trả đúng nguyên liệu chuẩn |
| TC-24 | FR-15 | Admin tạo model `draft`, gán đủ `ai_labels`, kích hoạt sang `active` | `200 OK`; model `active` cũ tự chuyển sang `archived` trong cùng giao dịch; nếu thiếu nhãn trả `400 MODEL_NOT_ACTIVATABLE` (`unmapped_class_indices`) |
| TC-25 | FR-16 | Admin gắn nutrition tag thiếu `source_url` hoặc URL sai định dạng | Trả `422 VALIDATION_ERROR`; khi có `source_url` hợp lệ trả `200 OK` và hiển thị đúng |
| TC-26 | FR-17 | Admin tạo/cập nhật recipe, ingredient, model và xem `GET /admin/audit-logs` | Có bản ghi `actor_id`, `action`, `entity_type`, `entity_id`, `created_at`; không lộ secret/token |
| TC-27 | FR-18 | AI trả `detections=[]` hoặc Guest/User mở thẳng luồng nhập tay | Tìm kiếm tiếng Việt/chọn nguyên liệu thủ công và gọi `/recommendations` hoạt động bình thường với `scan_id=null` |
| TC-28 | FR-12 | User A `GET`/`DELETE /scan-sessions/{scan_id}`; User B truy cập `scan_id` của A | A xem và xóa được (`204`); B nhận `404 SCAN_NOT_OWNED` |
| TC-29 | FR-04 | Gọi `POST /ai/detect` khi hệ thống chưa có model nào ở trạng thái `active` | Trả `503 MODEL_NOT_READY`, không crash worker |
| TC-30 | FR-04 | Gọi `POST /ai/detect` khi tác vụ suy luận vượt ngưỡng timeout cấu hình | Backend hủy tác vụ, giải phóng bộ nhớ tạm và trả `504 INFERENCE_TIMEOUT` |
| TC-31 | FR-05 | Màn hình xác nhận nguyên liệu hiển thị thanh gia vị sẵn có (`category='pantry'`) | Mặc định bật sẵn 5 gia vị nền; khi người dùng tắt "Nước mắm", payload gửi `excluded_pantry_ids: ["55555555-5555-4555-8555-555555555555"]` |
| TC-32 | FR-06 | Công thức "Trứng xào cà chua" có gia vị bắt buộc "Nước mắm"; gửi `excluded_pantry_ids=[nuoc_mam_id]` | `E=2/3`, `C=2/3.5`, `S=68.1`, `availability="missing"`, `missing_required_ingredient_ids` chứa `nuoc_mam_id` |
| TC-33 | FR-06 | Gửi `POST /recommendations` với `include_missing=false` | Chỉ trả về các món có `availability="ready"`, loại bỏ toàn bộ món `"missing"` |
| TC-34 | FR-06 | Gửi `POST /recommendations` khi không có công thức nào khớp nguyên liệu chính (`C=0`) hoặc bộ lọc | Trả `200 OK` với `items=[]`, `total=0`; không bịa công thức |
| TC-35 | FR-07 | Gửi `preferred_cuisine_codes=["VN"]` (không đặt `cuisine_codes`) | Món `VN` nhận `P=1.0`; món `EU`/`US` vẫn được giữ lại nhưng nhận `P=0.0` (giảm `10.0` điểm tổng ở `v1.0`) |
| TC-36 | FR-05 | Kiểm tra `GET /ingredients`: (1) gọi không token + kiểm tra `Cache-Control`; (2) tìm `?q=dau phu` (`no-store`); (3) lọc `category=pantry` và `exclude_pantry=true`; (4) gửi `category=pantry&exclude_pantry=true` | (1) `200 OK` chỉ trả nguyên liệu `is_active=true` kèm `max-age=300`; (2) khớp alias `Đậu hũ` với `Cache-Control: no-store`; (3) lọc đúng nhóm; (4) trả `422 INVALID_QUERY_PARAMS` |
| TC-37 | FR-05 | Kiểm tra `POST /recommendations`: (1) gửi UUID `pantry` trong `ingredient_ids`; (2) gửi UUID nguyên liệu chính (`category != 'pantry'`) trong `excluded_pantry_ids`; (3) gửi UUID không tồn tại hoặc `inactive` | Cả 3 bước đều bị chặn với `422 INVALID_INGREDIENTS` kèm chi tiết `details` tương ứng |
| TC-38 | FR-13 | Kiểm tra điều kiện công bố và sửa món `published`: (1) publish món chỉ có nguyên liệu `pantry`; (2) publish món chứa nguyên liệu `is_active=false`; (3) publish món có 1 bước với `estimated_minutes > prep_minutes + cook_minutes`; (4) gọi `PATCH /admin/recipes/{id}` trên món **đang `published`** làm vi phạm một trong các điều kiện trên | Cả 4 bước đều bị chặn với `400 RECIPE_NOT_PUBLISHABLE` và giữ nguyên trạng thái/dữ liệu hợp lệ trước đó |
| TC-39 | FR-14 | Kiểm tra `PATCH /admin/ingredients/{id}`: (1) đổi `category` sang `pantry` hoặc đặt `is_active=false` cho nguyên liệu đang thuộc công thức `published`; (2) đổi `category` sang `pantry` hoặc đặt `is_active=false` cho nguyên liệu đang được ánh xạ trong `ai_labels` của model `draft` hoặc `active` | Cả 2 bước đều bị chặn với `400 INGREDIENT_IN_USE` |
| TC-40 | FR-09a, FR-09b | Yêu cầu khôi phục mật khẩu qua email (`resetPasswordForEmail`) và đặt mật khẩu mới | Nhận liên kết khôi phục hợp lệ, cập nhật mật khẩu thành công và đăng nhập được bằng mật khẩu mới |
| TC-41 | FR-15 | Kiểm tra Rollback model `PATCH /admin/ai-models/{id}/status` (`archived -> active`): (1) Ca thành công: kích hoạt lại model `archived` có toàn bộ nhãn hợp lệ; (2) Ca thất bại: lấy một nguyên liệu chỉ thuộc model `archived` (không thuộc model `draft`/`active` hay món `published`), đổi `category` sang `'pantry'` (`200 OK`), sau đó gọi rollback model `archived` đó sang `active` | (1) Trả `200 OK`, model `active` cũ chuyển sang `archived`; (2) Bị chặn với `400 MODEL_NOT_ACTIVATABLE` (`invalid_mapped_class_indices`) |
| TC-42 | FR-15 | Gọi `POST /admin/ai-labels` hoặc `PATCH /admin/ai-labels/{id}` trên model đang ở trạng thái `active` hoặc `archived` | Bị chặn với `400 MODEL_IMMUTABLE` |
| TC-43 | FR-03 | Upload ảnh chụp dọc từ điện thoại có cờ `EXIF Orientation != 1` và chứa metadata GPS/EXIF | Backend tự xoay ảnh về đúng chiều hiển thị chuẩn trước khi suy luận, xóa sạch metadata EXIF/GPS trong bộ nhớ, tọa độ `bbox` trả về khớp với ảnh đã xoay |
| TC-44 | FR-15 | Gọi `POST` hoặc `PATCH /admin/ai-labels` trên model `draft` nhưng trỏ `ingredient_id` tới nguyên liệu có `category='pantry'` hoặc `is_active=false` | Bị chặn với `400 INVALID_LABEL_MAPPING` |
| TC-45 | FR-11 | Kiểm tra `POST /feedback` theo ngữ cảnh: (1) gửi lần 1 với `scan_id=null` rồi gửi lần 2 cùng `scan_id=null` với `rating` mới; (2) gửi tiếp cho cùng `recipe_id` nhưng kèm `scan_id=S1` hợp lệ của User | (1) Lần 1 trả `201 Created`, lần 2 trả `200 OK` (upsert cập nhật `updated_at`); (2) Tạo bản ghi mới cho ngữ cảnh `S1` và trả `201 Created` |
| TC-46 | FR-09a, FR-09b | User hoặc Admin gọi `supabase.auth.signOut({ scope: 'local' })` | Xóa phiên cục bộ trên thiết bị hiện tại, giao diện chuyển về Guest và không gọi được API yêu cầu Bearer token |
| TC-47 | FR-12, FR-11 | User A tạo `scan_session` `S1`, gửi 1 feedback gắn với `S1` và 1 feedback cho cùng món với `scan_id=null`; sau đó gọi `DELETE /scan-sessions/{S1}` | Trả `204 No Content` (không lỗi xung đột unique); feedback gắn với `S1` bị xóa theo `ON DELETE CASCADE`, còn feedback `scan_id=null` vẫn giữ nguyên |

---

## C. Security, Privacy & Contract (`SEC-01`..`07`, `API-01`..`04`)

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| SEC-01 | Token User B truy cập `favorites` (hoặc `user_preferences`) của User A | Không thấy và không sửa được dữ liệu của A; DB RLS chặn truy cập ngoài quyền |
| SEC-02 | Guest detect `save_history=true` / `false` | `true` → `401 UNAUTHORIZED`, `false` → `200 OK`; không có ảnh lưu trong Storage |
| SEC-03 | User thường `POST /admin/recipes` hoặc giả `role=admin` trong payload | `403 FORBIDDEN`, không tạo data/audit thành công |
| SEC-04 | Thử Data API trực tiếp `anon` / User A / User B | `GRANT` + `RLS` bảo vệ `profiles`/`favorites`/`scan_sessions`/`user_preferences`; public chỉ đọc được `published` |
| SEC-05 | File ảnh giả/ảnh gây giải mã nặng, spam request | Validation, rate limit (`429 RATE_LIMITED` kèm `Retry-After`), timeout (`504`); không crash/leak file |
| SEC-06 | User B gửi `scan_id` thuộc A qua `/scan-sessions/{id}`, `/recommendations` hoặc `/feedback` | Trả `404 SCAN_NOT_OWNED` (chống dò quét UUID); không đọc/sửa được dữ liệu của A |
| SEC-07 | User thường tự `PATCH profiles.role` bằng Data API | Bị từ chối bởi `REVOKE`/`RLS`, `role` không đổi |
| API-01 | Gửi input lỗi tại 3 endpoints đại diện | JSON có đủ `code`, `message`, `details`, `request_id` (`X-Request-Id`) |
| API-02 | Validate `openapi.yaml`; so với FastAPI `/openapi.json` | Schema OpenAPI 3.1 hợp lệ; routes/request/response chính khớp 100% |
| API-03 | Gửi request JSON body cho multipart detect | Từ chối `415`/`422` rõ ràng, không coi JSON là ảnh |
| API-04 | Gửi `ingredient_ids` rỗng hoặc UUID không tồn tại | Trả `422 VALIDATION_ERROR` / `422 INVALID_INGREDIENTS`, không gợi ý món giả |

---

## D. AI, Thực nghiệm Hệ gợi ý, UI, Performance, Legal & Operations

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| AI-01 | Đánh giá YOLO trên test split độc lập (`NFR-11`) | Xuất `Precision`, `Recall`, `F1`, `mAP50`, `mAP50:95`, bảng per-class `AP50`, `Recall`, `N_test` của toàn bộ lớp mục tiêu; **không loại lớp yếu sau khi chạy test** |
| AI-02 | Ảnh nhiều object, chồng lấp, nền đa dạng | Lưu TP/FP/FN, confusion matrix và ảnh minh họa các trường hợp khó, không cherry-pick |
| AI-03 | Đổi `model_version` / `class_index` và kiểm thử ngưỡng cảnh báo HITL ($\tau = 0.80$) | Ánh xạ đúng `ingredients.id` theo từng version; phát hiện có `confidence < 0.80` bật cảnh báo xác nhận HITL |
| AI-04 | Thực nghiệm đối chứng 4 biến thể Ranker **A – B – C – D** trên $\ge 100$ tình huống độc lập (`NFR-11`) | Xuất bảng `Precision@5`, `nDCG@5`, `Constraint Violation Rate` (`0%` cho C & D) và `ILD@5`; chia tập tương tác theo thời gian cho biến thể D |
| UI-01 | Chrome/Edge/Firefox ở `360px` / `768px` / `1366px` | Màn upload, HITL correction, thanh gia vị sẵn có, danh sách gợi ý (kèm giải thích XAI) và chi tiết món không vỡ bố cục |
| UI-02 | Mạng chậm / API timeout (`504`) | Có trạng thái loading/error/retry và lối tắt chuyển sang nhập tay; không treo vĩnh viễn |
| UI-03 | Kiểm tra ngôn ngữ hiển thị toàn bộ màn hình và thông báo lỗi (`NFR-12`) | 100% nhãn giao diện, hướng dẫn, thông báo lỗi hiển thị tiếng Việt có dấu chuẩn UTF-8; tìm kiếm hỗ trợ có dấu, không dấu và từ đồng nghĩa |
| UI-04 | Mở hộp thoại xác nhận xóa phiên quét `DELETE /scan-sessions/{scan_id}` | Hiển thị cảnh báo rõ việc xóa lịch sử quét sẽ xóa luôn các đánh giá (`feedback`) đã gửi trong phiên quét đó |
| PERF-01 | `>= 30` requests detect, ghi máy/model/ảnh/concurrency (`NFR-02`) | Báo cáo `p50`/`p95`; đối chiếu mục tiêu `p95 <= 10s` trên CPU demo (`<= 3s` nếu có GPU), không tự ghi Pass khi chưa đo |
| PERF-02 | Tập `>= 500` món, benchmark `/recommendations` và `/recipes` (`NFR-03`) | Báo cáo `p50`/`p95`; đối chiếu mục tiêu `p95 <= 1.0s` cho `/recommendations` và `p95 <= 500ms` cho `/recipes` |
| LEGAL-01 | Rà soát ảnh dataset + công thức + nguồn USDA + model license + bảo vệ DLCN (`NFR-13`) | Có căn cứ nguồn/giấy phép (`source_url`, `content_license`), kiểm chứng `ADR-005`, tuân thủ nguyên tắc tối thiểu hóa dữ liệu của Luật BV DLCN số 91/2025/QH15 |
| OPS-01 | Kiểm tra `GET /api/v1/health` và structured logging (`NFR-08`) | `/health` trả `200 OK` (`status: "ok"` / `"degraded"`); log JSON ghi nhận `request_id`, `latency_ms`, `model_version` mà không lộ JWT/secret |
| OPS-02 | Chạy quy trình migration + seed dữ liệu chuẩn trên DB trống (`NFR-09`) | Kích hoạt `unaccent` & `pg_trgm`, tạo sạch toàn bộ bảng, enum/check constraint (`category='pantry'`), index `UNIQUE NULLS NOT DISTINCT` và `idx_alias_trgm`, nạp đủ dữ liệu mẫu không lỗi |
| OPS-03 | Kiểm tra cấu hình bảo vệ tài nguyên suy luận AI (`NFR-14`) | Worker giới hạn đồng thời (`MAX_CONCURRENT_INFERENCES`), tự hủy khi quá `INFERENCE_TIMEOUT_SECONDS` (`504`) và áp dụng rate limit (`429`) đúng cấu hình |

---

## E. Unit Tests Công thức Toán học (`pytest`)

### E.1. Hợp đồng cốt lõi MVP (`Scoring v1.0`)

| Trường hợp kiểm thử | `C / E / T / P` | Kết quả kỳ vọng |
|---|---|---|
| 2 required chính đều có, 1 optional chính thiếu, đủ gia vị nền (`X=[]`), món 13 phút, không preference | `C=0.8, E=1.0, T=1.0, P=1.0` | `S = 89.0`, `availability = "ready"` |
| 2 required chính đều có, 1 optional chính thiếu, **bỏ chọn 1 gia vị bắt buộc** (`X=[nuoc_mam]`), món 13 phút, không preference | `C=2/3.5 (≈0.571), E=2/3 (≈0.667), T=1.0, P=1.0` | `S = 68.1`, `availability = "missing"` |
| Cả 3 nguyên liệu chính đều có, đủ gia vị nền (`X=[]`), món 13 phút, không preference | `C=1.0, E=1.0, T=1.0, P=1.0` | `S = 100.0`, `availability = "ready"` |
| Chỉ có 1/2 required chính, optional chính thiếu, đủ gia vị nền (`X=[]`), món 13 phút | `C=0.4, E=0.5, T=1.0, P=1.0` | `S = 54.5`, `availability = "missing"` |
| Không có required/optional chính nào trùng với `U` (dù đủ toàn bộ gia vị nền) | `C=0` | Bị loại khỏi tập ứng viên |
| Món 35 phút với `max_total_minutes=15` | Không chấm | Bị lọc cứng trước khi chấm điểm |
| Món thuộc `US` nhưng `preferred_cuisine_codes=["VN"]`, không lọc cứng | `P=0.0` | Điểm giảm `10.0` so với khi `P=1.0` |

### E.2. Cấu hình thông minh mở rộng (`Scoring v1.1` & 14 Thành phần — `MATH-01`..`MATH-07`)

| Mã Unit Test | Thành phần kiểm chứng | Đầu vào kiểm thử chuẩn | Kết quả kỳ vọng chính xác |
|---|---|---|---|
| **MATH-01** | **IoU NMS (TP 01) & CLIP Cosine (TP 02)** | Hai box $[10,10,20,20]$ và $[12,12,22,22]$; hai vector $v=(0.8,0.6)$, $t_1=(0.9,0.436)$ | $\text{IoU} = 64/136 \approx 0.471$ (hoặc ví dụ chuẩn $40/70 \approx 0.571$); $\text{sim}(v, t_1) \approx 0.982$ / $0.975$ đúng công thức tích vô hướng chuẩn hóa |
| **MATH-02** | **Suy luận 3 trạng thái & Lọc dị ứng (TP 04)** | (1) `required={ca_chua, trung, dau, muoi}`, `available={ca_chua:True, trung:None, dau:True, muoi:True}`; (2) Món chứa `trung` (`allergen=egg`) với `excluded_allergens={egg}` | (1) Trạng thái = `UNKNOWN` (không gắn `READY`, không gắn `MISSING_CONFIRMED`); (2) Trạng thái = `BLOCKED` ngay trước bước chấm điểm |
| **MATH-03** | **Weighted Coverage (TP 05)** | Trọng số `{ca_chua:4, trung:3, dau:1, muoi:1}`, xác nhận có `{ca_chua, dau, muoi}` | $C = (4 + 1 + 1) / (4 + 3 + 1 + 1) = 6/9 \approx 0.667$ |
| **MATH-04** | **Tversky Baseline B (TP 05, 06)** | $A=\{ca\_chua, dau, muoi\}$, $R=\{ca\_chua, trung, dau, muoi\}$, $\alpha=0.3, \beta=2.0$ | $T_{0.3, 2.0} = 3 / (3 + 0.3\times 0 + 2.0\times 1) = 3/5 = 0.60$ |
| **MATH-05** | **MCDA, Giải thích XAI & LR (TP 07, 08, 14)** | $C=6/9, G=1, T=1, P=0.5, Q=1$, trọng số `(0.50, 0.25, 0.15, 0.05, 0.05)`; LR với $x=[1,1,0], \theta=[0.2,0.3,-0.1], y=1, \eta=0.1$ | Đóng góp XAI `[33.33, 25.00, 15.00, 2.50, 5.00]`, tổng $S_{\text{base}} = 80.83$; LR $p = \sigma(0.5) \approx 0.622$, khi $\lambda_{\text{pers}}=0$ thì $S_{\text{final}} = S_{\text{base}}$ |
| **MATH-06** | **MMR Reranking (TP 09)** | $\lambda_{\text{mmr}}=0.7$; Canh biến thể $(\text{Rel}=0.91, \text{Sim}=0.75)$ so với Mì Ý $(\text{Rel}=0.88, \text{Sim}=0.20)$ | $\text{MMR}_{\text{canh}} = 0.7(0.91) - 0.3(0.75) = 0.412 < \text{MMR}_{\text{miY}} = 0.7(0.88) - 0.3(0.20) = 0.556 \implies$ chọn Mì Ý trước |
| **MATH-07** | **Khẩu phần, USDA & Tiếng Việt (TP 10, 11, 13)** | $100\text{ g}$ cà chua ($18\text{ kcal}/100\text{ g}$) + $60\text{ g}$ trứng ($144\text{ kcal}/100\text{ g}$), nhân đôi khẩu phần; `Norm("Đậu phụ")` | Gốc $= 18 + 86.4 = 104.4\text{ kcal}$ (hoặc $104.5\text{ kcal}$ theo bảng FDC cụ thể), nhân đôi $= 208.8\text{ kcal}$; `Norm("Đậu phụ") == "dau phu"` khớp mã `tofu` |

---

## F. Quy tắc đánh dấu `Pass` & Kiểm thử chéo

Chỉ đánh dấu `Pass` sau khi có **bản build xác định (`commit SHA`)**, dữ liệu kiểm thử độc lập, kết quả thực tế khớp kỳ vọng, đường dẫn bằng chứng và chữ ký của **thành viên kiểm thử chéo (Cross-Tester)**. Với các phép đo thực nghiệm (`AI-01`, `AI-04`, `PERF-01`, `PERF-02`), báo cáo trung thực con số đo được (nếu chưa đạt ngưỡng mục tiêu thì ghi rõ nguyên nhân và kế hoạch cải thiện, tuyệt đối không chỉnh sửa kỳ vọng hoặc loại bỏ lớp khó để giả đạt).
