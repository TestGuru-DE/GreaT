"""REQ-6011: Exporter-Registry.

Zentrale Registrierung aller Export-Formate.
"""
from __future__ import annotations

from .base import BaseExporter

exporters: dict[str, BaseExporter] = {}


def register_exporter(exp: BaseExporter) -> None:
    """Registriert einen Exporter unter seinem Namen."""
    exporters[exp.name] = exp


def get_exporter(name: str) -> BaseExporter | None:
    """Gibt einen Exporter fuer den gegebenen Formatnamen zurueck."""
    return exporters.get(name)


# ---------------------------------------------------------------------------
# Import und Registrierung aller Exporter
# ---------------------------------------------------------------------------

# Automatisierung
from .gherkin import GherkinExporter
register_exporter(GherkinExporter())

from .pytest_exporter import PytestExporter
register_exporter(PytestExporter())

from .json_data_driven import JsonDataDrivenExporter
register_exporter(JsonDataDrivenExporter())

from .robot import RobotExporter
register_exporter(RobotExporter())

# Testmanagement
from .xray_csv import XrayCsvExporter
register_exporter(XrayCsvExporter())

from .testrail_csv import TestRailCsvExporter
register_exporter(TestRailCsvExporter())

from .azuredevops_csv import AzureDevOpsCsvExporter
register_exporter(AzureDevOpsCsvExporter())

# Tabellen
from .markdown import MarkdownExporter
register_exporter(MarkdownExporter())