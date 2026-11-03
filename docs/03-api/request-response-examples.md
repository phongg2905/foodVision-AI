# Ví dụ API — dữ liệu mô phỏng theo hợp đồng & bài toán xuyên suốt

> Các UUID, tên món và điểm số bên dưới là **ví dụ hợp đồng** (khớp 100% với [`openapi.yaml`](./openapi.yaml) ở cấu hình cốt lõi `Scoring v1.0`, kèm ví dụ mở rộng `Scoring v1.1` cho lộ trình Giai đoạn 2–5). Khi seed dữ liệu thực, dùng ID thật; không đưa ví dụ này vào báo cáo dưới dạng kết quả thử nghiệm thực tế.

## 1. Upload ảnh nhận diện (`POST /api/v1/ai/detect`)

### 1.1. Hợp đồng cốt lõi MVP (`v1.0` — khớp `openapi.yaml`)

```http
POST /api/v1/ai/detect
Content-Type: multipart/form-data

file=<binary image/jpeg>
save_history=false
```

```json
{
  "scan_id": null,
  "model_version": "food-yolo-v1",
  "detections": [
    {
      "class_index": 0,
      "class_name": "tomato",
      "ingredient_id": "11111111-1111-4111-8111-111111111111",
      "ingredient_name": "Cà chua",
      "confidence": 0.92,
      "bbox": {"x1": 0.1, "y1": 0.12, "x2": 0.42, "y2": 0.58}
    },
    {
      "class_index": 1,
      "class_name": "egg",
      "ingredient_id": "22222222-2222-4222-8222-222222222222",
      "ingredient_name": "Trứng gà",
      "confidence": 0.88,
      "bbox": {"x1": 0.5, "y1": 0.2, "x2": 0.8, "y2": 0.7}
    }
  ],
  "suggested_ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111111", "name_vi": "Cà chua", "max_confidence": 0.92},
    {"ingredient_id": "22222222-2222-4222-8222-222222222222", "name_vi": "Trứng gà", "max_confidence": 0.88}
  ]
}
```

BBox `x1,y1,x2,y2` theo tỷ lệ `[0,1]` tính trên ảnh đã xoay chuẩn chiều hiển thị theo EXIF Orientation (metadata EXIF/GPS đã bị loại bỏ). Có thể có nhiều detection trùng loại nguyên liệu; `suggested_ingredients` đã khử trùng lặp theo `ingredient_id` (chỉ gồm nguyên liệu chính `category != 'pantry'`).

### 1.2. Mở rộng Giai đoạn 2 & 4 (Cờ HITL `needs_confirmation` & ứng viên CLIP tùy chọn)

Khi bật ngưỡng cảnh báo xác nhận HITL ($\tau = 0.80$, Thành phần 14) và nhánh phụ tùy chọn CLIP (Thành phần 02) cho phát hiện độ tin cậy thấp (`0.58 < 0.80`):

```json
{
  "class_index": 11,
  "class_name": "tofu",
  "ingredient_id": "66666666-6666-4666-8666-666666666666",
  "ingredient_name": "Đậu hũ",
  "confidence": 0.58,
  "needs_confirmation": true,
  "candidates": [
    {"ingredient_id": "66666666-6666-4666-8666-666666666666", "name_vi": "Đậu hũ", "similarity": 0.975}
  ],
  "bbox": {"x1": 0.52, "y1": 0.25, "x2": 0.81, "y2": 0.68}
}
```

## 2. Gợi ý món từ danh sách **đã xác nhận** (`POST /api/v1/recommendations`)

### 2.1. Hợp đồng cốt lõi MVP (`Scoring v1.0` — khớp `openapi.yaml`)

```http
POST /api/v1/recommendations
Content-Type: application/json
```

```json
{
  "ingredient_ids": [
    "11111111-1111-4111-8111-111111111111",
    "22222222-2222-4222-8222-222222222222"
  ],
  "excluded_pantry_ids": [],
  "max_total_minutes": 15,
  "cuisine_codes": ["VN"],
  "preferred_cuisine_codes": [],
  "include_missing": true,
  "limit": 20,
  "scan_id": null
}
```

```json
{
  "items": [
    {
      "recipe": {
        "id": "33333333-3333-4333-8333-333333333333",
        "name_vi": "Trứng xào cà chua",
        "slug": "trung-xao-ca-chua",
        "cuisine_code": "VN",
        "prep_minutes": 5,
        "cook_minutes": 8,
        "total_minutes": 13,
        "cover_image_url": null
      },
      "availability": "ready",
      "score": 89.0,
      "matched_ingredient_ids": [
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222"
      ],
      "missing_required_ingredient_ids": [],
      "missing_optional_ingredient_ids": ["44444444-4444-4444-8444-444444444444"],
      "score_breakdown": {"C": 0.8, "E": 1.0, "T": 1.0, "P": 1.0},
      "explanation_vi": "Đủ nguyên liệu bắt buộc; thiếu hành lá (tùy chọn)."
    }
  ],
  "total": 1,
  "limit": 20
}
```

Điểm **89.0** là ví dụ tính đúng theo công thức `Scoring v1.0` (`C=0.8, E=1, T=1, P=1`, trọng số `(0.55, 0.25, 0.10, 0.10)`) khi `excluded_pantry_ids = []`. Nếu người dùng bỏ chọn gia vị bắt buộc "Nước mắm" (`"excluded_pantry_ids": ["55555555-5555-4555-8555-555555555555"]`), món chuyển sang `availability: "missing"`, `missing_required_ingredient_ids: ["55555555-5555-4555-8555-555555555555"]`, `E = 2/3 ≈ 0.667`, `C = 2/3.5 ≈ 0.571`, `score = 68.1`.

### 2.2. Chi tiết công thức kèm phân loại gia vị nền (`GET /api/v1/recipes/{recipe_id}`)

Trong `RecipeDetail.ingredients`, mỗi phần tử `RecipeIngredientView` có trường `category` để giao diện tách riêng nhóm nguyên liệu chính và nhóm "Gia vị cần chuẩn bị" (`category = 'pantry'`):

```json
{
  "ingredient_id": "55555555-5555-4555-8555-555555555555",
  "name_vi": "Nước mắm",
  "category": "pantry",
  "is_required": true,
  "display_quantity": "1 muỗng canh",
  "sort_order": 3
}
```

### 2.3. Mở rộng Giai đoạn 2–5 (`Scoring v1.1` — Suy luận 3 trạng thái, Trọng số & MCDA XAI)

Khi nâng cấp lên cấu hình `Scoring v1.1` (cập nhật đồng bộ `openapi.yaml` theo `NFR-10`), trường hợp người dùng xác nhận có **Cà chua** ($w=4$), **Dầu ăn** ($w=1$), **Muối** ($w=1$) nhưng chưa khai báo **Trứng gà** ($w=3$, trạng thái `unknown`):

```json
{
  "availability": "unknown",
  "score": 80.83,
  "unknown_required_ingredient_ids": ["22222222-2222-4222-8222-222222222222"],
  "missing_required_ingredient_ids": [],
  "score_breakdown": {
    "features": {"C": 0.6667, "G": 1.0, "T": 1.0, "P": 0.5, "Q": 1.0},
    "contributions": {"C": 33.33, "G": 25.00, "T": 15.00, "P": 2.50, "Q": 5.00},
    "personalization_lambda": 0.0
  },
  "explanation_vi": "Độ phủ nguyên liệu theo trọng số đạt 66.7% (cà chua là nguyên liệu chính, nấu <= 15 phút); chưa xác nhận có trứng gà nên chưa gắn nhãn Nấu ngay."
}
```

Điểm **80.83** khớp tuyệt đối tổng đóng góp tuyến tính 5 tiêu chí MCDA: `33.33 + 25.00 + 15.00 + 2.50 + 5.00 = 80.83`. Nếu người dùng xác nhận có thêm Trứng gà (`C = 1.0`), món chuyển sang `availability: "ready"` và điểm tăng lên **97.50**.

## 3. API lỗi mẫu

```json
{
  "code": "IMAGE_TOO_LARGE",
  "message": "Ảnh vượt quá dung lượng 5 MB.",
  "details": {"max_bytes": 5242880},
  "request_id": "req_example_002"
}
```

## 4. Tạo công thức ở trạng thái draft (Admin — `POST /api/v1/admin/recipes`)

```http
POST /api/v1/admin/recipes
Authorization: Bearer <Supabase access token của Admin>
Content-Type: application/json
```

```json
{
  "slug": "trung-xao-ca-chua",
  "name_vi": "Trứng xào cà chua",
  "description": "Món ăn gia đình dùng nguyên liệu cơ bản.",
  "cuisine_code": "VN",
  "prep_minutes": 5,
  "cook_minutes": 8,
  "source_name": "Công thức tự biên soạn — cần nhóm xác nhận",
  "content_license": "original",
  "ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111111", "is_required": true, "display_quantity": "2 quả", "sort_order": 1},
    {"ingredient_id": "22222222-2222-4222-8222-222222222222", "is_required": true, "display_quantity": "2 quả", "sort_order": 2},
    {"ingredient_id": "55555555-5555-4555-8555-555555555555", "is_required": true, "display_quantity": "1 muỗng canh", "sort_order": 3}
  ],
  "steps": [
    {"step_no": 1, "instruction": "Sơ chế và cắt cà chua.", "estimated_minutes": 5},
    {"step_no": 2, "instruction": "Chế biến trứng và cà chua đến khi chín.", "estimated_minutes": 8}
  ]
}
```

Response dự kiến `HTTP 201` chứa đối tượng recipe ở trạng thái `draft` (ở Giai đoạn 2–3, mỗi phần tử `ingredients` có thể khai báo thêm `role`, `weight` và `grams` để phục vụ `Scoring v1.1` và quy đổi khẩu phần/dinh dưỡng USDA). Đổi sang `published` qua `PATCH /api/v1/admin/recipes/{id}/status` khi backend kiểm tra đủ thành phần bắt buộc (`>= 1` nguyên liệu bắt buộc `category != 'pantry'`, mọi nguyên liệu `is_active = true`) và bước hướng dẫn (`>= 1` bước, không có bước đơn lẻ nào có `estimated_minutes > prep_minutes + cook_minutes`). Các bất biến này cũng được kiểm tra khi `PATCH /api/v1/admin/recipes/{id}` trên một công thức đang `published`.

## 5. Mã lỗi nghiệp vụ chuẩn hóa (20 mã)

Chi tiết schema `details` của từng mã lỗi xem tại [`api-conventions.md`](./api-conventions.md#danh-mục-20-mã-lỗi-nghiệp-vụ-chuẩn-và-cấu-trúc-details):

1. `IMAGE_TOO_LARGE` (`413`)
2. `UNSUPPORTED_IMAGE_TYPE` (`415`)
3. `INVALID_IMAGE` (`422`)
4. `INVALID_INGREDIENTS` (`422`)
5. `RECIPE_NOT_PUBLISHABLE` (`400`)
6. `UNAUTHORIZED` (`401`)
7. `FORBIDDEN` (`403`)
8. `SCAN_NOT_OWNED` (`404`)
9. `RECIPE_NOT_FOUND` (`404`)
10. `DUPLICATE_SLUG` (`409`)
11. `RATE_LIMITED` (`429`)
12. `INTERNAL_ERROR` (`500`)
13. `MODEL_NOT_READY` (`503`)
14. `INVALID_QUERY_PARAMS` (`422`)
15. `VALIDATION_ERROR` (`422`)
16. `INGREDIENT_IN_USE` (`400`)
17. `MODEL_NOT_ACTIVATABLE` (`400`)
18. `MODEL_IMMUTABLE` (`400`)
19. `INVALID_LABEL_MAPPING` (`400`)
20. `INFERENCE_TIMEOUT` (`504`)
