"""Enums, data models, and provider protocols for controlled CLIP/VLM fallback."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
import math
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

import numpy as np

from app.ai.image_processor import BBoxInput
from app.core.errors import AppError

class FallbackStatus(StrEnum):
    """Terminal state of a controlled multimodal fallback evaluation."""

    SUGGESTED = "SUGGESTED"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


class FallbackTriggerReason(StrEnum):
    """Explicit condition that caused the fallback gate to open."""

    LOW_DETECTOR_CONFIDENCE = "low_detector_confidence"
    UNRESOLVED_YOLO_LABEL = "unresolved_yolo_label"
    NO_DETECTOR_PREDICTION = "no_detector_prediction"
    BACKEND_REQUESTED = "backend_requested"


class ConfirmationReason(StrEnum):
    """Machine-readable reasons explaining why human confirmation (HITL) is mandatory."""

    UNCALIBRATED_SIMILARITY = "uncalibrated_similarity_requires_hitl"
    LOW_DETECTOR_CONFIDENCE = "low_detector_confidence"
    UNRESOLVED_INITIAL_LABEL = "unresolved_initial_label"
    BACKEND_FORCED_REVIEW = "backend_forced_review"
    DETECTOR_FALLBACK_DISAGREEMENT = "detector_fallback_disagreement"
    CLOSE_CANDIDATE_SCORES = "close_candidate_scores"
    INVALID_BBOX_FULL_IMAGE_USED = "invalid_bbox_full_image_used"
    OUT_OF_DISTRIBUTION = "out_of_distribution"
    NON_FOOD_INPUT = "non_food_input"
    MODEL_ERROR = "model_error"
    NO_TRUSTWORTHY_CANDIDATE = "no_trustworthy_candidate"
    EMPTY_CANDIDATE_CATALOG = "empty_candidate_catalog"


class ScoreMetricType(StrEnum):
    """Explicit score semantics preventing misinterpretation as exact probability."""

    COSINE_SIMILARITY = "cosine_similarity"
    PROVIDER_RELEVANCE = "provider_relevance_score"


class FallbackModelError(RuntimeError):
    """Internal error raised when a multimodal provider is unconfigured or fails."""


@dataclass(frozen=True)
class CandidateEmbedding:
    """Precomputed text embedding g(T_m) for a valid non-pantry KB ingredient."""

    ingredient_id: UUID
    name_vi: str
    embedding: np.ndarray


@dataclass(frozen=True)
class KBCandidateIngredient:
    """Read-only Knowledge Base ingredient candidate (`category != 'pantry'`)."""

    ingredient_id: UUID
    name_vi: str
    slug: str = ""
    name_en: str | None = None
    category: str = "other"
    is_active: bool = True
    aliases: tuple[str, ...] = ()
    prompts: tuple[str, ...] = ()
    embedding: np.ndarray | None = None

    def text_descriptors(self) -> tuple[str, ...]:
        """Build deduplicated text descriptors strictly from KB metadata."""
        raw_items: Sequence[str] = (
            self.prompts
            if self.prompts
            else (
                self.name_vi,
                self.name_en or "",
                self.slug.replace("_", " ").replace("-", " "),
                *self.aliases,
            )
        )
        seen: set[str] = set()
        result: list[str] = []
        for item in raw_items:
            cleaned = item.strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return tuple(result)
