"""Strukturiertes Logging via structlog. REQ-4009."""
import logging
import re
import structlog
from app.config import LOG_LEVEL, LOG_FORMAT


def setup_logging() -> None:
    """Logging initialisieren."""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)
    install_secret_redaction()


# BUG N-06: Geheimnisse in Query-Strings (z. B. ?password=...) nie ins Zugriffslog schreiben.
_SECRET_QUERY = re.compile(r"(?i)([?&](?:password|passwort|pwd|token|secret)=)[^&\s\"]*")


def redact_secrets(text: str) -> str:
    """Ersetzt Werte geheimer Query-Parameter durch ***."""
    return _SECRET_QUERY.sub(r"\1***", text)


class RedactSecretsFilter(logging.Filter):
    """Schwaerzt geheime Query-Parameter in Log-Eintraegen (uvicorn.access u. a.)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple) and record.args:
            record.args = tuple(redact_secrets(a) if isinstance(a, str) else a for a in record.args)
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        return True


def install_secret_redaction() -> None:
    """Filter an die Zugriffs- und Fehler-Logger von uvicorn haengen (idempotent)."""
    for name in ("uvicorn.access", "uvicorn.error", "uvicorn"):
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactSecretsFilter) for f in logger.filters):
            logger.addFilter(RedactSecretsFilter())


def get_logger(name: str = __name__):
    """Strukturierten Logger abrufen."""
    return structlog.get_logger(name)
