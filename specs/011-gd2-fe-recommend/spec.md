# Feature Specification: Giao diện Danh sách Gợi ý (Ready/Missing), Tùy chọn Thời gian / Nguyên liệu chính & Chi tiết Công thức (GĐ2 - UI)

**Feature Branch**: `feat/011-gd2-fe-recommend`  
**Created**: 2026-11-15  
**Status**: In Implementation (`1.1.0` — `ADR-013`)  
**Owner**: `TV3 — Tâm Minh` (`@tamminh6`) · **Cross-Tester**: `TV1 — Minh Thành`  
**Input**: Trello Card `#11` (`[GĐ2 - UI]`): *"Xây dựng Giao diện Danh sách Gợi ý (Ready/Missing), Tùy chọn Thời gian mong muốn / Nguyên liệu chính & Trang Chi tiết Công thức"* bám chuẩn hệ thiết kế **NEWTASTE** (`specs/018-gd1-fe-ui/references/web-6-newtaste-recipe-website.jpg`).

**Authoritative References (`docs/`)**:
- [SRS](../../docs/01-requirements/SRS.md): `FR-02`, `FR-06`, `FR-07`, `FR-08`, `BR-03`, `BR-04`, `BR-05`, `NFR-01`, `NFR-12`
- [OpenAPI Contract](../../docs/03-api/openapi.yaml): `POST /api/v1/recommendations`, `GET /api/v1/recipes/{recipe_id}`
- [Recommendation Design (`ADR-013`)](../../docs/07-decisions/ADR-013-unified-mcda-and-ingredient-personalization.md): Mô hình chấm điểm 4 tiêu chí `C, G, T, P` (`S = 100 * (0.50*C + 0.25*G + 0.15*T + 0.10*P)`) và lý luận 3 trạng thái (`READY`, `UNKNOWN`, `MISSING_CONFIRMED`)
- [Test Cases](../../docs/06-testing/test-cases.md): `TC-03`, `TC-09`..`TC-15`, `TC-32`..`TC-35`, `UI-01`..`UI-03`, `DEF-03`, `DEF-04`, `DEF-09`, `DEF-10`, `LEGAL-01`

---

## User Scenarios & Testing

### User Story 1 - Danh sách Gợi ý Phân nhóm Ready / Missing (`FR-06`, `ADR-013`) (Priority: P1)

Là khách hoặc người dùng, sau khi chọn nguyên liệu chính và kiểm tra 5 gia vị bếp, tôi muốn nhận danh sách món ăn gợi ý được chia rành mạch giữa nhóm **"Nấu được ngay"** (`availability = 'ready'`) và nhóm **"Còn thiếu nguyên liệu"** (`availability = 'missing'`), hiển thị rõ điểm hợp nhất, nguyên liệu đã khớp, nguyên liệu/gia vị bắt buộc còn thiếu và giải thích tiếng Việt (`explanation_vi`) để chọn ngay được món phù hợp.

**Acceptance Scenarios**:
1. **Given** người dùng đã xác nhận đủ nguyên liệu bắt buộc cho một món và chưa tắt gia vị bắt buộc nào (`TC-10`), **When** gọi `POST /api/v1/recommendations`, **Then** món đó nằm trong khu vực **"Nấu được ngay"** (`availability = 'ready'`, xếp trước nhóm `missing`), hiển thị badge đã khớp và điểm hợp nhất `0–100`.
2. **Given** công thức thiếu nguyên liệu chính hoặc người dùng tắt gia vị bắt buộc trên thanh pantry (`excluded_pantry_ids`, `TC-11`, `TC-32`), **When** nhận kết quả gợi ý, **Then** món đó nằm trong khu vực **"Còn thiếu nguyên liệu"** (`availability = 'missing'`) và liệt kê rõ từng nguyên liệu/gia vị cần chuẩn bị thêm.
3. **Given** không có công thức nào khớp hoặc bộ lọc quá hẹp (`TC-34`), **When** API trả `items = []`, **Then** giao diện hiển thị trạng thái rỗng trung thực kèm gợi ý điều chỉnh bộ lọc, tuyệt đối không bịa món.

---

### User Story 2 - Tùy chọn Nguyên liệu chính, Thời gian mong muốn & Bộ lọc Ngữ cảnh (`FR-07`, `ADR-013`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn tùy chọn (hoặc bỏ qua) các **nguyên liệu muốn ưu tiên làm món chính (`main_ingredient_ids`)** và **thời gian nấu mong muốn (`desired_hours`)**, đồng thời lọc kết quả theo nền ẩm thực (`cuisine_codes`), thời gian tối đa (`max_total_minutes`), chế độ **chỉ xem món nấu ngay (`include_missing = false`)** và **đa dạng hóa thực đơn (`diversify = true`)**.

**Acceptance Scenarios**:
1. **Given** người dùng bỏ qua chọn món chính và thời gian mong muốn (`TC-12`), **When** bấm *"Gợi ý món ăn"*, **Then** hệ thống giữ giá trị mặc định an toàn (`main_ingredient_ids = []`, `desired_hours = 100.0`).
2. **Given** người dùng đánh dấu ưu tiên một hoặc nhiều nguyên liệu chính và chọn mốc thời gian mong muốn (ví dụ `15 phút` → `desired_hours = 0.25`, `TC-35`), **When** gửi yêu cầu gợi ý, **Then** payload gửi đúng `main_ingredient_ids` (tập con của `ingredient_ids`) và `desired_hours`, làm cập nhật tức thì điểm `G` và `T` trong kết quả trả về.
3. **Given** người dùng bật *"Chỉ hiện món nấu được ngay"* (`include_missing = false`, `TC-33`) hoặc lọc `cuisine_codes = ['VN']` (`TC-13`) / `max_total_minutes <= 15` (`TC-14`) / bật `diversify = true` (`DEF-10`), **When** kết quả cập nhật, **Then** chỉ các món thỏa ràng buộc được hiển thị.

---

### User Story 3 - Trang Chi tiết Công thức Tách Bếp & Thời gian (`FR-02`, `BR-05`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn bấm mở chi tiết bất kỳ công thức nào từ **Danh mục tra cứu** hoặc **Danh sách gợi ý** để xem hướng dẫn đầy đủ theo phong cách editorial **NEWTASTE**: thời gian sơ chế (`prep_minutes`), thời gian nấu & chờ (`cook_minutes`), tổng thời gian (`total_minutes`), danh sách **Nguyên liệu** (`category !== 'pantry'`) tách biệt khỏi **Gia vị cần chuẩn bị** (`category === 'pantry'`), các bước chế biến đánh số thứ tự (`steps`) và nguồn tham khảo (`source_name`, `source_url`, `content_license`).

**Acceptance Scenarios**:
1. **Given** người dùng chọn một công thức bất kỳ, **When** gọi `GET /api/v1/recipes/{recipe_id}`, **Then** trang chi tiết hiển thị đầy đủ thời gian (`prep_minutes`, `cook_minutes` kèm lưu ý bao gồm cả thời gian ướp/chờ theo `BR-05`, `total_minutes`), tách rõ cột **Nguyên liệu** và cột **Gia vị cần chuẩn bị**, cùng các bước chế biến theo thứ tự `step_no` (`TC-03`).
2. **Given** mã `recipe_id` không tồn tại hoặc đang ở trạng thái `draft`, **When** API trả `404 RECIPE_NOT_FOUND`, **Then** hiển thị thông báo tiếng Việt thân thiện kèm nút quay lại màn hình trước đó mà không mất bộ lọc/danh sách đã chọn.

---

### User Story 4 - Nhãn Dinh dưỡng Định tính & Tuyên bố Miễn trừ Bắt buộc (`FR-08`, `BR-03`, `TC-15`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn xem các **nhãn dinh dưỡng định tính** (kèm liên kết nguồn dẫn chứng `source_urls`) nếu công thức đã được kiểm duyệt gắn nhãn, không bao giờ thấy số `kcal`/`gram` suy diễn từ ảnh, và luôn nhìn thấy rõ **Tuyên bố miễn trừ trách nhiệm dinh dưỡng & dị ứng bắt buộc**.

**Acceptance Scenarios**:
1. **Given** công thức có `nutrition_evidence` hoặc có mảng rỗng `[]` (`TC-15`), **When** hiển thị trang chi tiết, **Then** các tag có liên kết `source_urls` mở tab mới an toàn (hoặc thông báo chưa có nhãn định tính nếu mảng rỗng), không suy diễn `kcal`/`gram`, và luôn hiển thị nguyên văn tuyên bố miễn trừ `BR-03`.

---

## Mandatory Verbatim Disclaimer (`BR-03`)

> Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu (ước tính khi có khối lượng chuẩn), không suy diễn từ ảnh chụp, không thay thế tư vấn y tế và người dùng cần tự kiểm tra thành phần dị ứng thực phẩm.
