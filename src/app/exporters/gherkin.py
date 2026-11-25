"""REQ-6011: Gherkin Export (.feature).

BDD-Format mit Feature/Scenario Outline/Examples.
Sprache DE (Funktionalitaet/Szenariogrundriss/Beispiele) oder EN waehlbar.
"""
from __future__ import annotations

from .base import BaseExporter, single_line


class GherkinExporter(BaseExporter):
    """Export als Gherkin .feature-Datei."""

    name = "gherkin"
    file_extension = ".feature"
    media_type = "text/plain"

    # Gherkin-Schluesselwoerter DE/EN
    KEYWORDS = {
        "en": {
            "feature": "Feature",
            "scenario_outline": "Scenario Outline",
            "examples": "Examples",
            "given": "Given",
            "when": "When",
            "then": "Then",
        },
        "de": {
            "feature": "Funktionalitaet",
            "scenario_outline": "Szenariogrundriss",
            "examples": "Beispiele",
            "given": "Angenommen",
            "when": "Wenn",
            "then": "Dann",
        },
    }

    def render_header(self, project_name: str, gen_id: str, strategy: str,
                      date: str, version: str) -> str:
        return (
            f"# G.R.E.A.T. Export | Projekt: {single_line(project_name)} | "
            f"Generierung: {single_line(gen_id)} | Strategie: {single_line(strategy)} | "
            f"Datum: {single_line(date)} | Version: {single_line(version)}\n"
        )

    def render(self, generation_view: dict, options: dict) -> bytes:
        lang = options.get("lang", "en")
        if lang not in self.KEYWORDS:
            lang = "en"
        kw = self.KEYWORDS[lang]

        lines: list[str] = []

        # Language-Deklaration
        lines.append(f"# language: {lang}")

        # Header-Kommentar
        date_str = generation_view.get("created_at", "")
        if options.get("deterministic"):
            date_str = "1970-01-01"
        header = self.render_header(
            generation_view["project_name"],
            str(generation_view["generation_id"]),
            generation_view["strategy"],
            date_str,
            generation_view.get("version", ""),
        )
        if header:
            lines.append(header)

        project_name = generation_view["project_name"]
        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        # Feature-Zeile
        lines.append(f"{kw['feature']}: {project_name}")
        lines.append("")

        # Scenario Outline
        lines.append(f"{kw['scenario_outline']}: Test Case Execution")
        lines.append("")

        # Given/When/Then-Schritte (Platzhalter pro Kategorie)
        step_idx = 0
        for cat in categories:
            if cat in result_categories:
                keyword = kw["then"]
            elif step_idx == 0:
                keyword = kw["given"]
            else:
                keyword = kw["when"]
            lines.append(f"  {keyword} <{gherkin_safe_name(cat)}> is '{gherkin_escape_value(generation_view['testcases'][0]['assignments'].get(cat, ''))}'")
            step_idx += 1

        lines.append("")

        # Examples-Tabelle
        lines.append(f"{kw['examples']}:")

        # Header-Zeile der Examples-Tabelle
        header_cells = ["TC-ID"] + [gherkin_safe_name(c) for c in categories]
        lines.append("  | " + " | ".join(header_cells) + " |")

        # Datenzeilen
        for tc in sorted(testcases, key=lambda t: t["name"]):
            row_cells = [tc["name"]]
            for cat in categories:
                val = tc["assignments"].get(cat, "")
                row_cells.append(gherkin_escape_value(val))
            lines.append("  | " + " | ".join(row_cells) + " |")

        lines.append("")  # trailing newline
        return "\n".join(lines).encode("utf-8")


def gherkin_safe_name(name: str) -> str:
    """Konvertiert Kategoriename in gherkin-sicheren Spaltennamen.

    Leerzeichen und Sonderzeichen werden durch Unterstriche ersetzt.
    """
    import re
    # Nur alphanumerische Zeichen und Unterstriche
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return safe


def gherkin_escape_value(value: str) -> str:
    """Escapes Pipe-Zeichen und Anführungszeichen in Gherkin-Werten.

    Pipe: \| escapen
    Anführungszeichen: '...' umschließen
    """
    # BUG A-02: Zeilenumbrueche als \n (Gherkin-Tabellen-Escape), sonstige
    # Steuerzeichen entfernen, damit keine neue Gherkin-Zeile entsteht.
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    value = single_line(value)
    escaped = value.replace("|", "\\|")
    if '"' in escaped or "'" in escaped:
        escaped = '"' + escaped.replace('"', '\\"') + '"'
    return escaped