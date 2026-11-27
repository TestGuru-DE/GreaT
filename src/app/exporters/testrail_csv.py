"""REQ-6011: TestRail CSV Export.

Single-Row Layout: Ein Testfall = eine Zeile.

BUG A-11: Die erste Zeile ist der Spaltenkopf (keine Kommentarzeile);
Title beginnt mit der TC-ID.
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter, expected_result, protect_formula, sorted_testcases, testcase_tags, testcase_title


class TestRailCsvExporter(BaseExporter):
    """Export als TestRail CSV (Semikolon-Delimiter)."""

    name = "testrail-csv"
    file_extension = ".csv"
    media_type = "text/csv"

    def render(self, generation_view: dict, options: dict) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_ALL)
        writer.writerow(["Title", "Preconditions", "Steps", "Expected Result", "Error Value", "Origin"])

        categories = generation_view.get("categories", [])
        result_categories = generation_view.get("result_categories", [])

        for tc in sorted_testcases(generation_view.get("testcases", [])):
            inputs = [
                (cat, tc["assignments"].get(cat, ""))
                for cat in categories
                if cat not in result_categories and tc["assignments"].get(cat, "")
            ]
            steps = " ".join(f"{i}. Set {cat} to {val}." for i, (cat, val) in enumerate(inputs, start=1))
            writer.writerow([
                protect_formula(testcase_title(tc, categories, result_categories)),
                "",
                protect_formula(steps),
                protect_formula(expected_result(tc, result_categories)),
                # Restbefund 9b: Fehlerwert und Herkunft (als benutzerdefinierte Felder importierbar)
                "Yes" if tc.get("has_error_value") else "No",
                tc.get("origin") or "generated",
            ])

        return output.getvalue().encode("utf-8")
