# Data Dictionary — PostgreSQL

**Quy ước:** `PK` khóa chính; `FK` khóa ngoại; `UQ` duy nhất; `NN` NOT NULL; `?` nullable; `ts` = `timestamptz`. Kiểu `text` có thể đặt giới hạn bằng CHECK tại migration. Dưới đây là **schema thiết kế**, không phải cấu trúc đã triển khai.

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
| category | varchar(40) | NN | vegetable/protein/seafood/spice/other |
| is_active | boolean | NN, DEFAULT true | Được chọn trong UI |
| created_at | ts | NN, DEFAULT now() | Tạo bản ghi |

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
| ingredient_id | uuid | FK→ingredients.id, NN | Mã chuẩn nội bộ |

Unique `(model_id, class_index)`; đổi model phải đối chiếu lại ánh xạ.

## 6. `recipes`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã món ăn |
| slug | text | UQ, NN | URL slug |
| name_vi | text | NN | Tên món |
| description | text | ? | Giới thiệu ngắn tự viết |
| cuisine_code | varchar(2) | NN, CHECK(VN/EU/US) | Nhóm ẩm thực theo UI |
| country_code | varchar(2) | ? | Mã quốc gia chi tiết nếu biết |
| prep_minutes | integer | NN, CHECK ≥0 | Thời gian sơ chế |
| cook_minutes | integer | NN, CHECK ≥0 | Thời gian nấu |
| cover_image_path | text | ? | Path ảnh được phép trên Storage |
| source_name | text | ? | Tên nguồn/đơn vị cung cấp |
| source_url | text | ? | Liên kết tham khảo |
| content_license | text | ? | Giấy phép hoặc `original` |
| status | varchar(12) | NN, CHECK(draft/published/archived) | Trạng thái |
| author_id | uuid | FK→profiles.id, NN | Admin tạo |
| created_at | ts | NN, DEFAULT now() | Ngày tạo |
| updated_at | ts | NN, DEFAULT now() | Ngày cập nhật |

`total_minutes = prep_minutes + cook_minutes` là **thuộc tính tính toán ở API**, không tạo cột lưu trữ.

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

Không có `image_path`: backend không lưu ảnh nguyên liệu gốc trong MVP. User có quyền xóa phiên; detections/ingredients dùng `ON DELETE CASCADE`, feedback.scan_session_id nên dùng `ON DELETE SET NULL`.

## 12. `scan_detections`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Dự đoán thô |
| scan_session_id | uuid | FK→scan_sessions.id, NN | Lượt scan |
| ai_label_id | uuid | FK→ai_labels.id, NN | Nhãn theo model version |
| confidence | numeric(4,3) | NN, CHECK 0..1 | Độ tin cậy |
| x1, y1, x2, y2 | numeric(6,5) | NN, CHECK 0..1, x1<x2, y1<y2 | Box chuẩn hóa xyxy |

## 13. `scan_ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| scan_session_id | uuid | PK, FK→scan_sessions.id | Lượt scan |
| ingredient_id | uuid | PK, FK→ingredients.id | ID đã xác nhận |
| provenance | varchar(10) | NN, CHECK(ai/manual/corrected) | Nguồn chọn cuối cùng |

Chỉ cập nhật sau khi user xác nhận và gửi `scan_id` hợp lệ qua `/recommendations`.

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
| user_id | uuid | FK→profiles.id, NN | Người gửi |
| recipe_id | uuid | FK→recipes.id, NN | Món đánh giá |
| scan_session_id | uuid | FK→scan_sessions.id, ? | Gắn scan nếu có, phải cùng user |
| rating | smallint | NN, CHECK 1..5 | Độ hữu ích, **không dùng như chất lượng AI** |
| note | varchar(500) | ? | Ý kiến |
| created_at | ts | NN, DEFAULT now() | Thời điểm |

## 16. `audit_logs`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Log |
| actor_id | uuid | FK→profiles.id, NN | Admin thao tác |
| action | text | NN | create/update/publish/archive/remap... |
| entity_type | text | NN | recipes/ingredients/ai_labels/nutrition_tags |
| entity_id | uuid | NN | ID bản ghi thay đổi |
| before_json | jsonb | ? | Giá trị trước (đã loại bí mật/PII) |
| after_json | jsonb | ? | Giá trị sau (đã loại bí mật/PII) |
| created_at | ts | NN, DEFAULT now() | Thời điểm |

## 17. Checklist migration

- [ ] Tạo bảng theo thứ tự FK, thêm ON DELETE phù hợp chính sách xóa dữ liệu.
- [ ] Khai báo ENUM/CHECK/UNIQUE/INDEX và trigger `updated_at`.
- [ ] Kích hoạt RLS, REVOKE quyền thừa, cấp đúng GRANT cho các schema exposed.
- [ ] Kiểm thử anon/user A/user B/admin và service role; không dựa vào kiểm tra UI.
- [ ] Seed ingredient/recipe/nutrition tags có nguồn; không giả định đã có dữ liệu.
- [ ] Tạo test cho trạng thái `published` và điều kiện có required ingredient + step.
