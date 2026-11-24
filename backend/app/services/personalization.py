"""Component 08 Personalization Service connecting Logistic Regression into Component 07 MCDA Scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import math
from typing import Any
from uuid import UUID

from app.core.database import RecipeRecord
from app.intelligence.personalization import (
    PersonalizationConfig,
    PersonalizationEngine,
    PersonalizationFeedback,
    RecipeFeatureInput,
    UserModelState,
    blend_cold_start_score,
    compute_cold_start_lambda,
    extract_recipe_feature_vector,
)
from app.schemas.reasoning import RecipeReasoningEvaluation

logger = logging.getLogger("foodvision.api")


def build_recipe_feature_input(
    recipe: RecipeRecord,
    *,
    c_val: float = 1.0,
    matched_req_ratio: float = 1.0,
    g_val: float = 1.0,
) -> RecipeFeatureInput:
    """Build the canonical 18-dim `RecipeFeatureInput` for a `RecipeRecord` (`TP 08`, `A3`)."""
    req_count = sum(1 for ri in recipe.ingredients if ri.is_required)
    return RecipeFeatureInput(
        cuisine_code=recipe.cuisine_code,
        cooking_method=recipe.cooking_method,
        total_minutes=recipe.total_minutes,
        ingredient_coverage=c_val,
        ingredient_required_ratio=matched_req_ratio,
        ingredient_primary_match=g_val,
        required_ingredient_count=max(1, req_count),
        equipment_count=len(recipe.required_equipment),
        step_count=max(1, len(recipe.steps)),
    )


def record_user_signal_to_personalization_engine(
    repo: Any,
    *,
    user_id: str,
    recipe_id: str,
    signal_type: str,
    rating: int | None = None,
    updated_at: datetime | None = None,
) -> None:
    """Propagate an explicit feedback or favorite signal from `/feedback` or `/favorites` into `PersonalizationEngine` (`A3`)."""
    try:
        engine = getattr(repo, "personalization_engine", None)
        if engine is None:
            return
        uid = _try_parse_uuid(user_id)
        rid = _try_parse_uuid(recipe_id)
        if uid is None or rid is None:
            return
        recipe = repo.get_published_recipe_by_id(str(rid))
        if recipe is None:
            return
        feat_input = build_recipe_feature_input(recipe)
        feat_vec = extract_recipe_feature_vector(feat_input, config=engine.config)
        norm_signal = "favorite_added" if signal_type == "favorite" else signal_type
        fb = PersonalizationFeedback(
            user_id=uid,
            recipe_id=rid,
            signal_type=norm_signal,  # type: ignore[arg-type]
            rating=rating,
            updated_at=updated_at or datetime.now(timezone.utc),
        )
        engine.update_from_feedback(uid, feat_vec, fb)
    except Exception as exc:
        logger.warning(
            "Failed to propagate user personalization signal (%s) for recipe %s: %s",
            signal_type,
            recipe_id,
            exc,
        )


@dataclass(frozen=True, slots=True)
class PreparedPersonalizationContext:
    """Pre-resolved per-request personalization state avoiding repeated DB/repo lookups across 500 recipes."""

    theta_tuple: tuple[float, ...]
    effective_lambda: float
    max_logit_abs: float
    config: PersonalizationConfig


def _try_parse_uuid(raw_user_id: str | UUID | None) -> UUID | None:
    if raw_user_id is None:
        return None
    if isinstance(raw_user_id, UUID):
        return raw_user_id
    try:
        return UUID(str(raw_user_id))
    except (ValueError, TypeError):
        return None


# THUẬT TOÁN: Tiền giải quyết Ngữ cảnh Cá nhân hóa Một lần Trên Mỗi Request (`PERF-02`)
# - Tách thao tác tra cứu `UserModelState` và tính `λ_pers(N_u)` ra khỏi vòng lặp chấm điểm 500 món.
# - Trả về `None` ngay lập tức (0 chi phí tính toán trong vòng lặp) nếu người dùng là Guest,
#   chưa có lịch sử tương tác hoặc đang trong vùng Cold-Start (`λ_pers(N_u) <= 0`).
def prepare_user_personalization_context(
    user_id: str | UUID | None = None,
    *,
    personalization_engine: PersonalizationEngine | None = None,
    user_model_state: UserModelState | None = None,
) -> PreparedPersonalizationContext | None:
    if personalization_engine is None and user_model_state is None:
        return None

    parsed_uid = _try_parse_uuid(user_id)
    if parsed_uid is None and user_model_state is None:
        return None

    cfg = (
        personalization_engine.config
        if personalization_engine is not None
        else PersonalizationConfig.from_settings()
    )
    if not cfg.enabled_by_default:
        return None

    state = user_model_state
    if state is None and personalization_engine is not None and parsed_uid is not None:
        state = personalization_engine._repository.get_user_model_state(parsed_uid)

    if (
        state is None
        or not state.personalization_enabled
        or state.theta_user is None
        or state.feedback_count <= 0
        or state.schema_version != cfg.feature_schema_version
    ):
        return None

    eff_lambda = compute_cold_start_lambda(state.feedback_count, config=cfg)
    if eff_lambda <= 0.0:
        return None

    theta_vals = tuple(float(v) for v in state.theta_user)
    if len(theta_vals) != cfg.feature_dimension or not all(math.isfinite(v) for v in theta_vals):
        return None

    return PreparedPersonalizationContext(
        theta_tuple=theta_vals,
        effective_lambda=eff_lambda,
        max_logit_abs=cfg.max_logit_abs,
        config=cfg,
    )


# CONFLICT-RESOLVED: Connect TP 08 Cold-Start Logistic Regression score blending (`S_final`)
# onto TP 07 Unified 4-Criteria MCDA base score (`S(r)` per ADR-013) without altering linear XAI contributions.
# THUẬT TOÁN: Trộn Điểm Cá nhân hóa Hồi quy Logistic Cold-Start (`TP 08` - `MATH-05` & `DEF-08`)
# - Công thức: S_final(u, r) = (1 - λ_pers(N_u)) * S(r) + 100 * λ_pers(N_u) * P(like | u, r)
# - Khi Guest hoặc người dùng mới (`N_u < N_min` => `λ_pers = 0`), trả về đúng điểm gốc `S(r)`.
def blend_personalized_score(
    base_score: float,
    preference_prob: float | None = None,
    *,
    feedback_count: int = 0,
    lambda_pers: float | None = None,
    config: PersonalizationConfig | None = None,
) -> float:
    """Blend MCDA base score `S(r)` with `100 * P(like | u, r)` using `lambda_pers(N_u)` (`MATH-05`)."""
    return blend_cold_start_score(
        score_base=base_score,
        preference_prob=preference_prob,
        feedback_count=feedback_count,
        lambda_override=lambda_pers,
        config=config,
    )


# THUẬT TOÁN: Suy luận Nhanh Xác suất Yêu thích P(like | u, r) và Trộn Điểm S_final(u, r)
# - Khi có `prepared_context` (đã tiền nạp 1 lần đầu request), thực hiện tích vô hướng 18 chiều
#   trực tiếp bằng math.fsum trong O(d) mà không cấp phát lại mảng NumPy hay truy vấn lại kho lưu trữ.
def resolve_recipe_personalization(
    recipe: RecipeRecord,
    evaluation: RecipeReasoningEvaluation,
    *,
    c_val: float,
    g_val: float,
    base_score: float,
    user_id: str | UUID | None = None,
    personalization_engine: PersonalizationEngine | None = None,
    user_model_state: UserModelState | None = None,
    prepared_context: PreparedPersonalizationContext | None = None,
    preference_prob: float | None = None,
    feedback_count: int = 0,
    lambda_pers: float | None = None,
) -> float:
    """Resolve `P(like | u, r)` and `lambda_pers(N_u)` and return blended `S_final(u, r)`."""
    if (
        preference_prob is None
        and prepared_context is None
        and personalization_engine is None
        and user_model_state is None
    ):
        return base_score

    if prepared_context is not None and preference_prob is None:
        req_count = sum(1 for ri in recipe.ingredients if ri.is_required)
        matched_req_ratio = (
            float(req_count - len(evaluation.missing_required_ingredient_ids))
            / float(req_count)
            if req_count > 0
            else 0.0
        )
        feat_vec = extract_recipe_feature_vector(
            build_recipe_feature_input(
                recipe,
                c_val=c_val,
                matched_req_ratio=matched_req_ratio,
                g_val=g_val,
            ),
            config=prepared_context.config,
        )
        raw_z = math.fsum(
            w * x for w, x in zip(prepared_context.theta_tuple, feat_vec.values, strict=True)
        )
        cap = prepared_context.max_logit_abs
        z = -cap if raw_z < -cap else (cap if raw_z > cap else raw_z)
        prob = 1.0 / (1.0 + math.exp(-z))
        eff_lam = prepared_context.effective_lambda if lambda_pers is None else float(lambda_pers)
        return round((1.0 - eff_lam) * base_score + 100.0 * eff_lam * prob, 2)

    resolved_prob = preference_prob
    resolved_count = feedback_count
    resolved_lambda = lambda_pers
    pers_cfg: PersonalizationConfig | None = None

    if resolved_prob is None and (
        personalization_engine is not None or user_model_state is not None
    ):
        ctx = prepare_user_personalization_context(
            user_id,
            personalization_engine=personalization_engine,
            user_model_state=user_model_state,
        )
        if ctx is None:
            return base_score
        return resolve_recipe_personalization(
            recipe,
            evaluation,
            c_val=c_val,
            g_val=g_val,
            base_score=base_score,
            prepared_context=ctx,
            lambda_pers=lambda_pers,
        )

    return blend_personalized_score(
        base_score=base_score,
        preference_prob=resolved_prob,
        feedback_count=resolved_count,
        lambda_pers=resolved_lambda,
        config=pers_cfg,
    )
