"""Feature schema v1.0 registry, signal taxonomies, and domain exceptions."""

from __future__ import annotations

from typing import Literal

FEATURE_SCHEMA_VERSION = "lr-feature-v1.0"
DEFAULT_PERSONALIZATION_MODEL_VERSION = "fv-lr-pers-v1.0"

FEATURE_NAMES_V1: tuple[str, ...] = (
    "bias",
    "cuisine_vn",
    "cuisine_eu",
    "cuisine_us",
    "method_canh",
    "method_xao",
    "method_kho",
    "method_chien",
    "method_nuong",
    "method_luoc_hap",
    "method_tron_salad",
    "method_other",
    "time_efficiency",
    "time_duration_norm",
    "difficulty_norm",
    "ingredient_coverage",
    "ingredient_required_ratio",
    "ingredient_primary_match",
)
FEATURE_DIM_V1: int = len(FEATURE_NAMES_V1)

_SCHEMA_REGISTRY: dict[str, tuple[str, ...]] = {
    FEATURE_SCHEMA_VERSION: FEATURE_NAMES_V1,
}

_COOKING_METHOD_BUCKETS: dict[str, str] = {
    "canh": "method_canh",
    "sup": "method_canh",
    "soup": "method_canh",
    "ham": "method_canh",
    "lau": "method_canh",
    "xao": "method_xao",
    "ap chao": "method_xao",
    "stir fry": "method_xao",
    "stir-fry": "method_xao",
    "kho": "method_kho",
    "rim": "method_kho",
    "om": "method_kho",
    "braise": "method_kho",
    "stew": "method_kho",
    "chien": "method_chien",
    "ran": "method_chien",
    "fry": "method_chien",
    "deep fry": "method_chien",
    "nuong": "method_nuong",
    "bo lo": "method_nuong",
    "grill": "method_nuong",
    "bake": "method_nuong",
    "roast": "method_nuong",
    "luoc": "method_luoc_hap",
    "hap": "method_luoc_hap",
    "tran": "method_luoc_hap",
    "boil": "method_luoc_hap",
    "steam": "method_luoc_hap",
    "salad": "method_tron_salad",
    "goi": "method_tron_salad",
    "tron": "method_tron_salad",
}

_DIFFICULTY_LEVEL_MAP: dict[str, float] = {
    "easy": 0.20,
    "de": 0.20,
    "low": 0.20,
    "medium": 0.50,
    "trung binh": 0.50,
    "vua": 0.50,
    "moderate": 0.50,
    "hard": 0.85,
    "kho": 0.85,
    "high": 0.85,
}

FeedbackSignalType = Literal[
    "explicit_rating",
    "rating",
    "favorite_added",
    "favorite_add",
    "favorite_remove",
    "cook_completed",
    "recipe_dismissed",
    "hitl_confirmed",
    "explicit_binary",
    "click",
    "view",
    "scroll",
    "impression",
    "unlabeled",
]

ColdStartSource = Literal[
    "user_model",
    "validated_global_model",
    "content_score",
    "neutral_prior",
    "disabled_fallback",
]

StateUpdateAction = Literal["sgd_update", "skipped", "reset", "disabled", "enabled"]

_DISABLED_MODEL_SENTINEL = "disabled"

_VALID_SIGNAL_TYPES: frozenset[str] = frozenset(
    {
        "explicit_rating",
        "rating",
        "favorite_added",
        "favorite_add",
        "favorite_remove",
        "cook_completed",
        "recipe_dismissed",
        "hitl_confirmed",
        "explicit_binary",
        "click",
        "view",
        "scroll",
        "impression",
        "unlabeled",
    }
)
_UNTRUSTED_IMPLICIT_SIGNALS: frozenset[str] = frozenset(
    {
        "click",
        "view",
        "scroll",
        "impression",
        "unlabeled",
        "favorite_remove",
        "hitl_confirmed",
    }
)


class PersonalizationError(Exception):
    """Base error for Component 08 personalization domain failures."""


class FeatureDimensionError(PersonalizationError, ValueError):
    """Raised when feature vectors or weight vectors violate schema dimensions."""


class SchemaVersionError(FeatureDimensionError):
    """Raised when an unsupported or mismatched feature schema version is supplied."""


class InvalidFeedbackError(PersonalizationError, ValueError):
    """Raised when feedback contains invalid labels, out-of-range ratings, or corrupt types."""


class UnauthorizedPersonalizationError(PersonalizationError, PermissionError):
    """Raised on cross-user access attempts or unauthenticated state mutations."""
