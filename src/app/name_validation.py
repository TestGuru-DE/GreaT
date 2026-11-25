"""BUG A-02: Gemeinsame Pruefung fuer Namen (Projekte, Kategorien, Seed-Saetze).

Namen landen in Kopf-/Kommentarzeilen und Bezeichnern von Exporten (pytest,
Robot, Gherkin, Markdown, CSV). Zeilenumbrueche und Steuerzeichen sind dort
gefaehrlich (Code-Injection) und fachlich nie sinnvoll. Werte (Testdaten) sind
davon ausgenommen und duerfen weiterhin Zeilenumbrueche enthalten.
"""
from __future__ import annotations

import re
from typing import Optional

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f\x85  ]")

CONTROL_CHARS_MESSAGE = "Name darf keine Zeilenumbrueche, Tabulatoren oder Steuerzeichen enthalten."


def reject_control_chars(value: Optional[str]) -> Optional[str]:
    """Wirft ValueError, wenn der Name Steuer- oder Zeilentrennzeichen enthaelt."""
    if value is not None and _CONTROL_CHARS_RE.search(value):
        raise ValueError(CONTROL_CHARS_MESSAGE)
    return value
