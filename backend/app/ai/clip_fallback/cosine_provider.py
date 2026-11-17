"""Cosine-similarity candidate ranker over multimodal text/image embeddings."""

from __future__ import annotations

from .candidates import _env_float
from .candidates import compute_cosine_similarity

from collections.abc import Sequence
import threading

import numpy as np

from .candidates import compute_cosine_similarities
from .models import (
    FallbackConfig,
    FallbackModelError,
    FallbackProvider,
    KBCandidateIngredient,
    MultimodalEmbeddingProvider,
    ProviderAssessment,
    RankedCandidate,
    ScoreMetricType,
)



# ==============================================================================
# THUẬT TOÁN: Đối sánh Biểu diễn Đa phương thức & Kiểm tra Biên Âm tính / OOD
# - Ý tưởng:
#   1. Mã hóa vùng ảnh thành f(I) và các mô tả văn bản của từng ứng viên KB thành
#      tập vector {g(T_{m,k})}; điểm tương đồng của ứng viên m là:
#          s_m = max_k Sim(I, T_{m,k})
#   2. Nếu có bộ mô tả đối chứng không phải thực phẩm (`non_food_prompts`) hoặc ngoài
#      phân phối (`ood_prompts`) được truyền vào cấu hình, so sánh:
#          max_neg + negative_margin >= max_m s_m
#      để phát hiện ảnh ngoài miền thực phẩm trước khi xếp hạng.
# - Độ phức tạp: O(P * d) với P là tổng số mô tả văn bản (có bộ nhớ đệm RAM).
# ==============================================================================
class CLIPCosineProvider:
    """Fallback provider matching image & KB text embeddings via Cosine Similarity."""

    def __init__(
        self,
        embedding_provider: MultimodalEmbeddingProvider,
        *,
        non_food_prompts: Sequence[str] = (),
        ood_prompts: Sequence[str] = (),
        negative_margin: float | None = None,
        max_cache_entries: int = 2048,
    ) -> None:
        self._embedder = embedding_provider
        self._non_food_prompts = tuple(p.strip() for p in non_food_prompts if p.strip())
        self._ood_prompts = tuple(p.strip() for p in ood_prompts if p.strip())
        env_neg_margin = _env_float("CLIP_NEGATIVE_MARGIN")
        self._negative_margin = (
            float(negative_margin)
            if negative_margin is not None
            else (env_neg_margin if env_neg_margin is not None else 0.0)
        )
        self._max_cache_entries = max(0, int(max_cache_entries))
        self._text_cache: dict[str, np.ndarray] = {}

    @property
    def model_source(self) -> str:
        return self._embedder.model_source

    def _encode_prompts_cached(self, prompts: Sequence[str]) -> np.ndarray:
        missing = [p for p in prompts if p not in self._text_cache]
        if missing:
            raw_vecs = self._embedder.encode_texts(missing)
            mat = np.asarray(raw_vecs, dtype=np.float64)
            if mat.ndim == 1:
                mat = mat.reshape(1, -1)
            if mat.shape[0] != len(missing):
                raise FallbackModelError("Text encoder output count mismatch")
            for text, vec in zip(missing, mat, strict=True):
                if (
                    self._max_cache_entries > 0
                    and len(self._text_cache) >= self._max_cache_entries
                ):
                    self._text_cache.clear()
                if self._max_cache_entries > 0:
                    self._text_cache[text] = np.asarray(vec, dtype=np.float64).ravel()

        return np.vstack(
            [
                self._text_cache[p]
                if p in self._text_cache
                else np.asarray(self._embedder.encode_texts([p]), dtype=np.float64).ravel()
                for p in prompts
            ]
        )

    def assess_candidates(
        self,
        rgb_image: np.ndarray,
        candidates: Sequence[KBCandidateIngredient],
    ) -> ProviderAssessment:
        try:
            img_vec = np.asarray(
                self._embedder.encode_image(rgb_image), dtype=np.float64
            ).ravel()
            if img_vec.size == 0 or not np.all(np.isfinite(img_vec)):
                raise FallbackModelError("Invalid or non-finite image embedding")
            if float(np.linalg.norm(img_vec)) == 0.0:
                return ProviderAssessment(
                    scores_by_id={},
                    model_source=self.model_source,
                    score_type=ScoreMetricType.COSINE_SIMILARITY,
                    is_out_of_distribution=True,
                )

            scores_by_id: dict[UUID, float] = {}
            prompts_to_encode: list[str] = []
            prompt_owners: list[UUID] = []

            for cand in candidates:
                if cand.embedding is not None:
                    scores_by_id[cand.ingredient_id] = compute_cosine_similarity(
                        img_vec, cand.embedding
                    )
                else:
                    descriptors = cand.text_descriptors()
                    for desc in descriptors:
                        prompts_to_encode.append(desc)
                        prompt_owners.append(cand.ingredient_id)

            if prompts_to_encode:
                unique_prompts = list(dict.fromkeys(prompts_to_encode))
                unique_mat = self._encode_prompts_cached(unique_prompts)
                unique_sims = compute_cosine_similarities(img_vec, unique_mat)
                sim_by_prompt = dict(
                    zip(unique_prompts, unique_sims.tolist(), strict=True)
                )
                for desc, owner_id in zip(prompts_to_encode, prompt_owners, strict=True):
                    sim = float(sim_by_prompt[desc])
                    prev = scores_by_id.get(owner_id)
                    if prev is None or sim > prev:
                        scores_by_id[owner_id] = sim

            best_food_sim = max(scores_by_id.values(), default=-1.0)
            is_non_food = False
            is_ood = False

            if self._non_food_prompts:
                nf_mat = self._encode_prompts_cached(self._non_food_prompts)
                nf_max = float(np.max(compute_cosine_similarities(img_vec, nf_mat)))
                if nf_max + self._negative_margin >= best_food_sim:
                    is_non_food = True

            if not is_non_food and self._ood_prompts:
                ood_mat = self._encode_prompts_cached(self._ood_prompts)
                ood_max = float(np.max(compute_cosine_similarities(img_vec, ood_mat)))
                if ood_max + self._negative_margin >= best_food_sim:
                    is_ood = True

            return ProviderAssessment(
                scores_by_id=scores_by_id,
                model_source=self.model_source,
                score_type=ScoreMetricType.COSINE_SIMILARITY,
                is_non_food=is_non_food,
                is_out_of_distribution=is_ood,
            )
        except FallbackModelError:
            raise
        except Exception as exc:
            raise FallbackModelError("CLIP cosine candidate assessment failed") from exc
