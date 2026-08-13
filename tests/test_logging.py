"""REQ-4009: Strukturiertes Logging."""
import logging
import os
import structlog
import pytest
from app.logging_config import setup_logging, get_logger
from app.config import LOG_LEVEL, LOG_FORMAT


def test_setup_logging_runs_without_error():
    """setup_logging() soll fehlerlos laufen."""
    setup_logging()  # Darf nicht werfen


def test_get_logger_returns_logger():
    """get_logger() soll einen Logger zurückgeben."""
    log = get_logger("test.logging")
    assert log is not None


def test_log_level_from_config():
    """LOG_LEVEL soll ein gültiger Logging-Level sein."""
    assert LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def test_log_format_from_config():
    """LOG_FORMAT soll 'text' oder 'json' sein."""
    assert LOG_FORMAT in ("text", "json")


def test_logger_info_works(caplog):
    """Logger.info() soll funktionieren."""
    setup_logging()
    with caplog.at_level(logging.INFO):
        logger = logging.getLogger("test.req4009")
        logger.info("test message")
    # Kein Fehler = Test bestanden


def test_logger_error_works(caplog):
    """Logger.error() soll funktionieren."""
    setup_logging()
    with caplog.at_level(logging.ERROR):
        logger = logging.getLogger("test.req4009")
        logger.error("test error")
    # Kein Fehler = Test bestanden


def test_logging_config_is_configured(caplog):
    """Nach setup_logging() soll Root-Logger konfiguriert sein."""
    setup_logging()
    root = logging.getLogger()
    assert len(root.handlers) > 0
