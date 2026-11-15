"""Post-hard-filter ranking and Component 07 MCDA reranking mixin."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any
from uuid import UUID
# CONFLICT-RESOLVED: Unify legacy app.intelligence.reasoning / app.intelligence.scoring imports
# with .models (ReasoningState, RankedRecipeCandidate) and v1.1.0 RecipeReasoningEvaluation per ADR-013.
from .cold_start import _coerce_schema_feature_vector, _verify_state_ownership
from .config import PersonalizationConfig, _ensure_uuid
from .constants import PersonalizationError
from .features import (
    RecipeFeatureInput,
    extract_context_feature_vector,
    extract_recipe_feature_vector,
)
from .models import (
    PersonalizedRankedCandidate,
    PostFilterCandidateInput,
    RankedRecipeCandidate,
    ReasoningState,
    UserModelState,
)
from .repositories import UserPersonalizationRepository


# THUẬT TOÁN: Giải nén Trạng thái Suy luận 3 Giá trị (`READY` / `UNKNOWN` / `MISSING_CONFIRMED` / `BLOCKED`)
def _unpack_post_filter_reasoning(
    reasoning: Any,
) -> tuple[bool, ReasoningState | None, int]:
    if hasattr(reasoning, "status_v1_1"):
        st_v11 = getattr(reasoning, "status_v1_1")
        if st_v11 == "BLOCKED" or bool(getattr(reasoning, "blocked_reasons", ())):
            return True, None, 0
        miss_req = getattr(reasoning, "missing_required_ingredient_ids", ())
        return False, st_v11, len(miss_req)

    if hasattr(reasoning, "state"):
        st = getattr(reasoning, "state")
        if st == "BLOCKED" or getattr(reasoning, "blocked_reason", None) is not None:
            return True, None, 0
        miss = set(getattr(reasoning, "missing_confirmed_ids", ()))
        unk = set(getattr(reasoning, "unknown_required_ids", ()))
        return False, st, len(miss | unk)

    if hasattr(reasoning, "status"):
        raw_status = str(getattr(reasoning, "status"))
        if raw_status.endswith("REJECTED") or bool(
            getattr(reasoning, "rejected_reasons", ())
        ):
            return True, None, 0
        if raw_status.endswith("READY"):
            mapped: ReasoningState = "READY"
        elif raw_status.endswith("UNKNOWN"):
            mapped = "UNKNOWN"
        else:
            mapped = "MISSING_CONFIRMED"
        miss = set(getattr(reasoning, "missing_ids", ()))
        unk = set(getattr(reasoning, "unknown_ids", ()))
        return False, mapped, len(miss | unk)

    raise PersonalizationError(
        f"Unsupported reasoning object passed to post-filter hook: {type(reasoning).__name__}"
    )


# THUẬT TOÁN: Sắp xếp Tất định Ứng viên MCDA sau Cá nhân hóa (`READY` trước `MISSING`, điểm giảm dần)
def sort_ranked_recipe_candidates(
    candidates: Sequence[RankedRecipeCandidate],
    *,
    ready_first: bool = True,
) -> list[RankedRecipeCandidate]:
    return sorted(
        candidates,
        key=lambda c: (
            (0 if c.is_ready else 1) if ready_first else 0,
            -c.total_score,
            c.missing_required_count,
            c.total_minutes,
            str(c.recipe_id),
        ),
    )


class _PersonalizationRankingMixin:
    """Mixin implementing post-hard-filter scoring and MCDA candidate reranking."""

    _repository: UserPersonalizationRepository
    _config: PersonalizationConfig

    def predict(self, *args: Any, **kwargs: Any) -> Any: ...

    def rank_post_hard_filter(
        self,
        authenticated_user_id: UUID | None,
        candidates: Sequence[PostFilterCandidateInput],
    ) -> list[PersonalizedRankedCandidate]:
        """Terminal 14 integration hook: score & deterministically rank non-BLOCKED candidates."""
        user_state: UserModelState | None = None
        if authenticated_user_id is not None:
            uid = _ensure_uuid(
                authenticated_user_id, field_name="authenticated_user_id"
            )
            user_state = self._repository.get_user_model_state(uid)
            if user_state is not None:
                _verify_state_ownership(user_state, uid, self._config)

        scored: list[PersonalizedRankedCandidate] = []
        for item in candidates:
            is_blocked, r_state, missing_req_count = _unpack_post_filter_reasoning(
                item.reasoning
            )
            has_req_main = (
                bool(getattr(item.recipe, "required_main_ids", None))
                if hasattr(item.recipe, "required_main_ids")
                else any(
                    ri.is_required and ri.category != "pantry"
                    for ri in getattr(item.recipe, "ingredients", ())
                )
            )
            if (
                is_blocked
                or r_state is None
                or item.recipe.status != "published"
                or not has_req_main
            ):
                continue

            vec = extract_context_feature_vector(
                item.recipe,
                confirmed_main_ids=item.confirmed_main_ids,
                all_pantry_ids=item.all_pantry_ids,
                excluded_pantry_ids=item.excluded_pantry_ids,
                focus_ids=item.focus_ids,
                difficulty=item.difficulty,
                step_count=item.step_count,
                config=self._config,
            )
            pred = self.predict(
                authenticated_user_id,
                vec,
                user_model_state=user_state,
                content_score_base=item.score_base,
            )
            final_score = (
                pred.blended_score
                if pred.blended_score is not None
                else round(float(item.score_base), 2)
            )
            raw_id = getattr(item.recipe, "recipe_id", None) or getattr(
                item.recipe, "id", None
            )
            rec_uuid = raw_id if isinstance(raw_id, UUID) else UUID(str(raw_id))
            scored.append(
                PersonalizedRankedCandidate(
                    recipe_id=rec_uuid,
                    reasoning_state=r_state,
                    is_ready=(r_state == "READY"),
                    score_base=round(float(item.score_base), 2),
                    personalization_probability=pred.personalization_probability,
                    effective_lambda=pred.effective_lambda,
                    score_final=final_score,
                    personalization_delta=round(
                        final_score - float(item.score_base), 2
                    ),
                    missing_required_count=missing_req_count,
                    total_minutes=item.recipe.total_minutes,
                    model_version=pred.model_version,
                    schema_version=pred.schema_version,
                    is_cold_start=pred.is_cold_start,
                    cold_start_source=pred.cold_start_source,
                )
            )

        return sorted(
            scored,
            key=lambda c: (
                0 if c.is_ready else 1,
                -c.score_final,
                c.missing_required_count,
                c.total_minutes,
                str(c.recipe_id),
            ),
        )

    def rerank_mcda_candidates(
        self,
        authenticated_user_id: UUID | None,
        candidates: Sequence[RankedRecipeCandidate],
        *,
        ready_first: bool = True,
    ) -> list[RankedRecipeCandidate]:
        """Terminal 14 hook for Component 07 `RankedRecipeCandidate` post-hard-filter list."""
        user_state: UserModelState | None = None
        if authenticated_user_id is not None:
            uid = _ensure_uuid(
                authenticated_user_id, field_name="authenticated_user_id"
            )
            user_state = self._repository.get_user_model_state(uid)
            if user_state is not None:
                _verify_state_ownership(user_state, uid, self._config)

        allowed_states = {"READY", "UNKNOWN", "MISSING_CONFIRMED"}
        personalized: list[RankedRecipeCandidate] = []

        for cand in candidates:
            if cand.reasoning_state not in allowed_states:
                continue

            if cand.feature_vector_lr is not None:
                vec = _coerce_schema_feature_vector(
                    cand.feature_vector_lr, config=self._config
                )
            else:
                feats = cand.features
                c_val = float(feats.get("C", 0.0))
                g_val = float(feats.get("G", 0.0))
                req_ratio = 1.0 if cand.is_ready else c_val
                meta = cand.metadata or {}
                vec = extract_recipe_feature_vector(
                    RecipeFeatureInput(
                        cuisine_code=cand.cuisine_code,
                        cooking_method=cand.cooking_method,
                        total_minutes=(
                            cand.total_minutes
                            if cand.total_minutes is not None
                            else self._config.reference_minutes
                        ),
                        difficulty=meta.get("difficulty"),
                        ingredient_coverage=c_val,
                        ingredient_required_ratio=req_ratio,
                        ingredient_primary_match=g_val,
                        required_ingredient_count=max(1, len(cand.ingredient_ids)),
                        equipment_count=int(meta.get("equipment_count", 0)),
                        step_count=max(1, int(meta.get("step_count", 1))),
                    ),
                    config=self._config,
                )

            pred = self.predict(
                authenticated_user_id,
                vec,
                user_model_state=user_state,
                content_score_base=cand.total_score,
            )
            final_score = (
                pred.blended_score
                if pred.blended_score is not None
                else cand.total_score
            )
            enriched = replace(cand, feature_vector_lr=vec.values).with_personalization(
                final_score,
                preference_prob=pred.personalization_probability,
                lambda_pers=pred.effective_lambda,
            )
            personalized.append(enriched)

        return sort_ranked_recipe_candidates(personalized, ready_first=ready_first)
