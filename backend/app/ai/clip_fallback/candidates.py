"""Configuration helpers, cosine similarity math, KB filtering, and trigger gating."""

from __future__ import annotations

from .models import CandidateEmbedding
from collections.abc import Mapping

from collections.abc import Sequence
import math
import os
from typing import Any
from uuid import UUID

import numpy as np

from app.core.config import get_settings
from .models import (
    FallbackTriggerReason,
    InitialYOLOPrediction,
    KBCandidateIngredient,
    _coerce_uuid,
)

def _env_float(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    val = float(raw.strip())
    if not math.isfinite(val):
        raise ValueError(f"Environment variable {name} must be finite")
    return val


def _env_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return int(raw.strip())


def _resolve_review_threshold(explicit: float | None) -> float:
    if explicit is not None:
        return float(explicit)
    env_val = _env_float("CLIP_REVIEW_THRESHOLD")
    if env_val is not None:
        return env_val
    return float(get_settings().default_review_threshold)


def _resolve_min_similarity(explicit: float | None) -> float:
    if explicit is not None:
        return float(explicit)
    env_val = _env_float("CLIP_MIN_SIMILARITY")
    if env_val is not None:
        return env_val
    return float(get_settings().default_confidence_threshold)


def _resolve_top_k(explicit: int | None, candidate_count: int) -> int:
    if explicit is not None:
        return int(explicit)
    env_val = _env_int("CLIP_TOP_K")
    if env_val is not None:
        return env_val
    return candidate_count


# ==============================================================================
# THUẬT TOÁN: Độ tương đồng Cosine đa phương thức CLIP — Sim(I, T_m)
# - Công thức (Radford et al., ICML 2021):
#       Sim(I, T_m) = (f(I) · g(T_m)) / (||f(I)||_2 * ||g(T_m)||_2) ∈ [-1, 1]
# - Ý tưởng: Đo cô-sin góc định hướng giữa vector đặc trưng vùng ảnh f(I) và vector
#   mô tả văn bản chuẩn g(T_m) của nguyên liệu trong Knowledge Base.
# - Ranh giới ngữ nghĩa: Giá trị trả về là độ tương đồng định hướng chưa hiệu chỉnh,
#   TUYỆT ĐỐI không diễn giải thành xác suất nhận diện chính xác P(y | I).
# - Độ phức tạp: O(d) cho 1 cặp vector; O(M * d) cho ma trận M ứng viên chiều d.
# ==============================================================================
def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute L2-normalized cosine similarity in `[-1.0, 1.0]` between 1-D vectors."""
    a = np.asarray(vec_a, dtype=np.float64).ravel()
    b = np.asarray(vec_b, dtype=np.float64).ravel()
    if a.size == 0 or a.size != b.size:
        raise ValueError("Feature vectors must be non-empty and match in dimension")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("Feature vectors must contain only finite numbers")

    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    raw_cos = float(np.dot(a, b) / (norm_a * norm_b))
    return max(-1.0, min(1.0, raw_cos))


# ==============================================================================
# THUẬT TOÁN: Tính Tương đồng Cosine Hàng loạt có Chuẩn hóa Vector L2 (Batch Cosine)
# - Chuẩn hóa L2 vector truy vấn ảnh `q` và ma trận văn bản `M`, tính tích vô hướng
#   vector hóa `M_norm @ q_norm` và kẹp miền giá trị trong `[-1.0, 1.0]`.
# - Độ phức tạp: O(N * D) với N là số ứng viên KB và D là số chiều không gian nhúng.
# ==============================================================================
def compute_cosine_similarities(
    image_vec: np.ndarray,
    text_matrix: np.ndarray,
) -> np.ndarray:
    """Compute vectorized L2-normalized cosine similarities against `(M, d)` embeddings."""
    img = np.asarray(image_vec, dtype=np.float64).ravel()
    mat = np.asarray(text_matrix, dtype=np.float64)
    if mat.ndim == 1:
        mat = mat.reshape(1, -1)
    if img.size == 0 or mat.ndim != 2 or mat.shape[0] == 0 or mat.shape[1] != img.size:
        raise ValueError("Incompatible image vector and text embedding matrix shapes")
    if not (np.all(np.isfinite(img)) and np.all(np.isfinite(mat))):
        raise ValueError("Embeddings must contain only finite numbers")

    img_norm = float(np.linalg.norm(img))
    if img_norm == 0.0:
        return np.zeros(mat.shape[0], dtype=np.float64)

    row_norms = np.linalg.norm(mat, axis=1)
    sims = np.zeros(mat.shape[0], dtype=np.float64)
    valid_rows = row_norms > 0.0
    if np.any(valid_rows):
        dots = mat[valid_rows] @ img
        sims[valid_rows] = np.clip(dots / (row_norms[valid_rows] * img_norm), -1.0, 1.0)
    return sims


# ==============================================================================
# THUẬT TOÁN: Chuẩn hóa & Lọc Ứng viên Chỉ-đọc từ Knowledge Base (KB Read-Only Filter)
# - Ý tưởng: Chuyển đổi bản ghi nguyên liệu từ Knowledge Base sang tập bất biến,
#   chỉ giữ nguyên liệu đang hoạt động (`is_active == True`), loại trừ hoàn toàn
#   nhóm gia vị nền (`category != 'pantry'`) theo `BR-04` & `BR-12`, và khử trùng lặp
#   theo `ingredient_id` mà không bao giờ ghi hay thêm nhãn mới vào Knowledge Base.
# - Độ phức tạp: O(N) với N là số bản ghi đầu vào.
# ==============================================================================
def filter_kb_candidates(
    raw_candidates: Sequence[Any] | None,
) -> tuple[KBCandidateIngredient, ...]:
    """Filter active non-pantry Knowledge Base candidates into an immutable tuple."""
    if not raw_candidates:
        return ()

    deduped: dict[UUID, KBCandidateIngredient] = {}
    for item in raw_candidates:
        cand = _coerce_kb_candidate(item)
        if cand is None:
            continue
        if not cand.is_active or cand.category.strip().casefold() == "pantry":
            continue
        if not cand.name_vi.strip():
            continue
        if cand.ingredient_id not in deduped:
            deduped[cand.ingredient_id] = cand
    return tuple(deduped.values())


def _extract_alias_strings(raw_aliases: Any) -> tuple[str, ...]:
    if not raw_aliases:
        return ()
    extracted: list[str] = []
    for item in raw_aliases:
        text = getattr(item, "alias", item)
        if isinstance(text, str) and text.strip():
            extracted.append(text.strip())
    return tuple(extracted)


# ==============================================================================
# THUẬT TOÁN: Ép kiểu & Làm sạch Ứng viên Cơ sở Tri thức cho Bộ Xếp hạng CLIP
# - Trích xuất định danh UUID, tên tiếng Việt, nhóm nguyên liệu và danh sách từ đồng nghĩa,
#   từ chối các bản ghi thiếu mã hợp lệ trước khi đưa vào không gian nhúng.
# ==============================================================================
def _coerce_kb_candidate(item: Any) -> KBCandidateIngredient | None:
    if isinstance(item, KBCandidateIngredient):
        return item
    if isinstance(item, CandidateEmbedding):
        return KBCandidateIngredient(
            ingredient_id=item.ingredient_id,
            name_vi=item.name_vi,
            embedding=item.embedding,
        )
    if isinstance(item, Mapping):
        ing_id = _coerce_uuid(item.get("ingredient_id") or item.get("id"))
        name_vi = str(item.get("name_vi", "")).strip()
        if ing_id is None or not name_vi:
            return None
        emb = item.get("embedding")
        raw_en = item.get("name_en")
        return KBCandidateIngredient(
            ingredient_id=ing_id,
            name_vi=name_vi,
            slug=str(item.get("slug", "")).strip(),
            name_en=str(raw_en).strip() if isinstance(raw_en, str) and raw_en.strip() else None,
            category=str(item.get("category", "other")).strip() or "other",
            is_active=bool(item.get("is_active", True)),
            aliases=_extract_alias_strings(item.get("aliases")),
            prompts=tuple(str(p) for p in (item.get("prompts") or ())),
            embedding=np.asarray(emb, dtype=np.float64) if emb is not None else None,
        )

    ing_id = _coerce_uuid(
        getattr(item, "ingredient_id", None) or getattr(item, "id", None)
    )
    name_vi = str(getattr(item, "name_vi", "") or "").strip()
    if ing_id is None or not name_vi:
        return None
    raw_emb = getattr(item, "embedding", None)
    raw_en = getattr(item, "name_en", None)
    return KBCandidateIngredient(
        ingredient_id=ing_id,
        name_vi=name_vi,
        slug=str(getattr(item, "slug", "") or "").strip(),
        name_en=str(raw_en).strip() if isinstance(raw_en, str) and raw_en.strip() else None,
        category=str(getattr(item, "category", "other") or "other").strip(),
        is_active=bool(getattr(item, "is_active", True)),
        aliases=_extract_alias_strings(getattr(item, "aliases", None)),
        prompts=tuple(str(p) for p in (getattr(item, "prompts", ()) or ())),
        embedding=np.asarray(raw_emb, dtype=np.float64) if raw_emb is not None else None,
    )


# ==============================================================================
# THUẬT TOÁN: Cổng Kích hoạt Fallback Có điều kiện (Conditional Fallback Gate)
# - Luật kích hoạt:
#   1. `requested_by_backend == True`           -> `BACKEND_REQUESTED`
#   2. Không có dự đoán từ detector             -> `NO_DETECTOR_PREDICTION`
#   3. Nhãn YOLO chưa ánh xạ (`ingredient_id` rỗng hoặc `is_unresolved`)
#                                               -> `UNRESOLVED_YOLO_LABEL`
#   4. Độ tin cậy detector thấp (`conf < tau`) hoặc đã gắn `needs_confirmation`
#                                               -> `LOW_DETECTOR_CONFIDENCE`
#   5. Ngược lại (`conf >= tau` & nhãn hợp lệ) -> Bỏ qua fallback (`False, None`).
# - Độ phức tạp: O(1).
# ==============================================================================
def should_trigger_fallback(
    yolo_prediction: Any = None,
    *,
    review_threshold: float | None = None,
    requested_by_backend: bool = False,
) -> tuple[bool, FallbackTriggerReason | None]:
    """Determine whether CLIP/VLM fallback should activate for a detection/image."""
    if requested_by_backend:
        return True, FallbackTriggerReason.BACKEND_REQUESTED

    pred = InitialYOLOPrediction.from_any(yolo_prediction)
    tau = _resolve_review_threshold(review_threshold)

    has_any_signal = (
        pred.ingredient_id is not None
        or pred.display_label is not None
        or pred.confidence is not None
    )
    if not has_any_signal:
        return True, FallbackTriggerReason.NO_DETECTOR_PREDICTION

    if pred.is_unresolved or pred.ingredient_id is None or pred.display_label is None:
        return True, FallbackTriggerReason.UNRESOLVED_YOLO_LABEL

    if (
        pred.needs_confirmation
        or pred.confidence is None
        or not math.isfinite(pred.confidence)
        or pred.confidence < tau
    ):
        return True, FallbackTriggerReason.LOW_DETECTOR_CONFIDENCE

    return False, None
