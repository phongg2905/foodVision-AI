"""Per-user model state, feedback payload, and post-filter ranking DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any
from uuid import UUID
from app.core.database import RecipeRecord
from app.schemas.reasoning import RecipeReasoningStatus as ReasoningState
from .config import _ensure_uuid, _validate_1d_numeric_array
from .constants import (
    ColdStartSource,
    FEATURE_SCHEMA_VERSION,
    FeatureDimensionError,
    FeedbackSignalType,
    SchemaVersionError,
    StateUpdateAction,
    _SCHEMA_REGISTRY,
)

# CONFLICT-RESOLVED: Unify legacy CandidateRecipeContext / RankedCandidateRecord / MMRCandidate DTOs
# with v1.1.0 RecipeRecord (`app.core.database`) and RecipeReasoningStatus (`app.schemas.reasoning`) per ADR-013.
@dataclass(frozen=True, slots=True)
class CandidateRecipeContext:
    """Recipe context for feature extraction and post-hard-filter ranking."""

    recipe_id: UUID
    name_vi: str = ""
    status: str = "published"
    cuisine_code: str = "VN"
    cooking_method: str | None = None
    prep_minutes: int = 5
    cook_minutes: int = 10
    required_main_ids: frozenset[UUID] = field(default_factory=frozenset)
    optional_main_ids: frozenset[UUID] = field(default_factory=frozenset)
    required_pantry_ids: frozenset[UUID] = field(default_factory=frozenset)
    primary_ids: frozenset[UUID] = field(default_factory=frozenset)
    essential_ids: frozenset[UUID] = field(default_factory=frozenset)
    weights: Mapping[UUID, float] = field(default_factory=dict)
    required_equipment: frozenset[str] = field(default_factory=frozenset)
    allergen_ids: frozenset[UUID] = field(default_factory=frozenset)
    quality_score: float = 1.0
    difficulty: str | float | int | None = None

    @property
    def total_minutes(self) -> int:
        return self.prep_minutes + self.cook_minutes

    @property
    def required_all_ids(self) -> frozenset[UUID]:
        return self.required_main_ids | self.required_pantry_ids


@dataclass(frozen=True, slots=True)
class RankedCandidateRecord:
    """Compact ranked candidate tuple for deterministic tie-breaking."""

    recipe_id: UUID
    is_ready: bool
    score: float
    missing_required_count: int
    total_minutes: int


@dataclass(frozen=True, slots=True)
class MMRCandidate:
    """MMR candidate adapter bridging personalized score into TP 09 diversification."""

    recipe_id: UUID
    relevance_score_100: float
    cuisine_code: str
    cooking_method: str | None
    ingredient_ids: frozenset[UUID]
    is_blocked: bool = False


@dataclass(frozen=True, slots=True)
class RankedRecipeCandidate:
    """Component 07 MCDA candidate record enriched with Component 08 personalization."""

    recipe_id: UUID
    reasoning_state: ReasoningState
    is_ready: bool
    total_score: float
    cuisine_code: str = "VN"
    cooking_method: str | None = None
    total_minutes: int = 15
    missing_required_count: int = 0
    ingredient_ids: frozenset[UUID] = field(default_factory=frozenset)
    features: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] | None = None
    feature_vector_lr: tuple[float, ...] | None = None
    preference_prob: float | None = None
    lambda_pers: float = 0.0

    # THUẬT TOÁN: Cập nhật Điểm Cuối S_final và Xác suất Sở thích P(like | u, r) vào Ứng viên
    def with_personalization(
        self,
        final_score: float,
        *,
        preference_prob: float,
        lambda_pers: float,
    ) -> RankedRecipeCandidate:
        return replace(
            self,
            total_score=round(float(final_score), 2),
            preference_prob=round(float(preference_prob), 6),
            lambda_pers=round(float(lambda_pers), 4),
        )

@dataclass(frozen=True, slots=True)
class PersonalizationFeedback:
    """Validated user interaction payload; sensitive fields are redacted from `repr`."""

    user_id: UUID = field(repr=False)
    recipe_id: UUID
    signal_type: FeedbackSignalType = "explicit_rating"
    rating: int | None = None
    explicit_label: int | None = None
    is_trusted: bool = True
    signal_confidence: float = 1.0
    scan_session_id: UUID | None = field(default=None, repr=False)
    updated_at: datetime | None = None
    note: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class UserModelState:
    """Isolated per-user Logistic Regression parameter state (`theta_user`); PII-redacted `repr`."""

    user_id: UUID = field(repr=False)
    theta_user: tuple[float, ...] | None = field(default=None, repr=False)
    feedback_count: int = 0
    model_version: str | None = None
    schema_version: str | None = None
    personalization_enabled: bool = True
    recipe_feedback_timestamps: Mapping[str, str] = field(
        default_factory=dict, repr=False
    )
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        _ensure_uuid(self.user_id, field_name="UserModelState.user_id")
        if isinstance(self.feedback_count, bool) or self.feedback_count < 0:
            raise ValueError("feedback_count must be an integer >= 0")
        if self.theta_user is not None:
            arr = _validate_1d_numeric_array(
                self.theta_user, name="UserModelState.theta_user"
            )
            if self.schema_version is not None:
                if self.schema_version not in _SCHEMA_REGISTRY:
                    raise SchemaVersionError(
                        f"Unsupported state schema_version: {self.schema_version}"
                    )
                expected_dim = len(_SCHEMA_REGISTRY[self.schema_version])
                if arr.size != expected_dim:
                    raise FeatureDimensionError(
                        f"UserModelState.theta_user dimension {arr.size} != "
                        f"expected {expected_dim} for {self.schema_version}"
                    )
            object.__setattr__(
                self, "theta_user", tuple(float(v) for v in arr.tolist())
            )
        copied_ts = dict(self.recipe_feedback_timestamps)
        object.__setattr__(self, "recipe_feedback_timestamps", copied_ts)


@dataclass(frozen=True, slots=True)
class ModelStateUpdate:
    """Audit-safe outcome of a personalization model update, skip, reset, or toggle."""

    applied: bool
    action: StateUpdateAction
    reason: str
    previous_feedback_count: int
    new_feedback_count: int
    resolved_label: int | None
    new_state: UserModelState = field(repr=False)
    model_version: str
    schema_version: str


@dataclass(frozen=True, slots=True)
class PersonalizationResult:
    """Standard Component 08 output contract (`personalization_probability`, `model_state_update`, `model_version`)."""

    personalization_probability: float
    model_state_update: ModelStateUpdate | None
    model_version: str
    schema_version: str = FEATURE_SCHEMA_VERSION
    is_cold_start: bool = True
    cold_start_source: ColdStartSource = "neutral_prior"
    effective_lambda: float = 0.0
    blended_score: float | None = None


@dataclass(frozen=True, slots=True)
class PostFilterCandidateInput:
    """Candidate passed from hard-constraint filtering (`Component 04`) to Terminal 14 ranking."""

    recipe: CandidateRecipeContext | RecipeRecord
    reasoning: Any
    score_base: float
    confirmed_main_ids: set[UUID] | frozenset[UUID]
    all_pantry_ids: set[UUID] | frozenset[UUID] = field(default_factory=frozenset)
    excluded_pantry_ids: set[UUID] | frozenset[UUID] = field(default_factory=frozenset)
    focus_ids: set[UUID] | frozenset[UUID] | None = None
    difficulty: str | float | int | None = None
    step_count: int = 1


@dataclass(frozen=True, slots=True)
class PersonalizedRankedCandidate:
    """Post-hard-filter personalized score container ready for Terminal 14 & MMR."""

    recipe_id: UUID
    reasoning_state: ReasoningState
    is_ready: bool
    score_base: float
    personalization_probability: float
    effective_lambda: float
    score_final: float
    personalization_delta: float
    missing_required_count: int
    total_minutes: int
    model_version: str
    schema_version: str
    is_cold_start: bool
    cold_start_source: ColdStartSource

    def to_ranked_record(self) -> RankedCandidateRecord:
        return RankedCandidateRecord(
            recipe_id=self.recipe_id,
            is_ready=self.is_ready,
            score=self.score_final,
            missing_required_count=self.missing_required_count,
            total_minutes=self.total_minutes,
        )

    def to_mmr_candidate(self, recipe: CandidateRecipeContext) -> MMRCandidate:
        return MMRCandidate(
            recipe_id=self.recipe_id,
            relevance_score_100=self.score_final,
            cuisine_code=recipe.cuisine_code,
            cooking_method=recipe.cooking_method,
            ingredient_ids=recipe.required_main_ids | recipe.optional_main_ids,
            is_blocked=False,
        )
