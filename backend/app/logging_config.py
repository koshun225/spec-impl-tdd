"""Structured logging configuration with request-ID middleware."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

def setup_logging() -> None:
    """Configure structlog globally with JSON output.

    Safe to call multiple times -- structlog.configure() is idempotent.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that assigns a unique request ID to every request.

    For each incoming request the middleware:
    1. Generates a UUID4 request ID.
    2. Binds it to the structlog context (``request_id``).
    3. Adds an ``X-Request-ID`` response header.
    4. Clears the structlog context after the request completes so that
       context does not leak between requests.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())

        # Clear any leftover context, then bind the new request_id
        clear_contextvars()
        bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_contextvars()
