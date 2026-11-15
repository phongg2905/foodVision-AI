"""RBAC user controls mixin (reset profile & enable/disable personalization)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from .cold_start import _verify_state_ownership
from .config import PersonalizationConfig, _ensure_uuid
from .constants import UnauthorizedPersonalizationError
from .models import ModelStateUpdate, UserModelState
from .repositories import UserPersonalizationRepository

def _content_or_neutral_prob(content_score_base: float | None) -> float:
    if content_score_base is None:
        return 0.5
    return round(max(0.0, min(1.0, float(content_score_base) / 100.0)), 6)


# ==============================================================================
# THUẬT TOÁN: Kiểm tra Phân quyền Sở hữu Dữ liệu Cá nhân hóa (RBAC Ownership Gate)
# - Chỉ chủ tài khoản (`actor_user_id == target_user_id`) hoặc quản trị viên đã xác minh
#   tại máy chủ (`actor_is_admin = True`) mới được phép đặt lại hoặc vô hiệu hóa hồ sơ.
# ==============================================================================
def _authorize_user_control(
    actor_user_id: UUID,
    *,
    target_user_id: UUID | None,
    actor_is_admin: bool,
) -> UUID:
    actor_uid = _ensure_uuid(actor_user_id, field_name="actor_user_id")
    resolved_target = (
        _ensure_uuid(target_user_id, field_name="target_user_id")
        if target_user_id is not None
        else actor_uid
    )
    if actor_uid != resolved_target and not actor_is_admin:
        raise UnauthorizedPersonalizationError(
            "Forbidden: user cannot reset or disable another user's personalization profile"
        )
    return resolved_target


class _PersonalizationControlsMixin:
    """Mixin implementing RBAC-protected reset and opt-in/opt-out user controls."""

    _repository: UserPersonalizationRepository
    _config: PersonalizationConfig

    def reset_user_personalization(
        self,
        actor_user_id: UUID,
        *,
        target_user_id: UUID | None = None,
        actor_is_admin: bool = False,
    ) -> ModelStateUpdate:
        """Reset `theta_user` and `feedback_count` enforcing strict user ownership."""
        target_uid = _authorize_user_control(
            actor_user_id,
            target_user_id=target_user_id,
            actor_is_admin=actor_is_admin,
        )
        prev = self._repository.get_user_model_state(target_uid)
        prev_count = prev.feedback_count if prev is not None else 0
        reset_state = self._repository.reset_user_model_state(
            target_uid, disable_personalization=False
        )
        _verify_state_ownership(reset_state, target_uid, self._config)
        return ModelStateUpdate(
            applied=True,
            action="reset",
            reason="user_requested_reset",
            previous_feedback_count=prev_count,
            new_feedback_count=0,
            resolved_label=None,
            new_state=reset_state,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
        )

    def set_personalization_enabled(
        self,
        actor_user_id: UUID,
        *,
        enabled: bool,
        clear_weights_on_disable: bool = True,
        target_user_id: UUID | None = None,
        actor_is_admin: bool = False,
    ) -> ModelStateUpdate:
        """Enable or disable personalization for the authorized user (wiping weights by default on opt-out)."""
        target_uid = _authorize_user_control(
            actor_user_id,
            target_user_id=target_user_id,
            actor_is_admin=actor_is_admin,
        )
        prev = self._repository.get_user_model_state(target_uid)
        prev_count = prev.feedback_count if prev is not None else 0

        if not enabled and clear_weights_on_disable:
            saved = self._repository.reset_user_model_state(
                target_uid, disable_personalization=True
            )
        else:
            next_state = UserModelState(
                user_id=target_uid,
                theta_user=prev.theta_user if prev is not None else None,
                feedback_count=prev_count,
                model_version=prev.model_version
                if prev is not None
                else self._config.model_version,
                schema_version=prev.schema_version
                if prev is not None
                else self._config.feature_schema_version,
                personalization_enabled=bool(enabled),
                recipe_feedback_timestamps=dict(prev.recipe_feedback_timestamps)
                if prev is not None
                else {},
                updated_at=datetime.now(timezone.utc),
            )
            saved = self._repository.save_user_model_state(next_state)

        _verify_state_ownership(saved, target_uid, self._config)
        return ModelStateUpdate(
            applied=True,
            action="enabled" if enabled else "disabled",
            reason="user_enabled_personalization"
            if enabled
            else "user_disabled_personalization",
            previous_feedback_count=prev_count,
            new_feedback_count=saved.feedback_count,
            resolved_label=None,
            new_state=saved,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
        )
