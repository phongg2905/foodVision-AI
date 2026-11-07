"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field


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
    app_name: str = "FoodVision AI REST API — Official Contract"
    app_version: str = "1.0.0"
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
    inference_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "10.0"))
    )
    max_concurrent_inferences: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_INFERENCES", "2"))
    )
    trgm_similarity_threshold: float = field(
        default_factory=lambda: float(os.getenv("TRGM_SIMILARITY_THRESHOLD", "0.30"))
    )
    review_confidence_threshold: float = 0.80


settings = Settings()

