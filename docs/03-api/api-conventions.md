# API Conventions — FoodVision AI v1

## 1. Cơ sở

- Base URL local: `http://localhost:8000/api/v1`.
- Content-Type mặc định: `application/json; charset=utf-8`.
- Upload ảnh: `multipart/form-data` với `file` và `save_history` (boolean).
- Supabase Auth xử lý sign-up/sign-in phía client; Backend **không tự viết `/login`**.
- `Authorization: Bearer <Supabase access token>` cho endpoint cá nhân và quản trị; `/ai/detect` cho phép guest nếu `save_history=false`.
- UUID là chuỗi định dạng UUID; thời gian là ISO 8601 UTC; điểm gợi ý 0–100 làm tròn 1 chữ số; confidence 0..1.
- Ngôn ngữ phản hồi nội dung người dùng: tiếng Việt; tên code/path/field: tiếng Anh snake_case.

## 2. Danh sách endpoint thiết kế

| Nhóm | Method | Đường dẫn sau `/api/v1` | Truy cập |
|---|---|---|---|
| Health | GET | `/health` | Public |
| Catalogue | GET | `/ingredients` | Public |
| Catalogue | GET | `/nutrition-tags` | Public |
| Recipes | GET | `/recipes` | Public |
| Recipes | GET | `/recipes/{recipe_id}` | Public |
| AI | POST | `/ai/detect` | Public (lưu history cần login) |
| Recommendation | POST | `/recommendations` | Public (ghi scan đã lưu cần login) |
| Favorites | GET | `/favorites` | User |
| Favorites | POST | `/favorites` | User |
| Favorites | DELETE | `/favorites/{recipe_id}` | User |
| Feedback | POST | `/feedback` | User |
| Scan history | GET | `/scan-sessions` | User |
| Scan history | GET | `/scan-sessions/{scan_id}` | User |
| Scan history | DELETE | `/scan-sessions/{scan_id}` | User |
| Admin recipes | GET | `/admin/recipes` | Admin |
| Admin recipes | GET | `/admin/recipes/{recipe_id}` | Admin |
| Admin recipes | POST | `/admin/recipes` | Admin |
| Admin recipes | PATCH | `/admin/recipes/{recipe_id}` | Admin |
| Admin recipes | PATCH | `/admin/recipes/{recipe_id}/status` | Admin |
| Admin ingredients | GET | `/admin/ingredients` | Admin |
| Admin ingredients | POST | `/admin/ingredients` | Admin |
| Admin ingredients | PATCH | `/admin/ingredients/{ingredient_id}` | Admin |
| Admin nutrition | PUT | `/admin/ingredients/{ingredient_id}/nutrition-tags` | Admin |
| Admin nutrition | GET | `/admin/nutrition-tags` | Admin |
| Admin nutrition | POST | `/admin/nutrition-tags` | Admin |
| Admin nutrition | PATCH | `/admin/nutrition-tags/{tag_id}` | Admin |
| Admin AI | GET | `/admin/ai-models` | Admin |
| Admin AI | POST | `/admin/ai-models` | Admin |
| Admin AI | PATCH | `/admin/ai-models/{model_id}/status` | Admin |
| Admin AI | GET | `/admin/ai-labels` | Admin |
| Admin AI | POST | `/admin/ai-labels` | Admin |
| Admin AI | PATCH | `/admin/ai-labels/{label_id}` | Admin |
| Admin audit | GET | `/admin/audit-logs` | Admin |

**Tổng:** 33 operations. Một đường dẫn REST có thể có nhiều operations. Định nghĩa chính xác ở `openapi.yaml`.

## 3. Mã HTTP và JSON lỗi

| Status | Ý nghĩa | Ví dụ |
|---|---|---|
| 200 | Thành công, trả kết quả (hoặc upsert bản ghi đã tồn tại) | GET, POST recommend/detect, POST favorite/feedback đã có |
| 201 | Tạo mới thành công | POST admin recipe, favorite mới, feedback mới |
| 204 | Xóa/unfavorite thành công, body trống | DELETE favorite, DELETE scan-session |
| 400 | Thao tác ghi/chuyển trạng thái vi phạm quy tắc toàn vẹn nghiệp vụ giữa các thực thể lưu trữ | Xuất công thức thiếu bước/nguyên liệu chính (`RECIPE_NOT_PUBLISHABLE`), sửa nguyên liệu đang dùng (`INGREDIENT_IN_USE`), sửa model bất biến (`MODEL_IMMUTABLE`), gán nhãn AI vào `pantry` (`INVALID_LABEL_MAPPING`) |
| 401 | Chưa xác thực hoặc token không hợp lệ | Lưu favorite khi guest |
| 403 | Đã xác thực nhưng không có quyền | User thường gọi `/admin/*` (`FORBIDDEN`) |
| 404 | Bản ghi không thấy hoặc không thuộc quyền sở hữu | Recipe draft/archived với public (`RECIPE_NOT_FOUND`), `scan_id` không tồn tại hoặc của người khác (`SCAN_NOT_OWNED`) |
| 409 | Xung đột khóa duy nhất (unique constraint) | Tạo slug/version/code đã tồn tại (`DUPLICATE_SLUG`) |
| 413 | Ảnh lớn hơn 5 MiB | Upload 6 MB (`IMAGE_TOO_LARGE`) |
| 415 | Định dạng/magic bytes file upload không được hỗ trợ | Ảnh HEIC/HEIF, TIFF, SVG (`UNSUPPORTED_IMAGE_TYPE`) |
| 422 | Tham số/payload đầu vào của request không hợp lệ về schema, kiểu hoặc miền giá trị | Ảnh JPEG/PNG/WebP hỏng không giải mã được (`INVALID_IMAGE`), `ingredient_ids` rỗng/chứa `pantry` (`INVALID_INGREDIENTS`), query mâu thuẫn (`INVALID_QUERY_PARAMS`), `rating` ngoài 1..5 (`VALIDATION_ERROR`) |
| 429 | Quá rate limit | Spam AI detect (`RATE_LIMITED`) |
| 500 | Server error không mong muốn | Lỗi nội bộ (`INTERNAL_ERROR`) |
| 503 | AI/DB service tạm không sẵn sàng | Model chưa load (`MODEL_NOT_READY`) |
| 504 | Quá thời gian chờ suy luận từ AI service | YOLO inference vượt ngưỡng timeout (`INFERENCE_TIMEOUT`) |

```json
{
  "code": "INVALID_INGREDIENTS",
  "message": "Danh sách nguyên liệu không hợp lệ.",
  "details": {
    "invalid_ids": ["55555555-5555-4555-8555-555555555555"],
    "reason": "pantry_in_main_list"
  },
  "request_id": "req_example_001"
}
```

**Quy ước phân biệt HTTP `400`, `409` và `422`:**
- `HTTP 422 Unprocessable Entity`: Dùng khi **tham số/payload đầu vào của request đọc hoặc tính toán không hợp lệ về mặt miền giá trị/khuôn dạng** (file ảnh hỏng không giải mã được, điểm `rating` ngoài `1..5`, query params mâu thuẫn `category=pantry&exclude_pantry=true`, hoặc truyền sai loại UUID nguyên liệu vào bộ tính điểm `/recommendations`).
- `HTTP 400 Bad Request`: Dùng khi **thao tác ghi/chuyển trạng thái trong CMS quản trị vi phạm quy tắc toàn vẹn nghiệp vụ giữa các thực thể lưu trữ** (`RECIPE_NOT_PUBLISHABLE`, `INGREDIENT_IN_USE`, `MODEL_NOT_ACTIVATABLE`, `MODEL_IMMUTABLE`, `INVALID_LABEL_MAPPING`). Mặc dù `INGREDIENT_IN_USE` và `MODEL_IMMUTABLE` có ngữ nghĩa gần với `409 Conflict`, FoodVision AI v1 dành riêng `409` cho xung đột khóa duy nhất (`DUPLICATE_SLUG`) và gom toàn bộ lỗi chặn quy tắc trạng thái về `400` để thống nhất xử lý lỗi phía client theo hợp đồng gốc.
- **Quy ước riêng cho `POST /ai/detect`:** Trả `200` với `detections=[]` khi mô hình chạy thành công nhưng không thấy nguyên liệu, **không phải lỗi 404**.
- **Quy ước riêng cho `SCAN_NOT_OWNED` (`HTTP 404`):** Giữ tên mã `SCAN_NOT_OWNED` để tương thích hợp đồng gốc nhưng luôn trả kèm HTTP `404 Not Found` cho cả trường hợp `scan_id` không tồn tại lẫn trường hợp `scan_id` thuộc người dùng khác nhằm chống dò quét định danh (anti-enumeration).

### Danh mục 20 mã lỗi nghiệp vụ chuẩn và cấu trúc `details`

| # | Mã lỗi (`code`) | HTTP | Ý nghĩa & Cấu trúc `details` |
|---:|---|---:|---|
| 1 | `IMAGE_TOO_LARGE` | 413 | Ảnh upload vượt quá 5 MiB (`details: {"max_bytes": 5242880}`) |
| 2 | `UNSUPPORTED_IMAGE_TYPE` | 415 | Định dạng/magic bytes không thuộc JPEG/PNG/WebP, ví dụ HEIC/TIFF/SVG (`details: {"allowed_types": ["image/jpeg", "image/png", "image/webp"]}`) |
| 3 | `INVALID_IMAGE` | 422 | Header là JPEG/PNG/WebP nhưng dữ liệu ảnh hỏng, không giải mã được RGB hoặc quá giới hạn pixel (`details: {"reason": "corrupted_or_unreadable_image"}`) |
| 4 | `INVALID_INGREDIENTS` | 422 | Danh sách nguyên liệu gửi lên `/recommendations` không hợp lệ (`details: {"invalid_ids": ["<uuid>"], "reason": "empty_main_ingredients" \| "pantry_in_main_list" \| "non_pantry_in_excluded_list" \| "unknown_or_inactive_id"}`) |
| 5 | `RECIPE_NOT_PUBLISHABLE` | 400 | Công thức không đủ điều kiện chuyển sang hoặc duy trì trạng thái `published` (`details: {"recipe_id": "<uuid>", "reasons": ["missing_required_main_ingredient" \| "inactive_ingredient" \| "missing_steps" \| "step_exceeds_total_minutes"]}`) |
| 6 | `UNAUTHORIZED` | 401 | Chưa đăng nhập hoặc JWT token hết hạn/không hợp lệ (`details: {}`) |
| 7 | `FORBIDDEN` | 403 | Đã đăng nhập nhưng không có quyền Admin (`details: {}`) |
| 8 | `SCAN_NOT_OWNED` | 404 | Không tìm thấy `scan_session` hoặc `scan_id` không thuộc quyền sở hữu của user hiện tại (`details: {"scan_id": "<uuid>"}`) |
| 9 | `RECIPE_NOT_FOUND` | 404 | Không tìm thấy bản ghi hoặc công thức đang ở trạng thái `draft`/`archived` đối với public (`details: {"recipe_id": "<uuid>"}`) |
| 10 | `DUPLICATE_SLUG` | 409 | Trùng khóa duy nhất: slug công thức/nguyên liệu, version model, code nhãn dinh dưỡng (`details: {"field": "slug", "value": "<slug>"}`) |
| 11 | `RATE_LIMITED` | 429 | Vượt giới hạn số lượng request trong khung thời gian (`details: {"retry_after_seconds": 60}`) |
| 12 | `INTERNAL_ERROR` | 500 | Lỗi hệ thống nội bộ không mong muốn (`details: {}`) |
| 13 | `MODEL_NOT_READY` | 503 | Dịch vụ AI hoặc model `active` chưa sẵn sàng phục vụ (`details: {}`) |
| 14 | `INVALID_QUERY_PARAMS` | 422 | Tham số truy vấn mâu thuẫn, ví dụ `category=pantry&exclude_pantry=true` (`details: {"params": ["category", "exclude_pantry"], "reason": "conflicting_pantry_filters"}`) |
| 15 | `VALIDATION_ERROR` | 422 | Lỗi schema/miền giá trị đầu vào chung, ví dụ `rating` ngoài 1..5 hoặc thiếu `source_url` (`details: {"field": "<field_name>", "reason": "<message>"}`) |
| 16 | `INGREDIENT_IN_USE` | 400 | Không thể đổi `category` (sang/từ `pantry`) hoặc tắt `is_active` vì đang dùng trong món `published` hoặc model `draft`/`active` (`details: {"ingredient_id": "<uuid>", "affected_published_recipe_ids": ["<uuid>"], "affected_active_or_draft_model_ids": ["<uuid>"]}`) |
| 17 | `MODEL_NOT_ACTIVATABLE` | 400 | Không thể chuyển model sang `active` (từ `draft` hoặc rollback từ `archived`) vì thiếu nhãn hoặc có nhãn trỏ tới nguyên liệu `inactive`/`pantry` (`details: {"model_id": "<uuid>", "unmapped_class_indices": [0, 1], "invalid_mapped_class_indices": [2, 3]}`) |
| 18 | `MODEL_IMMUTABLE` | 400 | Không được thêm/sửa `ai_labels` của model đang ở trạng thái `active` hoặc `archived` (`details: {"model_id": "<uuid>", "status": "active" \| "archived"}`) |
| 19 | `INVALID_LABEL_MAPPING` | 400 | Không được ánh xạ nhãn YOLO sang nguyên liệu thuộc nhóm `pantry` hoặc `inactive` (`details: {"ingredient_id": "<uuid>", "reason": "pantry_or_inactive_ingredient_not_allowed"}`) |
| 20 | `INFERENCE_TIMEOUT` | 504 | Quá thời gian chờ suy luận ảnh từ dịch vụ YOLO (`details: {"timeout_ms": 15000}`) |

## 4. Auth & security

- Public endpoint không cần token; nếu khách gửi token lỗi vào endpoint private thì trả 401.
- `save_history=true` bắt buộc token hợp lệ; không tự động lưu ảnh và không lưu lịch sử cho guest. User xem/xóa lịch sử đã lưu qua `/scan-sessions`, phải xác minh owner (`404 SCAN_NOT_OWNED` nếu sai chủ sở hữu hoặc không tồn tại).
- `POST /recommendations` và `POST /feedback` có kèm `scan_id` bắt buộc token của người sở hữu scan đó; nếu `scan_id` không tồn tại hoặc thuộc người khác thì trả `404 SCAN_NOT_OWNED`.
- Quyền Admin kiểm tra server-side từ nguồn tin cậy; không tin header `X-Role`, input `role`, hay localStorage.
- Không trả SQL/stacktrace/token/secret trong JSON lỗi.

## 5. Phân trang, sắp xếp, caching và idempotency

- List endpoints: `limit` (mặc định 20, tối đa 50), `offset` (mặc định 0); kết quả gồm `items`, `total`, `limit`, `offset`.
- `GET /ingredients` là endpoint công khai (không cần token), chỉ trả các nguyên liệu có `is_active = true`:
  - Hỗ trợ lọc theo `category` (`vegetable`, `protein`, `seafood`, `spice`, `pantry`, `other`) và `exclude_pantry` (`boolean`, mặc định `false`). Nếu gửi đồng thời `category=pantry&exclude_pantry=true`, trả `422 INVALID_QUERY_PARAMS`.
  - **Chính sách Cache:** Khi không truyền từ khóa tìm kiếm `q` (ví dụ `GET /ingredients?category=pantry`), trả `Cache-Control: public, max-age=300` (chấp nhận độ trễ tối đa 5 phút khi Admin sửa danh mục; CDN/reverse proxy phải dùng toàn bộ query string đã chuẩn hóa gồm `category`, `exclude_pantry`, `limit`, `offset` làm cache key). Khi có tham số `q`, trả `Cache-Control: no-store`.
- `GET /recipes` trả món `published` và sắp theo tên mặc định; sort bổ sung phải có whitelist.
- `GET /recipes/{id}` trả 404 (`RECIPE_NOT_FOUND`) nếu món `draft`/`archived` cho public.
- `POST /favorites` dùng PK `(user_id, recipe_id)`, gửi lại cùng món không tạo bản ghi trùng, trả 200 nếu đã tồn tại hoặc 201 nếu mới.
- `POST /feedback` dùng `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)`: gửi lần đầu trong một ngữ cảnh `(user_id, recipe_id, scan_session_id)` trả `201 Created`; gửi lại trong cùng ngữ cảnh sẽ upsert (`rating`, `note`, `updated_at`) và trả `200 OK`.
- Chuyển model sang `active` (từ `draft` hoặc rollback từ `archived`) phải có đầy đủ class mappings hợp lệ (`is_active = true`, `category != 'pantry'`) và archive model active cũ trong transaction (tối đa 1 model active).
- `POST /admin/ai-labels` và `PATCH /admin/ai-labels/{id}` chỉ cho phép thực hiện trên **model draft** và chỉ được trỏ tới nguyên liệu `is_active = true`, `category != 'pantry'`; nếu model đang `active`/`archived`, trả `400 MODEL_IMMUTABLE`.
- `PATCH /admin/recipes/{id}` có tính chất partial update; nếu truyền `ingredients` hoặc `steps`, **thay thế toàn bộ tập con trong transaction**, không merge từng dòng ngầm. Nếu công thức đang ở trạng thái `published`, backend vẫn kiểm tra đầy đủ các điều kiện xuất bản trong transaction trước khi commit (`400 RECIPE_NOT_PUBLISHABLE` nếu vi phạm).
- Mã `request_id` nên có trong response header `X-Request-ID` và các body lỗi.

## 6. Workflow frontend/backend

1. Nhóm thiết kế cùng review file OpenAPI trước coding.
2. Backend dùng Pydantic tạo schema và các route khớp contract; khi chạy kiểm `/openapi.json`.
3. Frontend sinh typed client nếu cần, hoặc viết mock theo examples; không hardcode class name, dùng `ingredient_id`.
4. Mọi thay đổi breaking API cần cập nhật `openapi.yaml`, README, consumer FE, test API và ghi changelog/ADR nếu ảnh hưởng lớn.

**Swagger**: ở môi trường FastAPI chạy thật, `/docs` hiển thị Swagger UI, `/redoc` hiển thị ReDoc. Đây không phải trang tài liệu đã hoạt động tại thời điểm viết đặc tả này.
