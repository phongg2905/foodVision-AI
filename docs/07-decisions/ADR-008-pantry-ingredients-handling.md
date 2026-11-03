# ADR-008 — Cơ chế bật/tắt gia vị nền gia dụng (`category = 'pantry'`) và tác động lên thuật toán gợi ý

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** Các công thức nấu ăn luôn cần các gia vị nền cơ bản trong bếp (muối, đường, nước mắm, dầu ăn, tiêu xay) và nước lọc. Mô hình YOLO Object Detection không thể nhận diện tin cậy các chất lỏng/bột đựng trong chai lọ (ví dụ phân biệt nước mắm với xì dầu, muối với đường), trong khi bắt người dùng nhập tay từng gia vị ở mỗi lần quét sẽ gây phiền hà. Tuy nhiên, nếu loại bỏ hoàn toàn gia vị nền khỏi thuật toán chấm điểm, người dùng đang hết một gia vị thiết yếu (như hết nước mắm) vẫn bị gợi ý món ở nhóm `"ready"`.
- **Decision:**
  1. Bổ sung giá trị `'pantry'` vào miền giá trị `ingredients.category` (`'vegetable'`, `'protein'`, `'seafood'`, `'spice'`, `'pantry'`, `'other'`) cho 5 gia vị nền gia dụng (`muoi`, `duong`, `nuoc-mam`, `dau-an`, `tieu-xay`). Nước lọc sinh hoạt không tạo bản ghi trong bảng `ingredients` mà chỉ ghi trong văn bản hướng dẫn (`recipe_steps.instruction`).
  2. Giữ tách biệt với `'spice'` (gia vị tươi có hình khối nhận diện thị giác được như tỏi, ớt, gừng). Cấm ánh xạ `ai_labels` vào nguyên liệu `pantry` (`400 INVALID_LABEL_MAPPING`), cấm tắt hoặc đổi `category` của nguyên liệu đang dùng trong công thức `published` hoặc model `draft`/`active` (`400 INGREDIENT_IN_USE`), và bắt buộc mỗi công thức `published` có tối thiểu 1 nguyên liệu chính bắt buộc (`is_required = true`, `category != 'pantry'`).
  3. Trên giao diện xác nhận nguyên liệu (`UC-03`, `FR-05`), hiển thị thanh **"Gia vị sẵn có trong bếp"** mặc định bật sẵn (`checked`). Khi người dùng bỏ chọn một gia vị vì đang hết, frontend gửi UUID của gia vị đó trong mảng `excluded_pantry_ids` (mặc định `[]`) của `POST /api/v1/recommendations`.
  4. Trong thuật toán chấm điểm (`FR-06`), gọi `M_pantry = R_pantry ∩ X` là tập gia vị nền bắt buộc của món mà người dùng báo thiếu (`X = set(excluded_pantry_ids)`):
     - `E = |R_main ∩ U| / (|R_main| + |M_pantry|)`
     - `C = (|R_main ∩ U| + 0.5 * |O_main ∩ U|) / (|R_main| + 0.5 * |O_main| + |M_pantry|)`
     - Khi `|M_pantry| > 0`, món tự động chuyển sang `availability = "missing"` và liệt kê các gia vị thiếu trong `missing_required_ingredient_ids`.
- **Alternatives:**
  - *Phương án A:* Bắt người dùng tự thêm muối, đường, nước mắm vào `ingredient_ids` mỗi lần tìm món (tốn thao tác, dễ quên).
  - *Phương án B:* Loại bỏ hoàn toàn `pantry` khỏi chấm điểm và không có nút bật/tắt (không xử lý được tình huống bếp hết nước mắm/dầu ăn).
- **Consequences:** Giữ nguyên điểm số chuẩn `S = 89.0` cho ví dụ cơ sở khi đủ gia vị (`excluded_pantry_ids = []`), đồng thời phản ánh chính xác việc thiếu gia vị bắt buộc (`S = 68.1`, `missing`) khi người dùng tắt gia vị trên UI. Hợp đồng API chặt chẽ: gửi UUID `pantry` trong `ingredient_ids` hoặc gửi nguyên liệu chính trong `excluded_pantry_ids` sẽ trả `422 INVALID_INGREDIENTS`.
- **Revisit when:** Hệ thống bổ sung tính năng lưu cấu hình tủ bếp cá nhân hóa bền vững theo hồ sơ User (`user_pantry_preferences`) ở các phiên bản sau MVP.
- **References:** [`docs/01-requirements/SRS.md`](../01-requirements/SRS.md), [`docs/03-api/openapi.yaml`](../03-api/openapi.yaml), [`docs/05-recommendation/recommendation-design.md`](../05-recommendation/recommendation-design.md).

