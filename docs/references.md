# Nguồn tham khảo và nguyên tắc dẫn nguồn

**Ngày rà soát:** 03/11/2026. Các liên kết dưới đây là tài liệu nền tảng/nguồn chính thức để nhóm tra cứu, **không phải bằng chứng rằng mô hình đã được huấn luyện hoặc API đã được triển khai**. Khi nộp báo cáo, ghi ngày truy cập và phiên bản sản phẩm/thư viện sử dụng thực tế.

## 1. Tài liệu kỹ thuật chính thức

1. FastAPI, **OpenAPI docs / Swagger UI**: https://fastapi.tiangolo.com/reference/openapi/docs/ — công cụ docs UI `/docs` và `/redoc`.
2. FastAPI, **Request Forms and Files**: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/ — upload Multipart/File/Form.
3. OpenAPI Initiative, **OpenAPI Specification**: https://spec.openapis.org/oas/ — đặc tả chuẩn OpenAPI, file thiết kế đang dùng `3.1.0` nhằm tương thích tooling.
4. Supabase, **Row Level Security**: https://supabase.com/docs/guides/database/postgres/row-level-security — GRANT và policy RLS.
5. Supabase, **JWT**: https://supabase.com/docs/guides/auth/jwts — xác minh access token và JWKS.
6. Supabase, **Secure configuration**: https://supabase.com/docs/guides/security/product-security — security guidance.
7. Ultralytics, **Object Detection**: https://docs.ultralytics.com/tasks/detect — output, training, validation metrics.
8. Ultralytics, **Object Detection Datasets**: https://docs.ultralytics.com/datasets/detect — YOLO annotation `class x_center y_center width height`.
9. Ultralytics, **License**: https://www.ultralytics.com/license — cần tự kiểm tra yêu cầu AGPL-3.0/Enterprise theo hình thức sử dụng.
10. Mermaid, **Getting Started**: https://mermaid.js.org/intro/getting-started — Mermaid code blocks trong Markdown.

## 2. Nguồn dữ liệu dinh dưỡng

11. U.S. Department of Agriculture (USDA), **FoodData Central**: https://fdc.nal.usda.gov/.
12. USDA, **FoodData Central API Guide / Licensing**: https://fdc.nal.usda.gov/api-guide/ — dữ liệu FDC công bố theo CC0/public domain, nên ghi công nguồn. **Không suy đoán lượng chất/kcal trong khẩu phần từ số liệu trên 100g nếu không có khối lượng.**

## 3. Dữ liệu món ăn và ảnh

**Chưa có bộ nguồn công thức/ảnh nào được xác minh cụ thể tại thời điểm lập docs.** Không điền tên nguồn hay khẳng định thời gian 10–15 phút là kết quả thực nghiệm khi chưa thu thập. Các tài nguyên phải có nhật ký cấp phép, nguồn gốc, tác giả, cách kiểm chứng thời gian và quyền sử dụng lại.

Checklist lập nguồn cho từng recipe/dataset:

| Trường | Bắt buộc? | Mô tả |
|---|---|---|
| source_url / source_name | Có khi dùng tài liệu ngoài | Truy xuất được nơi xuất bản |
| author / owner | Có nếu có dữ liệu | Người sở hữu hoặc tạo |
| license / permission | Có | CC0/CC-BY/giấy phép riêng/nội dung gốc |
| verified_on | Có | Ngày nhóm đối chiếu |
| prep_minutes / cook_minutes | Có khi công bố recipe | Tổng cần phù hợp nhãn thời gian |
| reviewer | Nên có | Người kiểm tra |
| notes | Nên có | Điều chỉnh công thức và hạn chế |

**Nguyên tắc trích dẫn học thuật:** tài liệu kỹ thuật nói về **khả năng của công cụ**; kết quả đánh giá AI chỉ có thể trích từ **thử nghiệm nhóm thực sự thực hiện** trên model/dataset xác định. Không dùng link docs công cụ làm bằng chứng model FoodVision đã đạt một mức mAP/precision nào đó.
