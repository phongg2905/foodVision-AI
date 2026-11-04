# Data Dictionary — PostgreSQL (>= 15)

**Quy ước:** `PK` khóa chính; `FK` khóa ngoại; `UQ` duy nhất; `NN` NOT NULL; `?` nullable; `ts` = `timestamptz`. Kiểu `text` có thể đặt giới hạn độ dài bằng `CHECK` tại migration. Dưới đây là **schema thiết kế chuẩn (`1.0.0`)**, bao gồm **16 bảng cốt lõi của MVP (`P0`)** và **4 bảng mở rộng Giai đoạn 2–4** cho lọc dị ứng, dinh dưỡng định lượng USDA cùng cá nhân hóa. Các cột đánh dấu *(Mở rộng GĐ 2–4)* đều có `DEFAULT` hoặc `NULL` để tương thích ngược 100% với hợp đồng `openapi.yaml` hiện hành.

## 1. `profiles` (liên kết Supabase Auth)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK, FK→`auth.users.id`, NN | Đồng nhất với tài khoản Supabase Auth |
| display_name | varchar(100) | ? | Tên hiển thị |
| role | varchar(10) | NN, DEFAULT `'user'`, CHECK(`user`/`admin`) | Vai trò do server kiểm soát (`Admin --\|> User` theo [ADR-011](../07-decisions/ADR-011-admin-role-inheritance.md)) |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo |

## 2. `ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã nguyên liệu chuẩn (`canonical_id`) |
| slug | text | UQ, NN | Mã ổn định dùng hiển thị/tra cứu (`tomato`, `tofu`...) |
| name_vi | text | NN | Tên chính thức tiếng Việt |
| category | varchar(40) | NN, CHECK(`vegetable`/`protein`/`seafood`/`spice`/`pantry`/`other`) | Phân nhóm nguyên liệu (`spice` là gia vị củ quả tươi nhận diện qua ảnh như tỏi, ớt, gừng; `pantry` là gia vị nền/chất lỏng gia dụng sẵn có trong bếp như muối, đường, nước mắm, dầu ăn, tiêu xay, giấm, hạt nêm...; không lưu nước lọc vào bảng này) |
| fdc_id | varchar(32) | ? | *(Mở rộng GĐ 3)* Mã tham chiếu USDA FoodData Central phục vụ đối chiếu dinh dưỡng định lượng |
| is_active | boolean | NN, DEFAULT true | Được chọn trong UI (`GET /ingredients` chỉ trả bản ghi `is_active = true`) |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo bản ghi |

Không được đổi `category` (sang/từ `pantry`) hoặc đặt `is_active = false` nếu nguyên liệu đang được dùng trong bất kỳ công thức `published` nào hoặc đang được trỏ bởi `ai_labels` của model `draft`/`active` (`400 INGREDIENT_IN_USE`).

## 3. `ingredient_aliases` (Từ đồng nghĩa & chuẩn hóa tiếng Việt — Thành phần 13)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã bản ghi bí danh |
| ingredient_id | uuid | FK→`ingredients.id` (`ON DELETE CASCADE`), NN | Nguyên liệu chuẩn tương ứng |
| alias | text | NN | Tên đồng nghĩa hiển thị (ví dụ `Đậu phụ`, `Đậu hũ`, `Cà chua bi`) |
| normalized_alias | text | NN | Chuỗi đã qua `casefold` + `đ -> d` + bỏ dấu Unicode NFD (`dau phu`, `dau hu`) |
| locale | varchar(10) | NN, DEFAULT `'vi'` | Ngôn ngữ (`vi` / `en`) |

Ràng buộc `UNIQUE(ingredient_id, normalized_alias, locale)` kèm GIN index `idx_alias_trgm` (`gin_trgm_ops`) để truy vấn không dấu và tam tự gần đúng `pg_trgm`.

## 4. `ai_models`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã phiên bản mô hình |
| version | text | UQ, NN | Định danh phiên bản (ví dụ `food-yolo-v1`) |
| family | text | NN | Họ mô hình (`Ultralytics YOLO`...) |
| dataset_version | text | NN | Phiên bản dataset huấn luyện |
| artifact_ref | text | NN | Đường dẫn/URI tới file trọng số (`ingredients_best.pt`) |
| confidence_threshold | numeric(4,3) | NN, DEFAULT 0.250, CHECK `0..1` | Ngưỡng sàn lọc phát hiện bbox (Thành phần 01) |
| review_threshold | numeric(4,3) | NN, DEFAULT 0.800, CHECK `0..1` | *(Mở rộng GĐ 2)* Ngưỡng $\tau$ kích hoạt cảnh báo xác nhận HITL `Review(x)` (Thành phần 14) |
| status | varchar(12) | NN, CHECK(`draft`/`active`/`archived`) | Vòng đời mô hình (chỉ tối đa 1 model `active` qua unique partial index) |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo |

## 5. `ai_labels`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | ID ánh xạ nhãn |
| model_id | uuid | FK→`ai_models.id` (`ON DELETE CASCADE`), NN | Model version |
| class_index | integer | NN, CHECK `>= 0` | Chỉ số class trong file `dataset.yaml` |
| class_name | text | NN | Tên class trong file dataset YAML (`tomato`, `tofu`...) |
| ingredient_id | uuid | FK→`ingredients.id` (`ON DELETE RESTRICT`), NN | Mã chuẩn nội bộ (bắt buộc trỏ tới nguyên liệu `is_active = true` và `category != 'pantry'`) |

Unique `(model_id, class_index)`; bảng ánh xạ của model `active`/`archived` là bất biến (`400 MODEL_IMMUTABLE`). Khi kích hoạt model từ `draft` hoặc rollback từ `archived` sang `active`, toàn bộ `ingredient_id` được trỏ tới phải đang `is_active = true` và `category != 'pantry'` (`400 MODEL_NOT_ACTIVATABLE`).

## 6. `recipes`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã món ăn |
| slug | text | UQ, NN | URL slug |
| name_vi | text | NN | Tên món ăn |
| description | text | ? | Giới thiệu ngắn tự biên soạn |
| cuisine_code | varchar(2) | NN, CHECK(`VN`/`EU`/`US`) | Nhóm ẩm thực theo UI |
| country_code | varchar(2) | ? | Mã quốc gia chi tiết nếu biết (`VN`, `IT`, `FR`...) |
| cooking_method | varchar(30) | ? | *(Mở rộng GĐ 3–4)* Cách chế biến chính (`canh`, `xao`, `kho`, `nuong`, `salad`...) phục vụ đặc trưng cá nhân hóa & đa dạng hóa MMR |
| required_equipment | text[] | NN, DEFAULT `'{}'` | *(Mở rộng GĐ 2)* Danh sách thiết bị cần có (`stove`, `oven`, `blender`...) cho kiểm tra $\text{EquipOK}$ |
| base_servings | smallint | NN, DEFAULT 2, CHECK `>= 1` | *(Mở rộng GĐ 3)* Số khẩu phần gốc $n_{\text{base}}$ để quy đổi tuyến tính |
| prep_minutes | integer | NN, CHECK `>= 0` | Thời gian sơ chế cơ học (rửa, gọt, thái, băm) |
| cook_minutes | integer | NN, CHECK `>= 0` | Tổng thời gian chế biến nhiệt trên bếp **cộng với thời gian ướp, ủ hoặc ninh/chờ bắt buộc** trong quy trình nấu ([ADR-009](../07-decisions/ADR-009-cooking-and-waiting-time.md)) |
| quality_score | numeric(4,3) | NN, DEFAULT 1.000, CHECK `0..1` | *(Mở rộng GĐ 2)* Điểm chất lượng nguồn & mức hoàn thiện $Q$ trong MCDA |
| cover_image_path | text | ? | Path ảnh hợp pháp trên Supabase Storage |
| source_name | text | ? | Tên nguồn/đơn vị cung cấp |
| source_url | text | ? | Liên kết tham khảo |
| content_license | text | ? | Giấy phép hoặc `original` |
| status | varchar(12) | NN, CHECK(`draft`/`published`/`archived`) | Trạng thái (`published` tương ứng $\text{Verified}(r) = 1$) |
| author_id | uuid | FK→`profiles.id`, NN | Admin tạo/duyệt |
| created_at | ts | NN, DEFAULT now() | Ngày tạo |
| updated_at | ts | NN, DEFAULT now() | Ngày cập nhật |

`total_minutes = prep_minutes + cook_minutes` là **thuộc tính tính toán ở API**, không tạo cột lưu trữ. Công thức ở trạng thái `published` bắt buộc có ít nhất 1 bước nấu, ít nhất 1 nguyên liệu bắt buộc thuộc nhóm chính (`category != 'pantry'`), mọi nguyên liệu trong món đều `is_active = true`, và không có bước đơn lẻ nào có `estimated_minutes > prep_minutes + cook_minutes` (`400 RECIPE_NOT_PUBLISHABLE`).

## 7. `recipe_ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| recipe_id | uuid | PK, FK→`recipes.id` (`ON DELETE CASCADE`) | Công thức |
| ingredient_id | uuid | PK, FK→`ingredients.id` (`ON DELETE RESTRICT`) | Nguyên liệu |
| is_required | boolean | NN, DEFAULT true | Nguyên liệu bắt buộc để xét `ready`/`missing` (MVP `v1.0`) và `READY`/`UNKNOWN`/`MISSING_CONFIRMED` (`v1.1`) |
| role | varchar(16) | NN, DEFAULT `'essential'`, CHECK(`primary`/`essential`/`secondary`) | *(Mở rộng GĐ 2)* Vai trò nguyên liệu trong món (chính / thiết yếu / phụ) phục vụ tiêu chí $G$ |
| weight | numeric(6,2) | NN, DEFAULT 1.00, CHECK `> 0` | *(Mở rộng GĐ 2)* Trọng số $w_{r,i}$ theo từng món cho Weighted Coverage (khi đồng nhất `1.00` sẽ suy biến về tỷ lệ phần tử của `v1.0`) |
| grams | numeric(8,2) | ?, CHECK `> 0` | *(Mở rộng GĐ 3)* Khối lượng ăn được ($m_i$, tính bằng gram) ứng với `base_servings` cho quy đổi khẩu phần & dinh dưỡng USDA |
| display_quantity | text | ? | Chuỗi hiển thị định lượng thân thiện (`2 quả`, `1 muỗng canh`) |
| scaling_note | text | ? | *(Mở rộng GĐ 3)* Lưu ý khi nhân khẩu phần không tuyến tính (gia vị/nhiệt/thời gian) |
| sort_order | integer | NN, DEFAULT 0 | Thứ tự hiển thị |

## 8. `recipe_steps`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã bước |
| recipe_id | uuid | FK→`recipes.id` (`ON DELETE CASCADE`), NN | Món |
| step_no | integer | NN, CHECK `>= 1`; UQ(`recipe_id`, `step_no`) | Thứ tự bước |
| instruction | text | NN | Nội dung hướng dẫn gốc có quyền sử dụng |
| estimated_minutes | integer | ?, CHECK `>= 0` | Thời gian ước tính của bước nếu có |

## 9. `nutrition_tags` (Nhãn định tính — Tầng 1 `P0`)

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
| ingredient_id | uuid | PK, FK→`ingredients.id` | Nguyên liệu |
| nutrition_tag_id | uuid | PK, FK→`nutrition_tags.id` | Nhóm chất |
| source_url | text | NN | Nguồn kiểm chứng |
| note | text | ? | Cách diễn giải có điều kiện |
| reviewed_at | ts | ? | Ngày nhóm kiểm duyệt |

Không ghi "giàu protein", "ít béo" khi không có căn cứ và tiêu chí định lượng; dùng diễn đạt trung lập "có chứa / nguồn tham khảo về ...".

## 11. `scan_sessions` (chỉ lưu nếu chủ động opt-in)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Lượt scan |
| user_id | uuid | FK→`profiles.id` (`ON DELETE CASCADE`), NN | Người đồng ý lưu (`save_history = true`) |
| model_id | uuid | FK→`ai_models.id`, NN | Model dùng trong phiên |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo |

Không có `image_path`: backend không lưu ảnh nguyên liệu gốc trong MVP. User có quyền xóa phiên; `scan_detections`, `scan_ingredients` và `recommendation_feedback.scan_session_id` đều dùng `ON DELETE CASCADE` (xem [ADR-012](../07-decisions/ADR-012-feedback-uniqueness-and-context.md)).

## 12. `scan_detections`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Dự đoán thô |
| scan_session_id | uuid | FK→`scan_sessions.id` (`ON DELETE CASCADE`), NN | Lượt scan |
| ai_label_id | uuid | FK→`ai_labels.id`, NN | Nhãn theo model version |
| confidence | numeric(4,3) | NN, CHECK `0..1` | Độ tin cậy |
| needs_confirmation | boolean | NN, DEFAULT false | *(Mở rộng GĐ 2)* Cờ cảnh báo $\text{confidence} < \tau$ trong luồng HITL |
| x1, y1, x2, y2 | numeric(6,5) | NN, CHECK `0..1`, `x1<x2`, `y1<y2` | Box chuẩn hóa `xyxy` (tính trên khung ảnh đã xoay chuẩn chiều EXIF) |

## 13. `scan_ingredients`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| scan_session_id | uuid | PK, FK→`scan_sessions.id` (`ON DELETE CASCADE`) | Lượt scan |
| ingredient_id | uuid | PK, FK→`ingredients.id` | ID nguyên liệu chính đã xác nhận (`category != 'pantry'`) |
| provenance | varchar(16) | NN, CHECK(`ai`/`clip_assisted`/`manual`/`corrected`) | Nguồn chọn cuối cùng (`ai/manual/corrected` ở MVP; `clip_assisted` khi bật nhánh phụ CLIP GĐ 4) |

Chỉ cập nhật sau khi user xác nhận và gửi `scan_id` hợp lệ qua `/recommendations`. Trạng thái bật/tắt gia vị `pantry` chỉ lưu trên client (`localStorage`/session), không lưu vào `scan_ingredients`.

## 14. `favorites`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| user_id | uuid | PK, FK→`profiles.id` (`ON DELETE CASCADE`) | Chủ sở hữu |
| recipe_id | uuid | PK, FK→`recipes.id` (`ON DELETE CASCADE`) | Món đã lưu |
| created_at | ts | NN, DEFAULT now() | Thời điểm lưu |

## 15. `recommendation_feedback`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã feedback |
| user_id | uuid | FK→`profiles.id` (`ON DELETE CASCADE`), NN | Người gửi |
| recipe_id | uuid | FK→`recipes.id` (`ON DELETE CASCADE`), NN | Món đánh giá |
| scan_session_id | uuid | FK→`scan_sessions.id` (`ON DELETE CASCADE`), ? | Gắn scan nếu có, phải cùng user (`404 SCAN_NOT_OWNED` nếu khác chủ) |
| rating | smallint | NN, CHECK `1..5` | Độ hữu ích của gợi ý, **không dùng thay thế mAP của model thị giác** |
| note | varchar(500) | ? | Ý kiến bổ sung |
| created_at | ts | NN, DEFAULT now() | Thời điểm tạo lần đầu |
| updated_at | ts | NN, DEFAULT now() | Thời điểm cập nhật gần nhất (khi upsert) |

Ràng buộc duy nhất: `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)` (yêu cầu PostgreSQL >= 15). Gửi lần đầu trong một ngữ cảnh tạo bản ghi mới (`201 Created`); gửi lại trong cùng `(user_id, recipe_id, scan_session_id)` cập nhật `rating`, `note`, `updated_at` (`200 OK`). Khi thống kê toàn hệ thống hoặc huấn luyện mô hình cá nhân hóa Logistic Regression (Thành phần 08), lấy bản ghi có `updated_at` mới nhất cho mỗi `(user_id, recipe_id)`.

## 16. `audit_logs`

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PK | Mã nhật ký |
| actor_id | uuid | FK→`profiles.id`, NN | Admin thao tác |
| action | text | NN | `create`/`update`/`publish`/`archive`/`remap`... |
| entity_type | text | NN | `recipes`/`ingredients`/`ai_models`/`ai_labels`/`nutrition_tags` |
| entity_id | uuid | NN | ID bản ghi thay đổi |
| before_json | jsonb | ? | Giá trị trước (đã loại bí mật/PII) |
| after_json | jsonb | ? | Giá trị sau (đã loại bí mật/PII) |
| created_at | ts | NN, DEFAULT now() | Thời điểm ghi |

## 17. Các bảng mở rộng Giai đoạn 2–4 (`Scoring v1.1` & Dinh dưỡng Tầng 2)

### 17.1. `allergens` và `ingredient_allergens` (Giai đoạn 2 — Kiểm tra $\text{DietOK}$)

| Bảng | Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|---|
| `allergens` | id | uuid | PK | Mã tác nhân dị ứng |
| `allergens` | code | varchar(30) | UQ, NN | `egg`, `milk`, `peanut`, `tree_nut`, `shellfish`, `fish`, `soy`, `wheat_gluten`... |
| `allergens` | name_vi | text | NN | Tên hiển thị tiếng Việt (`Trứng`, `Hải sản có vỏ`...) |
| `ingredient_allergens` | ingredient_id | uuid | PK, FK→`ingredients.id` (`ON DELETE CASCADE`) | Nguyên liệu mang tác nhân dị ứng |
| `ingredient_allergens` | allergen_id | uuid | PK, FK→`allergens.id` (`ON DELETE RESTRICT`) | Tác nhân dị ứng đã xác minh |

*(Có thể tạo SQL View `recipe_allergens` nối `recipe_ingredients` $\bowtie$ `ingredient_allergens` để truy vấn nhanh toàn bộ tác nhân dị ứng của mỗi món).*

### 17.2. `ingredient_nutrients` (Giai đoạn 3 — Dinh dưỡng Tầng 2 USDA `P1`)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| ingredient_id | uuid | PK, FK→`ingredients.id` (`ON DELETE CASCADE`) | Nguyên liệu chuẩn |
| kcal_100g | numeric(7,2) | NN, CHECK `>= 0` | Năng lượng (`kcal`) trên $100\text{ g}$ phần ăn được |
| protein_100g | numeric(6,2) | NN, CHECK `>= 0` | Protein (`g`) trên $100\text{ g}$ |
| fat_100g | numeric(6,2) | NN, CHECK `>= 0` | Lipid (`g`) trên $100\text{ g}$ |
| carb_100g | numeric(6,2) | NN, CHECK `>= 0` | Carbohydrate (`g`) trên $100\text{ g}$ |
| source_url | text | NN | Đường dẫn bản ghi USDA FoodData Central hoặc bảng thành phần chuẩn |
| reviewed_at | ts | ? | Thời điểm kiểm duyệt ánh xạ |

### 17.3. `user_preferences` (Giai đoạn 2 & 4 — Ràng buộc bếp/dị ứng & Logistic Regression)

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| user_id | uuid | PK, FK→`profiles.id` (`ON DELETE CASCADE`) | Chủ hồ sơ |
| excluded_allergen_ids | jsonb | NN, DEFAULT `'[]'` | Danh sách UUID tác nhân dị ứng cần lọc cứng (`BLOCKED`) |
| available_equipment | jsonb | ? | Thiết bị bếp hiện có (`null` = không giới hạn) |
| lr_weights | jsonb | ? | Vector tham số $\theta_u$ của mô hình Logistic Regression cá nhân hóa (Thành phần 08) |
| feedback_count | integer | NN, DEFAULT 0, CHECK `>= 0` | Số phản hồi hợp lệ để điều chỉnh hệ số $\lambda_{\text{pers}}$ (Cold-start) |
| lr_model_version | text | ? | Phiên bản cấu trúc đặc trưng $x_r$ đang áp dụng |
| updated_at | ts | NN, DEFAULT now() | Thời điểm cập nhật gần nhất |

## 18. Checklist migration

- [ ] Xác nhận phiên bản PostgreSQL trên dự án Supabase là **>= 15** (bắt buộc cho `UNIQUE NULLS NOT DISTINCT` trên `recommendation_feedback`).
- [ ] Kích hoạt extension `unaccent` và `pg_trgm` trước khi tạo bảng/chỉ mục GIN `idx_alias_trgm` trên `ingredient_aliases`.
- [ ] Tạo bảng theo thứ tự FK, thêm `ON DELETE` phù hợp chính sách xóa dữ liệu (`ON DELETE CASCADE` cho `scan_detections`, `scan_ingredients`, `recommendation_feedback.scan_session_id`, `favorites`, `user_preferences`; `ON DELETE RESTRICT` cho `recipe_ingredients.ingredient_id` và `ai_labels.ingredient_id`).
- [ ] Khai báo ENUM/CHECK (`ingredients.category IN ('vegetable', 'protein', 'seafood', 'spice', 'pantry', 'other')`), UNIQUE/INDEX và trigger `updated_at` cho `recipes`, `recommendation_feedback` và `user_preferences`.
- [ ] Kích hoạt RLS, REVOKE quyền thừa, cấp đúng GRANT cho tất cả các bảng trong schema exposed (kể cả các bảng mở rộng `allergens`, `ingredient_allergens`, `ingredient_nutrients`, `user_preferences`).
- [ ] Kiểm thử quyền truy cập cho `anon`, `user A`, `user B`, `admin` và `service_role`; không dựa vào kiểm tra UI.
- [ ] Seed bộ nguyên liệu, alias tiếng Việt (`đậu hũ`/`đậu phụ`...), nhãn dinh dưỡng định tính có nguồn (tách rõ nhóm `spice` như tỏi, ớt, gừng và nhóm `pantry` như muối, đường, nước mắm, dầu ăn, tiêu xay, nước tương, giấm, hạt nêm...; không tạo bản ghi cho nước lọc).
- [ ] Tạo test cho trạng thái `published` (đủ bước, đủ nguyên liệu chính bắt buộc ngoài `pantry`, mọi nguyên liệu `is_active = true`, không có bước đơn lẻ vượt `total_minutes`) và test chặn `INGREDIENT_IN_USE`.
