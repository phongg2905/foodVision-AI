# Thiết kế thông tin dinh dưỡng và quản trị công thức

## 1. Ranh giới thông tin dinh dưỡng

FoodVision AI MVP **không** có cân thực phẩm, ảnh chuẩn tỷ lệ, dữ liệu khẩu phần đã đo hay công cụ phân tích thành phần dinh dưỡng theo khối lượng. Vì vậy:

- **Được:** hiển thị các **nhóm chất/đặc điểm định tính** gắn với nguyên liệu có nguồn kiểm chứng (`source_url` hợp lệ), kèm lưu ý rằng lượng thực tế phụ thuộc khối lượng và cách chế biến.
- **Không được:** khẳng định một ảnh/công thức có chính xác `450 kcal`, `35 g protein`, `20 g fat` nếu chưa có khối lượng và bảng thành phần được tính đúng.
- **Không được:** kết luận "phù hợp cho người bệnh", "an toàn cho dị ứng", "đảm bảo ăn kiêng"; không suy diễn an toàn thực phẩm từ nhãn ảnh.

## 2. Nguồn và mô hình dữ liệu

USDA FoodData Central là nguồn thông tin thành phần dinh dưỡng đáng tin cậy và có dữ liệu CC0/public domain, nhưng thành phần thực tế còn khác theo loại thực phẩm, cách chuẩn bị và khối lượng. Sử dụng nó làm **nguồn tham chiếu**, không tự biến số trên 100 g thành số của một ảnh không biết lượng.

Mô hình:

```text
ingredients (cà chua)
  └── ingredient_nutrition_tags (source_url, reviewed_at)
         └── nutrition_tags (code, name_vi, description)
```

Ví dụ nhãn UI: "Thông tin tham khảo: vitamin C" và "Protein là nhóm chất có thể tìm thấy trong nguyên liệu này" khi có căn cứ phù hợp; tránh dùng các từ tuyệt đối như "đảm bảo đủ chất". Một nhãn không có nguồn (`source_url`) thì không được phép lưu hoặc công bố (`BR-03`).

**Nguồn chuẩn:** https://fdc.nal.usda.gov/ và https://fdc.nal.usda.gov/api-guide/.

## 3. Cách hiển thị trên màn hình công thức

- Tên nhãn nhóm chất (nếu có), các nguyên liệu liên quan và liên kết nguồn (`source_url`).
- Thông báo miễn trừ bắt buộc (`BR-03`): **"Đây là thông tin tham khảo ở mức nguyên liệu, không phải tính toán hàm lượng dinh dưỡng của khẩu phần; kết quả phụ thuộc khối lượng và cách chế biến. Hệ thống không thay thế tư vấn y tế, dinh dưỡng lâm sàng và không tự động sàng lọc dị ứng thực phẩm."**
- Tách bạch hiển thị nguyên liệu chính (`category != 'pantry'`) và khu vực nhắc nhở **"Gia vị cần chuẩn bị"** (`category = 'pantry'`, ví dụ: muối, đường, nước mắm, dầu ăn, tiêu xay).
- Không mặc định tổng hợp một món thành "giàu chất X" từ việc có nguyên liệu X; điều kiện định lượng cần chuẩn riêng và dữ liệu đủ.
- Nếu thiếu nguồn, hiển thị "Chưa có thông tin dinh dưỡng được kiểm chứng" thay vì điền dữ liệu đoán.

## 4. Nguồn công thức, thời gian nấu (`BR-05`) và bản quyền

**Định nghĩa `prep_minutes`, `cook_minutes` và `total_minutes` ([ADR-009](../07-decisions/ADR-009-cooking-and-waiting-time.md)):**
- `prep_minutes`: thời gian sơ chế nguyên liệu (rửa, gọt, thái, băm...).
- `cook_minutes`: tổng thời gian chế biến trên bếp **cộng thời gian ướp, chờ ngấm gia vị hoặc hầm bắt buộc** trong quy trình chế biến món ăn. Không được bỏ thời gian ướp/chờ bắt buộc ra ngoài `cook_minutes` để làm đẹp tổng thời gian hiển thị.
- `total_minutes = prep_minutes + cook_minutes`: chỉ số dùng để lọc `max_total_minutes` và tính điểm `T(r)`. Chỉ gắn nhãn "≤ 15 phút" nếu `total_minutes <= 15`.
- **Kiểm tra tự động điều kiện cần (`BR-01`, `BR-05`):** Khi công bố công thức (`PATCH /api/v1/admin/recipes/{id}/status` sang `published`) hoặc khi chỉnh sửa một công thức đang `published` (`PATCH /api/v1/admin/recipes/{id}`), backend kiểm tra không được có bất kỳ bước đơn lẻ nào trong `recipe_steps` có `estimated_minutes > prep_minutes + cook_minutes`. Nếu vi phạm, từ chối với `400 RECIPE_NOT_PUBLISHABLE` (`reason = "step_exceeds_total_minutes"`).
- **Cảnh báo biên tập trên Admin UI:** Vì một số bước có thể thực hiện song song (ví dụ vừa hầm xương vừa sơ chế rau), hệ thống không chặn cứng theo tổng cộng dồn các bước, nhưng khi `sum(estimated_minutes) > prep_minutes + cook_minutes`, giao diện Admin hiển thị cảnh báo vàng để người biên tập rà soát lại `cook_minutes` trước khi lưu.

Mỗi công thức cần: `name_vi`, `cuisine_code`, ingredients (required/optional, trong đó phải có tối thiểu 1 nguyên liệu bắt buộc thuộc nhóm thực phẩm chính `category != 'pantry'`), quantities **chỉ hiển thị**, steps tự biên soạn/hợp pháp, `prep_minutes`, `cook_minutes`, `source_name`, `source_url` và `content_license` hoặc bằng chứng tác giả gốc. Admin không được công bố món (hoặc sửa món đang `published`) khi thiếu bước, thiếu nguyên liệu chính bắt buộc, chứa nguyên liệu `is_active = false`, hoặc có bước đơn lẻ vượt quá tổng thời gian.

**Với món Việt/Âu/Mỹ:** chỉ dùng ba nhóm (`VN`, `EU`, `US`) để lọc giao diện MVP; có thể bổ sung `country_code` để truy xuất vùng/đất nước chi tiết (Ý, Pháp, Hoa Kỳ...) về sau. Với tên/phiên bản món địa phương, dùng mô tả từ nguồn có thể kiểm chứng; không tự khẳng định công thức "chính thống".

**Bản quyền:** không sao chép nguyên văn hướng dẫn dài hoặc ảnh từ website công thức mà chưa được cấp phép. Có thể học cách tính thời gian/cấu trúc từ nguồn tham khảo, sau đó tự viết công thức và kiểm chứng nguồn; liên kết nguồn không thay thế giấy phép nếu sử dụng lại tác phẩm.

## 5. Checklist nội dung trước publish

- [ ] Có ít nhất 1 nguyên liệu chính bắt buộc (`is_required = true`, `category != 'pantry'`) và ít nhất 1 bước hướng dẫn (`recipe_steps`).
- [ ] Tất cả nguyên liệu trong công thức đều đang hoạt động (`is_active = true`).
- [ ] Có `prep_minutes >= 0`, `cook_minutes >= 0` (đã tính cả thời gian ướp/chờ/hầm bắt buộc), và không có bước đơn lẻ nào có `estimated_minutes > prep_minutes + cook_minutes`.
- [ ] Đã rà soát cảnh báo nếu tổng `sum(estimated_minutes)` của các bước lớn hơn `total_minutes`.
- [ ] Hướng dẫn không khuyến nghị thao tác nguy hiểm, đặc biệt với nguyên liệu sống.
- [ ] Có nhóm ẩm thực phù hợp, không dùng "Âu" để chỉ một quốc gia cụ thể.
- [ ] Ảnh cover hợp pháp, ghi nguồn/giấy phép.
- [ ] Nếu có nutrition tag, nguồn (`source_url`) hợp lệ và có hiển thị thông báo miễn trừ trách nhiệm định lượng/dị ứng.

## 6. Mở rộng sau MVP

Nếu có yêu cầu ước lượng kcal/protein/chất béo, **bắt buộc thêm bước người dùng nhập khối lượng/phần ăn hoặc nguồn đo đáng tin**; thiết kế schema dữ liệu định lượng riêng, tính theo đơn vị và ghi sai số/giả định. Không chỉ thêm trường kcal mặc định dựa trên ảnh.
