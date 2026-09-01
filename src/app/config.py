"""Zentrale Konfiguration via Umgebungsvariablen.

REQ-4007: GREAT_PORT Umgebungsvariable fuer portierbare Deployment-Konfiguration.
REQ-4009: Logging-Konfiguration via Umgebungsvariablen.
REQ-4018: Maximale Anzahl Testfaelle (Obergrenze) als konfigurierbares Setting.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # lädt .env falls vorhanden

GREAT_PORT: int = int(os.getenv("GREAT_PORT", "8000"))
GREAT_HOST: str = os.getenv("GREAT_HOST", "0.0.0.0")
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
