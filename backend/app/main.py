"""FastAPI Application Entrypoint — FoodVision AI Backend (`v1.1.0`)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    admin,
    ai_detect,
    health,
    ingredients,
    personalization,
    preferences,
    recipes,
    recommendations,
    user_features,
)
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    """Create and configure the FoodVision AI FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "FoodVision AI Backend API — Nhận diện nguyên liệu thực phẩm từ hình ảnh, "
            "Suy luận Thế giới mở 3 trạng thái, Cá nhân hóa 3 danh sách nguyên liệu và Gợi ý Công thức MCDA."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    # Standardized Error Handlers (`docs/03-api/api-conventions.md`)
    register_exception_handlers(app)

    # API v1 Routers (Stage 1..5: TP 01..14, ADR-013)
    api_v1_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_v1_prefix)
    app.include_router(ingredients.router, prefix=api_v1_prefix)
    app.include_router(recipes.router, prefix=api_v1_prefix)
    app.include_router(ai_detect.router, prefix=api_v1_prefix)
    app.include_router(recommendations.router, prefix=api_v1_prefix)
    app.include_router(preferences.router, prefix=api_v1_prefix)
    app.include_router(personalization.router, prefix=api_v1_prefix)
    app.include_router(user_features.router, prefix=api_v1_prefix)
    app.include_router(admin.router, prefix=api_v1_prefix)

    return app


app = create_app()
