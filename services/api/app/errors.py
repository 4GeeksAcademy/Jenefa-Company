"""Platform-wide API error contract and sanitizing exception handlers.

Client payloads never include stack traces, filesystem paths, connection
strings, environment values, or authorization material.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

ERROR_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}

GENERIC_INTERNAL = "The request could not be completed. Please try again."

_LEAK_MARKERS = (
    "traceback",
    "/users/",
    "/home/",
    "appdata",
    "secret_key",
    "postgresql://",
    "mysql://",
    "mongodb://",
    "redis://",
    "sqlite://",
    "file://",
    ".py\"",
    "sqlalchemy",
    "pydantic",
    "starlette",
    "authorization",
    "bearer ",
)


def error_payload(status_code: int, detail: Any) -> dict[str, Any]:
    """Build the canonical `{error, detail}` JSON body."""
    title = ERROR_TITLES.get(status_code, "Error")
    return {"error": title, "detail": sanitize_detail(detail, status_code)}


def json_error(
    status_code: int,
    detail: Any,
    *,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_payload(status_code, detail),
        headers=headers,
    )


def sanitize_detail(detail: Any, status_code: int) -> Any:
    """Strip infrastructure metadata from a response detail value."""
    if status_code >= 500:
        return GENERIC_INTERNAL
    if isinstance(detail, str):
        return _scrub_text(detail, fallback=ERROR_TITLES.get(status_code, "Error"))
    if isinstance(detail, list):
        return [_sanitize_validation_item(item) for item in detail]
    return ERROR_TITLES.get(status_code, "Request failed.")


def _sanitize_validation_item(item: Any) -> dict[str, Any]:
    """Keep loc/msg for field mapping; drop submitted `input` (may contain secrets)."""
    if not isinstance(item, dict):
        return {"loc": ["body"], "msg": "Invalid value"}
    loc = item.get("loc")
    safe_loc: list[str | int] = []
    if isinstance(loc, (list, tuple)):
        safe_loc = [part for part in loc if isinstance(part, (str, int))]
    msg = item.get("msg")
    safe_msg = _scrub_text(str(msg), fallback="Invalid value") if msg else "Invalid value"
    return {"loc": safe_loc or ["body"], "msg": safe_msg}


def _scrub_text(text: str, *, fallback: str) -> str:
    if _looks_like_leak(text):
        return fallback
    cleaned = _SECRET_ASSIGNMENT.sub(r"\1=[redacted]", text)
    cleaned = _URI_RE.sub("[redacted-uri]", cleaned)
    return cleaned


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(secret|api[_-]?key|token|password|authorization)\s*[=:]\s*\S+"
)
_URI_RE = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb|redis|amqp|file)://\S+"
)


def _looks_like_leak(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _LEAK_MARKERS)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach sanitizing handlers. More specific types are registered first."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return json_error(422, exc.errors())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return json_error(exc.status_code, exc.detail, headers=dict(exc.headers or {}))

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return json_error(exc.status_code, exc.detail, headers=dict(exc.headers or {}))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API exception: %s", type(exc).__name__)
        return json_error(500, GENERIC_INTERNAL)
