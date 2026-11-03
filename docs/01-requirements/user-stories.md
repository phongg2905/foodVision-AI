# User Stories và Tiêu chí Chấp nhận (Gherkin Acceptance Criteria)

**Phiên bản:** `0.9.1-draft` · **Trạng thái:** Đề xuất (`Proposed`) · **Đối chiếu:** [SRS](SRS.md), [Use Cases](use-cases.md), [Traceability Matrix](traceability-matrix.md)

**Quy ước thiết kế:**
1. Mỗi User Story (`US-01`..`US-14`) ánh xạ trực tiếp tới các yêu cầu chức năng (`FR-01`..`FR-18`).
2. Mỗi khối Gherkin (`AC-01`..`AC-28`, trong đó tách `AC-19a`/`AC-19b` và `AC-22a`/`AC-22b`, tổng cộng **30 kịch bản AC nguyên tử**) tuân thủ nghiêm ngặt quy tắc **1 hành vi nguyên tử / 1 mệnh đề `When` duy nhất**. Các AC kiểm tra nhiều biến thể dữ liệu của cùng một hành vi sử dụng cấu trúc `Scenario Outline` + `Examples` (danh sách 10 khối dùng `Scenario Outline`: **`AC-06`, `AC-07`, `AC-08`, `AC-09`, `AC-20`, `AC-22a`, `AC-23`, `AC-24`, `AC-25`, `AC-27`**).

---

## 1. Danh sách User Stories (`US-01`..`US-14`)

| Mã US | User Story | FR liên quan | Ưu tiên | AC liên quan |
|---|---|---|---|---|
| **US-01** | Là khách/người dùng, tôi muốn tìm kiếm và lọc danh sách công thức theo từ khóa, nhóm ẩm thực và thời gian tối đa để nhanh chóng tìm được món ăn mong muốn. | `FR-01` | P0 | `AC-01`, `AC-02` |
| **US-02** | Là khách/người dùng, tôi muốn xem chi tiết nguyên liệu (tách rõ nguyên liệu chính và gia vị nền), thời gian sơ chế/nấu và từng bước hướng dẫn của công thức để chuẩn bị chế biến. | `FR-02` | P0 | `AC-03` |
| **US-03** | Là khách/người dùng, tôi muốn tải lên một bức ảnh nguyên liệu để hệ thống kiểm tra hợp lệ, tự động xoay đúng chiều hiển thị EXIF, xóa metadata GPS và nhận diện nhiều nguyên liệu kèm độ tin cậy. | `FR-03`, `FR-04` | P0 | `AC-04`, `AC-05`, `AC-06` |
| **US-04** | Là khách/người dùng, tôi muốn chỉnh sửa danh sách nguyên liệu AI gợi ý, nhập tay khi AI không nhận diện được, và bật/tắt các gia vị nền sẵn có trong bếp để danh sách đầu vào phản ánh đúng thực tế. | `FR-05`, `FR-18` | P0 | `AC-07`, `AC-08`, `AC-09` |
| **US-05** | Là khách/người dùng, tôi muốn nhận danh sách món ăn được chấm điểm, phân nhóm rõ món "nấu được ngay" (`ready`) và món "còn thiếu" (`missing`) kèm giải thích nguyên liệu/gia vị còn thiếu. | `FR-06` | P0 | `AC-10`, `AC-11`, `AC-12` |
| **US-06** | Là khách/người dùng, tôi muốn lọc cứng hoặc ưu tiên mềm theo nhóm ẩm thực Việt/Âu/Mỹ và giới hạn tổng thời gian (như `<= 15` phút) khi gợi ý món ăn. | `FR-07` | P0 | `AC-13` |
| **US-07** | Là khách/người dùng, tôi muốn xem thông tin nhóm chất dinh dưỡng định tính có dẫn nguồn rõ ràng và cảnh báo miễn trừ trách nhiệm để tham khảo an toàn. | `FR-08` | P0 | `AC-14` |
| **US-08** | Là người dùng hoặc quản trị viên, tôi muốn đăng ký, đăng nhập, khôi phục mật khẩu và đăng xuất cục bộ an toàn qua Supabase Auth. | `FR-09a`, `FR-09b` | P0 (`FR-09a`), P1 (`FR-09b`) | `AC-15`, `AC-16`, `AC-17` |
| **US-09** | Là người dùng đã đăng nhập, tôi muốn lưu, xem và bỏ lưu các công thức yêu thích của riêng mình mà người dùng khác không thể truy cập. | `FR-10` | P1 | `AC-18` |
| **US-10** | Là người dùng đã đăng nhập, tôi muốn gửi hoặc cập nhật đánh giá mức hữu ích (`1..5`) cho công thức gợi ý theo từng ngữ cảnh phiên quét hoặc duyệt tự do. | `FR-11` | P1 | `AC-20` |
| **US-11** | Là người dùng đã đăng nhập, tôi muốn chủ động chọn lưu hoặc không lưu lịch sử kết quả nhận diện, cũng như xem và xóa các phiên quét đã lưu của mình. | `FR-12` | P1 | `AC-19a`, `AC-19b` |
| **US-12** | Là quản trị viên, tôi muốn tạo, cập nhật và công bố công thức nấu ăn với cơ chế kiểm tra tự động nguyên liệu chính bắt buộc, trạng thái hoạt động và thời gian bước nấu. | `FR-13` | P0 | `AC-21`, `AC-22a`, `AC-22b` |
| **US-13** | Là quản trị viên, tôi muốn quản lý danh mục nguyên liệu chuẩn (bao gồm nhóm gia vị nền `pantry`) và tên đồng nghĩa, đồng thời ngăn chặn việc tắt hoặc đổi phân loại nguyên liệu đang được sử dụng. | `FR-14` | P0 | `AC-23`, `AC-24` |
| **US-14** | Là quản trị viên, tôi muốn quản lý phiên bản mô hình AI, ánh xạ nhãn YOLO, nhãn dinh dưỡng có nguồn và xem nhật ký kiểm toán hệ thống. | `FR-15`, `FR-16`, `FR-17` | P0 (`FR-15`), P1 (`FR-16`, `FR-17`) | `AC-25`, `AC-26`, `AC-27`, `AC-28` |

---

## 2. Định nghĩa Hoàn thành chung (Definition of Done — DoD)

Một User Story chỉ được coi là **Done** khi thỏa mãn toàn bộ các điều kiện sau:
1. Mã nguồn Backend/Frontend tuân thủ đúng hợp đồng [`openapi.yaml`](../03-api/openapi.yaml) và danh mục 20 mã lỗi trong [`api-conventions.md`](../03-api/api-conventions.md).
2. Các ràng buộc toàn vẹn dữ liệu và chính sách `RLS` tương ứng trong [`database-design.md`](../02-architecture/database-design.md) đã được áp dụng qua script migration.
3. Toàn bộ kịch bản Gherkin `AC-*` và các ca kiểm thử `TC-*` liên kết trong [`traceability-matrix.md`](traceability-matrix.md) đã được **thành viên kiểm thử chéo (Cross-Tester)** thực thi trên bản build xác định và đính kèm bằng chứng thực tế.
4. Giao diện hiển thị tiếng Việt có dấu chuẩn UTF-8, đáp ứng responsive ở `360px`, `768px`, `1366px` và không để lộ secret/token trong log.

---

## 3. Đặc tả Gherkin Acceptance Criteria (30 kịch bản nguyên tử)

### AC-01 — Tìm kiếm và lọc danh sách công thức công khai (`US-01`, `FR-01`, `TC-01`, `TC-02`)

```gherkin
Scenario: Tra cứu công thức đang published theo từ khóa, ẩm thực và tổng thời gian
  Given cơ sở dữ liệu có công thức "Trứng xào cà chua" (status="published", cuisine_code="VN", prep_minutes=5, cook_minutes=8)
  And công thức "Bò hầm rượu vang" (status="published", cuisine_code="EU", prep_minutes=20, cook_minutes=90)
  And công thức nháp "Canh chua cá" (status="draft", cuisine_code="VN", prep_minutes=10, cook_minutes=15)
  When người dùng gửi GET "/api/v1/recipes?q=trung&cuisine_code=VN&max_total_minutes=15&limit=20&offset=0"
  Then hệ thống trả HTTP 200 với mảng items chỉ chứa "Trứng xào cà chua" (total_minutes=13)
  And không trả công thức ở trạng thái "draft" hoặc vượt quá 15 phút
```

### AC-02 — Phân trang danh sách công thức (`US-01`, `FR-01`, `TC-01`)

```gherkin
Scenario: Phân trang kết quả tra cứu công thức theo limit và offset
  Given cơ sở dữ liệu có 15 công thức ở trạng thái "published"
  When người dùng gửi GET "/api/v1/recipes?limit=10&offset=10"
  Then hệ thống trả HTTP 200 với total=15, limit=10, offset=10 và mảng items có đúng 5 phần tử
```

### AC-03 — Xem chi tiết công thức và phân tách gia vị nền (`US-02`, `FR-02`, `TC-03`)

```gherkin
Scenario: Xem chi tiết công thức published có nguyên liệu chính và gia vị nền
  Given công thức "Trứng xào cà chua" đang ở trạng thái "published" có nguyên liệu "Trứng gà" (category="protein") và "Nước mắm" (category="pantry")
  When người dùng gửi GET "/api/v1/recipes/{recipe_id}" của công thức đó
  Then hệ thống trả HTTP 200 kèm prep_minutes, cook_minutes, total_minutes, steps[] và ingredients[]
  And mỗi phần tử trong ingredients[] có trường category để giao diện tách riêng khu vực "Gia vị cần chuẩn bị" (category="pantry")
```

### AC-04 — Tiền xử lý xoay ảnh EXIF Orientation và xóa metadata GPS (`US-03`, `FR-03`, `TC-04`, `TC-43`)

```gherkin
Scenario: Tải ảnh chụp dọc có cờ EXIF Orientation và metadata GPS
  Given người dùng chọn tệp ảnh JPEG hợp lệ dung lượng 1.5 MiB có cờ EXIF Orientation=6 (xoay 90 độ) và chứa tọa độ GPS
  When người dùng gửi POST "/api/v1/ai/detect" với file ảnh đó và save_history=false
  Then backend tự động xoay ảnh về đúng chiều hiển thị chuẩn (upright) và xóa sạch metadata EXIF/GPS trong bộ nhớ trước khi suy luận
  And hệ thống trả HTTP 200 với tọa độ bbox chuẩn hóa [0..1] khớp với chiều ảnh đã xoay và không lưu tệp ảnh gốc
```

### AC-05 — Nhận diện đa đối tượng và gộp trùng nguyên liệu gợi ý (`US-03`, `FR-04`, `TC-07`)

```gherkin
Scenario: Nhận diện nhiều đối tượng trong một ảnh và khử trùng lặp suggested_ingredients
  Given mô hình YOLO active phát hiện 2 hộp giới hạn "tomato" (confidence 0.92 và 0.81) và 1 hộp giới hạn "egg" (confidence 0.88)
  When người dùng gửi POST "/api/v1/ai/detect" với ảnh hợp lệ
  Then hệ thống trả HTTP 200 với mảng detections có 3 phần tử giữ nguyên từng bbox
  And mảng suggested_ingredients chỉ có 2 phần tử đã khử trùng lặp theo ingredient_id với max_confidence của "Cà chua" là 0.92
```

### AC-06 — Từ chối tệp tải lên không hợp lệ hoặc lỗi dịch vụ suy luận (`US-03`, `FR-03`, `FR-04`, `TC-05`, `TC-06`, `TC-29`, `TC-30`)

```gherkin
Scenario Outline: Trả đúng mã lỗi HTTP và error code khi tải ảnh lỗi hoặc dịch vụ AI gặp sự cố
  Given điều kiện đầu vào của yêu cầu nhận diện là "<tinh_huong>"
  When người dùng gửi POST "/api/v1/ai/detect"
  Then hệ thống trả HTTP <http_status> với mã lỗi "<error_code>" và không lưu tệp tạm trên server

  Examples:
    | tinh_huong                                   | http_status | error_code             |
    | tệp ảnh vượt quá dung lượng 5 MiB            | 413         | IMAGE_TOO_LARGE        |
    | tệp có MIME type là application/pdf hoặc TIFF| 415         | UNSUPPORTED_IMAGE_TYPE |
    | tệp gắn đuôi .jpg nhưng nội dung byte bị hỏng| 422         | INVALID_IMAGE          |
    | hệ thống chưa có mô hình nào ở trạng thái active | 503     | MODEL_NOT_READY        |
    | thời gian suy luận vượt ngưỡng timeout cấu hình  | 504     | INFERENCE_TIMEOUT      |
```

### AC-07 — Tra cứu danh mục nguyên liệu, tìm kiếm tiếng Việt và lọc gia vị nền (`US-04`, `FR-05`, `TC-36`, `DEF-06`)

```gherkin
Scenario Outline: Tra cứu danh mục nguyên liệu công khai theo bộ lọc category và exclude_pantry
  Given danh mục ingredients có nguyên liệu active thuộc nhóm "vegetable", "pantry" và nguyên liệu có is_active=false
  When client gửi GET "/api/v1/ingredients?<query_string>" không kèm Bearer token
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua_mong_doi>"

  Examples:
    | query_string                           | http_status | ket_qua_mong_doi                                          |
    | limit=20&offset=0                      | 200         | chỉ trả các nguyên liệu có is_active=true                 |
    | category=pantry                        | 200         | chỉ trả các gia vị nền active có category="pantry"        |
    | exclude_pantry=true                    | 200         | chỉ trả các nguyên liệu chính active có category!="pantry"|
    | category=pantry&exclude_pantry=true    | 422         | trả mã lỗi INVALID_QUERY_PARAMS                           |
```

### AC-08 — Chỉnh sửa nguyên liệu chính, bật/tắt gia vị nền và nhập tay dự phòng (`US-04`, `FR-05`, `FR-18`, `TC-08`, `TC-09`, `TC-27`, `TC-31`)

```gherkin
Scenario Outline: Chuẩn bị danh sách ingredient_ids và excluded_pantry_ids trên màn hình xác nhận
  Given người dùng đang ở màn hình xác nhận nguyên liệu với trạng thái khởi tạo "<trang_thai_dau>"
  When người dùng thực hiện thao tác "<thao_tac_nguoi_dung>"
  Then trạng thái dữ liệu chuẩn bị gửi tới API gợi ý là "<ket_qua_payload>"

  Examples:
    | trang_thai_dau                              | thao_tac_nguoi_dung                                              | ket_qua_payload                                                                 |
    | AI gợi ý Cà chua, Cà rốt; 5 gia vị nền bật  | đổi Cà rốt thành Trứng gà và giữ nguyên 5 gia vị nền             | ingredient_ids=[ca_chua, trung_ga], excluded_pantry_ids=[]                      |
    | AI gợi ý Cà chua, Trứng gà; 5 gia vị nền bật| bỏ chọn gia vị nền "Nước mắm" vì trong bếp đã hết                | ingredient_ids=[ca_chua, trung_ga], excluded_pantry_ids=[nuoc_mam_id]           |
    | AI trả detections=[] hoặc người dùng mở nhập tay | tìm và chọn thủ công Cà chua, Trứng gà                      | ingredient_ids=[ca_chua, trung_ga], excluded_pantry_ids=[], scan_id=null        |
    | danh sách đang có 1 nguyên liệu Cà chua     | xóa Cà chua khiến danh sách nguyên liệu chính trống rỗng         | UI vô hiệu hóa nút Gợi ý món và yêu cầu chọn tối thiểu 1 nguyên liệu chính      |
```

### AC-09 — Kiểm tra hợp đồng phân loại nguyên liệu trên API gợi ý (`US-04`, `FR-05`, `FR-06`, `TC-37`)

```gherkin
Scenario Outline: Từ chối yêu cầu gợi ý khi gửi sai nhóm nguyên liệu chính hoặc gia vị nền
  Given nguyên liệu "Cà chua" có category="vegetable" và "Nước mắm" có category="pantry"
  When client gửi POST "/api/v1/recommendations" với payload "<payload_loi>"
  Then hệ thống trả HTTP 422 với mã lỗi "INVALID_INGREDIENTS"

  Examples:
    | payload_loi                                                                 |
    | ingredient_ids chứa UUID của "Nước mắm" (category="pantry")                 |
    | excluded_pantry_ids chứa UUID của "Cà chua" (category="vegetable")          |
    | ingredient_ids hoặc excluded_pantry_ids chứa UUID không tồn tại hoặc inactive|
```

### AC-10 — Chấm điểm và xếp hạng khi đủ gia vị nền (`US-05`, `FR-06`, `TC-10`, `TC-11`, `TC-12`)

```gherkin
Scenario: Tính điểm S=89.0 và xếp nhóm ready trước missing khi người dùng không thiếu gia vị nền
  Given công thức "Trứng xào cà chua" (prep=5, cook=8, VN) có R_main={Trứng gà, Cà chua}, O_main={Hành lá}, R_pantry={Dầu ăn, Nước mắm}
  And công thức "Gà xào cà chua" (prep=10, cook=15, VN) có R_main={Thịt gà, Cà chua}, O_main={}, R_pantry={Dầu ăn, Nước mắm}
  When người dùng gửi POST "/api/v1/recommendations" với ingredient_ids=[Trứng gà, Cà chua], excluded_pantry_ids=[], include_missing=true
  Then "Trứng xào cà chua" có availability="ready", score=89.0 (C=0.8, E=1.0, T=1.0, P=1.0), missing_required_ingredient_ids=[]
  And "Gà xào cà chua" có availability="missing", missing_required_ingredient_ids=[Thịt gà] và được xếp sau "Trứng xào cà chua"
```

### AC-11 — Giảm điểm và chuyển sang nhóm missing khi người dùng tắt gia vị nền bắt buộc (`US-05`, `FR-06`, `TC-32`)

```gherkin
Scenario: Chuyển món sang nhóm missing và giảm điểm xuống S=68.1 khi tắt gia vị bắt buộc Nước mắm
  Given công thức "Trứng xào cà chua" (prep=5, cook=8, VN) có R_main={Trứng gà, Cà chua}, O_main={Hành lá}, R_pantry={Dầu ăn, Nước mắm}
  When người dùng gửi POST "/api/v1/recommendations" với ingredient_ids=[Trứng gà, Cà chua] và excluded_pantry_ids=[Nước mắm]
  Then hệ thống tính M_pantry={Nước mắm}, E=2/3 (≈0.667), C=2/3.5 (≈0.571), T=1.0, P=1.0 và trả score=68.1
  And món "Trứng xào cà chua" chuyển sang availability="missing" với missing_required_ingredient_ids=[Nước mắm]
```

### AC-12 — Lọc chỉ lấy món nấu được ngay (`include_missing=false`) và xử lý kết quả rỗng (`US-05`, `FR-06`, `TC-33`, `TC-34`)

```gherkin
Scenario: Loại bỏ các món thiếu nguyên liệu bắt buộc khi đặt include_missing=false
  Given tập ứng viên có 1 món availability="ready" và 2 món availability="missing"
  When người dùng gửi POST "/api/v1/recommendations" với include_missing=false
  Then hệ thống trả HTTP 200 với mảng items chỉ chứa 1 món có availability="ready" (và trả items=[] nếu không có món nào ready)
```

### AC-13 — Lọc cứng theo ẩm thực/thời gian và ưu tiên mềm theo sở thích ẩm thực (`US-06`, `FR-07`, `TC-13`, `TC-14`, `TC-35`)

```gherkin
Scenario: Áp dụng đồng thời lọc cứng max_total_minutes, cuisine_codes và ưu tiên mềm preferred_cuisine_codes
  Given món A (VN, prep=5, cook=10), món B (EU, prep=5, cook=10) và món C (VN, prep=15, cook=20) có cùng độ phủ C và E
  When người dùng gửi POST "/api/v1/recommendations" với cuisine_codes=["VN", "EU"], preferred_cuisine_codes=["VN"] và max_total_minutes=15
  Then món C (35 phút) bị loại trước khi chấm điểm
  And món A (VN, 15 phút) nhận P=1.0 còn món B (EU, 15 phút) vẫn xuất hiện nhưng nhận P=0.0 (điểm thấp hơn A đúng 10.0 điểm)
```

### AC-14 — Hiển thị nhãn dinh dưỡng định tính kèm nguồn và tuyên bố miễn trừ (`US-07`, `FR-08`, `TC-15`)

```gherkin
Scenario: Xem thông tin dinh dưỡng định tính của công thức đã công bố
  Given nguyên liệu "Cà chua" trong công thức có gắn nhãn dinh dưỡng "Vitamin C" kèm source_url hợp lệ
  When người dùng xem màn hình chi tiết công thức đó
  Then giao diện hiển thị nhãn "Vitamin C", liên kết source_url và câu cảnh báo miễn trừ trách nhiệm định lượng/dị ứng bắt buộc
  And phản hồi không chứa bất kỳ trường kcal hay khối lượng gram suy diễn nào từ ảnh
```

### AC-15 — Đăng ký, đăng nhập và kế thừa quyền `Admin --|> User` (`US-08`, `FR-09a`, `FR-09b`, `TC-16`)

```gherkin
Scenario: Đăng nhập qua Supabase Auth và sử dụng quyền kế thừa của Admin trên endpoint User
  Given một tài khoản Admin có profiles.role="admin" và một tài khoản User có profiles.role="user"
  When hai tài khoản đăng nhập qua Supabase Auth và gọi các endpoint dành cho User (như GET "/api/v1/favorites")
  Then cả hai tài khoản đều nhận được HTTP 200 hợp lệ trên dữ liệu cá nhân của chính mình
```

### AC-16 — Khôi phục mật khẩu qua email (`US-08`, `FR-09a`, `FR-09b`, `TC-40`)

```gherkin
Scenario: Yêu cầu đặt lại mật khẩu qua email với Supabase Auth
  Given người dùng hoặc Admin có địa chỉ email đã đăng ký hợp lệ
  When người dùng gửi yêu cầu resetPasswordForEmail và cập nhật mật khẩu mới qua liên kết xác thực
  Then mật khẩu mới được lưu thành công và người dùng đăng nhập lại được bằng mật khẩu mới
```

### AC-17 — Đăng xuất cục bộ (`scope: 'local'`) (`US-08`, `FR-09a`, `FR-09b`, `TC-46`)

```gherkin
Scenario: Đăng xuất khỏi phiên làm việc trên thiết bị hiện tại
  Given người dùng hoặc Admin đang có phiên đăng nhập hợp lệ trên trình duyệt
  When người dùng nhấn nút Đăng xuất để gọi supabase.auth.signOut({ scope: 'local' })
  Then token phiên cục bộ trên thiết bị hiện tại bị xóa ngay lập tức và giao diện chuyển về chế độ Guest
```

### AC-18 — Lưu, xem và xóa món ăn yêu thích cô lập theo chủ sở hữu (`US-09`, `FR-10`, `TC-17`, `TC-18`, `SEC-01`)

```gherkin
Scenario: Thêm yêu thích idempotent và bảo vệ quyền riêng tư danh sách yêu thích giữa hai người dùng
  Given User A và User B có hai JWT token riêng biệt và một công thức đang ở trạng thái "published"
  When User A gọi POST "/api/v1/favorites" hai lần liên tiếp cho công thức đó
  Then lần đầu trả HTTP 201, lần thứ hai trả HTTP 200 mà không tạo bản ghi trùng, và User B không nhìn thấy hay xóa được mục yêu thích của User A
```

### AC-19a — Tùy chọn lưu hoặc không lưu lịch sử khi nhận diện ảnh (`US-11`, `FR-12`, `TC-20`, `SEC-02`)

```gherkin
Scenario: Kiểm soát lưu lịch sử phiên quét theo cờ save_history
  Given User A đã đăng nhập có Bearer JWT hợp lệ
  When User A gọi POST "/api/v1/ai/detect" với save_history=false rồi gọi tiếp một lần với save_history=true
  Then lần gọi save_history=false trả scan_id=null và không ghi vào bảng scan_sessions
  And lần gọi save_history=true trả scan_id khác null, lưu metadata phiên quét thuộc sở hữu của User A (không lưu ảnh gốc)
```

### AC-19b — Xem, xóa phiên quét lịch sử và ẩn danh hóa lỗi quyền sở hữu (`US-11`, `FR-12`, `TC-28`, `TC-47`, `SEC-06`, `UI-04`)

```gherkin
Scenario: Xóa phiên quét lịch sử của chính mình kèm cascade feedback và chặn truy cập chéo bằng 404
  Given User A có phiên quét S1 (kèm 1 feedback gắn với S1 và 1 feedback khác của cùng món có scan_id=null) và User B có token riêng
  When User B gọi GET/DELETE "/api/v1/scan-sessions/{S1}" còn User A xác nhận hộp thoại cảnh báo và gọi DELETE "/api/v1/scan-sessions/{S1}"
  Then yêu cầu của User B bị từ chối với HTTP 404 "SCAN_NOT_OWNED"
  And yêu cầu của User A trả HTTP 204, xóa sạch S1 cùng feedback gắn với S1 (ON DELETE CASCADE) mà vẫn giữ nguyên bản ghi feedback có scan_id=null
```

### AC-20 — Gửi và cập nhật đánh giá gợi ý theo ngữ cảnh (`US-10`, `FR-11`, `TC-19`, `TC-45`)

```gherkin
Scenario Outline: Upsert đánh giá mức độ hữu ích theo tổ hợp (user_id, recipe_id, scan_id)
  Given User A đã đăng nhập, công thức R đang "published" và phiên quét S1 thuộc sở hữu của User A
  When User A gửi POST "/api/v1/feedback" với dữ liệu "<du_lieu_feedback>"
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua_feedback>"

  Examples:
    | du_lieu_feedback                                                  | http_status | ket_qua_feedback                                                |
    | recipe_id=R, scan_id=null, rating=4 (lần đầu trong ngữ cảnh null) | 201         | tạo bản ghi đánh giá mới cho ngữ cảnh scan_id=null              |
    | recipe_id=R, scan_id=null, rating=5 (gửi lại trong ngữ cảnh null) | 200         | cập nhật rating=5 và updated_at trên bản ghi scan_id=null hiện có|
    | recipe_id=R, scan_id=S1, rating=5 (lần đầu trong ngữ cảnh S1)     | 201         | tạo bản ghi đánh giá riêng gắn với phiên quét S1                |
    | recipe_id=R, scan_id=null, rating=6 (ngoài miền giá trị 1..5)     | 422         | trả mã lỗi VALIDATION_ERROR                                     |
    | recipe_id=R, scan_id của User B, rating=4                         | 404         | trả mã lỗi SCAN_NOT_OWNED                                       |
```

### AC-21 — Tạo công thức ở trạng thái nháp (`draft`) và kiểm soát quyền Admin (`US-12`, `FR-13`, `TC-21`, `SEC-03`)

```gherkin
Scenario: Admin tạo công thức draft hợp lệ và chặn người dùng thường gọi API quản trị
  Given tài khoản Admin (role="admin") và tài khoản User thường (role="user")
  When User thường và Admin cùng gửi POST "/api/v1/admin/recipes" với dữ liệu công thức hợp lệ
  Then yêu cầu của User thường bị chặn với HTTP 403 "FORBIDDEN"
  And yêu cầu của Admin trả HTTP 201 tạo công thức ở trạng thái "draft" (chưa xuất hiện trên GET "/api/v1/recipes")
```

### AC-22a — Chặn công bố công thức vi phạm điều kiện xuất bản (`US-12`, `FR-13`, `TC-22`, `TC-38`)

```gherkin
Scenario Outline: Kiểm tra 4 điều kiện bắt buộc khi chuyển trạng thái công thức sang published
  Given Admin có một công thức đang ở trạng thái "draft" với tình trạng dữ liệu "<tinh_trang_cong_thuc>"
  When Admin gửi PATCH "/api/v1/admin/recipes/{recipe_id}/status" với body {"status": "published"}
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua_publish>"

  Examples:
    | tinh_trang_cong_thuc                                                                 | http_status | ket_qua_publish                                                       |
    | không có bước hướng dẫn nào (steps=[])                                               | 400         | RECIPE_NOT_PUBLISHABLE (reason="missing_steps")                       |
    | chỉ có nguyên liệu bắt buộc thuộc nhóm pantry, thiếu nguyên liệu chính bắt buộc      | 400         | RECIPE_NOT_PUBLISHABLE (reason="missing_required_main_ingredient")    |
    | chứa một nguyên liệu đang bị vô hiệu hóa (is_active=false)                           | 400         | RECIPE_NOT_PUBLISHABLE (reason="inactive_ingredient")                 |
    | có 1 bước đơn lẻ với estimated_minutes=20 lớn hơn prep_minutes(5) + cook_minutes(10) | 400         | RECIPE_NOT_PUBLISHABLE (reason="step_exceeds_total_minutes")          |
    | có >=1 bước hợp lệ, >=1 nguyên liệu chính bắt buộc active, mọi bước <= total_minutes | 200         | chuyển trạng thái sang "published" và ghi bản ghi vào audit_logs      |
```

### AC-22b — Chặn chỉnh sửa làm vi phạm điều kiện xuất bản trên công thức đang `published` (`US-12`, `FR-13`, `TC-38`)

```gherkin
Scenario: Ngăn chặn PATCH công thức đang published nếu dữ liệu mới vi phạm điều kiện xuất bản
  Given một công thức đang ở trạng thái "published" hợp lệ
  When Admin gửi PATCH "/api/v1/admin/recipes/{recipe_id}" làm xóa hết nguyên liệu chính bắt buộc (hoặc thêm nguyên liệu inactive, hoặc đặt 1 bước có estimated_minutes > total_minutes)
  Then hệ thống từ chối giao dịch với HTTP 400 "RECIPE_NOT_PUBLISHABLE" và giữ nguyên dữ liệu hợp lệ trước đó của công thức
```

### AC-23 — Tạo và cập nhật nguyên liệu chuẩn kèm tên đồng nghĩa (`US-13`, `FR-14`, `TC-23`)

```gherkin
Scenario Outline: Thêm mới hoặc cập nhật nguyên liệu và kiểm tra trùng lặp slug
  Given danh mục nguyên liệu đã có bản ghi slug="ca-chua"
  When Admin gửi yêu cầu quản trị nguyên liệu "<yeu_cau_nguyen_lieu>"
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua>"

  Examples:
    | yeu_cau_nguyen_lieu                                                                 | http_status | ket_qua                                                       |
    | POST /api/v1/admin/ingredients với slug="nuoc-mam", category="pantry", aliases=[]   | 201         | tạo nguyên liệu gia vị nền thành công và ghi audit_logs       |
    | POST /api/v1/admin/ingredients với slug="ca-chua" bị trùng                          | 409         | trả mã lỗi DUPLICATE_SLUG                                     |
    | PATCH /api/v1/admin/ingredients/{id} cập nhật aliases=["cà chua bi", "cà chua đỏ"]  | 200         | thay thế toàn bộ aliases trong giao dịch và tìm kiếm khớp mã |
```

### AC-24 — Chặn tắt hoặc đổi phân loại nguyên liệu đang được sử dụng (`US-13`, `FR-14`, `TC-39`)

```gherkin
Scenario Outline: Bảo vệ tính toàn vẹn của nguyên liệu đang thuộc công thức published hoặc model draft/active
  Given nguyên liệu I đang nằm trong "<noi_su_dung>"
  When Admin gửi PATCH "/api/v1/admin/ingredients/{I}" để đặt "<thay_doi>"
  Then hệ thống trả HTTP 400 với mã lỗi "INGREDIENT_IN_USE" và không cập nhật bản ghi

  Examples:
    | noi_su_dung                                        | thay_doi               |
    | một công thức đang ở trạng thái published          | is_active=false        |
    | một công thức đang ở trạng thái published          | category="pantry"      |
    | bảng ai_labels của một model đang draft hoặc active| is_active=false        |
    | bảng ai_labels của một model đang draft hoặc active| category="pantry"      |
```

### AC-25 — Đăng ký, kích hoạt và Rollback phiên bản mô hình AI (`US-14`, `FR-15`, `TC-24`, `TC-41`)

```gherkin
Scenario Outline: Kiểm tra điều kiện kích hoạt hoặc rollback mô hình AI sang trạng thái active
  Given hệ thống đang có model M1 ở trạng thái "active" và model mục tiêu M2 có tình trạng "<tinh_trang_model_M2>"
  When Admin gửi PATCH "/api/v1/admin/ai-models/{M2}/status" với body {"status": "active"}
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua_model>"

  Examples:
    | tinh_trang_model_M2                                                                                      | http_status | ket_qua_model                                                                 |
    | M2 đang draft, đã ánh xạ đủ toàn bộ class_index vào các nguyên liệu chính đang active                    | 200         | M2 chuyển sang active, M1 tự động chuyển sang archived trong cùng transaction |
    | M2 đang draft nhưng còn thiếu ánh xạ cho class_index=3                                                   | 400         | MODEL_NOT_ACTIVATABLE (unmapped_class_indices=[3])                            |
    | M2 đang archived, toàn bộ nguyên liệu được ánh xạ hiện vẫn active và category!="pantry"                  | 200         | Rollback thành công: M2 chuyển sang active, M1 chuyển sang archived           |
    | M2 đang archived nhưng có 1 nguyên liệu ánh xạ đã bị đổi sang category="pantry" trong lúc M2 lưu trữ     | 400         | MODEL_NOT_ACTIVATABLE (invalid_mapped_class_indices chứa class_index vi phạm) |
```

### AC-26 — Bảo vệ tính bất biến của model `active`/`archived` và chặn ánh xạ nhãn vào `pantry`/`inactive` (`US-14`, `FR-15`, `TC-42`, `TC-44`)

```gherkin
Scenario: Chặn thêm/sửa ai_labels trên model không phải draft hoặc trỏ vào nguyên liệu pantry/inactive
  Given model M_active đang ở trạng thái "active" (hoặc "archived") và model M_draft đang ở trạng thái "draft"
  And nguyên liệu P có category="pantry" (hoặc is_active=false)
  When Admin gọi POST/PATCH "/api/v1/admin/ai-labels" trên M_active hoặc gán nhãn của M_draft vào nguyên liệu P
  Then thao tác trên M_active bị chặn với HTTP 400 "MODEL_IMMUTABLE"
  And thao tác gán nhãn vào nguyên liệu P trên M_draft bị chặn với HTTP 400 "INVALID_LABEL_MAPPING"
```

### AC-27 — Quản trị nhãn dinh dưỡng và bắt buộc nguồn tham khảo (`US-14`, `FR-16`, `TC-25`)

```gherkin
Scenario Outline: Kiểm tra bắt buộc source_url hợp lệ khi gán nhãn dinh dưỡng cho nguyên liệu
  Given Admin đã đăng nhập và chọn một nguyên liệu hợp lệ
  When Admin gửi PUT "/api/v1/admin/ingredients/{ingredient_id}/nutrition-tags" với "<du_lieu_source_url>"
  Then hệ thống trả HTTP <http_status> với kết quả "<ket_qua>"

  Examples:
    | du_lieu_source_url                                            | http_status | ket_qua                                           |
    | source_url="https://fdc.nal.usda.gov/food-details/170457/nutrients" | 200   | lưu ánh xạ nhãn dinh dưỡng và ghi nhận audit_logs |
    | thiếu trường source_url hoặc chuỗi không phải URI hợp lệ       | 422         | trả mã lỗi VALIDATION_ERROR                       |
```

### AC-28 — Tra cứu nhật ký kiểm toán hệ thống (`US-14`, `FR-17`, `TC-26`)

```gherkin
Scenario: Admin xem danh sách nhật ký thay đổi dữ liệu mà không lộ thông tin bí mật
  Given Admin vừa thực hiện cập nhật công thức, nguyên liệu và kích hoạt model AI
  When Admin gửi GET "/api/v1/admin/audit-logs?limit=20&offset=0"
  Then hệ thống trả HTTP 200 chứa danh sách bản ghi có đủ actor_id, action, entity_type, entity_id, created_at
  And không có bản ghi nào chứa mật khẩu, JWT hay service-role key
```


---

## 4. Liên kết mở rộng Giai đoạn 2–5 (`Scoring v1.1` & Kịch bản Bảo vệ Đồ án)

30 kịch bản Gherkin nguyên tử ở Mục 3 khóa chặt hợp đồng cốt lõi MVP (`P0` / `P1` nền tảng theo [`openapi.yaml`](../03-api/openapi.yaml)). Đối với các năng lực thông minh mở rộng ở Giai đoạn 2–5 (cảnh báo xác nhận HITL theo ngưỡng $\tau$, suy luận 3 trạng thái `READY` / `UNKNOWN` / `MISSING_CONFIRMED`, lọc cứng dị ứng/thiết bị `BLOCKED`, độ phủ có trọng số $w_{r,i}$, xếp hạng MCDA 5 tiêu chí kèm giải thích XAI `80.83`, cá nhân hóa Logistic Regression, đa dạng hóa MMR, quy đổi khẩu phần và dinh dưỡng Tầng 2 USDA), tiêu chí nghiệm thu chi tiết được đặc tả tại bộ **10 kịch bản bảo vệ đồ án (`DEF-01`..`DEF-10`)** và **Unit Test toán học (`MATH-01`..`MATH-07`)** trong [`06-testing/test-cases.md`](../06-testing/test-cases.md).
