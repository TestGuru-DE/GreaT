"""REQ-6011: pytest Export (.py).

Datei mit @pytest.mark.parametrize ueber alle Kategorien.
"""
from __future__ import annotations

import re

from .base import BaseExporter, single_line

# Python-Reserved-Worte die nicht als Variablenname verwendet werden duerfen
PYTHON_RESERVED = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
}

# Builtin-Funktionen/Klassen die kollidieren koennen
PYTHON_BUILTINS = {
    "os", "sys", "io", "str", "int", "float", "list", "dict", "set",
    "tuple", "bool", "type", "len", "print", "input", "open", "file",
    "value", "test", "case", "name", "id", "class", "method", "function",
}


class PytestExporter(BaseExporter):
    """Export als pytest-Testdatei."""

    name = "pytest"
    file_extension = ".py"
    media_type = "text/x-python"

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

        lines.append('"""Auto-generated test file by G.R.E.A.T."""')
        lines.append("import pytest")
        lines.append("")

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        # Variablennamen fuer Kategorien
        var_names = [to_python_identifier(cat) for cat in categories]

        # Mapping-Kommentar
        mapping_parts = [f"{vn} -> {cn}" for vn, cn in zip(var_names, categories)]
        lines.append(f"# Mapping: {', '.join(mapping_parts)}")
        lines.append("")

        # @pytest.mark.parametrize
        param_names = ", ".join(var_names)
        lines.append(f'@pytest.mark.parametrize("{param_names}", [')

        # Argument-Tupel + ids
        arg_tuples: list[str] = []
        ids: list[str] = []

        for tc in sorted(testcases, key=lambda t: t["name"]):
            values = []
            for cat in categories:
                val = tc["assignments"].get(cat, "")
                values.append(f"'{escape_python_string(val)}'")
            arg_tuples.append(f"    ({', '.join(values)}),")
            ids.append(f'"{tc["name"]}"')

        lines.extend(arg_tuples)
        lines.append("], ids=[" + ", ".join(ids) + "])")

        # Funktionssignatur
        lines.append(f"def test_generated({', '.join(var_names)}):")
        lines.append('    pytest.skip("TODO")')
        lines.append("")

        return "\n".join(lines).encode("utf-8")


def to_python_identifier(name: str) -> str:
    """Konvertiert Kategoriename in gueltigen Python-Bezeichner.

    - Umlaute -> ASCII (ae, oe, ue, ss)
    - Leerzeichen/Sonderzeichen -> _
    - Reserved-Worte/Builtins -> _ suffix
    """
    # Umlaute ersetzen
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    name = name.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    name = name.replace("ß", "ss")

    # Nur alphanumerische Zeichen und Unterstriche
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Fuhrende Unterstriffe/Ziffern entfernen
    name = re.sub(r"^[_0-9]+", "", name)

    # Falls leer: Fallback
    if not name:
        name = "param"

    # Reserved-Worte und Builtins: _ suffix
    if name in PYTHON_RESERVED or name in PYTHON_BUILTINS:
        name += "_"

    return name


def escape_python_string(value: str) -> str:
    """Escapes Zeichen fuer ein Python-String-Literal in einfachen Anfuehrungszeichen.

    BUG A-02: Neben Backslash, Quote und \\n/\\r/\\t werden alle weiteren Steuer- und
    Zeilentrennzeichen (\\x00-\\x1f, \\x7f, \\x85, U+2028, U+2029) als Escape-Sequenz
    ausgegeben. Das Literal bleibt damit immer einzeilig und ergibt exakt den Originalwert.
    """
    out = []
    for ch in value:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "'":
            out.append("\\'")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20 or ch in "\x7f\x85":
            out.append(f"\\x{ord(ch):02x}")
        elif ch in "  ":
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return "".join(out)