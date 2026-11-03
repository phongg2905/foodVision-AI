# FoodVision AI — Bộ tài liệu dự án

> **Phiên bản tài liệu:** 1.0.0 (bản đặc tả đề xuất)  
> **Cập nhật:** 03/11/2026  
> **Trạng thái:** Chờ nhóm và giảng viên phê duyệt trước khi coi là baseline triển khai  
> **Học phần:** Phát triển các hệ thống thông minh  
> **Loại sản phẩm:** Website gợi ý món ăn từ ảnh nguyên liệu

## 1. Mục đích

Thư mục `docs/` là **nguồn chuẩn (single source of truth) về yêu cầu và thiết kế** của FoodVision AI. Tất cả tài liệu ở đây mô tả **thiết kế dự kiến**, không đồng nghĩa rằng chức năng đã được lập trình hoặc kiểm thử thành công. Ngay khi giảng viên/nhóm duyệt baseline, các thay đổi về nghiệp vụ, mô hình dữ liệu, API và AI phải đi kèm pull request cập nhật tài liệu có liên quan.

**Tên đề tài đề xuất:** Xây dựng website thông minh gợi ý món ăn từ hình ảnh nguyên liệu sử dụng YOLO.

**Ý tưởng cốt lõi:** người dùng gửi ảnh nguyên liệu → YOLO phát hiện các nguyên liệu trong ảnh → người dùng xác nhận/chỉnh sửa → thuật toán đối chiếu công thức và tính điểm → hệ thống trả về danh sách món ăn Việt/Âu/Mỹ, nguyên liệu thiếu, thời gian và các bước chế biến. Thông tin dinh dưỡng giai đoạn đầu chỉ ở **mức nhóm chất/đặc điểm định tính**, không suy đoán gram hay kcal từ ảnh.

## 2. Mục lục

| Thư mục | Tài liệu chính | Mục đích |
|---|---|---|
| [01-requirements](01-requirements/README.md) | [SRS](01-requirements/SRS.md), [Use Cases](01-requirements/use-cases.md), [User Stories](01-requirements/user-stories.md), [Traceability](01-requirements/traceability-matrix.md) | Xác định **làm gì** và tiêu chí nghiệm thu |
| [02-architecture](02-architecture/README.md) | [Kiến trúc](02-architecture/system-architecture.md), [Database](02-architecture/database-design.md), [Data Dictionary](02-architecture/data-dictionary.md), [Bảo mật](02-architecture/security-and-deployment.md) | Xác định **hệ thống được xây như thế nào** |
| [03-api](03-api/README.md) | [Quy ước API](03-api/api-conventions.md), [OpenAPI 3.1](03-api/openapi.yaml), [Ví dụ](03-api/request-response-examples.md) | Hợp đồng Frontend–Backend |
| [04-ai-model](04-ai-model/README.md) | [Thiết kế AI](04-ai-model/ai-model-design.md), [Nhãn](04-ai-model/label-catalog.md), [Dữ liệu/đánh giá](04-ai-model/dataset-and-evaluation.md) | Thiết kế và kiểm chứng YOLO |
| [05-recommendation](05-recommendation/README.md) | [Thuật toán](05-recommendation/recommendation-design.md), [Dinh dưỡng/nội dung](05-recommendation/nutrition-and-content.md) | Giải thích xếp hạng món ăn minh bạch |
| [06-testing](06-testing/README.md) | [Kế hoạch](06-testing/test-plan.md), [Test cases](06-testing/test-cases.md), [Checklist](06-testing/acceptance-checklist.md) | Nghiệm thu trên bằng chứng |
| [07-decisions](07-decisions/README.md) | ADR-001…ADR-005 | Ghi nhận lựa chọn kỹ thuật và đánh đổi |
| Chung | [Nguồn tham khảo](references.md), [Changelog](CHANGELOG.md) | Nguồn chính thống và lịch sử thay đổi |

## 3. Baseline kỹ thuật đề xuất

- **Client:** React + TypeScript + Vite + Tailwind CSS; Web responsive, hỗ trợ trình duyệt điện thoại, **không xây APK/iOS app ở MVP**.
- **Server:** Python + FastAPI (business API); tách mô-đun nhận diện YOLO và mô-đun gợi ý quy tắc.
- **AI:** Ultralytics YOLO Object Detection, dùng mô hình đã fine-tune theo tập nhãn có quyền sử dụng; **chưa chốt biến thể/weights trước khi benchmark**.
- **Dữ liệu:** Supabase PostgreSQL; Supabase Auth; Storage chỉ cho ảnh công thức/tài nguyên được phép.
- **API contract:** OpenAPI 3.1, REST JSON; upload ảnh dùng multipart/form-data.

Thông số/giới hạn trong tài liệu được chia thành **(1) yêu cầu thiết kế**, **(2) mục tiêu kiểm thử**, **(3) kết quả thực nghiệm**. Chưa có kết quả thực nghiệm ở thời điểm phát hành tài liệu này.

## 4. Ranh giới MVP

**Có trong MVP:** nhận diện nhiều nguyên liệu trong một ảnh; sửa kết quả; tìm kiếm nguyên liệu thủ công; lọc món theo ẩm thực/thời gian; xếp hạng; công thức từng bước; nhóm dinh dưỡng định tính; đăng nhập; yêu thích; quản trị nguyên liệu/món/nhãn ánh xạ.

**Không trong MVP:** ước lượng khối lượng từ một ảnh RGB bất kỳ; cam kết chính xác năng lượng/kcal hoặc chất dinh dưỡng theo gram; lập kế hoạch ăn uống y khoa; chatbot LLM; ứng dụng mobile native; tự huấn luyện trực tiếp từ ảnh người dùng.

## 5. Cách đóng góp và duyệt thay đổi

1. Đề xuất thay đổi ở issue/PR và nêu rõ mã yêu cầu (FR/NFR/UC/API/TC).
2. Cập nhật SRS nếu đổi nghiệp vụ; cập nhật ERD/Data Dictionary nếu đổi dữ liệu; sửa `openapi.yaml` nếu đổi request/response; cập nhật test cases tương ứng.
3. Nếu là quyết định ảnh hưởng kiến trúc, viết ADR mới trong `07-decisions/`.
4. Người phụ trách kỹ thuật và người phụ trách yêu cầu review; sau đó mới merge vào nhánh chính theo quy trình nhóm.
5. Không commit `.env`, service-role secret, bộ dữ liệu ảnh có vấn đề bản quyền hoặc model weights dung lượng lớn vào Git thường.

**Thứ tự triển khai gợi ý:** FR-01…FR-06 → FR-07…FR-10 → FR-11…FR-15 → NFR, thử nghiệm AI và đánh giá gợi ý. Truy vết tại [traceability-matrix.md](01-requirements/traceability-matrix.md).
