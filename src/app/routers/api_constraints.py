"""
REQ-6001: CRUD API Endpunkte fuer logische Constraints.

Endpunkte unter /api/v1/projects/{project_id}/constraints/:
- GET / – Alle Constraints eines Projekts listen
- POST / – Neues Constraint anlegen
- GET /{constraint_id} – Einzelnes Constraint lesen
- PUT /{constraint_id} – Constraint aktualisieren
- DELETE /{constraint_id} – Constraint loeschen
- POST /validate – AST validieren ohne zu speichern
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer
from .. import models, schemas
from ..constraints.ast_parser import validate_ast, count_leaf_nodes, MAX_LEAF_NODES
from ..constraints.evaluator_3vl import check_unsatisfiable

log = logging.getLogger("great.api.constraints")

router = APIRouter(tags=["Constraints"], dependencies=[Depends(require_api_capable)])


def _parse_expression(expression_json: str) -> dict:
    """Liest expression_json aus DB und gibt dict zurueck."""
    if not expression_json:
        return {}
    return json.loads(expression_json)


def _constraint_to_read(c: models.Constraint) -> schemas.ConstraintRead:
    """Konvertiert ein Constraint-Modell ins Read-Schema."""
    return schemas.ConstraintRead(
        id=c.id,
        project_id=c.project_id,
        name=c.name,
        kind=c.kind,
        expression=_parse_expression(c.expression_json),
        is_valid=c.is_valid,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
        warnings=[],  # Default leer; wird bei POST/PUT durch check_unsatisfiable gefuellt
    )


def _load_categories_with_values(project_id: int, db: Session) -> Dict[int, dict]:
    """Ladet alle Kategorien mit Werten eines Projekts als Dict.

    Returns:
        {category_id: {"name": str, "values": {value_id: value_name}}}
    """
    result: Dict[int, dict] = {}
    categories = (
        db.query(models.Category)
        .filter(models.Category.project_id == project_id)
        .all()
    )
    for cat in categories:
        values = (
            db.query(models.Value)
            .filter(models.Value.category_id == cat.id)
            .all()
        )
        result[cat.id] = {
            "name": cat.name,
            "values": {v.id: v.value for v in values},
        }
    return result


def _load_existing_constraints(project_id: int, db: Session) -> List[dict]:
    """Ladet alle gueltigen Constraints eines Projekts als AST-Liste."""
    constraints = (
        db.query(models.Constraint)
        .filter(
            models.Constraint.project_id == project_id,
            models.Constraint.is_valid == True,  # noqa: E712
        )
        .all()
    )
    return [_parse_expression(c.expression_json) for c in constraints
            if c.expression_json]


def _run_unsatisfiable_check(
    project_id: int,
    new_constraint_ast: dict,
    exclude_constraint_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> List[str]:
    """REQ-6001 AK-8: Fuehrt die Widerspruchspruefung aus.

    Args:
        project_id: Projekt-ID
        new_constraint_ast: Neues Constraint-AST
        exclude_constraint_id: Wenn gesetzt, wird dieses Constraint aus
            den bestehenden Constraints ausgeschlossen (fuer PUT-Updates)
        db: DB-Session (wird fuer Kategorien/Constraints geladen)

    Returns:
        Liste von Warnstrings (leer wenn keine Warnung)
    """
    if db is None:
        return []

    try:
        categories = _load_categories_with_values(project_id, db)
        existing = _load_existing_constraints(project_id, db)

        # Bei PUT: das aktualisierte Constraint aus der bestehenden Liste entfernen
        if exclude_constraint_id is not None:
            existing = [
                c for c in existing
                if json.loads(c.get("expression_json", "{}") if isinstance(c, models.Constraint) else "{}").get("_id") != exclude_constraint_id
            ]
            # Einfacher: alle existing Constraints laden und das mit exclude_id entfernen
            # Da wir JSON-ASTs haben, muessen wir anders vorgehen
            # Die existing-Liste enthaelt bereits geparste ASTs ohne ID-Info
            # -> Wir laden die Constraints mit ID und filtern
            existing_raw = (
                db.query(models.Constraint)
                .filter(
                    models.Constraint.project_id == project_id,
                    models.Constraint.is_valid == True,  # noqa: E712
                    models.Constraint.id != exclude_constraint_id,
                )
                .all()
            )
            existing = [_parse_expression(c.expression_json) for c in existing_raw
                       if c.expression_json]

        is_unsat, warnings = check_unsatisfiable(categories, new_constraint_ast, existing)
        return warnings
    except Exception as e:
        log.warning("Unsatisfiable check failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{project_id}/constraints/
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/constraints", response_model=List[schemas.ConstraintRead])
def list_constraints(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Alle gueltigen Constraints eines Projekts listen (sortiert nach Name)."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    constraints = (
        db.query(models.Constraint)
        .filter(
            models.Constraint.project_id == project_id,
            models.Constraint.is_valid == True,  # noqa: E712
        )
        .order_by(models.Constraint.name)
        .all()
    )
    return [_constraint_to_read(c) for c in constraints]


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{project_id}/constraints/
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/constraints", response_model=schemas.ConstraintRead, status_code=201, dependencies=[Depends(require_writer)])
def create_constraint(
    project_id: int,
    payload: schemas.ConstraintCreate,
    db: Session = Depends(get_db),
):
    """Neues Constraint anlegen mit AST-Validierung."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # AST validieren
    ast_dict = {
        "kind": payload.kind,
        "condition": payload.expression,
    }
    if payload.kind == "implies":
        if payload.consequence is None:
            raise HTTPException(
                status_code=400,
                detail={"message": "implies-Constraints brauchen ein 'consequence'-Feld"},
            )
        ast_dict["consequence"] = payload.consequence
    elif payload.consequence is not None:
        raise HTTPException(
            status_code=400,
            detail={"message": "forbid-Constraints duerfen kein 'consequence'-Feld haben"},
        )

    is_valid, errors = validate_ast(ast_dict)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ungueltiges Constraint-AST",
                "errors": errors,
            },
        )

    # Leaf-count pruefen
    leaf_count = count_leaf_nodes(ast_dict)
    if leaf_count > MAX_LEAF_NODES:
        raise HTTPException(
            status_code=400,
            detail=f"Zu viele atomare Vergleiche: {leaf_count} (max {MAX_LEAF_NODES})",
        )

    # Constraint anlegen (komplettes AST speichern)
    constraint = models.Constraint(
        project_id=project_id,
        name=payload.name,
        kind=payload.kind,
        expression_json=json.dumps(ast_dict, ensure_ascii=False),
        is_valid=True,
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)

    # REQ-6001 AK-8: Widerspruchspruefung
    warnings = _run_unsatisfiable_check(project_id, ast_dict, db=db)

    log.info("Constraint created: id=%d, project=%d, name=%s, warnings=%d",
             constraint.id, project_id, payload.name, len(warnings))

    result = _constraint_to_read(constraint)
    result.warnings = warnings
    return result


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{project_id}/constraints/{constraint_id}
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/constraints/{constraint_id}", response_model=schemas.ConstraintRead)
def get_constraint(
    project_id: int,
    constraint_id: int,
    db: Session = Depends(get_db),
):
    """Einzelnes Constraint lesen."""
    constraint = (
        db.query(models.Constraint)
        .filter(
            models.Constraint.id == constraint_id,
            models.Constraint.project_id == project_id,
        )
        .first()
    )
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint nicht gefunden")
    return _constraint_to_read(constraint)


# ---------------------------------------------------------------------------
# PUT /api/v1/projects/{project_id}/constraints/{constraint_id}
# ---------------------------------------------------------------------------

@router.put("/projects/{project_id}/constraints/{constraint_id}", response_model=schemas.ConstraintRead, dependencies=[Depends(require_writer)])
def update_constraint(
    project_id: int,
    constraint_id: int,
    payload: schemas.ConstraintUpdate,
    db: Session = Depends(get_db),
):
    """Constraint teilweise aktualisieren."""
    constraint = (
        db.query(models.Constraint)
        .filter(
            models.Constraint.id == constraint_id,
            models.Constraint.project_id == project_id,
        )
        .first()
    )
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint nicht gefunden")

    # AST validieren wenn expression oder consequence geaendert wird
    if payload.expression is not None or payload.consequence is not None:
        # Bestehendes AST laden als Basis
        existing_ast = json.loads(constraint.expression_json) if constraint.expression_json else {}
        
        ast_dict = {
            "kind": payload.kind or constraint.kind,
            "condition": payload.expression if payload.expression is not None else existing_ast.get("condition", {}),
        }
        
        # consequence handling
        existing_consequence = existing_ast.get("consequence")
        if payload.kind == "implies" or constraint.kind == "implies":
            if payload.consequence is not None:
                ast_dict["consequence"] = payload.consequence
            elif existing_consequence is not None:
                ast_dict["consequence"] = existing_consequence
        elif payload.consequence is not None:
            raise HTTPException(
                status_code=400,
                detail={"message": "forbid-Constraints duerfen kein 'consequence'-Feld haben"},
            )
        
        is_valid, errors = validate_ast(ast_dict)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Ungueltiges Constraint-AST",
                    "errors": errors,
                },
            )

        leaf_count = count_leaf_nodes(ast_dict)
        if leaf_count > MAX_LEAF_NODES:
            raise HTTPException(
                status_code=400,
                detail=f"Zu viele atomare Vergleiche: {leaf_count} (max {MAX_LEAF_NODES})",
            )

    # Felder aktualisieren (nur wenn nicht-None)
    if payload.name is not None:
        constraint.name = payload.name
    if payload.kind is not None:
        constraint.kind = payload.kind
    if payload.expression is not None or payload.consequence is not None:
        # Komplettes AST speichern
        existing_ast = json.loads(constraint.expression_json) if constraint.expression_json else {}
        ast_dict = {
            "kind": payload.kind or constraint.kind,
            "condition": payload.expression if payload.expression is not None else existing_ast.get("condition", {}),
        }
        if payload.kind == "implies" or constraint.kind == "implies":
            if payload.consequence is not None:
                ast_dict["consequence"] = payload.consequence
            elif existing_ast.get("consequence") is not None:
                ast_dict["consequence"] = existing_ast["consequence"]
        constraint.expression_json = json.dumps(ast_dict, ensure_ascii=False)
    if payload.is_valid is not None:
        constraint.is_valid = payload.is_valid

    db.commit()
    db.refresh(constraint)

    # REQ-6001 AK-8: Widerspruchspruefung (nur wenn expression geaendert)
    warnings: List[str] = []
    if payload.expression is not None or payload.consequence is not None:
        # Neuestes AST fuer Pruefung bauen
        existing_ast = json.loads(constraint.expression_json) if constraint.expression_json else {}
        check_ast = {
            "kind": payload.kind or constraint.kind,
            "condition": payload.expression if payload.expression is not None else existing_ast.get("condition", {}),
        }
        if (payload.kind or constraint.kind) == "implies":
            if payload.consequence is not None:
                check_ast["consequence"] = payload.consequence
            elif existing_ast.get("consequence") is not None:
                check_ast["consequence"] = existing_ast["consequence"]
        warnings = _run_unsatisfiable_check(
            project_id, check_ast,
            exclude_constraint_id=constraint_id,
            db=db,
        )

    log.info("Constraint updated: id=%d, warnings=%d", constraint_id, len(warnings))

    result = _constraint_to_read(constraint)
    result.warnings = warnings
    return result


# ---------------------------------------------------------------------------
# DELETE /api/v1/projects/{project_id}/constraints/{constraint_id}
# ---------------------------------------------------------------------------

@router.delete("/projects/{project_id}/constraints/{constraint_id}", status_code=204, dependencies=[Depends(require_writer)])
def delete_constraint(
    project_id: int,
    constraint_id: int,
    db: Session = Depends(get_db),
):
    """Constraint loeschen."""
    constraint = (
        db.query(models.Constraint)
        .filter(
            models.Constraint.id == constraint_id,
            models.Constraint.project_id == project_id,
        )
        .first()
    )
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint nicht gefunden")

    db.delete(constraint)
    db.commit()

    log.info("Constraint deleted: id=%d", constraint_id)


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{project_id}/constraints/validate
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/constraints/validate", response_model=schemas.ConstraintValidateResponse)
def validate_constraint_ast(
    project_id: int,
    payload: schemas.ConstraintValidateRequest,
    db: Session = Depends(get_db),
):
    """AST validieren ohne zu speichern."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    ast_dict = {
        "kind": payload.kind,
        "condition": payload.expression,
    }
    if payload.kind == "implies":
        if payload.consequence is not None:
            ast_dict["consequence"] = payload.consequence

    is_valid, errors = validate_ast(ast_dict)
    leaf_count = count_leaf_nodes(ast_dict)

    warnings: List[str] = []
    if leaf_count > MAX_LEAF_NODES:
        warnings.append(f"Zu viele atomare Vergleiche: {leaf_count} (max {MAX_LEAF_NODES})")

    from ..constraints.ast_parser import get_depth
    depth = get_depth(ast_dict)

    return schemas.ConstraintValidateResponse(
        is_valid=is_valid and len(warnings) == 0,
        errors=errors,
        warnings=warnings,
        leaf_count=leaf_count,
        depth=depth,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{project_id}/constraints/convert-from-rule/{rule_id}
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/constraints/convert-from-rule/{rule_id}",
             response_model=schemas.ConstraintRead,
             status_code=201,
             dependencies=[Depends(require_writer)])
def convert_rule_to_constraint(
    project_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
):
    """REQ-6001 AK-9: Bestehende Regel in Constraint umwandeln.

    Mapping:
    - exclude → forbid (condition: cat=val)
    - dependency → implies (condition: if_cat=if_val, consequence: then_cat=then_val)
    - combine → implies (condition: if_cat=if_val, consequence: then_cat IN [values])
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    rule = db.query(models.Rule).filter(
        models.Rule.id == rule_id,
        models.Rule.project_id == project_id,
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regel nicht gefunden")

    # Mapping: exclude → forbid, dependency/combine → implies
    if rule.type == "exclude":
        kind = "forbid"
        expression = {
            "op": "eq",
            "category_id": rule.if_category_id,
            "value_id": None,  # wird unten gesetzt
        }
        # value_id aus if_value finden
        val = db.query(models.Value).filter(
            models.Value.category_id == rule.if_category_id,
            models.Value.value == rule.if_value,
        ).first()
        if not val:
            raise HTTPException(status_code=400, detail=f"Wert '{rule.if_value}' nicht gefunden")
        expression["value_id"] = val.id

        constraint = models.Constraint(
            project_id=project_id,
            name=f"{rule.type} (als Constraint)",
            kind=kind,
            expression_json=json.dumps({"kind": kind, "condition": expression}, ensure_ascii=False),
            is_valid=True,
        )
    elif rule.type == "dependency":
        kind = "implies"
        # if_value finden
        val_if = db.query(models.Value).filter(
            models.Value.category_id == rule.if_category_id,
            models.Value.value == rule.if_value,
        ).first()
        if not val_if:
            raise HTTPException(status_code=400, detail=f"Wert '{rule.if_value}' nicht gefunden")

        # then_value finden
        val_then = db.query(models.Value).filter(
            models.Value.category_id == rule.then_category_id,
            models.Value.value == rule.then_value,
        ).first()
        if not val_then:
            raise HTTPException(status_code=400, detail=f"Wert '{rule.then_value}' nicht gefunden")

        ast_dict = {
            "kind": kind,
            "condition": {"op": "eq", "category_id": rule.if_category_id, "value_id": val_if.id},
            "consequence": {"op": "eq", "category_id": rule.then_category_id, "value_id": val_then.id},
        }
        constraint = models.Constraint(
            project_id=project_id,
            name=f"{rule.type} (als Constraint)",
            kind=kind,
            expression_json=json.dumps(ast_dict, ensure_ascii=False),
            is_valid=True,
        )
    elif rule.type == "combine":
        kind = "implies"
        # if_value finden
        val_if = db.query(models.Value).filter(
            models.Value.category_id == rule.if_category_id,
            models.Value.value == rule.if_value,
        ).first()
        if not val_if:
            raise HTTPException(status_code=400, detail=f"Wert '{rule.if_value}' nicht gefunden")

        # then_values_json parsen
        allowed = json.loads(rule.then_values_json or "[]")
        if not allowed:
            raise HTTPException(status_code=400, detail="combine-Regel hat keine Zielwerte")

        # value_ids fuer allowed Werte finden
        val_thens = db.query(models.Value).filter(
            models.Value.category_id == rule.then_category_id,
            models.Value.value.in_(allowed),
        ).all()
        if len(val_thens) != len(allowed):
            raise HTTPException(status_code=400, detail="Nicht alle Zielwerte gefunden")

        ast_dict = {
            "kind": kind,
            "condition": {"op": "eq", "category_id": rule.if_category_id, "value_id": val_if.id},
            "consequence": {
                "op": "in",
                "category_id": rule.then_category_id,
                "value_ids": [v.id for v in val_thens],
            },
        }
        constraint = models.Constraint(
            project_id=project_id,
            name=f"{rule.type} (als Constraint)",
            kind=kind,
            expression_json=json.dumps(ast_dict, ensure_ascii=False),
            is_valid=True,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unbekannter Regeltyp: {rule.type}")

    db.add(constraint)
    db.commit()
    db.refresh(constraint)

    log.info("Rule %d converted to constraint %d", rule_id, constraint.id)
    return _constraint_to_read(constraint)