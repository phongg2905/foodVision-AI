"""Logistic Regression Preference Learning Service (`TP 08`, `ADR-012`, `MATH-05`, `DEF-08`).

Supports:
1. Numerically stable sigmoid & SGD update: theta <- theta + lr * ((y - p) * x - l2 * theta).
2. Cold-start safe score blending: S_final = (1 - lambda_pers) * S + 100 * lambda_pers * p_{u,r}.
3. ADR-012 deduplication: keeps only the latest `updated_at` feedback per `(user_id, recipe_id)`.
4. Interpretable recipe feature vector (cuisine one-hot + fast dish + cooking methods + plant/animal protein).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from app.core.database import RecipeRecord

FEATURE_NAMES: tuple[str, ...] = (
    "bias",
    "cuisine_vn",
    "cuisine_eu",
    "cuisine_us",
    "is_quick_15m",
    "method_stir_fry",
    "method_pan_fry",
    "method_boil_or_soup",
    "method_braise",
    "method_bake",
)


@dataclass(frozen=True)
class FeedbackSample:
    user_id: str
    recipe_id: str
    rating: int
    updated_at: datetime


def sigmoid(z: float) -> float:
    """Numerically stable logistic function sigma(z) = 1 / (1 + e^{-z})."""
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def predict_preference_prob(x: Sequence[float], theta: Sequence[float]) -> float:
    """Predict P(y = 1 | x; theta) = sigma(theta^T x) (`MATH-05`)."""
    if len(x) != len(theta):
        raise ValueError(f"Kích thước vector đặc trưng ({len(x)}) khác trọng số ({len(theta)}).")
    dot = sum(float(xi) * float(ti) for xi, ti in zip(x, theta))
    return sigmoid(dot)


def sgd_update_theta(
    x: Sequence[float],
    theta: Sequence[float],
    y: int,
    learning_rate: float = 0.1,
    l2_reg: float = 0.0,
) -> list[float]:
    """Perform one L2-regularized logistic regression SGD step (`MATH-05`)."""
    if y not in (0, 1):
        raise ValueError("Nhãn nhị phân y bắt buộc thuộc {0, 1}.")
    p = predict_preference_prob(x, theta)
    err = float(y) - p
    return [
        float(ti) + learning_rate * (err * float(xi) - l2_reg * float(ti))
        for xi, ti in zip(x, theta)
    ]


def blend_personalized_score(
    base_score: float,
    preference_prob: float,
    lambda_pers: float = 0.0,
) -> float:
    """Cold-start blend: S_final = (1 - lambda_pers)*S + 100*lambda_pers*p (`TP 08`, `MATH-05`)."""
    if not (0.0 <= lambda_pers <= 1.0):
        raise ValueError("lambda_pers bắt buộc nằm trong đoạn [0.0, 1.0].")
    if lambda_pers == 0.0:
        return round(float(base_score), 2)
    raw = (1.0 - lambda_pers) * float(base_score) + 100.0 * lambda_pers * float(preference_prob)
    clamped = max(0.0, min(100.0, raw))
    return round(clamped, 2)


def extract_recipe_feature_vector(recipe: RecipeRecord) -> list[float]:
    """Extract 10-dim interpretable feature vector x_r for `TP 08` & Stage 5 Variant D."""
    method = (recipe.cooking_method or "").lower()
    return [
        1.0,  # bias
        1.0 if recipe.cuisine_code == "VN" else 0.0,
        1.0 if recipe.cuisine_code == "EU" else 0.0,
        1.0 if recipe.cuisine_code == "US" else 0.0,
        1.0 if recipe.total_minutes <= 15 else 0.0,
        1.0 if method == "stir_fry" else 0.0,
        1.0 if method in {"pan_fry", "grill"} else 0.0,
        1.0 if method in {"boil", "soup"} else 0.0,
        1.0 if method == "braise" else 0.0,
        1.0 if method in {"bake", "roast"} else 0.0,
    ]


def deduplicate_latest_feedback(samples: Sequence[FeedbackSample]) -> list[FeedbackSample]:
    """Keep strictly 1 latest `updated_at` record per `(user_id, recipe_id)` (`ADR-012`)."""
    latest: dict[tuple[str, str], FeedbackSample] = {}
    for s in samples:
        key = (s.user_id, s.recipe_id)
        prev = latest.get(key)
        if prev is None or s.updated_at >= prev.updated_at:
            latest[key] = s
    return sorted(latest.values(), key=lambda item: (item.updated_at, item.recipe_id))


def fit_user_lr_weights(
    recipes_by_id: dict[str, RecipeRecord],
    feedback_samples: Sequence[FeedbackSample],
    favorite_recipe_ids: Sequence[str] = (),
    epochs: int = 15,
    learning_rate: float = 0.15,
    l2_reg: float = 0.01,
) -> tuple[list[float], int]:
    """Train user-specific LR weights theta_u from deduplicated feedback + favorites (`DEF-08`).

    - `rating >= 4` -> positive (`y = 1`)
    - `rating <= 2` -> negative (`y = 0`)
    - `rating == 3` -> neutral (ignored for binary classification)
    - `favorite_recipe_ids` -> positive (`y = 1`) if not already rated
    Returns `(theta_u, effective_sample_count)`.
    """
    deduped = deduplicate_latest_feedback(feedback_samples)
    training_pairs: list[tuple[list[float], int]] = []
    seen_recipes: set[str] = set()

    for fb in deduped:
        rec = recipes_by_id.get(fb.recipe_id)
        if rec is None:
            continue
        seen_recipes.add(fb.recipe_id)
        if fb.rating >= 4:
            training_pairs.append((extract_recipe_feature_vector(rec), 1))
        elif fb.rating <= 2:
            training_pairs.append((extract_recipe_feature_vector(rec), 0))

    for fav_rid in favorite_recipe_ids:
        if fav_rid in seen_recipes:
            continue
        rec = recipes_by_id.get(fav_rid)
        if rec is not None:
            seen_recipes.add(fav_rid)
            training_pairs.append((extract_recipe_feature_vector(rec), 1))

    theta = [0.0] * len(FEATURE_NAMES)
    if not training_pairs:
        return theta, 0

    for _ in range(max(1, epochs)):
        for x_vec, y_val in training_pairs:
            theta = sgd_update_theta(
                x=x_vec,
                theta=theta,
                y=y_val,
                learning_rate=learning_rate,
                l2_reg=l2_reg,
            )

    return [round(w, 6) for w in theta], len(training_pairs)


def adaptive_lambda_pers(sample_count: int, max_lambda: float = 0.20, min_samples: int = 3) -> float:
    """Return 0.0 for Guest/cold-start users (< min_samples), ramping smoothly up to `max_lambda`."""
    if sample_count < min_samples:
        return 0.0
    ramp = min(1.0, float(sample_count - min_samples + 1) / 5.0)
    return round(max_lambda * ramp, 4)
