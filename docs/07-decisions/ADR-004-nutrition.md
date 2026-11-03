# ADR-004 — Thông tin dinh dưỡng định tính ở MVP

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** ảnh một góc không cho biết chắc khối lượng, lượng dầu/đường, phần ăn; số kcal theo gram sẽ gây hiểu nhầm.
- **Decision:** chỉ hiển thị nhóm chất có nguồn từ nguyên liệu/công thức ở mức định tính; không công bố số kcal/g protein/g fat mà không có định lượng tin cậy.
- **Alternatives:** bắt người dùng cân và nhập gram từng thành phần (tăng thao tác); AI ước lượng lượng từ ảnh (độ bất định cao, ngoài MVP).
- **Consequences:** phạm vi thận trọng, giảm rủi ro cung cấp số sai; giảm sức hấp dẫn của ứng dụng calories nhưng phù hợp dữ liệu hiện tại.
- **Revisit when:** bổ sung trường định lượng + nguồn dữ liệu theo khẩu phần, đối chiếu các đơn vị và đánh giá sai số.
- **References:** `docs/05-recommendation/nutrition-and-content.md`, https://fdc.nal.usda.gov/.
