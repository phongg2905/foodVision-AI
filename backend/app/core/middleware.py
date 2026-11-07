"""Request ID correlation and structured JSON observability middleware (NFR-08)."""

from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("foodvision.api")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches X-Request-Id and logs structured JSON without exposing secrets."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = req_id
        start_time = time.perf_counter()

        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        response.headers["X-Request-Id"] = req_id

        log_payload = {
            "event": "http_request",
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        logger.info(json.dumps(log_payload, ensure_ascii=False))
        return response

