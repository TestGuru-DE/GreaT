"""REQ-6011: Basisklasse und Hilfsfunktionen fuer Exporter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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