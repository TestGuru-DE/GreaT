"""REQ-6011: Xray (Jira) CSV Export.

Ein Testfall = eine Zeile. Spalten nach Xray-Testimport.
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, protect_formula, single_line


class XrayCsvExporter(BaseExporter):
    """Export als Xray CSV (Semikolon-Delimiter)."""

    name = "xray-csv"
    file_extension = ".csv"
    media_type = "text/csv"

    def render_header(self, project_name: str, gen_id: str, strategy: str,
                      date: str, version: str) -> str:
        return (
            f"# G.R.E.A.T. Export | Projekt: {single_line(project_name)} | "
            f"Generierung: {single_line(gen_id)} | Strategie: {single_line(strategy)} | "
            f"Datum: {single_line(date)} | Version: {single_line(version)}\n"
        )

    def render(self, generation_view: dict, options: dict) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n",
                            quoting=csv.QUOTE_ALL)

        # Header-Kommentar (wird vom Import ignoriert)
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
            output.write(header)

        # CSV-Header
        writer.writerow([
            "Test Case Identifier", "Summary", "Action", "Data",
            "Expected Result", "Preconditions", "Test Type"
        ])

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        for tc in sorted(testcases, key=lambda t: t["name"]):
            assignments = tc["assignments"]

            # Summary: TC_X: val1/val2/val3 (nicht-Ergebnis-Kategorien)
            summary_parts = [tc["name"]]
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        summary_parts.append(val)
            summary = ": " + "/".join(summary_parts[1:]) if len(summary_parts) > 1 else tc["name"]

            # Data: Browser: val1, OS: val2, Eingabe: val3
            data_parts = []
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        data_parts.append(f"{cat}: {val}")
            data = ", ".join(data_parts)

            # Expected Result: Ergebnis: val4 (Ergebnis-Kategorien)
            expected_parts = []
            for cat in result_categories:
                val = assignments.get(cat, "")
                if val:
                    expected_parts.append(f"{cat}: {val}")
            expected = "; ".join(expected_parts) if expected_parts else ""

            # Formel-Schutz
            summary = protect_formula(summary)
            data = protect_formula(data)
            expected = protect_formula(expected)

            writer.writerow([
                tc["name"],
                summary,
                "Execute test",
                data,
                expected,
                "",  # Preconditions
                "Manual",
            ])

        return output.getvalue().encode("utf-8")