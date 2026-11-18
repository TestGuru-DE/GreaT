"""REQ-6013: YAML/JSON-Serialisierung fuer GreatModel.

- YAML: PyYAML safe_load/safe_dump, custom Dumper ohne Aliases, Blockstil, sort_keys=False
- JSON: json.dumps mit sort_keys=False, ensure_ascii=False, indent=2
- Deterministisch: zweimal exportiert = byte-identisch
"""
from __future__ import annotations

import json
from typing import Any, Dict

import yaml

from .models import GreatModel, ModelCategory, ModelDecisionConstraint, ModelRule, ModelValue


# ---------------------------------------------------------------------------
# Custom YAML Dumper: keine Aliases, Blockstil, sort_keys=False
# ---------------------------------------------------------------------------

class _NoAliasDumper(yaml.SafeDumper):
    """Custom Dumper: unterdrueckt YAML-Anker/Aliases (&id / *ig)."""

    def ignore_aliases(self, data):
        """Deaktiviert Anker/Aliases fuer alle Objekte."""
        return True


def _repr_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Strings immer als Literal-Block (|) wenn sie Newlines enthalten, sonst Plain."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_NoAliasDumper.add_representer(str, _repr_str)


def _model_to_dict(model: GreatModel) -> Dict[str, Any]:
    """Konvertiert GreatModel zu einem serialisierbaren Dict.

    Verwendet camelCase-Keys fuer YAML/JSON (alias-Felder).
    """
    data = model.model_dump(by_alias=True, mode="json")
    return data


def to_yaml(model: GreatModel) -> str:
    """Serialisiert GreatModel als YAML-String.

    - Blockstil, keine Aliases, sort_keys=False
    - Zeilenende LF (Unix)
    - UTF-8 (als String zurueck)
    - Deterministisch: gleiche Eingabe -> gleiche Ausgabe
    """
    data = _model_to_dict(model)
    return yaml.dump(
        data,
        Dumper=_NoAliasDumper,
        default_flow_style=False,  # Blockstil
        sort_keys=False,           # feste Reihenfolge aus model_dump
        allow_unicode=True,
        width=120,
        indent=2,
    ).rstrip() + "\n"


def from_yaml(yaml_str: str) -> GreatModel:
    """Parsert YAML-String zu GreatModel."""
    data = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return GreatModel(**data)


def to_json(model: GreatModel) -> str:
    """Serialisiert GreatModel als JSON-String.

    - ensure_ascii=False, indent=2
    - sort_keys=False (feste Reihenfolge aus model_dump)
    - Deterministisch: gleiche Eingabe -> gleiche Ausgabe
    """
    data = _model_to_dict(model)
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def from_json(json_str: str) -> GreatModel:
    """Parsert JSON-String zu GreatModel."""
    data = json.loads(json_str)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return GreatModel(**data)


def parse_input(content: str, format: str) -> GreatModel:
    """Parsert Eingabe basierend auf Format (yaml/json/dict)."""
    if format == "yaml":
        return from_yaml(content)
    elif format == "json":
        return from_json(content)
    elif format == "dict":
        # content is actually a dict passed directly
        if isinstance(content, dict):
            return GreatModel(**content)
        raise ValueError("dict format requires a dict, not a string")
    else:
        raise ValueError(f"Unknown format: {format}")