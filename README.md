# FoodVision AI

Hệ thống Web thông minh gợi ý món ăn từ hình ảnh nguyên liệu kết hợp nhận thức thị giác (YOLO + lớp hỗ trợ ứng viên CLIP/VLM + xác nhận HITL), chuẩn hóa tiếng Việt (`unaccent` + `pg_trgm` + từ đồng nghĩa), suy luận luật 3 trạng thái kết hợp thanh gia vị nền (`pantry`), xếp hạng đa tiêu chí (MCDA + MMR), cá nhân hóa sở thích (Logistic Regression), chính sách dinh dưỡng hai tầng có nguồn (nhãn định tính + ước tính USDA theo định lượng chuẩn) và giải thích điểm minh bạch (XAI).

## Cấu trúc thư mục dự án

```text
foodvision-ai/
├── .agents/skills/         # Bộ kỹ năng Spec Kit (speckit-*) tích hợp cho AI Coding Agent
├── .specify/               # Cấu hình GitHub Spec Kit, templates & Hiến pháp (constitution.md)
├── frontend/               # React + TypeScript + Tailwind (HITL xác nhận nhãn, gia vị pantry & giao diện XAI)
├── backend/                # FastAPI + YOLO/CLIP + Vietnamese Search + Reasoning, MCDA, LR, MMR & USDA
├── supabase/               # PostgreSQL >= 15 migrations (pg_trgm, alias, tri thức món ăn, RLS + GRANT)
├── tests/                  # Kiểm thử hợp đồng API, bảo mật RLS, 7 bài toán học & thực nghiệm A/B/C/D
├── docs/                   # Bộ tài liệu đặc tả & thiết kế chuẩn của dự án (0.9.1-draft)
│   ├── 01-requirements/    # SRS, Use Cases, UML Diagram, User Stories & Gherkin AC, RTM
│   ├── 02-architecture/    # Kiến trúc 7 tầng thông minh, ERD, Data Dictionary, Bảo mật & EXIF privacy
│   ├── 03-api/             # Quy ước API, OpenAPI 3.1, ví dụ mô phỏng và Postman Collection
│   ├── 04-ai-model/        # YOLO, lớp hỗ trợ CLIP/VLM, HITL, danh mục nhãn, đánh giá mAP@50:95
│   ├── 05-recommendation/  # Suy luận 3 trạng thái, Coverage, Tversky, MCDA, LR, MMR, USDA, XAI
│   ├── 06-testing/         # Kế hoạch kiểm thử, 47 TC chức năng, 10 kịch bản bảo vệ học phần & unit tests
│   ├── 07-decisions/       # Architecture Decision Records (ADR-001…ADR-012)
│   ├── assets/             # Hình ảnh, sơ đồ và tài nguyên tài liệu
│   └── README.md           # Mục lục tổng thể, kiến trúc 14 thành phần và lộ trình 5 giai đoạn
└── README.md               # Giới thiệu tổng quan & quy trình làm việc nhóm với Spec Kit + Trello
```

## Phân công nhóm & Quản trị tiến độ (Trello + GitHub Spec Kit)

- **Bảng Trello quản trị 5 giai đoạn (19 thẻ Đơn trách nhiệm):** [FoodVision AI Trello Board](https://trello.com/b/DxNLNPlP/foodvision-ai)
- **Hiến pháp dự án cho AI Agent:** [.specify/memory/constitution.md](./.specify/memory/constitution.md)

| Mã TV | Thành viên | Vai trò chính (Single Owner) | Kiểm thử chéo (Cross-Tester) |
| :--- | :--- | :--- | :--- |
| **`TV1`** | **Minh Thành** (`@minhthanh4`) | AI, ML & Data Content Lead (`TP 01`, `02`, `08`, `12a`, Seed Data & `/ai/detect` — 6 thẻ) | Kiểm thử độc lập API Backend, RLS & `MATH-01..07` của `TV2` |
| **`TV2`** | **Phong Phạm** (`@phongphm2`) | Backend, DB, Reasoning & Ranker Lead (`TP 03..07`, `09`, `10`, `11`, `12b`, `13`, CMS/User API — 7 thẻ) | Kiểm thử độc lập mô-đun AI, EXIF privacy & Dataset của `TV1` |
| **`TV3`** | **Tâm Minh** (`@tamminh6`) | Frontend, HITL/XAI & QA Lead (`TP 14`, toàn bộ giao diện React, E2E 47 TC, 10 DEF & Báo cáo — 6 thẻ) | Kiểm thử tích hợp End-to-End toàn hệ thống & giao diện |

### Quy trình triển khai từng thẻ Trello với Spec Kit

Khi bắt đầu thực hiện một thẻ trên Trello, thành viên phụ trách thực hiện theo các bước sau:

1. **Tạo nhánh làm việc** từ `main` (hoặc để Spec Kit tự tạo nhánh) gắn với mã thẻ Trello (ví dụ: `006-gd1-db-api`, `007-gd1-seed-data`, `018-gd1-fe-ui`).
2. **Sử dụng bộ kỹ năng Spec Kit** cùng mô tả & checklist trên thẻ Trello:
   - `/speckit-specify`: Khởi tạo đặc tả cho thẻ đang làm (tham chiếu trực tiếp các file trong `docs/` đã ghi trên thẻ).
   - `/speckit-plan`: Lập kế hoạch thiết kế kỹ thuật (bám sát [.specify/memory/constitution.md](./.specify/memory/constitution.md) và `docs/03-api/openapi.yaml`).
   - `/speckit-tasks`: Sinh danh sách công việc (`tasks.md`) chi tiết đến từng file trong `supabase/`, `backend/`, `frontend/`, `tests/`.
   - `/speckit-implement`: Thực thi viết code và chạy kiểm thử tự động theo từng task.
3. **Tạo Pull Request & Kiểm thử chéo:** Kéo thẻ Trello sang cột *Kiểm tra / Review (Cross-Testing)* để thành viên kiểm thử chéo chạy bộ test độc lập trước khi merge vào `main`.

## Tài liệu chi tiết

Xem mục lục đầy đủ, kiến trúc 7 tầng (14 thành phần thông minh) và lộ trình triển khai tại [docs/README.md](./docs/README.md).
