# Chính sách Dinh dưỡng Hai Tầng, Quy đổi Khẩu phần & Quản trị Nội dung Công thức

**Phiên bản:** `0.9.1-draft` · **Phạm vi kỹ thuật:** Thành phần 10 (Verified Recipe Retrieval & Portion Scaling), Thành phần 11 (USDA FoodData Central & Qualitative Nutrition), [`ADR-004`](../07-decisions/ADR-004-nutrition.md) & [`ADR-009`](../07-decisions/ADR-009-cooking-and-waiting-time.md).

## 1. Ranh giới an toàn về thông tin dinh dưỡng (`NFR-07`, `BR-03`, [`ADR-004`](../07-decisions/ADR-004-nutrition.md))

Ảnh chụp nguyên liệu thông thường tại nhà không có vật chuẩn kích thước, không có cân thực phẩm và không phản ánh tỷ lệ hao hụt hay lượng dầu/gia vị thực tế khi chế biến. Do đó, hệ thống áp dụng chính sách hai tầng nghiêm ngặt:

1. **Cấm tuyệt đối suy đoán khối lượng từ ảnh:** không bao giờ suy diễn số `gram` hay `kcal` trực tiếp từ kích thước hộp giới hạn (`bbox`) hoặc số vật thể trên ảnh RGB.
2. **Tầng 1 — Nhãn nhóm chất định tính (Mặc định bắt buộc ở MVP `P0`):** hiển thị các nhóm chất tham khảo (`nutrition_tags`) gắn với nguyên liệu kèm đường dẫn nguồn kiểm chứng hợp lệ (`source_url`, ví dụ USDA FoodData Central), tách bạch khu vực nguyên liệu chính (`category != 'pantry'`) với khu vực nhắc nhở **"Gia vị cần chuẩn bị"** (`category = 'pantry'`), và luôn hiển thị câu cảnh báo miễn trừ trách nhiệm bắt buộc (`BR-03`):
   > *"Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu/công thức chuẩn, kết quả thực tế phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không cam kết miễn trừ dị ứng tuyệt đối."*
3. **Tầng 2 — Ước tính định lượng tham khảo theo USDA FoodData Central (Mở rộng Giai đoạn 4 / `P1`):** chỉ kích hoạt khi công thức `published` đã được biên tập đầy đủ khối lượng ăn được $m_i$ (`grams` theo `base_servings`) và ánh xạ chuẩn sang bảng thành phần trên `100g` của USDA (`ingredient_nutrients`), hoặc khi người dùng chủ động nhập/quy đổi khẩu phần.

## 2. Mô hình dữ liệu và công thức ước tính dinh dưỡng USDA (Thành phần 11)

```text
ingredients
  ├── ingredient_nutrition_tags (source_url, note, reviewed_at) ──► nutrition_tags (Tầng 1 — P0)
  └── ingredient_nutrients (fdc_id, kcal/protein/carbs/fat_per_100g, source_url) (Tầng 2 — P1)
```

Gọi $m_i > 0$ là khối lượng phần ăn được (tính bằng `gram`) của nguyên liệu $i$ trong công thức $r$ và $V_{i,k}$ là hàm lượng chất dinh dưỡng $k$ (năng lượng `kcal`, chất đạm, chất béo, chất bột đường, chất xơ...) trên mỗi `100g` nguyên liệu $i$ theo **USDA FoodData Central** (https://fdc.nal.usda.gov/):

\[
N_k(r) = \sum_{i \in \text{Ingredients}(r)} \frac{m_i}{100} \, V_{i,k}
\]

*(Khi có dữ liệu khoa học tin cậy về tỷ lệ giữ lại chất dinh dưỡng theo phương pháp nhiệt $\text{ret}_{i,k}$, có thể mở rộng thành $\sum \frac{m_i}{100} V_{i,k} \text{ret}_{i,k}$; nếu chưa có bảng hệ số kiểm chứng cho cách nấu cụ thể, giữ $\text{ret}_{i,k} = 1$ và ghi rõ đây là ước tính trên nguyên liệu thô trước chế biến).*

- **Ví dụ kiểm chứng tính tay:** với `150g` cà chua ($18\text{ kcal}/100\text{g}$) và `50g` trứng gà ($155\text{ kcal}/100\text{g}$):
  \[
  E = \frac{150}{100} \times 18 + \frac{50}{100} \times 155 = 27 + 77.5 = 104.5\text{ kcal} \quad (\text{làm tròn hiển thị } \approx 105\text{ kcal; hoặc } 104\text{ kcal nếu trứng } 154\text{ kcal}/100\text{g})
  \]
- Nếu một công thức chưa có đủ `grams` hoặc thiếu ánh xạ nguồn cho các thành phần chính, hệ thống tự động chỉ hiển thị **Tầng 1 (nhãn định tính)** hoặc thông báo *"Chưa đủ định lượng chuẩn để ước tính kcal"*, tuyệt đối không điền số đoán.

## 3. Quản trị công thức kiểm duyệt, quy đổi khẩu phần & quy ước thời gian (Thành phần 10 & `BR-05`)

### 3.1. Chống ảo giác nội dung (Verified Recipe Retrieval)

Hệ thống chỉ phục vụ các công thức từ kho dữ liệu có cấu trúc đã được Admin kiểm duyệt (`status = 'published'`). Không cho phép mô hình ngôn ngữ (LLM) tự ý sinh công thức chưa kiểm duyệt, thêm bớt nguyên liệu hay lược bỏ cảnh báo thành phần dị ứng.

### 3.2. Công thức quy đổi khẩu phần và giới hạn tuyến tính

Khi người dùng thay đổi số khẩu phần từ khẩu phần gốc $n_{\text{base}}$ (`base_servings`) sang $n_{\text{new}}$:

\[
q_i^{\text{new}} = q_i^{\text{base}} \frac{n_{\text{new}}}{n_{\text{base}}}
\]

Khối lượng nguyên liệu $m_i$ và ước tính năng lượng tổng $N_k(r)$ thay đổi tỷ lệ thuận theo $n_{\text{new}} / n_{\text{base}}$, kèm ghi chú bắt buộc trên UI: **thời gian chế biến, mức nhiệt và lượng gia vị nêm nếm có thể không tăng/giảm tuyến tính hoàn toàn theo phép nhân khẩu phần**.

### 3.3. Quy ước `prep_minutes`, `cook_minutes` và kiểm tra tính nhất quán (`BR-01`, `BR-05`, [`ADR-009`](../07-decisions/ADR-009-cooking-and-waiting-time.md))

- `prep_minutes`: thời gian sơ chế cơ học (rửa, gọt, thái, băm...).
- `cook_minutes`: tổng thời gian chế biến nhiệt trên bếp **cộng thời gian ướp, chờ ngấm gia vị hoặc ninh/hầm bắt buộc** trong quy trình chuẩn. Không được tách bỏ thời gian ướp/chờ bắt buộc ra ngoài `cook_minutes` để làm thấp giả tạo `total_minutes`.
- `total_minutes = prep_minutes + cook_minutes`: chỉ số duy nhất dùng để lọc cứng `max_total_minutes` và tính điểm thời gian `T(r)`. Chỉ gắn nhãn nhanh `"<= 15 phút"` khi `total_minutes <= 15`.
- **Kiểm tra tự động bắt buộc:** khi công bố công thức (`PATCH /api/v1/admin/recipes/{id}/status` sang `published`) **hoặc khi chỉnh sửa (`PATCH /api/v1/admin/recipes/{id}`) một công thức đang `published`**, backend từ chối với `400 RECIPE_NOT_PUBLISHABLE` (`reason = "step_exceeds_total_minutes"`) nếu có bất kỳ bước đơn lẻ nào trong `recipe_steps` có `estimated_minutes > prep_minutes + cook_minutes`. Nếu tổng cộng dồn `sum(estimated_minutes) > total_minutes` (do có các bước sơ chế/hầm song song), giao diện Admin hiển thị cảnh báo vàng để người biên tập rà soát lại.

### 3.4. Đa dạng ẩm thực Việt / Âu / Mỹ và bản quyền nội dung

- Cả ba nhóm ẩm thực giao diện (`cuisine_code IN ('VN', 'EU', 'US')`, kèm `country_code` ISO tùy chọn như `IT`, `FR`, `VN`) dùng chung 100% khung thuật toán suy luận, tính điểm, cá nhân hóa và dinh dưỡng; sự khác biệt nằm ở dữ liệu công thức, bảng bí danh (`ingredient_aliases`) và trọng số vai trò nguyên liệu $w_{r,i}$ theo từng món.
- Không sao chép nguyên văn văn bản hướng dẫn dài hoặc ảnh có bản quyền khi chưa được phép; bắt buộc lưu đầy đủ `source_name`, `source_url` và `content_license`.

## 4. Checklist nội dung trước khi chuyển sang `published`

- [ ] Có ít nhất `1` nguyên liệu chính bắt buộc (`is_required = true`, `category != 'pantry'`) và ít nhất `1` bước hướng dẫn (`recipe_steps`).
- [ ] Toàn bộ nguyên liệu gắn với công thức đều đang hoạt động (`is_active = true`).
- [ ] `prep_minutes >= 0`, `cook_minutes >= 0` (đã gồm thời gian ướp/chờ/hầm bắt buộc), và không có bước đơn lẻ nào có `estimated_minutes > prep_minutes + cook_minutes`.
- [ ] Đã rà soát cảnh báo biên tập nếu `sum(estimated_minutes) > total_minutes` và khai báo đúng tác nhân dị ứng (`ingredient_allergens`) cho giai đoạn lọc cứng.
- [ ] Hướng dẫn chế biến rõ ràng, đảm bảo an toàn vệ sinh thực phẩm với nguyên liệu sống (`raw_chicken`, `raw_pork`, `seafood`, `mushroom`).
- [ ] Ảnh minh họa hợp pháp, ghi đầy đủ `source_name`, `source_url`, `content_license`; mọi nhãn dinh dưỡng/chỉ số USDA đều có `source_url` hợp lệ và hiển thị thông báo miễn trừ trách nhiệm.
