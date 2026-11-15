"""Shared base schemas for strict OpenAPI 3.1 contract enforcement."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    """Base schema forbidding undeclared fields (`additionalProperties: false`)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class HealthResponse(StrictSchema):
    """API health status response (`/api/v1/health`)."""

    status: Literal["ok", "degraded"]


class ReadyResponse(StrictSchema):
    """Readiness probe response for ``/api/v1/ready``."""

    ready: bool
    checks: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(StrictSchema):
    """Standardized error envelope across all endpoints."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str

