"""REQ-6011: Azure DevOps Test Plans CSV Export.

Format nach Microsoft Learn "Bulk import or export test cases" (Azure Test Plans):
- Jeder Schritt = eigene Zeile; Work Item Type, Title usw. in jeder Zeile wiederholen,
  Test Step fortlaufend.
- BUG A-11: Spalte ID bleibt leer (neue Testfaelle). Eine Zahl wuerde als ID eines
  vorhandenen Work Items gelesen und dieses ueberschreiben.
- Komma als Trennzeichen (wie in allen Beispielen der Dokumentation), UTF-8,
  erste Zeile = Spaltenkopf, State "Design" (Standard fuer neue Testfaelle).
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, expected_result, protect_formula, sorted_testcases, testcase_title


class AzureDevOpsCsvExporter(BaseExporter):
    """Export als Azure DevOps CSV (Komma-Delimiter)."""

    name = "azuredevops-csv"
    file_extension = ".csv"
    media_type = "text/csv"

    HEADER = ["ID", "Work Item Type", "Title", "Test Step", "Step Action",
              "Step Expected", "Area Path", "Assigned To", "State"]

    def render(self, generation_view: dict, options: dict) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=",", lineterminator="\r\n", quoting=csv.QUOTE_ALL)
        writer.writerow(self.HEADER)

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])

        for tc in sorted_testcases(generation_view.get("testcases", [])):
            title = protect_formula(testcase_title(tc, categories, result_categories))
            inputs = [
                (cat, tc["assignments"].get(cat, ""))
                for cat in categories
                if cat not in result_categories and tc["assignments"].get(cat, "")
            ]
            expected = protect_formula(expected_result(tc, result_categories))
            steps = inputs or [None]  # ohne Eingaben: ein leerer Schritt
            for number, step in enumerate(steps, start=1):
                action = protect_formula(f"Set {step[0]} to {step[1]}") if step else ""
                writer.writerow([
                    "",            # ID leer = neuer Testfall
                    "Test Case",
                    title,
                    number,
                    action,
                    expected if number == len(steps) else "",  # Ergebnis am letzten Schritt
                    "",            # Area Path
                    "",            # Assigned To
                    "Design",
                ])

        return output.getvalue().encode("utf-8")
