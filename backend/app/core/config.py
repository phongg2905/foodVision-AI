"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field


# THUẬT TOÁN: Nạp biến môi trường từ tệp `.env` cấp dự án mà không ghi đè biến hệ thống
def _load_dotenv() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    for env_path in (repo_root / ".env", repo_root.parent / ".env"):
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Typed runtime settings shared across Catalog, Reasoning, MCDA, and Vision AI layers."""

    app_name: str = "FoodVision AI REST API — Official Contract"
    app_version: str = "1.1.0"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "https://aqjeztwtqkhvjjxnsijs.supabase.co")
    )
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    direct_url: str = field(default_factory=lambda: os.getenv("DIRECT_URL", ""))
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]
    )
    max_upload_bytes: int = field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_BYTES", "5242880"))
    )
    max_image_pixels: int = field(
        default_factory=lambda: int(os.getenv("MAX_IMAGE_PIXELS", "16777216"))
    )
    min_image_dimension: int = field(
        default_factory=lambda: int(os.getenv("MIN_IMAGE_DIMENSION", "64"))
    )
    inference_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "10.0"))
    )
    inference_timeout_ms: int = field(
        default_factory=lambda: int(
            os.getenv(
                "INFERENCE_TIMEOUT_MS",
                str(int(float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "10.0")) * 1000)),
            )
        )
    )
    max_concurrent_inferences: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_INFERENCES", "2"))
    )
    trgm_similarity_threshold: float = field(
        default_factory=lambda: float(os.getenv("TRGM_SIMILARITY_THRESHOLD", "0.30"))
    )
    review_confidence_threshold: float = 0.80
    default_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.25"))
    )
    default_review_threshold: float = field(
        default_factory=lambda: float(os.getenv("DEFAULT_REVIEW_THRESHOLD", "0.80"))
    )
    default_reference_minutes: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_REFERENCE_MINUTES", "15"))
    )
    model_artifact_path: str = field(
        default_factory=lambda: os.getenv(
            "MODEL_ARTIFACT_PATH", "weights/yolo/ingredients_best.pt"
        )
    )
    active_model_version: str = field(
        default_factory=lambda: os.getenv(
            "ACTIVE_MODEL_VERSION", "yolo11n-foodvision-v1.0"
        )
    )
    enable_clip_fallback: bool = field(
        default_factory=lambda: os.getenv("ENABLE_CLIP_FALLBACK", "false").lower()
        in {"1", "true", "yes", "on"}
    )
    model_config_path: str = field(
        default_factory=lambda: os.getenv("MODEL_CONFIG", "")
    )


settings = Settings()


# THUẬT TOÁN: Truy xuất cấu hình hệ thống đồng bộ với Dependency Injection của FastAPI
def get_settings() -> Settings:
    """Return current runtime settings instance."""
    return settings


def reset_settings_cache() -> None:
    """Rebuild settings from current environment variables (used in isolated tests)."""
    global settings
    settings = Settings()
