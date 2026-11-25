import { ApiClientError, apiPostMultipartWithFallback } from './client';
import {
  Detection,
  DetectResponse,
  REVIEW_CONFIDENCE_THRESHOLD,
  SuggestedIngredient,
} from './types';
import {
  inspectImageFile,
  ValidImageInspection,
} from '../utils/imageValidation';

export interface DetectImageOptions {
  saveHistory?: boolean;
}

export interface DetectImageWithMetaResult {
  response: DetectResponse;
  inspection: ValidImageInspection;
}

const ID_CA_CHUA = '11111111-1111-4111-8111-111111111101';
const ID_TRUNG_GA = '11111111-1111-4111-8111-111111111102';
const ID_DAU_HU = '11111111-1111-4111-8111-111111111103';
const ID_DUA_LEO = '11111111-1111-4111-8111-111111111207';

/**
 * Chuẩn hóa cấu trúc DetectResponse đảm bảo:
 * - Khử trùng suggested_ingredients theo max_confidence (TC-07)
 * - Phân tách chính xác clear_ingredients (>= 0.80) và uncertain_ingredients (< 0.80) (ADR-013, AI-03)
 */
export function normalizeDetectResponse(raw: DetectResponse): DetectResponse {
  const detections: Detection[] = (raw.detections ?? []).map((det) => ({
    ...det,
    needs_confirmation:
      Boolean(det.needs_confirmation) ||
      det.confidence < REVIEW_CONFIDENCE_THRESHOLD,
  }));

  const aggregatedMap = new Map<string, SuggestedIngredient>();

  for (const item of raw.suggested_ingredients ?? []) {
    const existing = aggregatedMap.get(item.ingredient_id);
    if (!existing || item.max_confidence > existing.max_confidence) {
      aggregatedMap.set(item.ingredient_id, { ...item });
    }
  }

  if (aggregatedMap.size === 0) {
    for (const det of detections) {
      if (!det.ingredient_id || !det.ingredient_name) continue;
      const existing = aggregatedMap.get(det.ingredient_id);
      if (!existing || det.confidence > existing.max_confidence) {
        aggregatedMap.set(det.ingredient_id, {
          ingredient_id: det.ingredient_id,
          name_vi: det.ingredient_name,
          max_confidence: det.confidence,
        });
      }
    }
  }

  const suggested = Array.from(aggregatedMap.values()).sort(
    (a, b) => b.max_confidence - a.max_confidence
  );

  // F3: Chỉ tự phân tách clear / uncertain từ suggested khi CẢ HAI mảng từ server cùng rỗng
  const bothServerTiersEmpty =
    (raw.clear_ingredients?.length ?? 0) === 0 &&
    (raw.uncertain_ingredients?.length ?? 0) === 0;

  const clear = bothServerTiersEmpty
    ? suggested.filter(
        (item) => item.max_confidence >= REVIEW_CONFIDENCE_THRESHOLD
      )
    : (raw.clear_ingredients ?? []);

  const uncertain = bothServerTiersEmpty
    ? suggested.filter(
        (item) => item.max_confidence < REVIEW_CONFIDENCE_THRESHOLD
      )
    : (raw.uncertain_ingredients ?? []);

  return {
    scan_id: raw.scan_id ?? null,
    model_version: raw.model_version || 'yolo11n-foodvision-v1',
    detections,
    suggested_ingredients: suggested,
    clear_ingredients: clear,
    uncertain_ingredients: uncertain,
  };
}

/**
 * Bộ mô phỏng suy luận thị giác chuẩn hợp đồng OpenAPI v1.1.0 khi chạy độc lập (VITE_API_MOCK_MODE=true / offline):
 * - Hỗ trợ đầy đủ kịch bản DEF-01 (ảnh dọc EXIF), DEF-02 (ảnh mờ detections=[] & vùng < 0.80 cần xác nhận HITL),
 *   TC-07 (2 hộp Cà chua gộp thành 1 suggested_ingredient theo max_confidence), TC-29 (503) & TC-30 (504).
 */
function buildMockDetectResponse(
  file: File,
  inspection: ValidImageInspection
): DetectResponse {
  const lowerName = (file.name || '').toLowerCase();

  if (lowerName.includes('mock-503')) {
    throw new ApiClientError(
      503,
      'MODEL_NOT_READY',
      'Chưa có mô hình nhận diện AI ở trạng thái active.'
    );
  }

  if (lowerName.includes('mock-504')) {
    throw new ApiClientError(
      504,
      'INFERENCE_TIMEOUT',
      'Quá thời gian chờ suy luận ảnh từ dịch vụ AI.'
    );
  }

  // Kịch bản DEF-02 / TC-27: ảnh mờ hoặc ngoài phân phối -> detections = []
  if (
    lowerName.includes('empty') ||
    lowerName.includes('blur') ||
    lowerName.includes('ood') ||
    lowerName.includes('khong-ro')
  ) {
    return {
      scan_id: null,
      model_version: 'yolo11n-foodvision-v1',
      detections: [],
      suggested_ingredients: [],
      clear_ingredients: [],
      uncertain_ingredients: [],
    };
  }

  // Kịch bản DEF-01 / TC-43: ảnh dọc điện thoại có cờ EXIF Orientation != 1
  if (inspection.swapsAxes || lowerName.includes('portrait') || lowerName.includes('exif')) {
    return normalizeDetectResponse({
      scan_id: null,
      model_version: 'yolo11n-foodvision-v1',
      detections: [
        {
          class_index: 0,
          class_name: 'tomato',
          ingredient_id: ID_CA_CHUA,
          ingredient_name: 'Cà chua',
          confidence: 0.94,
          needs_confirmation: false,
          bbox: { x1: 0.16, y1: 0.14, x2: 0.82, y2: 0.5 },
        },
        {
          class_index: 3,
          class_name: 'egg',
          ingredient_id: ID_TRUNG_GA,
          ingredient_name: 'Trứng gà',
          confidence: 0.88,
          needs_confirmation: false,
          bbox: { x1: 0.22, y1: 0.56, x2: 0.78, y2: 0.86 },
        },
      ],
      suggested_ingredients: [
        {
          ingredient_id: ID_CA_CHUA,
          name_vi: 'Cà chua',
          max_confidence: 0.94,
        },
        {
          ingredient_id: ID_TRUNG_GA,
          name_vi: 'Trứng gà',
          max_confidence: 0.88,
        },
      ],
      clear_ingredients: [],
      uncertain_ingredients: [],
    });
  }

  // Mặc định (TC-07 + AI-03 + DEF-02):
  // - 2 hộp Cà chua (0.93 & 0.85) gộp thành 1 suggested_ingredient max_confidence = 0.93 (>= 0.80 -> clear)
  // - 1 hộp Đậu hũ (0.86 >= 0.80 -> clear)
  // - 1 hộp Dưa leo (0.64 < 0.80 -> uncertain, bật cảnh báo HITL Review cho phép xác nhận hoặc đổi nhãn)
  return normalizeDetectResponse({
    scan_id: null,
    model_version: 'yolo11n-foodvision-v1',
    detections: [
      {
        class_index: 0,
        class_name: 'tomato',
        ingredient_id: ID_CA_CHUA,
        ingredient_name: 'Cà chua',
        confidence: 0.93,
        needs_confirmation: false,
        bbox: { x1: 0.08, y1: 0.18, x2: 0.36, y2: 0.74 },
      },
      {
        class_index: 0,
        class_name: 'tomato',
        ingredient_id: ID_CA_CHUA,
        ingredient_name: 'Cà chua',
        confidence: 0.85,
        needs_confirmation: false,
        bbox: { x1: 0.28, y1: 0.44, x2: 0.5, y2: 0.84 },
      },
      {
        class_index: 1,
        class_name: 'tofu',
        ingredient_id: ID_DAU_HU,
        ingredient_name: 'Đậu hũ',
        confidence: 0.86,
        needs_confirmation: false,
        bbox: { x1: 0.46, y1: 0.16, x2: 0.72, y2: 0.62 },
      },
      {
        class_index: 5,
        class_name: 'cucumber',
        ingredient_id: ID_DUA_LEO,
        ingredient_name: 'Dưa leo',
        confidence: 0.64,
        needs_confirmation: true,
        bbox: { x1: 0.68, y1: 0.28, x2: 0.93, y2: 0.82 },
      },
    ],
    suggested_ingredients: [
      {
        ingredient_id: ID_CA_CHUA,
        name_vi: 'Cà chua',
        max_confidence: 0.93,
      },
      {
        ingredient_id: ID_DAU_HU,
        name_vi: 'Đậu hũ',
        max_confidence: 0.86,
      },
      {
        ingredient_id: ID_DUA_LEO,
        name_vi: 'Dưa leo',
        max_confidence: 0.64,
      },
    ],
    clear_ingredients: [],
    uncertain_ingredients: [],
  });
}

/**
 * Gửi ảnh nguyên liệu tới POST /api/v1/ai/detect (multipart/form-data).
 */
export async function detectIngredientsFromImage(
  file: File,
  options?: DetectImageOptions
): Promise<DetectImageWithMetaResult> {
  const inspection = await inspectImageFile(file);
  if (!inspection.ok) {
    throw new ApiClientError(
      inspection.status,
      inspection.code,
      inspection.message
    );
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('save_history', options?.saveHistory ? 'true' : 'false');

  const rawResponse = await apiPostMultipartWithFallback<DetectResponse>(
    '/ai/detect',
    formData,
    () => buildMockDetectResponse(file, inspection)
  );

  return {
    response: normalizeDetectResponse(rawResponse),
    inspection,
  };
}
