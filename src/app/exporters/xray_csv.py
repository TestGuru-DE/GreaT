"""REQ-6011: Xray (Jira) CSV Export.

Ein Testfall = eine Zeile. Spalten nach Xray-Testimport.

BUG A-11: Die erste Zeile ist der Spaltenkopf (keine Kommentarzeile, die der
Importer als Kopf lesen wuerde); Summary beginnt mit der TC-ID.
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, expected_result, protect_formula, sorted_testcases, testcase_tags, testcase_title


class XrayCsvExporter(BaseExporter):
    """Export als Xray CSV (Semikolon-Delimiter)."""

    name = "xray-csv"
    file_extension = ".csv"
    media_type = "text/csv"

    def render(self, generation_view: dict, options: dict) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_ALL)
        writer.writerow([
            "Test Case Identifier", "Summary", "Action", "Data",
            "Expected Result", "Preconditions", "Test Type", "Labels",
        ])

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])

        for tc in sorted_testcases(generation_view.get("testcases", [])):
            data = ", ".join(
                f"{cat}: {tc['assignments'].get(cat, '')}"
                for cat in categories
                if cat not in result_categories and tc["assignments"].get(cat, "")
            )
            writer.writerow([
                protect_formula(tc["name"]),
                protect_formula(testcase_title(tc, categories, result_categories)),
                "Execute test",
                protect_formula(data),
                protect_formula(expected_result(tc, result_categories)),
                "",  # Preconditions
                "Manual",
                " ".join(testcase_tags(tc)),  # Restbefund 9b: Fehlerwert/Herkunft als Jira-Labels
            ])

        return output.getvalue().encode("utf-8")
