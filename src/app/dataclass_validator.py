"""
src/app/dataclass_validator.py
REQ-2003: Typvalidierung fuer Datenklassen-Werte.
Geprueft werden: text, number, date, time, boolean, email, freetext
"""
from __future__ import annotations
import re
from datetime import datetime

DATACLASS_TYPES = ("text", "number", "date", "time", "boolean", "email", "freetext")

_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y")
_TIME_FORMATS = ("%H:%M", "%H:%M:%S")
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_BOOL_VALUES = frozenset(("true", "false", "1", "0", "ja", "nein", "yes", "no"))


def validate_value(value: str, value_type: str) -> tuple[bool, str]:
    """
    Prueft ob `value` dem `value_type` entspricht.
    Gibt (True, "") zurueck wenn gueltig, sonst (False, Fehlermeldung).
    """
    v = value.strip()
    if value_type == "freetext":
        return True, ""
    if value_type == "text":
        if not v:
            return False, "Text darf nicht leer sein."
        return True, ""
    if value_type == "number":
        try:
            float(v)
            return True, ""
        except ValueError:
            return False, f'"{v}" ist keine gueltige Zahl.'
    if value_type == "date":
        for fmt in _DATE_FORMATS:
            try:
                datetime.strptime(v, fmt)
                return True, ""
            except ValueError:
                pass
        return False, f'"{v}" ist kein gueltiges Datum (YYYY-MM-DD, DD.MM.YYYY oder DD/MM/YYYY).'
    if value_type == "time":
        for fmt in _TIME_FORMATS:
            try:
                datetime.strptime(v, fmt)
                return True, ""
            except ValueError:
                pass
        return False, f'"{v}" ist keine gueltige Uhrzeit (HH:MM oder HH:MM:SS).'
    if value_type == "boolean":
        if v.lower() in _BOOL_VALUES:
            return True, ""
        return False, f'"{v}" ist kein gueltiger Boolean-Wert (true/false/1/0/ja/nein).'
    if value_type == "email":
        if _EMAIL_RE.match(v):
            return True, ""
        return False, f'"{v}" ist keine gueltige E-Mail-Adresse.'
    return False, f'Unbekannter Typ: "{value_type}".'