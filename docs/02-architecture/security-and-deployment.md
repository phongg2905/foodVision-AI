# Bảo mật, quyền riêng tư và triển khai

**Phiên bản:** `1.0.0` · **Trạng thái:** Chính thức (`Approved Baseline`); bắt buộc kiểm chứng khi tích hợp môi trường Supabase/Backend thật.

## 1. Threat model ngắn

| Nguy cơ | Rủi ro | Biện pháp |
|---|---|---|
| Client giả vai trò admin | Sửa công thức và danh mục | Verify Supabase JWT + tra quyền admin từ nguồn tin cậy phía server; không tin `role` gửi từ body |
| Đọc dữ liệu user khác | Lộ favorites/history/preferences | RLS ownership + kiểm tra `user_id` khi dùng `service_role` |
| File giả ảnh / ảnh quá lớn | Exhaust memory, thư viện ảnh lỗi | Multipart 5 MB, kiểm tra magic bytes (`415` nếu sai định dạng như HEIC/TIFF, `422` nếu ảnh hỏng), giải mã với giới hạn kích thước pixel, timeout `504` |
| Injection qua search | Lỗi truy vấn | Query parameterized/ORM (kể cả truy vấn `pg_trgm`); validate sort/filter; không ghép SQL từ input |
| Lộ Supabase service key | Toàn quyền DB | Secret chỉ ở backend env, không commit, không expose qua Vite `VITE_*` |
| Trích xuất dinh dưỡng sai / bỏ sót dị ứng | Gây hiểu nhầm sức khỏe hoặc rủi ro an toàn thực phẩm | Ở Tầng 1 (`P0`) chỉ hiển thị nhãn định tính có nguồn; ở Tầng 2 (`P1`) chỉ tính USDA khi có `grams` kiểm duyệt/người dùng nhập (tuyệt đối không đoán gram từ ảnh 2D); lọc dị ứng dựa trên thành phần chuẩn đã kiểm duyệt (`ingredient_allergens`), không tự ánh xạ ngầm từ truy vấn tìm kiếm mơ hồ |
| Abuse endpoint detect | Tốn CPU/GPU | Rate limiting theo IP/user, quota, concurrency limit |
| Lưu ảnh trái ý / lộ metadata EXIF | Lộ hình ảnh cá nhân hoặc tọa độ GPS | Không lưu ảnh gốc bền vững; xoay chuẩn chiều theo EXIF rồi xóa sạch toàn bộ metadata EXIF/GPS khi giải mã RGB; dọn file spool tạm; history kết quả **opt-in** |

## 2. Quyền và JWT

- Guest có thể đọc món `published`, danh mục nguyên liệu (`is_active = true`) và gửi `detect`/`recommend`, nhưng không ghi bảng nội bộ.
- Supabase Auth cấp token; FastAPI phải xác thực chữ ký, issuer, audience, expiration, subject; ưu tiên phương thức phù hợp kiểu signing key, JWKS nếu asymmetric.
- Khi người dùng bấm Đăng xuất trên giao diện, Frontend gọi `supabase.auth.signOut({ scope: 'local' })` để xóa session trên trình duyệt hiện tại và thu hồi `refresh_token` của phiên đó mà không làm văng phiên đăng nhập trên các thiết bị khác. Lưu ý: `access_token` JWT ngắn hạn là stateless nên vẫn còn hiệu lực chữ ký cho đến thời điểm `exp` nếu backend không duy trì danh sách thu hồi (blacklist) ở MVP.
- Quyền `Admin` phải được server xác minh; vai trò trong `profiles.role` do luồng cấp quyền có kiểm soát. Không cho người dùng tự `PATCH` role. Tài khoản `Admin` kế thừa quyền của `User` (`Admin --|> User`) cộng thêm quyền quản trị `/admin/*`; khuyến nghị vận hành dùng tài khoản quản trị riêng biệt với tài khoản cá nhân (xem [ADR-011](../07-decisions/ADR-011-admin-role-inheritance.md)).
- Dù JWT hợp lệ, phải kiểm tra quan hệ sở hữu trước khi ghi `scan_ingredients` vào `scan_session`, hoặc nhận feedback chứa `scan_id` (nếu không tồn tại hoặc không thuộc chủ sở hữu, trả `HTTP 404 SCAN_NOT_OWNED` để chống dò quét ID).
- Nếu FastAPI dùng `service_role` (bỏ qua RLS), **FastAPI phải tự enforce đầy đủ authorization**, không dựa vào RLS. Đối với Data API trực tiếp, RLS + GRANT là lớp phòng thủ chiều sâu (defense-in-depth).

## 3. Ma trận RLS/grants (định hướng)

| Bảng | anon | authenticated | Admin qua backend |
|---|---|---|---|
| `ingredients`, `ingredient_aliases`, `allergens`, `ingredient_allergens` | SELECT có kiểm soát | SELECT | CRUD |
| `recipes`, `recipe_steps`, `recipe_ingredients` | SELECT chỉ `published` | SELECT chỉ `published` | CRUD cả `draft`/`archived` |
| `nutrition_tags`, `ingredient_nutrients` và mapping | SELECT active/public | SELECT active/public | CRUD |
| `profiles`, `user_preferences` | Không | SELECT/UPDATE hồ sơ & tùy chọn bản thân, **không tự đổi role** | Duyệt quyền có kiểm soát |
| `favorites`, `scan_sessions`, `scan_detections`, `scan_ingredients` | Không | Chỉ dữ liệu sở hữu | Theo policy, không tùy tiện truy xuất user khác |
| `recommendation_feedback` | Không | Chỉ tạo/cập nhật/xem bản thân | Thống kê ẩn danh không lộ PII |
| `ai_models`, `ai_labels` | Chỉ public metadata nếu cần | Chỉ public metadata nếu cần | Quản lý |
| `audit_logs` | Không | Không | SELECT có kiểm soát; INSERT server-only |

**Lưu ý Supabase mới:** cần thực hiện cả `GRANT/REVOKE` và `RLS`; chỉ viết policy mà không rà soát grant là chưa đủ. Xem nguồn: https://supabase.com/docs/guides/database/postgres/row-level-security.

## 4. Chính sách ảnh và dữ liệu cá nhân

- Tuân thủ nguyên tắc bảo vệ dữ liệu cá nhân theo pháp luật Việt Nam hiện hành (Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 có hiệu lực từ 01/01/2026 và các văn bản hướng dẫn thi hành): tối thiểu hóa dữ liệu thu thập, đồng ý tường minh (opt-in) và đảm bảo quyền tự xóa dữ liệu.
- `POST /ai/detect` đọc cờ EXIF Orientation để xoay ảnh về đúng chiều hiển thị chuẩn, **xóa bỏ toàn bộ metadata EXIF (đặc biệt là tọa độ GPS và thông tin thiết bị)** khi giải mã sang mảng RGB cho inference, và không upload ảnh nguyên liệu lên Supabase Storage; nếu thư viện tạo temporary upload file, đóng và xóa ngay sau request.
- `save_history=false` mặc định cho cả user đã login; guest không được đặt `true`.
- `save_history=true` lưu nhãn, bbox (trên khung ảnh đã xoay chuẩn EXIF) và danh sách nguyên liệu chính sau xác nhận, **không lưu ảnh gốc**.
- UI cần nêu rõ lưu lịch sử là tùy chọn, cho phép User xem và xóa những lịch sử kết quả mà họ đã chủ động lưu; API `GET/DELETE /scan-sessions/{scan_id}` phải kiểm tra owner (trả `404 SCAN_NOT_OWNED` nếu không tồn tại hoặc không thuộc chủ sở hữu); khi xóa phiên lịch sử, hộp thoại UI cảnh báo người dùng rằng kết quả nhận diện và các đánh giá (`recommendation_feedback`) gắn với phiên đó sẽ bị xóa vĩnh viễn theo `ON DELETE CASCADE`.
- Không ghi binary file, raw JWT, token, địa chỉ IP cá nhân, email, hình ảnh vào audit log và log hệ thống.

## 5. Biến môi trường

```text
# FRONTEND — chỉ giá trị public
VITE_SUPABASE_URL=...
VITE_SUPABASE_PUBLISHABLE_KEY=...
VITE_API_BASE_URL=http://localhost:8000/api/v1

# BACKEND — KHÔNG commit .env
SUPABASE_URL=...
SUPABASE_SECRET_KEY=...    # chỉ khi thực sự cần service role/secret, tùy SDK
SUPABASE_DB_URL=...       # chỉ nếu chọn direct database
ALLOWED_ORIGINS=http://localhost:5173
MODEL_ARTIFACT_PATH=...
MAX_UPLOAD_BYTES=5242880
```

Tên biến có thể tùy SDK/phiên bản Supabase đang dùng. Không đưa bí mật vào `VITE_*`, trình duyệt, ảnh chụp báo cáo hoặc tài liệu Git.

## 6. Môi trường triển khai

| Môi trường | Frontend | Backend | Database/AI |
|---|---|---|---|
| Local | Vite dev server (localhost:5173) | Uvicorn (localhost:8000) | Supabase project dev + model local |
| Staging | Web staging (HTTPS) | FastAPI staging (HTTPS) | DB/bucket/model tách biệt hoặc chính sách dữ liệu thử nghiệm |
| Demo | Build Vite static | FastAPI chạy bằng process/container phù hợp | Supabase project của nhóm; model đã benchmark |

Không đưa vào production khi chưa có test quyền, bảo vệ endpoint upload, kiểm tra nguồn ảnh/công thức và giấy phép model.

## 7. Observability và xử lý sự cố

- Mỗi request có `request_id` để nối log; không log nội dung ảnh/tokens.
- Ghi `model_version`, image dimensions, thời gian decode/infer/map nhưng không có ảnh nhạy cảm.
- Phân biệt lỗi API, lỗi model, lỗi database; client nhận thông báo thân thiện.
- Khi DB/AI lỗi, cho phép User quay lại màn nhập nguyên liệu; API gợi ý vẫn chạy độc lập ngay cả khi model thị giác gặp lỗi.
