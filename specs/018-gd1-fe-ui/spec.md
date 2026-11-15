# Feature Specification: Giao diện Tra cứu Công thức, Tìm kiếm Nguyên liệu Tiếng Việt & Thanh 5 Gia vị Pantry (GĐ1 - UI)

**Feature Branch**: `feat/018-gd1-fe-ui`

**Created**: 2026-11-04

**Status**: Approved (`0.9.1-draft` baseline)

**Input**: User description: "Thẻ #18 [GĐ1 - UI] (TV3 — Tâm Minh): Dựng khung Frontend, Giao diện Tra cứu Công thức (FR-01), Tìm kiếm Nguyên liệu Tiếng Việt dự phòng (FR-18) & Thanh 5 Gia vị Pantry (FR-05), đáp ứng responsive 360px/768px/1366px (NFR-01, NFR-12)."

**Authoritative References (`docs/`)**:
- `docs/01-requirements/SRS.md`: `FR-01`, `FR-05`, `FR-18`, `NFR-01`, `NFR-12`, `BR-04`, `BR-07`, `BR-12`
- `docs/01-requirements/user-stories.md`: `US-01` (`AC-01`, `AC-02`), `US-04` (`AC-07`, `AC-08`)
- `docs/01-requirements/use-cases.md`: `UC-01`, `UC-03`
- `docs/03-api/openapi.yaml`: `GET /api/v1/recipes`, `GET /api/v1/ingredients`
- `docs/06-testing/test-cases.md`: `TC-01`, `TC-02`, `TC-08`, `TC-09`, `TC-27`, `TC-31`, `TC-36`, `UI-01`..`UI-03`, `DEF-04`, `DEF-06`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tra cứu và Khám phá Công thức Món ăn (`US-01` / `FR-01`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn tìm kiếm và lọc danh sách các công thức món ăn đã được kiểm duyệt (`published`) theo từ khóa tiếng Việt (có dấu hoặc không dấu), nhóm ẩm thực (`VN`, `EU`, `US`) và tổng thời gian chế biến tối đa (`<= 15 phút`, `<= 30 phút`, `<= 60 phút`) kèm phân trang để nhanh chóng khám phá món ăn phù hợp.

**Why this priority**: Đây là luồng khám phá cơ bản nhất của hệ thống (`UC-01`), giúp người dùng tra cứu kho tri thức món ăn ngay cả khi chưa tải ảnh hoặc chọn nguyên liệu, đồng thời kiểm chứng khả năng kết nối danh mục công thức chuẩn.

**Independent Test**: Có thể kiểm thử độc lập bằng cách mở màn hình *Khám phá Công thức*, nhập từ khóa không dấu `"trung"`, chọn ẩm thực `"Việt Nam (VN)"` và bộ lọc thời gian `"<= 15 phút"`, xác nhận danh sách chỉ hiển thị các món thỏa mãn điều kiện (ví dụ *"Trứng xào cà chua"*, `total_minutes = 13`) và hỗ trợ chuyển trang.

**Acceptance Scenarios**:

1. **Given** kho dữ liệu có công thức *"Trứng xào cà chua"* (`published`, `VN`, `total_minutes = 13`), *"Bò hầm rượu vang"* (`published`, `EU`, `total_minutes = 110`) và món nháp *"Canh chua cá"* (`draft`), **When** người dùng nhập từ khóa `"trung"`, chọn ẩm thực `"VN"` và thời gian tối đa `"<= 15 phút"`, **Then** màn hình chỉ hiển thị *"Trứng xào cà chua"* cùng tổng thời gian `13 phút` và không hiển thị món `draft` hay món vượt quá 15 phút (`AC-01`, `TC-01`, `TC-02`).
2. **Given** danh sách kết quả có nhiều hơn số món trên một trang (`total > limit`), **When** người dùng chuyển sang trang tiếp theo, **Then** giao diện cập nhật danh sách món đúng với vị trí phân trang (`limit`, `offset`, `total`) mà không làm mất bộ lọc hiện tại (`AC-02`).

---

### User Story 2 - Tìm kiếm Tiếng Việt và Chọn Nguyên liệu Chính Thủ công (`US-04` / `FR-18`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn truy cập màn hình chọn nguyên liệu thủ công để tìm kiếm nguyên liệu chính theo tên tiếng Việt có dấu, không dấu hoặc từ đồng nghĩa vùng miền (`đậu hũ`/`đậu phụ`, `bắp`/`ngô`, `dưa leo`/`dưa chuột`, `thịt heo`/`thịt lợn`), thêm/xóa nguyên liệu vào danh sách hiện có với cơ chế tự động chống trùng lặp, và chỉ cho phép bấm *"Gợi ý món ăn"* khi đã có ít nhất 1 nguyên liệu chính.

**Why this priority**: Luồng chọn nguyên liệu thủ công (`FR-18`, `UC-03`) vừa là công cụ chỉnh sửa Human-in-the-Loop (`FR-05`), vừa là đường dự phòng bắt buộc khi người dùng không dùng ảnh hoặc khi dịch vụ AI trả `detections = []` / lỗi `503` / `504`.

**Independent Test**: Mở màn hình *Chọn Nguyên Liệu & Gợi Ý*, gõ `"dau phu"` hoặc `"bap"`, chọn nguyên liệu gợi ý từ danh sách thả xuống, thử chọn lại cùng nguyên liệu đó để kiểm tra khử trùng lặp, sau đó xóa hết nguyên liệu để kiểm tra trạng thái khóa nút *"Gợi ý món ăn"*.

**Acceptance Scenarios**:

1. **Given** người dùng đang ở ô tìm kiếm nguyên liệu chính (`exclude_pantry = true`), **When** người dùng nhập từ khóa không dấu `"ca chua"` hoặc từ đồng nghĩa vùng miền `"dau phu"`, **Then** danh sách gợi ý hiển thị đúng nguyên liệu chuẩn tương ứng (*"Cà chua"*, *"Đậu hũ"*) và không bao giờ hiển thị các gia vị nền thuộc nhóm `pantry` (`AC-07`, `TC-36`, `DEF-06`).
2. **Given** danh sách nguyên liệu chính đã chọn đang có *"Cà chua"*, **When** người dùng chọn thêm *"Cà chua"* một lần nữa từ ô tìm kiếm, **Then** hệ thống giữ nguyên 1 thẻ *"Cà chua"* duy nhất (không tạo phần tử trùng lặp trong `ingredient_ids`) (`AC-08`, `TC-08`).
3. **Given** danh sách nguyên liệu chính đang trống (`ingredient_ids = []`), **When** người dùng quan sát khu vực hành động gợi ý món, **Then** nút *"Gợi ý món ăn"* bị vô hiệu hóa kèm thông báo nhắc chọn tối thiểu 1 nguyên liệu chính (`AC-08`, `TC-09`).

---

### User Story 3 - Bật/Tắt Thanh 5 Gia vị Sẵn có trong Bếp (`US-04` / `FR-05` / `ADR-008`) (Priority: P1)

Là khách hoặc người dùng, tôi muốn thấy thanh **"Gia vị sẵn có trong bếp"** hiển thị 5 gia vị nền cơ bản (**Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu**) mặc định được bật sẵn (`checked`), và có thể bỏ chọn những gia vị đang hết trong bếp để hệ thống ghi nhận vào danh sách gia vị báo thiếu (`excluded_pantry_ids`).

**Why this priority**: Phản ánh đúng thực tế gian bếp (`ADR-008`, `BR-04`): người dùng không chụp ảnh từng lọ muối/nước mắm nhưng nếu trong bếp hết nước mắm thì cần tắt đi để hệ thống không xếp món cần nước mắm vào nhóm *"Nấu được ngay"*.

**Independent Test**: Quan sát thanh 5 gia vị nền khi mới mở trang (tất cả đều bật → `excluded_pantry_ids = []`), bấm tắt *"Nước mắm"* và xác nhận trạng thái chuẩn bị gửi gợi ý ghi nhận đúng mã định danh của *"Nước mắm"* vào `excluded_pantry_ids`.

**Acceptance Scenarios**:

1. **Given** người dùng mở màn hình chọn nguyên liệu lần đầu, **When** thanh *"Gia vị sẵn có trong bếp"* được hiển thị, **Then** cả 5 gia vị nền (*Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) đều ở trạng thái bật (`checked`) và danh sách gia vị báo thiếu `excluded_pantry_ids` là mảng rỗng `[]` (`AC-08`, `TC-31`).
2. **Given** người dùng đã chọn *"Cà chua"* và *"Trứng gà"* làm nguyên liệu chính, **When** người dùng bỏ chọn gia vị *"Nước mắm"* trên thanh gia vị nền, **Then** trạng thái đầu vào chuẩn bị cho bộ gợi ý có `ingredient_ids = [ca_chua_id, trung_ga_id]` và `excluded_pantry_ids = [nuoc_mam_id]` (`AC-08`, `DEF-04`).

---

### User Story 4 - Điều hướng Chung & Trải nghiệm Đa Thiết bị (`NFR-01` / `NFR-12`) (Priority: P2)

Là khách hoặc người dùng truy cập trên điện thoại (`360px`), máy tính bảng (`768px`) hoặc máy tính để bàn (`1366px`), tôi muốn có thanh điều hướng rõ ràng giữa các khu vực chức năng chính (*Chọn Nguyên Liệu / Quét Ảnh* và *Khám Phá Công Thức*) với hiển thị tiếng Việt chuẩn xác, không bị vỡ khung hay tràn ngang.

**Why this priority**: Đảm bảo tiêu chuẩn khả dụng bắt buộc `NFR-01` và `NFR-12` (`UI-01`..`UI-03`) cho toàn bộ các giai đoạn tiếp theo.

**Independent Test**: Thay đổi kích thước khung nhìn trình duyệt ở `360px`, `768px`, `1366px` và chuyển đổi qua lại giữa các trang trên thanh điều hướng.

**Acceptance Scenarios**:

1. **Given** người dùng mở ứng dụng trên màn hình di động `360px`, tablet `768px` hoặc desktop `1366px`, **When** người dùng thao tác tìm kiếm công thức, chọn nguyên liệu chính và bật/tắt thanh 5 gia vị nền, **Then** mọi thành phần giao diện hiển thị đầy đủ tiếng Việt có dấu, nút bấm dễ thao tác và không xuất hiện thanh cuộn ngang ngoài ý muốn (`UI-01`, `UI-03`).

---

### Edge Cases

- **Không tìm thấy công thức hoặc nguyên liệu khớp từ khóa**: Hiển thị trạng thái trống (Empty State) thân thiện bằng tiếng Việt kèm nút xóa nhanh bộ lọc hoặc gợi ý thử từ khóa khác.
- **Người dùng xóa hết nguyên liệu chính sau khi đã chọn**: Nút *"Gợi ý món ăn"* tự động chuyển sang trạng thái khóa (`disabled`) ngay lập tức và hiển thị chỉ dẫn rõ ràng (`FR-05`, `AC-08`).
- **Người dùng tắt toàn bộ 5 gia vị nền**: Hệ thống cho phép tắt cả 5 gia vị (`excluded_pantry_ids` chứa đủ 5 UUID) và hiển thị nút *"Khôi phục mặc định (Đủ 5 gia vị)"* để bật lại nhanh.
- **Máy chủ API đang khởi động hoặc chưa kết nối trong môi trường phát triển độc lập**: Hiển thị thông báo lỗi rõ ràng theo chuẩn mã lỗi tiếng Việt hoặc cho phép chạy với dữ liệu mẫu chuẩn (Mock/Fallback) khớp đúng hợp đồng dữ liệu để kiểm thử giao diện độc lập.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-FE-001 (`FR-01`, `AC-01`, `AC-02`)**: Giao diện **PHẢI** cung cấp màn hình Tra cứu & Khám phá công thức chỉ hiển thị các món `published`, hỗ trợ tìm kiếm theo từ khóa `q` (tiếng Việt có dấu/không dấu), lọc theo nhóm ẩm thực `cuisine_code` (`Tất cả`, `VN`, `EU`, `US`), lọc theo tổng thời gian tối đa `max_total_minutes` (`Tất cả`, `<= 15 phút`, `<= 30 phút`, `<= 60 phút`) và phân trang (`limit`, `offset`, `total`).
- **FR-FE-002 (`FR-05`, `FR-18`, `AC-07`, `AC-08`)**: Giao diện **PHẢI** cung cấp ô tìm kiếm và chọn nguyên liệu chính thủ công kết nối danh mục nguyên liệu hoạt động (`is_active = true`, `exclude_pantry = true`), hỗ trợ tìm tiếng Việt có dấu, không dấu và từ đồng nghĩa vùng miền (`đậu hũ`/`đậu phụ`, `bắp`/`ngô`, `dưa leo`/`dưa chuột`, `thịt heo`/`thịt lợn`).
- **FR-FE-003 (`FR-05`, `AC-08`, `BR-07`)**: Giao diện **PHẢI** tự động khử trùng lặp theo `ingredient_id` khi người dùng chọn thêm nguyên liệu đã có trong danh sách `ingredient_ids`, cho phép xóa từng nguyên liệu hoặc xóa tất cả, và khóa nút *"Gợi ý món ăn"* khi `ingredient_ids` rỗng.
- **FR-FE-004 (`FR-05`, `ADR-008`, `BR-04`, `BR-12`)**: Giao diện **PHẢI** hiển thị thanh **"Gia vị sẵn có trong bếp"** gồm đúng 5 gia vị nền (`category = 'pantry'`: *Muối, Đường, Nước mắm, Dầu ăn, Hạt tiêu*) mặc định ở trạng thái bật (`checked`), tách biệt hoàn toàn với danh sách nguyên liệu chính, và tự động đưa UUID của các gia vị bị người dùng bỏ chọn vào mảng `excluded_pantry_ids`.
- **FR-FE-005 (`NFR-01`, `NFR-12`)**: Khung ứng dụng **PHẢI** có bố cục điều hướng rõ ràng, hiển thị tiếng Việt UTF-8 chuẩn xác và đáp ứng tốt (responsive) ở cả 3 mốc kích thước màn hình `360px`, `768px` và `1366px`.

### Key Entities

- **Nguyên liệu (`Ingredient`)**: Đại diện cho thực phẩm hoặc gia vị trong hệ thống, gồm định danh `id` (UUID), tên tiếng Việt `name_vi`, đường dẫn tĩnh `slug`, phân nhóm `category` (`vegetable`, `protein`, `seafood`, `spice`, `pantry`, `other`) và danh sách tên gọi đồng nghĩa vùng miền.
- **Công thức tóm tắt (`RecipeSummary`)**: Đại diện cho món ăn đã kiểm duyệt trên màn hình tra cứu, gồm `id`, `title_vi`, `slug`, `cuisine_code` (`VN` | `EU` | `US`), `prep_minutes`, `cook_minutes`, `total_minutes`, `servings` và ảnh minh họa `image_url`.
- **Trạng thái Đầu vào Bếp của Người dùng (`KitchenSelectionState`)**: Bao gồm tập nguyên liệu chính đã xác nhận `ingredient_ids` (`category != 'pantry'`, tối thiểu 1 phần tử khi gửi gợi ý), tập gia vị nền báo thiếu `excluded_pantry_ids` (`category = 'pantry'`, mặc định `[]`) và các bộ lọc tìm kiếm/gợi ý.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng có thể tìm thấy và lọc công thức món ăn theo từ khóa tiếng Việt (có dấu hoặc không dấu), nhóm ẩm thực (`VN`/`EU`/`US`) và mốc thời gian (`<= 15 phút`) chỉ trong tối đa 3 thao tác với kết quả hiển thị dưới 1 giây.
- **SC-002**: 100% thao tác tìm kiếm nguyên liệu bằng tên không dấu hoặc phương ngữ vùng miền phổ biến (*đậu phụ, ngô, dưa chuột, thịt lợn*) trả về đúng nguyên liệu chuẩn và không bao giờ trộn lẫn 5 gia vị nền (`pantry`) vào danh sách nguyên liệu chính.
- **SC-003**: 100% các trường hợp kiểm thử trong `AC-01`, `AC-02`, `AC-07`, `AC-08` (`TC-01`, `TC-02`, `TC-08`, `TC-09`, `TC-27`, `TC-31`, `TC-36`, `DEF-04`, `DEF-06`) tạo ra trạng thái dữ liệu đầu vào (`ingredient_ids`, `excluded_pantry_ids`, bộ lọc) khớp tuyệt đối với đặc tả.
- **SC-004**: Giao diện hiển thị không bị tràn ngang hay che khuất nút chức năng trên cả 3 độ rộng màn hình chuẩn `360px`, `768px` và `1366px` (`UI-01`..`UI-03`).

## Assumptions

- Trong thời gian chờ Backend API (`Thẻ #6` của `TV2`) hoàn tất hoặc khi chạy môi trường phát triển Frontend độc lập, ứng dụng hỗ trợ lớp dữ liệu mẫu dự phòng (Fallback/Mock Data) bám sát 100% cấu trúc dữ liệu của `docs/03-api/openapi.yaml` và `docs/04-ai-model/label-catalog.md` (20 nguyên liệu chính + 5 gia vị `pantry` + các cặp từ đồng nghĩa vùng miền + bộ công thức mẫu Việt/Âu/Mỹ) để có thể kiểm thử giao diện tức thì.
- Màn hình hiển thị danh sách kết quả chấm điểm gợi ý (`POST /api/v1/recommendations`) và trang Chi tiết công thức (`GET /api/v1/recipes/{id}`) sẽ được hoàn thiện đầy đủ ở **Thẻ `#11` (`[GĐ2 - UI]`)**; ở **Thẻ `#18` (`[GĐ1 - UI]`)**, trạng thái `ingredient_ids` và `excluded_pantry_ids` đã được chuẩn bị đầy đủ và sẵn sàng truyền sang luồng gợi ý của Giai đoạn 2.
