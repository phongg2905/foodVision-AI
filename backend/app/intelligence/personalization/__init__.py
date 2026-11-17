"""Per-User Logistic Regression Personalization Engine (Component 08)."""

from __future__ import annotations

from .cold_start import blend_cold_start_score, compute_cold_start_lambda
from .config import PersonalizationConfig
from .constants import (
    ColdStartSource,
    DEFAULT_PERSONALIZATION_MODEL_VERSION,
    FEATURE_DIM_V1,
    FEATURE_NAMES_V1,
    FEATURE_SCHEMA_VERSION,
    FeatureDimensionError,
    FeedbackSignalType,
    InvalidFeedbackError,
    PersonalizationError,
    SchemaVersionError,
    StateUpdateAction,
    UnauthorizedPersonalizationError,
)
from .engine import PersonalizationEngine, evaluate_personalization
from .engine_ranking import sort_ranked_recipe_candidates
from .features import (
    RecipeFeatureInput,
    RecipeFeatureVector,
    extract_context_feature_vector,
    extract_recipe_feature_vector,
)
from .logistic_sgd import (
    deduplicate_latest_feedback,
    predict_preference_prob,
    resolve_explicit_feedback_label,
    update_lr_weights_sgd,
)
from .models import (
    CandidateRecipeContext,
    MMRCandidate,
    ModelStateUpdate,
    PersonalizationFeedback,
    PersonalizedRankedCandidate,
    PostFilterCandidateInput,
    PersonalizationResult,
    RankedCandidateRecord,
    RankedRecipeCandidate,
    UserModelState,
)
from .repositories import (
    InMemoryPersonalizationRepository,
    InteractionRepositoryPersonalizationAdapter,
    UserPersonalizationRepository,
)

__all__ = [
    "CandidateRecipeContext",
    "ColdStartSource",
    "DEFAULT_PERSONALIZATION_MODEL_VERSION",
    "FEATURE_DIM_V1",
    "FEATURE_NAMES_V1",
    "FEATURE_SCHEMA_VERSION",
    "FeatureDimensionError",
    "FeedbackSignalType",
    "InMemoryPersonalizationRepository",
    "InteractionRepositoryPersonalizationAdapter",
    "InvalidFeedbackError",
    "MMRCandidate",
    "ModelStateUpdate",
    "PersonalizationConfig",
    "PersonalizationEngine",
    "PersonalizationError",
    "PersonalizationFeedback",
    "PersonalizationResult",
    "PersonalizedRankedCandidate",
    "PostFilterCandidateInput",
    "RankedCandidateRecord",
    "RankedRecipeCandidate",
    "RecipeFeatureInput",
    "RecipeFeatureVector",
    "SchemaVersionError",
    "StateUpdateAction",
    "UnauthorizedPersonalizationError",
    "UserModelState",
    "UserPersonalizationRepository",
    "blend_cold_start_score",
    "compute_cold_start_lambda",
    "deduplicate_latest_feedback",
    "evaluate_personalization",
    "extract_context_feature_vector",
    "extract_recipe_feature_vector",
    "predict_preference_prob",
    "resolve_explicit_feedback_label",
    "sort_ranked_recipe_candidates",
    "update_lr_weights_sgd",
]
