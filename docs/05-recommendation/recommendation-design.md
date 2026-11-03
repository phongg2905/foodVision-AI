# Thiết kế thuật toán gợi ý món ăn — Scoring v1

**Mã:** FV-REC-001 · **Phiên bản:** 1.0.0 · **Trạng thái:** Proposed, chưa hiệu chỉnh trên phản hồi thực tế.

## 1. Đầu vào và nguồn sự thật

Input là danh sách UUID nguyên liệu **do User đã xác nhận**; có thể đến từ YOLO, chỉnh sửa hoặc nhập tay. Mọi `ingredient_id` được kiểm tra tồn tại/hoạt động, khử trùng lặp; không dùng `confidence` YOLO làm độ tin cậy về việc *người dùng có thật nguyên liệu* sau xác nhận.

```json
{
  "ingredient_ids": ["...", "..."],
  "max_total_minutes": 15,
  "cuisine_codes": ["VN"],
  "preferred_cuisine_codes": [],
  "include_missing": true,
  "limit": 20,
  "scan_id": null
}
```

- `cuisine_codes`: lọc **cứng** nhóm ẩm thực (rỗng = không lọc).
- `max_total_minutes`: lọc **cứng** `prep_minutes + cook_minutes ≤ limit` (null = không lọc).
- `preferred_cuisine_codes`: sở thích **mềm** để tính điểm P (rỗng = trung lập, P=1).
- `include_missing=false`: chỉ trả nhóm đủ nguyên liệu bắt buộc.
- `scan_id`: chỉ để lưu ingredient list đã duyệt khi user có consent; **không ảnh hưởng điểm**.

## 2. Chuẩn hóa dữ liệu

- Ký hiệu `U`: tập ingredient IDs user có, đã loại trùng.
- Với công thức `r`, `R_r` gồm **required ingredients**, `O_r` gồm **optional ingredients**; ràng buộc `|R_r|≥1` khi published.
- Trọng số hiện diện của required là 1; optional là 0.5. **Đây là lựa chọn sản phẩm để thử nghiệm**, không phải bằng chứng khoa học về giá trị dinh dưỡng.
- Chỉ xét các công thức published, có thời gian hợp lệ, steps và nguyên liệu bắt buộc.
- Loại món nếu `C=0` (không khớp bất kỳ nguyên liệu nào). Món còn thiếu có thể hiện tùy `include_missing`.

## 3. Công thức tính điểm

### 3.1. Độ phủ nguyên liệu C

\[
C(r,U)=\frac{|R_r \cap U|+0.5\,|O_r \cap U|}{|R_r|+0.5\,|O_r|}
\]

### 3.2. Độ phủ nguyên liệu bắt buộc E

\[
E(r,U)=\frac{|R_r \cap U|}{|R_r|}
\]

### 3.3. Mức phù hợp thời gian T

Gọi `t = prep_minutes + cook_minutes` (phút). Lựa chọn hàm thử nghiệm:

\[
T(r) = \max\!\left(0,\min\!\left(1,\frac{60-t}{45}\right)\right)
\]

Nghĩa là món **≤15 phút** nhận `T=1`, 30 phút nhận `T≈0.667`, **≥60 phút** nhận `T=0`. Nếu có `max_total_minutes` thì món quá giới hạn phải bị loại **trước khi chấm**, không chỉ giảm điểm.

### 3.4. Mức phù hợp nhóm ẩm thực P

\[
P(r)=\begin{cases}
1, & \text{khi không chọn sở thích hoặc món thuộc preferred\_cuisine\_codes}\\
0, & \text{khi có sở thích nhưng món không thuộc nhóm đó}
\end{cases}
\]

### 3.5. Điểm tổng S

\[
\boxed{S(r,U)=100\,(0.55\,C+0.25\,E+0.10\,T+0.10\,P)}
\]

`C,E,T,P∈[0,1]`, nên `S∈[0,100]`. `score` trả về làm tròn 1 chữ số. Trọng số **0.55/0.25/0.10/0.10** là cấu hình v1 và cần đánh giá độ hợp lý qua benchmark người dùng, không được mô tả là đã tối ưu bằng AI.

## 4. Nhóm khả thi và thứ tự hiển thị

- `availability=ready` khi **tất cả required ingredients có trong U** (`E=1`). Thiếu optional vẫn là ready.
- `availability=missing` khi thiếu ≥1 required; trả `missing_required_ingredient_ids`, `missing_optional_ingredient_ids`.
- Lọc cứng: recipe published, cuisine_codes nếu có, max_total_minutes nếu có, `C>0`, include_missing.
- Xếp **ready trước missing**, trong từng nhóm theo `S DESC`, rồi `số required thiếu ASC`, `total_minutes ASC`, `recipe_id ASC` để ổn định.
- Lấy top `limit` sau sắp xếp; `total` phản ánh số ứng viên sau lọc trước limit.
- Nếu không có kết quả, trả `items=[]`, UI khuyến khích thêm nguyên liệu hoặc gỡ bộ lọc; **không bịa công thức**.

## 5. Ví dụ tính tay, kiểm chứng được

Giả sử công thức "Trứng xào cà chua" có 2 nguyên liệu bắt buộc: `trứng gà`, `cà chua`; 1 tùy chọn: `hành lá`; thời gian sơ chế 5 phút + nấu 8 phút, thuộc VN.

User có **trứng và cà chua**; không có hành lá; không đặt sở thích mềm; chọn lọc VN và tối đa 15 phút.

- C = (1+1)/(1+1+0.5) = **0.8**.
- E = 2/2 = **1**.
- T = clamp((60−13)/45,0,1) = **1**.
- P = **1** (không có sở thích mềm).
- S = 100 × (0.55×0.8 + 0.25×1 + 0.10×1 + 0.10×1) = **89.0**.
- Nhóm: `ready`; lý do: đủ nguyên liệu bắt buộc, thiếu hành lá (tùy chọn).

Nếu user có thêm hành lá thì C=1 và điểm trở thành **100.0**. Nếu món 35 phút, phải bị loại bởi bộ lọc `max_total_minutes=15` dù điểm thành phần khác cao.

**Lưu ý:** thời gian 5+8 và nguyên liệu trên là ví dụ dữ liệu để mô tả thuật toán, không phải thời gian thực nghiệm của một recipe đã xác minh.

## 6. Pseudocode độc lập công nghệ

```python
def recommend(confirmed_ids, recipes, max_total_minutes=None,
              cuisine_codes=None, preferred_cuisine_codes=None,
              include_missing=True, limit=20):
    U = set(confirmed_ids)
    assert len(U) >= 1
    items = []
    for r in recipes:
        if r.status != 'published' or not r.required: continue
        if cuisine_codes and r.cuisine_code not in cuisine_codes: continue
        t = r.prep_minutes + r.cook_minutes
        if max_total_minutes is not None and t > max_total_minutes: continue
        required, optional = set(r.required), set(r.optional)
        C = (len(required & U) + 0.5 * len(optional & U)) / (len(required) + 0.5 * len(optional))
        if C == 0: continue
        E = len(required & U) / len(required)
        if not include_missing and E < 1: continue
        T = max(0.0, min(1.0, (60.0 - t) / 45.0))
        P = 1.0 if not preferred_cuisine_codes or r.cuisine_code in preferred_cuisine_codes else 0.0
        score = round(100 * (0.55*C + 0.25*E + 0.10*T + 0.10*P), 1)
        items.append({
            'recipe_id': r.id,
            'availability': 'ready' if E == 1 else 'missing',
            'score': score,
            'missing_required_ingredient_ids': sorted(required - U),
            'missing_optional_ingredient_ids': sorted(optional - U),
            'score_breakdown': dict(C=C, E=E, T=T, P=P),
        })
    return sorted(items, key=lambda x: (
        0 if x['availability'] == 'ready' else 1,
        -x['score'], len(x['missing_required_ingredient_ids']),
        recipe_total_minutes[x['recipe_id']], str(x['recipe_id'])
    ))[:limit]
```

Trong mã sản phẩm, `recipe_total_minutes` phải được xây dựng từ dữ liệu recipe thực; pseudocode chỉ minh họa ý tưởng, không phải hàm chạy độc lập. Cần bổ sung truy vấn DB, validate, pagination, và giải thích tên nguyên liệu.

## 7. Đánh giá thuật toán

Đánh giá không chỉ "có kết quả": dùng bộ ít nhất 20–30 kịch bản thành phần/công thức do nhóm tạo và được review; đối chiếu thứ tự top-k với chuyên gia/nhóm người dùng theo tiêu chí đã chốt. Chỉ số có thể dùng: tỷ lệ món `ready` được xếp đúng nhóm, Precision@5 cho món phù hợp theo nhãn do người đánh giá xác nhận, mức hữu ích tự báo cáo, và tỷ lệ thiếu nguyên liệu bắt buộc được hiển thị chính xác.

Không gọi điểm S là "độ chính xác AI"; S là **điểm tương thích quy tắc**. Việc thay đổi trọng số chỉ sau khi có báo cáo thử nghiệm mới tạo `Scoring v2` và ghi ADR nếu ảnh hưởng hành vi.
