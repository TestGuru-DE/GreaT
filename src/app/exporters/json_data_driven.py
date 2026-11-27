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

        # Restbefund 9b: Eine Kategorie namens "id" (o. ae.) ueberschrieb die Testfall-ID.
        # Metadaten behalten ihre Namen; kollidierende Kategorien erhalten einen Suffix.
        reserved = {"id", "has_error_value", "origin"}
        keys: dict[str, str] = {}
        for cat in categories:
            key, n = cat, 2
            while key in reserved or key in keys.values():
                key = f"{cat} ({n})"
                n += 1
            keys[cat] = key

        result: list[dict] = []
        for tc in testcases:
            obj: dict = {
                "id": tc["name"],
                "has_error_value": tc.get("has_error_value", False),
                "origin": tc.get("origin") or "generated",
            }
            for cat in categories:
                obj[keys[cat]] = tc["assignments"].get(cat, "")
            result.append(obj)

        return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")