"""REQ-6011: Azure DevOps Test Plans CSV Export.

Multi-Row: Jeder Schritt = eigene Zeile; ID, Title etc. in jeder Zeile wiederholen.
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, protect_formula, single_line


class AzureDevOpsCsvExporter(BaseExporter):
    """Export als Azure DevOps CSV (Semikolon-Delimiter)."""

    name = "azuredevops-csv"
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
        writer.writerow([
            "ID", "Work Item Type", "Title", "Test Step",
            "Step Action", "Step Expected", "Area Path",
            "Assigned To", "State"
        ])

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])
        testcases = generation_view.get("testcases", [])

        # ID-Counter (fortlaufend pro Testfall: 1, 1, 1, 2, 2, 2, ...)
        tc_counter = 0

        for tc in sorted(testcases, key=lambda t: t["name"]):
            tc_counter += 1
            assignments = tc["assignments"]

            # Title: TC_X: val1/val2/val3
            title_parts = [tc["name"]]
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        title_parts.append(val)
            title = ": " + "/".join(title_parts[1:]) if len(title_parts) > 1 else tc["name"]
            title = protect_formula(title)

            # Steps: jeder nicht-Ergebnis-Wert = ein Schritt
            step_num = 0
            for cat in categories:
                if cat not in result_categories:
                    val = assignments.get(cat, "")
                    if val:
                        step_num += 1
                        step_action = f"Set {cat} to {val}"
                        step_action = protect_formula(step_action)

                        # Expected: letzter Schritt hat das Ergebnis, sonst leer
                        if step_num == self._count_input_steps(categories, result_categories, assignments):
                            expected_parts = []
                            for rc in result_categories:
                                rv = assignments.get(rc, "")
                                if rv:
                                    expected_parts.append(f"{rc}: {rv}")
                            step_expected = "; ".join(expected_parts) if expected_parts else ""
                        else:
                            step_expected = ""
                        step_expected = protect_formula(step_expected)

                        writer.writerow([
                            tc_counter,
                            "Test Case",
                            title,
                            step_num,
                            step_action,
                            step_expected,
                            "",  # Area Path
                            "",  # Assigned To
                            "New",
                        ])

            # Wenn keine Input-Schritte: eine Zeile mit leerem Schritt
            if step_num == 0:
                writer.writerow([
                    tc_counter,
                    "Test Case",
                    title,
                    1,
                    "",
                    "",
                    "",
                    "",
                    "New",
                ])

        return output.getvalue().encode("utf-8")

    def _count_input_steps(self, categories: list[str], result_categories: list[str],
                           assignments: dict) -> int:
        """Zaehlt die Anzahl nicht-Ergebnis-Kategorien mit Werten."""
        count = 0
        for cat in categories:
            if cat not in result_categories and assignments.get(cat, ""):
                count += 1
        return count