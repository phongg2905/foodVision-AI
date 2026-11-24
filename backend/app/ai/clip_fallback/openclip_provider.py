"""Callable, OpenCLIP, and Cosine-similarity multimodal providers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import os
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .models import (
    FallbackModelError,
    KBCandidateIngredient,
    ProviderAssessment,
)

class CallableEmbeddingProvider:
    """Dependency-injection embedding provider for offline/unit testing without paid APIs."""

    def __init__(
        self,
        *,
        image_encoder: Callable[[np.ndarray], np.ndarray],
        text_encoder: Callable[[Sequence[str]], np.ndarray | Sequence[np.ndarray]],
        model_source: str,
    ) -> None:
        if not model_source or not model_source.strip():
            raise ValueError("model_source must be a non-empty identifier")
        self._image_encoder = image_encoder
        self._text_encoder = text_encoder
        self._model_source = model_source.strip()

    @property
    def model_source(self) -> str:
        return self._model_source

    def encode_image(self, rgb_image: np.ndarray) -> np.ndarray:
        return np.asarray(self._image_encoder(rgb_image), dtype=np.float64)

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray | Sequence[np.ndarray]:
        return self._text_encoder(texts)


class CallableFallbackProvider:
    """Dependency-injection fallback provider for deterministic VLM/custom testing."""

    def __init__(
        self,
        *,
        assessor: Callable[
            [np.ndarray, Sequence[KBCandidateIngredient]], ProviderAssessment
        ],
        model_source: str,
    ) -> None:
        if not model_source or not model_source.strip():
            raise ValueError("model_source must be a non-empty identifier")
        self._assessor = assessor
        self._model_source = model_source.strip()

    @property
    def model_source(self) -> str:
        return self._model_source

    def assess_candidates(
        self,
        rgb_image: np.ndarray,
        candidates: Sequence[KBCandidateIngredient],
    ) -> ProviderAssessment:
        return self._assessor(rgb_image, candidates)


class OpenCLIPEmbeddingProvider:
    """Lazy `open_clip` adapter reading all model/weights identifiers from config or env."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        pretrained: str | None = None,
        weights_path: str | None = None,
        device: str | None = None,
    ) -> None:
        self._model_name = (model_name or os.getenv("CLIP_MODEL_NAME") or "").strip()
        self._pretrained = (pretrained or os.getenv("CLIP_PRETRAINED") or "").strip() or None
        self._weights_path = (
            weights_path or os.getenv("CLIP_WEIGHTS_PATH") or ""
        ).strip() or None
        self._device = (device or os.getenv("CLIP_DEVICE") or "").strip() or "cpu"
        self._model: Any = None
        self._preprocess: Any = None
        self._tokenizer: Any = None
        self._torch: Any = None

    @property
    def model_source(self) -> str:
        if not self._model_name:
            return "open_clip:unconfigured"
        tag = self._pretrained or (
            Path(self._weights_path).name if self._weights_path else "custom"
        )
        return f"open_clip:{self._model_name}:{tag}"

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        if not self._model_name:
            raise FallbackModelError("CLIP model_name is not configured")
        if self._weights_path and not Path(self._weights_path).is_file():
            raise FallbackModelError("Configured CLIP weights_path does not exist")
        try:
            import open_clip  # type: ignore[import-not-found]
            import torch
        except ImportError as exc:
            raise FallbackModelError("open_clip or torch is not installed") from exc

        try:
            pretrained_arg = None if self._weights_path else self._pretrained
            model, _, preprocess = open_clip.create_model_and_transforms(
                self._model_name,
                pretrained=pretrained_arg,
                device=self._device,
            )
            if self._weights_path:
                state = torch.load(
                    self._weights_path, map_location=self._device, weights_only=True
                )
                model.load_state_dict(state, strict=False)
            model.eval()
            self._model = model
            self._preprocess = preprocess
            self._tokenizer = open_clip.get_tokenizer(self._model_name)
            self._torch = torch
        except Exception as exc:
            raise FallbackModelError("Failed to initialize OpenCLIP model") from exc

    def encode_image(self, rgb_image: np.ndarray) -> np.ndarray:
        self._ensure_loaded()
        pil_img = Image.fromarray(rgb_image)
        try:
            tensor = self._preprocess(pil_img).unsqueeze(0).to(self._device)
            with self._torch.inference_mode():
                feat = self._model.encode_image(tensor)
            return np.asarray(feat[0].detach().cpu().numpy(), dtype=np.float64)
        except Exception as exc:
            raise FallbackModelError("OpenCLIP image encoding failed") from exc
        finally:
            pil_img.close()

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray:
        self._ensure_loaded()
        if not texts:
            return np.empty((0, 0), dtype=np.float64)
        try:
            tokens = self._tokenizer(list(texts)).to(self._device)
            with self._torch.inference_mode():
                feats = self._model.encode_text(tokens)
            return np.asarray(feats.detach().cpu().numpy(), dtype=np.float64)
        except Exception as exc:
            raise FallbackModelError("OpenCLIP text encoding failed") from exc
