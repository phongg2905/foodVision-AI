# ADR-005 — Kiểm soát giấy phép YOLO và dữ liệu

- **Status:** Accepted
- **Date:** 03/11/2026
- **Context:** Ultralytics phân phối phần mềm/model theo các điều khoản AGPL-3.0/Enterprise; ảnh và công thức từ Internet cũng có bản quyền riêng.
- **Decision:** trong đồ án phải ghi rõ model/weights/framework và license, xem lại điều khoản hiện hành trước khi phân phối ứng dụng hoặc triển khai public; có thể phải công khai source theo AGPL hoặc mua license phù hợp. Không khẳng định học thuật = được miễn license. Mọi nguồn dataset/công thức/ảnh phải có quyền dùng.
- **Alternatives:** lựa chọn framework/trọng số có license khác được phép theo tình huống; xin phép chủ sở hữu; tự chụp ảnh/tự viết công thức.
- **Consequences:** tăng khâu kiểm duyệt nhưng tránh vi phạm khi demo/công bố; có thể phải thay model nếu điều khoản không phù hợp mục tiêu repo.
- **Revisit when:** chọn weights cuối cùng, thay cách phân phối repo, chuyển sang sản phẩm thương mại hoặc thay license.
- **References:** https://www.ultralytics.com/license, `docs/references.md`. Tài liệu này không phải tư vấn pháp lý.
