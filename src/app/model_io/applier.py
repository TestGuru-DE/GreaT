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

from .models import GreatModel
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

    _apply_categories(db, project, model)
    _apply_rules(db, project, model)
    _apply_decision_constraints(db, project, model)

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

    db.flush()

    # Neue Kategorien/Werte/Regeln anlegen
    _apply_categories(db, project, model)
    _apply_rules(db, project, model)
    _apply_decision_constraints(db, project, model)

    db.commit()
    log.info("model_updated", project_id=project.id, project_name=project.name)
    return project


def _apply_categories(
    db: Session,
    project: models.Project,
    model: GreatModel,
) -> None:
    """Tragt Kategorien und Werte in die DB ein."""
    cat_name_to_id: dict[str, int] = {}

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


def _apply_rules(
    db: Session,
    project: models.Project,
    model: GreatModel,
) -> None:
    """Tragt Regeln in die DB ein (Referenzen ueber Namen -> IDs)."""
    # Kategorie-Namen -> IDs mappen
    cat_name_to_id: dict[str, int] = {}
    for cat in project.categories:
        cat_name_to_id[cat.name] = cat.id

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