# Danh mục Nhãn Thị giác & Chuẩn hóa Nguyên liệu Tiếng Việt

**Phiên bản:** `1.0.0` · **Trạng thái:** 20 lớp ứng viên khởi điểm (`Approved Baseline`). Danh sách lớp chính thức chỉ được khóa ở mốc `dataset_ready` trước khi chạy đánh giá cuối cùng trên tập `test` độc lập (`NFR-11`).

## 1. Bảng 20 lớp thị giác ứng viên ban đầu

| Class index (đề xuất) | Code | Tên hiển thị chuẩn (`name_vi`) | Nhóm (`category`) | Lưu ý dữ liệu & xử lý nhập nhằng thị giác |
|---:|---|---|---|---|
| 0 | `tomato` | Cà chua | `vegetable` | Phân biệt với ớt chuông đỏ; nguyên quả và cắt múi là hai điều kiện hình ảnh khác nhau |
| 1 | `egg` | Trứng gà | `protein` | Giai đoạn đầu tập trung trứng nguyên quả có vỏ |
| 2 | `potato` | Khoai tây | `vegetable` | Dễ nhầm củ khác khi dính đất hoặc thiếu bối cảnh |
| 3 | `carrot` | Cà rốt | `vegetable` | Kiểm chứng cả củ nguyên và cắt khúc |
| 4 | `onion` | Hành tây | `vegetable` | Tách biệt rõ với hành tím, hành lá và tỏi |
| 5 | `garlic` | Tỏi | `spice` | Củ/tép tươi có hình khối; không nhận diện bột tỏi |
| 6 | `chili_pepper` | Ớt | `spice` | Phân biệt với ớt chuông |
| 7 | `cucumber` | Dưa leo | `vegetable` | Dễ nhầm bí ngòi (`zucchini`); cần cảnh báo xác nhận HITL khi $p_{\max} < \tau$ |
| 8 | `cabbage` | Bắp cải | `vegetable` | Nguyên bắp hoặc lá tách rời |
| 9 | `broccoli` | Bông cải xanh | `vegetable` | Nguyên bông hoặc cắt nhỏ |
| 10 | `mushroom` | Nấm | `vegetable` | Lớp rộng; **tuyệt đối không suy diễn "nấm an toàn để ăn"** từ ảnh |
| 11 | `tofu` | Đậu hũ | `protein` | Khối trắng dễ nhầm phô mai trắng/thạch — ứng viên điển hình cho lớp hỗ trợ CLIP/VLM (Thành phần 02) |
| 12 | `raw_chicken` | Thịt gà sống | `protein` | Nguy cơ nhầm cao với thịt heo sống; bắt buộc kiểm chứng trên ảnh thực tế |
| 13 | `raw_pork` | Thịt heo sống | `protein` | Không kết luận chỉ dựa vào sắc độ đỏ/hồng đơn lẻ |
| 14 | `raw_shrimp` | Tôm | `seafood` | Nguyên con và tôm bóc vỏ có đặc trưng thị giác khác nhau |
| 15 | `whole_fish` | Cá nguyên con | `seafood` | Không áp dụng tự động cho cá phi lê/cắt khúc |
| 16 | `ginger` | Gừng | `spice` | Củ nguyên hoặc cắt lát |
| 17 | `scallion` | Hành lá | `vegetable` | Dễ nhầm lá hẹ hoặc các loại rau lá xanh |
| 18 | `bell_pepper` | Ớt chuông | `vegetable` | Đa dạng màu sắc (xanh, đỏ, vàng) và hình dạng |
| 19 | `sweet_corn` | Bắp ngọt | `vegetable` | Nguyên trái hoặc tách hạt; có từ đồng nghĩa vùng miền (`"ngô ngọt"`) |

**Chú ý an toàn dữ liệu (`NFR-11`):** các lớp `raw_chicken`/`raw_pork` có nguy cơ nhầm lẫn cao; `mushroom` là lớp khái quát, không được suy diễn an toàn độc tố. Nếu thiếu dữ liệu đủ chất lượng ở bước rà soát trước khi khóa `dataset_ready`, nhóm chủ động thu hẹp tập lớp mục tiêu **trước khi chạy đánh giá tập `test`** (chuyển các nguyên liệu đó sang tìm kiếm/chọn thủ công), tuyệt đối không loại bỏ lớp yếu sau khi đã xem kết quả test.

## 2. Quy tắc đặt nhãn, ranh giới `pantry` và chuẩn hóa tiếng Việt (Thành phần 13)

- **Tên lớp trong dataset YOLO:** tiếng Anh, `lowercase`, `snake_case`, đơn nghĩa.
- **Phân tách nguyên liệu chính/gia vị tươi có hình khối và gia vị nền (`BR-04`, `BR-12`, [`ADR-008`](../07-decisions/ADR-008-pantry-ingredients-handling.md)):**
  - Nhãn YOLO (`ai_labels`) chỉ ánh xạ tới nguyên liệu thực phẩm hoặc gia vị tươi có hình khối nhận diện thị giác được (`category IN ('vegetable', 'protein', 'seafood', 'spice', 'other')` và `is_active = true`).
  - **Tuyệt đối không ánh xạ nhãn YOLO vào nhóm gia vị nền gia dụng (`category = 'pantry'`: muối, đường, nước mắm, dầu ăn, tiêu xay)** vì chúng đựng trong chai/lọ/hũ không thể phân biệt tin cậy bằng thị giác; backend chặn vi phạm bằng mã lỗi `400 INVALID_LABEL_MAPPING`.
- **Không đổi `class_index` trên model đã khóa:** bảng `ai_labels` của model `active` hoặc `archived` là bất biến (`400 MODEL_IMMUTABLE`). Khi mở rộng từ 20 lên 40/60 lớp, phải tạo `ai_models.version` mới.
- **Liên kết tìm kiếm tiếng Việt có dấu / không dấu / từ đồng nghĩa vùng miền (Thành phần 13):**
  Không thể chỉ dựa vào hàm bỏ dấu Unicode vì người dùng Việt Nam dùng nhiều từ đồng nghĩa khác hẳn mặt chữ (như `"đậu hũ"` ↔ `"đậu phụ"`, `"bắp"` ↔ `"ngô"`, `"dưa leo"` ↔ `"dưa chuột"`). Hệ thống kết hợp 3 lớp xử lý để quy mọi truy vấn về đúng UUID `ingredients.id`:
  1. **Hàm chuẩn hóa chuỗi $\text{Norm}(s)$:** chuyển chữ thường (`casefold`), đổi `đ -> d`, chuẩn hóa khoảng trắng, phân rã Unicode `NFD` và loại bỏ dấu thanh (`Mn`).
  2. **Bảng bí danh `ingredient_aliases(ingredient_id, alias, normalized_alias, locale)`:** ánh xạ nhiều tên gọi vùng miền về cùng một `ingredient_id` (ví dụ cả `"dau hu"` và `"dau phu"` đều trỏ về `tofu`).
  3. **Độ tương đồng tam tự PostgreSQL `pg_trgm`:** tính $\text{Score}(q, a) = \text{Similarity}(\text{Norm}(q), \text{Norm}(a))$ trên chỉ mục GIN (`gin_trgm_ops`) theo thứ tự ưu tiên 4 bậc: khớp mã/alias chính xác → khớp chuỗi đã chuẩn hóa `Norm(s)` → khớp gần đúng `pg_trgm` vượt ngưỡng → hiển thị danh sách ứng viên để người dùng xác nhận tường minh.

## 3. Chiến lược mở rộng đa dạng món Việt / Âu / Mỹ

Số lượng **công thức món ăn (`recipes`) và danh mục nguyên liệu (`ingredients`) trong PostgreSQL hoàn toàn độc lập với giới hạn 20 lớp của YOLO**:

- Các nguyên liệu phổ biến ngoài 20 lớp đầu (mì Ý, bơ, phô mai, thịt bò, các loại rau thơm...) và 5 gia vị nền `pantry` vẫn có đầy đủ `ingredients.id` cùng `ingredient_aliases` để người dùng tìm kiếm thủ công hoặc bật/tắt trên thanh gia vị sẵn có.
- Khi chỉ bổ sung nguyên liệu và công thức Việt (`VN`), Âu (`EU`), Mỹ (`US`) vào CSDL: **không cần huấn luyện lại YOLO** và **không cần sửa thuật toán chấm điểm**.
- Khi muốn AI tự phát hiện thêm nguyên liệu mới từ ảnh: thu thập ảnh hợp pháp → gán nhãn → huấn luyện & kiểm định độc lập → phát hành `ai_models.version` mới mà không làm hỏng dữ liệu lịch sử quét cũ.

## 4. Vòng đời nghiệm thu nhãn

Mỗi lớp thị giác đi qua chu trình: `proposed -> dataset_ready -> annotated -> evaluated -> released`. Không gắn trạng thái `released` khi chưa có số liệu đánh giá độc lập theo từng lớp (`AP50`, `Recall`, `N_test`) trong báo cáo kiểm định.
