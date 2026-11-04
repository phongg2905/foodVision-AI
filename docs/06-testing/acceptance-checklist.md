# Checklist Nghiệm thu & Kịch bản Demo Bảo vệ Học phần

**Phiên bản:** `0.9.1-draft` · **Trạng thái:** chưa thực thi. Chỉ đánh dấu hoàn thành sau khi có mã nguồn, dữ liệu seed hợp lệ, bằng chứng thực nghiệm và xác nhận kiểm thử chéo.

## 1. Kiểm tra trước buổi bảo vệ

- [ ] Repo có `README.md` hướng dẫn chạy FE/BE/Supabase/Model rõ ràng; không lộ `.env` hay secret key trong Git.
- [ ] Toàn bộ tài liệu `docs/` khớp với schema database (PostgreSQL `>= 15`, `unaccent`, `pg_trgm`), `openapi.yaml` và công thức tính điểm trong code đang demo.
- [ ] Database có sẵn công thức Việt (`VN`), Âu (`EU`), Mỹ (`US`) đã kiểm duyệt (`published`), có món `<= 15` phút, phân tách rõ 5 gia vị nền (`category = 'pantry'`) và bộ từ đồng nghĩa tiếng Việt (`đậu hũ`/`đậu phụ`...).
- [ ] Công bố rõ `model_version`, `dataset_version`, số lớp $K$ được huấn luyện thực tế và chuẩn bị sẵn bộ ảnh thử độc lập (ngoài tập `train`, bao gồm ảnh chụp dọc điện thoại có EXIF).
- [ ] Tài khoản `User A`, `User B` và `Admin` demo tách biệt, không lộ token trên màn hình trình chiếu.
- [ ] Chuẩn bị sẵn báo cáo thực nghiệm độc lập (`mAP@50`, `mAP@50:95`, per-class `AP50`/`N_test` của YOLO; và bảng đối chứng `Precision@5`, `nDCG@5` giữa các biến thể A–B–C–D khi nghiệm thu đầy đủ Giai đoạn 5).

## 2. Kịch bản trình diễn liên tục (bao phủ luồng cốt lõi `P0` & 10 kịch bản bảo vệ `DEF-01`..`DEF-10`)

1. **Nhận diện, EXIF & HITL (`DEF-01`, `DEF-02`, `TC-43`):** tải ảnh chụp từ điện thoại có 2+ nguyên liệu → hệ thống tự xoay chuẩn chiều EXIF, xóa GPS, hiển thị `bbox` + `confidence`; thử thêm ảnh mờ/vật thể lạ → hệ thống bật cảnh báo xác nhận HITL hoặc trả `detections=[]`, cho phép sửa/xóa nhãn trực tiếp.
2. **Tìm kiếm tiếng Việt & Thanh gia vị sẵn có (`DEF-06`, `TC-31`):** gõ `dau phu` và `dau hu` (không dấu/đồng nghĩa) vào ô tìm kiếm → hệ thống ánh xạ về cùng một nguyên liệu chuẩn `Đậu hũ`; minh họa bật/tắt một gia vị trên thanh **"Gia vị sẵn có trong bếp"** (`excluded_pantry_ids`).
3. **Suy luận trạng thái, Chấm điểm & Giải thích XAI (`DEF-03`, `DEF-04`, `DEF-10`):** lọc `max_total_minutes = 15`, `cuisine_codes = ["VN"]`; trình diễn sự khác biệt giữa món đủ nguyên liệu (`ready`) và món thiếu/chưa xác nhận đủ nguyên liệu (`missing` ở `v1.0` / `unknown` & `missing_confirmed` ở `v1.1`), đối chiếu bảng điểm thành phần XAI khớp phép tính tay (`89.0` / `68.1` ở `v1.0`; `80.83` ở `v1.1`) và tính đa dạng kết quả (MMR).
4. **Lọc ràng buộc an toàn & Công thức kiểm duyệt (`DEF-05`, `DEF-09`):** mở chi tiết một công thức `published`, xem khu vực "Gia vị cần chuẩn bị", bước hướng dẫn và thông tin dinh dưỡng kèm `source_url` + tuyên bố miễn trừ trách nhiệm (minh họa quy đổi khẩu phần & ước tính USDA khi có `grams` xác thực ở Giai đoạn 3, và lọc cứng `BLOCKED` khi bật dị ứng ở Giai đoạn 2).
5. **Quyền riêng tư, Cá nhân hóa & Quản trị CMS (`DEF-08`, `SEC-01`, `TC-38`):** đăng nhập `User A` lưu `favorites`/gửi `feedback` (minh chứng `User B` không xem được dữ liệu của `User A`, xóa `scan_session` cascade feedback an toàn); đăng nhập `Admin` tạo món `draft` → kiểm tra chặn `400 RECIPE_NOT_PUBLISHABLE` khi thiếu bước → bổ sung đủ dữ liệu → `publish` → xem `audit_logs`.
6. **Trình bày báo cáo thực nghiệm (`DEF-07`, `AI-01`, `AI-04`):** trình chiếu báo cáo đánh giá độc lập của YOLO (bao gồm cả các lớp khó, không loại lớp yếu sau test theo `NFR-11`) và bảng đối chứng các biến thể hệ gợi ý.

## 3. Bảng nghiệm thu tổng hợp

| Hạng mục | Tiêu chí đạt | Minh chứng cần thu thập | Trạng thái |
|---|---|---|---|
| Nhận thức YOLO, EXIF & HITL (`TP 01, 02, 14`) | `TC-04`..`09`, `TC-43`, `DEF-01`, `DEF-02` đạt | Video/ảnh màn hình + response log | Not run |
| Tiếng Việt `pg_trgm` & Cơ sở tri thức (`TP 03, 10, 13`) | `TC-01`..`03`, `TC-23`, `TC-36`, `DEF-06` đạt | Kết quả test SQL/API `pg_trgm` | Not run |
| Suy luận trạng thái, Pantry & Dị ứng (`TP 04`) | `TC-10`..`14`, `TC-31`..`35`, `DEF-03`..`05` đạt | Output `pytest` + API test | Not run |
| Xếp hạng MCDA, MMR & Giải thích XAI (`TP 05, 07, 09, 14`) | `MATH-03`..`06`, `DEF-10` đạt (điểm khớp tính tay) | Output `pytest` + giao diện XAI | Not run |
| Cá nhân hóa LR & Dinh dưỡng 2 tầng (`TP 08, 11`) | `TC-15`, `TC-25`, `DEF-08`, `DEF-09` đạt | Log cập nhật $\theta_u$ + kiểm tra nguồn USDA | Not run |
| Thực nghiệm đối chứng AI & Ranker (`TP 06, 12`) | `AI-01`..`AI-04`, `DEF-07` có số đo thật độc lập | Báo cáo đánh giá + script tái lập | Not run |
| Bảo mật, RLS, Hợp đồng OpenAPI & Pháp lý | `SEC-01`..`07`, `API-01`..`04`, `LEGAL-01`, `OPS-01`..`03` đạt | Test quyền Supabase + `/openapi.json` diff | Not run |

## 4. Những luận điểm khoa học phải nói rõ khi bảo vệ

- **Kiến trúc 7 tầng phối hợp, không thần thánh hóa một mô hình đơn lẻ:** tính thông minh của hệ thống nằm ở chuỗi phối hợp Nhận thức (YOLO + nhánh phụ CLIP tùy chọn) → Biểu diễn tri thức có cấu trúc → Suy luận trạng thái & Ràng buộc cứng → Quyết định đa tiêu chí (MCDA + MMR) → Học sở thích nhẹ (Logistic Regression) → Kiểm soát lỗi (HITL + XAI) → Thực nghiệm khách quan; **YOLO chỉ phát hiện nguyên liệu trong tập lớp đã học, không tự sáng tác món ăn**.
- **Không giả định thế giới đóng (Open-World Assumption):** không thấy một nguyên liệu trong ảnh chỉ có nghĩa là hệ thống chưa biết (`unknown`) hoặc cần kiểm tra gia vị bếp, khác bản chất với việc người dùng xác nhận đã hết nguyên liệu đó (`confirmed_missing` / `excluded_pantry_ids`).
- **Phân biệt rõ hai cơ chế cập nhật từ phản hồi người dùng:** đánh giá món ăn (`favorites`/`feedback`) cập nhật trọng số sở thích cá nhân $\theta_u$ của mô hình Logistic Regression nhẹ, còn thao tác sửa nhãn ảnh trên giao diện HITL chỉ áp dụng cho phiên hiện tại (và lưu metadata nếu opt-in) — **mô hình YOLO không tự huấn luyện lại tức thời sau một cú nhấp chuột**.
- **Dinh dưỡng hai tầng có căn cứ, tuyệt đối không đoán `gram` từ ảnh 2D:** ở Tầng 1 (`P0`) chỉ hiển thị nhãn định tính có dẫn nguồn; ở Tầng 2 (`P1`) chỉ tính `kcal`/macros từ USDA FoodData Central khi công thức có định lượng `grams` đã kiểm duyệt hoặc người dùng nhập rõ khối lượng, luôn kèm miễn trừ trách nhiệm y tế/dị ứng.
- **Trung thực thực nghiệm & Kiểm thử chéo:** phân biệt rõ con số ví dụ minh họa công thức (`89.0`, `68.1`, `80.83`, `104.5 kcal`) với số liệu đo thực tế trên tập kiểm định độc lập; tuân thủ `NFR-11` không loại bỏ lớp yếu sau khi chạy test.
