"""Post-hoc confidence calibration (Identity, Temperature Scaling, Platt Scaling)."""

from __future__ import annotations

import math
import os

from .exceptions import DetectorConfigurationError
from .models import ConfidenceCalibrator

# ==============================================================================
# THUẬT TOÁN: Hiệu chỉnh xác suất hậu nghiệm (Post-hoc Probability Calibration)
# - Cơ sở khoa học (Guo et al., ICML 2017; Platt, 1999):
#   Điểm tự tin thô s ∈ [0, 1] từ đầu ra mạng YOLO thường quá tự tin (overconfident)
#   và không phản ánh xác suất đúng thực nghiệm P(Ŷ = Y | S = s).
#   1. Biến đổi sang miền logit ổn định số học với biên kẹp ε = 1e-6:
#          z = ln(s' / (1 - s')),   với s' = clip(s, ε, 1 - ε)
#   2. Temperature Scaling:  p̂ = σ(z / T) = 1 / (1 + exp(-z / T)),  T > 0
#   3. Platt Logistic Scaling: p̂ = σ(a * z + b), hỗ trợ tham số riêng từng lớp (a_c, b_c)
#   4. IdentityCalibrator: giữ nguyên s nhưng đánh dấu `is_calibrated = False` để
#      tầng gọi phân biệt rõ điểm thô chưa hiệu chỉnh với xác suất đã hiệu chỉnh.
# - Độ phức tạp: O(1) cho mỗi hộp dự đoán.
# ==============================================================================
def _clamp_unit_probability(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Confidence value must be finite")
    return min(1.0, max(0.0, float(value)))


def _prob_to_logit(prob: float, eps: float = 1e-6) -> float:
    clamped = min(1.0 - eps, max(eps, _clamp_unit_probability(prob)))
    return math.log(clamped / (1.0 - clamped))


def _sigmoid(logit: float) -> float:
    if logit >= 0.0:
        exp_neg = math.exp(-logit)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(logit)
    return exp_pos / (1.0 + exp_pos)


class IdentityCalibrator:
    """Pass-through calibrator explicitly marking predictions as uncalibrated."""

    @property
    def method_name(self) -> str:
        return "identity"

    @property
    def is_calibrated(self) -> bool:
        return False

    def calibrate(
        self, raw_confidence: float, class_id: int | None = None
    ) -> float:
        _ = class_id
        return _clamp_unit_probability(raw_confidence)


class TemperatureScalingCalibrator:
    """Single-parameter Temperature Scaling calibrator fitted on validation set."""

    def __init__(self, temperature: float) -> None:
        if not math.isfinite(temperature) or temperature <= 0.0:
            raise ValueError("Temperature T must be a finite positive number")
        self._temperature = float(temperature)

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def method_name(self) -> str:
        return "temperature_scaling"

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(
        self, raw_confidence: float, class_id: int | None = None
    ) -> float:
        _ = class_id
        logit = _prob_to_logit(raw_confidence)
        return _clamp_unit_probability(_sigmoid(logit / self._temperature))


class PlattScalingCalibrator:
    """Affine logit Platt calibrator with optional per-class `(scale_a, shift_b)`."""

    def __init__(
        self,
        *,
        scale_a: float,
        shift_b: float,
        per_class_params: Mapping[int, tuple[float, float]] | None = None,
    ) -> None:
        if not (math.isfinite(scale_a) and math.isfinite(shift_b)):
            raise ValueError("Platt scaling parameters must be finite")
        self._scale_a = float(scale_a)
        self._shift_b = float(shift_b)
        self._per_class: dict[int, tuple[float, float]] = {}
        if per_class_params:
            for cls_id, (a_val, b_val) in per_class_params.items():
                if not (math.isfinite(a_val) and math.isfinite(b_val)):
                    raise ValueError("Per-class Platt parameters must be finite")
                self._per_class[int(cls_id)] = (float(a_val), float(b_val))

    @property
    def method_name(self) -> str:
        return "platt_scaling"

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(
        self, raw_confidence: float, class_id: int | None = None
    ) -> float:
        scale_a, shift_b = (
            self._per_class.get(class_id, (self._scale_a, self._shift_b))
            if class_id is not None
            else (self._scale_a, self._shift_b)
        )
        logit = _prob_to_logit(raw_confidence)
        return _clamp_unit_probability(_sigmoid(scale_a * logit + shift_b))


# ==============================================================================
# THUẬT TOÁN: Khởi tạo Bộ Hiệu chuẩn Độ tin cậy từ Biến Môi trường
# - Đọc chế độ `YOLO_CALIBRATION_MODE` (`none`, `temperature`, `platt`) cùng các tham số
#   nhiệt độ `T > 0` hoặc hệ số affine `(a, b)` để biến đổi xác suất hậu nghiệm.
# ==============================================================================
def build_calibrator_from_env() -> ConfidenceCalibrator:
    """Construct post-hoc calibrator from environment variables if configured."""
    method = os.getenv("CALIBRATION_METHOD", "identity").strip().lower()
    if not method or method == "identity":
        return IdentityCalibrator()
    if method == "temperature_scaling":
        raw_temp = os.getenv("CALIBRATION_TEMPERATURE", "").strip()
        if not raw_temp:
            raise DetectorConfigurationError(
                "Thiếu tham số CALIBRATION_TEMPERATURE cho phương pháp temperature_scaling.",
                details={"reason": "missing_calibration_temperature"},
            )
        return TemperatureScalingCalibrator(temperature=float(raw_temp))
    if method == "platt_scaling":
        raw_a = os.getenv("CALIBRATION_PLATT_A", "").strip()
        raw_b = os.getenv("CALIBRATION_PLATT_B", "").strip()
        if not raw_a or not raw_b:
            raise DetectorConfigurationError(
                "Thiếu tham số CALIBRATION_PLATT_A hoặc CALIBRATION_PLATT_B cho platt_scaling.",
                details={"reason": "missing_platt_parameters"},
            )
        return PlattScalingCalibrator(scale_a=float(raw_a), shift_b=float(raw_b))
    raise DetectorConfigurationError(
        "Phương pháp hiệu chỉnh xác suất không được hỗ trợ.",
        details={"reason": "unsupported_calibration_method", "method": method},
    )
