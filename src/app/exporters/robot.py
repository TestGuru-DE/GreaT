"""REQ-6011: Robot Framework Export (.robot).

Data-Driven-Test mit [Template] und einer Zeile je Testfall.
Space-separated Format (2+ Spaces als Trennzeichen).
"""
from __future__ import annotations

from .base import BaseExporter, single_line


class RobotExporter(BaseExporter):
    """Export als Robot Framework .robot-Datei."""

    name = "robot"
    file_extension = ".robot"
    media_type = "text/plain"

    def render_header(self, project_name: str, gen_id: str, strategy: str,
                      date: str, version: str) -> str:
        return (
            f"# G.R.E.A.T. Export | Projekt: {single_line(project_name)} | "
            f"Generierung: {single_line(gen_id)} | Strategie: {single_line(strategy)} | "
            f"Datum: {single_line(date)} | Version: {single_line(version)}\n"
        )

    def render(self, generation_view: dict, options: dict) -> bytes:
        lines: list[str] = []

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

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        # *** Settings ***
        lines.append("*** Settings ***")
        lines.append("[Template]    Execute Test Case")
        lines.append("")

        # *** Test Cases ***
        lines.append("*** Test Cases ***")

        for tc in sorted(testcases, key=lambda t: t["name"]):
            values = []
            for cat in categories:
                val = tc["assignments"].get(cat, "")
                values.append(robot_escape_value(val))
            # 4-Space-Trennung zwischen Werten
            line = f"{tc['name']}"
            for v in values:
                line += "    " + v
            lines.append(line)

        lines.append("")

        # *** Keywords ***
        lines.append("*** Keywords ***")
        lines.append("Execute Test Case")

        # [Arguments]
        arg_parts = []
        for cat in categories:
            vn = robot_safe_varname(cat)
            arg_parts.append("$" + "{" + vn + "}")
        lines.append("[Arguments]    " + "    ".join(arg_parts))
        lines.append("")

        # Log-Schritte (Platzhalter)
        for cat in categories:
            varname = robot_safe_varname(cat)
            if cat in result_categories:
                lines.append("    Should Be Equal As Strings    $" + "{" + varname + "}" + "    Expected Result")
            else:
                lines.append("    Log    " + robot_escape_value(single_line(cat)) + ": $" + "{" + varname + "}")

        lines.append("")
        return "\n".join(lines).encode("utf-8")


def robot_safe_varname(name: str) -> str:
    """Konvertiert Kategoriename in Robot-sicheren Variablennamen."""
    import re
    # Nur alphanumerische Zeichen und Unterstriche
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return safe


def robot_escape_value(value: str) -> str:
    r"""Escapes Pipe-Zeichen und Anführungszeichen in Robot-Werten.

    Pipe: \| escapen
    Anführungszeichen: ${"quoted"} Syntax
    """
    if not value:
        return value

    # BUG A-02: Zeilenumbrueche und Steuerzeichen duerfen keine neue Robot-Zeile
    # (und damit keine neuen Abschnitte wie *** Settings ***) erzeugen.
    # Robot kennt die Escape-Sequenzen \n, \r, \t und \xhh.
    value = (
        value.replace("\\", "\\\\")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    value = "".join(
        f"\\x{ord(c):02x}" if (ord(c) < 0x20 or c in "\x7f\x85") else
        f"\\u{ord(c):04x}" if c in "  " else c
        for c in value
    )

    escaped = value.replace("|", "\\|")

    # Bei Sonderzeichen: ${"quoted"} Syntax
    if '"' in escaped or "'" in escaped or "\\" in escaped:
        escaped = escaped.replace('"', '\\"')
        return '${"' + escaped + '"}'

    return escaped