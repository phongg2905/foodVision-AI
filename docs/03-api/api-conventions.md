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
| 200 | Thành công, trả kết quả | GET, POST recommend/detect |
| 201 | Tạo thành công | POST admin recipe, favorite, feedback |
| 204 | Xóa/unfavorite thành công, body trống | DELETE favorite |
| 400 | Request sai quy tắc nghiệp vụ | Xuất công thức chưa đủ nguyên liệu/bước |
| 401 | Chưa xác thực hoặc token không hợp lệ | Lưu favorite khi guest |
| 403 | Đã xác thực nhưng không có quyền | User gọi Admin |
| 404 | Bản ghi không thấy/không được phép xem | Recipe draft |
| 409 | Xung đột unique | Tạo slug đã tồn tại |
| 413 | Ảnh lớn hơn 5 MB | Upload 6 MB |
| 415 | Unsupported Media Type | Ảnh TIFF/SVG |
| 422 | Input không hợp lệ hoặc ảnh không giải mã | ingredient ID sai/ảnh hỏng |
| 429 | Quá rate limit | Spam AI detect |
| 500 | Server error không mong muốn | Lỗi nội bộ |
| 503 | AI/DB service tạm không sẵn sàng | Model chưa load |

```json
{
  "code": "INVALID_INGREDIENTS",
  "message": "Danh sách nguyên liệu không hợp lệ.",
  "details": {"ingredient_ids": ["must contain at least one valid ID"]},
  "request_id": "req_example_001"
}
```

**Quy ước riêng:** `POST /ai/detect` trả `200` với `detections=[]` khi mô hình chạy thành công nhưng không thấy nguyên liệu, **không phải lỗi 404**.

## 4. Auth & security

- Public endpoint không cần token; nếu khách gửi token lỗi vào endpoint private thì trả 401.
- `save_history=true` bắt buộc token hợp lệ; không tự động lưu ảnh và không lưu lịch sử cho guest. User xem/xóa lịch sử đã lưu qua `/scan-sessions`, phải xác minh owner.
- `POST /recommendations` với `scan_id` bắt buộc token của người sở hữu scan đó; không tự cho phép sửa scan của người khác.
- Quyền Admin kiểm tra server-side từ nguồn tin cậy; không tin header `X-Role`, input `role`, hay localStorage.
- Không trả SQL/stacktrace/token/secret trong JSON lỗi.

## 5. Phân trang, sắp xếp, idempotency

- List endpoints: `limit` (mặc định 20, tối đa 50), `offset` (mặc định 0); kết quả gồm `items`, `total`, `limit`, `offset`.
- `GET /recipes` trả món `published` và sắp theo tên mặc định; sort bổ sung phải có whitelist.
- `GET /recipes/{id}` trả 404 nếu món draft/archived cho public.
- `POST /favorites` dùng PK `(user_id, recipe_id)`, gửi lại cùng món không tạo bản ghi trùng, trả 200 nếu đã tồn tại hoặc 201 nếu mới.
- Chuyển model sang `active` phải có đầy đủ class mappings và archive model active cũ trong transaction (tối đa 1 model active).
- `PATCH /admin/ai-labels/{id}` chỉ sửa mapping của **model draft**; nếu model active, phải tạo version mới.
- `PATCH /admin/recipes/{id}` có tính chất partial update; nếu truyền `ingredients` hoặc `steps`, **thay thế toàn bộ tập con trong transaction**, không merge từng dòng ngầm.
- Mã request_id nên có trong response header `X-Request-ID` và các body lỗi.

## 6. Workflow frontend/backend

1. Nhóm thiết kế cùng review file OpenAPI trước coding.
2. Backend dùng Pydantic tạo schema và các route khớp contract; khi chạy kiểm `/openapi.json`.
3. Frontend sinh typed client nếu cần, hoặc viết mock theo examples; không hardcode class name, dùng `ingredient_id`.
4. Mọi thay đổi breaking API cần cập nhật `openapi.yaml`, README, consumer FE, test API và ghi changelog/ADR nếu ảnh hưởng lớn.

**Swagger**: ở môi trường FastAPI chạy thật, `/docs` hiển thị Swagger UI, `/redoc` hiển thị ReDoc. Đây không phải trang tài liệu đã hoạt động tại thời điểm viết đặc tả này.
