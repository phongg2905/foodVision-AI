"""Bounded inference execution and calibrated HITL post-processing mixin."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import logging
import math

import numpy as np

from app.core.errors import AppError
from .calibration import _clamp_unit_probability
from .config import DetectorConfig
from .exceptions import (
    DetectorConfigurationError,
    DetectorInferenceTimeoutError,
)
from .mapping import normalize_class_mapping
from .models import (
    BoundingBox,
    ClassMappingInput,
    ConfidenceCalibrator,
    ConfirmationStatus,
    DetectedIngredientItem,
    LabelMappingEntry,
    RawBoxPrediction,
    YOLOInferenceBackend,
)
from .nms import (
    apply_classwise_nms,
    needs_hitl_review,
)

logger = logging.getLogger(__name__)


class _DetectorPostprocessMixin:
    """Mixin executing timeout-bounded inference, calibration, NMS, and label mapping."""

    _config: DetectorConfig
    _calibrator: ConfidenceCalibrator
    _backend: YOLOInferenceBackend
    _executor: ThreadPoolExecutor
    model_version: str
    confidence_threshold: float
    review_threshold: float
    timeout_ms: int

    def _execute_bounded_inference(
        self, rgb_image: np.ndarray
    ) -> Sequence[RawBoxPrediction]:
        self.load()
        timeout_sec = self.timeout_ms / 1000.0
        future = self._executor.submit(
            self._backend.predict_raw,
            rgb_image,
            confidence_threshold=self.confidence_threshold,
        )
        try:
            return future.result(timeout=timeout_sec)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise DetectorInferenceTimeoutError(
                "Quá thời gian chờ suy luận ảnh từ dịch vụ AI.",
                details={"timeout_ms": self.timeout_ms},
            ) from exc
        except AppError:
            raise
        except Exception as exc:
            raise DetectorConfigurationError(
                "Lỗi thực thi suy luận từ mô hình nhận diện AI.",
                details={"reason": "inference_execution_failed"},
            ) from exc

    # ==========================================================================
    # THUẬT TOÁN: Ánh xạ lớp thực phẩm, chuẩn hóa hộp giới hạn & phân tách xác suất
    # - Ý tưởng (`FR-04`, `ADR-006`, `BR-12`, Guo et al. ICML 2017):
    #   1. Loại bỏ hộp suy biến hoặc có `raw_confidence < confidence_threshold`.
    #   2. Quy đổi tọa độ về miền chuẩn hóa `[0, 1]` trên khung ảnh đã xoay EXIF;
    #      tùy chọn chạy Class-wise NMS nếu `nms_iou_threshold` được cấu hình.
    #   3. Đối chiếu nghiêm ngặt `class_id` với `effective_mapping`:
    #      - Nếu không có trong mapping: ghi nhận vào `unmapped_class_ids` + cảnh báo
    #        log, TUYỆT ĐỐI không lấy nhãn mặc định từ lớp YOLO/COCO gốc.
    #      - Nếu mục ánh xạ thuộc `pantry` hoặc `inactive`: bỏ qua theo `BR-04`/`BR-12`.
    #   4. Giữ nguyên `confidence` thô của mô hình, đồng thời tính xác suất đúng đã
    #      hiệu chỉnh `calibrated_confidence = calibrator.calibrate(raw_conf, cls_id)`
    #      và suy ra `needs_confirmation = (calibrated_confidence < review_threshold)`.
    # ==========================================================================
    def _postprocess_predictions(
        self,
        raw_predictions: Sequence[RawBoxPrediction],
        *,
        image_width: int,
        image_height: int,
        effective_mapping: Mapping[int, LabelMappingEntry],
    ) -> tuple[list[DetectedIngredientItem], list[int]]:
        normalized_candidates: list[RawBoxPrediction] = []
        for pred in raw_predictions:
            if not (
                math.isfinite(pred.confidence)
                and math.isfinite(pred.x1)
                and math.isfinite(pred.y1)
                and math.isfinite(pred.x2)
                and math.isfinite(pred.y2)
            ):
                continue
            raw_conf = _clamp_unit_probability(pred.confidence)
            if raw_conf < self.confidence_threshold:
                continue

            if pred.normalized:
                nx1, ny1, nx2, ny2 = pred.x1, pred.y1, pred.x2, pred.y2
            else:
                nx1 = pred.x1 / float(image_width)
                ny1 = pred.y1 / float(image_height)
                nx2 = pred.x2 / float(image_width)
                ny2 = pred.y2 / float(image_height)

            cx1 = round(min(1.0, max(0.0, float(nx1))), 5)
            cy1 = round(min(1.0, max(0.0, float(ny1))), 5)
            cx2 = round(min(1.0, max(0.0, float(nx2))), 5)
            cy2 = round(min(1.0, max(0.0, float(ny2))), 5)
            if cx1 >= cx2 or cy1 >= cy2:
                continue

            normalized_candidates.append(
                RawBoxPrediction(
                    class_id=int(pred.class_id),
                    confidence=raw_conf,
                    x1=cx1,
                    y1=cy1,
                    x2=cx2,
                    y2=cy2,
                    normalized=True,
                )
            )

        if (
            self._config.nms_iou_threshold is not None
            and len(normalized_candidates) > 1
        ):
            normalized_candidates = apply_classwise_nms(
                normalized_candidates,
                iou_threshold=self._config.nms_iou_threshold,
            )

        detections: list[DetectedIngredientItem] = []
        unmapped_set: set[int] = set()

        for cand in normalized_candidates:
            mapped = effective_mapping.get(cand.class_id)
            if mapped is None:
                unmapped_set.add(cand.class_id)
                continue
            if mapped.is_pantry or mapped.category == "pantry" or not mapped.is_active:
                continue

            raw_score = round(cand.confidence, 4)
            calibrated_score = round(
                self._calibrator.calibrate(cand.confidence, class_id=cand.class_id),
                4,
            )
            requires_review = needs_hitl_review(calibrated_score, self.review_threshold)
            status: ConfirmationStatus = (
                "needs_confirmation" if requires_review else "confident"
            )

            detections.append(
                DetectedIngredientItem(
                    class_id=cand.class_id,
                    label=mapped.class_name,
                    confidence=raw_score,
                    calibrated_confidence=calibrated_score,
                    is_calibrated=self._calibrator.is_calibrated,
                    bounding_box=BoundingBox(
                        x1=cand.x1,
                        y1=cand.y1,
                        x2=cand.x2,
                        y2=cand.y2,
                    ),
                    model_version=self.model_version,
                    needs_confirmation=requires_review,
                    confirmation_status=status,
                    ingredient_id=mapped.ingredient_id,
                    ingredient_name_vi=mapped.ingredient_name_vi,
                )
            )

        if unmapped_set:
            logger.warning(
                "Ignored unmapped YOLO class IDs not present in food class_mapping: %s (model_version=%s)",
                sorted(unmapped_set),
                self.model_version,
            )

        detections.sort(
            key=lambda d: (-d.calibrated_confidence, -d.confidence, d.class_id)
        )
        return detections, sorted(unmapped_set)

    def _resolve_required_mapping(
        self, override_mapping: ClassMappingInput | None
    ) -> Mapping[int, LabelMappingEntry]:
        effective = (
            normalize_class_mapping(override_mapping, strict=True)
            if override_mapping is not None
            else self._config.class_mapping
        )
        if not effective:
            raise DetectorConfigurationError(
                "Chưa cấu hình bảng ánh xạ nhãn thực phẩm (class_mapping) cho mô hình YOLO.",
                details={
                    "reason": "missing_class_mapping",
                    "model_version": self.model_version,
                },
            )
        return effective
