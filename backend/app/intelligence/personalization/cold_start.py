"""Cold-start lambda ramp, score blending, and state/schema ownership guards."""

from __future__ import annotations

from collections.abc import Sequence
import math
from uuid import UUID
import numpy as np
from .config import (
    PersonalizationConfig,
    _ensure_uuid,
    _validate_1d_numeric_array,
)
from .constants import (
    FeatureDimensionError,
    SchemaVersionError,
    UnauthorizedPersonalizationError,
    _SCHEMA_REGISTRY,
)
from .features import RecipeFeatureVector
from .models import UserModelState

# ==============================================================================
# THUẬT TOÁN: Trộn điểm Cá nhân hóa An toàn cho Người dùng mới (Cold-Start Blending)
# - Công thức:
#     S_final(u, r) = (1 - λ_pers) * S_base(r) + 100 * λ_pers * p_{u, r}
# - Quy tắc Cold-Start:
#   * Guest, người dùng tắt cá nhân hóa, hoặc `feedback_count < min_feedback_for_blend`:
#     `λ_pers = 0.0` -> bảo toàn 100% điểm nội dung `S_base(r)` hoặc dùng mô hình chung
#     đã được kiểm định (`global_model_validated = True`) cho xác suất khởi đầu.
#   * Khi đủ lịch sử phản hồi: `λ_pers` tăng tuyến tính tới trần `max_blend_lambda`
#     để phản ánh khẩu vị cá nhân mà không lấn át độ phủ nguyên liệu thực tế trong bếp.
# - Độ phức tạp: O(1).
# ==============================================================================
def compute_cold_start_lambda(
    feedback_count: int,
    *,
    min_feedback: int | None = None,
    full_maturity_feedback: int | None = None,
    max_lambda: float | None = None,
    config: PersonalizationConfig | None = None,
) -> float:
    """Compute safe personalization weight `lambda_pers` in `[0.0, max_lambda]`."""
    cfg = config or PersonalizationConfig.from_settings()
    min_fb = cfg.min_feedback_for_blend if min_feedback is None else int(min_feedback)
    full_fb = (
        cfg.full_maturity_feedback
        if full_maturity_feedback is None
        else int(full_maturity_feedback)
    )
    cap_lam = cfg.max_blend_lambda if max_lambda is None else float(max_lambda)

    if feedback_count < min_fb or cap_lam <= 0.0:
        return 0.0
    span = max(1, full_fb - min_fb)
    progress = min(1.0, (feedback_count - min_fb) / float(span))
    return round(cap_lam * progress, 4)


def blend_cold_start_score(
    score_base: float,
    preference_prob: float | None,
    *,
    feedback_count: int = 0,
    lambda_override: float | None = None,
    config: PersonalizationConfig | None = None,
) -> float:
    """Blend `S_base` and `100 * p_{u,r}` safely under cold-start constraints."""
    if preference_prob is None:
        return round(float(score_base), 2)

    lam = (
        max(0.0, min(1.0, float(lambda_override)))
        if lambda_override is not None
        else compute_cold_start_lambda(feedback_count, config=config)
    )
    blended = (1.0 - lam) * float(score_base) + 100.0 * lam * float(preference_prob)
    return round(blended, 2)


def _coerce_schema_feature_vector(
    feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
    *,
    config: PersonalizationConfig,
) -> RecipeFeatureVector:
    if isinstance(feature_vector, RecipeFeatureVector):
        if feature_vector.schema_version != config.feature_schema_version:
            raise SchemaVersionError(
                f"Feature vector schema {feature_vector.schema_version} != "
                f"configured schema {config.feature_schema_version}"
            )
        return feature_vector

    arr = _validate_1d_numeric_array(feature_vector, name="feature_vector")
    expected_names = _SCHEMA_REGISTRY[config.feature_schema_version]
    if arr.size != len(expected_names):
        raise FeatureDimensionError(
            f"Feature vector dimension {arr.size} does not match schema "
            f"{config.feature_schema_version} ({len(expected_names)})"
        )
    return RecipeFeatureVector(
        values=tuple(float(v) for v in arr.tolist()),
        schema_version=config.feature_schema_version,
        feature_names=expected_names,
    )


def _verify_state_ownership(
    state: UserModelState,
    authenticated_user_id: UUID,
    config: PersonalizationConfig,
) -> None:
    if state.user_id != authenticated_user_id:
        raise UnauthorizedPersonalizationError(
            "UserModelState ownership mismatch: cross-user profile usage is prohibited"
        )
    if state.theta_user is not None:
        if (
            state.schema_version is not None
            and state.schema_version != config.feature_schema_version
        ):
            raise SchemaVersionError(
                f"Stored theta_user schema {state.schema_version} incompatible with "
                f"active schema {config.feature_schema_version}"
            )
        if len(state.theta_user) != config.feature_dimension:
            raise FeatureDimensionError(
                f"Stored theta_user length {len(state.theta_user)} != "
                f"schema dimension {config.feature_dimension}"
            )
