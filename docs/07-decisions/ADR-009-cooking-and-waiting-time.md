# ADR-009 — Quy ước tính thời gian ướp/chờ/hầm bắt buộc vào `cook_minutes` và kiểm tra tính nhất quán thời gian

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** Nhiều món ăn có thời gian ướp nguyên liệu, chờ ngấm gia vị hoặc ninh/hầm bắt buộc (ví dụ ướp thịt 20 phút, hầm 40 phút). Nếu chỉ tính thời gian đứng đảo trên bếp vào `cook_minutes`, tổng thời gian `total_minutes = prep_minutes + cook_minutes` sẽ thấp giả tạo, làm bộ lọc `max_total_minutes` và điểm thời gian `T(r)` sai lệch so với thực tế trải nghiệm của người nấu.
- **Decision:**
  1. Quy định `cook_minutes` trong bảng `recipes` bao gồm cả thời gian chế biến nhiệt trên bếp **và** thời gian ướp, chờ ngấm gia vị hoặc hầm bắt buộc trong quy trình chuẩn (`BR-05`).
  2. Kiểm tra tự động điều kiện cần khi công bố công thức (`PATCH /api/v1/admin/recipes/{id}/status` sang `published`) và khi sửa công thức đang `published` (`PATCH /api/v1/admin/recipes/{id}`): không được có bất kỳ bước đơn lẻ nào trong `recipe_steps` có `estimated_minutes > prep_minutes + cook_minutes` (vi phạm trả `400 RECIPE_NOT_PUBLISHABLE` với `reason = "step_exceeds_total_minutes"`).
  3. Không chặn cứng khi tổng cộng dồn `sum(estimated_minutes)` của các bước vượt `prep_minutes + cook_minutes` (vì các bước sơ chế và hầm/ướp có thể diễn ra song song), nhưng hiển thị cảnh báo biên tập trên Admin UI để người nhập liệu rà soát.
- **Alternatives:**
  - Tách thêm cột `wait_minutes` / `marinate_minutes` riêng trong bảng `recipes` (làm phức tạp thêm schema và giao diện lọc trong phạm vi MVP).
  - Ràng buộc cứng `sum(estimated_minutes) <= prep_minutes + cook_minutes` ở tầng DB/API (gây lỗi giả với các món có bước song song).
- **Consequences:** Giữ nguyên cấu trúc 2 cột `prep_minutes` và `cook_minutes` hiện có trong DB và OpenAPI, ngăn chặn lỗi nhập liệu vô lý (1 bước dài hơn tổng thời gian cả món) mà vẫn linh hoạt cho các quy trình nấu song song.
- **Revisit when:** Cần bộ lọc tách riêng "thời gian đứng bếp chủ động" (active time) và "tổng thời gian chờ" (passive time) sau MVP.
- **References:** [`docs/01-requirements/SRS.md`](../01-requirements/SRS.md), [`docs/02-architecture/data-dictionary.md`](../02-architecture/data-dictionary.md), [`docs/05-recommendation/nutrition-and-content.md`](../05-recommendation/nutrition-and-content.md).

