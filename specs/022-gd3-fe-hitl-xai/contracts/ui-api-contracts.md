# UI ↔ API Contracts: Thẻ #22 (Vision Detect, HITL & XAI)

## 1. `POST /api/v1/ai/detect` (`multipart/form-data`)
- **Form Fields**:
  - `file`: Binary image (`image/jpeg`, `image/png`, `image/webp`, `<= 5 MiB` = `5,242,880` bytes)
  - `save_history`: `'false'` (mặc định cho Guest / GĐ3; `'true'` yêu cầu Bearer JWT ở GĐ4)
- **Response `200 OK` (`DetectResponse`)**:
  - `scan_id`: `string | null`
  - `model_version`: `string`
  - `detections`: `Array<{ class_index, class_name, ingredient_id, ingredient_name, confidence, needs_confirmation, bbox: { x1, y1, x2, y2 } }>` (tọa độ chuẩn hóa `[0, 1]` trên ảnh đã xoay `EXIF Orientation`)
  - `suggested_ingredients`: `Array<{ ingredient_id, name_vi, max_confidence }>`
  - `clear_ingredients`: `SuggestedIngredient[]` (`max_confidence >= 0.80`)
  - `uncertain_ingredients`: `SuggestedIngredient[]` (`max_confidence < 0.80`)
- **Error Responses**:
  - `413 IMAGE_TOO_LARGE`
  - `415 UNSUPPORTED_IMAGE_TYPE`
  - `422 INVALID_IMAGE`
  - `503 MODEL_NOT_READY`
  - `504 INFERENCE_TIMEOUT`

## 2. `POST /api/v1/recommendations` (liên kết XAI & `scan_id`)
- Truyền `scan_id` nhận được từ `/api/v1/ai/detect` (hoặc `null` khi chuyển sang nhập tay `FR-18`).
- Hiển thị trực quan `score_contributions: { C, G, T, P }` thỏa $\text{C} + \text{G} + \text{T} + \text{P} = S$ (`50*C_raw + 25*G_raw + 15*T_raw + 10*P_raw`) và `explanation_vi`.
