"""REQ-6011: TestRail CSV Export.

Single-Row Layout: Ein Testfall = eine Zeile.
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, protect_formula


class TestRailCsvExporter(BaseExporter):
    """Export als TestRail CSV (Semikolon-Delimiter)."""

    name = "testrail-csv"
    file_extension = ".csv"
    media_type = "text/csv"

    def render_header(self, project_name: str, gen_id: str, strategy: str,
                      date: str, version: str) -> str:
        return (
            f"# G.R.E.A.T. Export | Projekt: {project_name} | "
            f"Generierung: {gen_id} | Strategie: {strategy} | "
            f"Datum: {date} | Version: {version}\n"
        )

    def render(self, generation_view: dict, options: dict) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n",
                            quoting=csv.QUOTE_ALL)

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
            output.write(header)

        # CSV-Header
        writer.writerow(["Title", "Preconditions", "Steps", "Expected Result"])

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        for tc in sorted(testcases, key=lambda t: t["name"]):
            assignments = tc["assignments"]

            # Title: TC_X: val1/val2/val3
            title_parts = [tc["name"]]
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        title_parts.append(val)
            title = ": " + "/".join(title_parts[1:]) if len(title_parts) > 1 else tc["name"]

            # Steps: "1. Set Browser to val1. 2. Set OS to val2. ..."
            step_parts = []
            step_num = 1
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        step_parts.append(f"{step_num}. Set {cat} to {val}.")
                        step_num += 1
            steps = " ".join(step_parts)

            # Expected Result: Ergebnis: val4
            expected_parts = []
            for cat in result_categories:
                val = assignments.get(cat, "")
                if val:
                    expected_parts.append(f"{cat}: {val}")
            expected = "; ".join(expected_parts) if expected_parts else ""

            # Formel-Schutz
            title = protect_formula(title)
            steps = protect_formula(steps)
            expected = protect_formula(expected)

            writer.writerow([title, "", steps, expected])

        return output.getvalue().encode("utf-8")