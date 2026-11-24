"""Controlled CLIP/VLM candidate fallback for ambiguous food regions (Component 02)."""

from .candidates import (
    compute_cosine_similarities,
    compute_cosine_similarity,
    filter_kb_candidates,
    should_trigger_fallback,
)
from .embedding_providers import (
    CLIPCosineProvider,
    CallableEmbeddingProvider,
    CallableFallbackProvider,
    OpenCLIPEmbeddingProvider,
)
from .models import (
    CandidateEmbedding,
    ConfirmationReason,
    FallbackConfig,
    FallbackModelError,
    FallbackProvider,
    FallbackResult,
    FallbackStatus,
    FallbackTriggerReason,
    InitialYOLOPrediction,
    KBCandidateIngredient,
    MultimodalEmbeddingProvider,
    ProviderAssessment,
    RankedCandidate,
    ScoreMetricType,
)
from .ranker import (
    CLIPFallbackRanker,
    MultimodalFallbackProtocol,
    get_clip_fallback_service,
)
from .service import CLIPFallbackService
from .vlm_provider import OpenAICompatibleVLMProvider

__all__ = [
    "CLIPCosineProvider",
    "CLIPFallbackRanker",
    "CLIPFallbackService",
    "CallableEmbeddingProvider",
    "CallableFallbackProvider",
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
    "MultimodalFallbackProtocol",
    "OpenAICompatibleVLMProvider",
    "OpenCLIPEmbeddingProvider",
    "ProviderAssessment",
    "RankedCandidate",
    "ScoreMetricType",
    "compute_cosine_similarities",
    "compute_cosine_similarity",
    "filter_kb_candidates",
    "get_clip_fallback_service",
    "should_trigger_fallback",
]
