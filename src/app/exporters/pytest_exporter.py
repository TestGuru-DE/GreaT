"""REQ-6011: pytest Export (.py).

Datei mit @pytest.mark.parametrize ueber alle Kategorien.
"""
from __future__ import annotations

import re

from .base import BaseExporter, metadata_comment, single_line, sorted_testcases, unique_names

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
    "pytest",  # wuerde im Testkoerper das Modul verdecken (pytest.skip)
}


class PytestExporter(BaseExporter):
    """Export als pytest-Testdatei."""

    name = "pytest"
    file_extension = ".py"
    media_type = "text/x-python"

    def render(self, generation_view: dict, options: dict) -> bytes:
        lines: list[str] = [
            f"# {metadata_comment(generation_view, options)}",
            "",
            '"""Auto-generated test file by G.R.E.A.T."""',
            "import pytest",
            "",
        ]

        categories = generation_view.get("categories", [])
        testcases = sorted_testcases(generation_view.get("testcases", []))  # BUG A-12

        # BUG A-12: eindeutige Bezeichner ("a b" und "a-b" -> a_b, a_b_2)
        var_names = unique_names(categories, to_python_identifier)

        # Mapping-Kommentar
        mapping_parts = [f"{vn} -> {single_line(cn)}" for vn, cn in zip(var_names, categories)]
        lines.append(f"# Mapping: {', '.join(mapping_parts)}")
        lines.append("")

        if not var_names:
            lines.append("def test_generated():")
            lines.append('    pytest.skip("TODO")')
            lines.append("")
            return "\n".join(lines).encode("utf-8")

        lines.append(f'@pytest.mark.parametrize("{", ".join(var_names)}", [')
        ids: list[str] = []
        for tc in testcases:
            values = [f"'{escape_python_string(tc['assignments'].get(cat, ''))}'" for cat in categories]
            lines.append(f"    ({', '.join(values)}),")
            ids.append(f"'{escape_python_string(tc.get('name', ''))}'")
        lines.append("], ids=[" + ", ".join(ids) + "])")

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