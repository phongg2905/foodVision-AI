"""Logistic Regression probability inference, L2-regularized SGD, and ADR-012 deduplication."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
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
    InvalidFeedbackError,
    UnauthorizedPersonalizationError,
    _SCHEMA_REGISTRY,
    _UNTRUSTED_IMPLICIT_SIGNALS,
    _VALID_SIGNAL_TYPES,
)
from .features import RecipeFeatureVector
from .models import PersonalizationFeedback

# ==============================================================================
# THUẬT TOÁN: Hồi quy Logistic & Cập nhật Gradient Ngẫu nhiên Trực tuyến (Online SGD)
# - Cơ sở toán học:
#     p_{u, r} = σ(θ_u · x_r) = 1 / (1 + exp(-θ_u · x_r)) ∈ (0, 1)
#     θ_u^{new} = θ_u^{old} + η * ((y - p_{u, r}) * x_r - λ_L2 * R(θ_u^{old}))
#   Khi `l2_reg = 0`, công thức suy biến chính xác về:
#     θ_u^{new} = θ_u^{old} + learning_rate * (y - p_{u, r}) * x_r
# - Ổn định số học:
#   * Kẹp tích vô hướng `z = θ_u · x_r` trong `[-max_logit_abs, max_logit_abs]` để chống tràn `exp`.
#   * Chiếu chuẩn L2 của `θ_u^{new}` vào hình cầu bán kính `max_weight_norm` để chống phân kỳ.
# - Độ phức tạp: O(d) thời gian và bộ nhớ với d là số chiều vector đặc trưng cố định.
# ==============================================================================
def predict_preference_prob(
    theta_u: Sequence[float] | np.ndarray,
    feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
    *,
    max_logit_abs: float | None = None,
    config: PersonalizationConfig | None = None,
) -> float:
    """Compute `p_{u,r} = sigmoid(theta_u · x_r)` in `(0.0, 1.0)`."""
    raw_features = (
        feature_vector.values
        if isinstance(feature_vector, RecipeFeatureVector)
        else feature_vector
    )
    w = _validate_1d_numeric_array(theta_u, name="theta_u")
    x = _validate_1d_numeric_array(raw_features, name="feature_vector")
    if w.size != x.size:
        raise FeatureDimensionError(
            f"theta_u dimension ({w.size}) and feature_vector dimension ({x.size}) must match"
        )

    cfg = config or PersonalizationConfig.from_settings()
    logit_cap = (
        float(max_logit_abs) if max_logit_abs is not None else cfg.max_logit_abs
    )
    if logit_cap <= 0.0 or not math.isfinite(logit_cap):
        raise ValueError("max_logit_abs must be a positive finite number")

    z = float(np.clip(np.dot(w, x), -logit_cap, logit_cap))
    return 1.0 / (1.0 + math.exp(-z))


# ==============================================================================
# THUẬT TOÁN: Cập nhật Trọng số Hồi quy Logistic bằng SGD Có Điều chuẩn L2
# - Thực hiện 1 bước cập nhật trực tuyến với nhãn nhị phân tường minh `y ∈ {0, 1}`:
#     error     = y - σ(θ_u · x_r)
#     θ_u^{new} = θ_u + lr * (error * x_r - l2_reg * penalty(θ_u))
#   trong đó thành phần `bias` ở chiều 0 được miễn phạt L2 khi `regularize_bias=False`,
#   và vector sau cập nhật được chiếu vào hình cầu chuẩn L2 bán kính `max_weight_norm`.
# - Độ phức tạp: O(d) với d = 18 chiều đặc trưng cố định.
# ==============================================================================
def update_lr_weights_sgd(
    theta_u: Sequence[float] | np.ndarray,
    feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
    label: int,
    *,
    learning_rate: float | None = None,
    l2_reg: float | None = None,
    regularize_bias: bool | None = None,
    config: PersonalizationConfig | None = None,
) -> list[float]:
    """Perform one validated explicit-feedback SGD step on `theta_u`."""
    if isinstance(label, bool) or not isinstance(label, (int, np.integer)) or int(
        label
    ) not in (0, 1):
        raise InvalidFeedbackError(
            "Explicit feedback label must be a strict binary integer (0 or 1)"
        )

    cfg = config or PersonalizationConfig.from_settings()
    lr = cfg.learning_rate if learning_rate is None else float(learning_rate)
    reg = cfg.l2_reg if l2_reg is None else float(l2_reg)
    reg_bias = cfg.regularize_bias if regularize_bias is None else bool(regularize_bias)

    if not math.isfinite(lr) or lr <= 0.0 or lr > 1.0:
        raise ValueError("learning_rate must be finite and in (0.0, 1.0]")
    if not math.isfinite(reg) or reg < 0.0 or reg > 1.0:
        raise ValueError("l2_reg must be finite and in [0.0, 1.0]")

    raw_features = (
        feature_vector.values
        if isinstance(feature_vector, RecipeFeatureVector)
        else feature_vector
    )
    w = _validate_1d_numeric_array(theta_u, name="theta_u")
    x = _validate_1d_numeric_array(raw_features, name="feature_vector")
    if w.size != x.size:
        raise FeatureDimensionError(
            f"theta_u dimension ({w.size}) and feature_vector dimension ({x.size}) must match"
        )

    prob = predict_preference_prob(w, x, config=cfg)
    error = float(int(label)) - prob

    penalty = w.copy()
    has_leading_bias = (
        isinstance(feature_vector, RecipeFeatureVector)
        and feature_vector.feature_names[0] == "bias"
    ) or (
        not isinstance(feature_vector, RecipeFeatureVector)
        and x.size == cfg.feature_dimension
        and _SCHEMA_REGISTRY[cfg.feature_schema_version][0] == "bias"
    )
    if not reg_bias and has_leading_bias:
        penalty[0] = 0.0

    updated = w + lr * (error * x - reg * penalty)
    norm_val = float(np.linalg.norm(updated))
    if norm_val > cfg.max_weight_norm:
        updated = updated * (cfg.max_weight_norm / norm_val)

    return [round(float(val), 6) for val in updated.tolist()]


# ==============================================================================
# THUẬT TOÁN: Kiểm định Nhãn Phản hồi Tường minh & Khử trùng lặp Ngữ cảnh (ADR-012)
# - Nguyên tắc chống nhiễu & bảo vệ mô hình:
#   1. Xác minh chủ sở hữu nghiêm ngặt: `feedback.user_id == authenticated_user_id`.
#   2. Tuyệt đối KHÔNG học từ tín hiệu ngầm đơn lẻ (`click`, `view`, `scroll`, `impression`)
#      hoặc dữ liệu thiếu nhãn (`unlabeled`), độ tin cậy thấp (`< min_signal_confidence`).
#   3. Với `explicit_rating`: chỉ gán `y = 1` khi `rating >= positive_min_rating` và `y = 0`
#      khi `rating <= negative_max_rating`; mức trung tính ở giữa bị bỏ qua an toàn.
#   4. Với `ADR-012`: trên tập phản hồi của một người dùng, chỉ giữ duy nhất 1 bản ghi có
#      `updated_at` mới nhất cho mỗi cặp `(user_id, recipe_id)` để tránh lệch trọng số.
# - Độ phức tạp: O(1) cho kiểm định đơn lẻ; O(M) cho khử trùng lặp M bản ghi phản hồi.
# ==============================================================================
def resolve_explicit_feedback_label(
    feedback: PersonalizationFeedback,
    *,
    authenticated_user_id: UUID,
    config: PersonalizationConfig | None = None,
) -> tuple[int | None, str]:
    """Validate `PersonalizationFeedback` and return `(binary_label_or_None, reason)`."""
    auth_uid = _ensure_uuid(authenticated_user_id, field_name="authenticated_user_id")
    fb_uid = _ensure_uuid(feedback.user_id, field_name="feedback.user_id")
    if fb_uid != auth_uid:
        raise UnauthorizedPersonalizationError(
            "Cross-user feedback contamination blocked: feedback.user_id != authenticated_user_id"
        )

    if feedback.signal_type not in _VALID_SIGNAL_TYPES:
        raise InvalidFeedbackError(
            f"Unsupported feedback signal_type: {feedback.signal_type!r}"
        )

    cfg = config or PersonalizationConfig.from_settings()

    if feedback.signal_type in _UNTRUSTED_IMPLICIT_SIGNALS:
        return None, f"implicit_or_unlabeled_signal_ignored:{feedback.signal_type}"

    if not feedback.is_trusted:
        return None, "untrusted_feedback_source_ignored"

    if (
        not math.isfinite(feedback.signal_confidence)
        or feedback.signal_confidence < cfg.min_signal_confidence
    ):
        return None, "below_min_signal_confidence"

    if feedback.signal_type in {"favorite_added", "favorite_add", "cook_completed"}:
        return 1, f"verified_positive_event:{feedback.signal_type}"

    if feedback.signal_type == "recipe_dismissed":
        return 0, "verified_negative_event:recipe_dismissed"

    if feedback.signal_type in {"explicit_rating", "rating"}:
        rating = feedback.rating
        if rating is None:
            raise InvalidFeedbackError(
                "explicit_rating feedback requires an integer rating in 1..5"
            )
        if isinstance(rating, bool) or not isinstance(rating, int) or not (
            1 <= rating <= 5
        ):
            raise InvalidFeedbackError("Feedback rating must be an integer in [1, 5]")
        if rating >= cfg.positive_min_rating:
            return 1, "explicit_positive_rating"
        if rating <= cfg.negative_max_rating:
            return 0, "explicit_negative_rating"
        return None, "neutral_ambiguous_rating_ignored"

    label = feedback.explicit_label
    if label is None:
        raise InvalidFeedbackError(
            "explicit_binary feedback requires explicit_label in {0, 1}"
        )
    if isinstance(label, bool) or not isinstance(label, int) or label not in (0, 1):
        raise InvalidFeedbackError(
            "explicit_binary label must be a strict integer in {0, 1}"
        )
    return label, "verified_explicit_binary"


# ==============================================================================
# THUẬT TOÁN: Khử Trùng lặp Phản hồi Theo Dấu thời gian Mới nhất (`ADR-012`)
# - Duyệt danh sách phản hồi đã xác thực chủ sở hữu `authenticated_user_id`, gom nhóm
#   theo `recipe_id` và chỉ giữ lại duy nhất bản ghi có `updated_at` (chuẩn hóa UTC)
#   lớn nhất nhằm ngăn một món ăn bị cập nhật lặp làm lệch hướng vector `θ_u`.
# - Độ phức tạp: O(M log M) với M là số phản hồi đầu vào (do sắp xếp đầu ra tất định).
# ==============================================================================
def deduplicate_latest_feedback(
    feedbacks: Sequence[PersonalizationFeedback],
    *,
    authenticated_user_id: UUID,
) -> list[PersonalizationFeedback]:
    """Keep only the single latest `updated_at` record per `(user_id, recipe_id)` (`ADR-012`)."""
    auth_uid = _ensure_uuid(authenticated_user_id, field_name="authenticated_user_id")
    latest_by_recipe: dict[UUID, PersonalizationFeedback] = {}
    epoch_min = datetime.min.replace(tzinfo=timezone.utc)

    for fb in feedbacks:
        if _ensure_uuid(fb.user_id, field_name="feedback.user_id") != auth_uid:
            raise UnauthorizedPersonalizationError(
                "Batch contains feedback belonging to another user"
            )
        existing = latest_by_recipe.get(fb.recipe_id)
        if existing is None:
            latest_by_recipe[fb.recipe_id] = fb
            continue
        ts_new = _normalize_utc(fb.updated_at) or epoch_min
        ts_old = _normalize_utc(existing.updated_at) or epoch_min
        if ts_new >= ts_old:
            latest_by_recipe[fb.recipe_id] = fb

    return sorted(
        latest_by_recipe.values(),
        key=lambda item: (
            _normalize_utc(item.updated_at) or epoch_min,
            str(item.recipe_id),
        ),
    )


def _normalize_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
