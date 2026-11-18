"""REQ-6011: JSON Data-Driven Export.

Liste von Objekten fuer data-driven Tests (Playwright/Jest test.each, JUnit5 @MethodSource).
"""
from __future__ import annotations

import json

from .base import BaseExporter


class JsonDataDrivenExporter(BaseExporter):
    """Export als Liste von JSON-Objekten, eins pro Testfall."""

    name = "json-data-driven"
    file_extension = ".json"
    media_type = "application/json"

    def render(self, generation_view: dict, options: dict) -> bytes:
        testcases = generation_view.get("testcases", [])
        categories = generation_view.get("categories", [])

        result: list[dict] = []
        for tc in testcases:
            obj: dict = {
                "id": tc["name"],
                "has_error_value": tc.get("has_error_value", False),
            }
            for cat in categories:
                obj[cat] = tc["assignments"].get(cat, "")
            result.append(obj)

        return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")