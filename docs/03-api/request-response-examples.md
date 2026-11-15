# Ví dụ API — dữ liệu mô phỏng theo hợp đồng & bài toán xuyên suốt (`1.1.0`)

> Các UUID, tên món và điểm số bên dưới là **ví dụ hợp đồng** (khớp 100% với [`openapi.yaml`](./openapi.yaml) và công thức MCDA 4 tiêu chí hợp nhất trong [`recommendation-design.md`](../05-recommendation/recommendation-design.md)). Khi seed dữ liệu thực, dùng ID thật; không đưa ví dụ này vào báo cáo dưới dạng kết quả thử nghiệm thực tế.

## 1. Upload ảnh nhận diện (`POST /api/v1/ai/detect`)

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
      "ingredient_id": "11111111-1111-4111-8111-111111111101",
      "ingredient_name": "Cà chua",
      "confidence": 0.92,
      "needs_confirmation": false,
      "bbox": {"x1": 0.1, "y1": 0.12, "x2": 0.42, "y2": 0.58}
    },
    {
      "class_index": 2,
      "class_name": "tofu",
      "ingredient_id": "11111111-1111-4111-8111-111111111103",
      "ingredient_name": "Đậu hũ",
      "confidence": 0.58,
      "needs_confirmation": true,
      "bbox": {"x1": 0.52, "y1": 0.25, "x2": 0.81, "y2": 0.68}
    }
  ],
  "suggested_ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111101", "name_vi": "Cà chua", "max_confidence": 0.92},
    {"ingredient_id": "11111111-1111-4111-8111-111111111103", "name_vi": "Đậu hũ", "max_confidence": 0.58}
  ],
  "clear_ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111101", "name_vi": "Cà chua", "max_confidence": 0.92}
  ],
  "uncertain_ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111103", "name_vi": "Đậu hũ", "max_confidence": 0.58}
  ]
}
```

- `clear_ingredients`: nguyên liệu rõ (`max_confidence >= 0.80`), tự động tích sẵn.
- `uncertain_ingredients`: nguyên liệu không rõ (`max_confidence < 0.80`), cần người dùng xác nhận trên giao diện HITL trước khi đưa vào `ingredient_ids`.

## 2. Gợi ý món từ danh sách đã xác nhận (`POST /api/v1/recommendations`)

### 2.1. Trường hợp mặc định (Bỏ qua chọn nguyên liệu chính, mặc định `desired_hours = 100.0`, Guest trung lập `P = 0.5`)

```http
POST /api/v1/recommendations
Content-Type: application/json
```

```json
{
  "ingredient_ids": [
    "11111111-1111-4111-8111-111111111101",
    "11111111-1111-4111-8111-111111111102"
  ],
  "main_ingredient_ids": [],
  "desired_hours": 100.0,
  "allergic_ingredient_ids": [],
  "kitchen_spice_ids": null,
  "excluded_pantry_ids": [],
  "favorite_ingredient_ids": [],
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
        "id": "22222222-2222-4222-8222-222222222204",
        "name_vi": "Trứng xào cà chua",
        "slug": "trung-xao-ca-chua",
        "cuisine_code": "VN",
        "prep_minutes": 5,
        "cook_minutes": 10,
        "total_minutes": 15,
        "cover_image_url": null
      },
      "availability": "ready",
      "reasoning_status": "READY",
      "score": 95.0,
      "matched_ingredient_ids": [
        "11111111-1111-4111-8111-111111111101",
        "11111111-1111-4111-8111-111111111102"
      ],
      "missing_required_ingredient_ids": [],
      "missing_optional_ingredient_ids": ["11111111-1111-4111-8111-111111111105"],
      "score_breakdown": {"C": 1.0, "G": 1.0, "T": 1.0, "P": 0.5},
      "score_contributions": {"C": 50.0, "G": 25.0, "T": 15.0, "P": 5.0},
      "explanation_vi": "Đủ nguyên liệu bắt buộc để nấu ngay (Cà chua, Trứng gà); thời gian hoàn thành 15 phút."
    }
  ],
  "total": 1,
  "limit": 20
}
```

- Điểm **95.0** khớp công thức $S = 100 \times (0.50\,C + 0.25\,G + 0.15\,T + 0.10\,P)$ với `C=1.0, G=1.0, T=1.0, P=0.5`.
- Nếu người dùng tắt gia vị bắt buộc "Nước mắm" (`excluded_pantry_ids: ["11111111-1111-4111-8111-111111111107"]`), trọng số khớp giảm còn `9/10` (`C = 0.9`), điểm giảm xuống **90.0** và chuyển sang `availability: "missing"` (`reasoning_status: "MISSING_CONFIRMED"`).

### 2.2. Trường hợp có chọn nguyên liệu chính (`0.7 / 0.3`), thời gian mong muốn `0.25h` và sở thích `favorite_ingredient_ids`

Với món **"Đậu hũ sốt cà chua"** (`total_minutes = 30` $\implies t_r = 0.50\text{h}$, `Đậu hũ` là `core/main` $w=4$, `Cà chua` là `secondary/sub` $w=2$, `Muối` $w=1$, `Dầu ăn` $w=1$), khi gửi `ingredient_ids = [dau_hu, ca_chua]`, `main_ingredient_ids = [dau_hu]`, `desired_hours = 0.25`, `favorite_ingredient_ids = [dau_hu, thit_ba_chi]`:
- `score_breakdown = {"C": 1.0, "G": 0.85, "T": 0.5, "P": 0.5}`
- `score_contributions = {"C": 50.0, "G": 21.25, "T": 7.5, "P": 5.0}` $\implies$ `score = 83.75`.

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
  "cook_minutes": 10,
  "source_name": "Công thức tự biên soạn — cần nhóm xác nhận",
  "content_license": "original",
  "ingredients": [
    {"ingredient_id": "11111111-1111-4111-8111-111111111101", "is_required": true, "display_quantity": "2 quả", "sort_order": 1},
    {"ingredient_id": "11111111-1111-4111-8111-111111111102", "is_required": true, "display_quantity": "2 quả", "sort_order": 2},
    {"ingredient_id": "11111111-1111-4111-8111-111111111107", "is_required": true, "display_quantity": "1 muỗng canh", "sort_order": 3}
  ],
  "steps": [
    {"step_no": 1, "instruction": "Sơ chế và cắt cà chua.", "estimated_minutes": 5},
    {"step_no": 2, "instruction": "Chế biến trứng và cà chua đến khi chín.", "estimated_minutes": 10}
  ]
}
```

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
