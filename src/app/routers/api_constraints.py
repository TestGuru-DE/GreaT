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
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer
from .. import models, schemas
from ..constraints.ast_parser import validate_ast, count_leaf_nodes, MAX_LEAF_NODES

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
    )


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

    log.info("Constraint created: id=%d, project=%d, name=%s", constraint.id, project_id, payload.name)
    return _constraint_to_read(constraint)


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

    log.info("Constraint updated: id=%d", constraint_id)
    return _constraint_to_read(constraint)


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