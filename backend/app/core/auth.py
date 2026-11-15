"""Authentication helpers and FastAPI dependencies for Bearer token extraction."""

from __future__ import annotations

import base64
import json

from fastapi import Header

from app.core.errors import AppError


def extract_user_id_from_authorization(authorization: str | None) -> str | None:
    """Extract user UUID (`sub`) from `Authorization: Bearer <jwt>` or `Bearer user:<id>`."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token:
        return None
    if token.startswith("user:"):
        return token.split("user:", 1)[1].strip() or None

    jwt_parts = token.split(".")
    if len(jwt_parts) == 3:
        try:
            payload_b64 = jwt_parts[1]
            padding = "=" * (-len(payload_b64) % 4)
            decoded = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
            data = json.loads(decoded)
            sub = data.get("sub")
            if isinstance(sub, str) and sub.strip():
                return sub.strip()
        except Exception:
            return None
    return token


def get_optional_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str | None:
    """FastAPI dependency returning the authenticated user_id if a Bearer token is present."""
    return extract_user_id_from_authorization(authorization)


def get_required_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """FastAPI dependency requiring a valid Bearer token; raises 401 UNAUTHORIZED otherwise."""
    user_id = extract_user_id_from_authorization(authorization)
    if not user_id:
        raise AppError(
            status_code=401,
            code="UNAUTHORIZED",
            message="Cần xác thực Bearer token hợp lệ để truy cập tài nguyên người dùng.",
            details={},
        )
    return user_id
