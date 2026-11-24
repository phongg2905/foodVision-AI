# Implementation Plan: [GĐ3 - TP14] Upload/Camera, BBox EXIF, Xác nhận HITL & Giải thích XAI

**Branch**: `feat/022-gd3-fe-hitl-xai` | **Date**: 2026-11-17 | **Spec**: [spec.md](./spec.md)

## Summary
Hoàn thiện luồng Nhận thức — Tương tác Người-Máy — Giải thích (`TP 14`) trên Frontend cho Thẻ Trello `#22`:
1. Tích hợp client `POST /api/v1/ai/detect` (`multipart/form-data`) kèm kiểm tra sớm ở trình duyệt (`<= 5 MiB`, magic bytes `JPEG`/`PNG`/`WebP`, đọc cờ `EXIF Orientation`) và cơ chế bảo toàn mã lỗi nghiệp vụ `413` / `415` / `422` / `503` / `504`.
2. Xây dựng `VisionScanPanel` và `BoundingBoxStage` bên trong Thanh Tủ Bếp Ngang (Phương án A): khung ảnh shrink-wrap theo đúng tỷ lệ sau xoay `EXIF` (`image-orientation: from-image`) giúp hộp giới hạn `bbox` `[0, 1]` khớp tuyệt đối trên cả ảnh ngang và ảnh dọc điện thoại.
3. Xây dựng bảng duyệt HITL tách rõ `clear_ingredients` (`>= 0.80`, tích sẵn) và `uncertain_ingredients` (`< 0.80`, gắn huy hiệu `Cần kiểm tra lại`, cho phép tích xác nhận hoặc đổi nhãn tại chỗ), khử trùng lặp UUID (`TC-08`), truyền `scan_id` sang `POST /api/v1/recommendations`, và chuyển mượt về ô tìm tiếng Việt (`FR-18`) khi `detections=[]` hoặc lỗi `503`/`504`.
4. Hiển thị trực quan thanh phân rã đóng góp điểm tuyến tính **XAI (`50·C + 25·G + 15·T + 10·P = S`)** đơn sắc ấm trên `RecommendationCard` và bảng chi tiết XAI trên `RecipeDetailView`.

## Constitution & Design System Check
- **Single-Owner Scope**: Chỉ tạo/sửa file trong `frontend/` và `specs/022-gd3-fe-hitl-xai/`. Không chạm `backend/`, `supabase/`, `docs/`.
- **Privacy & Non-Hallucination (`BR-03`, `BR-05`, `BR-09`)**: Không lưu ảnh xuống `localStorage`/`sessionStorage`; giải phóng `URL.createObjectURL` khi đổi ảnh hoặc đóng khay; không ước lượng `gram`/`kcal` từ diện tích `bbox`.
- **Anti-AI-Slop & NEWTASTE Craft**: Giữ nguyên bảng màu ấm `#E8D8C6` / `#FFF8F0` / `#EFE2D2` / `#B4490E`, không thêm icon trang trí thừa, thanh điểm XAI dùng sắc độ đất nung ấm đồng nhất thay vì 4 màu cầu vồng.

## Project Structure Additions
```text
frontend/src/
├── shared/
│   ├── api/
│   │   ├── types.ts                      # + BBox, Detection, SuggestedIngredient, DetectResponse, scan_id
│   │   ├── client.ts                     # + apiPostMultipartWithFallback (giữ nguyên lỗi 4xx/503/504 có mã lỗi)
│   │   └── aiDetectApi.ts                # Client POST /api/v1/ai/detect + mock fallback chuẩn schema
│   └── utils/
│       └── imageValidation.ts            # Kiểm tra <= 5 MiB, magic bytes JPEG/PNG/WebP & đọc EXIF Orientation
├── features/
│   ├── vision/
│   │   ├── VisionScanPanel.tsx           # Giao diện Upload/Camera, HITL Review (< 0.80), đổi nhãn & fallback FR-18
│   │   ├── components/
│   │   │   └── BoundingBoxStage.tsx      # Khung vẽ bbox [0, 1] bám sát ảnh upright sau xoay EXIF
│   │   ├── utils/
│   │   │   └── demoScanFixtures.ts       # Bộ ảnh mẫu tạo trên RAM (gồm cả JPEG có cờ EXIF Orientation = 6)
│   │   └── __tests__/
│   │       └── VisionScanHitlXai.test.tsx # Kiểm thử tự động toàn bộ TC-05..08, TC-27, TC-29..30, TC-43, DEF-01..02, DEF-10
│   ├── search/IngredientKitchenView.tsx  # Kết nối nút Quét ảnh AI mở VisionScanPanel & đồng bộ nguyên liệu/scan_id
│   ├── recommend/
│   │   ├── RecommendationResultsView.tsx # Truyền scan_id vào POST /api/v1/recommendations
│   │   └── components/RecommendationCard.tsx # Thanh & chỉ số đóng góp điểm XAI trực quan 4 tiêu chí
│   └── recipes/RecipeDetailView.tsx      # Bảng phân rã chi tiết đóng góp điểm XAI 4 tiêu chí
```
