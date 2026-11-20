"""FastAPI Application Entrypoint — FoodVision AI Backend (`v1.1.0`)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CONFLICT-RESOLVED: Combine PR #12 preferences router with Stage 3 ai_detect router.
from app.api.v1 import (
    ai_detect,
    health,
    ingredients,
    personalization,
    preferences,
    recipes,
    recommendations,
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

    # CONFLICT-RESOLVED: Register Stage 1..3 routers including ai_detect and PR #12 preferences.
    # API v1 Routers (Stage 1, Stage 2 & Stage 3: TP 01..07, TP 09, TP 13, TP 14, ADR-013)
    api_v1_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_v1_prefix)
    app.include_router(ingredients.router, prefix=api_v1_prefix)
    app.include_router(recipes.router, prefix=api_v1_prefix)
    app.include_router(ai_detect.router, prefix=api_v1_prefix)
    app.include_router(recommendations.router, prefix=api_v1_prefix)
    app.include_router(preferences.router, prefix=api_v1_prefix)
    app.include_router(personalization.router, prefix=api_v1_prefix)

    return app


app = create_app()
