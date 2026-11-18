"""REQ-6013: Export eines Projekts als GreatModel.

Liest alle Daten aus der DB und erzeugt ein GreatModel-Objekt.
Nicht enthalten: Generierungen, Benutzer, IDs, Zeitstempel.
Referenzen ueber Namen (Kategoriename, Wertname), nicht IDs.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models
from app.logging_config import get_logger

from .models import GreatModel, ModelCategory, ModelRule, ModelValue

log = get_logger(__name__)


def export_model(db: Session, project_id: int) -> GreatModel:
    """Exportiert ein Projekt als GreatModel.

    Args:
        db: Datenbank-Session
        project_id: ID des zu exportierenden Projekts

    Returns:
        GreatModel-Objekt mit allen Kategorien, Werten und Regeln.

    Raises:
        ValueError: Wenn Projekt nicht existiert.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Kategorie-ID -> Name Mapping
    cat_id_to_name: dict[int, str] = {}

    # Kategorien exportieren
    categories = []
    for cat in sorted(project.categories, key=lambda c: c.order_index):
        cat_id_to_name[cat.id] = cat.name

        cat_values = []
        for val in sorted(cat.values, key=lambda v: v.order_index):
            cat_values.append(ModelValue(
                value=val.value,
                risk_weight=val.risk_weight,
                vtype=val.vtype,
                allowed=val.allowed,
                order_index=val.order_index,
                is_default=val.is_default,
            ))

        categories.append(ModelCategory(
            name=cat.name,
            order_index=cat.order_index,
            is_result=cat.is_result,
            category_type=cat.category_type,
            values=cat_values,
        ))

    # Regeln exportieren (Referenzen ueber Namen)
    rules = []
    for rule in project.rules:
        if_cat_name = cat_id_to_name.get(rule.if_category_id, "")
        then_cat_name = cat_id_to_name.get(rule.then_category_id, "")

        if not if_cat_name or not then_cat_name:
            log.warning(
                "Rule %d references missing category, skipping",
                rule.id,
            )
            continue

        rules.append(ModelRule(
            type=rule.type,
            if_category_name=if_cat_name,
            if_value=rule.if_value,
            then_category_name=then_cat_name,
            then_value=rule.then_value or "",
            then_values_json=rule.then_values_json,
        ))

    # Decision Constraints (optional)
    from app.models.decision_table_constraint import DecisionTableConstraint
    from .models import ModelDecisionConstraint

    decision_constraints = []
    constraints = db.query(DecisionTableConstraint).filter(
        DecisionTableConstraint.project_id == project_id
    ).all()
    for dc in constraints:
        decision_constraints.append(ModelDecisionConstraint(
            constraint_type=dc.constraint_type,
            targets=dc.targets or {},
            description=dc.description,
        ))

    result = GreatModel(
        schema_version=1,
        project_name=project.name,
        categories=categories,
        rules=rules,
        decision_constraints=decision_constraints,
    )

    log.info("model_exported", project_id=project_id, project_name=project.name)
    return result