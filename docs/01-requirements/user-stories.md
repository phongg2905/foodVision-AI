# User Stories và Acceptance Criteria

**Quy ước:** US-xx gắn FR; kịch bản Given/When/Then mang ý nghĩa điều kiện cần đạt, **chưa phải kết quả kiểm thử**.

| ID | Story | FR | Ưu tiên |
|---|---|---|---|
| US-01 | Là khách, tôi muốn tìm món theo tên/ẩm thực/thời gian để nhanh chọn được công thức. | FR-01 | P0 |
| US-02 | Là khách, tôi muốn xem nguyên liệu, bước và thời gian để biết có thể nấu món không. | FR-02 | P0 |
| US-03 | Là khách, tôi muốn tải ảnh chứa nhiều nguyên liệu để hệ thống tự đề xuất danh sách. | FR-03, FR-04 | P0 |
| US-04 | Là khách, tôi muốn sửa kết quả AI và thêm nguyên liệu thủ công để không bị gợi ý sai. | FR-05, FR-18 | P0 |
| US-05 | Là khách, tôi muốn thấy món nấu được và món còn thiếu nguyên liệu cùng lý do xếp hạng. | FR-06 | P0 |
| US-06 | Là khách, tôi muốn lọc món Việt/Âu/Mỹ và thời gian ≤15 phút khi cần nấu nhanh. | FR-07 | P0 |
| US-07 | Là khách, tôi muốn biết nhóm dinh dưỡng có nguồn nhưng không bị cung cấp kcal thiếu căn cứ. | FR-08 | P0 |
| US-08 | Là user, tôi muốn đăng nhập, lưu món yêu thích và chỉ mình tôi xem được danh sách đó. | FR-09, FR-10 | P1 |
| US-09 | Là user, tôi muốn chọn lưu, xem/xóa lịch sử, hoặc không để lại lịch sử phân tích. | FR-12 | P1 |
| US-10 | Là user, tôi muốn đánh giá món gợi ý để nhóm có dữ liệu kiểm chứng độ hữu ích. | FR-11 | P1 |
| US-11 | Là admin, tôi muốn tạo/sửa/công bố công thức và nguyên liệu chuẩn để dữ liệu sạch. | FR-13, FR-14 | P0 |
| US-12 | Là admin, tôi muốn chỉnh ánh xạ nhãn AI và nội dung dinh dưỡng, xem log thay đổi. | FR-15, FR-16, FR-17 | P1 |

## AC-01 — Phát hiện nhiều nguyên liệu (US-03)

```gherkin
Given ảnh JPEG hợp lệ có tối thiểu 2 nguyên liệu thuộc lớp YOLO đã huấn luyện
When guest gửi ảnh đến /api/v1/ai/detect
Then hệ thống trả HTTP 200 và trường detections là một mảng
And mỗi detection có class_name, confidence [0..1], bbox chuẩn hóa [0..1], ingredient_id nếu ánh xạ được
And UI hiển thị các phát hiện để khách xác nhận
```

*Chú ý:* không bắt buộc AI phải phát hiện đủ mọi vật thể trong mỗi ảnh; mức chất lượng đo ở báo cáo AI riêng.

## AC-02 — Sửa AI (US-04)

```gherkin
Given AI gợi ý "cà chua" và "cà rốt"
When khách đổi "cà rốt" thành "khoai tây" và xác nhận
Then request /recommendations chỉ chứa ID của cà chua và khoai tây
And các ID trùng bị gộp, không tính hai lần
```

## AC-03 — Tính đúng nhóm món (US-05)

```gherkin
Given công thức A cần cà chua và trứng, đều thuộc danh sách đã xác nhận
And công thức B cần cà chua và thịt gà, nhưng user không có thịt gà
When gọi /recommendations với include_missing=true
Then A có availability=ready
And B có availability=missing với missing_required_ingredient_ids chứa ID thịt gà
And nhóm ready xuất hiện trước nhóm missing dù điểm B có thể cao hơn
```

## AC-04 — Lọc thời gian (US-06)

```gherkin
Given công thức A có prep_minutes=5 và cook_minutes=10
And công thức B có prep_minutes=15 và cook_minutes=20
When max_total_minutes=15
Then A có thể hiển thị
And B phải bị loại khỏi kết quả
```

## AC-05 — Quyền riêng tư (US-08, US-09)

```gherkin
Given user A và user B có hai token Supabase khác nhau
When A lưu món yêu thích
Then B không thể xem, xóa, hoặc chỉnh dữ liệu của A
And guest dùng detect với save_history=false không có scan_session hay ảnh lưu trên server
```

## AC-06 — Quản trị (US-11)

```gherkin
Given user thường có token hợp lệ
When user gọi POST /api/v1/admin/recipes
Then server trả 403
And database không có công thức mới hoặc audit thành công giả
```
