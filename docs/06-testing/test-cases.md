# Test Cases — danh sách kiểm thử kế hoạch

**Trạng thái mặc định tất cả case:** `Not run`. **Tiền điều kiện chung:** API/Frontend chạy trên môi trường test, seed dữ liệu đúng như mô tả, kiểm thử viên ghi build SHA. **Mã:** TC (functional), SEC (security), PERF (performance), API (contract), AI (model), UI, LEGAL.

## A. Functional (FR)

| ID | FR | Dữ liệu/thao tác | Kết quả mong đợi |
|---|---|---|---|
| TC-01 | FR-01 | GET `/recipes?q=trung` | Chỉ món published có từ khóa phù hợp, phân trang đúng |
| TC-02 | FR-01 | GET `/recipes?cuisine_code=VN&max_total_minutes=15` | Chỉ món VN có prep+cook ≤15 |
| TC-03 | FR-02 | GET `/recipes/{id}` món published/draft | Published trả detail/steps; draft trả 404 với Guest |
| TC-04 | FR-03 | Upload ảnh JPEG 1 MB hợp lệ | 200 và JSON đúng schema (có thể detections=[]) |
| TC-05 | FR-03 | Upload file >5 MiB | 413 `IMAGE_TOO_LARGE`, không infer |
| TC-06 | FR-03 | Upload text giả `.jpg` / TIFF | 415/422, không crash, không lưu file |
| TC-07 | FR-04 | Ảnh 2+ lớp từ test fixture | JSON có nhiều bbox nếu model detect; đo TP/FP/FN bằng eval độc lập |
| TC-08 | FR-05 | AI trả 2 cà chua và 1 trứng; user gộp/sửa | Request recommendation chỉ gồm ID đã xác nhận, không trùng |
| TC-09 | FR-05 | User xóa tất cả ingredient IDs | UI ngăn gửi recommend; có cách thêm tay |
| TC-10 | FR-06 | Recipe cần trứng+cà chua đều có | `availability=ready`, thiếu required rỗng |
| TC-11 | FR-06 | Recipe cần gà+cà chua, user có cà chua | `availability=missing`, gà ở missing_required |
| TC-12 | FR-06 | Cùng dữ liệu, so score tính tay và API | Điểm khớp công thức, sai số làm tròn ≤0.05 trước round |
| TC-13 | FR-07 | `cuisine_codes=["VN"]` | Không có món EU/US |
| TC-14 | FR-07 | `max_total_minutes=15`, món 5+10 và 15+20 | Chỉ có món 15 phút; món 35 phút loại |
| TC-15 | FR-08 | Xem recipe có tag/không tag | Tag có nguồn + cảnh báo; không có kcal/gram suy ra từ ảnh |
| TC-16 | FR-09 | Đăng nhập/đăng xuất với Supabase Auth | Có session hợp lệ, logout không gọi private API được |
| TC-17 | FR-10 | User A lưu món 2 lần | Không trùng favorite; GET chỉ một item |
| TC-18 | FR-10 | User A bỏ favorite | 204; danh sách không còn món |
| TC-19 | FR-11 | User gửi `rating=3` và `rating=6` | 3 → 201, 6 → 422 |
| TC-20 | FR-12 | User detect save_history=false/true | false: scan_id=null, không lưu; true: có scan_id và owner=User |
| TC-28 | FR-12 | User A GET/DELETE lịch sử, user B dùng scan_id của A | A xem/xóa được; B không truy cập được; các bản ghi con được dọn đúng FK |
| TC-21 | FR-13 | Admin tạo recipe draft đủ dữ liệu | 201; recipe chưa hiện public trước publish |
| TC-22 | FR-13 | Publish recipe không có required/steps | 400 `RECIPE_NOT_PUBLISHABLE`; không công bố |
| TC-23 | FR-14 | Admin tạo ingredient slug trùng | 409; thêm alias đúng, search alias tìm mã chuẩn |
| TC-24 | FR-15 | Admin tạo model draft và mapping; kích hoạt | Chỉ một active model, mapping đúng class index; audit có bản ghi |
| TC-25 | FR-16 | Admin gắn nutrition tag không có source_url | 422; có nguồn → tag hiển thị đúng |
| TC-26 | FR-17 | Admin cập nhật recipe | Có audit actor, action, entity_id, thời gian; không log secret |
| TC-27 | FR-18 | AI trả `detections=[]`; guest nhập cà chua/trứng tay | Recommend hoạt động, không cần scan_id |

## B. Security, Privacy, Contract

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| SEC-01 | Token User B truy cập favorite User A | Không thấy và không sửa favorite A; DB RLS chặn truy cập ngoài quyền |
| SEC-02 | Guest detect save_history=true / false | true →401, false →200; không có ảnh lưu trong Storage |
| SEC-03 | User thường POST `/admin/recipes` hoặc giả `role=admin` | 403, không tạo data/audit thành công |
| SEC-04 | Thử Data API trực tiếp anon/user A/user B | GRANT + RLS bảo vệ profiles/favorites/scans; public chỉ published |
| SEC-05 | File ảnh giả/ảnh gây giải mã nặng, spam request | Validation, rate limit, timeout; không crash/leak file |
| SEC-06 | User B gửi `scan_id` thuộc A qua recommendations/feedback | 403 hoặc 404; không sửa được `scan_ingredients` của A |
| SEC-07 | User thường tự PATCH `profiles.role` bằng Data API | Bị từ chối, role không đổi |
| API-01 | Gửi input lỗi tại 3 endpoints đại diện | JSON có `code`, `message`, `details`, `request_id` |
| API-02 | Validate `openapi.yaml`; so với FastAPI `/openapi.json` | Schema hợp lệ; routes/request/response chính khớp |
| API-03 | Gửi request JSON body cho multipart detect | Từ chối/validation rõ, không coi JSON là ảnh |
| API-04 | Gửi ingredient ID không tồn tại hoặc array rỗng | 422, không gợi ý món giả |

## C. AI, UI và Performance

| ID | Đầu vào / Thao tác | Kết quả mong đợi |
|---|---|---|
| AI-01 | Đánh giá test split độc lập | Xuất Precision/Recall/mAP50/mAP50-95, per-class AP và version |
| AI-02 | Ảnh nhiều object, nền đa dạng | Lưu TP/FP/FN, ảnh minh họa các trường hợp khó, không cherry-pick |
| AI-03 | Đổi model version và class index | Vẫn ánh xạ đúng ingredients.id theo từng version |
| UI-01 | Chrome/Edge/Firefox ở 360/768/1366px | Màn upload, correction, list, detail không mất nút chính |
| UI-02 | Mạng chậm / API timeout | Có loading/error/retry; không treo vĩnh viễn |
| PERF-01 | ≥30 requests detect, ghi máy/model/ảnh/concurrency | Báo p50/p95; so mục tiêu đề xuất 10s, không tự ghi Pass |
| PERF-02 | Tập 500 món, benchmark recommendations | Báo p50/p95; so mục tiêu đề xuất 1s |
| LEGAL-01 | Rà soát 5 ảnh + 5 công thức + model license | Có căn cứ nguồn/giấy phép, không sao chép trái phép |

## D. Kiểm tra tính đúng của thuật toán (unit tests cần code)

| Trường hợp | C / E / T / P | Điểm kỳ vọng |
|---|---|---|
| 2 required đều có, 1 optional thiếu, món 13 phút, không preference | C=0.8,E=1,T=1,P=1 | S=89.0, ready |
| Cả 3 nguyên liệu đều có, món 13 phút, không preference | C=1,E=1,T=1,P=1 | S=100.0, ready |
| Chỉ 1 required/2 required, optional thiếu, món 13 phút | C=0.4,E=0.5,T=1,P=1 | S=54.5, missing |
| Không có required/optional nào trùng | C=0 | Bị loại khỏi candidates |
| Món 35 phút với max_total_minutes=15 | Không chấm | Bị filter trước scoring |
| Món thuộc US nhưng preferred chỉ VN, không hard filter | P=0 | Điểm giảm 10.0 so với P=1 |

Lưu ý unit case thứ ba: C=(1)/(2+0.5)=0.4; S=100×(0.22+0.125+0.1+0.1)=54.5.

## E. Khi nào đánh dấu Pass

Chỉ đánh `Pass` sau khi có **build xác định**, dữ liệu test độc lập, actual response khớp expected và link evidence. Với AI, có thể ghi "mục tiêu mAP chưa đạt" nhưng kiểm thử đo lường vẫn là **đã chạy**, không tự sửa expected để giả đạt.
