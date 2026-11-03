# Ví dụ API — dữ liệu mô phỏng, chưa có server/DB chạy

> Các UUID, tên món và điểm số bên dưới là **ví dụ hợp đồng**. Khi seed dữ liệu thực, dùng ID thật; không đưa ví dụ này vào báo cáo dưới dạng kết quả thử nghiệm.

## 1. Upload ảnh nhận diện

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

BBox `x1,y1,x2,y2` theo tỷ lệ [0,1]. Có thể có nhiều detection trùng loại nguyên liệu; `suggested_ingredients` đã khử trùng lặp theo ingredient ID.

## 2. Gợi ý từ danh sách **đã xác nhận**

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

Điểm **89.0** là ví dụ tính đúng theo công thức giả định C=0.8, E=1, T=1, P=1, trọng số (0.55,0.25,0.10,0.10). Không phải giá trị của AI học máy.

## 3. API lỗi mẫu

```json
{
  "code": "IMAGE_TOO_LARGE",
  "message": "Ảnh vượt quá dung lượng 5 MB.",
  "details": {"max_bytes": 5242880},
  "request_id": "req_example_002"
}
```

## 4. Tạo công thức ở trạng thái draft (Admin)

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
    {"ingredient_id": "22222222-2222-4222-8222-222222222222", "is_required": true, "display_quantity": "2 quả", "sort_order": 2}
  ],
  "steps": [
    {"step_no": 1, "instruction": "Sơ chế và cắt cà chua.", "estimated_minutes": 5},
    {"step_no": 2, "instruction": "Chế biến trứng và cà chua đến khi chín.", "estimated_minutes": 8}
  ]
}
```

Response dự kiến HTTP 201 chứa đối tượng recipe ở trạng thái `draft`. Đổi sang `published` qua `PATCH /api/v1/admin/recipes/{id}/status` khi backend kiểm tra đủ thành phần bắt buộc và bước hướng dẫn.

## 5. Mã lỗi nghiệp vụ đề xuất

`IMAGE_TOO_LARGE`, `UNSUPPORTED_IMAGE_TYPE`, `INVALID_IMAGE`, `MODEL_NOT_READY`, `INVALID_INGREDIENTS`, `SCAN_NOT_OWNED`, `RECIPE_NOT_FOUND`, `RECIPE_NOT_PUBLISHABLE`, `DUPLICATE_SLUG`, `UNAUTHORIZED`, `FORBIDDEN`, `RATE_LIMITED`, `INTERNAL_ERROR`.
