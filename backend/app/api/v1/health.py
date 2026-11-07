"""Healthcheck Endpoint (`GET /api/v1/health`) — OPS-01."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.core.database import CatalogRepository, get_catalog_repo


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]


router = APIRouter(tags=["System & Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> HealthResponse:
    """Return service health status (`ok` or `degraded`)."""
    is_healthy = repo.check_health()
    return HealthResponse(status="ok" if is_healthy else "degraded")
