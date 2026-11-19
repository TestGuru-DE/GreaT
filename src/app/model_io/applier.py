"""REQ-6013: Import/Aktualisierung eines Projekts aus GreatModel.

- Als neues Projekt: Name aus Datei, bei Konflikt Suffix
- Als Aktualisierung: Transaktion, bestehende Generierungen bleiben
- Fehler -> Rollback, nichts wird geaendert
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app import models
from app.logging_config import get_logger

from .models import GreatModel, ModelConstraint
from .serializers import parse_input

log = get_logger(__name__)


def apply_model(
    db: Session,
    project_id: Optional[int],
    content: str | Dict[str, Any],
    format: str = "yaml",
) -> models.Project:
    """Importiert oder aktualisiert ein Projekt aus einem Modell.

    Args:
        db: Datenbank-Session
        project_id: None fuer neues Projekt, ID fuer Aktualisierung
        content: YAML/JSON-String oder Dict
        format: "yaml", "json" oder "dict"

    Returns:
        Das importierte/aktualisierte Projekt.

    Raises:
        ValueError: Bei Validierungsfehlern oder fehlendem Projekt.
    """
    # Modell parsen
    if isinstance(content, dict):
        model = GreatModel(**content)
    else:
        model = parse_input(content, format)

    # Validieren
    from .validator import validate_model
    errors = validate_model(model.model_dump(mode="json"))
    if errors:
        error_msgs = [f"{e.path}: {e.message}" for e in errors]
        raise ValueError(f"Modell-Validierung fehlgeschlagen: {'; '.join(error_msgs)}")

    if project_id is None:
        return _create_new_project(db, model)
    else:
        return _update_existing_project(db, project_id, model)


def _create_new_project(db: Session, model: GreatModel) -> models.Project:
    """Erstellt ein neues Projekt aus dem Modell.

    Bei Namenskonflikt: Suffix _imported_{n}.
    """
    name = model.project_name

    # Namenskonflikt-Handling
    existing = db.query(models.Project).filter(models.Project.name == name).first()
    if existing:
        counter = 1
        while True:
            candidate = f"{name}_imported_{counter}"
            if not db.query(models.Project).filter(models.Project.name == candidate).first():
                name = candidate
                break
            counter += 1
            if counter > 100:
                raise ValueError(f"Zu viele Konflikte fuer Projekt '{name}'")

    project = models.Project(name=name)
    db.add(project)
    db.flush()

    cat_name_to_id, catval_to_id = _apply_categories(db, project, model)
    _apply_rules(db, project, model, cat_name_to_id)
    _apply_decision_constraints(db, project, model)
    _apply_constraints(db, project, model, cat_name_to_id, catval_to_id)

    db.commit()
    log.info("model_imported_new", project_id=project.id, project_name=project.name)
    return project


def _update_existing_project(
    db: Session,
    project_id: int,
    model: GreatModel,
) -> models.Project:
    """Aktualisiert ein bestehendes Projekt aus dem Modell.

    - Bestehende Generierungen bleiben unveraendert (Historie)
    - Kategorien/Werte/Regeln werden synchronisiert
    - Transaktion: bei Fehler -> Rollback
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Projektname aktualisieren (falls geaendert)
    project.name = model.project_name

    # Bestehende Kategorien loeschen (wird durch neue ersetzt)
    for cat in project.categories:
        for val in cat.values:
            db.delete(val)
        db.delete(cat)

    # Bestehende Regeln loeschen
    for rule in project.rules:
        db.delete(rule)

    # Bestehende Decision Constraints loeschen
    from app.models.decision_table_constraint import DecisionTableConstraint
    db.query(DecisionTableConstraint).filter(
        DecisionTableConstraint.project_id == project_id
    ).delete(synchronize_session=False)

    # REQ-6001 AK-10: Bestehende Constraints loeschen
    db.query(models.Constraint).filter(
        models.Constraint.project_id == project_id
    ).delete(synchronize_session=False)

    db.flush()

    # Neue Kategorien/Werte/Regeln anlegen
    cat_name_to_id, catval_to_id = _apply_categories(db, project, model)
    _apply_rules(db, project, model, cat_name_to_id)
    _apply_decision_constraints(db, project, model)
    _apply_constraints(db, project, model, cat_name_to_id, catval_to_id)

    db.commit()
    log.info("model_updated", project_id=project.id, project_name=project.name)
    return project


def _apply_categories(
    db: Session,
    project: models.Project,
    model: GreatModel,
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """Tragt Kategorien und Werte in die DB ein.
    
    Returns:
        (cat_name_to_id, catval_to_id) Mappings fuer nachfolgende Funktionen.
    """
    cat_name_to_id: dict[str, int] = {}
    catval_to_id: dict[tuple[str, str], int] = {}

    for cat_data in model.categories:
        cat = models.Category(
            name=cat_data.name,
            project_id=project.id,
            order_index=cat_data.order_index,
            is_result=cat_data.is_result,
            category_type=cat_data.category_type,
        )
        db.add(cat)
        db.flush()
        cat_name_to_id[cat_data.name] = cat.id

        for val_data in cat_data.values:
            val = models.Value(
                value=val_data.value,
                category_id=cat.id,
                risk_weight=val_data.risk_weight,
                vtype=val_data.vtype,
                allowed=val_data.allowed,
                order_index=val_data.order_index,
                is_default=val_data.is_default,
            )
            db.add(val)
            db.flush()
            catval_to_id[(cat_data.name, val_data.value)] = val.id

    return cat_name_to_id, catval_to_id


def _apply_rules(
    db: Session,
    project: models.Project,
    model: GreatModel,
    cat_name_to_id: dict[str, int],
) -> None:
    """Tragt Regeln in die DB ein (Referenzen ueber Namen -> IDs)."""
    for rule_data in model.rules:
        if_cat_id = cat_name_to_id.get(rule_data.if_category_name)
        then_cat_id = cat_name_to_id.get(rule_data.then_category_name)

        if not if_cat_id or not then_cat_id:
            log.warning(
                "Rule references missing category, skipping: %s",
                rule_data.if_category_name,
            )
            continue

        rule = models.Rule(
            project_id=project.id,
            type=rule_data.type,
            if_category_id=if_cat_id,
            if_value=rule_data.if_value,
            then_category_id=then_cat_id,
            then_value=rule_data.then_value or "",
            then_values_json=rule_data.then_values_json,
        )
        db.add(rule)


def _apply_decision_constraints(
    db: Session,
    project: models.Project,
    model: GreatModel,
) -> None:
    """Tragt Decision Constraints in die DB ein (optional, EPIC-20)."""
    from app.models.decision_table_constraint import DecisionTableConstraint

    for dc_data in model.decision_constraints:
        dc = DecisionTableConstraint(
            project_id=project.id,
            constraint_type=dc_data.constraint_type,
            targets=dc_data.targets or {},
            description=dc_data.description,
        )
        db.add(dc)


# ---------------------------------------------------------------------------
# REQ-6001 AK-10: Constraints import (Namen -> IDs)
# ---------------------------------------------------------------------------

def _apply_constraints(
    db: Session,
    project: models.Project,
    model: GreatModel,
    cat_name_to_id: dict[str, int],
    catval_to_id: dict[tuple[str, str], int],
) -> None:
    """Tragt Constraints in die DB ein (Referenzen ueber Namen -> IDs)."""

    def _resolve_expression(expr: dict) -> dict:
        """Konvertiert category_name/value_name zurueck zu category_id/value_id."""
        if not isinstance(expr, dict):
            return expr
        resolved = {}
        for k, v in expr.items():
            if k == "category_name" and isinstance(v, str):
                cat_id = cat_name_to_id.get(v)
                if cat_id is None:
                    log.warning("Constraint references unknown category '%s', skipping", v)
                    resolved[k] = None
                else:
                    resolved["category_id"] = cat_id
                continue
            if k == "value_name" and isinstance(v, str):
                # value_name allein ist nicht eindeutig; brauche category_name aus Parent
                # -> wird im aufrufenden Kontext geloescht
                resolved[k] = v
                continue
            if k == "value_names" and isinstance(v, list):
                resolved[k] = v
                continue
            if isinstance(v, dict):
                resolved[k] = _resolve_expression(v)
            elif isinstance(v, list):
                resolved[k] = [_resolve_expression(item) if isinstance(item, dict) else item for item in v]
            else:
                resolved[k] = v
        return resolved

    def _resolve_value_ids(expr: dict, parent_cat_name: str | None = None) -> dict:
        """Nachbearbeitung: value_name/value_names -> value_id/value_ids mit Kategorie-Kontext."""
        if not isinstance(expr, dict):
            return expr
        resolved = {}
        current_cat = parent_cat_name
        for k, v in expr.items():
            if k == "category_id" and isinstance(v, str):
                # Im Export ist category_id als Name gespeichert -> zurueck zu ID
                cat_id = cat_name_to_id.get(v)
                if cat_id is not None:
                    resolved["category_id"] = cat_id
                    current_cat = v
                else:
                    resolved["category_id"] = None
                continue
            if k == "category_id" and isinstance(v, int):
                # Bereits eine ID -> direkt uebernehmen und Kategoriename ermitteln
                resolved["category_id"] = v
                for cn, cid in cat_name_to_id.items():
                    if cid == v:
                        current_cat = cn
                        break
                continue
            if k == "category_name" and isinstance(v, str):
                current_cat = v
                if "category_id" not in resolved:
                    cat_id = cat_name_to_id.get(v)
                    if cat_id is not None:
                        resolved["category_id"] = cat_id
                continue
            if k == "value_id" and isinstance(v, str) and current_cat:
                val_id = catval_to_id.get((current_cat, v))
                if val_id is not None:
                    resolved["value_id"] = val_id
                else:
                    log.warning("Constraint references unknown value '%s' in category '%s'", v, current_cat)
                    resolved["value_id"] = None
                continue
            if k == "value_ids" and isinstance(v, list) and current_cat:
                val_ids = []
                for vn in v:
                    vid = catval_to_id.get((current_cat, vn))
                    if vid is not None:
                        val_ids.append(vid)
                    else:
                        log.warning("Constraint references unknown value '%s' in category '%s'", vn, current_cat)
                        val_ids.append(None)
                resolved["value_ids"] = val_ids
                continue
            # Uebrige Felder (op, kind, condition, consequence, args, arg)
            if isinstance(v, dict):
                child = _resolve_value_ids(v, current_cat)
                resolved[k] = child
                # Wenn das Kind eine category_id hat, aktualisiere current_cat fuer Geschwister
                if isinstance(child, dict) and "category_id" in child and isinstance(child["category_id"], int):
                    for cn, cid in cat_name_to_id.items():
                        if cid == child["category_id"]:
                            current_cat = cn
                            break
            elif isinstance(v, list):
                resolved[k] = [_resolve_value_ids(item, current_cat) if isinstance(item, dict) else item for item in v]
            else:
                resolved[k] = v
        return resolved

    for c_data in model.constraints:
        expr_raw = c_data.expression
        if not isinstance(expr_raw, dict):
            log.warning("Constraint '%s' has non-dict expression, skipping", c_data.name)
            continue

        # Schritt 1: category_name -> category_id + value_name -> value_id
        expr_resolved = _resolve_value_ids(expr_raw)

        # Pruefen ob alle category_id gueltig sind (None = nicht gefunden)
        def _has_none_ids(e: Any) -> bool:
            if not isinstance(e, dict):
                return False
            # Direkte ID-Felder pruefen
            if "category_id" in e and e["category_id"] is None:
                return True
            if "value_id" in e and e["value_id"] is None:
                return True
            if "value_ids" in e and isinstance(e["value_ids"], list) and None in e["value_ids"]:
                return True
            # Rekursiv in alle Werte
            for v in e.values():
                if _has_none_ids(v):
                    return True
            return False

        if _has_none_ids(expr_resolved):
            log.warning("Constraint '%s' has unresolved references, marking invalid", c_data.name)
            import json as json_mod
            c = models.Constraint(
                project_id=project.id,
                name=c_data.name,
                kind=c_data.kind,
                expression_json=json_mod.dumps(expr_resolved, ensure_ascii=False),
                is_valid=False,
            )
        else:
            import json as json_mod2
            c = models.Constraint(
                project_id=project.id,
                name=c_data.name,
                kind=c_data.kind,
                expression_json=json_mod2.dumps(expr_resolved, ensure_ascii=False),
                is_valid=c_data.is_valid,
            )
        db.add(c)