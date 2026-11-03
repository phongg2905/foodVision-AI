# Quy trình dữ liệu và đánh giá AI

## 1. Nguồn dữ liệu và pháp lý

**Ưu tiên:** tự chụp ảnh có quyền sử dụng, tập open data có license rõ ràng, hoặc dữ liệu do thành viên tự cung cấp và đồng ý. Với mỗi nguồn lưu metadata: `source_id`, đường dẫn/trang, tác giả/nhà cung cấp, giấy phép, số lượng ảnh, ngày truy xuất, quyền chỉnh sửa và công bố.

Không được thu thập ảnh bừa từ Google Images/website công thức rồi coi là dữ liệu có giấy phép. Không tự sử dụng ảnh upload của user để train nếu chưa có đồng ý riêng. Không commit ảnh dataset/weights lớn vào Git thường; sử dụng storage có version + manifest/hash.

## 2. Cấu trúc dataset (format YOLO detect)

```text
datasets/foodvision-v1/
  dataset.yaml
  images/train/ ...
  images/val/ ...
  images/test/ ...
  labels/train/ ...
  labels/val/ ...
  labels/test/ ...
  manifest.csv          # ID ảnh/nguồn/license/split/scene_id
```

`dataset.yaml` ví dụ, tên lớp và số lượng phải khớp bảng nhãn thật:

```yaml
path: datasets/foodvision-v1
train: images/train
val: images/val
test: images/test
names:
  0: tomato
  1: egg
  2: potato
  # ...
```

Mỗi dòng nhãn: `class_index x_center y_center width height` (tất cả bbox xywh chuẩn hóa `[0, 1]`). Bbox trả ra API lại dùng **xyxy** chuẩn hóa trên ảnh đã xoay chuẩn theo EXIF Orientation: hai định dạng **không giống nhau**.

## 3. Kế hoạch thu thập và split

- **Mục tiêu thu thập khởi đầu để kiểm tra tính khả thi:** ít nhất khoảng 80 đối tượng được gán nhãn/lớp; **không phải mức đủ bảo đảm chất lượng**. Ưu tiên tăng mẫu lớp khó và sự đa dạng cảnh, ánh sáng, nền, góc chụp hơn là chỉ tăng số lượng.
- Split ban đầu đề xuất **70% train / 15% validation / 15% test** ở cấp *scene/source/session*; ảnh cùng phiên chụp và ảnh augment của một ảnh gốc **không được rơi vào các tập khác nhau**.
- Test giữ cố định, không dùng test để tune confidence/hyperparameter. Ghi seed, phiên bản annotation/dataset và model.
- Có ảnh **không chứa nguyên liệu**, ảnh nhiều vật thể chồng nhau, ảnh rung/mờ, nền bếp, ánh sáng kém, ảnh thiết bị khác nhau (bao gồm ảnh xoay dọc có cờ EXIF Orientation).
- Bước kiểm tra annotation: bbox khép kín, đúng lớp, không vượt biên ảnh, không trùng lặp sai, audit ngẫu nhiên và đối chiếu giữa 2 người gán nhãn với lớp khó.

## 4. Protocol huấn luyện

| Mục | Phải ghi lại |
|---|---|
| Environment | OS, Python, package versions, CPU/GPU/RAM, CUDA nếu có |
| Model | family/size, weights init, model version, license |
| Dataset | dataset version/hash, class list, split manifest, license |
| Training | epochs, batch size, image size, augmentation, optimizer, seed |
| Tuning | chọn confidence/NMS trên validation; lý do |
| Artifact | hash của weights, đường dẫn lưu có kiểm soát, model metadata |
| Evaluation | Precision, Recall, mAP50, mAP50-95, per-class AP50, per-class Recall, per-class `N_test`, confusion/error cases |
| Performance | p50/p95 inference và API end-to-end, concurrency, peak RAM |

Không ghi "đã đạt 90%" hoặc tương tự khi chưa có log đánh giá thật.

## 5. Metric, định nghĩa và quy tắc minh bạch đánh giá (`NFR-11`)

- **Precision** = `TP / (TP + FP)`: trong các dự đoán, tỷ lệ đúng.
- **Recall** = `TP / (TP + FN)`: trong vật thể thật, tỷ lệ phát hiện.
- **F1** = `2 * P * R / (P + R)`, khi `P + R > 0`.
- **mAP50** = mean average precision tính ở IoU 0.50 qua toàn bộ các lớp mục tiêu; **mAP50-95** trung bình theo các ngưỡng IoU từ 0.50 đến 0.95. Phải ghi phương pháp tính từ framework.
- **Latency p95**: thời gian 95th percentile của các lượt đo trên phần cứng báo cáo, không phải lời hứa đoán trước.

### Quy tắc đánh giá chất lượng mô hình (`NFR-11`)

1. **Chốt danh sách lớp trước khi đánh giá (`dataset_ready`):** Tập lớp mục tiêu của một phiên bản model phải được chốt trước khi chạy đánh giá cuối cùng trên tập test độc lập, dựa trên điều kiện đủ mẫu và chất lượng gán nhãn.
2. **Cấm loại bỏ lớp yếu sau khi đã chạy đánh giá (No post-hoc class dropping):** Sau khi chạy đánh giá trên tập test, **không được phép loại bỏ các lớp có kết quả thấp khỏi mẫu số tính `mean mAP50`** nhằm làm đẹp chỉ số trung bình.
3. **Bắt buộc công bố bảng chi tiết từng lớp:** Báo cáo đánh giá bắt buộc công bố đầy đủ bảng **per-class `AP50`**, **per-class `Recall`** và **số lượng mẫu kiểm thử `N_test` của từng lớp** bên cạnh chỉ số `mAP50` tổng thể.
4. **Lưu ý phương sai thống kê:** Với quy mô thu thập khởi đầu khoảng 80 đối tượng/lớp và tỷ lệ chia 15% test, mỗi lớp chỉ có khoảng `12–15` đối tượng trong tập test (`N_test` nhỏ), dẫn đến phương sai thống kê trên từng lớp cao. Báo cáo phải ghi rõ `N_test` để hội đồng đánh giá khách quan.
5. **Mục tiêu tham chiếu và mốc chốt:** Ngưỡng tham chiếu dự kiến là `mAP50 >= 0.70` trên tập test độc lập (API detect p95 `<= 10s` trên thiết bị demo). Ngưỡng nghiệm thu chính thức và mốc thời gian chốt sẽ được **AI Lead và Giảng viên hướng dẫn** xác nhận sau khi có kết quả thực nghiệm vòng đầu (Pilot run).

## 6. Bộ kịch bản kiểm chứng

| ID | Ảnh/test | Tiêu chí ghi nhận |
|---|---|---|
| AI-01 | Ảnh có 2–5 loại nguyên liệu | Per-image TP/FP/FN, khả năng hiển thị nhiều bbox |
| AI-02 | Ảnh một nhãn nhưng nhiều đối tượng | Bbox khác nhau; UI danh sách gộp ID đúng |
| AI-03 | Ảnh không có nguyên liệu | False positive rate, manual fallback |
| AI-04 | Ảnh mờ/thiếu sáng/che khuất | Precision/Recall theo nhóm điều kiện |
| AI-05 | Lớp giống nhau (hành các loại, thịt sống) | Confusion matrix, ví dụ nhầm lẫn |
| AI-06 | Ảnh hợp lệ nhưng size lớn | Giới hạn decode, benchmark RAM và latency |
| AI-07 | Class index từ model version mới | Mapping về ingredient chuẩn vẫn chính xác |

## 7. Biểu mẫu báo cáo kết quả (để điền sau khi đo)

| Model version | Dataset version | Số lớp mục tiêu | Precision | Recall | mAP50 | mAP50-95 | p95 detect | Ghi chú (kèm bảng per-class `AP50`, `Recall`, `N_test`) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| _Chưa thực nghiệm_ | _Chưa thực nghiệm_ | — | — | — | — | — | — | Không được tự tạo số liệu; không loại lớp yếu sau khi chạy test |

**Nguồn chính thức:** https://docs.ultralytics.com/datasets/detect và https://docs.ultralytics.com/tasks/detect. **License:** https://www.ultralytics.com/license.
