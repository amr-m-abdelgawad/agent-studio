from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
    return error_response(exc.code, exc.message, exc.status_code)


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return error_response("http_error", str(exc.detail), exc.status_code)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    for err in exc.errors():
        loc = err.get("loc", ())
        if "password" in loc and err.get("type") in {"string_too_short", "value_error"}:
            return error_response(
                "password_too_short", "Password must be at least 12 characters", 422
            )
    return error_response("validation_error", "Invalid request", 422)
