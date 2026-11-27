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


def concrete_value(value: Any) -> Any:
    """REQ-6007 / Restbefund 9b-9c: Symbolische Langwerte (<STR len=N charset=X>) fuer
    Testfall-Exporte in echte Zeichenketten aufloesen.

    Deterministisch: Der Seed haengt nur vom Platzhalter ab, derselbe Wert ergibt in jedem
    Export dieselbe Zeichenkette. Andere Werte bleiben unveraendert.
    """
    if not isinstance(value, str) or not value.startswith("<STR "):
        return value
    import zlib
    from combinatorics.symbolic_values import concretize_symbolic, is_symbolic

    if not is_symbolic(value):
        return value
    return concretize_symbolic(value, seed=zlib.crc32(value.encode("utf-8")))


def concrete_assignments(assignments: dict) -> dict:
    """Alle Werte einer Belegung mit concrete_value aufloesen."""
    return {k: concrete_value(v) for k, v in assignments.items()}
