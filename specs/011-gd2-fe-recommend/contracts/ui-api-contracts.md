# UI <-> API Contracts (GĐ2 - Thẻ #11, `v1.1.0`)

Khớp 100% với [`docs/03-api/openapi.yaml`](../../../docs/03-api/openapi.yaml) và `backend/app/schemas/` (đều bật `ConfigDict(extra="forbid")`).

---

## 1. `POST /api/v1/recommendations`

### Request Body (`RecommendRequest`)

- `ingredient_ids`: `string[]` (bắt buộc, ít nhất 1 UUID duy nhất, `category !== 'pantry'`)
- `main_ingredient_ids`: `string[]` (mặc định `[]`; mọi phần tử phải là tập con của `ingredient_ids`)
- `desired_hours`: `number` (mặc định `100.0`; `> 0`)
- `excluded_pantry_ids`: `string[]` (mặc định `[]`; chỉ chứa UUID có `category === 'pantry'`)
- `cuisine_codes`: `('VN' | 'EU' | 'US')[]` (mặc định `[]`)
- `max_total_minutes`: `number | null` (mặc định `null`, trong khoảng `1..720`)
- `include_missing`: `boolean` (mặc định `true`; đặt `false` khi bật *"Chỉ hiện món nấu được ngay"*)
- `diversify`: `boolean` (mặc định `false`; đặt `true` khi bật *"Đa dạng hóa thực đơn (MMR)"*)
- `limit`: `number` (mặc định `20`, trong khoảng `1..50`)
- `scan_id`: `string | null` (chỉ gửi khi khác `undefined`)
- `allergic_ingredient_ids`, `kitchen_spice_ids`, `favorite_ingredient_ids`: **KHÔNG gửi** nếu UI Guest chưa chỉnh sửa để Backend tự nạp `user_preferences` qua `model_fields_set` khi User đã đăng nhập.

### Response (`200 OK` — `RecommendResponse`)

```json
{
  "items": [
    {
      "recipe": {
        "id": "uuid",
        "slug": "dau-hu-sot-ca-chua",
        "name_vi": "Đậu hũ sốt cà chua",
        "cuisine_code": "VN",
        "prep_minutes": 10,
        "cook_minutes": 15,
        "total_minutes": 25,
        "cover_image_url": "https://..."
      },
      "availability": "ready",
      "reasoning_status": "READY",
      "score": 83.75,
      "matched_ingredient_ids": ["..."],
      "missing_required_ingredient_ids": [],
      "missing_optional_ingredient_ids": [],
      "score_breakdown": { "C": 1.0, "G": 0.85, "T": 0.5, "P": 0.5 },
      "score_contributions": { "C": 50.0, "G": 21.25, "T": 7.5, "P": 5.0 },
      "explanation_vi": "..."
    }
  ],
  "total": 1,
  "limit": 20
}
```

### Error Responses

- `422 INVALID_INGREDIENTS` / `422 VALIDATION_ERROR`: Không nuốt lỗi ở fallback; hiển thị thông báo tiếng Việt từ server.

---

## 2. `GET /api/v1/recipes/{recipe_id}`

### Path Parameters

- `recipe_id`: UUID công thức (`published`).

### Response (`200 OK` — `RecipeDetail`)

- `id`, `slug`, `name_vi`, `cuisine_code`, `prep_minutes`, `cook_minutes`, `total_minutes`, `cover_image_url`
- `description`: `string | null`
- `country_code`: `string | null`
- `ingredients`: `Array<{ ingredient_id, name_vi, category, is_required, display_quantity, sort_order }>`
- `steps`: `Array<{ step_no, instruction, estimated_minutes }>`
- `nutrition_evidence`: `Array<{ tag: { id, code, name_vi, description, is_active }, source_urls: string[], note: string | null }>`
- `source_name`, `source_url`, `content_license`: `string | null`

### Error Responses

- `404 RECIPE_NOT_FOUND`: Trả về khi công thức không tồn tại hoặc đang ở trạng thái `draft`.
