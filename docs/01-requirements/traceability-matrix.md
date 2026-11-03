# Requirement Traceability Matrix (RTM)

Mục tiêu: mỗi yêu cầu chức năng có Use Case, API (hoặc SDK), test case và trạng thái. **Tất cả ở trạng thái `Planned` khi khởi tạo**; không coi là đã test.

| FR | Use Case | API / SDK phụ trách | Test Case | Trạng thái |
|---|---|---|---|---|
| FR-01 | UC-01 | GET `/recipes` | TC-01, TC-02 | Planned |
| FR-02 | UC-01 | GET `/recipes/{id}` | TC-03 | Planned |
| FR-03 | UC-02 | POST `/ai/detect` | TC-04, TC-05, TC-06 | Planned |
| FR-04 | UC-02 | POST `/ai/detect` | TC-07, AI-01 | Planned |
| FR-05 | UC-03 | Client state → POST `/recommendations` | TC-08, TC-09 | Planned |
| FR-06 | UC-04 | POST `/recommendations` | TC-10, TC-11, TC-12 | Planned |
| FR-07 | UC-04 | POST `/recommendations`; GET `/recipes` | TC-13, TC-14 | Planned |
| FR-08 | UC-05 | GET `/recipes/{id}`, GET `/nutrition-tags` | TC-15 | Planned |
| FR-09 | UC-06 | Supabase Auth SDK | TC-16 | Planned |
| FR-10 | UC-06 | GET/POST/DELETE `/favorites` | TC-17, TC-18, SEC-01 | Planned |
| FR-11 | UC-07 | POST `/feedback` | TC-19 | Planned |
| FR-12 | UC-07 | POST `/ai/detect`; GET `/scan-sessions`; GET/DELETE `/scan-sessions/{scan_id}` | TC-20, TC-28, SEC-02 | Planned |
| FR-13 | UC-08 | POST/PATCH `/admin/recipes`; PATCH status | TC-21, TC-22 | Planned |
| FR-14 | UC-08 | POST/PATCH `/admin/ingredients` | TC-23 | Planned |
| FR-15 | UC-09 | GET/POST `/admin/ai-models`; GET/POST/PATCH `/admin/ai-labels` | TC-24 | Planned |
| FR-16 | UC-09 | POST/PATCH `/admin/nutrition-tags` | TC-25 | Planned |
| FR-17 | UC-09 | GET `/admin/audit-logs` | TC-26 | Planned |
| FR-18 | UC-02 | POST `/recommendations` không cần detect | TC-27 | Planned |

**NFR → kiểm thử:** NFR-01→UI-01; 02→PERF-01; 03→PERF-02; 04→SEC-01,03; 05→SEC-04; 06→SEC-02; 07→TC-15; 08→API-01; 09→SEC-05; 10→API-02; 11→AI-01,02; 12→LEGAL-01.

API trong bảng được hiểu theo prefix `/api/v1` (trừ Supabase Auth SDK). Test cases chi tiết: [06-testing/test-cases.md](../06-testing/test-cases.md).
