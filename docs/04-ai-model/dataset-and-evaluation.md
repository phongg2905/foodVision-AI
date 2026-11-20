# Dataset, Huấn luyện và Đánh giá Thực nghiệm Mô hình AI

**Phiên bản:** `1.0.0` · **Phạm vi kỹ thuật:** Thành phần 01, Thành phần 12.2 (`IoU`, `mAP@50`, `mAP@50:95`) & Quy tắc minh bạch `NFR-11`.

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

## 6. Biểu mẫu báo cáo kết quả (Số liệu đo thực tế độc lập trên `split='test'`)

### 6.1. Bảng tổng hợp chất lượng thị giác (`AI-01`, `AI-02`) & độ trễ suy luận (`PERF-01`)

| Model version | Dataset version | Số lớp khóa ($K$) | Ảnh `test` (OOD) | Precision | Recall | F1 | mAP@50 | mAP@50:95 | `p50` / `p95` detect (`PERF-01`) | Trạng thái trọng số |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `yolo11n-foodvision-v1.0` | `foodvision-yolo-v1.0.0` | `15` | `1116` (`118`) | `0.5278` | `0.4005` | `0.4554` | `0.3411` | `0.1766` | `86.65 ms` / `118.39 ms` (`30` req) | `ultralytics_yolo` |

- **Mã băm toàn vẹn:** `dataset_manifest_sha256 = b56aba197e6ef2ed...`, `weights_sha256 = e6bb515c5f15ffed...`.
- **Ghi chú trung thực thực nghiệm (`NFR-11`):** Trọng số Ultralytics YOLO11n huấn luyện đầy đủ trên GPU (`ultralytics_yolo`).
- **Kiểm soát OOD & Cảnh báo HITL (`AI-03`, $\tau = 0.80$):** Trên `118` ảnh đối chứng âm (`OOD` không chứa nguyên liệu mục tiêu), số ảnh phát sinh báo động giả là `23`; tỷ lệ hộp dự đoán có `confidence < 0.80` được chuyển sang luồng người dùng xác nhận HITL là `1792 / 1929`.

### 6.2. Bảng chi tiết từng lớp trên toàn bộ $K$ lớp đã khóa (`NFR-11` — Cấm loại lớp yếu sau test)

| `class_index` | Mã nhãn (`code`) | `N_test` (GT boxes) | `TP@50` | `FP@50` | `FN@50` | Precision | Recall | F1 | `AP@50` | `AP@50:95` |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `tomato` | 180 | 57 | 22 | 123 | 0.7215 | 0.3167 | 0.4402 | 0.2730 | 0.1352 |
| 1 | `egg` | 318 | 163 | 131 | 155 | 0.5544 | 0.5126 | 0.5327 | 0.4300 | 0.2000 |
| 2 | `potato` | 215 | 44 | 109 | 171 | 0.2876 | 0.2047 | 0.2391 | 0.1308 | 0.0283 |
| 3 | `carrot` | 72 | 12 | 15 | 60 | 0.4444 | 0.1667 | 0.2424 | 0.0927 | 0.0230 |
| 4 | `onion` | 62 | 35 | 19 | 27 | 0.6481 | 0.5645 | 0.6034 | 0.5374 | 0.3632 |
| 5 | `garlic` | 108 | 2 | 121 | 106 | 0.0163 | 0.0185 | 0.0173 | 0.0101 | 0.0100 |
| 6 | `chili_pepper` | 518 | 167 | 196 | 351 | 0.4601 | 0.3224 | 0.3791 | 0.2538 | 0.1004 |
| 7 | `cucumber` | 90 | 57 | 52 | 33 | 0.5229 | 0.6333 | 0.5729 | 0.5451 | 0.2347 |
| 8 | `cabbage` | 135 | 73 | 4 | 62 | 0.9481 | 0.5407 | 0.6887 | 0.5429 | 0.2530 |
| 9 | `broccoli` | 45 | 45 | 16 | 0 | 0.7377 | 1.0000 | 0.8491 | 1.0000 | 0.6153 |
| 10 | `mushroom` | 385 | 113 | 127 | 272 | 0.4708 | 0.2935 | 0.3616 | 0.1728 | 0.0801 |
| 13 | `raw_pork` | 59 | 15 | 17 | 44 | 0.4688 | 0.2542 | 0.3297 | 0.1943 | 0.1360 |
| 17 | `scallion` | 129 | 42 | 16 | 87 | 0.7241 | 0.3256 | 0.4492 | 0.2943 | 0.1533 |
| 18 | `bell_pepper` | 182 | 110 | 107 | 72 | 0.5069 | 0.6044 | 0.5514 | 0.4520 | 0.2367 |
| 19 | `sweet_corn` | 68 | 17 | 25 | 51 | 0.4048 | 0.2500 | 0.3091 | 0.1875 | 0.0802 |

### 6.3. Minh bạch 5 lớp ứng viên chuyển sang nhập tay / CLIP trước khi mở tập `test` (`NFR-11`)

Theo quy tắc tại [`label-catalog.md`](label-catalog.md) (Mục 1), 5 lớp ứng viên có số mẫu thô `< 80` đã được khóa chuyển sang tìm kiếm tiếng Việt (`FR-18`) và nhánh phụ CLIP (`TP 02`) **tại mốc `dataset_ready` trước khi chạy `split='test'`**, tuyệt đối không phải loại bỏ hậu kiểm:

| `class_index` | Mã nhãn (`code`) | Tổng mẫu thô hiện có | Thiếu hụt so với ngưỡng `80` | Cơ chế bù đắp trong kiến trúc 7 tầng |
|---:|---|---:|---:|---|
| 11 | `tofu` | 41 | 39 | `FR-18 manual search & TP-02 CLIP helper` |
| 12 | `raw_chicken` | 52 | 28 | `FR-18 manual search & TP-02 CLIP helper` |
| 14 | `raw_shrimp` | 0 | 80 | `FR-18 manual search & TP-02 CLIP helper` |
| 15 | `whole_fish` | 6 | 74 | `FR-18 manual search & TP-02 CLIP helper` |
| 16 | `ginger` | 23 | 57 | `FR-18 manual search & TP-02 CLIP helper` |

### 6.4. Phân tích cặp lớp dễ nhầm lẫn & vai trò bù đắp của HITL (`TP 14`)

- **Cặp hình thái tương đồng cao:** `raw_chicken` vs `raw_pork` (thớ thịt tươi phụ thuộc ánh sáng vàng/trắng nhà bếp), `tofu` vs phô mai trắng `Paneer` (khối vuông trắng đồng nhất), `cucumber` vs bí ngòi `zucchini`, và `tomato` vs `bell_pepper` đỏ.
- **Vai trò bù đắp của HITL (`TP 14`) & CLIP (`TP 02`):** Mọi phát hiện có $p_{\max} < \tau = 0.80$ tự động đưa vào danh sách `uncertain_ingredients[]` kèm cờ `needs_confirmation = true`; người dùng xác nhận/sửa trực tiếp trên giao diện hoặc tra cứu tiếng Việt không dấu/từ đồng nghĩa (`pg_trgm`) trước khi hệ suy luận 3 trạng thái (`TP 04`) chấm điểm công thức, đảm bảo sai số tầng thị giác không lan truyền mù quáng sang tầng gợi ý.

**Nguồn tham khảo:** Redmon et al. (*CVPR*, 2016), https://docs.ultralytics.com/datasets/detect, https://docs.ultralytics.com/tasks/detect và https://www.ultralytics.com/license.
