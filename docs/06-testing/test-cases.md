# Test Cases — danh sách kiểm thử kế hoạch

**Trạng thái mặc định tất cả case:** `Not run`. **Tiền điều kiện chung:** API/Frontend chạy trên môi trường test, seed dữ liệu đúng như mô tả, kiểm thử viên ghi build SHA. **Mã:** TC (functional), SEC (security), PERF (performance), API (contract), AI (model), UI (giao diện), LEGAL (pháp lý/bản quyền), OPS (vận hành/độ tin cậy).

## A. Functional (FR)

| ID | FR | Dữ liệu/thao tác | Kết quả mong đợi |
|---|---|---|---|
| TC-01 | FR-01 | GET `/recipes?q=trung` | Chỉ món published có từ khóa phù hợp, phân trang đúng (`limit`, `offset`, `total`) |
| TC-02 | FR-01 | GET `/recipes?cuisine_code=VN&max_total_minutes=15` | Chỉ món VN có `prep_minutes + cook_minutes <= 15` |
| TC-03 | FR-02 | GET `/recipes/{id}` món published/draft | Published trả detail/steps và danh sách nguyên liệu có `category`; draft trả `404 RECIPE_NOT_FOUND` với Guest |
| TC-04 | FR-03 | Upload ảnh JPEG 1 MB hợp lệ | `200 OK` và JSON đúng schema (có thể `detections=[]`) |
| TC-05 | FR-03 | Upload file `> 5 MiB` | `413 IMAGE_TOO_LARGE`, không chạy suy luận |
| TC-06 | FR-03 | (1) Upload file sai MIME (`.pdf`, `.tiff`); (2) Upload file giả `.jpg` chứa nội dung text hỏng | (1) `415 UNSUPPORTED_IMAGE_TYPE`; (2) `422 INVALID_IMAGE`; không crash, không lưu file |
| TC-07 | FR-04 | Ảnh 2+ lớp từ test fixture | JSON có nhiều bbox chuẩn hóa `[0, 1]`, `suggested_ingredients` gộp trùng theo `ingredient_id` với `max_confidence` |
| TC-08 | FR-05 | AI trả 2 cà chua và 1 trứng; user gộp/sửa | Request recommendation chỉ gồm ID nguyên liệu chính đã xác nhận, không trùng |
| TC-09 | FR-05 | User xóa tất cả ingredient IDs | UI ngăn gửi recommend; có hướng dẫn thêm tay |
| TC-10 | FR-06 | Recipe cần trứng+cà chua đều có, gia vị nền mặc định đủ (`excluded_pantry_ids=[]`) | `availability=ready`, `missing_required_ingredient_ids=[]` |
| TC-11 | FR-06 | Recipe cần gà+cà chua, user chỉ có cà chua | `availability=missing`, gà nằm trong `missing_required_ingredient_ids` |
| TC-12 | FR-06 | Cùng dữ liệu, so score tính tay và API | Điểm khớp công thức `S = round(100*(0.55*C + 0.25*E + 0.10*T + 0.10*P), 1)`, xếp nhóm `ready` trước `missing` |
| TC-13 | FR-07 | `cuisine_codes=["VN"]` | Chỉ trả món thuộc `VN`, không có món `EU`/`US` |
| TC-14 | FR-07 | `max_total_minutes=15`, món `5+10` và `15+20` | Chỉ có món 15 phút; món 35 phút bị loại trước khi chấm điểm |
| TC-15 | FR-08 | Xem recipe có tag/không tag | Tag có `source_url` + tuyên bố miễn trừ định lượng/dị ứng; không có kcal/gram suy ra từ ảnh |
| TC-16 | FR-09a, FR-09b | Đăng ký (User) và đăng nhập (User/Admin) với Supabase Auth | Có session JWT hợp lệ; tài khoản Admin kế thừa quyền User (`Admin --|> User`) gọi được các API của User |
| TC-17 | FR-10 | User A lưu món yêu thích 2 lần (`POST /favorites`) | Lần 1 trả `201`, lần 2 trả `200` idempotent; `GET /favorites` chỉ có 1 bản ghi |
| TC-18 | FR-10 | User A bỏ favorite (`DELETE /favorites/{recipe_id}`) | Trả `204 No Content`; danh sách yêu thích không còn món |
| TC-19 | FR-11 | User gửi `rating=3` và `rating=6` | `rating=3` → `201 Created`, `rating=6` → `422 VALIDATION_ERROR` |
| TC-20 | FR-12 | User detect `save_history=false` và `save_history=true` | `false`: `scan_id=null`, không lưu DB; `true`: tạo `scan_id`, lưu metadata và `scan_ingredients` khi gọi recommend kèm `scan_id` |
| TC-21 | FR-13 | Admin tạo recipe draft đủ dữ liệu | `201 Created`; recipe ở trạng thái `draft`, chưa hiện trên public API trước khi publish |
| TC-22 | FR-13 | Publish recipe thiếu `steps` (`steps=[]`) | `400 RECIPE_NOT_PUBLISHABLE` (`reason="missing_steps"`); không công bố |
| TC-23 | FR-14 | Admin tạo ingredient `slug` trùng; thêm alias hợp lệ | Trùng `slug` trả `409 DUPLICATE_SLUG`; thêm alias hợp lệ thành công, tìm kiếm theo alias trả đúng nguyên liệu chuẩn |
| TC-24 | FR-15 | Admin tạo model `draft`, gán đủ `ai_labels`, kích hoạt sang `active` | `200 OK`; model `active` cũ tự chuyển sang `archived` trong cùng giao dịch; nếu thiếu nhãn trả `400 MODEL_NOT_ACTIVATABLE` (`unmapped_class_indices`) |
| TC-25 | FR-16 | Admin gắn nutrition tag thiếu `source_url` hoặc URL sai định dạng | Trả `422 VALIDATION_ERROR`; khi có `source_url` hợp lệ trả `200 OK` và hiển thị đúng |
| TC-26 | FR-17 | Admin tạo/cập nhật recipe, ingredient, model và xem `GET /admin/audit-logs` | Có bản ghi `actor_id`, `action`, `entity_type`, `entity_id`, `created_at`; không lộ secret/token |
| TC-27 | FR-18 | AI trả `detections=[]` hoặc Guest/User mở thẳng luồng nhập tay | Tìm kiếm/chọn nguyên liệu thủ công và gọi `/recommendations` hoạt động bình thường với `scan_id=null` |
| TC-28 | FR-12 | User A `GET`/`DELETE /scan-sessions/{scan_id}`; User B truy cập `scan_id` của A | A xem và xóa được (`204`); B nhận `404 SCAN_NOT_OWNED` |
| TC-29 | FR-04 | Gọi `POST /ai/detect` khi hệ thống chưa có model nào ở trạng thái `active` | Trả `503 MODEL_NOT_READY`, không crash worker |
| TC-30 | FR-04 | Gọi `POST /ai/detect` khi tác vụ suy luận vượt ngưỡng timeout cấu hình | Backend hủy tác vụ, giải phóng bộ nhớ tạm và trả `504 INFERENCE_TIMEOUT` |
| TC-31 | FR-05 | Màn hình xác nhận nguyên liệu hiển thị thanh gia vị sẵn có (`category='pantry'`) | Mặc định bật sẵn 5 gia vị nền; khi người dùng tắt "Nước mắm", payload gửi `excluded_pantry_ids: ["55555555-5555-4555-8555-555555555555"]` |
| TC-32 | FR-06 | Công thức "Trứng xào cà chua" có gia vị bắt buộc "Nước mắm"; gửi `excluded_pantry_ids=[nuoc_mam_id]` | `E=2/3`, `C=2/3.5`, `S=68.1`, `availability="missing"`, `missing_required_ingredient_ids` chứa `nuoc_mam_id` |
| TC-33 | FR-06 | Gửi `POST /recommendations` với `include_missing=false` | Chỉ trả về các món có `availability="ready"`, loại bỏ toàn bộ món `"missing"` |
| TC-34 | FR-06 | Gửi `POST /recommendations` khi không có công thức nào khớp nguyên liệu chính (`C=0`) hoặc bộ lọc | Trả `200 OK` với `items=[]`, `total=0`; không bịa công thức |
| TC-35 | FR-07 | Gửi `preferred_cuisine_codes=["VN"]` (không đặt `cuisine_codes`) | Món `VN` nhận `P=1.0`; món `EU`/`US` vẫn được giữ lại nhưng nhận `P=0.0` (giảm `10.0` điểm tổng) |
| TC-36 | FR-05 | Kiểm tra `GET /ingredients`: (1) gọi không token; (2) lọc `category=pantry` và `exclude_pantry=true`; (3) gửi đồng thời `category=pantry&exclude_pantry=true` | (1) `200 OK` chỉ trả nguyên liệu `is_active=true`; (2) lọc đúng nhóm `pantry` hoặc loại trừ `pantry`; (3) trả `422 INVALID_QUERY_PARAMS` |
| TC-37 | FR-05 | Kiểm tra `POST /recommendations`: (1) gửi UUID `pantry` trong `ingredient_ids`; (2) gửi UUID nguyên liệu chính (`category != 'pantry'`) trong `excluded_pantry_ids`; (3) gửi UUID không tồn tại hoặc `inactive` | Cả 3 bước đều bị chặn với `422 INVALID_INGREDIENTS` kèm chi tiết `details` tương ứng |
| TC-38 | FR-13 | Kiểm tra điều kiện công bố và sửa món `published`: (1) publish món chỉ có nguyên liệu `pantry`; (2) publish món chứa nguyên liệu `is_active=false`; (3) publish món có 1 bước với `estimated_minutes > prep_minutes + cook_minutes`; (4) gọi `PATCH /admin/recipes/{id}` trên món **đang `published`** làm vi phạm một trong các điều kiện trên | Cả 4 bước đều bị chặn với `400 RECIPE_NOT_PUBLISHABLE` và giữ nguyên trạng thái/dữ liệu hợp lệ trước đó |
| TC-39 | FR-14 | Kiểm tra `PATCH /admin/ingredients/{id}`: (1) đổi `category` sang `pantry` hoặc đặt `is_active=false` cho nguyên liệu đang thuộc công thức `published`; (2) đổi `category` sang `pantry` hoặc đặt `is_active=false` cho nguyên liệu đang được ánh xạ trong `ai_labels` của model `draft` hoặc `active` | Cả 2 bước đều bị chặn với `400 INGREDIENT_IN_USE` (`published_recipe_count` / `active_or_draft_model_count`) |
| TC-40 | FR-09a, FR-09b | Yêu cầu khôi phục mật khẩu qua email (`resetPasswordForEmail`) và đặt mật khẩu mới | Nhận liên kết khôi phục hợp lệ, cập nhật mật khẩu thành công và đăng nhập được bằng mật khẩu mới |
| TC-41 | FR-15 | Kiểm tra Rollback model `PATCH /admin/ai-models/{id}/status` (`archived -> active`): (1) Ca thành công: kích hoạt lại model `archived` có toàn bộ nhãn hợp lệ; (2) Ca thất bại: lấy một nguyên liệu chỉ thuộc model `archived` (không thuộc model `draft`/`active` hay món `published`), gọi `PATCH /admin/ingredients/{id}` đổi `category` sang `'pantry'` (`200 OK` vì `INGREDIENT_IN_USE` bỏ qua model `archived`), sau đó gọi rollback model `archived` đó sang `active` | (1) Trả `200 OK`, model `active` cũ chuyển sang `archived`; (2) Bị chặn với `400 MODEL_NOT_ACTIVATABLE` (`invalid_mapped_class_indices`) |
| TC-42 | FR-15 | Gọi `POST /admin/ai-labels` hoặc `PATCH /admin/ai-labels/{id}` trên model đang ở trạng thái `active` hoặc `archived` | Bị chặn với `400 MODEL_IMMUTABLE` |
| TC-43 | FR-03 | Upload ảnh chụp dọc từ điện thoại có cờ `EXIF Orientation != 1` và chứa metadata GPS/EXIF | Backend tự xoay ảnh về đúng chiều hiển thị chuẩn trước khi suy luận, xóa sạch metadata EXIF/GPS trong bộ nhớ, tọa độ `bbox` trả về khớp với ảnh đã xoay |
| TC-44 | FR-15 | Gọi `POST` hoặc `PATCH /admin/ai-labels` trên model `draft` nhưng trỏ `ingredient_id` tới nguyên liệu có `category='pantry'` hoặc `is_active=false` | Bị chặn với `400 INVALID_LABEL_MAPPING` |
| TC-45 | FR-11 | Kiểm tra `POST /feedback` theo ngữ cảnh: (1) gửi lần 1 với `scan_id=null` rồi gửi lần 2 cùng `scan_id=null` với `rating` mới; (2) gửi tiếp cho cùng `recipe_id` nhưng kèm `scan_id=S1` hợp lệ của User | (1) Lần 1 trả `201 Created`, lần 2 trả `200 OK` (upsert cập nhật `updated_at`); (2) Tạo bản ghi mới cho ngữ cảnh `S1` và trả `201 Created` |
| TC-46 | FR-09a, FR-09b | User hoặc Admin gọi `supabase.auth.signOut({ scope: 'local' })` | Xóa phiên cục bộ trên thiết bị hiện tại, giao diện chuyển về Guest và không gọi được API yêu cầu Bearer token |
| TC-47 | FR-12, FR-11 | User A tạo `scan_session` `S1`, gửi 1 feedback gắn với `S1` và 1 feedback cho cùng món với `scan_id=null`; sau đó gọi `DELETE /scan-sessions/{S1}` | Trả `204 No Content` (không lỗi xung đột unique); feedback gắn với `S1` bị xóa theo `ON DELETE CASCADE`, còn feedback `scan_id=null` vẫn giữ nguyên |

## B. Security, Privacy, Contract

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| SEC-01 | Token User B truy cập favorite User A | Không thấy và không sửa favorite A; DB RLS chặn truy cập ngoài quyền |
| SEC-02 | Guest detect `save_history=true` / `false` | `true` → `401 UNAUTHORIZED`, `false` → `200 OK`; không có ảnh lưu trong Storage |
| SEC-03 | User thường `POST /admin/recipes` hoặc giả `role=admin` | `403 FORBIDDEN`, không tạo data/audit thành công |
| SEC-04 | Thử Data API trực tiếp anon/user A/user B | GRANT + RLS bảo vệ `profiles`/`favorites`/`scan_sessions`; public chỉ đọc được `published` |
| SEC-05 | File ảnh giả/ảnh gây giải mã nặng, spam request | Validation, rate limit (`429 RATE_LIMITED` kèm `Retry-After`), timeout (`504`); không crash/leak file |
| SEC-06 | User B gửi `scan_id` thuộc A qua `/scan-sessions/{id}`, `/recommendations` hoặc `/feedback` | Trả `404 SCAN_NOT_OWNED` (chống dò quét UUID); không đọc/sửa được dữ liệu của A |
| SEC-07 | User thường tự PATCH `profiles.role` bằng Data API | Bị từ chối bởi REVOKE/RLS, `role` không đổi |
| API-01 | Gửi input lỗi tại 3 endpoints đại diện | JSON có đủ `code`, `message`, `details`, `request_id` (`X-Request-Id`) |
| API-02 | Validate `openapi.yaml`; so với FastAPI `/openapi.json` | Schema OpenAPI 3.1 hợp lệ; routes/request/response chính khớp 100% |
| API-03 | Gửi request JSON body cho multipart detect | Từ chối `415`/`422` rõ ràng, không coi JSON là ảnh |
| API-04 | Gửi `ingredient_ids` rỗng hoặc UUID không tồn tại | Trả `422 VALIDATION_ERROR` / `422 INVALID_INGREDIENTS`, không gợi ý món giả |

## C. AI, UI, Performance, Legal và Operations

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| AI-01 | Đánh giá test split độc lập (`NFR-11`) | Xuất `Precision`, `Recall`, `mAP50`, `mAP50-95`, bảng per-class `AP50`, `Recall`, `N_test` của toàn bộ lớp mục tiêu; không loại lớp yếu sau khi chạy test |
| AI-02 | Ảnh nhiều object, nền đa dạng | Lưu TP/FP/FN, ảnh minh họa các trường hợp khó, không cherry-pick |
| AI-03 | Đổi model version và class index | Vẫn ánh xạ đúng `ingredients.id` theo từng version |
| UI-01 | Chrome/Edge/Firefox ở `360px` / `768px` / `1366px` | Màn upload, correction, thanh gia vị sẵn có, list, detail không vỡ bố cục hoặc mất nút chính |
| UI-02 | Mạng chậm / API timeout (`504`) | Có trạng thái loading/error/retry và lối tắt chuyển sang nhập tay; không treo vĩnh viễn |
| UI-03 | Kiểm tra ngôn ngữ hiển thị toàn bộ màn hình và thông báo lỗi (`NFR-12`) | 100% nhãn giao diện, hướng dẫn, thông báo lỗi hiển thị tiếng Việt có dấu chuẩn UTF-8; tìm kiếm hỗ trợ cả có dấu và không dấu |
| UI-04 | Mở hộp thoại xác nhận xóa phiên quét `DELETE /scan-sessions/{scan_id}` | Hiển thị cảnh báo rõ việc xóa lịch sử quét sẽ xóa luôn các đánh giá (`feedback`) đã gửi trong phiên quét đó |
| PERF-01 | `>= 30` requests detect, ghi máy/model/ảnh/concurrency (`NFR-02`) | Báo cáo `p50`/`p95`; đối chiếu mục tiêu `p95 <= 10s` trên CPU demo (`<= 3s` nếu có GPU), không tự ghi Pass khi chưa đo |
| PERF-02 | Tập `>= 500` món, benchmark `/recommendations` và `/recipes` (`NFR-03`) | Báo cáo `p50`/`p95`; đối chiếu mục tiêu `p95 <= 1.0s` cho `/recommendations` và `p95 <= 500ms` cho `/recipes` |
| LEGAL-01 | Rà soát 5 ảnh + 5 công thức + model license + tuân thủ dữ liệu cá nhân (`NFR-13`) | Có căn cứ nguồn/giấy phép (`source_url`, `content_license`), kiểm chứng `ADR-005`, tuân thủ nguyên tắc tối thiểu hóa dữ liệu của Luật BV DLCN số 91/2025/QH15 |
| OPS-01 | Kiểm tra `GET /api/v1/health` và structured logging (`NFR-08`) | `/health` trả `200 OK` (`status: "ok"` / `"degraded"`); log JSON ghi nhận `request_id`, `latency_ms`, `model_version` mà không lộ JWT/secret |
| OPS-02 | Chạy quy trình migration + seed dữ liệu chuẩn trên DB trống (`NFR-09`) | Tạo sạch toàn bộ bảng, enum/check constraint (`category='pantry'`), index `UNIQUE NULLS NOT DISTINCT`, nạp đủ danh mục nguyên liệu (gồm 5 gia vị nền) và công thức mẫu không lỗi |
| OPS-03 | Kiểm tra cấu hình bảo vệ tài nguyên suy luận AI (`NFR-14`) | Worker giới hạn đồng thời (`MAX_CONCURRENT_INFERENCES`), tự hủy khi quá `INFERENCE_TIMEOUT_SECONDS` (`504`) và áp dụng rate limit (`429`) đúng cấu hình |

## D. Kiểm tra tính đúng của thuật toán (unit tests cần code)

| Trường hợp | C / E / T / P | Điểm kỳ vọng |
|---|---|---|
| 2 required chính đều có, 1 optional chính thiếu, đủ gia vị nền (`X=[]`), món 13 phút, không preference | `C=0.8, E=1.0, T=1.0, P=1.0` | `S=89.0, ready` |
| 2 required chính đều có, 1 optional chính thiếu, **bỏ chọn 1 gia vị bắt buộc** (`X=[nuoc_mam]`), món 13 phút, không preference | `C=2/3.5 (≈0.571), E=2/3 (≈0.667), T=1.0, P=1.0` | `S=68.1, missing` |
| Cả 3 nguyên liệu chính đều có, đủ gia vị nền (`X=[]`), món 13 phút, không preference | `C=1.0, E=1.0, T=1.0, P=1.0` | `S=100.0, ready` |
| Chỉ có 1/2 required chính, optional chính thiếu, đủ gia vị nền (`X=[]`), món 13 phút | `C=0.4, E=0.5, T=1.0, P=1.0` | `S=54.5, missing` |
| Không có required/optional chính nào trùng với `U` (dù đủ toàn bộ gia vị nền) | `C=0` | Bị loại khỏi tập ứng viên |
| Món 35 phút với `max_total_minutes=15` | Không chấm | Bị lọc cứng trước khi chấm điểm |
| Món thuộc `US` nhưng `preferred_cuisine_codes=["VN"]`, không lọc cứng | `P=0.0` | Điểm giảm `10.0` so với khi `P=1.0` |

Lưu ý:
- Ca thứ hai (`X=[nuoc_mam]`): `|R_main|=2`, `|O_main|=1`, `|M_pantry|=1` → `E = 2/(2+1) = 2/3`, `C = 2/(2+0.5+1) = 2/3.5` → `S = round(100 * (0.55*(2/3.5) + 0.25*(2/3) + 0.1 + 0.1), 1) = 68.1`.
- Ca thứ tư: `C = 1/(2+0.5) = 0.4`; `S = 100 * (0.22 + 0.125 + 0.1 + 0.1) = 54.5`.

## E. Khi nào đánh dấu Pass

Chỉ đánh `Pass` sau khi có **build xác định**, dữ liệu test độc lập, actual response khớp expected và link evidence. Với AI, có thể ghi "mục tiêu mAP chưa đạt" nhưng kiểm thử đo lường vẫn là **đã chạy**, không tự sửa expected để giả đạt.
