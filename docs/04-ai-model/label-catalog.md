# Danh mục nhãn nguyên liệu — đề xuất MVP 20 lớp

**Trạng thái:** Chưa xác minh tập ảnh, chưa chốt mô hình, chưa cam kết độ chính xác. Bảng này là **candidate label taxonomy**, thứ tự class index chỉ chốt khi xuất `dataset.yaml` chính thức.

## 1. Nhãn dự kiến ban đầu

| Class index (đề xuất) | Code | Tên hiển thị | Nhóm | Lưu ý dữ liệu |
|---:|---|---|---|---|
| 0 | tomato | Cà chua | vegetable | Phân biệt với ớt chuông; cả quả và đã cắt là 2 điều kiện khác |
| 1 | egg | Trứng gà | protein | Chỉ trứng nguyên quả có vỏ ở giai đoạn đầu |
| 2 | potato | Khoai tây | vegetable | Dễ nhầm củ khác nếu thiếu bối cảnh |
| 3 | carrot | Cà rốt | vegetable | Củ nguyên/cắt khúc phải kiểm chứng |
| 4 | onion | Hành tây | vegetable | Tách với hành tím/hành lá |
| 5 | garlic | Tỏi | spice | Củ/tép tươi có hình khối; không nhận bột tỏi |
| 6 | chili_pepper | Ớt | spice | Phân biệt với ớt chuông |
| 7 | cucumber | Dưa leo | vegetable | Các giống khác nhau |
| 8 | cabbage | Bắp cải | vegetable | Nguyên bắp/lá tách rời |
| 9 | broccoli | Bông cải xanh | vegetable | Nguyên bông/cắt nhỏ |
| 10 | mushroom | Nấm | vegetable | Lớp rộng; không xác định nấm ăn được/độc |
| 11 | tofu | Đậu hũ | protein | Thường dạng khối; cần ảnh thực tế |
| 12 | raw_chicken | Thịt gà sống | protein | Dễ nhầm với thịt khác; ảnh thật cần kiểm chứng |
| 13 | raw_pork | Thịt heo sống | protein | Dễ nhầm với thịt gà; không dựa vào màu đơn lẻ |
| 14 | raw_shrimp | Tôm | seafood | Nguyên con/đã bóc vỏ khác nhau |
| 15 | whole_fish | Cá nguyên con | seafood | Không áp dụng cho phi lê/cá cắt khúc |
| 16 | ginger | Gừng | spice | Củ nguyên/cắt lát |
| 17 | scallion | Hành lá | vegetable | Dễ nhầm lá hẹ/các loại rau xanh |
| 18 | bell_pepper | Ớt chuông | vegetable | Đa dạng màu, hình dạng |
| 19 | sweet_corn | Bắp ngọt | vegetable | Nguyên trái/hạt rời khác nhau |

**Chú ý đặc biệt:** các lớp `raw_chicken`/`raw_pork` có nguy cơ nhầm cao; `mushroom` là lớp rộng, không được suy diễn "nấm an toàn để ăn". Nếu thiếu dữ liệu đủ chất lượng ở bước chốt danh sách lớp trước khi chạy đánh giá cuối cùng (`dataset_ready`), thu hẹp tập lớp mục tiêu trước khi đánh giá thay vì tạo độ chính xác ảo.

## 2. Quy tắc đặt nhãn

- Tên trong dataset: tiếng Anh, lowercase, snake_case, một ý nghĩa duy nhất.
- Tên trong UI: tiếng Việt có dấu, map về `ingredients.name_vi`.
- **Phân tách nguyên liệu chính/gia vị tươi có hình khối và gia vị nền (`BR-04`, `BR-12`):** Nhãn YOLO (`ai_labels`) chỉ ánh xạ tới nguyên liệu thực phẩm hoặc gia vị tươi có hình khối nhận diện thị giác được (`category IN ('vegetable', 'protein', 'seafood', 'spice', 'other')` và `is_active = true`, ví dụ: tỏi củ, ớt trái, gừng củ). **Tuyệt đối không ánh xạ nhãn YOLO vào nhóm gia vị nền gia dụng (`category = 'pantry'`, gồm: muối, đường, nước mắm, dầu ăn, tiêu xay)** vì chúng thường đựng trong chai/lọ/hũ không thể phân biệt tin cậy bằng thị giác; backend sẽ chặn bằng mã lỗi `400 INVALID_LABEL_MAPPING`.
- Một class có thể tương ứng **một** ingredient chuẩn trong cùng model version. Không tạo nhãn `vegetable` mơ hồ nếu recipe yêu cầu cà rốt/cà chua cụ thể.
- Alias như "cà chua bi" chỉ map vào "cà chua" khi nhóm xác nhận có thể thay thế về mặt chế biến; các nguyên liệu khác cần ID khác.
- Không thay đổi `class_index` trong cùng một model đã đóng băng (`active` hoặc `archived`). Khi mở rộng từ 20 lên 40/60 nhãn, tạo dataset/model version mới.
- Nhãn ảnh cần phản ánh thứ nhìn thấy, không suy đoán từ màu sắc món đã nấu.

## 3. Chiến lược đa dạng món Việt/Âu/Mỹ

Số lượng **món ăn/công thức trong database** không bị giới hạn bởi số nhãn YOLO. Một món dùng nguyên liệu chưa hỗ trợ AI vẫn có thể được chọn thủ công, miễn đã có `ingredients.id` trong database. Vì thế nhóm có thể mở rộng kho món Việt/Âu/Mỹ sớm, trong khi chỉ nhận diện tự động các loại đủ dữ liệu.

**Tác động mở rộng nhãn:** khi chỉ thêm danh mục nguyên liệu và recipe, **không cần train lại YOLO**; khi muốn AI tự nhận ra loại mới, **phải thu thập/gán nhãn/train/eval model version mới**. Công thức scoring không cần viết lại nếu ID chuẩn và dữ liệu recipe vẫn cùng schema.

## 4. Trạng thái nghiệm thu nhãn

Đối với mỗi nhãn: `proposed → data_ready → annotated → evaluated → released`. Không đặt `released` khi chưa có test độc lập theo lớp. Dùng báo cáo dataset/evaluation để theo dõi.
