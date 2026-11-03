# SRS — Đặc tả yêu cầu phần mềm (rút gọn nhưng triển khai được)

**Mã:** FV-SRS-001 · **Phiên bản:** 1.0.0 · **Ngày:** 03/11/2026 · **Trạng thái:** Đề xuất, chờ duyệt.  
**Người duyệt:** Giảng viên phụ trách / nhóm dự án (chưa xác nhận).  
**Liên kết:** [Use Cases](use-cases.md) · [User Stories](user-stories.md) · [Traceability](traceability-matrix.md)

## 1. Giới thiệu

### 1.1. Bối cảnh và vấn đề

Người nấu ăn có nguyên liệu tại nhà nhưng thiếu ý tưởng món phù hợp. Việc tìm công thức theo văn bản mất thời gian và không tận dụng được ảnh. **Tên đề tài đề xuất:** "Xây dựng website thông minh gợi ý món ăn từ hình ảnh nguyên liệu sử dụng YOLO". FoodVision AI cung cấp công cụ Web giúp nhận diện nguyên liệu từ ảnh, cho phép chỉnh sửa sai sót và gợi ý công thức dựa trên các nguyên liệu thực tế.

### 1.2. Mục tiêu có thể kiểm chứng

- Mục tiêu G-01: dùng ảnh chứa nhiều loại nguyên liệu để tạo danh sách nguyên liệu có thể chỉnh sửa.
- Mục tiêu G-02: gợi ý các món có thể làm ngay và các món còn thiếu nguyên liệu, giải thích điểm xếp hạng.
- Mục tiêu G-03: phân loại món Việt/Âu/Mỹ, hiển thị thời gian sơ chế/nấu và hướng dẫn theo bước; hỗ trợ tìm món nhanh 10–15 phút nếu dữ liệu công thức hợp lệ.
- Mục tiêu G-04: tách rõ API, database và AI, có kiểm thử chất lượng nhận diện/gợi ý cùng bản trình diễn Web.
- Mục tiêu G-05: thể hiện nhóm thành phần dinh dưỡng ở mức **định tính có nguồn**, không suy diễn khối lượng, kcal hoặc g protein từ ảnh.

### 1.3. Phạm vi

**MVP gồm:** (1) trang tìm và xem công thức, (2) tải/chụp ảnh, (3) nhiều bounding box + độ tin cậy, (4) danh sách nguyên liệu đã xác nhận, (5) thuật toán gợi ý dựa trên công thức và bộ lọc, (6) Supabase Auth cho lưu yêu thích, (7) CMS đơn giản cho Admin, (8) thử nghiệm AI và thuật toán.

**Ngoài phạm vi:** điều trị/chẩn đoán dinh dưỡng, dị ứng được bảo đảm 100%, suy ra gram từ ảnh, tự đặt thực phẩm, chat AI, livestream camera, app Android/iOS native, thanh toán, OCR hóa đơn.

### 1.4. Tác nhân và quyền

| Tác nhân | Diễn giải | Quyền |
|---|---|---|
| Guest (khách) | Chưa đăng nhập | Xem món, upload ảnh, gợi ý, chỉnh sửa nguyên liệu cục bộ; không lưu lịch sử/yêu thích |
| User | Đăng nhập Supabase Auth | Toàn bộ quyền Guest; lưu món yêu thích, gửi đánh giá, tùy chọn lưu lịch sử kết quả nhận diện |
| Admin | User có vai trò được cấp **từ server** | Quản lý nguyên liệu, công thức, nhãn ánh xạ AI, nội dung dinh dưỡng; xem log thao tác |
| AI Inference Service | Thành phần nội bộ | Nhận ảnh, trả nhãn/bbox/confidence; **không tự chọn món** |

### 1.5. Quy trình nghiệp vụ chính

1. Guest/User chọn ảnh JPG/PNG/WebP (≤5 MB). Backend kiểm tra dung lượng, MIME thực, kích thước và giải mã an toàn.
2. YOLO trả danh sách đối tượng: nhãn, confidence, bounding box; backend ánh xạ phiên bản nhãn → `ingredients.id`.
3. Giao diện hiển thị các nguyên liệu đã gộp trùng; người dùng **thêm/xóa/sửa** nguyên liệu. Chỉ danh sách sau xác nhận được đưa vào hệ gợi ý.
4. Người dùng chọn tối đa thời gian nấu và nhóm ẩm thực (nếu muốn); backend tìm công thức đang công bố và chấm điểm theo thiết kế [recommendation-design.md](../05-recommendation/recommendation-design.md).
5. Hiển thị **Nhóm A — có đủ nguyên liệu bắt buộc** trước **Nhóm B — còn thiếu** (nếu người dùng cho phép); mỗi món có điểm, nguyên liệu còn thiếu, thời gian và lý do xếp hạng.
6. Người dùng xem chi tiết công thức và nhóm dinh dưỡng định tính. User có thể lưu yêu thích/gửi phản hồi và xem/xóa lịch sử đã tự chọn lưu.

## 2. Yêu cầu chức năng (FR)

**Ưu tiên:** P0 = bắt buộc MVP; P1 = làm sau luồng cốt lõi trong đồ án; P2 = mở rộng.  
**Nghiệm thu:** mỗi FR có ít nhất một TC liên kết ở [traceability-matrix.md](traceability-matrix.md).

| ID | Vai trò | Yêu cầu có thể kiểm thử | Ưu tiên |
|---|---|---|---|
| FR-01 | Guest/User | Tra cứu danh sách món theo từ khóa, nhóm ẩm thực, tổng thời gian | P0 |
| FR-02 | Guest/User | Xem chi tiết món: nguyên liệu, bắt buộc/tùy chọn, sơ chế, nấu, bước, nguồn | P0 |
| FR-03 | Guest/User | Tải 1 ảnh JPEG/PNG/WebP ≤5 MB; báo lỗi rõ khi ảnh không hợp lệ | P0 |
| FR-04 | Guest/User | Nhận diện **nhiều** đối tượng nguyên liệu, hiển thị confidence và bbox | P0 |
| FR-05 | Guest/User | Xác nhận và thêm/sửa/xóa nguyên liệu, gộp trùng, không buộc theo dự đoán AI | P0 |
| FR-06 | Guest/User | Nhận danh sách món được tính điểm, xếp hạng; giải thích nguyên liệu có/thiếu | P0 |
| FR-07 | Guest/User | Lọc/ưu tiên nhóm món Việt, Âu, Mỹ và thời gian (bao gồm ≤15 phút) | P0 |
| FR-08 | Guest/User | Xem thông tin **nhóm chất dinh dưỡng định tính** có dẫn nguồn, cảnh báo hạn chế | P0 |
| FR-09 | User | Đăng ký/đăng nhập/đăng xuất qua Supabase Auth | P1 |
| FR-10 | User | Thêm/bỏ/xem danh sách món yêu thích; chỉ thấy dữ liệu của mình | P1 |
| FR-11 | User | Gửi đánh giá mức hữu ích (1–5) cho món gợi ý | P1 |
| FR-12 | User | Chọn lưu hoặc không lưu; xem và xóa lịch sử **kết quả** nhận diện của mình; mặc định **không lưu** | P1 |
| FR-13 | Admin | Tạo/sửa/ẩn/công bố món, các bước nấu và nguyên liệu tương ứng | P0 |
| FR-14 | Admin | Quản lý danh mục nguyên liệu, tên đồng nghĩa, trạng thái hoạt động | P0 |
| FR-15 | Admin | Quản lý phiên bản mô hình và ánh xạ class YOLO → nguyên liệu; không tự động huấn luyện | P1 |
| FR-16 | Admin | Quản lý nhãn dinh dưỡng và căn cứ nguồn, không cho phép khẳng định số gram khi thiếu dữ liệu | P1 |
| FR-17 | Admin | Xem nhật ký thay đổi dữ liệu quan trọng | P1 |
| FR-18 | Guest/User | Khi ảnh không nhận diện được, vẫn nhập thủ công và dùng chức năng gợi ý | P0 |

**Ràng buộc FR quan trọng:** chức năng nhận diện không bảo đảm mọi nhãn và không thay thế xác nhận người dùng. Công thức phải có tối thiểu một nguyên liệu bắt buộc và một bước hướng dẫn trước khi chuyển sang `published`.

## 3. Yêu cầu phi chức năng (NFR)

| ID | Yêu cầu / mục tiêu kiểm chứng | Phương pháp |
|---|---|---|
| NFR-01 | Web responsive, hỗ trợ Chrome/Edge/Firefox phiên bản hiện hành; mobile browser ≥360px | UI test ở 360/768/1366px |
| NFR-02 | Với ảnh hợp lệ ≤5 MB, API nhận diện có **mục tiêu** p95 ≤10s trên cấu hình benchmark đã công bố | 30+ lượt đo, ghi CPU/GPU, model, kích thước ảnh |
| NFR-03 | API gợi ý **mục tiêu** p95 ≤1s với tập 500 công thức, không tính AI | Load test + log |
| NFR-04 | Bảo vệ vai trò Admin cả tại server; JWT phải được xác minh; không tin role do client gửi | Kiểm thử 401/403 và cấp quyền |
| NFR-05 | Bảng public có kiểm soát GRANT + RLS khi sử dụng Supabase Data API | Kiểm thử RLS bằng 2 tài khoản và anon |
| NFR-06 | Không lưu ảnh gốc ở MVP; lịch sử kết quả AI chỉ lưu khi User chủ động chọn | Kiểm thử Storage/DB và quyền riêng tư |
| NFR-07 | Không công bố kcal/protein/chất béo theo gram từ 1 ảnh không có khối lượng xác thực | Review nội dung và API |
| NFR-08 | Mọi API có lỗi chuẩn `code`, `message`, `details`, `request_id` | Contract test |
| NFR-09 | Tất cả input được validate; image type qua magic bytes; giới hạn request, chống file giả | Security & negative tests |
| NFR-10 | Có OpenAPI và bảng dữ liệu cập nhật cùng code; CI hoặc lệnh local xác thực OpenAPI | Review PR, schema validation |
| NFR-11 | Đánh giá YOLO trên test độc lập, công bố Precision/Recall/mAP50/mAP50-95, confusion/error cases | Báo cáo eval, không giả định kết quả |
| NFR-12 | Không sử dụng tài sản ảnh/công thức/model trái giấy phép; quản lý nguồn và ghi công | Checklist license/attribution |

**Mục tiêu NFR-02/03 là kỳ vọng thiết kế, không phải kết quả đã đo.** Nếu phần cứng/bộ dữ liệu thay đổi, benchmark phải được làm lại và điều chỉnh tiêu chí qua PR.

## 4. Quy tắc nghiệp vụ (BR)

- **BR-01:** chỉ `recipes.status = published` mới xuất hiện trong API công khai.
- **BR-02:** nguyên liệu tên đồng nghĩa phải quy về mã chuẩn `ingredients.id` trước khi tính điểm; phải xử lý trùng lặp.
- **BR-03:** nguồn sự thật cho gợi ý là danh sách `ingredient_ids` **sau xác nhận**, không phải nhãn YOLO chưa duyệt.
- **BR-04:** món chỉ thuộc nhóm "nấu được ngay" khi có **100% nguyên liệu bắt buộc**; nguyên liệu tùy chọn không ngăn vào nhóm này.
- **BR-05:** khi lọc thời gian tối đa, dùng `total_minutes = prep_minutes + cook_minutes` theo dữ liệu công thức đã duyệt; nếu thiếu thời gian không được gắn nhãn ≤15 phút.
- **BR-06:** mỗi công thức có `cuisine_code` trong VN/EU/US; EU là nhóm giao diện rộng, có thể bổ sung `country_code` về sau; không coi mọi món châu Âu đồng nhất.
- **BR-07:** nhãn chất dinh dưỡng chỉ đưa ra khi nguồn dữ liệu đáng tin cậy; không diễn giải thành khuyến nghị y khoa.
- **BR-08:** người dùng được dùng tính năng chính khi không đăng nhập; đăng nhập chỉ yêu cầu cho yêu thích, feedback, xem/lưu/xóa lịch sử.
- **BR-09:** không có kết quả AI ⇒ cho nhập thủ công; không có món phù hợp ⇒ hiển thị lý do và đề xuất bỏ bớt bộ lọc.
- **BR-10:** role Admin chỉ được cập nhật qua luồng quản trị có kiểm soát; client không được tự cập nhật role.

## 5. Dữ liệu đầu vào/đầu ra

| Chức năng | Đầu vào | Đầu ra |
|---|---|---|
| Detect | `multipart/form-data`: `file`, `save_history=false` | danh sách detection (label, confidence, bbox), nguyên liệu gợi ý đã chuẩn hóa, `scan_id` có thể null |
| Recommend | JSON: `ingredient_ids`, `max_total_minutes?`, `cuisine_codes?`, `include_missing`, `scan_id?` | nhóm `ready` / `missing`, điểm 0–100, lý do, `missing_ingredient_ids` |
| Recipe details | `recipe_id` | tên, quốc gia/nhóm, thời gian, steps, ingredients, nutrition tags, nguồn |
| Favorites | token người dùng + recipe ID | trạng thái đã lưu và danh sách riêng của chủ sở hữu |
| Admin CRUD | token Admin + dữ liệu hợp lệ | tài nguyên mới/cập nhật; ghi audit |

Chi tiết hợp đồng: [openapi.yaml](../03-api/openapi.yaml).

## 6. Giới hạn và phụ thuộc

1. Nhận diện nguyên liệu bị cắt, che khuất, dạng đã chế biến hoặc rất giống nhau có thể sai; phải có danh sách nhãn được hỗ trợ.
2. Không nhận định độ chính xác trước khi huấn luyện và đánh giá thực nghiệm.
3. Công thức dùng thông tin thời gian từ tác giả/nguồn hợp lệ, phải kiểm tra độ hợp lý trước khi công bố; **không hứa mọi món chỉ nấu trong 10–15 phút**.
4. Không được sao chép nguyên văn công thức/hình ảnh có bản quyền khi không có quyền sử dụng. Nguồn tham khảo riêng tại [references.md](../references.md).
5. Quyết định license Ultralytics/YOLO phải được kiểm tra trước khi công khai hoặc thương mại hóa; xem ADR-005.

## 7. Quy trình phê duyệt baseline

- [ ] Nhóm xác nhận MVP, tính năng P0/P1 và số nhãn giai đoạn đầu.
- [ ] Giảng viên duyệt tên đề tài, phạm vi AI và bộ chỉ số đánh giá.
- [ ] Review Use Case, ERD, công thức xếp hạng và quyền dữ liệu.
- [ ] Chạy kiểm tra tính hợp lệ OpenAPI.
- [ ] Ghi nhận quyết định bằng PR/ADR; chuyển trạng thái tài liệu sang `Approved` sau khi được duyệt.
