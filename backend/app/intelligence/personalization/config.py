"""Personalization hyperparameters and low-level numeric/UUID validators."""

from __future__ import annotations

from pydantic import Field
from collections.abc import Mapping
from app.schemas.common import StrictSchema
from .constants import UnauthorizedPersonalizationError
from pydantic import model_validator
from collections.abc import Sequence
from dataclasses import dataclass
import json
import math
import os
from typing import Any
from uuid import UUID
import numpy as np
from app.core.config import Settings, get_settings
from .constants import (
    DEFAULT_PERSONALIZATION_MODEL_VERSION,
    FEATURE_SCHEMA_VERSION,
    FeatureDimensionError,
    PersonalizationError,
    SchemaVersionError,
    _SCHEMA_REGISTRY,
)

class PersonalizationConfig(StrictSchema):
    """Runtime-resolved hyperparameters & learning gates (never hardcoded in math core)."""

    enabled_by_default: bool = Field(default=True)
    feature_schema_version: str = Field(default=FEATURE_SCHEMA_VERSION, min_length=1)
    model_version: str = Field(
        default=DEFAULT_PERSONALIZATION_MODEL_VERSION, min_length=1
    )
    learning_rate: float = Field(default=0.05, gt=0.0, le=1.0)
    l2_reg: float = Field(default=1e-4, ge=0.0, le=1.0)
    regularize_bias: bool = Field(default=False)
    max_logit_abs: float = Field(default=35.0, gt=0.0, le=50.0)
    max_weight_norm: float = Field(default=25.0, gt=0.0, le=500.0)
    min_feedback_for_blend: int = Field(default=5, ge=1)
    full_maturity_feedback: int = Field(default=25, ge=1)
    max_blend_lambda: float = Field(default=0.25, ge=0.0, le=1.0)
    positive_min_rating: int = Field(default=4, ge=1, le=5)
    negative_max_rating: int = Field(default=2, ge=1, le=5)
    min_signal_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    reference_minutes: int = Field(default=15, ge=1)
    max_norm_minutes: int = Field(default=120, ge=1)
    validated_global_weights: tuple[float, ...] | None = Field(default=None)
    global_model_validated: bool = Field(default=False)

    @model_validator(mode="after")
    def _validate_invariants(self) -> PersonalizationConfig:
        if self.feature_schema_version not in _SCHEMA_REGISTRY:
            raise SchemaVersionError(
                f"Unsupported feature_schema_version: {self.feature_schema_version}"
            )
        if self.negative_max_rating >= self.positive_min_rating:
            raise ValueError(
                "negative_max_rating must be strictly less than positive_min_rating"
            )
        if self.full_maturity_feedback < self.min_feedback_for_blend:
            raise ValueError(
                "full_maturity_feedback must be >= min_feedback_for_blend"
            )
        if self.validated_global_weights is not None:
            expected_dim = len(_SCHEMA_REGISTRY[self.feature_schema_version])
            if len(self.validated_global_weights) != expected_dim:
                raise FeatureDimensionError(
                    f"validated_global_weights length {len(self.validated_global_weights)} "
                    f"does not match schema dimension {expected_dim}"
                )
            if any(not math.isfinite(float(v)) for v in self.validated_global_weights):
                raise FeatureDimensionError(
                    "validated_global_weights must contain only finite numbers"
                )
        return self

    @property
    def feature_dimension(self) -> int:
        return len(_SCHEMA_REGISTRY[self.feature_schema_version])

    # ==========================================================================
    # THUẬT TOÁN: Hợp nhất Cấu hình Siêu tham số Cá nhân hóa từ Settings & ENV
    # - Đọc tốc độ học SGD, hệ số L2, ngưỡng cold-start và trọng số toàn cục đã
    #   kiểm định (nếu có), sau đó thực thi bất biến `_validate_invariants`.
    # ==========================================================================
    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> PersonalizationConfig:
        """Load hyperparameters from `Settings` attributes and environment variables."""
        runtime_settings = settings or get_settings()
        payload: dict[str, Any] = {
            "reference_minutes": runtime_settings.default_reference_minutes,
        }
        settings_attr_map = {
            "personalization_enabled": "enabled_by_default",
            "personalization_schema_version": "feature_schema_version",
            "personalization_model_version": "model_version",
            "personalization_learning_rate": "learning_rate",
            "personalization_l2_reg": "l2_reg",
            "personalization_regularize_bias": "regularize_bias",
            "personalization_max_logit_abs": "max_logit_abs",
            "personalization_max_weight_norm": "max_weight_norm",
            "personalization_min_feedback": "min_feedback_for_blend",
            "personalization_maturity_feedback": "full_maturity_feedback",
            "personalization_max_lambda": "max_blend_lambda",
            "personalization_positive_min_rating": "positive_min_rating",
            "personalization_negative_max_rating": "negative_max_rating",
            "personalization_min_signal_confidence": "min_signal_confidence",
            "personalization_max_norm_minutes": "max_norm_minutes",
            "personalization_global_model_validated": "global_model_validated",
        }
        for attr_name, field_name in settings_attr_map.items():
            if hasattr(runtime_settings, attr_name):
                val = getattr(runtime_settings, attr_name)
                if val is not None:
                    payload[field_name] = val

        env_map = {
            "PERSONALIZATION_ENABLED": ("enabled_by_default", _parse_env_bool),
            "PERSONALIZATION_SCHEMA_VERSION": ("feature_schema_version", str),
            "PERSONALIZATION_MODEL_VERSION": ("model_version", str),
            "PERSONALIZATION_LEARNING_RATE": ("learning_rate", float),
            "PERSONALIZATION_L2_REG": ("l2_reg", float),
            "PERSONALIZATION_REGULARIZE_BIAS": ("regularize_bias", _parse_env_bool),
            "PERSONALIZATION_MAX_LOGIT_ABS": ("max_logit_abs", float),
            "PERSONALIZATION_MAX_WEIGHT_NORM": ("max_weight_norm", float),
            "PERSONALIZATION_MIN_FEEDBACK": ("min_feedback_for_blend", int),
            "PERSONALIZATION_MATURITY_FEEDBACK": ("full_maturity_feedback", int),
            "PERSONALIZATION_MAX_LAMBDA": ("max_blend_lambda", float),
            "PERSONALIZATION_POSITIVE_MIN_RATING": ("positive_min_rating", int),
            "PERSONALIZATION_NEGATIVE_MAX_RATING": ("negative_max_rating", int),
            "PERSONALIZATION_MIN_SIGNAL_CONFIDENCE": ("min_signal_confidence", float),
            "PERSONALIZATION_REFERENCE_MINUTES": ("reference_minutes", int),
            "PERSONALIZATION_MAX_NORM_MINUTES": ("max_norm_minutes", int),
            "PERSONALIZATION_GLOBAL_MODEL_VALIDATED": (
                "global_model_validated",
                _parse_env_bool,
            ),
        }
        for env_key, (field_name, caster) in env_map.items():
            raw = os.getenv(env_key)
            if raw is not None and raw.strip() != "":
                payload[field_name] = caster(raw.strip())

        raw_global = os.getenv("PERSONALIZATION_GLOBAL_WEIGHTS_JSON")
        if raw_global is not None and raw_global.strip() != "":
            parsed = json.loads(raw_global)
            if not isinstance(parsed, list):
                raise FeatureDimensionError(
                    "PERSONALIZATION_GLOBAL_WEIGHTS_JSON must decode to a JSON list"
                )
            payload["validated_global_weights"] = tuple(float(v) for v in parsed)

        return cls.model_validate(payload)


def _parse_env_bool(raw: str) -> bool:
    norm = raw.strip().lower()
    if norm in {"1", "true", "yes", "on"}:
        return True
    if norm in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean configuration string: {raw!r}")


def _validate_1d_numeric_array(
    values: Sequence[float] | np.ndarray,
    *,
    name: str,
) -> np.ndarray:
    if isinstance(values, (str, bytes, Mapping)):
        raise FeatureDimensionError(f"{name} must be a 1D numeric sequence")
    if isinstance(values, np.ndarray):
        if values.ndim != 1:
            raise FeatureDimensionError(
                f"{name} must be 1D, got {values.ndim}D ndarray"
            )
        if values.dtype == np.bool_:
            raise FeatureDimensionError(f"{name} must not contain boolean elements")
        raw_list = values.tolist()
    else:
        try:
            raw_list = list(values)
        except TypeError as exc:
            raise FeatureDimensionError(
                f"{name} must be a 1D numeric sequence"
            ) from exc

    if len(raw_list) == 0:
        raise FeatureDimensionError(f"{name} must be non-empty")

    converted: list[float] = []
    for item in raw_list:
        if isinstance(item, (bool, np.bool_)) or not isinstance(
            item, (int, float, np.integer, np.floating)
        ):
            raise FeatureDimensionError(
                f"{name} contains non-numeric or boolean value"
            )
        f_val = float(item)
        if not math.isfinite(f_val):
            raise FeatureDimensionError(f"{name} must contain only finite floats")
        converted.append(f_val)

    return np.asarray(converted, dtype=np.float64)


def _ensure_uuid(value: UUID, *, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise UnauthorizedPersonalizationError(f"{field_name} must be a verified UUID")
    return value
