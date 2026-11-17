"""Core PersonalizationEngine class and unified functional entrypoint."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID
import numpy as np
from .cold_start import (
    _coerce_schema_feature_vector,
    _verify_state_ownership,
    blend_cold_start_score,
    compute_cold_start_lambda,
)
from .config import PersonalizationConfig, _ensure_uuid
from .constants import ColdStartSource, UnauthorizedPersonalizationError
from .engine_controls import (
    _PersonalizationControlsMixin,
    _content_or_neutral_prob,
)
from .engine_ranking import _PersonalizationRankingMixin
from .engine_updater import _PersonalizationUpdateMixin
from .features import RecipeFeatureVector
from .logistic_sgd import predict_preference_prob
from .models import (
    PersonalizationFeedback,
    PersonalizationResult,
    UserModelState,
)
from .repositories import (
    InMemoryPersonalizationRepository,
    UserPersonalizationRepository,
)

# THUẬT TOÁN: Điều phối Cá nhân hóa Cô lập theo Người dùng & Tích hợp Xếp hạng Hậu lọc
# - Luồng xử lý:
#   1. Dự đoán (`predict`): Kiểm tra quyền sở hữu `user_id` và phiên bản schema. Nếu người
#      dùng tắt cá nhân hóa hoặc đang ở trạng thái cold-start, ưu tiên mô hình chung đã
#      kiểm định (`global_model_validated`) hoặc quy đổi từ điểm nội dung `S_base / 100`.
#   2. Cập nhật (`update_from_feedback`): Kiểm tra chủ sở hữu, chống ghi đè bản ghi cũ theo
#      `updated_at` (`ADR-012`), chỉ cập nhật SGD khi nhãn tường minh hợp lệ, lưu qua
#      `UserPersonalizationRepository` được inject.
#   3. Xếp hạng hậu lọc cứng (`rank_post_hard_filter` cho Terminal 14): Chặn tuyệt đối mọi
#      ứng viên `BLOCKED` hoặc chưa `published`, tính `S_final`, bảo toàn thứ tự ưu tiên
#      nhóm `READY` trước `UNKNOWN`/`MISSING_CONFIRMED`.
# - Bảo mật dữ liệu cá nhân: Không ghi `user_id`, `theta_user`, `note` hay dữ liệu nhạy cảm ra log.
# ==============================================================================
class PersonalizationEngine(
    _PersonalizationUpdateMixin,
    _PersonalizationControlsMixin,
    _PersonalizationRankingMixin,
):
    """Stateful-via-repository Logistic Regression personalization service (Component 08)."""

    def __init__(
        self,
        repository: UserPersonalizationRepository,
        config: PersonalizationConfig | None = None,
    ) -> None:
        if not isinstance(repository, UserPersonalizationRepository):
            raise TypeError(
                "repository must implement UserPersonalizationRepository protocol"
            )
        self._repository = repository
        self._config = config or PersonalizationConfig.from_settings()

    @property
    def config(self) -> PersonalizationConfig:
        return self._config

    def predict(
        self,
        authenticated_user_id: UUID | None,
        recipe_feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
        *,
        user_model_state: UserModelState | None = None,
        content_score_base: float | None = None,
    ) -> PersonalizationResult:
        """Predict `personalization_probability` with cold-start and opt-out safeguards."""
        vec = _coerce_schema_feature_vector(
            recipe_feature_vector, config=self._config
        )

        state: UserModelState | None = None
        if authenticated_user_id is None:
            if user_model_state is not None:
                raise UnauthorizedPersonalizationError(
                    "Cannot attach a user model state to an unauthenticated Guest request"
                )
        else:
            uid = _ensure_uuid(
                authenticated_user_id, field_name="authenticated_user_id"
            )
            state = (
                user_model_state
                if user_model_state is not None
                else self._repository.get_user_model_state(uid)
            )
            if state is not None:
                _verify_state_ownership(state, uid, self._config)

        if not self._config.enabled_by_default or (
            state is not None and not state.personalization_enabled
        ):
            fallback_prob = _content_or_neutral_prob(content_score_base)
            return PersonalizationResult(
                personalization_probability=fallback_prob,
                model_state_update=None,
                model_version=self._config.model_version,
                schema_version=self._config.feature_schema_version,
                is_cold_start=True,
                cold_start_source="disabled_fallback",
                effective_lambda=0.0,
                blended_score=round(float(content_score_base), 2)
                if content_score_base is not None
                else None,
            )

        if state is not None and state.theta_user is not None and state.feedback_count > 0:
            prob = round(
                predict_preference_prob(state.theta_user, vec, config=self._config), 6
            )
            eff_lam = compute_cold_start_lambda(
                state.feedback_count, config=self._config
            )
            is_cold = eff_lam == 0.0
            blended = (
                blend_cold_start_score(
                    content_score_base,
                    prob,
                    lambda_override=eff_lam,
                    config=self._config,
                )
                if content_score_base is not None
                else None
            )
            return PersonalizationResult(
                personalization_probability=prob,
                model_state_update=None,
                model_version=state.model_version or self._config.model_version,
                schema_version=self._config.feature_schema_version,
                is_cold_start=is_cold,
                cold_start_source="user_model",
                effective_lambda=eff_lam,
                blended_score=blended,
            )

        if (
            self._config.global_model_validated
            and self._config.validated_global_weights is not None
        ):
            prior_prob = round(
                predict_preference_prob(
                    self._config.validated_global_weights, vec, config=self._config
                ),
                6,
            )
            source: ColdStartSource = "validated_global_model"
        elif content_score_base is not None:
            prior_prob = _content_or_neutral_prob(content_score_base)
            source = "content_score"
        else:
            prior_prob = 0.5
            source = "neutral_prior"

        return PersonalizationResult(
            personalization_probability=prior_prob,
            model_state_update=None,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
            is_cold_start=True,
            cold_start_source=source,
            effective_lambda=0.0,
            blended_score=round(float(content_score_base), 2)
            if content_score_base is not None
            else None,
        )


# ==============================================================================
# THUẬT TOÁN: Điểm vào Hàm Thuần nhất Đánh giá & Cập nhật Cá nhân hóa
# - Tự động phân nhánh giữa suy luận không biến đổi trạng thái (`feedback=None`)
#   và cập nhật trực tuyến SGD (`feedback` tường minh hợp lệ, cấm phiên Guest).
# ==============================================================================
def evaluate_personalization(
    authenticated_user_id: UUID | None,
    recipe_feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
    user_model_state: UserModelState | None = None,
    feedback: PersonalizationFeedback | None = None,
    *,
    content_score_base: float | None = None,
    repository: UserPersonalizationRepository | None = None,
    config: PersonalizationConfig | None = None,
) -> PersonalizationResult:
    """Unified functional entrypoint mapping `(user_id, feature_vector, state, feedback)` to `PersonalizationResult`."""
    repo = repository or InMemoryPersonalizationRepository()
    engine = PersonalizationEngine(repository=repo, config=config)
    if feedback is None:
        return engine.predict(
            authenticated_user_id,
            recipe_feature_vector,
            user_model_state=user_model_state,
            content_score_base=content_score_base,
        )

    if authenticated_user_id is None:
        raise UnauthorizedPersonalizationError(
            "Guest session cannot update personalization model state"
        )
    return engine.update_from_feedback(
        authenticated_user_id,
        recipe_feature_vector,
        feedback,
        user_model_state=user_model_state,
        content_score_base=content_score_base,
    )
