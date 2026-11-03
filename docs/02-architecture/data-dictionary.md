# Data Dictionary — PostgreSQL (>= 15)

**Quy ước:** `PK` khóa chính; `FK` khóa ngoại; `UQ` duy nhất; `NN` NOT NULL; `?` nullable; `ts` = `timestamptz`. Kiểu `text` có thể đặt giới hạn bằng CHECK tại migration. Dưới đây là **schema thiết kế (`0.9.0-draft`)**, không phải cấu trúc đã triển khai.

## 1. `profiles` (liên kết Supabase Auth)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK, FK→`auth.users.id`, NN | Đồng nhất với user Auth |
| display_name | varchar(100) | ? | Tên hiển thị |
| role | varchar(10) | NN, DEFAULT `user`, CHECK(user/admin) | Vai trò server-controlled |
| created_at | ts | NN, DEFAULT now() | Ngày tạo |

Không để client tự cập nhật `role`. Email/mật khẩu do Supabase Auth quản lý, không nhân bản vào `profiles`.

## 2. `ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã nguyên liệu chuẩn |
| slug | text | UQ, NN | Mã ổn định dùng hiển thị/tra cứu |
| name_vi | text | NN | Tên tiếng Việt |
| category | varchar(40) | NN, CHECK(`vegetable`/`protein`/`seafood`/`spice`/`pantry`/`other`) | Phân nhóm nguyên liệu (`spice` là gia vị củ quả tươi nhận diện qua ảnh như tỏi, ớt, gừng; `pantry` là gia vị nền/chất lỏng gia dụng sẵn có trong bếp như muối, đường, nước mắm, dầu ăn, tiêu xay, giấm, hạt nêm...; không lưu nước lọc vào bảng này) |
| is_active | boolean | NN, DEFAULT true | Được chọn trong UI (`GET /ingredients` chỉ trả bản ghi `is_active = true`) |
| created_at | ts | NN, DEFAULT now() | Tạo bản ghi |

Không được đổi `category` (sang/từ `pantry`) hoặc đặt `is_active = false` nếu nguyên liệu đang được dùng trong bất kỳ công thức `published` nào hoặc đang được trỏ bởi `ai_labels` của model `draft`/`active` (`400 INGREDIENT_IN_USE`).

## 3. `ingredient_aliases`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã alias |
| ingredient_id | uuid | FK→ingredients.id, NN | Nguyên liệu chuẩn |
| alias | text | NN | Tên đồng nghĩa hiển thị |
| normalized_alias | text | NN | Bỏ dấu/lowercase/trim để tìm kiếm |
| locale | varchar(10) | NN, DEFAULT `vi` | vi/en/... |

Unique `(ingredient_id, normalized_alias, locale)`; tên đồng nghĩa trùng giữa các nguyên liệu khác nhau cần được xử lý thủ công thay vì ánh xạ mù.

## 4. `ai_models`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Phiên bản model |
| version | text | UQ, NN | Ví dụ `food-yolo-v1` |
| family | text | NN | Model family chọn sau thử nghiệm |
| dataset_version | text | NN | Version dữ liệu huấn luyện |
| artifact_ref | text | NN | URI artifact bảo vệ, không commit weights |
| confidence_threshold | numeric(4,3) | NN, DEFAULT 0.25, CHECK 0..1 | Ngưỡng khởi tạo cần tuning |
| status | varchar(12) | NN, CHECK(draft/active/archived) | Vòng đời model |
| created_at | ts | NN, DEFAULT now() | Tạo version |

## 5. `ai_labels`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | ID ánh xạ nhãn |
| model_id | uuid | FK→ai_models.id, NN | Model version |
| class_index | integer | NN, CHECK ≥0 | Chỉ số class trong model |
| class_name | text | NN | Tên class trong file dataset YAML |
| ingredient_id | uuid | FK→ingredients.id (`ON DELETE RESTRICT`), NN | Mã chuẩn nội bộ (bắt buộc trỏ tới nguyên liệu `is_active = true` và `category != 'pantry'`) |

Unique `(model_id, class_index)`; bảng ánh xạ của model `active`/`archived` là bất biến (`400 MODEL_IMMUTABLE`). Khi kích hoạt model từ `draft` hoặc rollback từ `archived` sang `active`, toàn bộ `ingredient_id` được trỏ tới phải đang `is_active = true` và `category != 'pantry'` (`400 MODEL_NOT_ACTIVATABLE`).

## 6. `recipes`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã món ăn |
| slug | text | UQ, NN | URL slug |
| name_vi | text | NN | Tên món |
| description | text | ? | Giới thiệu ngắn tự viết |
| cuisine_code | varchar(2) | NN, CHECK(VN/EU/US) | Nhóm ẩm thực theo UI |
| country_code | varchar(2) | ? | Mã quốc gia chi tiết nếu biết |
| prep_minutes | integer | NN, CHECK ≥0 | Thời gian sơ chế cơ học (rửa, gọt, thái, băm) |
| cook_minutes | integer | NN, CHECK ≥0 | Tổng thời gian chế biến nhiệt trên bếp **cộng với thời gian ướp, ủ hoặc ninh/chờ bắt buộc** trong quy trình nấu |
| cover_image_path | text | ? | Path ảnh được phép trên Storage |
| source_name | text | ? | Tên nguồn/đơn vị cung cấp |
| source_url | text | ? | Liên kết tham khảo |
| content_license | text | ? | Giấy phép hoặc `original` |
| status | varchar(12) | NN, CHECK(draft/published/archived) | Trạng thái |
| author_id | uuid | FK→profiles.id, NN | Admin tạo |
| created_at | ts | NN, DEFAULT now() | Ngày tạo |
| updated_at | ts | NN, DEFAULT now() | Ngày cập nhật |

`total_minutes = prep_minutes + cook_minutes` là **thuộc tính tính toán ở API**, không tạo cột lưu trữ. Công thức ở trạng thái `published` bắt buộc có ít nhất 1 bước nấu, ít nhất 1 nguyên liệu bắt buộc thuộc nhóm chính (`category != 'pantry'`), mọi nguyên liệu trong món đều `is_active = true`, và không có bước đơn lẻ nào có `estimated_minutes > prep_minutes + cook_minutes`.

## 7. `recipe_ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| recipe_id | uuid | PK (composite), FK→recipes.id | Món |
| ingredient_id | uuid | PK (composite), FK→ingredients.id | Nguyên liệu |
| is_required | boolean | NN, DEFAULT true | Thành phần bắt buộc |
| display_quantity | text | ? | Ví dụ `2 quả`, chỉ để tham khảo, không suy ra từ ảnh |
| sort_order | integer | NN, DEFAULT 0 | Thứ tự hiển thị |

## 8. `recipe_steps`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã bước |
| recipe_id | uuid | FK→recipes.id, NN | Món |
| step_no | integer | NN, CHECK ≥1; UQ(recipe_id, step_no) | Thứ tự bước |
| instruction | text | NN | Nội dung gốc có quyền sử dụng |
| estimated_minutes | integer | ?, CHECK ≥0 | Thời gian bước nếu có |

## 9. `nutrition_tags`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã nhóm |
| code | text | UQ, NN | `protein_source`, `vitamin_c`, ... |
| name_vi | text | NN | Nhãn định tính |
| description | text | NN | Giải thích giới hạn sử dụng |
| is_active | boolean | NN, DEFAULT true | Hiển thị |

## 10. `ingredient_nutrition_tags`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| ingredient_id | uuid | PK, FK→ingredients.id | Nguyên liệu |
| nutrition_tag_id | uuid | PK, FK→nutrition_tags.id | Nhóm chất |
| source_url | text | NN | Nguồn kiểm chứng |
| note | text | ? | Cách diễn giải có điều kiện |
| reviewed_at | ts | ? | Ngày nhóm kiểm duyệt |

Không ghi "giàu protein", "ít béo" khi không có căn cứ và tiêu chí định lượng; tốt nhất dùng "có chứa/nguồn tham khảo về ...".

## 11. `scan_sessions` (chỉ lưu nếu chủ động opt-in)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Lượt scan |
| user_id | uuid | FK→profiles.id, NN | Người đồng ý lưu |
| model_id | uuid | FK→ai_models.id, NN | Model dùng |
| created_at | ts | NN, DEFAULT now() | Thời điểm |

Không có `image_path`: backend không lưu ảnh nguyên liệu gốc trong MVP. User có quyền xóa phiên; `scan_detections`, `scan_ingredients` và `recommendation_feedback.scan_session_id` đều dùng `ON DELETE CASCADE` (xem [ADR-012](../07-decisions/ADR-012-feedback-uniqueness-and-context.md)).

## 12. `scan_detections`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Dự đoán thô |
| scan_session_id | uuid | FK→scan_sessions.id, NN | Lượt scan |
| ai_label_id | uuid | FK→ai_labels.id, NN | Nhãn theo model version |
| confidence | numeric(4,3) | NN, CHECK 0..1 | Độ tin cậy |
| x1, y1, x2, y2 | numeric(6,5) | NN, CHECK 0..1, x1<x2, y1<y2 | Box chuẩn hóa xyxy (tính trên khung ảnh đã xoay chuẩn chiều EXIF) |

## 13. `scan_ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| scan_session_id | uuid | PK, FK→scan_sessions.id | Lượt scan |
| ingredient_id | uuid | PK, FK→ingredients.id | ID nguyên liệu chính đã xác nhận (`category != 'pantry'`) |
| provenance | varchar(10) | NN, CHECK(ai/manual/corrected) | Nguồn chọn cuối cùng |

Chỉ cập nhật sau khi user xác nhận và gửi `scan_id` hợp lệ qua `/recommendations`. Trạng thái bật/tắt gia vị `pantry` chỉ lưu trên client (`localStorage`/session), không lưu vào `scan_ingredients`.

## 14. `favorites`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| user_id | uuid | PK, FK→profiles.id | Chủ sở hữu |
| recipe_id | uuid | PK, FK→recipes.id | Món đã lưu |
| created_at | ts | NN, DEFAULT now() | Thời điểm |

## 15. `recommendation_feedback`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã feedback |
| user_id | uuid | FK→profiles.id (`ON DELETE CASCADE`), NN | Người gửi |
| recipe_id | uuid | FK→recipes.id (`ON DELETE CASCADE`), NN | Món đánh giá |
| scan_session_id | uuid | FK→scan_sessions.id (`ON DELETE CASCADE`), ? | Gắn scan nếu có, phải cùng user |
| rating | smallint | NN, CHECK 1..5 | Độ hữu ích, **không dùng như chất lượng AI** |
| note | varchar(500) | ? | Ý kiến |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo lần đầu |
| updated_at | ts | NN, DEFAULT now() | Thời điểm cập nhật gần nhất (khi upsert) |

Ràng buộc duy nhất: `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)` (yêu cầu PostgreSQL >= 15). Gửi lần đầu trong một ngữ cảnh tạo bản ghi mới (`201 Created`); gửi lại trong cùng `(user_id, recipe_id, scan_session_id)` cập nhật `rating`, `note`, `updated_at` (`200 OK`). Khi thống kê toàn hệ thống, lấy bản ghi có `updated_at` mới nhất cho mỗi `(user_id, recipe_id)`.

## 16. `audit_logs`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Log |
| actor_id | uuid | FK→profiles.id, NN | Admin thao tác |
| action | text | NN | create/update/publish/archive/remap... |
| entity_type | text | NN | recipes/ingredients/ai_models/ai_labels/nutrition_tags |
| entity_id | uuid | NN | ID bản ghi thay đổi |
| before_json | jsonb | ? | Giá trị trước (đã loại bí mật/PII) |
| after_json | jsonb | ? | Giá trị sau (đã loại bí mật/PII) |
| created_at | ts | NN, DEFAULT now() | Thời điểm |

## 17. Checklist migration

- [ ] Xác nhận phiên bản PostgreSQL trên dự án Supabase là **>= 15** (bắt buộc cho `UNIQUE NULLS NOT DISTINCT` trên `recommendation_feedback`).
- [ ] Tạo bảng theo thứ tự FK, thêm `ON DELETE` phù hợp chính sách xóa dữ liệu (`ON DELETE CASCADE` cho `scan_detections`, `scan_ingredients`, `recommendation_feedback.scan_session_id`; `ON DELETE RESTRICT` cho `recipe_ingredients.ingredient_id` và `ai_labels.ingredient_id`).
- [ ] Khai báo ENUM/CHECK (`ingredients.category IN ('vegetable', 'protein', 'seafood', 'spice', 'pantry', 'other')`), UNIQUE/INDEX và trigger `updated_at` cho `recipes` và `recommendation_feedback`.
- [ ] Kích hoạt RLS, REVOKE quyền thừa, cấp đúng GRANT cho các schema exposed.
- [ ] Kiểm thử anon/user A/user B/admin và service role; không dựa vào kiểm tra UI.
- [ ] Seed ingredient/recipe/nutrition tags có nguồn: tách rõ nhóm `spice` (tỏi, ớt, gừng) và nhóm `pantry` (muối, đường, nước mắm, dầu ăn, tiêu xay, nước tương, giấm, hạt nêm...; không tạo bản ghi cho nước lọc).
- [ ] Tạo test cho trạng thái `published` (đủ bước, đủ nguyên liệu chính bắt buộc ngoài `pantry`, mọi nguyên liệu `is_active = true`, không có bước đơn lẻ vượt `total_minutes`) và test chặn `INGREDIENT_IN_USE`.
