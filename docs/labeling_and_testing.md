# Quy Chuẩn Gán Nhãn 12 Nhãn YOLO & Kế Hoạch 7 Lớp Kiểm Thử — FoodVision AI

## 1. Quy Chuẩn Gán Nhãn 12 Class Nguyên Liệu (Labeling Guidelines)

Để đảm bảo mô hình YOLO học ổn định và không bị nhiễu giữa các trạng thái thực phẩm (Mục 5.1 & 5.2), cả nhóm tuân thủ nghiêm ngặt quy tắc gán nhãn sau:

| ID | Nhãn (`yolo_class`) | Tên tiếng Việt | Quy tắc gán nhãn (Bounding Box) | Trường hợp KHÔNG gán nhãn / Loại trừ |
| :-: | :--- | :--- | :--- | :--- |
| `0` | `tomato` | Cà chua | Quả cà chua nguyên quả hoặc bổ múi cau lớn còn rõ hình dáng vỏ/ruột đỏ. | Nước sốt cà chua, cà chua đã nấu nhuyễn. |
| `1` | `carrot` | Cà rốt | Củ cà rốt nguyên củ hoặc khúc cắt lớn nhìn rõ màu cam và hình trụ. | Cà rốt bào sợi quá mảnh trộn lẫn trong nộm. |
| `2` | `potato` | Khoai tây | Củ khoai tây nguyên vỏ hoặc đã gọt vỏ còn nguyên củ/miếng lớn. | Khoai tây nghiền hoặc khoai tây chiên sợi mỏng. |
| `3` | `onion` | Hành tây | Củ hành tây nguyên củ (vỏ nâu/trắng) hoặc bổ đôi/múi lớn. | Hành tây phi khô. |
| `4` | `cucumber` | Dưa leo | Quả dưa leo nguyên quả hoặc cắt khúc/lát dày rõ vỏ xanh. | Dưa muối đã biến màu hoàn toàn. |
| `5` | `egg` | Trứng nguyên vỏ | **Chỉ gán nhãn trứng còn nguyên vỏ** (trứng gà/vịt vỏ trắng hoặc nâu). | Trứng đã đập ra bát, trứng chiên, trứng luộc bóc vỏ. |
| `6` | `cabbage` | Bắp cải | Bắp cải nguyên bắp, bổ đôi hoặc bắp cải tím/trắng còn rõ kết cấu lá cuộn. | Bắp cải thái vụn đã xào chín. |
| `7` | `bell_pepper` | Ớt chuông | Quả ớt chuông xanh, đỏ, vàng nguyên quả hoặc bổ miếng lớn. | Ớt chỉ thiên nhỏ, ớt bột. |
| `8` | `pumpkin` | Bí đỏ | Quả bí đỏ nguyên quả hoặc miếng bí đỏ cắt khúc rõ phần thịt vàng cam. | Súp bí đỏ đã xay nhuyễn. |
| `9` | `garlic` | Tỏi | Củ tỏi nguyên củ hoặc tép tỏi nguyên (còn vỏ hoặc đã bóc vỏ). | Tỏi băm nhuyễn hoặc tỏi phi. |
| `10` | `green_onion` | Hành lá | Cây hành lá nguyên nhánh (gồm gốc trắng và lá xanh). | Hành lá cắt nhỏ rắc trên bát canh. |
| `11` | `lemon` | Chanh | Quả chanh xanh/vàng nguyên quả hoặc cắt nửa quả. | Nước cốt chanh trong chén. |

### Nguyên tắc tách tập dữ liệu (Data Split Anti-Leakage)
- Tỷ lệ: **70% Train / 15% Validation / 15% Test**.
- **Chống rò rỉ (Data Leakage)**: Các bức ảnh chụp liên tiếp trong cùng một phiên chụp (cùng bàn bếp, cùng đĩa nguyên liệu chỉ xoay góc nhẹ) **bắt buộc phải nằm trong cùng một tập** (`train` hoặc `val` hoặc `test`).

---

## 2. Kế Hoạch 7 Lớp Kiểm Thử & Nghiệm Thu (Tuần 3)

| STT | Lớp kiểm thử | Kịch bản kiểm thử cụ thể | Bằng chứng cần lưu vào Báo cáo Chương 6 |
| :-: | :--- | :--- | :--- |
| **1** | **Dữ liệu ảnh thực tế** | Ảnh chụp điện thoại ngoài tập train: đủ sáng, thiếu sáng, góc nghiêng, 3–5 nguyên liệu đặt cạnh nhau, che khuất một phần, ảnh không có nguyên liệu. | Bộ ảnh test độc lập, nhãn ground-truth và ảnh vẽ bounding box dự đoán. |
| **2** | **Mô hình YOLO** | Đánh giá định lượng trên tập `test` độc lập. | Bảng `Precision`, `Recall`, `mAP@50` tổng thể và theo từng lớp; Confusion Matrix; phân tích cặp lớp hay nhầm. |
| **3** | **Khuyến nghị Top 5** | • Đủ 100% nguyên liệu chính.<br>• Thiếu 1 nguyên liệu chính.<br>• Hòa điểm số (kiểm tra tiêu chí phá hòa).<br>• Không có món nào khớp. | Bảng tình huống đầu vào, kết quả Top 5 trả về, tính toán kiểm chứng điểm `Score(I, R)`. |
| **4** | **5 Tình huống Dinh dưỡng (Mục 8.5)** | • **TC-N1**: Món có 2–3 nguyên liệu đủ ánh xạ → Hiển thị chất không lặp + đúng nguyên liệu căn cứ.<br>• **TC-N2**: 1 nguyên liệu chưa có hồ sơ dinh dưỡng → Báo *"chưa có dữ liệu đáng tin cậy"*, không tự bịa.<br>• **TC-N3**: 2 nguyên liệu cùng chứa Vitamin C / Protein → Gộp thành 1 mục duy nhất kèm tên cả 2 nguyên liệu.<br>• **TC-N4**: Người dùng sửa nhãn AI nhận diện sai → Gợi ý và dinh dưỡng cập nhật theo nhãn đã sửa.<br>• **TC-N5**: Yêu cầu tính calo/gram từ ảnh → Hiển thị rõ thông báo tính năng định lượng chưa hỗ trợ. | Ảnh chụp màn hình giao diện & JSON response của `/api/recipes/{id}/nutrients` cho cả 5 test cases. |
| **5** | **Giao diện & API** | Tải file `.txt`/`.pdf` giả ảnh, ảnh >10MB, ảnh không phát hiện đối tượng nào, người dùng thêm/xóa nguyên liệu thủ công. | Bảng Test Case UI/API, mã trạng thái HTTP (`200`, `400`, `404`), ảnh màn hình thông báo lỗi. |
| **6** | **Hiệu năng (Latency)** | Đo thời gian tiền xử lý, thời gian suy luận YOLO, thời gian truy vấn gợi ý/dinh dưỡng trên cấu hình máy demo thật. | Bảng thống kê độ trễ trung bình (`ms`) kèm thông số CPU/RAM/GPU của máy chạy demo. |
| **7** | **Bảo mật Supabase** | Kiểm tra Row Level Security (RLS), quyền đọc công khai bảng danh mục và kiểm tra mã nguồn Frontend không chứa `service_role key`. | Ảnh chụp cấu hình RLS trên Supabase Dashboard và kết quả kiểm thử truy cập. |

