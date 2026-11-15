"""Online SGD state updater mixin enforcing ADR-012 timestamp deduplication."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID
import numpy as np
from .cold_start import _coerce_schema_feature_vector, _verify_state_ownership
from .config import PersonalizationConfig, _ensure_uuid
from .features import RecipeFeatureVector
from .logistic_sgd import (
    _normalize_utc,
    resolve_explicit_feedback_label,
    update_lr_weights_sgd,
)
from .models import (
    ModelStateUpdate,
    PersonalizationFeedback,
    PersonalizationResult,
    UserModelState,
)
from .repositories import UserPersonalizationRepository

logger = logging.getLogger(__name__)


class _PersonalizationUpdateMixin:
    """Mixin implementing ADR-012 explicit-feedback online SGD state updates."""

    _repository: UserPersonalizationRepository
    _config: PersonalizationConfig

    def predict(self, *args: Any, **kwargs: Any) -> PersonalizationResult: ...

    def update_from_feedback(
        self,
        authenticated_user_id: UUID,
        recipe_feature_vector: RecipeFeatureVector | Sequence[float] | np.ndarray,
        feedback: PersonalizationFeedback,
        *,
        user_model_state: UserModelState | None = None,
        content_score_base: float | None = None,
    ) -> PersonalizationResult:
        """Validate explicit feedback, update ONLY `authenticated_user_id` state, and persist."""
        uid = _ensure_uuid(authenticated_user_id, field_name="authenticated_user_id")
        vec = _coerce_schema_feature_vector(
            recipe_feature_vector, config=self._config
        )

        current = (
            user_model_state
            if user_model_state is not None
            else self._repository.get_user_model_state(uid)
        )
        if current is not None:
            _verify_state_ownership(current, uid, self._config)
        else:
            current = UserModelState(
                user_id=uid,
                theta_user=None,
                feedback_count=0,
                model_version=self._config.model_version,
                schema_version=self._config.feature_schema_version,
                personalization_enabled=self._config.enabled_by_default,
            )

        resolved_label, reason = resolve_explicit_feedback_label(
            feedback, authenticated_user_id=uid, config=self._config
        )

        if not self._config.enabled_by_default or not current.personalization_enabled:
            pred = self.predict(
                uid,
                vec,
                user_model_state=current,
                content_score_base=content_score_base,
            )
            skipped = ModelStateUpdate(
                applied=False,
                action="skipped",
                reason="personalization_disabled",
                previous_feedback_count=current.feedback_count,
                new_feedback_count=current.feedback_count,
                resolved_label=None,
                new_state=current,
                model_version=self._config.model_version,
                schema_version=self._config.feature_schema_version,
            )
            return PersonalizationResult(
                personalization_probability=pred.personalization_probability,
                model_state_update=skipped,
                model_version=pred.model_version,
                schema_version=pred.schema_version,
                is_cold_start=pred.is_cold_start,
                cold_start_source=pred.cold_start_source,
                effective_lambda=pred.effective_lambda,
                blended_score=pred.blended_score,
            )

        if resolved_label is None:
            pred = self.predict(
                uid,
                vec,
                user_model_state=current,
                content_score_base=content_score_base,
            )
            skipped = ModelStateUpdate(
                applied=False,
                action="skipped",
                reason=reason,
                previous_feedback_count=current.feedback_count,
                new_feedback_count=current.feedback_count,
                resolved_label=None,
                new_state=current,
                model_version=self._config.model_version,
                schema_version=self._config.feature_schema_version,
            )
            logger.debug(
                "Personalization update skipped (reason=%s, model_version=%s)",
                reason,
                self._config.model_version,
            )
            return PersonalizationResult(
                personalization_probability=pred.personalization_probability,
                model_state_update=skipped,
                model_version=pred.model_version,
                schema_version=pred.schema_version,
                is_cold_start=pred.is_cold_start,
                cold_start_source=pred.cold_start_source,
                effective_lambda=pred.effective_lambda,
                blended_score=pred.blended_score,
            )

        recipe_key = str(feedback.recipe_id)
        fb_ts = _normalize_utc(feedback.updated_at)
        prev_iso = current.recipe_feedback_timestamps.get(recipe_key)
        if fb_ts is not None and prev_iso is not None:
            prev_ts = _normalize_utc(datetime.fromisoformat(prev_iso))
            if prev_ts is not None and fb_ts < prev_ts:
                pred = self.predict(
                    uid,
                    vec,
                    user_model_state=current,
                    content_score_base=content_score_base,
                )
                stale = ModelStateUpdate(
                    applied=False,
                    action="skipped",
                    reason="stale_feedback_timestamp_adr012",
                    previous_feedback_count=current.feedback_count,
                    new_feedback_count=current.feedback_count,
                    resolved_label=resolved_label,
                    new_state=current,
                    model_version=self._config.model_version,
                    schema_version=self._config.feature_schema_version,
                )
                return PersonalizationResult(
                    personalization_probability=pred.personalization_probability,
                    model_state_update=stale,
                    model_version=pred.model_version,
                    schema_version=pred.schema_version,
                    is_cold_start=pred.is_cold_start,
                    cold_start_source=pred.cold_start_source,
                    effective_lambda=pred.effective_lambda,
                    blended_score=pred.blended_score,
                )

        if current.theta_user is not None:
            base_theta: Sequence[float] = current.theta_user
        elif (
            self._config.global_model_validated
            and self._config.validated_global_weights is not None
        ):
            base_theta = self._config.validated_global_weights
        else:
            base_theta = [0.0] * self._config.feature_dimension

        new_theta_list = update_lr_weights_sgd(
            base_theta,
            vec,
            resolved_label,
            config=self._config,
        )
        now_utc = fb_ts or datetime.now(timezone.utc)
        next_timestamps = dict(current.recipe_feedback_timestamps)
        is_first_for_recipe = recipe_key not in next_timestamps
        next_timestamps[recipe_key] = now_utc.isoformat()
        next_count = (
            current.feedback_count + 1
            if is_first_for_recipe
            else current.feedback_count
        )
        next_count = max(1, next_count)

        updated_state = UserModelState(
            user_id=uid,
            theta_user=tuple(new_theta_list),
            feedback_count=next_count,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
            personalization_enabled=True,
            recipe_feedback_timestamps=next_timestamps,
            updated_at=now_utc,
        )
        saved_state = self._repository.save_user_model_state(updated_state)
        _verify_state_ownership(saved_state, uid, self._config)

        post_pred = self.predict(
            uid,
            vec,
            user_model_state=saved_state,
            content_score_base=content_score_base,
        )
        state_update = ModelStateUpdate(
            applied=True,
            action="sgd_update",
            reason=reason,
            previous_feedback_count=current.feedback_count,
            new_feedback_count=saved_state.feedback_count,
            resolved_label=resolved_label,
            new_state=saved_state,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
        )
        logger.debug(
            "Personalization SGD update applied (model_version=%s, schema=%s)",
            self._config.model_version,
            self._config.feature_schema_version,
        )
        return PersonalizationResult(
            personalization_probability=post_pred.personalization_probability,
            model_state_update=state_update,
            model_version=self._config.model_version,
            schema_version=self._config.feature_schema_version,
            is_cold_start=post_pred.is_cold_start,
            cold_start_source=post_pred.cold_start_source,
            effective_lambda=post_pred.effective_lambda,
            blended_score=post_pred.blended_score,
        )
