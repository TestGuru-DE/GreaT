"""REQ-6005: Uebersetzungstabelle fuer serverseitige Fehlermeldungen.

Fuer HTTP-Fehler ohne stabilen `code` sendet das Frontend `Accept-Language`,
und der Server liefert den `detail`-Text in dieser Sprache.
Fehlercodes bleiben sprachneutral.
"""
from typing import Optional


# Mapping: error_code -> { "de": ..., "en": ... }
ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "invalid_credentials": {
        "de": "Ungültige Anmeldedaten",
        "en": "Invalid credentials",
    },
    "account_deactivated": {
        "de": "Konto ist deaktiviert",
        "en": "Account is deactivated",
    },
    "no_refresh_token": {
        "de": "Kein Refresh-Token",
        "en": "No refresh token",
    },
    "invalid_refresh_token": {
        "de": "Ungültiger Refresh-Token",
        "en": "Invalid refresh token",
    },
    "refresh_token_expired": {
        "de": "Refresh-Token abgelaufen",
        "en": "Refresh token expired",
    },
    "invalid_token_type": {
        "de": "Ungültiger Token-Typ",
        "en": "Invalid token type",
    },
    "user_not_found": {
        "de": "Nutzer nicht gefunden",
        "en": "User not found",
    },
    "session_expired": {
        "de": "Sitzung abgelaufen, bitte neu anmelden",
        "en": "Session expired, please log in again",
    },
    "login_rate_limited": {
        "de": "Zu viele Login-Versuche. Bitte versuche es spaeter erneut.",
        "en": "Too many login attempts. Please try again later.",
    },
    "password_change_required": {
        "de": "Passwortwechsel erforderlich",
        "en": "Password change required",
    },
    "current_password_invalid": {
        "de": "Aktuelles Passwort ist falsch",
        "en": "Current password is incorrect",
    },
    "password_is_default": {
        "de": "Passwort darf nicht das Standardpasswort sein",
        "en": "Password must not be the default password",
    },
    "password_too_short": {
        "de": "Passwort zu kurz",
        "en": "Password too short",
    },
    "password_too_long": {
        "de": "Passwort zu lang",
        "en": "Password too long",
    },
    "too_many_attempts": {
        "de": "Zu viele Versuche. Bitte versuche es spaeter erneut.",
        "en": "Too many attempts. Please try again later.",
    },
    "internal_error": {
        "de": "Interner Serverfehler",
        "en": "Internal server error",
    },
    "invalid_language": {
        "de": "Ungültige Sprache. Gueltige Werte: de, en",
        "en": "Invalid language. Valid values: de, en",
    },
}


def get_error_message(error_code: str, lang: str = "de") -> str:
    """Liefert die Uebersetzung fuer einen Fehlercode.

    Falls der Code nicht bekannt oder die Sprache nicht verfuegbar ist,
    wird der englische Text als Fallback verwendet.
    """
    entry = ERROR_MESSAGES.get(error_code)
    if entry is None:
        return error_code
    return entry.get(lang, entry.get("en", error_code))


def detect_request_language(request_headers: dict[str, str]) -> str:
    """Bestimmt die Sprache aus dem Accept-Language-Header.

    Prioritaet: de > en > Default de
    """
    accept = request_headers.get("accept-language", "")
    if not accept:
        return "de"
    # Einfache Pruefung: erster Eintrag
    for part in accept.split(","):
        part = part.strip().lower()
        if part.startswith("de"):
            return "de"
        if part.startswith("en"):
            return "en"
    return "de"