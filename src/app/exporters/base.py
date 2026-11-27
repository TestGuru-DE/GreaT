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


_DIGITS_RE = re.compile(r"(\d+)")


def natural_key(name: Any) -> list:
    """BUG A-12: Sortierschluessel TC_1, TC_2, ..., TC_10 (statt TC_1, TC_10, TC_2)."""
    return [(0, int(part), "") if part.isdigit() else (1, 0, part.casefold())
            for part in _DIGITS_RE.split(str(name)) if part != ""]


def sorted_testcases(testcases: list[dict]) -> list[dict]:
    """BUG A-12: Testfaelle in natuerlicher Reihenfolge ihrer Namen."""
    return sorted(testcases, key=lambda tc: natural_key(tc.get("name", "")))


def unique_names(names: list[str], make: Any, key: Any = None) -> list[str]:
    """BUG A-12: Bildet je Name einen Bezeichner und macht Kollisionen eindeutig.

    make(name) liefert den Bezeichner (z. B. Python-Variable). Kollidieren zwei
    Bezeichner (z. B. "a b" und "a-b" -> "a_b"), erhalten weitere ein Suffix _2, _3, ...
    key(bezeichner) bestimmt, wann zwei Bezeichner als gleich gelten (Standard: exakt).
    """
    key = key or (lambda s: s)
    used: set = set()
    result: list[str] = []
    for name in names:
        base = make(name)
        candidate, n = base, 2
        while key(candidate) in used:
            candidate = f"{base}_{n}"
            n += 1
        used.add(key(candidate))
        result.append(candidate)
    return result


def testcase_title(tc: dict, categories: list[str], result_categories) -> str:
    """BUG A-11: Titel fuer Testmanagement-Formate: "TC_1: wert1/wert2".

    Frueher fehlte durch die Operatorrangfolge die TC-ID (Titel begann mit ": ").
    """
    name = single_line(tc.get("name", ""))
    parts = [single_line(tc["assignments"].get(c, "")) for c in categories if c not in result_categories]
    parts = [p for p in parts if p]
    return f"{name}: {'/'.join(parts)}" if parts else name


def expected_result(tc: dict, result_categories: list[str]) -> str:
    """Erwartetes Ergebnis aus den Ergebnis-Kategorien: "Kategorie: Wert; ..."."""
    parts = [f"{c}: {tc['assignments'].get(c, '')}" for c in result_categories if tc["assignments"].get(c, "")]
    return "; ".join(parts)


def metadata_comment(generation_view: dict, options: dict) -> str:
    """Kopfzeilen-Inhalt (ohne Kommentarzeichen) fuer Formate mit Kommentaren."""
    date_str = "1970-01-01" if options.get("deterministic") else generation_view.get("created_at", "")
    return (
        f"G.R.E.A.T. Export | Projekt: {single_line(generation_view.get('project_name', ''))} | "
        f"Generierung: {single_line(generation_view.get('generation_id', ''))} | "
        f"Strategie: {single_line(generation_view.get('strategy', ''))} | "
        f"Datum: {single_line(date_str)} | Version: {single_line(generation_view.get('version', ''))}"
    )


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


def testcase_tags(tc: dict) -> list[str]:
    """Restbefund 9b: Kennzeichen fuer Testmanagement-Formate (Fehlerwert, Herkunft)."""
    tags: list[str] = []
    if tc.get("has_error_value"):
        tags.append("error-value")
    origin = tc.get("origin")
    if origin == "seed":
        tags.append("seed")
    elif origin == "supplemented":
        tags.append("gap-fill")
    return tags


def protect_formula(value: str) -> str:
    """Schuetzt vor Formel-Injection in CSV/XLS.

    Werte die mit =, +, -, @ oder Tab/CR beginnen werden
    mit Apostroph ('") vorangestellt.

    Reine Zahlen bleiben unveraendert.
    """
    from ..export_utils import escape_spreadsheet_value
    return escape_spreadsheet_value(value)