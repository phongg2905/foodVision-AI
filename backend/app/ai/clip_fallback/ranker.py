"""Direct embedding ranker, multimodal protocol, and singleton service factory."""

from __future__ import annotations

from .cosine_provider import CLIPCosineProvider
from .openclip_provider import OpenCLIPEmbeddingProvider

from collections.abc import Sequence
import os
from typing import Any, Protocol, runtime_checkable

import numpy as np

from app.ai.image_processor import BBoxInput, ImageInput
from .candidates import (
    _resolve_min_similarity,
    _resolve_review_threshold,
    _resolve_top_k,
    compute_cosine_similarities,
    compute_cosine_similarity,
    filter_kb_candidates,
    should_trigger_fallback,
)
from .vlm_provider import OpenAICompatibleVLMProvider
from .models import (
    CandidateEmbedding,
    ConfirmationReason,
    FallbackResult,
    FallbackStatus,
    FallbackTriggerReason,
    InitialYOLOPrediction,
    KBCandidateIngredient,
    RankedCandidate,
    ScoreMetricType,
)
from .service import CLIPFallbackService

class CLIPFallbackRanker:
    """Precomputed-embedding candidate ranker preserved for direct vector workflows."""

    def __init__(
        self,
        candidates: Sequence[CandidateEmbedding | KBCandidateIngredient] | None = None,
        *,
        model_source: str = "precomputed_embedding_ranker",
    ) -> None:
        self._candidates = filter_kb_candidates(candidates)
        self._model_source = model_source

    def rank_image_embedding(
        self,
        image_embedding: np.ndarray,
        *,
        top_k: int = 3,
        min_similarity: float | None = None,
    ) -> list[RankedCandidate]:
        """Rank registered non-pantry KB embeddings for explicit HITL confirmation."""
        if not self._candidates or top_k <= 0:
            return []

        threshold = _resolve_min_similarity(min_similarity)
        scored: list[RankedCandidate] = []
        for cand in self._candidates:
            if cand.embedding is None:
                continue
            sim = compute_cosine_similarity(image_embedding, cand.embedding)
            if sim >= threshold:
                scored.append(
                    RankedCandidate(
                        ingredient_id=cand.ingredient_id,
                        name_vi=cand.name_vi,
                        similarity=round(sim, 4),
                        slug=cand.slug or None,
                        model_source=self._model_source,
                        needs_confirmation=True,
                        score_type=ScoreMetricType.COSINE_SIMILARITY,
                        is_calibrated_probability=False,
                    )
                )

        scored.sort(
            key=lambda item: (-item.similarity, item.name_vi, str(item.ingredient_id))
        )
        return scored[:top_k]

    # ==========================================================================
    # THUẬT TOÁN: Xếp hạng Vector Nhúng Ảnh Trực tiếp có Cổng Chặn OOD (Margin & Threshold Gate)
    # - Tính điểm tương đồng Cosine giữa vector ảnh và các vector nguyên liệu ứng viên không thuộc pantry.
    # - Từ chối gán nhãn (`UNKNOWN`) nếu điểm cao nhất dưới `min_similarity` hoặc biên chênh lệch Top-1/Top-2
    #   quá hẹp, luôn bắt buộc gắn cờ xác nhận HITL cho người dùng.
    # ==========================================================================
    def evaluate_image_embedding(
        self,
        image_embedding: np.ndarray,
        *,
        yolo_prediction: Any = None,
        requested_by_backend: bool = False,
        top_k: int = 3,
        min_similarity: float | None = None,
        review_threshold: float | None = None,
    ) -> FallbackResult:
        """Evaluate a precomputed image embedding through the full safety & UNKNOWN gate."""
        yolo_pred = InitialYOLOPrediction.from_any(yolo_prediction)
        should_run, trigger = should_trigger_fallback(
            yolo_pred,
            review_threshold=review_threshold,
            requested_by_backend=requested_by_backend,
        )
        if not should_run:
            return FallbackResult(
                status=FallbackStatus.SKIPPED,
                activated=False,
                needs_confirmation=False,
                candidates=[],
                model_source="yolo_primary",
                initial_yolo_label=yolo_pred.display_label,
                initial_yolo_confidence=yolo_pred.confidence,
            )

        if not self._candidates:
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source=self._model_source,
                trigger_reason=trigger,
                confirmation_reasons=[ConfirmationReason.EMPTY_CANDIDATE_CATALOG],
                confirmation_message_vi="Danh sách nhãn ứng viên hợp lệ từ Knowledge Base đang rỗng.",
                initial_yolo_label=yolo_pred.display_label,
                initial_yolo_confidence=yolo_pred.confidence,
            )

        try:
            ranked = self.rank_image_embedding(
                image_embedding, top_k=top_k, min_similarity=min_similarity
            )
        except Exception:
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source=self._model_source,
                trigger_reason=trigger,
                confirmation_reasons=[ConfirmationReason.MODEL_ERROR],
                confirmation_message_vi="Vector đặc trưng không hợp lệ hoặc lỗi đối sánh.",
                initial_yolo_label=yolo_pred.display_label,
                initial_yolo_confidence=yolo_pred.confidence,
            )

        if not ranked:
            return FallbackResult(
                status=FallbackStatus.UNKNOWN,
                activated=True,
                needs_confirmation=True,
                candidates=[],
                model_source=self._model_source,
                trigger_reason=trigger,
                confirmation_reasons=[ConfirmationReason.NO_TRUSTWORTHY_CANDIDATE],
                confirmation_message_vi="Không có ứng viên nào đạt ngưỡng tương đồng tối thiểu.",
                initial_yolo_label=yolo_pred.display_label,
                initial_yolo_confidence=yolo_pred.confidence,
            )

        return FallbackResult(
            status=FallbackStatus.SUGGESTED,
            activated=True,
            needs_confirmation=True,
            candidates=ranked,
            model_source=self._model_source,
            trigger_reason=trigger,
            confirmation_reasons=[ConfirmationReason.UNCALIBRATED_SIMILARITY],
            confirmation_message_vi=(
                "Điểm tương đồng Cosine chỉ dùng để gợi ý xếp hạng, cần người dùng xác nhận."
            ),
            initial_yolo_label=yolo_pred.display_label,
            initial_yolo_confidence=yolo_pred.confidence,
        )


@runtime_checkable
class MultimodalFallbackProtocol(Protocol):
    """Service-level protocol injectable into FastAPI routes and orchestrators."""

    @property
    def model_source(self) -> str: ...

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
    ) -> FallbackResult: ...

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
    ) -> list[FallbackResult]: ...


def get_clip_fallback_service() -> CLIPFallbackService:
    """FastAPI dependency factory building a provider from environment without hardcoding."""
    vlm_model = (os.getenv("VLM_MODEL_NAME") or "").strip()
    clip_model = (os.getenv("CLIP_MODEL_NAME") or "").strip()
    provider: FallbackProvider | None = None
    if vlm_model:
        provider = OpenAICompatibleVLMProvider()
    elif clip_model:
        provider = CLIPCosineProvider(OpenCLIPEmbeddingProvider())
    return CLIPFallbackService(provider=provider)
