# Dataset, Huấn luyện và Đánh giá Thực nghiệm Mô hình AI

**Phiên bản:** `1.0.0` · **Phạm vi kỹ thuật:** Thành phần 01, Thành phần 12.2 (`IoU`, `mAP@50`, `mAP@50:95`) & Quy tắc minh bạch `NFR-11`.

## 1. Nguồn dữ liệu và nguyên tắc bản quyền ([`ADR-005`](../07-decisions/ADR-005-yolo-licensing.md))

Dự án kết hợp có kiểm soát giữa các bộ dữ liệu công khai có giấy phép mở đã xác minh (`CC BY 4.0` / `CC BY 2.0` / `CC0`) và dữ liệu ảnh bếp thực tế. Mọi nguồn dữ liệu bên ngoài đều được ghi nhận đầy đủ `source_url`, tác giả, giấy phép và số lượng hộp đóng góp trong tệp kiểm toán [`backend/configs/dataset_attribution_v1_1.json`](../../backend/configs/dataset_attribution_v1_1.json) trước khi huấn luyện; tuyệt đối không dùng ảnh Proprietary/No-License và không dùng ảnh người dùng tải lên khi chưa có sự đồng ý tường minh.

| Nguồn dữ liệu | Tác giả / Nền tảng | Giấy phép | URL nguồn | Đóng góp (`v1.1` khóa 20/20 lớp) |
|---|---|---|---|---|
| `food-ingredients-roboflow-v1` (Base + OOD) | Roboflow Universe Community | `CC BY 4.0` | https://universe.roboflow.com | Tập nền 15 lớp + đối chứng âm OOD (đã lọc bỏ 2 nhãn lệch domain `Tree Tomato` & `Akabare Khursani` và toàn bộ 4 nhãn gia vị `pantry`) |
| `food ingredients` (v5, 1x raw `640px`, no aug) | My workspace (Roboflow Universe) | `CC BY 4.0` | https://universe.roboflow.com/my-workspace-idgwe/food-ingredients-2alny/dataset/5 | `1,753` cảnh độc lập / `8,852` hộp bổ sung 16 lớp (`raw_chicken`, `raw_pork`, `raw_shrimp`, `whole_fish`, `ginger`, `tofu`, `garlic`, `carrot`, `onion`, `potato`, `tomato`, `cucumber`, `bell_pepper`...) |
| `Fish` (v1, 1x raw whole market fish) | blxm (Roboflow Universe) | `CC BY 4.0` | https://universe.roboflow.com/blxm/fish-yjekd/dataset/1 | `168` cảnh độc lập / `170` hộp bổ sung lớp `15: whole_fish` |
| `Tofu` (v1) | SAGES (Roboflow Universe) | `CC BY 4.0` | https://universe.roboflow.com/sages/tofu-47uo2/dataset/1 | `165` cảnh độc lập / `246` hộp bổ sung lớp `11: tofu` |
| Google Open Images Dataset v7 (`Broccoli /m/0hkxq`) | Google / Flickr Contributors | `CC BY 4.0` / `CC BY 2.0` | https://storage.googleapis.com/openimages/web/index.html | `80` cảnh độc lập / `143` hộp bổ sung lớp `9: broccoli` |

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
| `yolo11n-foodvision-v1.0` | `foodvision-yolo-v1.0.0` | `20` | `1314` (`149`) | `0.6851` | `0.5651` | `0.6193` | `0.5836` | `0.3005` | `118.72 ms` / `136.59 ms` (`30` req) | `ultralytics_yolo` |

- **Mã băm toàn vẹn:** `dataset_manifest_sha256 = 5eb7b1e7500127be...`, `weights_sha256 = f72e4c5860772202...`.
- **Ghi chú trung thực thực nghiệm (`NFR-11`):** Trọng số Ultralytics YOLO11s (`imgsz=640`, dataset `v1.1` khóa đầy đủ 20/20 lớp) huấn luyện trên GPU Tesla T4 (`ultralytics_yolo`); tích phân PR-curve theo chuẩn COCO (`conf=0.001`), vận hành tại `conf=0.25`.
- **Kiểm soát OOD & Cảnh báo HITL (`AI-03`, $\tau = 0.80$):** Trên `149` ảnh đối chứng âm (`OOD` không chứa nguyên liệu mục tiêu), số ảnh phát sinh báo động giả là `44`; tỷ lệ hộp dự đoán có `confidence < 0.80` được chuyển sang luồng người dùng xác nhận HITL là `1836 / 3107`.

### 6.2. Bảng chi tiết từng lớp trên toàn bộ $K$ lớp đã khóa (`NFR-11` — Cấm loại lớp yếu sau test)

| `class_index` | Mã nhãn (`code`) | `N_test` (GT boxes) | `TP@50` | `FP@50` | `FN@50` | Precision | Recall | F1 | `AP@50` | `AP@50:95` |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `tomato` | 175 | 99 | 28 | 76 | 0.7795 | 0.5657 | 0.6556 | 0.6412 | 0.3021 |
| 1 | `egg` | 382 | 320 | 187 | 62 | 0.6312 | 0.8377 | 0.7199 | 0.7476 | 0.3621 |
| 2 | `potato` | 384 | 205 | 37 | 179 | 0.8471 | 0.5339 | 0.6550 | 0.6295 | 0.3021 |
| 3 | `carrot` | 166 | 101 | 104 | 65 | 0.4927 | 0.6084 | 0.5445 | 0.5564 | 0.2602 |
| 4 | `onion` | 225 | 208 | 13 | 17 | 0.9412 | 0.9244 | 0.9327 | 0.9602 | 0.5057 |
| 5 | `garlic` | 265 | 168 | 28 | 97 | 0.8571 | 0.6340 | 0.7289 | 0.6559 | 0.3623 |
| 6 | `chili_pepper` | 468 | 103 | 127 | 365 | 0.4478 | 0.2201 | 0.2951 | 0.2252 | 0.0708 |
| 7 | `cucumber` | 136 | 75 | 85 | 61 | 0.4688 | 0.5515 | 0.5068 | 0.4783 | 0.2442 |
| 8 | `cabbage` | 154 | 108 | 41 | 46 | 0.7248 | 0.7013 | 0.7129 | 0.7685 | 0.4050 |
| 9 | `broccoli` | 57 | 23 | 32 | 34 | 0.4182 | 0.4035 | 0.4107 | 0.3872 | 0.2242 |
| 10 | `mushroom` | 389 | 92 | 46 | 297 | 0.6667 | 0.2365 | 0.3491 | 0.3485 | 0.1330 |
| 11 | `tofu` | 73 | 43 | 21 | 30 | 0.6719 | 0.5890 | 0.6277 | 0.5204 | 0.3059 |
| 12 | `raw_chicken` | 145 | 114 | 21 | 31 | 0.8444 | 0.7862 | 0.8143 | 0.8106 | 0.4689 |
| 13 | `raw_pork` | 206 | 99 | 51 | 107 | 0.6600 | 0.4806 | 0.5562 | 0.5516 | 0.2401 |
| 14 | `raw_shrimp` | 70 | 30 | 28 | 40 | 0.5172 | 0.4286 | 0.4688 | 0.4380 | 0.2176 |
| 15 | `whole_fish` | 70 | 26 | 10 | 44 | 0.7222 | 0.3714 | 0.4906 | 0.5349 | 0.2690 |
| 16 | `ginger` | 58 | 35 | 2 | 23 | 0.9459 | 0.6034 | 0.7368 | 0.6001 | 0.2943 |
| 17 | `scallion` | 127 | 51 | 18 | 76 | 0.7391 | 0.4016 | 0.5204 | 0.4805 | 0.3018 |
| 18 | `bell_pepper` | 270 | 182 | 54 | 88 | 0.7712 | 0.6741 | 0.7194 | 0.7346 | 0.3666 |
| 19 | `sweet_corn` | 68 | 51 | 41 | 17 | 0.5543 | 0.7500 | 0.6375 | 0.6029 | 0.3751 |

### 6.3. Minh bạch trạng thái khóa đầy đủ 20/20 lớp (`NFR-11` — 0 lớp chuyển dự phòng)

Toàn bộ **20/20 lớp nguyên liệu chuẩn** (từ `0: tomato` đến `19: sweet_corn`) đều vượt ngưỡng `>= 80` hộp nhãn tại mốc `dataset_ready` nhờ bổ sung hợp pháp các bộ dữ liệu `CC BY 4.0` / `CC BY 2.0` (`ADR-005`), đạt `0` lớp chuyển dự phòng và `0` lớp loại bỏ hậu kiểm (`post_hoc_dropped_classes = []`). Nhánh tìm kiếm tiếng Việt (`FR-18`) và VLM/CLIP (`TP 02`) tiếp tục đóng vai trò mở rộng cho nguyên liệu ngoài 20 lớp chuẩn (ví dụ: `Sả`, `Nghệ tươi`, `Thịt bò`, `Mực tươi`, `Rau muống`...).

### 6.4. Phân tích cặp lớp dễ nhầm lẫn & vai trò bù đắp của HITL (`TP 14`)

- **Cặp hình thái tương đồng cao:** `raw_chicken` vs `raw_pork` (thớ thịt tươi phụ thuộc ánh sáng vàng/trắng nhà bếp), `tofu` vs phô mai trắng `Paneer` (khối vuông trắng đồng nhất), `cucumber` vs bí ngòi `zucchini`, và `tomato` vs `bell_pepper` đỏ.
- **Vai trò bù đắp của HITL (`TP 14`) & CLIP (`TP 02`):** Mọi phát hiện có $p_{\max} < \tau = 0.80$ tự động đưa vào danh sách `uncertain_ingredients[]` kèm cờ `needs_confirmation = true`; người dùng xác nhận/sửa trực tiếp trên giao diện hoặc tra cứu tiếng Việt không dấu/từ đồng nghĩa (`pg_trgm`) trước khi hệ suy luận 3 trạng thái (`TP 04`) chấm điểm công thức, đảm bảo sai số tầng thị giác không lan truyền mù quáng sang tầng gợi ý.

**Nguồn tham khảo:** Redmon et al. (*CVPR*, 2016), https://docs.ultralytics.com/datasets/detect, https://docs.ultralytics.com/tasks/detect và https://www.ultralytics.com/license.
