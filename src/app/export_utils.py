"""Export-Hilfsfunktionen fuer CSV/XLSX.

B-05: Schuetzt Werte vor Formel-Injection in Tabellenkalkulationen.
"""
from __future__ import annotations

import re
from typing import Any

# Regex fuer reine Zahlen (optional mit Vorzeichen und Dezimaltrenner . oder ,)
_NUMBER_RE = re.compile(r"^[+-]?\d+([.,]\d+)?$")

FORMULA_CHARS = ("=", "+", "-", "@", "\t", "\r")


def escape_spreadsheet_value(value: Any) -> Any:
    """Schuetzt Werte vor Formel-Injection in Tabellenkalkulationen.

    Wenn der Wert mit =, +, -, @, Tab oder CR beginnt, wird ein Apostroph
    vorangestellt, damit Excel/LibreOffice ihn als Text behandelt.

    Ausnahme: Reine Zahlen (z. B. -1, +5, -0,5) bleiben unveraendert.
    Nicht-String-Werte werden unveraendert zurueckgegeben.

    Args:
        value: Der zu escapende Wert (string, int, float, None, etc.)

    Returns:
        Den ggf. mit Apostroph vorangestellten String, oder den Originalwert
        wenn kein Escape benoetigt ist.
    """
    if not isinstance(value, str) or not value:
        return value

    # Reine Zahlen unveraendert lassen
    if _NUMBER_RE.match(value):
        return value

    # Formel-Startzeichen: mit Apostroph schuetzen
    if value[0] in FORMULA_CHARS:
        return f"'{value}"

    return value