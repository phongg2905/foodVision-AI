"""Standard API error codes and exception handlers (docs/03-api/api-conventions.md)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Canonical error code taxonomy across FoodVision AI endpoints."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_IMAGE = "INVALID_IMAGE"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    UNSUPPORTED_IMAGE_TYPE = "UNSUPPORTED_IMAGE_TYPE"
    INVALID_INGREDIENTS = "INVALID_INGREDIENTS"
    INGREDIENT_IN_USE = "INGREDIENT_IN_USE"
    RECIPE_NOT_PUBLISHABLE = "RECIPE_NOT_PUBLISHABLE"
    MODEL_IMMUTABLE = "MODEL_IMMUTABLE"
    INVALID_LABEL_MAPPING = "INVALID_LABEL_MAPPING"
    MODEL_NOT_ACTIVATABLE = "MODEL_NOT_ACTIVATABLE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    SCAN_NOT_OWNED = "SCAN_NOT_OWNED"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    MODEL_NOT_READY = "MODEL_NOT_READY"
    INFERENCE_TIMEOUT = "INFERENCE_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Domain/API exception conforming to FoodVision AI standard ErrorResponse envelope."""

    def __init__(
        self,
        status_code: int,
        code: str | ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        if isinstance(code, ErrorCode):
            self.code: str | ErrorCode = code
        elif code in ErrorCode._value2member_map_:
            self.code = ErrorCode(code)
        else:
            self.code = str(code)
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


# THUẬT TOÁN: Trích xuất mã định danh truy vết yêu cầu (Request Correlation ID)
# - Ưu tiên đọc từ `request.state.request_id` do middleware gắn hoặc header `X-Request-Id`.
def get_request_id(request: Request) -> str:
    return (
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-Id")
        or request.headers.get("X-Request-ID")
        or "req-local"
    )


# THUẬT TOÁN: Đăng ký bộ xử lý ngoại lệ chuẩn hóa theo khung ErrorResponse (`openapi.yaml`)
# - Mọi lỗi nghiệp vụ (`AppError`) và lỗi kiểm tra dữ liệu (`RequestValidationError`) đều trả về
#   cấu trúc `{code, message, details, request_id}` kèm header `X-Request-Id`.
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        req_id = get_request_id(request)
        headers = {"X-Request-Id": req_id, **exc.headers}
        code_str = exc.code.value if isinstance(exc.code, Enum) else str(exc.code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": code_str,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_request_id(request)
        return JSONResponse(
            status_code=422,
            content={
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": "Dữ liệu yêu cầu không hợp lệ.",
                "details": {"errors": exc.errors()},
                "request_id": req_id,
            },
            headers={"X-Request-Id": req_id},
        )
