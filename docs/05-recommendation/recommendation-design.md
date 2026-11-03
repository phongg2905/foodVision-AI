# Thiết kế thuật toán gợi ý món ăn — Scoring v1

**Mã:** FV-REC-001 · **Phiên bản:** 1.0.0 (`0.9.0-draft`) · **Trạng thái:** Proposed, chưa hiệu chỉnh trên phản hồi thực tế.

## 1. Đầu vào và nguồn sự thật

Input là danh sách UUID nguyên liệu chính **do User đã xác nhận** (`ingredient_ids`, chỉ chứa nguyên liệu có `category != 'pantry'`, `minItems: 1`) và danh sách UUID gia vị nền mà người dùng báo đang thiếu (`excluded_pantry_ids`, mặc định `[]`, chỉ chứa nguyên liệu có `category = 'pantry'`). Mọi UUID được kiểm tra tồn tại, đang hoạt động (`is_active = true`) và đúng nhóm phân loại (`422 INVALID_INGREDIENTS` nếu sai nhóm hoặc không tồn tại); không dùng `confidence` YOLO làm độ tin cậy về việc *người dùng có thật nguyên liệu* sau xác nhận.

```json
{
  "ingredient_ids": ["...", "..."],
  "excluded_pantry_ids": [],
  "max_total_minutes": 15,
  "cuisine_codes": ["VN"],
  "preferred_cuisine_codes": [],
  "include_missing": true,
  "limit": 20,
  "scan_id": null
}
```

- `ingredient_ids`: danh sách nguyên liệu chính (`category != 'pantry'`) người dùng hiện có (`U`), tối thiểu 1 phần tử.
- `excluded_pantry_ids`: danh sách gia vị nền (`category = 'pantry'`) người dùng chủ động bỏ chọn vì đang hết trong bếp (`X`), mặc định `[]`.
- `cuisine_codes`: lọc **cứng** nhóm ẩm thực (rỗng = không lọc).
- `max_total_minutes`: lọc **cứng** `prep_minutes + cook_minutes <= limit` (`null` = không lọc).
- `preferred_cuisine_codes`: sở thích **mềm** để tính điểm `P` (rỗng = trung lập, `P = 1`).
- `include_missing=false`: chỉ trả nhóm đủ toàn bộ nguyên liệu bắt buộc (`availability = "ready"`).
- `scan_id`: chỉ để lưu danh sách nguyên liệu chính đã duyệt vào `scan_ingredients` khi user có consent (`save_history=true`); nếu `scan_id` không tồn tại hoặc thuộc người dùng khác sẽ trả `404 SCAN_NOT_OWNED`; **không ảnh hưởng điểm**.

## 2. Chuẩn hóa dữ liệu và quy tắc gia vị nền (`BR-04`, [ADR-008](../07-decisions/ADR-008-pantry-ingredients-handling.md))

- Gọi `Pantry` là tập toàn bộ nguyên liệu có `category = 'pantry'` trong hệ thống (gồm 5 gia vị nền: muối, đường, nước mắm, dầu ăn, tiêu xay; nước lọc sinh hoạt không tạo bản ghi trong bảng `ingredients`).
- Gọi `U = set(ingredient_ids)` là tập nguyên liệu chính người dùng có (`U ∩ Pantry = ∅`, `|U| >= 1`).
- Gọi `X = set(excluded_pantry_ids)` là tập gia vị nền người dùng báo đang thiếu (`X ⊆ Pantry`).
- Với mỗi công thức `r` đang ở trạng thái `published`:
  - `R_main = R_r \ Pantry`: tập nguyên liệu **chính bắt buộc** (`is_required = true`, `category != 'pantry'`). Ràng buộc xuất bản bắt buộc `|R_main| >= 1` (`BR-01`).
  - `O_main = O_r \ Pantry`: tập nguyên liệu **chính tùy chọn** (`is_required = false`, `category != 'pantry'`).
  - `R_pantry = R_r ∩ Pantry`: tập **gia vị nền bắt buộc** của công thức (`is_required = true`, `category = 'pantry'`).
  - `M_pantry = R_pantry ∩ X`: tập **gia vị nền bắt buộc mà người dùng đang thiếu** (do đã bỏ chọn trên giao diện).
  - Các gia vị nền tùy chọn (`O_r ∩ Pantry`) được loại trừ khỏi cả tử số và mẫu số chấm điểm để tránh làm phình điểm `C` giả tạo.
- **Điều kiện lọc ứng viên ban đầu:** Chỉ xét các công thức `published` có ít nhất một nguyên liệu chính (bắt buộc hoặc tùy chọn) khớp với `U`, tức là `|(R_main ∪ O_main) ∩ U| >= 1` (tương đương `C > 0`). Công thức không khớp bất kỳ nguyên liệu chính nào trong `U` bị loại ngay từ đầu, ngay cả khi người dùng có đủ toàn bộ gia vị nền trong bếp.

## 3. Công thức tính điểm

### 3.1. Độ phủ nguyên liệu bắt buộc `E`

```text
E(r, U, X) = |R_main ∩ U| / (|R_main| + |M_pantry|)
```

Vì công thức `published` luôn có `|R_main| >= 1` và `|M_pantry| >= 0`, mẫu số luôn `>= 1` (không bao giờ chia cho `0`). Khi người dùng không thiếu gia vị nền bắt buộc nào (`|M_pantry| = 0`), công thức rút gọn về `|R_main ∩ U| / |R_main|`.

### 3.2. Độ phủ nguyên liệu tổng hợp `C`

Trọng số hiện diện của nguyên liệu chính bắt buộc là `1.0`, của nguyên liệu chính tùy chọn là `0.5`, và mỗi gia vị nền bắt buộc bị báo thiếu (`M_pantry`) làm tăng mẫu số thêm `1.0`:

```text
C(r, U, X) = (|R_main ∩ U| + 0.5 * |O_main ∩ U|) / (|R_main| + 0.5 * |O_main| + |M_pantry|)
```

### 3.3. Mức phù hợp thời gian `T`

Gọi `t = prep_minutes + cook_minutes` (phút, trong đó `cook_minutes` đã bao gồm cả thời gian ướp/chờ/hầm bắt buộc theo `BR-05`). Hàm chuẩn hóa thời gian:

```text
T(r) = max(0.0, min(1.0, (60.0 - t) / 45.0))
```

Nghĩa là món `<= 15` phút nhận `T = 1.0`, `30` phút nhận `T ≈ 0.667`, `>= 60` phút nhận `T = 0.0`. Nếu có `max_total_minutes` thì món có `t > max_total_minutes` phải bị loại **trước khi chấm**, không chỉ giảm điểm.

### 3.4. Mức phù hợp nhóm ẩm thực `P`

```text
P(r) = 1.0  khi preferred_cuisine_codes rỗng HOẶC r.cuisine_code thuộc preferred_cuisine_codes
P(r) = 0.0  khi preferred_cuisine_codes khác rỗng VÀ r.cuisine_code không thuộc preferred_cuisine_codes
```

### 3.5. Điểm tổng `S`

```text
S(r, U, X) = round(100.0 * (0.55 * C + 0.25 * E + 0.10 * T + 0.10 * P), 1)
```

`C, E, T, P` thuộc `[0, 1]`, nên `S` thuộc `[0, 100]`. `score` trả về làm tròn 1 chữ số thập phân. Trọng số **0.55 / 0.25 / 0.10 / 0.10** là cấu hình quy tắc v1 và cần đánh giá độ hợp lý qua benchmark người dùng, không được mô tả là đã tối ưu bằng AI.

## 4. Nhóm khả thi và thứ tự hiển thị

- `availability = "ready"` khi và chỉ khi người dùng đủ toàn bộ nguyên liệu chính bắt buộc VÀ không thiếu gia vị nền bắt buộc nào: `|R_main - U| = 0` và `|M_pantry| = 0` (tương đương `E = 1.0`). Thiếu nguyên liệu tùy chọn (`O_main`) vẫn là `"ready"`.
- `availability = "missing"` khi `|R_main - U| >= 1` hoặc `|M_pantry| >= 1` (`E < 1.0`); trả về:
  - `matched_ingredient_ids = sorted((R_main ∪ O_main) ∩ U)`
  - `missing_required_ingredient_ids = sorted((R_main - U) ∪ M_pantry)`
  - `missing_optional_ingredient_ids = sorted(O_main - U)`
- Lọc cứng: recipe `published`, `cuisine_codes` (nếu có), `max_total_minutes` (nếu có), `|(R_main ∪ O_main) ∩ U| >= 1` (`C > 0`), và `include_missing`.
- Xếp nhóm **`ready` trước `missing`**, trong từng nhóm xếp theo:
  1. `score DESC`
  2. `len(missing_required_ingredient_ids) ASC`
  3. `total_minutes ASC`
  4. `recipe_id ASC` (để ổn định kết quả).
- Lấy top `limit` sau sắp xếp; `total` phản ánh tổng số ứng viên thỏa điều kiện lọc trước khi cắt theo `limit`.
- Nếu không có kết quả, trả `items = []`, `total = 0`, UI khuyến khích thêm nguyên liệu hoặc gỡ bộ lọc; **không bịa công thức**.

## 5. Ví dụ tính tay, kiểm chứng được

Giả sử công thức **"Trứng xào cà chua"** (`prep_minutes = 5`, `cook_minutes = 8`, `total_minutes = 13`, `cuisine_code = "VN"`) có:
- Nguyên liệu chính bắt buộc (`R_main`): `trứng gà`, `cà chua` (`|R_main| = 2`).
- Nguyên liệu chính tùy chọn (`O_main`): `hành lá` (`|O_main| = 1`).
- Gia vị nền bắt buộc (`R_pantry`): `dầu ăn`, `nước mắm` (`|R_pantry| = 2`).

Người dùng xác nhận có **trứng gà và cà chua** (`U = {trứng gà, cà chua}`); không có hành lá; không đặt sở thích mềm (`P = 1.0`); chọn lọc `VN` và tối đa `15` phút (`T = 1.0`).

### Trường hợp 1: Mặc định đủ gia vị nền (`excluded_pantry_ids = []`)

- `M_pantry = ∅` (`|M_pantry| = 0`).
- `E = 2 / (2 + 0) = 1.0`.
- `C = (2 + 0.5 * 0) / (2 + 0.5 * 1 + 0) = 2 / 2.5 = 0.8`.
- `T = max(0, min(1, (60 - 13) / 45)) = 1.0`.
- `P = 1.0`.
- `S = round(100 * (0.55 * 0.8 + 0.25 * 1.0 + 0.10 * 1.0 + 0.10 * 1.0), 1) = 89.0`.
- Nhóm: `availability = "ready"`, `missing_required_ingredient_ids = []`, `missing_optional_ingredient_ids = [hanh_la_id]`.

Nếu người dùng có thêm hành lá thì `C = 1.0` và điểm trở thành **100.0**.

### Trường hợp 2: Người dùng bỏ chọn "Nước mắm" (`excluded_pantry_ids = [nuoc_mam_id]`)

- `M_pantry = {nước mắm}` (`|M_pantry| = 1`).
- `E = 2 / (2 + 1) = 2/3 ≈ 0.6667`.
- `C = (2 + 0.5 * 0) / (2 + 0.5 * 1 + 1) = 2 / 3.5 ≈ 0.5714`.
- `T = 1.0`, `P = 1.0`.
- `S = round(100 * (0.55 * (2 / 3.5) + 0.25 * (2 / 3) + 0.10 * 1.0 + 0.10 * 1.0), 1) = round(68.095..., 1) = 68.1`.
- Nhóm: chuyển từ `"ready"` sang `availability = "missing"`, `missing_required_ingredient_ids = [nuoc_mam_id]`, `missing_optional_ingredient_ids = [hanh_la_id]`.

**Lưu ý:** thời gian `5 + 8` và nguyên liệu trên là ví dụ dữ liệu để mô tả thuật toán, không phải thời gian thực nghiệm của một recipe đã xác minh.

## 6. Pseudocode độc lập công nghệ

```python
def recommend(confirmed_ids, recipes, excluded_pantry_ids=None,
              max_total_minutes=None, cuisine_codes=None,
              preferred_cuisine_codes=None, include_missing=True, limit=20):
    U = set(confirmed_ids)
    X = set(excluded_pantry_ids or [])
    assert len(U) >= 1
    items = []
    for r in recipes:
        if r.status != 'published' or not r.required_main:
            continue
        if cuisine_codes and r.cuisine_code not in cuisine_codes:
            continue
        t = r.prep_minutes + r.cook_minutes
        if max_total_minutes is not None and t > max_total_minutes:
            continue
        R_main = set(r.required_main)
        O_main = set(r.optional_main)
        R_pantry = set(r.required_pantry)
        if not ((R_main | O_main) & U):
            continue
        M_pantry = R_pantry & X
        E = len(R_main & U) / (len(R_main) + len(M_pantry))
        C = (len(R_main & U) + 0.5 * len(O_main & U)) / (
            len(R_main) + 0.5 * len(O_main) + len(M_pantry)
        )
        missing_req = (R_main - U) | M_pantry
        is_ready = (len(missing_req) == 0)
        if not include_missing and not is_ready:
            continue
        T = max(0.0, min(1.0, (60.0 - t) / 45.0))
        P = 1.0 if not preferred_cuisine_codes or r.cuisine_code in preferred_cuisine_codes else 0.0
        score = round(100.0 * (0.55 * C + 0.25 * E + 0.10 * T + 0.10 * P), 1)
        items.append({
            'recipe_id': r.id,
            'availability': 'ready' if is_ready else 'missing',
            'score': score,
            'matched_ingredient_ids': sorted((R_main | O_main) & U),
            'missing_required_ingredient_ids': sorted(missing_req),
            'missing_optional_ingredient_ids': sorted(O_main - U),
            'score_breakdown': dict(C=C, E=E, T=T, P=P),
            'total_minutes': t,
        })
    items.sort(key=lambda x: (
        0 if x['availability'] == 'ready' else 1,
        -x['score'],
        len(x['missing_required_ingredient_ids']),
        x['total_minutes'],
        str(x['recipe_id']),
    ))
    return items[:limit], len(items)
```

Trong mã sản phẩm, các tập `required_main`, `optional_main`, `required_pantry` được tách tự động từ `recipe_ingredients JOIN ingredients` theo `is_required` và `category = 'pantry'`.

## 7. Đánh giá thuật toán và quy tắc thống kê phản hồi

Đánh giá không chỉ "có kết quả": dùng bộ ít nhất 20–30 kịch bản thành phần/công thức do nhóm tạo và được review; đối chiếu thứ tự top-k với chuyên gia/nhóm người dùng theo tiêu chí đã chốt. Chỉ số có thể dùng: tỷ lệ món `ready` được xếp đúng nhóm, Precision@5 cho món phù hợp theo nhãn do người đánh giá xác nhận, mức hữu ích tự báo cáo (`recommendation_feedback`), và tỷ lệ thiếu nguyên liệu bắt buộc (kể cả gia vị nền bị bỏ chọn) được hiển thị chính xác.

- **Lưu ý quy tắc thống kê `recommendation_feedback` ([ADR-012](../07-decisions/ADR-012-feedback-uniqueness-and-context.md)):** Bảng `recommendation_feedback` dùng khóa duy nhất `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)` và khóa ngoại `scan_session_id REFERENCES scan_sessions(id) ON DELETE CASCADE`. Khi người dùng xóa một phiên quét (`DELETE /api/v1/scan-sessions/{scan_id}`), các đánh giá gắn với phiên quét đó cũng bị xóa theo để tránh xung đột với bản ghi đánh giá duyệt tự do (`scan_session_id IS NULL`). Khi tổng hợp điểm đánh giá trung bình theo công thức cho báo cáo phân tích (ngoài phạm vi MVP), nếu một người dùng có nhiều bản ghi đánh giá cho cùng một `recipe_id` ở các ngữ cảnh `scan_session_id` khác nhau, truy vấn thống kê chỉ lấy **1 bản ghi có `updated_at` mới nhất trên mỗi cặp `(user_id, recipe_id)`** để tránh lệch trọng số.

Không gọi điểm `S` là "độ chính xác AI"; `S` là **điểm tương thích quy tắc**. Việc thay đổi trọng số chỉ sau khi có báo cáo thử nghiệm mới tạo `Scoring v2` và ghi ADR nếu ảnh hưởng hành vi.
