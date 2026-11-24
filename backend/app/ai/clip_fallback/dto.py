"""Prediction, ranked candidate, and provider protocol DTOs for CLIP fallback."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

import numpy as np

from .enums import (
    ConfirmationReason,
    FallbackStatus,
    FallbackTriggerReason,
    KBCandidateIngredient,
    ScoreMetricType,
)

@dataclass(frozen=True, slots=True)
class InitialYOLOPrediction:
    """Normalized view of an upstream YOLO detector prediction for a region."""

    class_index: int | None = None
    class_name: str | None = None
    ingredient_id: UUID | None = None
    ingredient_name: str | None = None
    confidence: float | None = None
    bbox: Any = None
    needs_confirmation: bool = False
    is_unresolved: bool = False

    @property
    def display_label(self) -> str | None:
        raw = self.ingredient_name or self.class_name
        return raw.strip() if isinstance(raw, str) and raw.strip() else None

    # ==========================================================================
    # THUẬT TOÁN: Chuẩn hóa Đa hình Dự đoán Đầu vào từ YOLO sang `InitialYOLOPrediction`
    # - Chấp nhận object ORM/Pydantic/dataclass hoặc dict thô, trích xuất đồng nhất độ tự tin
    #   hiệu chuẩn, tọa độ hộp giới hạn và cờ xác nhận HITL để cổng fallback đánh giá.
    # ==========================================================================
    @classmethod
    def from_any(
        cls,
        yolo_input: Any = None,
        *,
        confidence: float | None = None,
        bbox: Any = None,
    ) -> InitialYOLOPrediction:
        """Adapt `Detection`, `DetectedIngredientItem`, `Mapping`, `str`, or `None`."""
        if isinstance(yolo_input, InitialYOLOPrediction):
            return cls(
                class_index=yolo_input.class_index,
                class_name=yolo_input.class_name,
                ingredient_id=yolo_input.ingredient_id,
                ingredient_name=yolo_input.ingredient_name,
                confidence=confidence if confidence is not None else yolo_input.confidence,
                bbox=bbox if bbox is not None else yolo_input.bbox,
                needs_confirmation=yolo_input.needs_confirmation,
                is_unresolved=yolo_input.is_unresolved,
            )
        if yolo_input is None:
            return cls(confidence=confidence, bbox=bbox)
        if isinstance(yolo_input, str):
            stripped = yolo_input.strip()
            return cls(
                class_name=stripped or None,
                confidence=confidence,
                bbox=bbox,
                is_unresolved=not bool(stripped),
            )
        if isinstance(yolo_input, Mapping):
            raw_id = yolo_input.get("ingredient_id")
            ing_id = _coerce_uuid(raw_id)
            cls_idx = yolo_input.get("class_index")
            if cls_idx is None:
                cls_idx = yolo_input.get("class_id")
            cls_name = yolo_input.get("class_name") or yolo_input.get("label")
            ing_name = yolo_input.get("ingredient_name") or yolo_input.get(
                "ingredient_name_vi"
            )
            det_conf = (
                yolo_input.get("calibrated_confidence")
                if yolo_input.get("is_calibrated")
                else yolo_input.get("confidence")
            )
            raw_conf = confidence if confidence is not None else det_conf
            resolved_bbox = (
                bbox
                if bbox is not None
                else (
                    yolo_input.get("bbox")
                    if yolo_input.get("bbox") is not None
                    else yolo_input.get("bounding_box")
                )
            )
            needs_conf = bool(yolo_input.get("needs_confirmation", False)) or (
                yolo_input.get("confirmation_status") == "needs_confirmation"
            )
            return cls(
                class_index=int(cls_idx) if cls_idx is not None else None,
                class_name=cls_name,
                ingredient_id=ing_id,
                ingredient_name=ing_name,
                confidence=float(raw_conf) if raw_conf is not None else None,
                bbox=resolved_bbox,
                needs_confirmation=needs_conf,
                is_unresolved=bool(yolo_input.get("is_unresolved", False)),
            )

        raw_id = getattr(yolo_input, "ingredient_id", None)
        cls_idx = getattr(yolo_input, "class_index", None)
        if cls_idx is None:
            cls_idx = getattr(yolo_input, "class_id", None)
        cls_name = getattr(yolo_input, "class_name", None) or getattr(
            yolo_input, "label", None
        )
        ing_name = getattr(yolo_input, "ingredient_name", None) or getattr(
            yolo_input, "ingredient_name_vi", None
        )
        is_cal = bool(getattr(yolo_input, "is_calibrated", False))
        det_conf = (
            getattr(yolo_input, "calibrated_confidence", None)
            if is_cal
            else getattr(yolo_input, "confidence", None)
        )
        raw_conf = confidence if confidence is not None else det_conf
        obj_bbox = getattr(yolo_input, "bbox", None)
        if obj_bbox is None:
            obj_bbox = getattr(yolo_input, "bounding_box", None)
        needs_conf = bool(getattr(yolo_input, "needs_confirmation", False)) or (
            getattr(yolo_input, "confirmation_status", None) == "needs_confirmation"
        )
        return cls(
            class_index=int(cls_idx) if cls_idx is not None else None,
            class_name=cls_name,
            ingredient_id=_coerce_uuid(raw_id),
            ingredient_name=ing_name,
            confidence=float(raw_conf) if raw_conf is not None else None,
            bbox=bbox if bbox is not None else obj_bbox,
            needs_confirmation=needs_conf,
            is_unresolved=bool(getattr(yolo_input, "is_unresolved", False)),
        )


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    """Controlled candidate suggestion returned to the HITL UI (never auto-committed)."""

    ingredient_id: UUID
    name_vi: str
    similarity: float
    slug: str | None = None
    model_source: str | None = None
    needs_confirmation: bool = True
    score_type: ScoreMetricType = ScoreMetricType.COSINE_SIMILARITY
    is_calibrated_probability: bool = False

    @property
    def similarity_score(self) -> float:
        """Alias emphasizing directional similarity rather than probability."""
        return self.similarity


@dataclass(frozen=True, slots=True)
class FallbackResult:
    """Structured output of CLIP/VLM candidate assistance for HITL review."""

    status: FallbackStatus
    activated: bool
    needs_confirmation: bool
    candidates: list[RankedCandidate]
    model_source: str
    trigger_reason: FallbackTriggerReason | None = None
    confirmation_reasons: list[ConfirmationReason] = field(default_factory=list)
    confirmation_message_vi: str = ""
    score_type: ScoreMetricType = ScoreMetricType.COSINE_SIMILARITY
    is_calibrated_probability: bool = False
    was_cropped: bool = False
    initial_yolo_label: str | None = None
    initial_yolo_confidence: float | None = None

    @property
    def top_candidates(self) -> list[RankedCandidate]:
        """Return ranked top candidates requiring explicit user confirmation."""
        return self.candidates

    def to_dict(self) -> dict[str, Any]:
        """Serialize `FallbackResult` to a JSON-compatible dictionary."""
        return {
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "activated": self.activated,
            "needs_confirmation": self.needs_confirmation,
            "model_source": self.model_source,
            "trigger_reason": (
                self.trigger_reason.value
                if self.trigger_reason is not None and hasattr(self.trigger_reason, "value")
                else self.trigger_reason
            ),
            "confirmation_reasons": [
                r.value if hasattr(r, "value") else str(r)
                for r in self.confirmation_reasons
            ],
            "confirmation_message_vi": self.confirmation_message_vi,
            "score_type": (
                self.score_type.value
                if hasattr(self.score_type, "value")
                else str(self.score_type)
            ),
            "is_calibrated_probability": self.is_calibrated_probability,
            "was_cropped": self.was_cropped,
            "initial_yolo_label": self.initial_yolo_label,
            "initial_yolo_confidence": self.initial_yolo_confidence,
            "candidates": [
                {
                    "ingredient_id": str(c.ingredient_id),
                    "name_vi": c.name_vi,
                    "slug": c.slug,
                    "similarity": c.similarity,
                    "model_source": c.model_source,
                    "needs_confirmation": c.needs_confirmation,
                    "score_type": (
                        c.score_type.value
                        if hasattr(c.score_type, "value")
                        else str(c.score_type)
                    ),
                    "is_calibrated_probability": c.is_calibrated_probability,
                }
                for c in self.candidates
            ],
        }


@dataclass(frozen=True, slots=True)
class ProviderAssessment:
    """Raw closed-set candidate scores and OOD/non-food flags from a provider."""

    scores_by_id: Mapping[UUID, float]
    model_source: str
    score_type: ScoreMetricType = ScoreMetricType.COSINE_SIMILARITY
    is_non_food: bool = False
    is_out_of_distribution: bool = False


@dataclass(frozen=True, slots=True)
class FallbackConfig:
    """Runtime configuration injected or resolved from environment/settings."""

    review_threshold: float | None = None
    min_similarity: float | None = None
    top_k: int | None = None
    ambiguity_margin: float | None = None
    ood_min_margin: float | None = None
    crop_padding_ratio: float = 0.0
    strict_bbox: bool = False


@runtime_checkable
class MultimodalEmbeddingProvider(Protocol):
    """Independent embedding interface for CLIP-like dual-encoder models."""

    @property
    def model_source(self) -> str: ...

    def encode_image(self, rgb_image: np.ndarray) -> np.ndarray: ...

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray | Sequence[np.ndarray]: ...


@runtime_checkable
class FallbackProvider(Protocol):
    """Provider-agnostic interface for CLIP embedding or VLM candidate assessment."""

    @property
    def model_source(self) -> str: ...

    def assess_candidates(
        self,
        rgb_image: np.ndarray,
        candidates: Sequence[KBCandidateIngredient],
    ) -> ProviderAssessment: ...


def _coerce_uuid(value: Any) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value.strip())
        except ValueError:
            return None
    return None
