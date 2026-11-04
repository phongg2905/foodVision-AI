# ADR-004 — Chính sách Dinh dưỡng Hai Tầng: Nhãn Định tính (`P0`) & Ước tính USDA theo Định lượng Chuẩn (`P1`)

- **Status:** Accepted
- **Date:** 03/11/2026
- **Context:** Một ảnh RGB chụp nguyên liệu tại nhà không có vật chuẩn kích thước, không cho biết khối lượng gram thực tế hay tỷ lệ hao hụt/ngấm dầu khi nấu. Suy đoán số `kcal` trực tiếp từ ảnh sẽ tạo sai số lớn; tuy nhiên, ở giai đoạn mở rộng khi công thức đã được biên tập định lượng `grams` chuẩn theo khẩu phần, hệ thống cần cơ sở toán học minh bạch để ước tính dinh dưỡng tham khảo.
- **Decision:** Áp dụng chính sách dinh dưỡng hai tầng có kiểm soát theo lộ trình:
  1. **Cấm tuyệt đối suy đoán khối lượng từ ảnh (`NFR-07`, `BR-03`):** Không bao giờ biến kích thước bounding box hay số lượng vật thể trong ảnh thành số `gram` hoặc `kcal` tự động.
  2. **Tầng 1 — Nhãn nhóm chất định tính (Mặc định bắt buộc ở MVP `P0`):** Hiển thị các nhóm chất tham khảo (`nutrition_tags`) gắn với nguyên liệu kèm đường dẫn nguồn kiểm chứng hợp lệ (`source_url`) và tuyên bố miễn trừ trách nhiệm y tế/dị ứng.
  3. **Tầng 2 — Ước tính định lượng theo USDA FoodData Central (Mở rộng Giai đoạn 4 / `P1`):** Chỉ khi công thức `published` đã có khối lượng ăn được $m_i$ (`grams` đã kiểm duyệt theo `base_servings`) hoặc người dùng chủ động nhập/quy đổi khẩu phần $q_i^{\text{new}} = q_i^{\text{base}}(n_{\text{new}}/n_{\text{base}})$, hệ thống mới tính ước tính tham khảo theo công thức chuẩn $N_k(r) = \sum (m_i / 100) V_{i,k}$ (chỉ nhân hệ số giữ lại $\text{ret}_{i,k}$ khi có căn cứ dữ liệu), hiển thị kèm nguồn USDA và cảnh báo giả định chế biến.
- **Alternatives:** Ước lượng thể tích/khối lượng 3D trực tiếp từ 1 ảnh RGB (sai số rất lớn khi thiếu vật chuẩn); hoặc cấm vĩnh viễn mọi phép tính `kcal` kể cả khi công thức đã có sẵn số gram chuẩn hóa.
- **Consequences:** Bảo đảm hợp đồng MVP `P0` an toàn tuyệt đối (không ảo giác gram từ ảnh), đồng thời cung cấp công thức tính toán chuẩn USDA rõ ràng cho Giai đoạn 4 và kịch bản bảo vệ học phần (`DEF-09`).
- **Revisit when:** Tích hợp cân nhà bếp thông minh hoặc quy trình chụp ảnh có vật chuẩn kích thước được kiểm định sai số thực nghiệm.
- **References:** [`docs/05-recommendation/nutrition-and-content.md`](../05-recommendation/nutrition-and-content.md), https://fdc.nal.usda.gov/.
