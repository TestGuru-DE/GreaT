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
# B-25: Persistierte JWT-Secrets – bei SQLite ohne Env-Var wird eine
# jwt_secrets.json neben der DB-Datei erzeugt, damit Neustarts nicht
# alle bestehenden Tokens invalidieren.
import json as _json
import secrets
import logging as _logging_config

_jwt_log = _logging_config.getLogger("great.config")

# Pfad fuer persistente JWT-Secrets (B-25)
if getattr(sys, "frozen", False):
    _jwt_secrets_dir = Path.home() / ".great"
else:
    _db_url = os.getenv("DATABASE_URL", "sqlite:///./great.db")
    if _db_url.startswith("sqlite:///"):
        _db_path = Path(_db_url.replace("sqlite:///", ""))
        _jwt_secrets_dir = _db_path.parent if _db_path.is_absolute() else Path.cwd()
    else:
        _jwt_secrets_dir = Path.cwd()

_jwt_secrets_dir.mkdir(parents=True, exist_ok=True)
_jwt_secrets_file = _jwt_secrets_dir / "jwt_secrets.json"


def _get_or_create_jwt_secrets() -> tuple[str, str]:
    access_secret = os.getenv("JWT_SECRET_KEY")
    refresh_secret = os.getenv("JWT_REFRESH_SECRET_KEY")
    if access_secret and refresh_secret:
        return access_secret, refresh_secret
    if _jwt_secrets_file.exists():
        try:
            with open(_jwt_secrets_file, "r", encoding="utf-8") as f:
                stored = _json.load(f)
            if not access_secret:
                access_secret = stored.get("access", "")
            if not refresh_secret:
                refresh_secret = stored.get("refresh", "")
            if access_secret and refresh_secret:
                return access_secret, refresh_secret
        except Exception:
            pass
    if not access_secret:
        access_secret = secrets.token_urlsafe(64)
    if not refresh_secret:
        refresh_secret = secrets.token_urlsafe(64)
    try:
        _json.dump({"access": access_secret, "refresh": refresh_secret},
                    _jwt_secrets_file.open("w", encoding="utf-8"))
        _jwt_secrets_file.chmod(0o600)
    except OSError:
        pass
    return access_secret, refresh_secret


JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY = _get_or_create_jwt_secrets()
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# B-08: X-Forwarded-For nur vertrauenswürdiger Proxy
GREAT_TRUST_PROXY_HEADERS: bool = os.getenv("GREAT_TRUST_PROXY_HEADERS", "false").lower() == "true"

# B-26: Cookie Secure-Flag konfigurierbar (Default: False fuer HTTP-Development)
GREAT_COOKIE_SECURE: bool = os.getenv("GREAT_COOKIE_SECURE", "false").lower() == "true"

# Warnung wenn Default-Secrets verwendet werden (nicht in Production!)
if not os.getenv("JWT_SECRET_KEY"):
    _jwt_log.warning("JWT_SECRET_KEY not set! Using persisted or random default. Set this in production via environment variable!")
if not os.getenv("JWT_REFRESH_SECRET_KEY"):
    _jwt_log.warning("JWT_REFRESH_SECRET_KEY not set! Using persisted or random default. Set this in production via environment variable!")


# ============================================================================
# Kombinatorik-Optimierung – Generierungslimits
# ============================================================================

GREAT_MAX_COMBINATIONS_DEFAULT: int = 100000


def get_max_combinations() -> int:
    """Liefert die Obergrenze fuer kartesische Produktgroessen.

    Schuetzt vor kombinatorischer Explosion bei 'all'-Strategie und
    t_wise mit t >= Anzahl Kategorien. Nicht-positive Werte fallen
    auf den Default (100000) zurueck.
    """
    raw = os.getenv("GREAT_MAX_COMBINATIONS", str(GREAT_MAX_COMBINATIONS_DEFAULT))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return GREAT_MAX_COMBINATIONS_DEFAULT
    return value if value > 0 else GREAT_MAX_COMBINATIONS_DEFAULT


# Maximale Backup-Dateigroesse in MB (Default 50 MB)
GREAT_MAX_BACKUP_MB: int = int(os.getenv("GREAT_MAX_BACKUP_MB", "50"))


GREAT_GENERATION_TIMEOUT_S_DEFAULT: int = 60


def get_generation_timeout() -> float:
    """Liefert das Timeout in Sekunden fuer Generierungsalgorithmen.

    Nicht-positive Werte fallen auf den Default (60s) zurueck.
    Unterstuetzt auch Dezimalwerte (z. B. 0.1 fuer Tests).
    """
    raw = os.getenv("GREAT_GENERATION_TIMEOUT_S", str(GREAT_GENERATION_TIMEOUT_S_DEFAULT))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return float(GREAT_GENERATION_TIMEOUT_S_DEFAULT)
    return value if value > 0 else float(GREAT_GENERATION_TIMEOUT_S_DEFAULT)


# ============================================================================
# REQ-6012: API-Token Rate-Limit (Standard 600/Minute, konfigurierbar)
# ============================================================================

GREAT_TOKEN_RATE_LIMIT: int = int(os.getenv("GREAT_TOKEN_RATE_LIMIT", "600"))
