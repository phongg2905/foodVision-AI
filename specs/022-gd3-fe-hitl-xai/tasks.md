# Tasks: [GĐ3 - TP14] Giao diện Upload/Camera, Cảnh báo HITL (conf < τ) & Giải thích XAI

- [x] **T01** Tạo nhánh `feat/022-gd3-fe-hitl-xai` từ `main` (`cfaf639`) và khởi tạo đặc tả tại `specs/022-gd3-fe-hitl-xai/`
- [x] **T02** Mở rộng `types.ts`, `client.ts` (`apiPostMultipartWithFallback`), `imageValidation.ts` (kiểm tra `<= 5 MiB`, magic bytes, đọc cờ `EXIF Orientation`) và `aiDetectApi.ts` (`POST /api/v1/ai/detect`)
- [x] **T03** Xây dựng `BoundingBoxStage.tsx` vẽ hộp giới hạn `[0, 1]` khớp chính xác trên cả ảnh ngang và ảnh dọc có `EXIF Orientation`
- [x] **T04** Xây dựng `VisionScanPanel.tsx` & `demoScanFixtures.ts`: tải ảnh/chụp camera, tách `clear_ingredients` (`>= 0.80`) & cảnh báo HITL `uncertain_ingredients` (`< 0.80`), đổi nhãn nguyên liệu, khử trùng UUID và chuyển mượt về nhập tay (`FR-18`) khi `detections=[]` hoặc lỗi `503`/`504`
- [x] **T05** Hiển thị trực quan thanh & bảng đóng góp điểm XAI (`50·C + 25·G + 15·T + 10·P = S`) trên `RecommendationCard.tsx` và `RecipeDetailView.tsx`, nối `scan_id` xuyên suốt `IngredientKitchenView` -> `App` -> `RecommendationResultsView`
- [x] **T06** Viết kiểm thử tự động `VisionScanHitlXai.test.tsx`, chạy vượt qua `typecheck`, `vitest`, `build`, `impeccable detect` và kiểm chứng thị giác Playwright trên `1366px` / `768px` / `360px`
