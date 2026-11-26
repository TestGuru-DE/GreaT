"""REQ-6011: Gherkin Export (.feature).

BDD-Format mit Feature/Scenario Outline/Examples.
Sprache DE (Funktionalität/Szenariogrundriss/Beispiele) oder EN waehlbar.

BUG A-05: Gueltige deutsche Schluesselwoerter; Schritte verwenden Platzhalter
(<Spalte>) statt der Werte des ersten Testfalls; Tabellenzellen werden nach der
Gherkin-Spezifikation maskiert (\\|, \\\\, \\n), Werte bleiben unveraendert.
BUG A-12: Spaltennamen behalten Umlaute und sind eindeutig; natuerliche Sortierung.
"""
from __future__ import annotations

import re

from .base import BaseExporter, metadata_comment, single_line, sorted_testcases, unique_names


class GherkinExporter(BaseExporter):
    """Export als Gherkin .feature-Datei."""

    name = "gherkin"
    file_extension = ".feature"
    media_type = "text/plain"

    # Gherkin-Schluesselwoerter DE/EN (offizielle Gherkin-Sprachdefinition)
    KEYWORDS = {
        "en": {
            "feature": "Feature",
            "scenario_outline": "Scenario Outline",
            "scenario_title": "Test case execution",
            "examples": "Examples",
            "given": "Given",
            "when": "When",
            "then": "Then",
            "is": "is",
        },
        "de": {
            "feature": "Funktionalität",
            "scenario_outline": "Szenariogrundriss",
            "scenario_title": "Testfall-Ausführung",
            "examples": "Beispiele",
            "given": "Angenommen",
            "when": "Wenn",
            "then": "Dann",
            "is": "ist",
        },
    }

    def render(self, generation_view: dict, options: dict) -> bytes:
        lang = options.get("lang", "en")
        if lang not in self.KEYWORDS:
            lang = "en"
        kw = self.KEYWORDS[lang]

        categories = generation_view.get("categories", [])
        result_categories = set(generation_view.get("result_categories", []))
        # "TC-ID" ist als erste Spalte reserviert
        columns = unique_names(["TC-ID"] + categories, gherkin_column_name)[1:]

        lines: list[str] = [
            f"# language: {lang}",  # muss die erste Zeile sein
            f"# {metadata_comment(generation_view, options)}",
            f"{kw['feature']}: {single_line(generation_view.get('project_name', ''))}",
            "",
            f"  {kw['scenario_outline']}: {kw['scenario_title']}",
        ]

        # Schritte: erste Eingabe Given, weitere When, Ergebnisse Then
        inputs_seen = 0
        for cat, col in zip(categories, columns):
            if cat in result_categories:
                keyword = kw["then"]
            else:
                keyword = kw["given"] if inputs_seen == 0 else kw["when"]
                inputs_seen += 1
            lines.append(f"    {keyword} {col} {kw['is']} \"<{col}>\"")

        lines.append("")
        lines.append(f"    {kw['examples']}:")
        lines.append("      | " + " | ".join(["TC-ID"] + columns) + " |")
        for tc in sorted_testcases(generation_view.get("testcases", [])):
            cells = [gherkin_escape_value(tc.get("name", ""))]
            cells += [gherkin_escape_value(tc["assignments"].get(cat, "")) for cat in categories]
            lines.append("      | " + " | ".join(cells) + " |")

        lines.append("")
        return "\n".join(lines).encode("utf-8")


_COLUMN_UNSAFE_RE = re.compile(r"[|<>\\\"]")


def gherkin_column_name(name: str) -> str:
    """Spaltenname = Platzhaltername. Zeichen, die Tabelle oder Platzhalter stoeren, -> _.

    Umlaute und andere Buchstaben bleiben erhalten (A-12).
    """
    safe = _COLUMN_UNSAFE_RE.sub("_", single_line(name)).strip()
    return safe or "Kategorie"


def gherkin_escape_value(value: str) -> str:
    """Maskiert einen Wert fuer eine Gherkin-Tabellenzelle (\\\\, \\|, \\n).

    Der Gherkin-Parser liefert danach exakt den Originalwert zurueck, mit einer
    Ausnahme: fuehrende/abschliessende Leerzeichen einer Zelle entfernt Gherkin immer.
    """
    value = "" if value is None else str(value)
    value = value.replace("\\", "\\\\").replace("|", "\\|")
    # BUG A-02: Zeilenumbrueche als \n, sonstige Steuerzeichen entfernen
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    return single_line(value)
