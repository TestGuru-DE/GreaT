"""Zentrale Konfiguration via Umgebungsvariablen.

REQ-4007: GREAT_PORT Umgebungsvariable fuer portierbare Deployment-Konfiguration.
REQ-4009: Logging-Konfiguration via Umgebungsvariablen.
REQ-4018: Maximale Anzahl Testfaelle (Obergrenze) als konfigurierbares Setting.
REQ-5001: Datenbank-Pfad-Anpassung fuer PyInstaller-Portable-Modus.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # lädt .env falls vorhanden

GREAT_PORT: int = int(os.getenv("GREAT_PORT", "8000"))
GREAT_HOST: str = os.getenv("GREAT_HOST", "0.0.0.0")

# REQ-5001: Datenbank-Pfad fuer portable EXE
# Wenn als PyInstaller-EXE gefroren: DB im User-Home-Verzeichnis (.great/)
# Sonst: relative DB im Projektverzeichnis (wie bisher)
if getattr(sys, "frozen", False):
    _db_dir = Path.home() / ".great"
    _db_dir.mkdir(parents=True, exist_ok=True)
    DATABASE_URL: str = f"sqlite:///{_db_dir / 'great.db'}"
else:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./great.db")

# REQ-4009: Logging-Konfiguration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text")  # "text" oder "json"

# REQ-4018: Obergrenze fuer generierte Testfaelle (Default 1000).
# Anders als GREAT_PORT wird dieser Wert bei jedem Generierungs-Request frisch
# aus der Umgebung gelesen (siehe get_max_testcases()), damit eine Aenderung
# des Settings ohne Server-Neustart wirksam werden kann.
GREAT_MAX_TESTCASES_DEFAULT: int = 1000


def get_max_testcases() -> int:
    """Liefert die aktuell konfigurierte Obergrenze fuer generierte Testfaelle.

    Robust gegen fehlerhafte Konfiguration: nicht-numerische oder nicht-positive
    Werte fallen auf den Default (1000) zurueck, statt den Request stillschweigend
    mit einem unsinnigen Limit (z. B. 0 oder negativ) zu verarbeiten.
    """
    raw = os.getenv("GREAT_MAX_TESTCASES", str(GREAT_MAX_TESTCASES_DEFAULT))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return GREAT_MAX_TESTCASES_DEFAULT
    return value if value > 0 else GREAT_MAX_TESTCASES_DEFAULT


# ============================================================================
# EPIC-18 Security Pre-Tasks (Sprint 11 Vorbereitung)
# ============================================================================

# CORS-Whitelist (kommaseparierte Origins, Default: Vite Dev + Backend)
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
]

# JWT-Secrets (MUSS in Production ueber Env-Var gesetzt werden!)
# Wenn nicht gesetzt: zufaelliger Default mit Warnung (NUR fuer Development!)
import secrets
import logging as _logging_config

_jwt_log = _logging_config.getLogger("great.config")

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(64)
JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY") or secrets.token_urlsafe(64)
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Warnung wenn Default-Secrets verwendet werden (nicht in Production!)
if not os.getenv("JWT_SECRET_KEY"):
    _jwt_log.warning("JWT_SECRET_KEY not set! Using random default. Set this in production via environment variable!")
if not os.getenv("JWT_REFRESH_SECRET_KEY"):
    _jwt_log.warning("JWT_REFRESH_SECRET_KEY not set! Using random default. Set this in production via environment variable!")
