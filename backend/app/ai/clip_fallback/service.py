"""Controlled CLIP/VLM candidate fallback orchestration service."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import logging
from typing import Any

from app.ai.image_processor import BBoxInput, ImageInput, crop_region_from_bbox
from app.core.errors import AppError
from .candidates import (
    _resolve_min_similarity,
    _resolve_review_threshold,
    _resolve_top_k,
    filter_kb_candidates,
    should_trigger_fallback,
)
from .embedding_providers import CLIPCosineProvider
from .helpers import _FallbackResultBuilderMixin
from .models import (
    ConfirmationReason,
    FallbackConfig,
    FallbackProvider,
    FallbackResult,
    FallbackStatus,
    InitialYOLOPrediction,
    KBCandidateIngredient,
    MultimodalEmbeddingProvider,
)
from .vlm_provider import _resolve_yolo_with_kb

logger = logging.getLogger(__name__)

# ==============================================================================
# THUẬT TOÁN: Xếp hạng Top-K Có kiểm soát & Phân lớp An toàn Trạng thái UNKNOWN
# - Ý tưởng:
#   1. Chỉ kích hoạt khi qua cổng `should_trigger_fallback`.
#   2. Lọc ứng viên từ Knowledge Base (`is_active == True`, `category != 'pantry'`).
#   3. Tiền xử lý ảnh và cắt vùng `bbox` nếu `bbox` hợp lệ.
#   4. Chạy `FallbackProvider`; nếu lỗi model, ảnh không phải thực phẩm, ảnh ngoài
#      phân phối (OOD), danh sách ứng viên rỗng hoặc không ứng viên nào đạt ngưỡng
#      tương đồng tối thiểu -> trả `FallbackStatus.UNKNOWN` (`candidates=[]`).
#   5. Sắp xếp giảm dần theo `(similarity, name_vi)`, cắt `top_k`, luôn đặt
#      `needs_confirmation=True` và ghi rõ lý do cần xác nhận HITL.
# ==============================================================================
class CLIPFallbackService(_FallbackResultBuilderMixin):
    """Orchestrates conditional CLIP/VLM fallback over Knowledge Base candidates."""

    def __init__(
        self,
        provider: FallbackProvider | MultimodalEmbeddingProvider | None = None,
        *,
        candidate_loader: Callable[[], Sequence[Any]] | None = None,
        config: FallbackConfig | None = None,
    ) -> None:
        if isinstance(provider, MultimodalEmbeddingProvider) and not isinstance(
            provider, FallbackProvider
        ):
            self._provider: FallbackProvider | None = CLIPCosineProvider(provider)
        else:
            self._provider = provider
        self._candidate_loader = candidate_loader
        self._config = config or FallbackConfig()

    @property
    def model_source(self) -> str:
        return self._provider.model_source if self._provider is not None else "unconfigured"

    def suggest(
        self,
        image: ImageInput,
        *,
        candidates: Sequence[Any] | None = None,
        yolo_prediction: Any = None,
        yolo_label: str | None = None,
        yolo_confidence: float | None = None,
        bbox: BBoxInput | None = None,
        requested_by_backend: bool = False,
        top_k: int | None = None,
        min_similarity: float | None = None,
        review_threshold: float | None = None,
    ) -> FallbackResult:
        """Evaluate a region or full image and return controlled HITL suggestions."""
        effective_yolo_input = yolo_prediction if yolo_prediction is not None else yolo_label
        yolo_pred = InitialYOLOPrediction.from_any(
            effective_yolo_input, confidence=yolo_confidence, bbox=bbox
        )
        effective_tau = _resolve_review_threshold(
            review_threshold
            if review_threshold is not None
            else self._config.review_threshold
        )

        kb_loaded = False
        kb_load_failed = False
        kb_candidates: tuple[KBCandidateIngredient, ...] = ()
        if candidates is not None or self._candidate_loader is not None:
            try:
                raw_candidates = (
                    candidates
                    if candidates is not None
                    else (self._candidate_loader() if self._candidate_loader else ())
                )
                kb_candidates = filter_kb_candidates(raw_candidates)
                kb_loaded = True
                yolo_pred = _resolve_yolo_with_kb(
                    effective_yolo_input, yolo_pred, kb_candidates
                )
            except Exception as exc:
                kb_load_failed = True
                logger.warning(
                    "Knowledge Base candidate loading failed: %s", type(exc).__name__
                )

        should_run, trigger = should_trigger_fallback(
            yolo_pred,
            review_threshold=effective_tau,
            requested_by_backend=requested_by_backend,
        )
        if not should_run:
            return FallbackResult(
                status=FallbackStatus.SKIPPED,
                activated=False,
                needs_confirmation=False,
                candidates=[],
                model_source="yolo_primary",
                trigger_reason=None,
                confirmation_reasons=[],
                confirmation_message_vi=(
                    "Kết quả YOLO đã có nhãn hợp lệ và đạt ngưỡng tin cậy, "
                    "không cần kích hoạt CLIP/VLM fallback."
                ),
                initial_yolo_label=yolo_pred.display_label,
                initial_yolo_confidence=yolo_pred.confidence,
            )

        if kb_load_failed:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.MODEL_ERROR,
                message_vi="Không thể tải danh sách nhãn ứng viên từ Knowledge Base; vui lòng chọn nguyên liệu thủ công.",
                yolo_pred=yolo_pred,
            )

        if not kb_loaded or not kb_candidates:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.EMPTY_CANDIDATE_CATALOG,
                message_vi="Danh sách nhãn ứng viên hợp lệ từ Knowledge Base đang rỗng; vui lòng tìm kiếm thủ công.",
                yolo_pred=yolo_pred,
            )

        try:
            region = crop_region_from_bbox(
                image,
                yolo_pred.bbox,
                padding_ratio=self._config.crop_padding_ratio,
                strict_bbox=self._config.strict_bbox,
            )
        except (AppError, ValueError) as exc:
            logger.warning("Fallback image preprocessing/cropping failed: %s", type(exc).__name__)
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.OUT_OF_DISTRIBUTION,
                message_vi="Ảnh đầu vào hoặc vùng cắt không hợp lệ để trích xuất đặc trưng; vui lòng xác nhận thủ công.",
                yolo_pred=yolo_pred,
            )

        if self._provider is None:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.MODEL_ERROR,
                message_vi="Chưa cấu hình provider CLIP/VLM; vui lòng chọn nguyên liệu thủ công.",
                yolo_pred=yolo_pred,
                was_cropped=region.was_cropped,
            )

        try:
            assessment = self._provider.assess_candidates(region.rgb_array, kb_candidates)
        except Exception as exc:
            logger.warning("Multimodal provider inference failed: %s", type(exc).__name__)
            cause_str = f"{exc} {getattr(exc, '__cause__', '')}"
            err_msg = (
                "Provider VLM trả về HTTP 402 Payment Required (tài khoản Ollama Cloud chưa nạp credit); "
                "có thể nạp credit tại ollama.com/plans, chạy Ollama local (127.0.0.1:11434/v1) hoặc đổi sang khóa Gemini Free Tier."
                if "402" in cause_str or "Payment Required" in cause_str
                else "Mô hình hỗ trợ CLIP/VLM gặp sự cố khi suy luận; vui lòng chọn nguyên liệu thủ công."
            )
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.MODEL_ERROR,
                message_vi=err_msg,
                yolo_pred=yolo_pred,
                was_cropped=region.was_cropped,
            )

        if assessment.is_non_food:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.NON_FOOD_INPUT,
                message_vi="Ảnh hoặc vùng cắt được đánh giá không phải thực phẩm; không gợi ý nguyên liệu tự động.",
                yolo_pred=yolo_pred,
                was_cropped=region.was_cropped,
                model_source=assessment.model_source,
                score_type=assessment.score_type,
            )

        if assessment.is_out_of_distribution:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.OUT_OF_DISTRIBUTION,
                message_vi="Ảnh nằm ngoài phân phối nhận diện thực phẩm đã biết; vui lòng chọn nguyên liệu thủ công.",
                yolo_pred=yolo_pred,
                was_cropped=region.was_cropped,
                model_source=assessment.model_source,
                score_type=assessment.score_type,
            )

        effective_min_sim = _resolve_min_similarity(
            min_similarity
            if min_similarity is not None
            else self._config.min_similarity
        )
        effective_top_k = _resolve_top_k(
            top_k if top_k is not None else self._config.top_k,
            len(kb_candidates),
        )
        if effective_top_k <= 0:
            return self._unknown_result(
                trigger=trigger,
                reason=ConfirmationReason.NO_TRUSTWORTHY_CANDIDATE,
                message_vi="Cấu hình số lượng gợi ý top_k không cho phép trả ứng viên.",
                yolo_pred=yolo_pred,
                was_cropped=region.was_cropped,
                model_source=assessment.model_source,
                score_type=assessment.score_type,
            )

        return self._evaluate_assessment_scores(
            assessment=assessment,
            kb_candidates=kb_candidates,
            effective_min_sim=effective_min_sim,
            effective_top_k=effective_top_k,
            trigger=trigger,
            yolo_pred=yolo_pred,
            was_cropped=region.was_cropped,
            bbox_valid=region.bbox_valid,
        )
