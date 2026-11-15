# UI ↔ API Contracts: [GĐ1 - UI] Recipe Catalog, Ingredient Search & 5-Pantry Bar

**Feature Branch**: `feat/018-gd1-fe-ui`  
**Date**: 2026-04-11  
**Contract Reference**: [`docs/03-api/openapi.yaml`](../../../docs/03-api/openapi.yaml) (`v0.9.1-draft`)

---

## 1. Tra cứu Danh mục Công thức (`FR-01`, `AC-01`, `AC-02`)

### Endpoint
`GET /api/v1/recipes`

### Query Parameters Sent by Frontend (`features/recipes`)

| Tham số | Kiểu | Bắt buộc | Ràng buộc | Mô tả sử dụng trên UI |
|---|---|---|---|---|
| `q` | `string` | Không | `maxLength: 100` | Từ khóa tìm kiếm tên món ăn tiếng Việt (có dấu hoặc không dấu). Chỉ gửi khi chuỗi sau khi `.trim()` khác rỗng. |
| `cuisine_code` | `'VN' \| 'EU' \| 'US'` | Không | Enum | Chỉ gửi khi người dùng chọn tab/chip ẩm thực cụ thể (`Món Việt`, `Món Âu`, `Món Mỹ`). Bỏ qua khi chọn `Tất cả`. |
| `max_total_minutes` | `integer` | Không | `1..720` | Chỉ gửi khi người dùng chọn mốc thời gian (`15`, `30`, `60` phút). Bỏ qua khi chọn `Tất cả`. |
| `limit` | `integer` | Không | `1..50` (mặc định `12`) | Số lượng thẻ món ăn hiển thị trên mỗi trang. |
| `offset` | `integer` | Không | `>= 0` (mặc định `0`) | Vị trí bắt đầu phân trang (`(page - 1) * limit`). Reset về `0` mỗi khi `q`, `cuisine_code`, hoặc `max_total_minutes` thay đổi. |

### Response `200 OK` (`PagedRecipes`)

```json
{
  "items": [
    {
      "id": "a1111111-1111-4111-8111-000000000001",
      "slug": "canh-ca-chua-trung",
      "name_vi": "Canh cà chua trứng",
      "cuisine_code": "VN",
      "prep_minutes": 5,
      "cook_minutes": 10,
      "total_minutes": 15,
      "cover_image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=800&q=80"
    }
  ],
  "total": 1,
  "limit": 12,
  "offset": 0
}
```

---

## 2. Tìm kiếm Nguyên liệu Chính Thủ công (`FR-18`, `AC-07`)

### Endpoint
`GET /api/v1/ingredients`

### Query Parameters Sent by Frontend (`features/search` - Main Ingredient Combobox)

| Tham số | Kiểu | Giá trị gửi từ UI | Ghi chú hợp đồng |
|---|---|---|---|
| `q` | `string` | Từ khóa người dùng nhập (ví dụ: `"đậu phụ"`, `"dau hu"`, `"ngô"`) | Hỗ trợ khớp tên chính, không dấu và từ đồng nghĩa vùng miền. |
| `exclude_pantry` | `boolean` | `true` | Luôn gửi `exclude_pantry=true` để loại trừ 5 gia vị cơ bản khỏi ô tìm kiếm nguyên liệu chính. **Tuyệt đối không gửi kèm `category=pantry`**. |
| `limit` | `integer` | `20` | Giới hạn danh sách gợi ý dropdown. |
| `offset` | `integer` | `0` | Mặc định trang đầu tiên. |

### Response `200 OK` (`PagedIngredients`)

```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-000000000001",
      "slug": "dau-hu",
      "name_vi": "Đậu hũ",
      "category": "protein",
      "is_active": true
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## 3. Tải Danh sách 5 Gia vị Sẵn có trong Bếp (`FR-05`, `ADR-008`)

### Endpoint
`GET /api/v1/ingredients?category=pantry&limit=10&offset=0`

### Query Parameters Sent by Frontend (`features/search` - Pantry Toggle Bar)

| Tham số | Kiểu | Giá trị gửi từ UI | Ghi chú hợp đồng |
|---|---|---|---|
| `category` | `string` | `'pantry'` | Lấy đúng 5 gia vị cơ bản (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*). **Không gửi `exclude_pantry=true`** để tránh lỗi `422 INVALID_QUERY_PARAMS`. |
| `limit` | `integer` | `10` | Đủ chứa toàn bộ 5 gia vị pantry. |
| `offset` | `integer` | `0` | Mặc định `0`. |

### Response `200 OK` (`PagedIngredients`)

```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-000000000001",
      "slug": "muoi",
      "name_vi": "Muối",
      "category": "pantry",
      "is_active": true
    },
    {
      "id": "22222222-2222-4222-8222-000000000002",
      "slug": "duong",
      "name_vi": "Đường",
      "category": "pantry",
      "is_active": true
    },
    {
      "id": "22222222-2222-4222-8222-000000000003",
      "slug": "nuoc-mam",
      "name_vi": "Nước mắm",
      "category": "pantry",
      "is_active": true
    },
    {
      "id": "22222222-2222-4222-8222-000000000004",
      "slug": "dau-an",
      "name_vi": "Dầu ăn",
      "category": "pantry",
      "is_active": true
    },
    {
      "id": "22222222-2222-4222-8222-000000000005",
      "slug": "hat-tieu",
      "name_vi": "Hạt tiêu",
      "category": "pantry",
      "is_active": true
    }
  ],
  "total": 5,
  "limit": 10,
  "offset": 0
}
```

---

## 4. Đầu ra Chuẩn bị cho Luồng Gợi ý Món ăn (`RecommendRequest` Draft Contract)

Khi người dùng đã chọn ít nhất 1 nguyên liệu chính (`ingredient_ids.length >= 1`) và nhấn nút **"Gợi ý món ăn"**, thành phần `features/search` tạo payload chuẩn khớp 100% với `POST /api/v1/recipes/recommend` (sẽ kết nối hiển thị xếp hạng ở Thẻ `#19`):

```json
{
  "ingredient_ids": [
    "11111111-1111-4111-8111-000000000001",
    "11111111-1111-4111-8111-000000000002"
  ],
  "excluded_pantry_ids": [
    "22222222-2222-4222-8222-000000000003"
  ]
}
```
