# REQ-EPIC18-PRE: JWT-Config Tests
# ADR-015: Security Pre-Tasks fuer EPIC-18 (Multi-User)
# OWASP: A02 Cryptographic Failures
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


def test_jwt_secret_key_exists():
    """JWT_SECRET_KEY is configured and has minimum length."""
    _reload_config()
    from app.config import JWT_SECRET_KEY
    assert JWT_SECRET_KEY is not None
    assert len(JWT_SECRET_KEY) > 32  # Mindestens 32 Zeichen


def test_jwt_refresh_secret_key_different():
    """JWT_REFRESH_SECRET_KEY is different from JWT_SECRET_KEY."""
    _reload_config()
    from app.config import JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY
    assert JWT_REFRESH_SECRET_KEY != JWT_SECRET_KEY


def test_jwt_algorithm_default():
    """JWT_ALGORITHM defaults to HS256."""
    _reload_config()
    from app.config import JWT_ALGORITHM
    assert JWT_ALGORITHM == "HS256"


def test_jwt_access_token_expire_default():
    """JWT_ACCESS_TOKEN_EXPIRE_MINUTES defaults to 15."""
    _reload_config()
    from app.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    assert JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15


def test_jwt_refresh_token_expire_default():
    """JWT_REFRESH_TOKEN_EXPIRE_DAYS defaults to 7."""
    _reload_config()
    from app.config import JWT_REFRESH_TOKEN_EXPIRE_DAYS
    assert JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7


def test_jwt_secret_from_env():
    """JWT_SECRET_KEY can be overridden via environment variable."""
    os.environ["JWT_SECRET_KEY"] = "my-custom-secret-key-for-testing-1234567890"
    _reload_config()
    from app.config import JWT_SECRET_KEY
    assert JWT_SECRET_KEY == "my-custom-secret-key-for-testing-1234567890"
    # Cleanup
    os.environ.pop("JWT_SECRET_KEY", None)
    _reload_config()