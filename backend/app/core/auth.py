"""Authentication helpers and FastAPI dependencies for Bearer token extraction."""

from __future__ import annotations

import base64
import json

from fastapi import Header


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

