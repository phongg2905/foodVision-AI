"""Authentication & Authorization dependencies (`FR-09a`, `FR-09b`, `NFR-04`, `SEC-01`, `SEC-03`)."""

from __future__ import annotations

import base64
import functools
import json
import time
import uuid

import jwt
from fastapi import Depends, Header

from app.core.config import settings
from app.core.database import CatalogRepository, get_catalog_repo
from app.core.errors import AppError

ADMIN_SEED_USER_ID = "00000000-0000-4000-8000-000000000001"
_PLACEHOLDER_SECRETS = {"", "your-supabase-jwt-secret"}


def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


@functools.lru_cache(maxsize=4)
def _get_jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


def extract_user_id_from_authorization(authorization: str | None) -> str | None:
    """Extract and validate user UUID (`sub`) from `Authorization: Bearer <jwt>` or dev `Bearer user:<uuid>`."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token:
        return None

    # Deterministic test/dev token helper (`Bearer user:<uuid>`) — disabled in production
    if token.startswith("user:"):
        if settings.app_env == "production":
            return None
        candidate = token.split("user:", 1)[1].strip()
        return candidate if _is_valid_uuid(candidate) else None

    jwt_parts = token.split(".")
    if len(jwt_parts) != 3:
        return None

    try:
        header_data = json.loads(_b64url_decode(jwt_parts[0]).decode("utf-8"))
        alg = str(header_data.get("alg") or "").upper()
        jwt_secret = settings.supabase_jwt_secret.strip()
        has_real_hs_secret = jwt_secret not in _PLACEHOLDER_SECRETS

        # 1. Asymmetric Supabase JWT (ES256 / RS256) verified via JWKS
        if alg in {"ES256", "RS256"} and settings.supabase_url.strip():
            base_url = settings.supabase_url.strip().rstrip("/")
            jwks_client = _get_jwks_client(f"{base_url}/auth/v1/.well-known/jwks.json")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                issuer=f"{base_url}/auth/v1",
                options={"verify_aud": False},
            )
        # 2. Symmetric HS256 JWT verified with SUPABASE_JWT_SECRET when configured
        elif alg == "HS256" and has_real_hs_secret:
            data = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        # 3. Non-production unit test JWTs when no real secret is configured
        elif settings.app_env != "production" and not has_real_hs_secret:
            data = json.loads(_b64url_decode(jwt_parts[1]).decode("utf-8"))
            exp = data.get("exp")
            if isinstance(exp, (int, float)) and time.time() >= float(exp):
                return None
        else:
            return None

        sub = data.get("sub")
        if isinstance(sub, str) and _is_valid_uuid(sub.strip()):
            return sub.strip()
    except Exception:
        return None

    return None


def get_optional_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str | None:
    """Return authenticated user_id if present; raise 401 if a malformed Authorization header was sent."""
    if authorization is None or not authorization.strip():
        return None
    user_id = extract_user_id_from_authorization(authorization)
    if not user_id:
        raise AppError(
            status_code=401,
            code="UNAUTHORIZED",
            message="Bearer token không hợp lệ hoặc đã hết hạn.",
            details={},
        )
    return user_id


def get_required_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """Require a valid Bearer token; raise 401 UNAUTHORIZED otherwise."""
    user_id = extract_user_id_from_authorization(authorization)
    if not user_id:
        raise AppError(
            status_code=401,
            code="UNAUTHORIZED",
            message="Cần xác thực Bearer token hợp lệ để truy cập tài nguyên người dùng.",
            details={},
        )
    return user_id


def get_required_admin_id(
    user_id: str = Depends(get_required_user_id),
    repo: CatalogRepository = Depends(get_catalog_repo),
) -> str:
    """Verify server-side `public.profiles.role == 'admin'` (`FR-09a`, `NFR-04`, `SEC-03`).

    Never trusts client-supplied `role` claims or request fields.
    """
    role = repo.get_profile_role(user_id)
    if role != "admin":
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Tài khoản hiện tại không có quyền Quản trị viên (Admin).",
            details={},
        )
    return user_id
