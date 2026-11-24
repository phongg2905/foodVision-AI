"""Aggregated CLIP fallback enums, DTOs, and provider protocols."""

from .dto import (
    FallbackConfig,
    FallbackProvider,
    FallbackResult,
    InitialYOLOPrediction,
    MultimodalEmbeddingProvider,
    ProviderAssessment,
    RankedCandidate,
    _coerce_uuid,
)
from .enums import (
    CandidateEmbedding,
    ConfirmationReason,
    FallbackModelError,
    FallbackStatus,
    FallbackTriggerReason,
    KBCandidateIngredient,
    ScoreMetricType,
)

__all__ = [
    "CandidateEmbedding",
    "ConfirmationReason",
    "FallbackConfig",
    "FallbackModelError",
    "FallbackProvider",
    "FallbackResult",
    "FallbackStatus",
    "FallbackTriggerReason",
    "InitialYOLOPrediction",
    "KBCandidateIngredient",
    "MultimodalEmbeddingProvider",
    "ProviderAssessment",
    "RankedCandidate",
    "ScoreMetricType",
    "_coerce_uuid",
]
