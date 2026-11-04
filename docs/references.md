# Nguồn tham khảo khoa học, kỹ thuật và nguyên tắc dẫn nguồn

**Ngày rà soát:** `04/11/2026` · **Phiên bản:** `1.0.0`. Danh mục dưới đây tổng hợp đầy đủ các công trình khoa học nền tảng của 14 thành phần thông minh và tài liệu kỹ thuật chính thức của các công cụ sử dụng, **không phải bằng chứng rằng mô hình của nhóm đã huấn luyện xong hoặc đạt một mức độ chính xác cụ thể**.

## 1. Tài liệu khoa học nền tảng (theo 14 thành phần thông minh)

1. Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). **You Only Look Once: Unified, Real-Time Object Detection**. *CVPR*. https://arxiv.org/abs/1506.02640 — cơ sở họ mô hình phát hiện vật thể YOLO (Thành phần 01).
2. Radford, A. và cộng sự. (2021). **Learning Transferable Visual Models From Natural Language Supervision**. *ICML*. https://proceedings.mlr.press/v139/radford21a.html — cơ sở không gian biểu diễn chung ảnh–văn bản CLIP cho vùng ảnh khó (Thành phần 02).
3. Poole, D., & Mackworth, A. **Artificial Intelligence: Foundations of Computational Agents**. https://artint.info/ — nền tảng biểu diễn tri thức và suy luận bằng luật có thể giải thích (Thành phần 03, 04).
4. Tversky, A. (1977). **Features of Similarity**. *Psychological Review*, 84(4), 327–352. https://doi.org/10.1037/0033-295X.84.4.327 — mô hình tương đồng tập hợp bất đối xứng dùng làm thuật toán đối chứng Baseline B (Thành phần 06).
5. Carbonell, J., & Goldstein, J. (1998). **The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries**. *SIGIR*. https://dl.acm.org/doi/10.1145/290941.291025 — thuật toán Maximal Marginal Relevance đa dạng hóa Top-K (Thành phần 09).
6. Järvelin, K., & Kekäläinen, J. (2002). **Cumulated Gain-based Evaluation of IR Techniques**. *ACM TOIS*. https://doi.org/10.1145/582415.582418 — cơ sở chỉ số đánh giá xếp hạng `DCG@K` và `nDCG@K` (Thành phần 12).
7. Guo, C. và cộng sự. (2017). **On Calibration of Modern Neural Networks**. *ICML*. https://proceedings.mlr.press/v70/guo17a.html — cơ sở hiệu chỉnh độ tin cậy mạng nơ-ron phục vụ ngưỡng xác nhận HITL (Thành phần 14).
8. Rendle, S. và cộng sự. (2009). **BPR: Bayesian Personalized Ranking from Implicit Feedback**. *UAI*. https://arxiv.org/abs/1205.2618 — tài liệu tham chiếu mở rộng cho học xếp hạng cá nhân hóa từ phản hồi (Thành phần 08).
9. Tian, Y. và cộng sự. (2022). **RecipeRec: A Heterogeneous Graph Learning Model for Recipe Recommendation**. *IJCAI*. https://www.ijcai.org/proceedings/2022/481 — nghiên cứu tham chiếu về gợi ý công thức nấu ăn.
10. Soekamto, Y. S. và cộng sự. (2025). **Pic2Plate: A Vision-Language and Retrieval-Augmented Framework for Personalized Recipe Recommendations**. *Sensors* — nghiên cứu đối chiếu liên quan (không phải kiến trúc bắt buộc của MVP).

## 2. Tài liệu kỹ thuật chính thức, Pháp lý & Nguồn dữ liệu dinh dưỡng

11. Ultralytics Documentation, **YOLO Object Detection & Validation**: https://docs.ultralytics.com/tasks/detect và https://docs.ultralytics.com/datasets/detect.
12. Ultralytics, **License**: https://www.ultralytics.com/license — kiểm tra điều khoản AGPL-3.0 / Enterprise trước khi phân phối (`ADR-005`).
13. PostgreSQL Documentation, **`pg_trgm`, `unaccent` và `UNIQUE NULLS NOT DISTINCT` (PostgreSQL >= 15)**: https://www.postgresql.org/docs/current/pgtrgm.html và https://www.postgresql.org/docs/current/unaccent.html — tìm kiếm tiếng Việt gần đúng, bỏ dấu và toàn vẹn khóa duy nhất theo ngữ cảnh (Thành phần 13, `ADR-012`).
14. U.S. Department of Agriculture (USDA), **FoodData Central & API Guide**: https://fdc.nal.usda.gov/ và https://fdc.nal.usda.gov/api-guide/ — nguồn dữ liệu dinh dưỡng trên $100\text{ g}$ theo CC0/public domain (Thành phần 11). **Không suy đoán lượng chất/kcal từ ảnh không có khối lượng chuẩn.**
15. FastAPI Documentation, **OpenAPI & Multipart Request Files**: https://fastapi.tiangolo.com/reference/openapi/docs/ và https://fastapi.tiangolo.com/tutorial/request-forms-and-files/.
16. OpenAPI Initiative, **OpenAPI Specification 3.1**: https://spec.openapis.org/oas/.
17. Supabase Documentation, **Row Level Security, JWTs & Product Security**: https://supabase.com/docs/guides/database/postgres/row-level-security, https://supabase.com/docs/guides/auth/jwts và https://supabase.com/docs/guides/security/product-security.
18. Quốc hội nước CHXHCN Việt Nam (2025), **Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15** (có hiệu lực từ `01/01/2026`) và **Nghị định 13/2023/NĐ-CP** — cơ sở pháp lý cho nguyên tắc tối thiểu hóa dữ liệu, xóa metadata EXIF/GPS, lịch sử opt-in và quyền tự xóa dữ liệu (`NFR-06`, `NFR-13`).

## 3. Quản trị nguồn dữ liệu món ăn và tập ảnh

**Chưa có tập ảnh hay kho công thức nào được công bố là đã kiểm chứng xong tại thời điểm lập đặc tả.** Mỗi bản ghi công thức và nguồn ảnh khi đưa vào dự án bắt buộc lưu đầy đủ nhật ký kiểm duyệt:

| Trường | Bắt buộc? | Mô tả |
|---|---|---|
| `source_url` / `source_name` | Có khi tham khảo nguồn ngoài | Liên kết truy xuất nguồn gốc |
| `author` / `owner` | Có nếu xác định được | Tác giả hoặc đơn vị sở hữu |
| `license` / `permission` | Có | `CC0` / `CC-BY` / giấy phép riêng / `original` tự biên soạn |
| `verified_on` & `reviewer` | Có | Ngày và thành viên kiểm duyệt nội dung, thời gian, dị ứng |
| `prep_minutes` / `cook_minutes` | Có khi `published` | `cook_minutes` bao gồm cả thời gian ướp/chờ/hầm bắt buộc (`ADR-009`) |
| `notes` | Nên có | Giả định định lượng gram, lưu ý đổi khẩu phần và giới hạn |

**Nguyên tắc trích dẫn học thuật:** tài liệu tham khảo dùng để chứng minh **cơ sở lý thuyết của phương pháp**; mọi con số `mAP@50:95`, `Precision@5`, `nDCG@5` trong báo cáo cuối kỳ bắt buộc trích từ **thực nghiệm do chính nhóm chạy trên dataset và model có version xác định**.
