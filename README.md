# FoodVision AI

Hệ thống Web thông minh gợi ý món ăn từ hình ảnh nguyên liệu kết hợp nhận thức thị giác (YOLO + lớp hỗ trợ ứng viên CLIP/VLM + xác nhận HITL), chuẩn hóa tiếng Việt (`unaccent` + `pg_trgm` + từ đồng nghĩa), suy luận luật 3 trạng thái kết hợp thanh gia vị nền (`pantry`), xếp hạng đa tiêu chí (MCDA + MMR), cá nhân hóa sở thích (Logistic Regression), chính sách dinh dưỡng hai tầng có nguồn (nhãn định tính + ước tính USDA theo định lượng chuẩn) và giải thích điểm minh bạch (XAI).

## Cấu trúc thư mục dự án

```text
foodvision-ai/
├── frontend/               # React + TypeScript + Tailwind (HITL xác nhận nhãn, gia vị pantry & giao diện XAI)
├── backend/                # FastAPI + YOLO/CLIP + Vietnamese Search + Reasoning, MCDA, LR, MMR & USDA
├── supabase/               # PostgreSQL >= 15 migrations (pg_trgm, alias, tri thức món ăn, RLS + GRANT)
├── tests/                  # Kiểm thử hợp đồng API, bảo mật RLS và thực nghiệm đối chứng A/B/C/D
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
└── README.md               # Giới thiệu tổng quan dự án
```

## Tài liệu chi tiết

Xem mục lục đầy đủ, kiến trúc 7 tầng (14 thành phần thông minh) và lộ trình triển khai tại [docs/README.md](./docs/README.md).
