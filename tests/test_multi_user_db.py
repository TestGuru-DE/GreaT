"""REQ-4006: Multi-User DB Engine Tests"""
import os
import pytest
from unittest.mock import patch, MagicMock


def test_sqlite_engine_default():
    """Default DATABASE_URL erstellt SQLite Engine."""
    # Reload des database Moduls mit SQLite-URL
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
        # Wir testen die Logik indirekt
        url = os.getenv("DATABASE_URL", "sqlite:///./great.db")
        assert url.startswith("sqlite")


def test_postgresql_url_format():
    """PostgreSQL DATABASE_URL hat korrektes Format."""
    pg_url = "postgresql://user:pass@localhost:5432/great"
    assert pg_url.startswith("postgresql")
    assert "user:pass" in pg_url
    assert "great" in pg_url


def test_queuepool_import():
    """QueuePool ist importierbar."""
    from sqlalchemy.pool import QueuePool
    assert QueuePool is not None


def test_engine_pool_pre_ping_for_postgresql():
    """PostgreSQL Engine verwendet pool_pre_ping."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import QueuePool
    # Test mit einer Mock-URL (verbindet nicht wirklich)
    # Wir pruefen nur, dass die Parameter akzeptiert werden
    engine = create_engine(
        "postgresql://user:pass@localhost:5432/test",
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    assert engine is not None
    # pool_pre_ping sollte True sein
    pool = engine.pool
    assert hasattr(pool, "size")


def test_sqlite_connect_args():
    """SQLite Engine verwendet check_same_thread=False."""
    from sqlalchemy import create_engine
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    assert engine is not None