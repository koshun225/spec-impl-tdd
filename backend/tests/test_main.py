"""Tests for FastAPI application setup: CORS, lifespan, and logging middleware.

Contract under test (T009):
- FastAPI application instance importable as `from app.main import app`
- CORS middleware configured for http://localhost:3000
- Lifespan event calls init_db()/setup_logging() on startup, close_db() on shutdown
- RequestIdMiddleware applied (X-Request-ID header on responses)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI

from app.main import app  # noqa: I001

# ---------------------------------------------------------------------------
# 1. App is a FastAPI instance
# ---------------------------------------------------------------------------


class TestAppInstance:
    """Verify that the exported `app` object is a proper FastAPI instance."""

    def test_app_is_fastapi_instance(self) -> None:
        assert isinstance(app, FastAPI)

    def test_app_is_importable(self) -> None:
        """The app object should be importable from app.main."""
        from app.main import app as imported_app

        assert imported_app is app


# ---------------------------------------------------------------------------
# 2. CORS middleware configuration
# ---------------------------------------------------------------------------


class TestCORSMiddleware:
    """Verify CORS is configured for http://localhost:3000."""

    @pytest.fixture
    def _mock_lifespan_deps(self):
        """Mock the lifespan dependencies so the app can start."""
        with (
            patch("app.main.init_db", new_callable=AsyncMock) as mock_init,
            patch("app.main.close_db", new_callable=AsyncMock) as mock_close,
            patch("app.main.setup_logging") as mock_logging,
        ):
            yield mock_init, mock_close, mock_logging

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_cors_allows_localhost_3000(self) -> None:
        """A preflight request from http://localhost:3000 should succeed."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_cors_allows_credentials(self) -> None:
        """CORS should allow credentials."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_cors_allows_all_methods(self) -> None:
        """CORS should allow all HTTP methods."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "DELETE",
                },
            )
        # When allow_methods=["*"], FastAPI/Starlette reflects the
        # requested method back in the allowed methods header.
        allowed = response.headers.get("access-control-allow-methods", "")
        assert "DELETE" in allowed

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_cors_allows_all_headers(self) -> None:
        """CORS should allow all request headers."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "X-Custom-Header",
                },
            )
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert "x-custom-header" in allowed_headers.lower()

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_cors_rejects_unknown_origin(self) -> None:
        """A preflight from an unknown origin should not get allow-origin."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://evil.example.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert (
            response.headers.get("access-control-allow-origin")
            != "http://evil.example.com"
        )


# ---------------------------------------------------------------------------
# 3. Lifespan events (startup / shutdown)
# ---------------------------------------------------------------------------


class TestLifespan:
    """Verify database init/close and logging setup via lifespan."""

    async def test_init_db_called_on_startup(self) -> None:
        """init_db() should be called when the app starts."""
        from app.main import lifespan

        with (
            patch("app.main.init_db", new_callable=AsyncMock) as mock_init,
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_logging"),
        ):
            async with lifespan(app):
                mock_init.assert_awaited_once()

    async def test_setup_logging_called_on_startup(self) -> None:
        """setup_logging() should be called when the app starts."""
        from app.main import lifespan

        with (
            patch("app.main.init_db", new_callable=AsyncMock),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_logging") as mock_logging,
        ):
            async with lifespan(app):
                mock_logging.assert_called_once()

    async def test_close_db_called_on_shutdown(self) -> None:
        """close_db() should be called when the app shuts down."""
        from app.main import lifespan

        with (
            patch("app.main.init_db", new_callable=AsyncMock),
            patch("app.main.close_db", new_callable=AsyncMock) as mock_close,
            patch("app.main.setup_logging"),
        ):
            async with lifespan(app):
                pass
            mock_close.assert_awaited_once()


# ---------------------------------------------------------------------------
# 4. RequestIdMiddleware (X-Request-ID header)
# ---------------------------------------------------------------------------


class TestRequestIdMiddleware:
    """Verify RequestIdMiddleware is applied to the app."""

    @pytest.fixture
    def _mock_lifespan_deps(self):
        """Mock the lifespan dependencies so the app can start."""
        with (
            patch("app.main.init_db", new_callable=AsyncMock),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_logging"),
        ):
            yield

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_response_has_x_request_id_header(self) -> None:
        """Every response should include an X-Request-ID header."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.get("/")
        assert "x-request-id" in response.headers

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_x_request_id_is_uuid4_format(self) -> None:
        """X-Request-ID should be a valid UUID4 string."""
        import uuid

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.get("/")
        request_id = response.headers.get("x-request-id", "")
        # Should not raise
        parsed = uuid.UUID(request_id, version=4)
        assert str(parsed) == request_id

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_x_request_id_unique_per_request(self) -> None:
        """Each request should get a different X-Request-ID."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            resp1 = await client.get("/")
            resp2 = await client.get("/")
        id1 = resp1.headers.get("x-request-id")
        id2 = resp2.headers.get("x-request-id")
        assert id1 != id2


# ---------------------------------------------------------------------------
# 5. Basic app responsiveness
# ---------------------------------------------------------------------------


class TestAppResponds:
    """Verify the app responds to basic HTTP requests."""

    @pytest.fixture
    def _mock_lifespan_deps(self):
        """Mock the lifespan dependencies so the app can start."""
        with (
            patch("app.main.init_db", new_callable=AsyncMock),
            patch("app.main.close_db", new_callable=AsyncMock),
            patch("app.main.setup_logging"),
        ):
            yield

    @pytest.mark.usefixtures("_mock_lifespan_deps")
    async def test_app_responds_to_get(self) -> None:
        """The app should respond to a GET request (even if 404, it's alive)."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.get("/")
        # App is alive; a 404 or 200 is fine — just not a connection error
        assert response.status_code in (200, 404, 405)
