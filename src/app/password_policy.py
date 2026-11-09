"""Passwort-Policy fuer Selbst- und Admin-Passwortwechsel.

REQ-4028 AK-4: Mindestlaenge 12 Zeichen (serverseitig).
REQ-4028 AK-5 / REQ-4027 AK-14: Ablehnung bekannter Standardpasswoerter
  (nach Trim, ohne Beruecksichtigung der Gross-/Kleinschreibung).
REQ-4028 AK-9 / REQ-4027 AK-12: Fehler tragen nur einen Code, nie Passwort oder Laenge.
"""
from .bootstrap import DEFAULT_ADMIN_PASSWORD, LEGACY_DEFAULT_ADMIN_PASSWORD

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128

# REQ-4028 AK-5 Startliste (Projektinhaber bestaetigt; Erweiterung nur per Entscheidung).
KNOWN_DEFAULT_PASSWORDS = (
    DEFAULT_ADMIN_PASSWORD,
    LEGACY_DEFAULT_ADMIN_PASSWORD,
    "admin",
    "password",
)

# Stabile Fehlercodes (Frontend-Vertrag)
ERROR_CURRENT_PASSWORD_INVALID = "current_password_invalid"
ERROR_PASSWORD_IS_DEFAULT = "password_is_default"
ERROR_PASSWORD_TOO_SHORT = "password_too_short"
ERROR_PASSWORD_TOO_LONG = "password_too_long"


class PasswordError(Exception):
    """Fachlicher Fehler beim Passwortwechsel. Traegt nur einen stabilen Code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def is_known_default_password(password: str) -> bool:
    """True, wenn das Passwort nach Trim/casefold einem bekannten Standardpasswort entspricht."""
    normalized = password.strip().casefold()
    return any(normalized == known.strip().casefold() for known in KNOWN_DEFAULT_PASSWORDS)


def validate_new_password(password: str) -> None:
    """Prueft ein neues Passwort gegen die Policy. Wirft PasswordError mit Code."""
    if is_known_default_password(password):
        raise PasswordError(ERROR_PASSWORD_IS_DEFAULT)
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        raise PasswordError(ERROR_PASSWORD_TOO_SHORT)
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordError(ERROR_PASSWORD_TOO_LONG)
