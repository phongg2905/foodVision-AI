"""Persistence port, snapshot-isolated in-memory store, and UoW adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from uuid import UUID
from .config import PersonalizationConfig, _ensure_uuid
from .constants import (
    SchemaVersionError,
    UnauthorizedPersonalizationError,
    _DISABLED_MODEL_SENTINEL,
    _SCHEMA_REGISTRY,
)
from .models import UserModelState

@runtime_checkable
class UserPersonalizationRepository(Protocol):
    """Injected persistence port for strict per-user `theta_user` storage (`user_preferences`)."""

    def get_user_model_state(self, user_id: UUID) -> UserModelState | None:
        """Load personalization state owned strictly by `user_id` (`None` if absent)."""

    def save_user_model_state(self, state: UserModelState) -> UserModelState:
        """Persist updated `UserModelState` strictly scoped to `state.user_id`."""

    def reset_user_model_state(
        self,
        user_id: UUID,
        *,
        disable_personalization: bool = False,
    ) -> UserModelState:
        """Clear `theta_user` and `feedback_count` for `user_id` (optionally disabling learning)."""


# ==============================================================================
# THUẬT TOÁN: Lưu trữ Cô lập Trạng thái Mô hình theo Định danh UUID (Snapshot Isolation)
# - Mỗi bản ghi `UserModelState` được khóa chặt theo `UUID` chủ sở hữu và sao chép bất biến
#   (`tuple`, `dict` mới) khi đọc/ghi nhằm triệt tiêu hiện tượng rò rỉ tham chiếu bộ nhớ
#   (aliasing) giữa hai người dùng khác nhau trong cùng tiến trình.
# ==============================================================================
class InMemoryPersonalizationRepository:
    """Isolated per-UUID repository adapter copying immutable `UserModelState` snapshots."""

    def __init__(self) -> None:
        self._store: dict[UUID, UserModelState] = {}

    def get_user_model_state(self, user_id: UUID) -> UserModelState | None:
        uid = _ensure_uuid(user_id, field_name="user_id")
        existing = self._store.get(uid)
        if existing is None:
            return None
        return UserModelState(
            user_id=existing.user_id,
            theta_user=tuple(existing.theta_user)
            if existing.theta_user is not None
            else None,
            feedback_count=existing.feedback_count,
            model_version=existing.model_version,
            schema_version=existing.schema_version,
            personalization_enabled=existing.personalization_enabled,
            recipe_feedback_timestamps=dict(existing.recipe_feedback_timestamps),
            updated_at=existing.updated_at,
        )

    def save_user_model_state(self, state: UserModelState) -> UserModelState:
        uid = _ensure_uuid(state.user_id, field_name="state.user_id")
        snapshot = UserModelState(
            user_id=uid,
            theta_user=tuple(state.theta_user)
            if state.theta_user is not None
            else None,
            feedback_count=state.feedback_count,
            model_version=state.model_version,
            schema_version=state.schema_version,
            personalization_enabled=state.personalization_enabled,
            recipe_feedback_timestamps=dict(state.recipe_feedback_timestamps),
            updated_at=state.updated_at or datetime.now(timezone.utc),
        )
        self._store[uid] = snapshot
        return snapshot

    def reset_user_model_state(
        self,
        user_id: UUID,
        *,
        disable_personalization: bool = False,
    ) -> UserModelState:
        uid = _ensure_uuid(user_id, field_name="user_id")
        cleared = UserModelState(
            user_id=uid,
            theta_user=None,
            feedback_count=0,
            model_version=None,
            schema_version=None,
            personalization_enabled=not disable_personalization,
            recipe_feedback_timestamps={},
            updated_at=datetime.now(timezone.utc),
        )
        self._store[uid] = cleared
        return cleared


class _UserInteractionStorePort(Protocol):
    """Structural port matching `IUserInteractionRepository` (`app/db/interfaces.py`)."""

    def get_or_create_preferences(self, user_id: UUID) -> Any: ...

    def update_lr_model_state(
        self,
        user_id: UUID,
        *,
        lr_weights: list[float],
        feedback_count: int,
        lr_model_version: str,
        lr_feature_names: list[str] | None = None,
    ) -> Any: ...


# ==============================================================================
# THUẬT TOÁN: Bộ Chuyển đổi Giao diện Kho Lưu trữ Tương tác (`user_preferences` Adapter)
# - Cầu nối Dependency Inversion giữa `PersonalizationEngine` (Component 08) và
#   `IUserInteractionRepository` (Component 03 / Terminal 14) mà không phụ thuộc ORM trực tiếp.
# - Kiểm tra tính toàn vẹn của `user_id`, thứ tự `lr_feature_names` và cờ vô hiệu hóa.
# ==============================================================================
class InteractionRepositoryPersonalizationAdapter:
    """Adapts `IUserInteractionRepository` (`uow.interactions`) to `UserPersonalizationRepository`."""

    def __init__(
        self,
        interactions_repo: _UserInteractionStorePort,
        *,
        config: PersonalizationConfig | None = None,
    ) -> None:
        self._interactions = interactions_repo
        self._config = config or PersonalizationConfig.from_settings()

    def get_user_model_state(self, user_id: UUID) -> UserModelState | None:
        uid = _ensure_uuid(user_id, field_name="user_id")
        pref = self._interactions.get_or_create_preferences(uid)
        if getattr(pref, "user_id", None) != uid:
            raise UnauthorizedPersonalizationError(
                "Preferences record user_id mismatch from underlying repository"
            )

        raw_version: str | None = getattr(pref, "lr_model_version", None)
        is_enabled = raw_version != _DISABLED_MODEL_SENTINEL
        raw_weights = getattr(pref, "lr_weights", None)
        stored_names = getattr(pref, "lr_feature_names", None)
        expected_names = _SCHEMA_REGISTRY[self._config.feature_schema_version]

        if stored_names is not None and len(stored_names) > 0:
            if tuple(stored_names) != expected_names:
                raise SchemaVersionError(
                    "Stored lr_feature_names order does not match active feature schema"
                )

        theta_tuple: tuple[float, ...] | None = None
        schema_ver: str | None = None
        if raw_weights is not None and len(raw_weights) > 0:
            theta_tuple = tuple(float(v) for v in raw_weights)
            schema_ver = self._config.feature_schema_version

        return UserModelState(
            user_id=uid,
            theta_user=theta_tuple,
            feedback_count=int(getattr(pref, "feedback_count", 0) or 0),
            model_version=None
            if raw_version == _DISABLED_MODEL_SENTINEL
            else raw_version,
            schema_version=schema_ver,
            personalization_enabled=is_enabled,
            updated_at=getattr(pref, "updated_at", None),
        )

    def save_user_model_state(self, state: UserModelState) -> UserModelState:
        uid = _ensure_uuid(state.user_id, field_name="state.user_id")
        expected_names = list(_SCHEMA_REGISTRY[self._config.feature_schema_version])
        version_tag = (
            _DISABLED_MODEL_SENTINEL
            if not state.personalization_enabled
            else (state.model_version or self._config.model_version)
        )
        weights_payload = (
            list(state.theta_user) if state.theta_user is not None else []
        )
        pref = self._interactions.update_lr_model_state(
            uid,
            lr_weights=weights_payload,
            feedback_count=state.feedback_count,
            lr_model_version=version_tag,
            lr_feature_names=expected_names,
        )
        if getattr(pref, "user_id", None) != uid:
            raise UnauthorizedPersonalizationError(
                "Persisted preferences user_id mismatch"
            )
        return UserModelState(
            user_id=uid,
            theta_user=tuple(weights_payload) if weights_payload else None,
            feedback_count=int(getattr(pref, "feedback_count", state.feedback_count)),
            model_version=None if not state.personalization_enabled else version_tag,
            schema_version=state.schema_version
            if weights_payload
            else None,
            personalization_enabled=state.personalization_enabled,
            recipe_feedback_timestamps=dict(state.recipe_feedback_timestamps),
            updated_at=getattr(pref, "updated_at", state.updated_at),
        )

    def reset_user_model_state(
        self,
        user_id: UUID,
        *,
        disable_personalization: bool = False,
    ) -> UserModelState:
        uid = _ensure_uuid(user_id, field_name="user_id")
        version_tag = (
            _DISABLED_MODEL_SENTINEL
            if disable_personalization
            else self._config.model_version
        )
        pref = self._interactions.update_lr_model_state(
            uid,
            lr_weights=[],
            feedback_count=0,
            lr_model_version=version_tag,
            lr_feature_names=list(
                _SCHEMA_REGISTRY[self._config.feature_schema_version]
            ),
        )
        return UserModelState(
            user_id=uid,
            theta_user=None,
            feedback_count=0,
            model_version=None,
            schema_version=None,
            personalization_enabled=not disable_personalization,
            recipe_feedback_timestamps={},
            updated_at=getattr(pref, "updated_at", datetime.now(timezone.utc)),
        )
