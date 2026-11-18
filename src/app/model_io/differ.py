"""REQ-6013: Aenderungsvorschau (Diff) zwischen bestehendem Projekt und Import-Modell.

Vergleicht das aktuelle Projekt mit dem zu importierenden Modell und
liefert eine Liste von hinzugefuegten, geaenderten und entfernten Elementen.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from sqlalchemy.orm import Session

from app import models
from app.logging_config import get_logger

from .exporter import export_model
from .models import GreatModel

log = get_logger(__name__)


def diff_model(
    db: Session,
    project_id: int,
    new_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Berechnet den Diff zwischen bestehendem Projekt und neuem Modell.

    Args:
        db: Datenbank-Session
        project_id: ID des bestehenden Projekts
        new_data: Dict mit dem neuen Modell (bereits validiert)

    Returns:
        Dict mit Struktur:
        {
            "added": {"categories": [...], "values": [...], "rules": [...]},
            "modified": {"categories": [...], "values": [...], "rules": [...]},
            "removed": {"categories": [...], "values": [...], "rules": [...]},
        }
    """
    # Aktuelles Modell exportieren
    current = export_model(db, project_id)

    # Neues Modell parsen
    from .serializers import parse_input
    try:
        new_model = GreatModel(**new_data)
    except Exception as e:
        raise ValueError(f"Ungueltiges Modell-Format: {e}")

    result = {
        "added": {"categories": [], "values": [], "rules": []},
        "modified": {"categories": [], "values": [], "rules": []},
        "removed": {"categories": [], "values": [], "rules": []},
    }

    # --- Kategorien ---
    current_cat_names: Set[str] = {c.name for c in current.categories}
    new_cat_names: Set[str] = {c.name for c in new_model.categories}

    # Hinzugefuegte Kategorien
    for name in new_cat_names - current_cat_names:
        result["added"]["categories"].append(name)

    # Entfernte Kategorien
    for name in current_cat_names - new_cat_names:
        result["removed"]["categories"].append(name)

    # --- Werte pro Kategorie ---
    for cat_name in current_cat_names & new_cat_names:
        current_cat = next((c for c in current.categories if c.name == cat_name), None)
        new_cat = next((c for c in new_model.categories if c.name == cat_name), None)

        if not current_cat or not new_cat:
            continue

        current_val_names: Set[str] = {v.value for v in current_cat.values}
        new_val_names: Set[str] = {v.value for v in new_cat.values}

        # Hinzugefuegte Werte
        for val_name in new_val_names - current_val_names:
            result["added"]["values"].append(f"{cat_name}/{val_name}")

        # Entfernte Werte
        for val_name in current_val_names - new_val_names:
            result["removed"]["values"].append(f"{cat_name}/{val_name}")

        # Geaenderte Werte (gleicher Name, aber andere Eigenschaften)
        for val_name in current_val_names & new_val_names:
            current_val = next((v for v in current_cat.values if v.value == val_name), None)
            new_val = next((v for v in new_cat.values if v.value == val_name), None)

            if current_val and new_val and _values_differ(current_val, new_val):
                result["modified"]["values"].append(f"{cat_name}/{val_name}")

    # Geaenderte Kategorien (gleicher Name, aber andere Eigenschaften)
    for cat_name in current_cat_names & new_cat_names:
        current_cat = next((c for c in current.categories if c.name == cat_name), None)
        new_cat = next((c for c in new_model.categories if c.name == cat_name), None)

        if current_cat and new_cat and _categories_differ(current_cat, new_cat):
            result["modified"]["categories"].append(cat_name)

    # --- Regeln ---
    current_rules_keyed = _key_rules(current.rules)
    new_rules_keyed = _key_rules(new_model.rules)

    current_rule_keys = set(current_rules_keyed.keys())
    new_rule_keys = set(new_rules_keyed.keys())

    # Hinzugefuegte Regeln
    for key in new_rule_keys - current_rule_keys:
        result["added"]["rules"].append(key)

    # Entfernte Regeln
    for key in current_rule_keys - new_rule_keys:
        result["removed"]["rules"].append(key)

    # Geaenderte Regeln
    for key in current_rule_keys & new_rule_keys:
        if current_rules_keyed[key] != new_rules_keyed[key]:
            result["modified"]["rules"].append(key)

    log.info(
        "model_diff_computed",
        project_id=project_id,
        added=len(result["added"]["categories"]) + len(result["added"]["values"]) + len(result["added"]["rules"]),
        modified=len(result["modified"]["categories"]) + len(result["modified"]["values"]) + len(result["modified"]["rules"]),
        removed=len(result["removed"]["categories"]) + len(result["removed"]["values"]) + len(result["removed"]["rules"]),
    )

    return result


def _values_differ(v1, v2) -> bool:
    """Prueft, ob zwei ModelValue-Objekte sich unterscheiden (außer value)."""
    return (
        v1.risk_weight != v2.risk_weight
        or v1.vtype != v2.vtype
        or v1.allowed != v2.allowed
        or v1.order_index != v2.order_index
        or v1.is_default != v2.is_default
    )


def _categories_differ(c1, c2) -> bool:
    """Prueft, ob zwei ModelCategory-Objekte sich unterscheiden (außer name/values)."""
    return (
        c1.order_index != c2.order_index
        or c1.is_result != c2.is_result
        or c1.category_type != c2.category_type
    )


def _key_rules(rules) -> Dict[str, Dict[str, Any]]:
    """Erstellt ein Dict von Regeln mit einem eindeutigen Key."""
    result = {}
    for rule in rules:
        key = f"{rule.type}:{rule.if_category_name}/{rule.if_value} -> {rule.then_category_name}/{rule.then_value}"
        result[key] = {
            "type": rule.type,
            "if_category_name": rule.if_category_name,
            "if_value": rule.if_value,
            "then_category_name": rule.then_category_name,
            "then_value": rule.then_value,
            "then_values_json": rule.then_values_json,
        }
    return result