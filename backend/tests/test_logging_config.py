"""Tests for structured logging configuration and request tracing middleware.

Verifies the contract specifications from plan.md and constitution:
- structlog is configured for JSON structured output
- Request ID middleware generates unique request IDs (UUID4)
- Request ID is added to response headers as X-Request-ID
- Logging context includes request_id for request tracing
- Middleware works with FastAPI/Starlette (ASGI)
"""

from __future__ import annotations

import json
import uuid
from io import StringIO
from unittest.mock import patch

import pytest
import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.logging_config import RequestIdMiddleware, setup_logging


# ---------------------------------------------------------------------------
# setup_logging Tests
# ---------------------------------------------------------------------------


class TestSetupLogging:
    """Test structlog configuration via setup_logging."""

    def setup_method(self) -> None:
        """Reset structlog configuration before each test."""
        structlog.reset_defaults()

    def teardown_method(self) -> None:
        """Reset structlog configuration after each test."""
        structlog.reset_defaults()

    def test_setup_logging_does_not_raise(self) -> None:
        """setup_logging should complete without errors."""
        setup_logging()

    def test_setup_logging_configures_structlog(self) -> None:
        """After setup_logging, structlog should be configured (not defaults)."""
        setup_logging()
        # Verify structlog has been configured by checking we can get a logger
        # and that it produces output without error
        logger = structlog.get_logger()
        assert logger is not None

    def test_structlog_produces_json_output(self) -> None:
        """After setup_logging, log output should be valid JSON."""
        setup_logging()
        output = StringIO()

        # Configure a logger that writes to our StringIO
        logger = structlog.get_logger()

        # We need to capture the output; use structlog's PrintLogger or
        # redirect. The implementation should use JSONRenderer.
        # We test by checking the configured processors include JSON rendering.
        config = structlog.get_config()
        processors = config.get("processors", [])

        # There should be a JSON renderer in the processor chain
        processor_names = [
            type(p).__name__ if not callable(p) or hasattr(p, "__name__") is False
            else getattr(p, "__name__", type(p).__name__)
            for p in processors
        ]
        processor_classes = [type(p).__name__ for p in processors]

        json_renderer_found = any(
            "JSON" in name or "json" in name
            for name in processor_classes
        )
        assert json_renderer_found, (
            f"Expected a JSON renderer in structlog processors. "
            f"Found processor types: {processor_classes}"
        )

    def test_structlog_processors_include_timestamp(self) -> None:
        """structlog configuration should include a timestamp processor."""
        setup_logging()
        config = structlog.get_config()
        processors = config.get("processors", [])
        processor_classes = [type(p).__name__ for p in processors]

        # Look for timestamper or similar
        timestamp_found = any(
            "timestamper" in name.lower() or "timestamp" in name.lower()
            for name in processor_classes
        )
        assert timestamp_found, (
            f"Expected a timestamp processor in structlog processors. "
            f"Found processor types: {processor_classes}"
        )

    def test_structlog_processors_include_log_level(self) -> None:
        """structlog configuration should include a log level processor."""
        setup_logging()
        config = structlog.get_config()
        processors = config.get("processors", [])
        processor_classes = [type(p).__name__ for p in processors]
        processor_func_names = [
            getattr(p, "__name__", "") for p in processors
        ]

        # Look for add_log_level or similar
        log_level_found = any(
            "log_level" in name.lower() or "loglevel" in name.lower()
            for name in processor_classes + processor_func_names
        )
        assert log_level_found, (
            f"Expected a log level processor in structlog processors. "
            f"Found processor types: {processor_classes}, "
            f"function names: {processor_func_names}"
        )

    def test_setup_logging_is_idempotent(self) -> None:
        """Calling setup_logging multiple times should not raise errors."""
        setup_logging()
        setup_logging()
        # Should still work after double configuration
        logger = structlog.get_logger()
        assert logger is not None


# ---------------------------------------------------------------------------
# RequestIdMiddleware Tests
# ---------------------------------------------------------------------------


def _make_test_app(
    log_request_id: bool = False,
) -> Starlette:
    """Create a minimal Starlette app wrapped in RequestIdMiddleware.

    Args:
        log_request_id: If True, the endpoint will log a message
            to verify request_id appears in log context.
    """

    async def homepage(request: Request) -> PlainTextResponse:
        if log_request_id:
            logger = structlog.get_logger()
            await logger.ainfo("test log message")
        return PlainTextResponse("OK")

    async def echo_header(request: Request) -> PlainTextResponse:
        """Echo back the X-Request-ID from the request if present."""
        req_id = request.headers.get("x-request-id", "none")
        return PlainTextResponse(f"received: {req_id}")

    app = Starlette(
        routes=[
            Route("/", homepage),
            Route("/echo", echo_header),
        ],
    )
    app.add_middleware(RequestIdMiddleware)
    return app


class TestRequestIdMiddleware:
    """Test the RequestIdMiddleware ASGI middleware."""

    def setup_method(self) -> None:
        """Reset structlog and configure logging before each test."""
        structlog.reset_defaults()
        setup_logging()

    def teardown_method(self) -> None:
        """Reset structlog after each test."""
        structlog.reset_defaults()

    def test_middleware_adds_x_request_id_header(self) -> None:
        """Response should include an X-Request-ID header."""
        app = _make_test_app()
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_request_id_is_valid_uuid4(self) -> None:
        """The X-Request-ID header value should be a valid UUID4."""
        app = _make_test_app()
        client = TestClient(app)
        response = client.get("/")

        request_id = response.headers["x-request-id"]
        # Should not raise ValueError if it is a valid UUID
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    def test_each_request_gets_unique_id(self) -> None:
        """Each request should receive a different request ID."""
        app = _make_test_app()
        client = TestClient(app)

        response1 = client.get("/")
        response2 = client.get("/")

        id1 = response1.headers["x-request-id"]
        id2 = response2.headers["x-request-id"]
        assert id1 != id2, "Each request should get a unique request_id"

    def test_multiple_requests_all_have_unique_ids(self) -> None:
        """A batch of requests should all have distinct request IDs."""
        app = _make_test_app()
        client = TestClient(app)

        ids: set[str] = set()
        num_requests = 10
        for _ in range(num_requests):
            response = client.get("/")
            ids.add(response.headers["x-request-id"])

        assert len(ids) == num_requests, (
            f"Expected {num_requests} unique request IDs, got {len(ids)}"
        )

    def test_request_id_in_structlog_context(self) -> None:
        """Log messages during a request should include request_id in context."""
        app = _make_test_app(log_request_id=True)
        client = TestClient(app)

        log_output: list[dict] = []

        # Capture structlog output
        original_processors = structlog.get_config().get("processors", [])

        def capture_processor(
            logger: object, method_name: str, event_dict: dict
        ) -> dict:
            log_output.append(event_dict.copy())
            return event_dict

        # Reconfigure with our capture processor inserted before the final renderer
        setup_logging()
        config = structlog.get_config()
        processors = list(config.get("processors", []))
        # Insert capture before the last processor (JSON renderer)
        processors.insert(-1, capture_processor)
        structlog.configure(processors=processors)

        response = client.get("/")

        assert response.status_code == 200

        # Check that at least one log entry has request_id
        entries_with_request_id = [
            entry for entry in log_output if "request_id" in entry
        ]
        assert len(entries_with_request_id) > 0, (
            f"Expected at least one log entry with 'request_id'. "
            f"Log entries: {log_output}"
        )

    def test_request_id_in_log_matches_response_header(self) -> None:
        """The request_id in log context should match the X-Request-ID response header."""
        app = _make_test_app(log_request_id=True)
        client = TestClient(app)

        log_output: list[dict] = []

        def capture_processor(
            logger: object, method_name: str, event_dict: dict
        ) -> dict:
            log_output.append(event_dict.copy())
            return event_dict

        setup_logging()
        config = structlog.get_config()
        processors = list(config.get("processors", []))
        processors.insert(-1, capture_processor)
        structlog.configure(processors=processors)

        response = client.get("/")
        header_request_id = response.headers["x-request-id"]

        # Find log entries with request_id
        entries_with_request_id = [
            entry for entry in log_output if "request_id" in entry
        ]
        assert len(entries_with_request_id) > 0

        # The request_id in log should match the header
        log_request_id = entries_with_request_id[0]["request_id"]
        assert log_request_id == header_request_id, (
            f"Log request_id ({log_request_id}) should match "
            f"X-Request-ID header ({header_request_id})"
        )

    def test_middleware_does_not_break_response_body(self) -> None:
        """The middleware should not alter the response body."""
        app = _make_test_app()
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert response.text == "OK"

    def test_middleware_works_with_different_routes(self) -> None:
        """The middleware should add X-Request-ID to all routes."""
        app = _make_test_app()
        client = TestClient(app)

        response_home = client.get("/")
        response_echo = client.get("/echo")

        assert "x-request-id" in response_home.headers
        assert "x-request-id" in response_echo.headers

        # Both should have different IDs
        assert (
            response_home.headers["x-request-id"]
            != response_echo.headers["x-request-id"]
        )

    def test_middleware_works_with_post_requests(self) -> None:
        """The middleware should work with POST (and other) HTTP methods."""
        async def post_handler(request: Request) -> PlainTextResponse:
            return PlainTextResponse("created", status_code=201)

        app = Starlette(
            routes=[
                Route("/items", post_handler, methods=["POST"]),
            ],
        )
        app.add_middleware(RequestIdMiddleware)

        client = TestClient(app)
        response = client.post("/items")

        assert response.status_code == 201
        assert "x-request-id" in response.headers
        parsed = uuid.UUID(response.headers["x-request-id"])
        assert parsed.version == 4


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestLoggingIntegration:
    """Integration tests for logging configuration + middleware together."""

    def setup_method(self) -> None:
        """Reset structlog before each test."""
        structlog.reset_defaults()

    def teardown_method(self) -> None:
        """Reset structlog after each test."""
        structlog.reset_defaults()

    def test_setup_then_middleware_works_end_to_end(self) -> None:
        """Calling setup_logging then using the middleware should work together."""
        setup_logging()

        app = _make_test_app()
        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "x-request-id" in response.headers

        # Verify the request ID is a valid UUID4
        parsed = uuid.UUID(response.headers["x-request-id"])
        assert parsed.version == 4

    def test_concurrent_requests_have_isolated_context(self) -> None:
        """Different requests should not share request_id context.

        Each request's request_id should be unique and not leak between
        concurrent requests.
        """
        setup_logging()
        app = _make_test_app()
        client = TestClient(app)

        ids: list[str] = []
        for _ in range(5):
            response = client.get("/")
            ids.append(response.headers["x-request-id"])

        # All IDs should be unique
        assert len(set(ids)) == len(ids), (
            f"All request IDs should be unique. Got: {ids}"
        )
