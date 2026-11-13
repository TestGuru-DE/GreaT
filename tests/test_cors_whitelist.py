# REQ-EPIC18-PRE: CORS-Whitelist Tests
# ADR-015: Security Pre-Tasks fuer EPIC-18 (Multi-User)
# OWASP: A05 Security Misconfiguration
import os
import importlib
import pytest


def _reload_config():
    """Helper: reload config module to pick up env changes.

    REQ-1300: Verwendet importlib.reload() statt sys.modules zu loeschen,
    damit andere app.*-Module (z.B. rate_limiter, database) nicht
    aus dem Cache geworfen werden und ihre Referenzen behalten.
    """
    import app.config
    importlib.reload(app.config)


def test_cors_origins_default():
    """Default CORS_ORIGINS contains localhost:5173 and localhost:8000."""
    os.environ.pop("CORS_ORIGINS", None)
    _reload_config()
    from app.config import CORS_ORIGINS
    assert "http://localhost:5173" in CORS_ORIGINS
    assert "http://localhost:8000" in CORS_ORIGINS


def test_cors_origins_custom():
    """CORS_ORIGINS can be overridden via environment variable."""
    os.environ["CORS_ORIGINS"] = "http://example.com,http://other.example.com:3000"
    _reload_config()
    from app.config import CORS_ORIGINS
    assert "http://example.com" in CORS_ORIGINS
    assert "http://other.example.com:3000" in CORS_ORIGINS
    assert "http://localhost:5173" not in CORS_ORIGINS
    # Cleanup
    os.environ.pop("CORS_ORIGINS", None)
    _reload_config()


def test_cors_middleware_added():
    """CORSMiddleware is added to the FastAPI app."""
    from app.main import app
    middleware_names = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_names


def test_cors_middleware_options_method():
    """OPTIONS requests are allowed by CORS middleware (preflight)."""
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    # Preflight request - CORS middleware adds headers even on 405 responses
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    # CORS headers should be present (middleware handles preflight)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"