# Dataset, Huấn luyện và Đánh giá Thực nghiệm Mô hình AI

**Phiên bản:** `0.9.1-draft` · **Phạm vi kỹ thuật:** Thành phần 01, Thành phần 12.2 (`IoU`, `mAP@50`, `mAP@50:95`) & Quy tắc minh bạch `NFR-11`.

## 1. Nguồn dữ liệu và nguyên tắc bản quyền ([`ADR-005`](../07-decisions/ADR-005-yolo-licensing.md))

Dự án kết hợp có kiểm soát giữa bộ dữ liệu công khai có giấy phép rõ ràng và ảnh nguyên liệu thực tế do nhóm tự chụp trong bối cảnh gian bếp Việt Nam. Mọi nguồn dữ liệu bên ngoài phải được ghi nhận URL, tác giả, giấy phép (`CC0`, `CC-BY`...) và điều kiện phân phối trước khi đưa vào tập huấn luyện; không thu thập ảnh tự động trái điều khoản dịch vụ và không dùng ảnh của người dùng tải lên khi chưa có sự đồng ý tường minh.

## 2. Cấu trúc Dataset chuẩn Ultralytics YOLO

```yaml
# data/ingredients.yaml
path: ../datasets/foodvision-v1
train: images/train
val: images/val
test: images/test

names:
  0: tomato
  1: egg
  2: potato
  3: carrot
  # ... khớp danh sách lớp đã khóa ở mốc dataset_ready (không chứa pantry)
```

Mỗi dòng trong tệp nhãn `.txt` tuân theo định dạng `class_index x_center y_center width height` chuẩn hóa trong đoạn `[0, 1]`. Lưu ý: phản hồi của API `POST /api/v1/ai/detect` sử dụng định dạng **`xyxy` (`x1, y1, x2, y2`) chuẩn hóa `[0, 1]` tính trên khung ảnh đã xoay chuẩn theo cờ `EXIF Orientation`** — hai hệ tọa độ này khác nhau và phải được kiểm thử chuyển đổi chính xác ở tầng hậu xử lý.

## 3. Kế hoạch thu thập và phân chia tập dữ liệu chống rò rỉ

- **Mục tiêu thu thập khởi đầu (Pilot):** tối thiểu khoảng `80` đối tượng được gán nhãn trên mỗi lớp mục tiêu để kiểm tra tính khả thi; ưu tiên tăng mẫu cho các cặp lớp dễ nhầm (`raw_chicken` vs `raw_pork`, `cucumber` vs `zucchini`, `tofu`) và đa dạng hóa nền bếp, ánh sáng, góc chụp, mức che khuất.
- **Chia tập `70% train / 15% validation / 15% test` ở cấp `scene/source/session`:** các ảnh chụp trong cùng một phiên hoặc các biến thể augmentation sinh từ cùng một ảnh gốc **tuyệt đối không được rơi vào hai tập khác nhau**.
- **Đóng băng tập `test`:** tập `test` chỉ dùng đúng cho đánh giá báo cáo cuối cùng; mọi thao tác tinh chỉnh `confidence_threshold`, ngưỡng NMS hay ngưỡng cảnh báo xác nhận HITL $\tau$ đều phải thực hiện trên tập `validation`.
- **Tập ảnh đối chứng thực tế & ngoài phân phối (OOD):** bổ sung ảnh **không chứa nguyên liệu**, ảnh nhiều vật thể chồng lấp, ảnh rung/mờ, ảnh thiếu sáng, ảnh chụp dọc có cờ `EXIF Orientation != 1` và vật thể ngoài danh mục để kiểm chứng cơ chế cảnh báo HITL ($\text{Review}(x) = 1$) và luồng dự phòng nhập tay (`FR-18`).
- **Kiểm soát chất lượng gán nhãn:** hộp giới hạn bao sát vật thể, đúng lớp, không vượt biên `[0, 1]`, kiểm tra chéo ngẫu nhiên giữa tối thiểu 2 thành viên trên các lớp khó.

## 4. Nhật ký bắt buộc khi huấn luyện và kiểm định

| Hạng mục | Nội dung bắt buộc ghi nhận để tái lập |
|---|---|
| `Environment` | Hệ điều hành, phiên bản Python / PyTorch / Ultralytics, thông số CPU / GPU / RAM, CUDA |
| `Model` | Biến thể YOLO, trọng số khởi tạo, `model_version`, giấy phép sử dụng |
| `Dataset` | `dataset_version`, mã băm manifest chia tập, danh sách $K$ lớp đã khóa (`dataset_ready`), giấy phép |
| `Training` | Số `epochs`, `batch_size`, `imgsz`, cấu hình augmentation, optimizer, `seed` |
| `Tuning` | Ngưỡng phát hiện `confidence_threshold` (khởi điểm `0.25`), ngưỡng NMS IoU, ngưỡng cảnh báo HITL $\tau$ (khởi điểm `0.80`) chọn trên tập `val` |
| `Artifact` | Đường dẫn lưu trữ có kiểm soát, mã băm SHA-256 của tệp trọng số |
| `Evaluation` | `Precision`, `Recall`, `F1`, `mAP@50`, `mAP@50:95`, bảng per-class `AP50` / `Recall` / `N_test`, ma trận nhầm lẫn và ca lỗi điển hình |
| `Performance` | Độ trễ suy luận và API end-to-end (`p50` / `p95`), mức giới hạn luồng đồng thời, RAM đỉnh |

## 5. Công thức đo lường thực nghiệm AI thị giác (Thành phần 12.2) & Quy tắc `NFR-11`

Bộ đo lường của dự án **tách bạch hoàn toàn giữa chất lượng nhận diện thị giác và chất lượng hệ gợi ý món ăn** (đánh giá hệ gợi ý bằng `Precision@5` và `nDCG@5` được quy định tại [`recommendation-design.md`](../05-recommendation/recommendation-design.md)).

- **IoU (Intersection over Union):**
  \[
  \text{IoU}(B_p, B_g) = \frac{|B_p \cap B_g|}{|B_p \cup B_g|}
  \]
- **Precision, Recall và F1-score:**
  \[
  \text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \qquad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \qquad F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}
  \]
- **`mAP@50` và `mAP@50:95` (Mean Average Precision trên dải ngưỡng IoU):**
  \[
  \text{mAP@50} = \frac{1}{K} \sum_{c=1}^{K} \text{AP}_{c, 0.50}, \qquad \text{mAP@50:95} = \frac{1}{10K} \sum_{t \in \{0.50, 0.55, \dots, 0.95\}} \sum_{c=1}^{K} \text{AP}_{c,t}
  \]
  Trong đó $K$ là tổng số lớp mục tiêu đưa vào đánh giá và $\text{AP}_{c,t}$ là Average Precision của lớp $c$ tại ngưỡng $\text{IoU} = t$, xuất trực tiếp từ công cụ kiểm định chuẩn của Ultralytics:

```python
from ultralytics import YOLO

model = YOLO("models/ingredients_best.pt")
metrics = model.val(data="data/ingredients.yaml", split="test")
print(metrics.box.map50)  # mAP@50
print(metrics.box.map)    # mAP@50:95
```

### Quy tắc minh bạch đánh giá mô hình bắt buộc (`NFR-11`)

1. **Chốt danh sách lớp trước khi đánh giá (`dataset_ready`):** tập $K$ lớp mục tiêu của một phiên bản model phải được khóa trước khi chạy đánh giá cuối cùng trên tập `test` độc lập.
2. **Cấm loại bỏ lớp yếu sau khi chạy test (No post-hoc class dropping):** sau khi đã chạy đánh giá trên tập `test`, **nghiêm cấm loại bỏ các lớp có kết quả thấp khỏi mẫu số tính `mAP@50` / `mAP@50:95`** để nâng khống chỉ số trung bình.
3. **Bắt buộc công bố bảng chi tiết từng lớp:** báo cáo phải công bố đầy đủ **per-class `AP50`**, **per-class `Recall`** và **số lượng mẫu kiểm thử `N_test` của từng lớp** (lưu ý rõ phương sai thống kê cao khi `N_test ≈ 12–15` mẫu ở giai đoạn đầu).
4. **Mục tiêu tham chiếu:** ngưỡng mục tiêu thiết kế là `mAP@50 >= 0.70` trên tập `test` độc lập và độ trễ API detect `p95 <= 10.0s` trên CPU demo (`<= 3.0s` trên GPU); ngưỡng nghiệm thu chính thức được chốt cùng Giảng viên hướng dẫn sau Pilot run.

## 6. Biểu mẫu báo cáo kết quả (chỉ điền sau khi chạy thực nghiệm thật)

| Model version | Dataset version | Số lớp mục tiêu ($K$) | Precision | Recall | mAP@50 | mAP@50:95 | p95 detect | Ghi chú (đính kèm bảng per-class `AP50`, `Recall`, `N_test`) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| _Chưa thực nghiệm_ | _Chưa thực nghiệm_ | — | — | — | — | — | — | Không tự tạo số liệu giả định; cấm loại lớp yếu sau khi chạy test |

**Nguồn tham khảo:** Redmon et al. (*CVPR*, 2016), https://docs.ultralytics.com/datasets/detect, https://docs.ultralytics.com/tasks/detect và https://www.ultralytics.com/license.
