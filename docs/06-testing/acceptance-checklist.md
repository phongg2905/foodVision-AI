# Checklist nghiệm thu / Demo cho giảng viên

**Trạng thái:** chưa có kết quả thực thi. Dùng checklist này **sau** khi code và test, không đánh dấu trước.

## 1. Trước khi chạy demo

- [ ] Repo có README hướng dẫn FE/BE/env/database/model; không có secret trong Git.
- [ ] SRS, ERD, API và AI label list không mâu thuẫn với code, migration, model đang demo.
- [ ] DB có món Việt/Âu/Mỹ, có món 10–15 phút được nguồn/nhóm kiểm tra thời gian.
- [ ] Nêu model version, dataset version, số nhãn hỗ trợ thực tế; không gọi nhãn chưa train là đã nhận diện được.
- [ ] Có ảnh thử độc lập (không chỉ ảnh đã đưa vào tập train).
- [ ] Tài khoản User A/User B/Admin demo tách biệt, không lộ token.

## 2. Kịch bản demo liên tục (≤10 phút là gợi ý cho nhóm, không phải giới hạn của học phần)

1. **Guest** vào website trên desktop/mobile; tìm một món Việt/Âu/Mỹ, xem chi tiết và thời gian nấu.
2. Chọn ảnh 2+ nguyên liệu; hệ thống hiển thị bounding box, nhãn và confidence.
3. Cố tình chọn một nhãn AI sai hoặc xóa một phát hiện, nhập thủ công nguyên liệu khác để minh chứng correction.
4. Chọn `max_total_minutes=15` và cuisine VN; nhận danh sách món có score + nhóm ready/missing + thiếu nguyên liệu.
5. Mở món có điểm cao, xem công thức bước-by-bước và nhãn dinh dưỡng định tính có nguồn.
6. Đăng nhập User A, lưu favorite; User B không xem được favorite của A.
7. Admin tạo món draft → thêm required ingredients và steps → publish → món xuất hiện public; show audit.
8. Trình bày báo cáo YOLO thật (Precision/Recall/mAP + lớp sai) và giải thích scoring tính tay cho một ví dụ.

## 3. Bảng nghiệm thu chức năng

| Hạng mục | Tiêu chí đạt | Minh chứng cần thu thập | Trạng thái |
|---|---|---|---|
| Luồng ảnh → correction → gợi ý | Các TC P0 tương ứng qua | Browser recording/screenshot/log | Not run |
| Bộ lọc ẩm thực và thời gian | Không trả món ngoài điều kiện cứng | API response/test fixture | Not run |
| Độ đúng điểm S | Unit sample S=89.0 và S=100.0 | pytest console + fixtures | Not run |
| Quản trị | User không sửa dữ liệu admin | 401/403 và DB audit | Not run |
| RLS/privacy | User A/B cô lập, ảnh gốc không lưu; User xóa được history | SQL tests và Storage inspect | Not run |
| AI | Báo cáo test độc lập, không bịa số | Evaluation artifact/version | Not run |
| API | Hợp đồng OpenAPI khớp code | Validation + /openapi.json diff | Not run |
| Nội dung | Công thức/dinh dưỡng đúng phạm vi, có nguồn | Content review và source links | Not run |

## 4. Những nội dung phải nói rõ khi bảo vệ

- YOLO phát hiện các nguyên liệu **nằm trong tập nhãn đã huấn luyện**, không hiểu mọi thực phẩm.
- Recommendation là công thức có trọng số và hard filters, **không phải YOLO tự sáng tác món ăn**.
- Thời gian nấu 10–15 phút là **bộ lọc dựa trên dữ liệu công thức**, không phải AI đo từ ảnh.
- Nhóm dinh dưỡng là **định tính**, chưa dự báo kcal/protein/fat theo gram.
- Phân biệt số liệu mục tiêu thiết kế và số liệu thực nghiệm; trình bày hạn chế và hướng mở rộng trung thực.
