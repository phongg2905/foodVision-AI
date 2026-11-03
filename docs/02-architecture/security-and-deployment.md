# Bảo mật, quyền riêng tư và triển khai

**Trạng thái:** Đề xuất; phải kiểm tra khi tích hợp môi trường Supabase/Backend thật.

## 1. Threat model ngắn

| Nguy cơ | Rủi ro | Biện pháp |
|---|---|---|
| Client giả vai trò admin | Sửa công thức và danh mục | Verify Supabase JWT + tra quyền admin từ nguồn tin cậy phía server; không tin `role` gửi từ body |
| Đọc dữ liệu user khác | Lộ favorites/history | RLS ownership + kiểm tra user_id khi dùng service-role |
| File giả ảnh / ảnh quá lớn | Exhaust memory, thư viện ảnh lỗi | Multipart 5 MB, kiểm tra magic bytes, giải mã với giới hạn kích thước pixel, timeout |
| Injection qua search | Lỗi truy vấn | Query parameterized/ORM; validate sort/filter; không ghép SQL từ input |
| Lộ Supabase service key | Toàn quyền DB | Secret chỉ ở backend env, không commit, không expose qua Vite `VITE_*` |
| Trích xuất dữ liệu dinh dưỡng sai | Gây hiểu nhầm sức khỏe | Dữ liệu định tính, nguồn rõ, bỏ tuyên bố y khoa và định lượng không có căn cứ |
| Abuse endpoint detect | Tốn CPU/GPU | Rate limiting theo IP/user, quota, concurrency limit |
| Lưu ảnh trái ý | Lộ hình ảnh cá nhân | Không lưu ảnh gốc bền vững; không ghi log ảnh; dọn file spool tạm (nếu framework tạo); history kết quả **opt-in** |

## 2. Quyền và JWT

- Guest có thể đọc món published, danh mục nguyên liệu và gửi detect/recommend, nhưng không ghi bảng nội bộ.
- Supabase Auth cấp token; FastAPI phải xác thực chữ ký, issuer, audience, expiration, subject; ưu tiên phương thức phù hợp kiểu signing key, JWKS nếu asymmetric.
- Quyền `Admin` phải được server xác minh; vai trò trong `profiles.role` do luồng cấp quyền có kiểm soát. Không cho người dùng tự PATCH role.
- Dù JWT hợp lệ, phải kiểm tra quan hệ sở hữu trước khi ghi `scan_ingredients` vào scan_session, hoặc nhận feedback chứa scan_id.
- Nếu FastAPI dùng service-role (bỏ qua RLS), **FastAPI phải tự enforce đầy đủ authorization**, không dựa vào RLS. Đối với Data API trực tiếp, RLS + GRANT phải phù hợp.

## 3. Ma trận RLS/grants (định hướng)

| Bảng | anon | authenticated | Admin qua backend |
|---|---|---|---|
| ingredients, aliases | SELECT có kiểm soát | SELECT | CRUD |
| recipes, steps, recipe_ingredients | SELECT chỉ published | SELECT chỉ published | CRUD cả draft |
| nutrition_tags và mapping | SELECT active/public | SELECT active/public | CRUD |
| profiles | Không | SELECT/UPDATE tên bản thân, **không role** | Duyệt quyền có kiểm soát |
| favorites, scan_sessions, detections, scan_ingredients | Không | Chỉ dữ liệu sở hữu | Theo policy, không tùy tiện truy xuất user khác |
| recommendation_feedback | Không | Chỉ tạo/xem bản thân nếu cần | Thống kê không lộ PII |
| ai_models, ai_labels | Chỉ public metadata nếu cần | Chỉ public metadata nếu cần | Quản lý |
| audit_logs | Không | Không | SELECT có kiểm soát; INSERT server-only |

**Lưu ý Supabase mới:** cần thực hiện cả `GRANT/REVOKE` và `RLS`; chỉ viết policy mà không rà soát grant là chưa đủ. Xem nguồn: https://supabase.com/docs/guides/database/postgres/row-level-security.

## 4. Chính sách ảnh và dữ liệu

- `POST /ai/detect` giải mã ảnh cho inference và không upload ảnh nguyên liệu lên Supabase Storage; nếu thư viện tạo temporary upload file, đóng và xóa ngay sau request.
- `save_history=false` mặc định cho cả user đã login; guest không được đặt true.
- `save_history=true` lưu nhãn, bbox và danh sách nguyên liệu sau xác nhận, **không lưu ảnh gốc**.
- UI cần nêu rõ lưu lịch sử là tùy chọn, cho phép User xem và xóa những lịch sử kết quả mà họ đã chủ động lưu; API `GET/DELETE /scan-sessions` phải kiểm tra owner; xóa bản ghi con bằng FK phù hợp.
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
- Ghi model version, image dimensions, thời gian decode/infer/map nhưng không có ảnh nhạy cảm.
- Phân biệt lỗi API, lỗi model, lỗi database; client nhận thông báo thân thiện.
- Khi DB/AI lỗi, cho phép User quay lại màn nhập nguyên liệu; API gợi ý có thể vẫn chạy nếu model lỗi.
