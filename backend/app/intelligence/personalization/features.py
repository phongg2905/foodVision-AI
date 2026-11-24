"""18-dimensional deterministic recipe & kitchen context feature extraction."""

from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID
# CONFLICT-RESOLVED: Unify legacy app.intelligence.weighted_coverage and app.utils.text_normalizer
# with v1.1.0 app.services.coverage and app.services.vietnamese_search.norm_vi per ADR-013.
from app.core.database import RecipeRecord
from app.services.coverage import compute_recipe_weighted_coverage, compute_weighted_coverage
from app.services.vietnamese_search import norm_vi as normalize_vietnamese
from .config import PersonalizationConfig, _validate_1d_numeric_array
from .constants import (
    FEATURE_NAMES_V1,
    FEATURE_SCHEMA_VERSION,
    FeatureDimensionError,
    SchemaVersionError,
    _COOKING_METHOD_BUCKETS,
    _DIFFICULTY_LEVEL_MAP,
    _SCHEMA_REGISTRY,
)
from .models import CandidateRecipeContext

@dataclass(frozen=True, slots=True)
class RecipeFeatureInput:
    """Structured domain attributes for deterministic recipe feature encoding."""

    cuisine_code: str
    cooking_method: str | None = None
    total_minutes: int = 15
    difficulty: str | float | int | None = None
    ingredient_coverage: float = 0.0
    ingredient_required_ratio: float = 0.0
    ingredient_primary_match: float = 0.0
    required_ingredient_count: int = 1
    equipment_count: int = 0
    step_count: int = 1


@dataclass(frozen=True, slots=True)
class RecipeFeatureVector:
    """Immutable, ordered, schema-versioned feature vector `x_r`."""

    values: tuple[float, ...]
    schema_version: str = FEATURE_SCHEMA_VERSION
    feature_names: tuple[str, ...] = FEATURE_NAMES_V1

    def __post_init__(self) -> None:
        if self.schema_version not in _SCHEMA_REGISTRY:
            raise SchemaVersionError(
                f"Unknown feature schema version: {self.schema_version}"
            )
        expected_names = _SCHEMA_REGISTRY[self.schema_version]
        if (
            self.feature_names is not expected_names
            and tuple(self.feature_names) != expected_names
        ):
            raise SchemaVersionError(
                "feature_names order does not match registered schema definition"
            )
        if isinstance(self.values, tuple) and len(self.values) == len(expected_names):
            cleaned: list[float] = []
            for v in self.values:
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                    arr = _validate_1d_numeric_array(
                        self.values, name="RecipeFeatureVector.values"
                    )
                    object.__setattr__(self, "values", tuple(float(x) for x in arr.tolist()))
                    return
                cleaned.append(float(v))
            object.__setattr__(self, "values", tuple(cleaned))
            return

        arr = _validate_1d_numeric_array(self.values, name="RecipeFeatureVector.values")
        if arr.size != len(expected_names):
            raise FeatureDimensionError(
                f"Feature dimension mismatch: expected {len(expected_names)} "
                f"for {self.schema_version}, got {arr.size}"
            )
        object.__setattr__(self, "values", tuple(float(v) for v in arr.tolist()))

    @property
    def dimension(self) -> int:
        return len(self.values)

    def to_list(self) -> list[float]:
        return list(self.values)

    def to_dict(self) -> dict[str, float]:
        return dict(zip(self.feature_names, self.values, strict=True))


# ==============================================================================
# THUẬT TOÁN: Trích xuất & Chuẩn hóa Vector Đặc trưng Công thức Có Phiên bản (x_r ∈ [0, 1]^18)
# - Cơ sở thiết kế:
#   Ánh xạ tất định một công thức `r` cùng mức khớp nguyên liệu của người dùng thành
#   vector cố định 18 chiều (`lr-feature-v1.0`) theo đúng thứ tự `FEATURE_NAMES_V1`:
#     [0]     `bias` = 1.0 (hệ số chặn học độ khắt khe/dễ tính của từng người dùng)
#     [1..3]  One-hot nhóm ẩm thực (`VN`, `EU`, `US`)
#     [4..11] One-hot phương pháp chế biến đã chuẩn hóa tiếng Việt không dấu
#             (`canh`, `xao`, `kho`, `chien`, `nuong`, `luoc_hap`, `tron_salad`, `other`)
#     [12..13] Đặc trưng thời gian: độ nhanh `min(1, t* / max(1, t_r))` và thời lượng
#              chuẩn hóa `min(1, t_r / t_max)`
#     [14]    Độ khó `difficulty_norm ∈ [0, 1]` (từ nhãn tường minh hoặc ước lượng tổ hợp
#             từ tổng thời gian, số nguyên liệu bắt buộc, số bước nấu và số thiết bị)
#     [15..17] Đặc trưng khớp nguyên liệu (`ingredient_coverage` C, `required_ratio` E,
#              `primary_match` G)
# - Độ phức tạp: O(1) đối với `RecipeFeatureInput`, O(|Ingredients(r)|) đối với `CandidateRecipeContext`.
# ==============================================================================
def _normalize_difficulty(
    difficulty: str | float | int | None,
    *,
    total_minutes: int,
    required_ingredient_count: int,
    equipment_count: int,
    step_count: int,
    max_norm_minutes: int,
) -> float:
    if difficulty is not None:
        if isinstance(difficulty, bool):
            raise FeatureDimensionError("difficulty must not be a boolean")
        if isinstance(difficulty, (int, float)):
            val = float(difficulty)
            if not math.isfinite(val):
                raise FeatureDimensionError("difficulty float must be finite")
            return round(max(0.0, min(1.0, val)), 4)
        if isinstance(difficulty, str):
            norm_key = normalize_vietnamese(difficulty)
            if norm_key in _DIFFICULTY_LEVEL_MAP:
                return _DIFFICULTY_LEVEL_MAP[norm_key]
            raise FeatureDimensionError(f"Unsupported difficulty label: {difficulty!r}")

    time_factor = min(1.0, max(0, total_minutes) / float(max(1, max_norm_minutes)))
    ing_factor = min(1.0, max(0, required_ingredient_count - 1) / 8.0)
    step_factor = min(1.0, max(0, step_count - 1) / 8.0)
    equip_factor = min(1.0, max(0, equipment_count) / 4.0)
    composite = (
        0.40 * time_factor
        + 0.25 * ing_factor
        + 0.20 * step_factor
        + 0.15 * equip_factor
    )
    return round(max(0.0, min(1.0, composite)), 4)


_METHOD_SLOT_NAMES: tuple[str, ...] = (
    "method_canh",
    "method_xao",
    "method_kho",
    "method_chien",
    "method_nuong",
    "method_luoc_hap",
    "method_tron_salad",
    "method_other",
)
_METHOD_ONEHOT_VECTORS: dict[str, tuple[float, ...]] = {
    name: tuple(1.0 if i == idx else 0.0 for i in range(len(_METHOD_SLOT_NAMES)))
    for idx, name in enumerate(_METHOD_SLOT_NAMES)
}
_DEFAULT_METHOD_ONEHOT: tuple[float, ...] = _METHOD_ONEHOT_VECTORS["method_other"]


# ==============================================================================
# THUẬT TOÁN: Mã hóa Vector Đặc trưng Công thức 18 Chiều (`lr-feature-v1.0`)
# - Biểu diễn món ăn thành vector thực hữu hạn cố định 18 chiều thuộc [0, 1]:
#   1 chiều `bias=1.0`, 3 chiều one-hot ẩm thực (`VN/EU/US`), 8 chiều one-hot
#   phương pháp nấu chuẩn hóa tiếng Việt không dấu (tra cứu hằng O(1)), 3 chiều
#   thời gian & độ khó tổng hợp, và 3 chiều ngữ cảnh khớp nguyên liệu (`coverage`,
#   `required_ratio`, `primary_match`). Bảo đảm thứ tự chiều bất biến giữa huấn luyện và suy luận.
# - Độ phức tạp: O(1).
# ==============================================================================
def extract_recipe_feature_vector(
    feature_input: RecipeFeatureInput,
    *,
    config: PersonalizationConfig | None = None,
) -> RecipeFeatureVector:
    """Encode `RecipeFeatureInput` into an ordered `RecipeFeatureVector` (`lr-feature-v1.0`)."""
    cfg = config or PersonalizationConfig.from_settings()
    if cfg.feature_schema_version != FEATURE_SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Unsupported schema version: {cfg.feature_schema_version}"
        )
    if feature_input.total_minutes < 0:
        raise FeatureDimensionError("total_minutes must be >= 0")

    cuisine_upper = (feature_input.cuisine_code or "").strip().upper()
    c_vn = 1.0 if cuisine_upper == "VN" else 0.0
    c_eu = 1.0 if cuisine_upper == "EU" else 0.0
    c_us = 1.0 if cuisine_upper == "US" else 0.0

    norm_method = (
        normalize_vietnamese(feature_input.cooking_method)
        if feature_input.cooking_method
        else ""
    )
    matched_bucket = _COOKING_METHOD_BUCKETS.get(norm_method, "method_other")
    method_vec = _METHOD_ONEHOT_VECTORS.get(matched_bucket, _DEFAULT_METHOD_ONEHOT)

    t_minutes = float(feature_input.total_minutes)
    time_eff = round(
        min(1.0, float(cfg.reference_minutes) / max(1.0, t_minutes)), 4
    )
    time_dur = round(
        min(1.0, max(0.0, t_minutes) / float(max(1, cfg.max_norm_minutes))), 4
    )

    diff_norm = _normalize_difficulty(
        feature_input.difficulty,
        total_minutes=feature_input.total_minutes,
        required_ingredient_count=feature_input.required_ingredient_count,
        equipment_count=feature_input.equipment_count,
        step_count=feature_input.step_count,
        max_norm_minutes=cfg.max_norm_minutes,
    )

    cov = round(max(0.0, min(1.0, float(feature_input.ingredient_coverage))), 4)
    req_ratio = round(
        max(0.0, min(1.0, float(feature_input.ingredient_required_ratio))), 4
    )
    prim_match = round(
        max(0.0, min(1.0, float(feature_input.ingredient_primary_match))), 4
    )

    ordered_values: tuple[float, ...] = (
        1.0,
        c_vn,
        c_eu,
        c_us,
        *method_vec,
        time_eff,
        time_dur,
        diff_norm,
        cov,
        req_ratio,
        prim_match,
    )
    return RecipeFeatureVector(
        values=ordered_values,
        schema_version=cfg.feature_schema_version,
        feature_names=FEATURE_NAMES_V1,
    )


# ==============================================================================
# THUẬT TOÁN: Trích xuất Vector Đặc trưng Ngữ cảnh Trực tiếp từ Trạng thái Bếp
# - Tính độ phủ có trọng số `C`, tỷ lệ nguyên liệu bắt buộc `E` và khớp vai trò
#   chính `G` từ tập nguyên liệu xác nhận hiện có của người dùng, sau đó ủy quyền
#   cho `extract_recipe_feature_vector` sinh vector 18 chiều chuẩn `lr-feature-v1.0`.
# - Độ phức tạp: O(|Ingredients(r)|).
# ==============================================================================
def extract_context_feature_vector(
    recipe: CandidateRecipeContext | RecipeRecord,
    *,
    confirmed_main_ids: set[UUID | str] | frozenset[UUID | str] | list[str],
    all_pantry_ids: set[UUID | str] | frozenset[UUID | str] | None = None,
    excluded_pantry_ids: set[UUID | str] | frozenset[UUID | str] | None = None,
    focus_ids: set[UUID | str] | frozenset[UUID | str] | None = None,
    difficulty: str | float | int | None = None,
    step_count: int = 1,
    config: PersonalizationConfig | None = None,
) -> RecipeFeatureVector:
    """Build `RecipeFeatureVector` directly from `CandidateRecipeContext` or `RecipeRecord` and kitchen state."""
    if isinstance(recipe, RecipeRecord):
        u_str = {str(i) for i in confirmed_main_ids}
        x_str = {str(i) for i in (excluded_pantry_ids or set())}
        pantry_str = {str(i) for i in (all_pantry_ids or set())} | {
            ri.ingredient_id for ri in recipe.ingredients if ri.category == "pantry"
        }
        confirmed_avail = u_str | (pantry_str - x_str)
        c_val = compute_recipe_weighted_coverage(recipe, confirmed_avail)
        req_ids = [ri.ingredient_id for ri in recipe.ingredients if ri.is_required]
        e_mvp = (
            sum(1 for iid in req_ids if iid in confirmed_avail) / float(len(req_ids))
            if req_ids
            else 0.0
        )
        focus_str = {str(i) for i in focus_ids} if focus_ids is not None else u_str
        main_ids = {ri.ingredient_id for ri in recipe.ingredients if ri.dish_role == "main"}
        sub_ids = {ri.ingredient_id for ri in recipe.ingredients if ri.dish_role != "main"}
        if main_ids & focus_str:
            g_val = 1.0
        elif sub_ids & focus_str:
            g_val = 0.5
        else:
            g_val = 0.0
        feat_in = RecipeFeatureInput(
            cuisine_code=recipe.cuisine_code,
            cooking_method=recipe.cooking_method,
            total_minutes=recipe.total_minutes,
            difficulty=difficulty,
            ingredient_coverage=c_val,
            ingredient_required_ratio=e_mvp,
            ingredient_primary_match=g_val,
            required_ingredient_count=max(1, len(req_ids)),
            equipment_count=len(recipe.required_equipment),
            step_count=max(1, len(recipe.steps) or step_count),
        )
        return extract_recipe_feature_vector(feat_in, config=config)

    u_set = set(confirmed_main_ids)
    pantry_set = set(all_pantry_ids or set())
    x_set = set(excluded_pantry_ids or set())

    req_all = set(recipe.required_main_ids) | set(recipe.required_pantry_ids)
    avail_mvp = u_set | (set(recipe.required_pantry_ids) - x_set)
    e_mvp = (
        len(req_all & avail_mvp) / float(len(req_all))
        if req_all
        else 0.0
    )
    all_ing = req_all | set(recipe.optional_main_ids)
    c_mvp = (
        len(all_ing & avail_mvp) / float(len(all_ing))
        if all_ing
        else 0.0
    )
    if recipe.weights:
        confirmed_available = {str(i) for i in (u_set | (pantry_set - x_set))}
        str_weights = {str(k): float(v) for k, v in recipe.weights.items()}
        c_val = compute_weighted_coverage(str_weights, confirmed_available)
    else:
        c_val = c_mvp

    focus = set(focus_ids) if focus_ids is not None else u_set
    if recipe.primary_ids & focus:
        g_val = 1.0
    elif (recipe.essential_ids | set(recipe.weights.keys()) | recipe.required_main_ids) & focus:
        g_val = 0.5
    else:
        g_val = 0.0

    effective_difficulty = (
        difficulty if difficulty is not None else getattr(recipe, "difficulty", None)
    )
    feat_in = RecipeFeatureInput(
        cuisine_code=recipe.cuisine_code,
        cooking_method=recipe.cooking_method,
        total_minutes=recipe.total_minutes,
        difficulty=effective_difficulty,
        ingredient_coverage=c_val,
        ingredient_required_ratio=e_mvp,
        ingredient_primary_match=g_val,
        required_ingredient_count=max(1, len(recipe.required_all_ids)),
        equipment_count=len(recipe.required_equipment),
        step_count=max(1, step_count),
    )
    return extract_recipe_feature_vector(feat_in, config=config)
