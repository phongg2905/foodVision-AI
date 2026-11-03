# Test Plan — FoodVision AI

**Mã:** FV-TEST-001 · **Phiên bản:** 1.0.0 · **Trạng thái:** Planned

## 1. Mục tiêu và phạm vi

Kiểm thử 4 trục độc lập:

1. **Functional/UI:** upload ảnh, correction, gợi ý, lọc món, xem công thức, auth/favorites, CMS.
2. **API/Database:** request/response theo OpenAPI, ràng buộc PK/FK, lỗi chuẩn, pagination, migrations, consistency.
3. **AI:** chất lượng object detection theo test set độc lập và khả năng người dùng khắc phục sai sót.
4. **Security/Privacy/Performance:** quyền user/admin, RLS, ảnh, tải, latency, dữ liệu nguồn.

Một luồng demo tốt không thay thế việc đánh giá AI; một model có mAP tốt cũng không thay thế kiểm thử nghiệp vụ.

## 2. Loại kiểm thử và công cụ

| Loại | Công cụ đề xuất | Bằng chứng |
|---|---|---|
| Backend unit tests | pytest | output tests, coverage (nếu có) |
| Contract/API | pytest + HTTPX / Postman / OpenAPI schema validation | response snapshots, run report |
| Frontend unit | Vitest + React Testing Library (nếu nhóm chọn) | output test report |
| E2E browser | Playwright (nếu nhóm chọn) | trace/screenshot, video cần che dữ liệu |
| Database RLS | Supabase SQL tests hoặc script anon/user A/B/admin | log allow/deny + migration hash |
| AI evaluation | Ultralytics val + báo cáo per-class | metrics, confusion/errors, model+data version |
| Performance | locust/k6 hoặc script load ổn định | p50/p95, CPU/RAM, concurrency |
| Manual UAT | test cases chuẩn + người chấm | sheet kết quả có build, ảnh màn hình |

## 3. Môi trường

**Local:** frontend Vite 5173, backend 8000, Supabase dev; model weights có quyền sử dụng. **Staging/Demo:** dữ liệu test không chứa thông tin cá nhân thật, secret không bị commit. Ghi rõ OS/browser/model version/dataset version/hardware/commit SHA khi báo cáo.

### Dữ liệu mẫu tối thiểu

- >=5 công thức published có required và optional; >=2 món 15 phút và >=2 món >15 phút; cả VN/EU/US.
- Một món draft, một món archived để test hidden.
- >=8 nguyên liệu được map từ nhãn và >=2 alias.
- User A, User B, Admin riêng; Guest không có token.
- Ảnh 2+ nguyên liệu, ảnh không có nguyên liệu, ảnh hỏng, ảnh quá 5 MiB, ảnh định dạng cấm.
- Nguồn kiểm chứng dinh dưỡng/tác quyền có bản ghi mẫu.

## 4. Entry / Exit criteria

**Entry:** SRS, API, migration, seed, model version, bộ ảnh kiểm thử được ghi nhận; test endpoint chạy được; secrets trong env.  
**Exit MVP (đề xuất):**

- Không còn lỗi nghiêm trọng P0 trong chuỗi ảnh → sửa → gợi ý → chi tiết món.
- 100% TC thuộc FR P0 đạt hoặc có ngoại lệ được giảng viên/nhóm chấp thuận bằng văn bản; P1 báo rõ chưa hoàn thành nếu chưa đạt.
- SEC-01…SEC-05 và RLS tests qua; không có đường tự sửa role/admin.
- AI có kết quả Precision/Recall/mAP50/mAP50-95 trên test độc lập (không bắt buộc tự nhận là đạt mục tiêu nếu không đạt).
- Có benchmark latency với cấu hình và số liệu thật, không ghi mục tiêu là số đo.
- OpenAPI hợp lệ và không mâu thuẫn routes khi chạy.
- Nội dung recipe và nutrition không có số kcal/kg giả định hoặc tài sản không rõ giấy phép.

## 5. Mức độ ưu tiên lỗi

| Mức | Diễn giải | Ví dụ |
|---|---|---|
| Blocker | Không thể trình diễn luồng chính hoặc lộ dữ liệu | API recommend luôn lỗi, Admin auth bypass |
| Critical | Sai logic cốt lõi hoặc gợi ý gây hiểu nhầm nghiêm trọng | Món thiếu required lại là ready |
| Major | Hỏng tính năng P1 / giao diện mobile | Favorites lỗi với token hợp lệ |
| Minor | Lỗi thông báo/văn bản ít ảnh hưởng | Nhãn UI không đồng nhất |

## 6. Mẫu ghi kết quả

| Trường | Ví dụ / cách điền |
|---|---|
| Test case ID | TC-10 |
| Build/commit | SHA thực tế, không viết `latest` |
| Env | Browser/OS/API version/DB/migration/model version |
| Input fixture | recipe IDs và ingredient IDs test |
| Expected | Theo test-cases.md |
| Actual | Response/UI đúng thực tế |
| Status | Not run / Pass / Fail / Blocked |
| Evidence | link logs, screenshot, test output |
| Issue | link issue nếu Fail |
| Tester/Date | người chạy và thời điểm thực tế |

## 7. Kế hoạch test theo vòng

1. Review SRS/RTM/API trước coding.
2. Unit scoring (tính tay), validation của DTO và RLS độc lập.
3. Contract test backend với mock AI/DB.
4. Integration thực với Supabase dev + model có dữ liệu.
5. E2E guest và user/admin; thử API lỗi/xâm quyền.
6. AI độc lập trên test giữ cố định, benchmark máy demo, tổng hợp kết quả.
7. UAT và chốt phạm vi trình bày giảng viên.
