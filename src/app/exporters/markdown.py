"""REQ-6011: Markdown Export.

Tabelle mit |-Trennzeichen fuer Wikis/Pull Requests.
"""
from __future__ import annotations

from .base import BaseExporter, metadata_comment, single_line, sorted_testcases


class MarkdownExporter(BaseExporter):
    """Export als Markdown-Tabelle."""

    name = "markdown"
    file_extension = ".md"
    media_type = "text/markdown"

    def render(self, generation_view: dict, options: dict) -> bytes:
        lines: list[str] = [f"<!-- {metadata_comment(generation_view, options)} -->", ""]

        categories = generation_view.get("categories", [])
        testcases = generation_view.get("testcases", [])

        # Header-Zeile
        header_parts = ["TC-ID"] + [escape_pipe(c) for c in categories]
        lines.append("| " + " | ".join(header_parts) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")

        # Datenzeilen
        for tc in sorted_testcases(testcases):  # BUG A-12
            row_parts = [tc["name"]]
            for cat in categories:
                val = tc["assignments"].get(cat, "")
                row_parts.append(format_md_value(val))
            lines.append("| " + " | ".join(row_parts) + " |")

        lines.append("")  # trailing newline
        return "\n".join(lines).encode("utf-8")


def escape_pipe(value: str) -> str:
    """Escapes Pipe-Zeichen in Markdown-Tabelle."""
    return value.replace("|", "\\|")


def format_md_value(value: str) -> str:
    """Formatiert einen Wert fuer Markdown (Pipe-Escaping + Backticks bei Sonderzeichen)."""
    # BUG A-02: Zeilenumbrueche zerstoeren die Tabelle -> <br>; Steuerzeichen entfernen
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    value = single_line(value)
    escaped = escape_pipe(value)
    # Backticks bei Werten mit Anführungszeichen oder Sonderzeichen
    if '"' in value or "'" in value or "`" in value:
        escaped = escaped.replace("|", "\\|")
        escaped = escaped.replace("`", "\\`")
        escaped = f"`{escaped}`"
    return escaped