"""REQ-6011: Basisklasse und Hilfsfunktionen fuer Exporter."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

# BUG A-02: Alle Zeichen, die in zeilenbasierten Formaten (Python, Robot, Gherkin,
# Markdown, CSV-Kommentar) eine Zeile beenden oder Steuerfunktionen haben.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f\x85  ]+")


def single_line(value: Any) -> str:
    """BUG A-02: Macht einen Namen einzeilig und frei von Steuerzeichen.

    Jede Folge von Steuer- oder Zeilentrennzeichen wird durch ein Leerzeichen
    ersetzt. Verwendet fuer Projekt-, Kategorie-, Generierungsnamen und andere
    Metadaten, die in Kopf-/Kommentarzeilen oder Bezeichnern landen.
    """
    if value is None:
        return ""
    return _CONTROL_CHARS_RE.sub(" ", str(value))


def sanitize_generation_view(view: dict) -> dict:
    """BUG A-02: Liefert eine Kopie des generation_view mit einzeiligen Namen.

    Werte (Testdaten) bleiben unveraendert; sie werden format-spezifisch maskiert.
    Kategorienamen werden konsistent in categories, result_categories und den
    Schluesseln der assignments ersetzt. Kollisionen nach dem Bereinigen werden
    durch einen Zaehler-Suffix aufgeloest.
    """
    rename: dict[str, str] = {}
    used: set[str] = set()
    for original in list(view.get("categories", [])) + list(view.get("result_categories", [])):
        if original in rename:
            continue
        clean = single_line(original)
        candidate, n = clean, 2
        while candidate in used:
            candidate = f"{clean} ({n})"
            n += 1
        rename[original] = candidate
        used.add(candidate)

    def _cat(name: str) -> str:
        return rename.get(name, single_line(name))

    out = dict(view)
    for key in ("project_name", "name", "strategy", "version", "created_at"):
        if key in out:
            out[key] = single_line(out[key])
    out["categories"] = [_cat(c) for c in view.get("categories", [])]
    out["result_categories"] = [_cat(c) for c in view.get("result_categories", [])]
    out["testcases"] = [
        {
            **tc,
            "name": single_line(tc.get("name", "")),
            "assignments": {_cat(k): v for k, v in tc.get("assignments", {}).items()},
        }
        for tc in view.get("testcases", [])
    ]
    return out


class BaseExporter(ABC):
    """Abstrakte Basisklasse fuer alle Export-Formate.

    Jeder Exporter implementiert `render()` und definiert statische
    Attribute fuer Formatname, Dateiendung und MIME-Typ.
    """

    name: str              # z.B. "gherkin", "pytest", "json-data-driven"
    file_extension: str    # z.B. ".feature", ".py", ".json"
    media_type: str        # z.B. "text/plain", "text/csv", "application/json"

    @abstractmethod
    def render(self, generation_view: dict, options: dict) -> bytes:
        """Erzeugt Export-Bytes aus generation_view.

        Args:
            generation_view: Dict mit Projekt-, Generierungs- und Testfalldaten.
                Struktur:
                {
                    "project_name": str,
                    "project_id": int,
                    "generation_id": int,
                    "strategy": str,
                    "name": str | None,
                    "created_at": str,
                    "version": str,
                    "categories": [str, ...],       # Kategorienamen in Reihenfolge
                    "result_categories": [str, ...], # Ergebnis-Kategorien
                    "error_values": [str, ...],      # Werte mit allowed=False
                    "testcases": [
                        {
                            "id": int,
                            "name": str,              # z.B. "TC_1"
                            "assignments": {cat_name: value, ...},
                            "has_error_value": bool,
                        },
                        ...
                    ],
                }
            options: Format-spezifische Optionen, z.B. {"lang": "de"}.

        Returns:
            Bytes der Export-Datei.
        """
        ...

    def render_header(self, project_name: str, gen_id: str, strategy: str,
                      date: str, version: str) -> str:
        """Format-spezifische Kopfzeile (wo Kommentare erlaubt).

        Standard-Implementierung gibt eine leere Zeichenkette zurueck.
        Unterklassen koennen dies ueberschreiben.
        """
        return ""


def protect_formula(value: str) -> str:
    """Schuetzt vor Formel-Injection in CSV/XLS.

    Werte die mit =, +, -, @ oder Tab/CR beginnen werden
    mit Apostroph ('") vorangestellt.

    Reine Zahlen bleiben unveraendert.
    """
    from ..export_utils import escape_spreadsheet_value
    return escape_spreadsheet_value(value)