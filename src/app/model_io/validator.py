"""REQ-6013: Validierung des GreatModel-Formats.

Prueft:
- Schema-Validierung (Pflichtfelder, Typen)
- Fachliche Regeln (Eindeutigkeit, Referenzen, Groesse)
- schemaVersion (aeltere werden migriert, neuere abgelehnt)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

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
    except Exception as e:
        errors.append(ValidationError(
            path="$",
            message=f"Pydantic-Validierung fehlgeschlagen: {e}",
        ))
        return errors  # Kein weitergehender Check bei strukturellen Fehlern

    # 5. Eindeutigkeit der Kategorienamen
    category_names = [c.name for c in model.categories]
    seen: set[str] = set()
    for name in category_names:
        if name in seen:
            errors.append(ValidationError(
                path=f"$.categories[].name",
                message=f"Doppelter Kategoriename: '{name}'",
            ))
        seen.add(name)

    # 6. Eindeutigkeit der Werte pro Kategorie
    for cat in model.categories:
        value_names = [v.value for v in cat.values]
        seen_values: set[str] = set()
        for val in value_names:
            if val in seen_values:
                errors.append(ValidationError(
                    path=f"$.categories[].name='{cat.name}'.values[].value",
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

    return errors