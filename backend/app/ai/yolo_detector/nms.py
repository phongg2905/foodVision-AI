"""IoU computation, class-wise Non-Maximum Suppression, and HITL gating."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import numpy as np

from app.core.config import get_settings
from app.schemas.ai import BBox, Detection, SuggestedIngredient

from .calibration import _clamp_unit_probability
from .models import (
    BoundingBox,
    DetectedIngredientItem,
    RawBoxPrediction,
)


def _extract_xyxy(box: BBox | BoundingBox | Sequence[float]) -> tuple[float, float, float, float]:
    if isinstance(box, (BBox, BoundingBox)):
        return float(box.x1), float(box.y1), float(box.x2), float(box.y2)
    if len(box) == 4:
        return float(box[0]), float(box[1]), float(box[2]), float(box[3])
    raise ValueError("Box must be BBox, BoundingBox, or a 4-element sequence (x1, y1, x2, y2)")


# ==============================================================================
# THUẬT TOÁN: Độ trùng khớp không gian IoU (Intersection over Union) & Class-wise NMS
# - Công thức (`MATH-01`): IoU(B_p, B_g) = |B_p ∩ B_g| / |B_p ∪ B_g| ∈ [0, 1]
# - Ý tưởng: Xác định hình chữ nhật phần giao giữa hai hộp (chuẩn hóa hoặc tọa độ pixel);
#   diện tích hợp bằng tổng diện tích hai hộp trừ diện tích giao. Dùng trong cả đánh giá
#   và lọc hộp trùng lắp cùng lớp (Greedy Class-wise Non-Maximum Suppression).
# - Độ phức tạp: O(1) cho mỗi cặp hộp; O(K^2) trên K hộp cùng một lớp.
# ==============================================================================
def compute_iou(
    box_a: BBox | BoundingBox | Sequence[float],
    box_b: BBox | BoundingBox | Sequence[float],
) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes."""
    ax1, ay1, ax2, ay2 = _extract_xyxy(box_a)
    bx1, by1, bx2, by2 = _extract_xyxy(box_b)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


# ==============================================================================
# THUẬT TOÁN: Triệt tiêu Cực đại Không Cực trị Vector hóa theo Lớp (Vectorized Class-wise NMS)
# - Bước 1: Phân nhóm các hộp dự đoán thô theo `class_id` để các nguyên liệu khác loại
#           nằm chồng lấp lên nhau trên đĩa không triệt tiêu nhầm nhau.
# - Bước 2: Với lớp chỉ có 1 hộp, giữ nguyên trong O(1); với lớp nhiều hộp, sắp giảm dần
#           theo `confidence` và tính đồng loạt IoU bằng mảng NumPy liên tục (SIMD broadcasting)
#           giữa hộp đỉnh hiện tại với toàn bộ các ứng viên còn lại chưa xét.
# - Bước 3: Hợp nhất kết quả các lớp và sắp xếp giảm dần toàn cục theo độ tự tin.
# - Độ phức tạp: O(sum_c n_c^2) chạy trên C/NumPy thay cho vòng lặp Python thuần.
# ==============================================================================
def apply_classwise_nms(
    predictions: Sequence[RawBoxPrediction],
    *,
    iou_threshold: float,
) -> list[RawBoxPrediction]:
    """Suppress duplicate overlapping normalized boxes within each `class_id`."""
    if not (0.0 < iou_threshold <= 1.0):
        raise ValueError("iou_threshold must be in (0.0, 1.0]")
    if len(predictions) <= 1:
        return list(predictions)

    by_class: dict[int, list[RawBoxPrediction]] = {}
    for pred in predictions:
        by_class.setdefault(pred.class_id, []).append(pred)

    kept: list[RawBoxPrediction] = []
    for cls_preds in by_class.values():
        if len(cls_preds) == 1:
            kept.append(cls_preds[0])
            continue

        ordered = sorted(cls_preds, key=lambda p: p.confidence, reverse=True)
        coords = np.array(
            [(p.x1, p.y1, p.x2, p.y2) for p in ordered],
            dtype=np.float64,
        )
        x1 = coords[:, 0]
        y1 = coords[:, 1]
        x2 = coords[:, 2]
        y2 = coords[:, 3]
        areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
        remaining = np.arange(len(ordered), dtype=np.int64)

        while remaining.size > 0:
            head = int(remaining[0])
            kept.append(ordered[head])
            if remaining.size == 1:
                break
            rest = remaining[1:]
            xx1 = np.maximum(x1[head], x1[rest])
            yy1 = np.maximum(y1[head], y1[rest])
            xx2 = np.minimum(x2[head], x2[rest])
            yy2 = np.minimum(y2[head], y2[rest])
            inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
            union = areas[head] + areas[rest] - inter
            ious = np.where(union > 0.0, inter / union, 0.0)
            remaining = rest[ious <= iou_threshold]

    kept.sort(key=lambda p: p.confidence, reverse=True)
    return kept


# ==============================================================================
# THUẬT TOÁN: Cờ cảnh báo xác nhận con người HITL — Review(x) = 1[p_hat(x) < tau]
# - Ý tưởng (Guo et al., ICML 2017): Khi xác suất dự đoán p_hat nhỏ hơn ngưỡng kiểm
#   duyệt tau lấy từ cấu hình hệ thống, gắn cờ yêu cầu người dùng xác nhận lại nhãn.
# ==============================================================================
def needs_hitl_review(
    confidence: float,
    review_threshold: float | None = None,
) -> bool:
    """Return True when prediction probability falls below configured HITL `tau`."""
    threshold = (
        get_settings().default_review_threshold
        if review_threshold is None
        else float(review_threshold)
    )
    if not (0.0 <= threshold <= 1.0):
        raise ValueError("review_threshold must lie within [0.0, 1.0]")
    return _clamp_unit_probability(confidence) < threshold


# ==============================================================================
# THUẬT TOÁN: Khử trùng lặp nguyên liệu gợi ý theo độ tin cậy cực đại (Max-Pool Aggregation)
# - Ý tưởng: Giữ nguyên toàn bộ hộp phát hiện trong `detections[]`, nhưng gom nhóm
#   theo `ingredient_id` (chỉ nhận nguyên liệu chính `category != 'pantry'`) và lấy
#   `max_confidence` giảm dần cho `suggested_ingredients[]`.
# - Độ phức tạp: O(D log D) với D là số hộp phát hiện hợp lệ.
# ==============================================================================
def aggregate_suggested_ingredients(
    detections: Sequence[Detection | DetectedIngredientItem],
    pantry_ids: set[UUID] | None = None,
) -> list[SuggestedIngredient]:
    """Group detections into unique non-pantry suggested ingredients."""
    excluded = pantry_ids or set()
    best_by_id: dict[UUID, tuple[str, float]] = {}

    for det in detections:
        ing_id = det.ingredient_id
        if ing_id is None or ing_id in excluded:
            continue

        if isinstance(det, DetectedIngredientItem):
            name = det.ingredient_name_vi or det.label
            score = det.calibrated_confidence
        else:
            name = det.ingredient_name or det.class_name
            score = det.confidence

        prev = best_by_id.get(ing_id)
        if prev is None or score > prev[1]:
            best_by_id[ing_id] = (name, score)

    suggestions = [
        SuggestedIngredient(
            ingredient_id=ing_id,
            name_vi=name_vi,
            max_confidence=round(max_conf, 4),
        )
        for ing_id, (name_vi, max_conf) in best_by_id.items()
    ]
    suggestions.sort(key=lambda item: (-item.max_confidence, item.name_vi))
    return suggestions


# ==============================================================================
# THUẬT TOÁN: Phân tách nhóm nguyên liệu rõ ràng và cần xác nhận (`ADR-013` v1.1.0)
# - Tách `suggested_ingredients` thành 2 danh sách phục vụ màn hình xác nhận HITL:
#   * `clear_ingredients`: `max_confidence >= review_threshold` (`needs_confirmation = false`)
#   * `uncertain_ingredients`: `max_confidence < review_threshold` (`needs_confirmation = true`)
# ==============================================================================
def split_clear_and_uncertain_ingredients(
    suggested_ingredients: Sequence[SuggestedIngredient],
    review_threshold: float | None = None,
) -> tuple[list[SuggestedIngredient], list[SuggestedIngredient]]:
    """Split suggested ingredients into (clear_ingredients, uncertain_ingredients) at `tau`."""
    threshold = (
        get_settings().default_review_threshold
        if review_threshold is None
        else float(review_threshold)
    )
    clear = [
        item for item in suggested_ingredients if item.max_confidence >= threshold
    ]
    uncertain = [
        item for item in suggested_ingredients if item.max_confidence < threshold
    ]
    return clear, uncertain
