"""REQ-6011: Robot Framework Export (.robot).

Data-Driven-Test mit `Test Template` und einer Zeile je Testfall.
Space-separated Format (4 Leerzeichen als Trennzeichen).

BUG A-06: Gueltige Syntax (Test Template in *** Settings ***, eingerueckte
[Arguments]); Werte werden nach den Robot-Regeln maskiert (Variablen, #, =,
Leerzeichen, leere Werte), sodass jedes Argument exakt den Originalwert erhaelt.
BUG A-12: Variablennamen behalten Umlaute und sind nach Robot-Regeln eindeutig
(Robot ignoriert Gross-/Kleinschreibung, Leerzeichen und Unterstriche).
"""
from __future__ import annotations

import re

from .base import BaseExporter, metadata_comment, single_line, sorted_testcases, unique_names

SEP = "    "
KEYWORD_NAME = "Execute Test Case"


class RobotExporter(BaseExporter):
    """Export als Robot Framework .robot-Datei."""

    name = "robot"
    file_extension = ".robot"
    media_type = "text/plain"

    def render(self, generation_view: dict, options: dict) -> bytes:
        categories = generation_view.get("categories", [])
        result_categories = set(generation_view.get("result_categories", []))
        varnames = unique_names(categories, robot_safe_varname, key=_robot_normalize)

        lines: list[str] = [
            f"# {metadata_comment(generation_view, options)}",
            "*** Settings ***",
            f"Test Template{SEP}{KEYWORD_NAME}",
            "",
            "*** Test Cases ***",
        ]
        for tc in sorted_testcases(generation_view.get("testcases", [])):
            cells = [robot_escape_name(tc.get("name", ""))]
            cells += [robot_escape_value(tc["assignments"].get(cat, "")) for cat in categories]
            lines.append(SEP.join(cells))

        lines += ["", "*** Keywords ***", KEYWORD_NAME]
        if varnames:
            lines.append(SEP + "[Arguments]" + SEP + SEP.join("${" + v + "}" for v in varnames))
            for cat, var in zip(categories, varnames):
                # Eine Zelle: "<Kategorie>: ${var}" (Log nimmt die Meldung als 1. Argument)
                prefix = "Expected " if cat in result_categories else ""
                label = robot_escape_value(prefix + single_line(cat).strip() + ":")
                lines.append(SEP + "Log" + SEP + label + " ${" + var + "}")
        else:
            lines.append(SEP + "No Operation")

        lines.append("")
        return "\n".join(lines).encode("utf-8")


def _robot_normalize(name: str) -> str:
    """Robot vergleicht Variablennamen ohne Gross-/Kleinschreibung, Leerzeichen und _."""
    return name.casefold().replace("_", "").replace(" ", "")


def robot_safe_varname(name: str) -> str:
    """Kategoriename -> Robot-Variablenname (Buchstaben inkl. Umlaute, Ziffern, _)."""
    safe = re.sub(r"\W", "_", single_line(name)).strip("_")
    if not safe or safe[0].isdigit():
        safe = "v_" + safe  # ${1} waere eine Zahl, kein Variablenname
    return safe


def robot_escape_value(value: str) -> str:
    """Maskiert einen Wert als einzelnes Robot-Argument (exakter Originalwert).

    - leerer Wert -> ${EMPTY}
    - Backslash, Variablenzeichen ($ @ & %), #, = -> mit Backslash maskiert
    - Zeilenumbruch/Tab/Steuerzeichen -> \\n, \\r, \\t, \\xhh, \\uhhhh
    - Leerzeichen am Rand oder mehrfach -> ${SPACE} (sonst Trennzeichen)
    """
    value = "" if value is None else str(value)
    if value == "":
        return "${EMPTY}"
    out: list[str] = []
    for ch in value:
        if ch in "\\$@&%#=":
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20 or ch in "\x7f\x85":
            out.append(f"\\x{ord(ch):02x}")
        elif ch in "  \xa0":
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    escaped = "".join(out)
    if " " in value and (value != value.strip(" ") or "  " in value):
        escaped = escaped.replace(" ", "${SPACE}")
    return escaped


def robot_escape_name(name: str) -> str:
    """Testfallname (erste Zelle einer Zeile); Leerzeichen bleiben einfach erhalten."""
    escaped = robot_escape_value(single_line(name).strip())
    return "TC" if escaped == "${EMPTY}" else escaped
