"""Personalization Diagnostics & Feedback Endpoints (`TP 08` — Card #23, `ADR-012`, `DEF-08`).

Provides authenticated Swagger-testable endpoints wired directly to `PersonalizationEngine`
without colliding with TV2 Card #24 (`/api/v1/feedback`):
- `POST /api/v1/personalization/feedback`: Submit explicit 1..5 rating or favorite signal
  with optional `updated_at` timestamp to exercise online SGD & `ADR-012` stale rejection.
- `GET /api/v1/personalization/state`: Inspect current `feedback_count`, `effective_lambda`,
  `is_cold_start`, 18-dim named weights `theta_user`, and `recipe_feedback_timestamps`.
- `DELETE /api/v1/personalization/state`: Reset the authenticated user's LR profile.
- `POST /api/v1/personalization/demo-seed`: Seed opposite User A (likes stir-fry) vs
  User B (likes boil/soup) interaction histories for live `DEF-08` verification on
  `POST /api/v1/recommendations`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import Field

from app.core.auth import get_required_user_id
from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError
from app.intelligence.personalization import (
    FEATURE_NAMES_V1,
    PersonalizationFeedback,
    RecipeFeatureInput,
    compute_cold_start_lambda,
    extract_recipe_feature_vector,
)
from app.schemas.common import StrictSchema

router = APIRouter(prefix="/personalization", tags=["Personalization"])

DEMO_USER_A_UUID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
DEMO_USER_B_UUID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


class PersonalizationFeedbackRequest(StrictSchema):
    """Explicit user feedback payload for online LR SGD update & ADR-012 verification."""

    recipe_id: UUID
    signal_type: str = Field(default="explicit_rating", min_length=1, max_length=40)
    rating: int | None = Field(default=None, ge=1, le=5)
    updated_at: datetime | None = Field(default=None)
    cuisine_code: str = Field(default="VN", min_length=2, max_length=4)
    cooking_method: str | None = Field(default=None, max_length=40)
    total_minutes: int = Field(default=15, ge=1, le=600)


def _parse_user_uuid(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        raise AppError(
            status_code=400,
            code="INVALID_USER_ID",
            message="Bearer user_id phải là UUID hợp lệ (ví dụ: Bearer user:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa).",
            details={"user_id": user_id},
        ) from exc


# THUẬT TOÁN: Cập nhật Trực tuyến Trọng số Hồi quy Logistic (`TP 08`) và Kiểm định `ADR-012`
# - Trích xuất vector 18 chiều từ công thức trong kho (`repo.get_recipe_by_id`) hoặc thuộc tính truyền vào.
# - Gọi `PersonalizationEngine.update_from_feedback` để lọc tín hiệu nhiễu (rating=3/click),
#   khử trùng bản ghi cũ hơn theo `updated_at` (`ADR-012`) và cập nhật SGD có chính quy hóa L2.
@router.post("/feedback")
def record_personalization_feedback(
    payload: PersonalizationFeedbackRequest,
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> dict[str, Any]:
    """Record explicit 1..5 rating or favorite signal into the authenticated user's LR model."""
    uid = _parse_user_uuid(user_id)
    engine = getattr(repo, "personalization_engine", None)
    if engine is None:
        raise AppError(
            status_code=503,
            code="PERSONALIZATION_UNAVAILABLE",
            message="PersonalizationEngine chưa sẵn sàng trên repository hiện tại.",
            details={},
        )

    recipe = repo.get_published_recipe_by_id(str(payload.recipe_id))
    if recipe is not None:
        req_count = sum(1 for ri in recipe.ingredients if ri.is_required)
        feat_input = RecipeFeatureInput(
            cuisine_code=recipe.cuisine_code,
            cooking_method=recipe.cooking_method,
            total_minutes=recipe.total_minutes,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
            required_ingredient_count=max(1, req_count),
            equipment_count=len(recipe.required_equipment),
            step_count=max(1, len(recipe.steps)),
        )
    else:
        feat_input = RecipeFeatureInput(
            cuisine_code=payload.cuisine_code,
            cooking_method=payload.cooking_method,
            total_minutes=payload.total_minutes,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
        )

    feat_vec = extract_recipe_feature_vector(feat_input, config=engine.config)
    fb = PersonalizationFeedback(
        user_id=uid,
        recipe_id=payload.recipe_id,
        signal_type=payload.signal_type,  # type: ignore[arg-type]
        rating=payload.rating,
        updated_at=payload.updated_at or datetime.now(timezone.utc),
    )
    res = engine.update_from_feedback(uid, feat_vec, fb)
    upd = res.model_state_update
    return {
        "user_id": str(uid),
        "recipe_id": str(payload.recipe_id),
        "applied": bool(upd.applied) if upd else False,
        "action": upd.action if upd else "skipped",
        "reason": upd.reason if upd else "unknown",
        "resolved_label": upd.resolved_label if upd else None,
        "previous_feedback_count": upd.previous_feedback_count if upd else 0,
        "new_feedback_count": upd.new_feedback_count if upd else 0,
        "effective_lambda": res.effective_lambda,
        "is_cold_start": res.is_cold_start,
        "personalization_probability": res.personalization_probability,
        "model_version": res.model_version,
    }


@router.get("/state")
def get_personalization_state(
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> dict[str, Any]:
    """Return the authenticated user's current LR weights, feedback count N_u, and lambda_pers."""
    uid = _parse_user_uuid(user_id)
    engine = getattr(repo, "personalization_engine", None)
    if engine is None:
        return {"user_id": str(uid), "feedback_count": 0, "effective_lambda": 0.0, "is_cold_start": True}

    state = engine._repository.get_user_model_state(uid)
    if state is None:
        return {
            "user_id": str(uid),
            "feedback_count": 0,
            "effective_lambda": 0.0,
            "is_cold_start": True,
            "personalization_enabled": True,
            "min_feedback_for_blend": engine.config.min_feedback_for_blend,
            "full_maturity_feedback": engine.config.full_maturity_feedback,
            "theta_by_feature": {},
            "recipe_feedback_timestamps": {},
        }

    eff_lam = compute_cold_start_lambda(state.feedback_count, config=engine.config)
    theta_map = (
        {
            name: round(float(val), 6)
            for name, val in zip(FEATURE_NAMES_V1, state.theta_user, strict=True)
        }
        if state.theta_user is not None
        else {}
    )
    return {
        "user_id": str(uid),
        "feedback_count": state.feedback_count,
        "effective_lambda": eff_lam,
        "is_cold_start": eff_lam == 0.0,
        "personalization_enabled": state.personalization_enabled,
        "min_feedback_for_blend": engine.config.min_feedback_for_blend,
        "full_maturity_feedback": engine.config.full_maturity_feedback,
        "theta_by_feature": theta_map,
        "recipe_feedback_timestamps": dict(state.recipe_feedback_timestamps),
    }


@router.delete("/state")
def reset_personalization_state(
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> dict[str, Any]:
    """Reset the authenticated user's LR weights and feedback history (`TP 08` RBAC control)."""
    uid = _parse_user_uuid(user_id)
    engine = getattr(repo, "personalization_engine", None)
    if engine is None:
        return {"user_id": str(uid), "reset": False}
    upd = engine.reset_user_personalization(uid)
    return {
        "user_id": str(uid),
        "reset": upd.applied,
        "previous_feedback_count": upd.previous_feedback_count,
        "new_feedback_count": upd.new_feedback_count,
    }


# THUẬT TOÁN: Khởi tạo Kịch bản Đối chứng `DEF-08` (User A thích món Xào vs User B thích món Canh/Luộc)
# - Huấn luyện 2 hồ sơ cô lập trên 20 tương tác (10 món 5 sao + 10 món 1 sao) để vượt ngưỡng cold-start.
# - Kiểm chứng luôn ca khử trùng `ADR-012` bằng cách phát lại một đánh giá 1 sao có `updated_at` cũ hơn.
@router.post("/demo-seed")
def seed_def08_demo_users(
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> dict[str, Any]:
    """Seed two opposite demo profiles (User A: likes stir_fry; User B: likes boil) for `DEF-08` Swagger testing."""
    engine = getattr(repo, "personalization_engine", None)
    if engine is None:
        raise AppError(
            status_code=503,
            code="PERSONALIZATION_UNAVAILABLE",
            message="PersonalizationEngine chưa sẵn sàng.",
            details={},
        )

    engine.reset_user_personalization(DEMO_USER_A_UUID)
    engine.reset_user_personalization(DEMO_USER_B_UUID)

    vec_stir_fry = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="stir_fry",
            total_minutes=15,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
            required_ingredient_count=4,
            step_count=1,
        ),
        config=engine.config,
    )
    vec_boil = extract_recipe_feature_vector(
        RecipeFeatureInput(
            cuisine_code="VN",
            cooking_method="boil",
            total_minutes=15,
            ingredient_coverage=1.0,
            ingredient_required_ratio=1.0,
            ingredient_primary_match=1.0,
            required_ingredient_count=3,
            step_count=1,
        ),
        config=engine.config,
    )

    base_ts = datetime(2026, 11, 19, 8, 0, tzinfo=timezone.utc)
    for idx in range(10):
        r_xao = UUID(f"10000000-0000-4000-8000-{idx:012d}")
        r_boil = UUID(f"20000000-0000-4000-8000-{idx:012d}")
        ts = base_ts + timedelta(minutes=idx + 1)

        # User A: 5-star stir_fry, 1-star boil
        engine.update_from_feedback(
            DEMO_USER_A_UUID,
            vec_stir_fry,
            PersonalizationFeedback(DEMO_USER_A_UUID, r_xao, rating=5, updated_at=ts),
        )
        engine.update_from_feedback(
            DEMO_USER_A_UUID,
            vec_boil,
            PersonalizationFeedback(DEMO_USER_A_UUID, r_boil, rating=1, updated_at=ts),
        )

        # User B: 5-star boil, 1-star stir_fry
        engine.update_from_feedback(
            DEMO_USER_B_UUID,
            vec_boil,
            PersonalizationFeedback(DEMO_USER_B_UUID, r_boil, rating=5, updated_at=ts),
        )
        engine.update_from_feedback(
            DEMO_USER_B_UUID,
            vec_stir_fry,
            PersonalizationFeedback(DEMO_USER_B_UUID, r_xao, rating=1, updated_at=ts),
        )

    # Verify ADR-012 stale timestamp rejection on User A's first stir_fry recipe
    stale_check = engine.update_from_feedback(
        DEMO_USER_A_UUID,
        vec_stir_fry,
        PersonalizationFeedback(
            DEMO_USER_A_UUID,
            UUID("10000000-0000-4000-8000-000000000000"),
            rating=1,
            updated_at=base_ts - timedelta(hours=1),
        ),
    )

    state_a = engine._repository.get_user_model_state(DEMO_USER_A_UUID)
    state_b = engine._repository.get_user_model_state(DEMO_USER_B_UUID)
    return {
        "seeded": True,
        "user_a_likes_stir_fry": {
            "authorization_header": f"Bearer user:{DEMO_USER_A_UUID}",
            "feedback_count": state_a.feedback_count if state_a else 0,
            "effective_lambda": compute_cold_start_lambda(
                state_a.feedback_count if state_a else 0, config=engine.config
            ),
        },
        "user_b_likes_boil_soup": {
            "authorization_header": f"Bearer user:{DEMO_USER_B_UUID}",
            "feedback_count": state_b.feedback_count if state_b else 0,
            "effective_lambda": compute_cold_start_lambda(
                state_b.feedback_count if state_b else 0, config=engine.config
            ),
        },
        "adr012_stale_replay_check": {
            "applied": stale_check.model_state_update.applied if stale_check.model_state_update else False,
            "reason": stale_check.model_state_update.reason if stale_check.model_state_update else None,
        },
        "recommended_test_payload": {
            "ingredient_ids": [
                "11111111-1111-4111-8111-111111111101",
                "11111111-1111-4111-8111-111111111102",
            ]
        },
    }
