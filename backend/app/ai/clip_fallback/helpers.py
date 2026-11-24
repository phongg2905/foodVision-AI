"""Confirmation reason builder and safe UNKNOWN fallback factory."""

from __future__ import annotations

from .candidates import _env_float

from collections.abc import Sequence
from typing import Any
from app.ai.image_processor import ImageInput

import math
from .models import (
    KBCandidateIngredient,
    ConfirmationReason,
    FallbackConfig,
    FallbackResult,
    FallbackStatus,
    FallbackTriggerReason,
    InitialYOLOPrediction,
    ProviderAssessment,
    RankedCandidate,
    ScoreMetricType,
)


class _FallbackResultBuilderMixin:
    """Helper mixin constructing grounded confirmation reasons and UNKNOWN results."""

    _config: FallbackConfig

    @property
    def model_source(self) -> str:  # pragma: no cover - overridden in subclass
        return "unconfigured"

    def _build_confirmation_reasons(
        self,
        *,
        trigger: FallbackTriggerReason | None,
        yolo_pred: InitialYOLOPrediction,
        ranked: Sequence[RankedCandidate],
        bbox_valid: bool | None,
    ) -> list[ConfirmationReason]:
        reasons: list[ConfirmationReason] = []
        if trigger == FallbackTriggerReason.LOW_DETECTOR_CONFIDENCE:
            reasons.append(ConfirmationReason.LOW_DETECTOR_CONFIDENCE)
        elif trigger in (
            FallbackTriggerReason.UNRESOLVED_YOLO_LABEL,
            FallbackTriggerReason.NO_DETECTOR_PREDICTION,
        ):
            reasons.append(ConfirmationReason.UNRESOLVED_INITIAL_LABEL)
        elif trigger == FallbackTriggerReason.BACKEND_REQUESTED:
            reasons.append(ConfirmationReason.BACKEND_FORCED_REVIEW)

        reasons.append(ConfirmationReason.UNCALIBRATED_SIMILARITY)

        if (
            yolo_pred.ingredient_id is not None
            and ranked
            and ranked[0].ingredient_id != yolo_pred.ingredient_id
        ):
            reasons.append(ConfirmationReason.DETECTOR_FALLBACK_DISAGREEMENT)

        amb_margin = (
            self._config.ambiguity_margin
            if self._config.ambiguity_margin is not None
            else _env_float("CLIP_AMBIGUITY_MARGIN")
        )
        if (
            amb_margin is not None
            and len(ranked) >= 2
            and (ranked[0].similarity - ranked[1].similarity) <= amb_margin
        ):
            reasons.append(ConfirmationReason.CLOSE_CANDIDATE_SCORES)

        if bbox_valid is False:
            reasons.append(ConfirmationReason.INVALID_BBOX_FULL_IMAGE_USED)
        return reasons

    def _unknown_result(
        self,
        *,
        trigger: FallbackTriggerReason | None,
        reason: ConfirmationReason,
        message_vi: str,
        yolo_pred: InitialYOLOPrediction,
        was_cropped: bool = False,
        model_source: str | None = None,
        score_type: ScoreMetricType = ScoreMetricType.COSINE_SIMILARITY,
    ) -> FallbackResult:
        return FallbackResult(
            status=FallbackStatus.UNKNOWN,
            activated=True,
            needs_confirmation=True,
            candidates=[],
            model_source=model_source or self.model_source,
            trigger_reason=trigger,
            confirmation_reasons=[reason],
            confirmation_message_vi=message_vi,
            score_type=score_type,
            is_calibrated_probability=False,
            was_cropped=was_cropped,
            initial_yolo_label=yolo_pred.display_label,
            initial_yolo_confidence=yolo_pred.confidence,
        )

    def assist_detections(
        self,
        image: ImageInput,
        detections: Any,
        *,
        candidates: Sequence[Any] | None = None,
        requested_by_backend: bool = False,
        fallback_on_empty_detections: bool = True,
        top_k: int | None = None,
        min_similarity: float | None = None,
        review_threshold: float | None = None,
    ) -> list[FallbackResult]:
        """Run conditional fallback across YOLO detections (or full image if empty)."""
        det_items: Sequence[Any] = (
            getattr(detections, "detections")
            if hasattr(detections, "detections")
            else (detections or ())
        )
        if not det_items:
            if not (fallback_on_empty_detections or requested_by_backend):
                return []
            return [
                self.suggest(
                    image,
                    candidates=candidates,
                    yolo_prediction=None,
                    requested_by_backend=requested_by_backend,
                    top_k=top_k,
                    min_similarity=min_similarity,
                    review_threshold=review_threshold,
                )
            ]

        return [
            self.suggest(
                image,
                candidates=candidates,
                yolo_prediction=det,
                requested_by_backend=requested_by_backend,
                top_k=top_k,
                min_similarity=min_similarity,
                review_threshold=review_threshold,
            )
            for det in det_items
        ]

    # ==========================================================================
    # THUẬT TOÁN: Lọc Ngưỡng Tương đồng, Kiểm tra Biên OOD & Sắp xếp Top-K Ứng viên
    # - Kẹp điểm cosine vào [-1, 1], kiểm tra biên độ chênh lệch top-1 vs top-2
    #   (`ood_min_margin`) để phát hiện phổ điểm phẳng bất thường (OOD), sau đó
    #   lọc `score >= min_similarity` và sắp xếp tất định `(-similarity, name_vi, id)`.
    # ==========================================================================
    def _evaluate_assessment_scores(
        self,
        *,
        assessment: ProviderAssessment,
        kb_candidates: Sequence[KBCandidateIngredient],
        effective_min_sim: float,
        effective_top_k: int,
        trigger: FallbackTriggerReason | None,
        yolo_pred: InitialYOLOPrediction,
        was_cropped: bool,
        bbox_valid: bool | None,
    ) -> FallbackResult:
        kb_by_id = {cand.ingredient_id: cand for cand in kb_candidates}
        all_valid_scores: list[float] = []
        passing_candidates: list[RankedCandidate] = []

        for cand_id, raw_score in assessment.scores_by_id.items():
            kb_item = kb_by_id.get(cand_id)
            if kb_item is None or not isinstance(raw_score, (int, float)):
                continue
            score_val = float(raw_score)
            if not math.isfinite(score_val):
                continue
            clamped = max(-1.0, min(1.0, score_val))
            all_valid_scores.append(clamped)
            if clamped >= effective_min_sim:
                passing_candidates.append(
                    RankedCandidate(
                        ingredient_id=kb_item.ingredient_id,
                        name_vi=kb_item.name_vi,
                        similarity=round(clamped, 4),
                        slug=kb_item.slug or None,
                        model_source=assessment.model_source,
                        needs_confirmation=True,
                        score_type=assessment.score_type,
                        is_calibrated_probability=False,
                    )
                )

        all_valid_scores.sort(reverse=True)
        ood_margin = (
            self._config.ood_min_margin
            if self._config.ood_min_margin is not None
            else _env_float("CLIP_OOD_MIN_MARGIN")
        )
        if (
            ood_margin is not None
            and len(all_valid_scores) >= 2
            and (all_valid_scores[0] - all_valid_scores[1]) < ood_margin
        ):
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.OUT_OF_DISTRIBUTION,
                message_vi="Phổ điểm tương đồng phẳng bất thường (nghi ngờ ngoài phân phối); cần chọn nguyên liệu thủ công.",
                yolo_pred=yolo_pred,
                was_cropped=was_cropped,
                model_source=assessment.model_source,
                score_type=assessment.score_type,
            )

        if not passing_candidates:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.NO_TRUSTWORTHY_CANDIDATE,
                message_vi="Không có nguyên liệu ứng viên nào đạt ngưỡng tương đồng tin cậy; vui lòng tìm kiếm thủ công.",
                yolo_pred=yolo_pred,
                was_cropped=was_cropped,
                model_source=assessment.model_source,
                score_type=assessment.score_type,
            )

        passing_candidates.sort(
            key=lambda item: (-item.similarity, item.name_vi, str(item.ingredient_id))
        )
        selected = passing_candidates[:effective_top_k]
        reasons = self._build_confirmation_reasons(
            trigger=trigger,
            yolo_pred=yolo_pred,
            ranked=passing_candidates,
            bbox_valid=bbox_valid,
        )
        return FallbackResult(
            status=FallbackStatus.SUGGESTED,
            activated=True,
            needs_confirmation=True,
            candidates=selected,
            model_source=assessment.model_source,
            trigger_reason=trigger,
            confirmation_reasons=reasons,
            confirmation_message_vi=(
                "Gợi ý từ mô hình đa phương thức dựa trên độ tương đồng đặc trưng "
                "(không phải xác suất nhận diện chính xác); vui lòng kiểm tra và xác nhận."
            ),
            score_type=assessment.score_type,
            is_calibrated_probability=False,
            was_cropped=was_cropped,
            initial_yolo_label=yolo_pred.display_label,
            initial_yolo_confidence=yolo_pred.confidence,
        )
