"""Passwort-Policy fuer Selbst- und Admin-Passwortwechsel.

REQ-4028 AK-4: Mindestlaenge 12 Zeichen (serverseitig).
REQ-4028 AK-5 / REQ-4027 AK-14: Ablehnung bekannter Standardpasswoerter
  (nach Trim, ohne Beruecksichtigung der Gross-/Kleinschreibung).
REQ-4028 AK-9 / REQ-4027 AK-12: Fehler tragen nur einen Code, nie Passwort oder Laenge.
B-23: Ablehnung gebräuchlicher Passwörter und Mindestzeichen-Vielfalt.
"""
import pathlib

from .bootstrap import DEFAULT_ADMIN_PASSWORD, LEGACY_DEFAULT_ADMIN_PASSWORD

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128

# B-23: Mindestanzahl verschiedener Zeichen
MIN_PASSWORD_VARIETY = 4

# REQ-4028 AK-5 Startliste (Projektinhaber bestaetigt; Erweiterung nur per Entscheidung).
# Eintraege < 12 Zeichen (MIN_PASSWORD_LENGTH) sind wirkungslos, da validate_new_password
# sie vorher aufgrund der Mindestlaenge ablehnt. Sie wurden daher entfernt.
# DEFAULT_ADMIN_PASSWORD bleibt explizit: es ist das Default-Admin-Passwort und muss immer
# blockiert werden, solange default_password_active=True.
KNOWN_DEFAULT_PASSWORDS = (
    DEFAULT_ADMIN_PASSWORD,
)

# Stabile Fehlercodes (Frontend-Vertrag)
ERROR_CURRENT_PASSWORD_INVALID = "current_password_invalid"
ERROR_PASSWORD_IS_DEFAULT = "password_is_default"
ERROR_PASSWORD_TOO_SHORT = "password_too_short"
ERROR_PASSWORD_TOO_LONG = "password_too_long"

# B-23: Neue Fehlercodes
ERROR_PASSWORD_TOO_COMMON = "password_too_common"
ERROR_PASSWORD_LOW_VARIETY = "password_low_variety"


class PasswordError(Exception):
    """Fachlicher Fehler beim Passwortwechsel. Traegt nur einen stabilen Code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------------------
# B-23: Common-passwords check
# ---------------------------------------------------------------------------

_COMMON_PASSWORDS: set[str] | None = None
_COMMON_PASSWORDS_PATH = pathlib.Path(__file__).parent / "data" / "common_passwords.txt"


def _load_common_passwords() -> set[str]:
    global _COMMON_PASSWORDS
    if _COMMON_PASSWORDS is not None:
        return _COMMON_PASSWORDS
    _COMMON_PASSWORDS = set()
    if _COMMON_PASSWORDS_PATH.exists():
        for line in _COMMON_PASSWORDS_PATH.read_text(encoding="utf-8").splitlines():
            pw = line.strip().casefold()
            if pw and not pw.startswith("#"):
                _COMMON_PASSWORDS.add(pw)
    return _COMMON_PASSWORDS


def _is_common_password(password: str) -> bool:
    return password.strip().casefold() in _load_common_passwords()


def _has_sufficient_variety(password: str) -> bool:
    return len(set(password)) >= MIN_PASSWORD_VARIETY


# ---------------------------------------------------------------------------
# Existing helpers
# ---------------------------------------------------------------------------

def is_known_default_password(password: str) -> bool:
    """True, wenn das Passwort nach Trim/casefold einem bekannten Standardpasswort entspricht."""
    normalized = password.strip().casefold()
    return any(normalized == known.strip().casefold() for known in KNOWN_DEFAULT_PASSWORDS)


def validate_new_password(password: str) -> None:
    """Prueft ein neues Passwort gegen die Policy. Wirft PasswordError mit Code.

    B-23: Prueft auch auf gebräuchliche Passwörter und Zeichen-Vielfalt.
    """
    if _is_common_password(password):
        raise PasswordError(ERROR_PASSWORD_TOO_COMMON)
    if is_known_default_password(password):
        raise PasswordError(ERROR_PASSWORD_IS_DEFAULT)
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        raise PasswordError(ERROR_PASSWORD_TOO_SHORT)
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordError(ERROR_PASSWORD_TOO_LONG)
    if not _has_sufficient_variety(password):
        raise PasswordError(ERROR_PASSWORD_LOW_VARIETY)