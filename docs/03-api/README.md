# 03 — API Contract

- [api-conventions.md](api-conventions.md): versioning, auth, lỗi, phân trang, tương tác Swagger/Postman.
- [openapi.yaml](openapi.yaml): **bản hợp đồng API thiết kế**, chuẩn OpenAPI 3.1, tham chiếu khi lập trình.
- [request-response-examples.md](request-response-examples.md): ví dụ request/response cho luồng chính.
- [foodvision-ai.postman_collection.json](foodvision-ai.postman_collection.json): collection khởi tạo cho Postman (không phải kết quả API đã hoạt động).

**Lưu ý quan trọng:** sau khi cài FastAPI, OpenAPI tại `/openapi.json` do server sinh ra phải được đối chiếu với `docs/03-api/openapi.yaml`. Không duy trì hai contract khác nhau. Mọi ví dụ JSON chỉ minh họa cấu trúc và không chứng minh đã có dữ liệu seed/DB.
