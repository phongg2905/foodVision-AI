# 01 — Requirements (`1.0.0`)

- [SRS.md](SRS.md): phạm vi (`P0`/`P1`/`P2+`) và lộ trình thông minh 5 giai đoạn, bảng phân vai & nguyên tắc kiểm thử chéo, Glossary, tác nhân (`Admin --|> User --|> Guest`), **19 yêu cầu chức năng (`FR-01`..`FR-18`, tách `FR-09a`/`FR-09b`)**, **14 yêu cầu phi chức năng (`NFR-01`..`NFR-14`)**, **12 quy tắc nghiệp vụ (`BR-01`..`BR-12`)**, bảng I/O và quản trị rủi ro.
- [use-cases.md](use-cases.md): sơ đồ luồng Use Case, bảng chuẩn hóa ánh xạ và đặc tả chi tiết **10 Use Case (`UC-01`..`UC-10`, với `UC-02 <<extend>> UC-03` tại `EP_InitFromImage`)**; [sơ đồ UML Use Case (PlantUML)](use-case-diagram.puml).
- [user-stories.md](user-stories.md): **14 User Stories (`US-01`..`US-14`)**, Definition of Done (DoD), **30 kịch bản Gherkin nguyên tử (`AC-01`..`AC-28`, gồm `AC-19a/b` và `AC-22a/b`)** và liên kết tới 10 kịch bản bảo vệ đồ án (`DEF-01`..`DEF-10`).
- [traceability-matrix.md](traceability-matrix.md): ma trận truy vết 2 chiều giữa `FR`/`NFR` & **14 thành phần thông minh** ↔ `UC` ↔ `US/AC` ↔ `API` ↔ `TC-01`..`TC-47`, `DEF-01`..`DEF-10` (`SEC`, `API`, `AI-01..04`, `UI`, `PERF`, `LEGAL`, `OPS`) và `Primary Owner`.

Mọi mức hiệu năng và độ chính xác ở đây là **mục tiêu thiết kế cần kiểm thử thực nghiệm**, không phải kết quả đã đạt.
