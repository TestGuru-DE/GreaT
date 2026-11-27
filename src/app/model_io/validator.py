"""REQ-6013: Validierung des GreatModel-Formats.

Prueft:
- Schema-Validierung (Pflichtfelder, Typen)
- Fachliche Regeln (Eindeutigkeit, Referenzen, Groesse)
- schemaVersion (aeltere werden migriert, neuere abgelehnt)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from pydantic import ValidationError as PydanticValidationError

from .models import GreatModel

# Hoechste unterstuetzte Schema-Version
MAX_SUPPORTED_SCHEMA_VERSION = 1

# Maximalgroesse in Bytes (5 MB)
MAX_MODEL_SIZE_BYTES = 5 * 1024 * 1024


class ValidationError:
    """Ein Validierungsfehler mit Pfad und Nachricht."""

    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"path": self.path, "message": self.message}

    def __repr__(self) -> str:
        return f"ValidationError(path={self.path!r}, message={self.message!r})"


def validate_model(data: Dict[str, Any]) -> List[ValidationError]:
    """Validiert ein Modell-Dict gegen Schema und fachliche Regeln.

    Args:
        data: Dict mit Modell-Daten (kann aus JSON/YAML stammen)

    Returns:
        Liste von ValidationError-Objekten. Leer wenn gueltig.
    """
    errors: List[ValidationError] = []

    # 1. Groessenpruefung
    size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    if size > MAX_MODEL_SIZE_BYTES:
        errors.append(ValidationError(
            path="$",
            message=f"Modell zu gross: {size} bytes (max {MAX_MODEL_SIZE_BYTES})",
        ))
        return errors  # Kein weiterer Check bei zu grossen Daten

    # 2. schemaVersion-Pruefung
    schema_version = data.get("schemaVersion", data.get("schema_version"))
    if schema_version is None:
        errors.append(ValidationError(
            path="$.schemaVersion",
            message="schemaVersion ist erforderlich",
        ))
    elif not isinstance(schema_version, int):
        errors.append(ValidationError(
            path="$.schemaVersion",
            message=f"schemaVersion muss eine Zahl sein, ist {type(schema_version).__name__}",
        ))
    elif schema_version > MAX_SUPPORTED_SCHEMA_VERSION:
        errors.append(ValidationError(
            path="$.schemaVersion",
            message=f"schemaVersion {schema_version} wird nicht unterstuetzt (max {MAX_SUPPORTED_SCHEMA_VERSION})",
        ))
    elif schema_version < 1:
        errors.append(ValidationError(
            path="$.schemaVersion",
            message=f"schemaVersion muss >= 1 sein, ist {schema_version}",
        ))

    # 3. projectName-Pruefung
    project_name = data.get("projectName", data.get("project_name"))
    if not project_name:
        errors.append(ValidationError(
            path="$.projectName",
            message="projectName ist erforderlich",
        ))
    elif not isinstance(project_name, str):
        errors.append(ValidationError(
            path="$.projectName",
            message=f"projectName muss ein String sein, ist {type(project_name).__name__}",
        ))
    elif len(project_name) > 200:
        errors.append(ValidationError(
            path="$.projectName",
            message=f"projectName darf max. 200 Zeichen haben, hat {len(project_name)}",
        ))

    # 4. Pydantic-Validierung (fuer Typen und Struktur)
    try:
        model = GreatModel(**data)
    except PydanticValidationError as e:
        # Restbefund 9b: Pfad mit Index statt nur "$"
        for err in e.errors():
            loc = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in err["loc"])
            errors.append(ValidationError(path="$" + loc, message=err["msg"]))
        return errors
    except Exception as e:
        errors.append(ValidationError(
            path="$",
            message=f"Pydantic-Validierung fehlgeschlagen: {e}",
        ))
        return errors  # Kein weitergehender Check bei strukturellen Fehlern

    # 5. Eindeutigkeit der Kategorienamen (BUG A-13: ohne Gross-/Kleinschreibung,
    #    sonst schlaegt das Generieren spaeter mit 409 fehl)
    seen: set[str] = set()
    for idx, name in enumerate(c.name for c in model.categories):
        if name.casefold() in seen:
            errors.append(ValidationError(
                path=f"$.categories[{idx}].name",
                message=f"Doppelter Kategoriename: '{name}'",
            ))
        seen.add(name.casefold())

    # 6. Eindeutigkeit der Werte pro Kategorie
    for cat_idx, cat in enumerate(model.categories):
        value_names = [v.value for v in cat.values]
        seen_values: set[str] = set()
        for val_idx, val in enumerate(value_names):
            if val in seen_values:
                errors.append(ValidationError(
                    path=f"$.categories[{cat_idx}].values[{val_idx}].value",
                    message=f"Doppelter Wert '{val}' in Kategorie '{cat.name}'",
                ))
            seen_values.add(val)

    # 7. Referenz-Validierung fuer Regeln
    cat_name_set = {c.name for c in model.categories}
    for i, rule in enumerate(model.rules):
        if rule.if_category_name not in cat_name_set:
            errors.append(ValidationError(
                path=f"$.rules[{i}].ifCategoryName",
                message=f"Kategorie '{rule.if_category_name}' existiert nicht",
            ))
        if rule.then_category_name not in cat_name_set:
            errors.append(ValidationError(
                path=f"$.rules[{i}].thenCategoryName",
                message=f"Kategorie '{rule.then_category_name}' existiert nicht",
            ))

        # Wert-Referenz pruefen
        if rule.if_category_name in cat_name_set:
            cat = next((c for c in model.categories if c.name == rule.if_category_name), None)
            if cat:
                val_set = {v.value for v in cat.values}
                if rule.if_value not in val_set:
                    errors.append(ValidationError(
                        path=f"$.rules[{i}].ifValue",
                        message=f"Wert '{rule.if_value}' existiert nicht in Kategorie '{rule.if_category_name}'",
                    ))

        if rule.then_category_name in cat_name_set:
            cat = next((c for c in model.categories if c.name == rule.then_category_name), None)
            if cat:
                val_set = {v.value for v in cat.values}
                if rule.then_value and rule.then_value not in val_set:
                    errors.append(ValidationError(
                        path=f"$.rules[{i}].thenValue",
                        message=f"Wert '{rule.then_value}' existiert nicht in Kategorie '{rule.then_category_name}'",
                    ))

    # 8. BUG A-13: Referenzen in Seed-Saetzen (Constraints mit falschen Referenzen
    #    werden nach REQ-6001 AK-10 nicht abgelehnt, sondern als ungueltig importiert)
    values_by_cat = {c.name: {v.value for v in c.values} for c in model.categories}
    for i, seed_set in enumerate(model.seed_sets):
        for j, case in enumerate(seed_set.cases):
            for cat_name, value in case.items():
                path = f"$.seedSets[{i}].cases[{j}]"
                if cat_name not in values_by_cat:
                    errors.append(ValidationError(path, f"Kategorie '{cat_name}' existiert nicht"))
                elif value is not None and value not in values_by_cat[cat_name]:
                    errors.append(ValidationError(
                        path, f"Wert '{value}' existiert nicht in Kategorie '{cat_name}'"))

    return errors


def constraint_reference_errors(expr: Any, values_by_cat: Dict[str, set], path: str) -> List[ValidationError]:
    """BUG A-13: Jede Kategorie- und Wertreferenz eines Constraints muss im Modell existieren.

    Referenzen erfolgen ueber Namen (`category_id`/`category_name` = Kategoriename,
    `value_id`/`value_name`/`value_ids`/`value_names` = Wertname). Zahlen-IDs sind in
    einer Modelldatei bedeutungslos und werden abgelehnt.
    """
    errors: List[ValidationError] = []
    if isinstance(expr, list):
        for k, item in enumerate(expr):
            errors.extend(constraint_reference_errors(item, values_by_cat, f"{path}[{k}]"))
        return errors
    if not isinstance(expr, dict):
        return errors

    cat_ref = expr.get("category_id", expr.get("category_name"))
    category = None
    if cat_ref is not None:
        if not isinstance(cat_ref, str):
            errors.append(ValidationError(path, "Kategorien werden ueber ihren Namen referenziert, nicht ueber eine ID"))
        elif cat_ref not in values_by_cat:
            errors.append(ValidationError(path, f"Kategorie '{cat_ref}' existiert nicht"))
        else:
            category = cat_ref

    value_refs: list = []
    for key in ("value_id", "value_name"):
        if key in expr:
            value_refs.append(expr[key])
    for key in ("value_ids", "value_names"):
        if isinstance(expr.get(key), list):
            value_refs.extend(expr[key])
    for ref in value_refs:
        if not isinstance(ref, str):
            errors.append(ValidationError(path, "Werte werden ueber ihren Namen referenziert, nicht ueber eine ID"))
        elif cat_ref is None:
            errors.append(ValidationError(path, f"Wert '{ref}' ohne Kategorie"))
        elif category is not None and ref not in values_by_cat[category]:
            errors.append(ValidationError(path, f"Wert '{ref}' existiert nicht in Kategorie '{category}'"))

    for key, child in expr.items():
        if isinstance(child, (dict, list)) and key not in ("value_ids", "value_names"):
            errors.extend(constraint_reference_errors(child, values_by_cat, f"{path}.{key}"))
    return errors
