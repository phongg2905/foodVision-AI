# Thiết kế thông tin dinh dưỡng và quản trị công thức

## 1. Ranh giới thông tin dinh dưỡng

FoodVision AI MVP **không** có cân thực phẩm, ảnh chuẩn tỷ lệ, dữ liệu khẩu phần đã đo hay công cụ phân tích thành phần dinh dưỡng theo khối lượng. Vì vậy:

- **Được:** hiển thị các **nhóm chất/đặc điểm định tính** gắn với nguyên liệu có nguồn kiểm chứng, kèm lưu ý rằng lượng thực tế phụ thuộc khối lượng và cách chế biến.
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

Ví dụ nhãn UI: "Thông tin tham khảo: vitamin C" và "Protein là nhóm chất có thể tìm thấy trong nguyên liệu này" khi có căn cứ phù hợp; tránh dùng các từ tuyệt đối như "đảm bảo đủ chất". Một nhãn không có nguồn thì không nên public.

**Nguồn chuẩn:** https://fdc.nal.usda.gov/ và https://fdc.nal.usda.gov/api-guide/.

## 3. Cách hiển thị trên màn hình công thức

- Tên nhãn nhóm chất (nếu có), các nguyên liệu liên quan và liên kết nguồn.
- Thông báo: **"Đây là thông tin tham khảo ở mức nguyên liệu, không phải tính toán hàm lượng dinh dưỡng của khẩu phần; kết quả phụ thuộc khối lượng và cách chế biến."**
- Không mặc định tổng hợp một món thành "giàu chất X" từ việc có nguyên liệu X; điều kiện định lượng cần chuẩn riêng và dữ liệu đủ.
- Nếu thiếu nguồn, hiển thị "Chưa có thông tin dinh dưỡng được kiểm chứng" thay vì điền dữ liệu đoán.

## 4. Nguồn công thức, thời gian nấu và bản quyền

**Vì sao cần `prep_minutes` và `cook_minutes` riêng?** Một món có thể mất 10 phút nấu nhưng thêm 20 phút sơ chế. Chỉ gắn nhãn "≤15 phút" nếu **tổng** thời gian của công thức đã duyệt ≤15. Không bịa thời gian để khớp filter.

Mỗi công thức cần: `name_vi`, `cuisine_code`, ingredients (required/optional), quantities **chỉ hiển thị**, steps tự biên soạn/hợp pháp, prep, cook, source_name, source_url và content_license hoặc bằng chứng tác giả gốc. Admin không được công bố món khi thiếu bước, thiếu nguyên liệu required hoặc không xác định được quyền dùng ảnh.

**Với món Việt/Âu/Mỹ:** chỉ dùng ba nhóm để lọc giao diện MVP; có thể bổ sung `country_code` để truy xuất vùng/đất nước chi tiết (Ý, Pháp, Hoa Kỳ...) về sau. Với tên/phiên bản món địa phương, dùng mô tả từ nguồn có thể kiểm chứng; không tự khẳng định công thức "chính thống".

**Bản quyền:** không sao chép nguyên văn hướng dẫn dài hoặc ảnh từ website công thức mà chưa được cấp phép. Có thể học cách tính thời gian/cấu trúc từ nguồn tham khảo, sau đó tự viết công thức và kiểm chứng nguồn; liên kết nguồn không thay thế giấy phép nếu sử dụng lại tác phẩm.

## 5. Checklist nội dung trước publish

- [ ] Có ít nhất 1 required ingredient và 1 step hữu ích.
- [ ] Có `prep_minutes≥0`, `cook_minutes≥0`, `total_minutes` hợp lý theo món được nhóm review.
- [ ] Hướng dẫn không khuyến nghị thao tác nguy hiểm, đặc biệt với nguyên liệu sống.
- [ ] Có nhóm ẩm thực phù hợp, không dùng "Âu" để chỉ một quốc gia cụ thể.
- [ ] Ảnh cover hợp pháp, ghi nguồn/giấy phép.
- [ ] Nếu có nutrition tag, nguồn rõ và cách diễn giải không phóng đại.
- [ ] Không gán nhãn 10–15 phút khi tổng thời gian vượt mức.

## 6. Mở rộng sau MVP

Nếu có yêu cầu ước lượng kcal/protein/chất béo, **bắt buộc thêm bước người dùng nhập khối lượng/phần ăn hoặc nguồn đo đáng tin**; thiết kế schema dữ liệu định lượng riêng, tính theo đơn vị và ghi sai số/giả định. Không chỉ thêm trường kcal mặc định dựa trên ảnh.
