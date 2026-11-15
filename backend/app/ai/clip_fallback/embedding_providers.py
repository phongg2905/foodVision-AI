"""Re-exported callable, OpenCLIP, and Cosine-similarity providers."""

from .cosine_provider import CLIPCosineProvider
from .openclip_provider import (
    CallableEmbeddingProvider,
    CallableFallbackProvider,
    OpenCLIPEmbeddingProvider,
)

__all__ = [
    "CLIPCosineProvider",
    "CallableEmbeddingProvider",
    "CallableFallbackProvider",
    "OpenCLIPEmbeddingProvider",
]
