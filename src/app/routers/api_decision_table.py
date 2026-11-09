"""REQ-5000/5003/5005/5012/5018/5021: Entscheidungstabelle API"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth_deps import get_current_user, require_editor_or_admin, require_api_capable
from ..database import get_db
from ..models import Category, Project
from ..models.decision_table_constraint import DecisionTableConstraint
from ..models.auth import User
from ..services_decision_table import (
    apply_constraints,
    apply_effect_priorities,
    calculate_checksum,
    collapse_rules,
    detect_contradictions,
    detect_gaps,
    generate_cause_effect_graph,
    generate_decision_table,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision-table", tags=["decision-table"])


class DecisionTableGenerateRequest(BaseModel):
    """Request-Payload fuer die Entscheidungstabelle-Generierung."""

    project_id: int
    constraints: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optionale Constraints (REQ-5007-5011)",
    )
    priorities: Optional[Dict[str, int]] = Field(
        default=None,
        description="REQ-5021: Optionale Prioritaeten fuer Wirkungen (effect_id -> priority, 1=hoechst)",
    )
    effect_mode: str = Field(
        default="binary",
        description="REQ-5016: 'binary' (X/-) oder 'text' (Werte aus Wirkung-Kategorie)",
    )
    enable_override: bool = Field(
        default=False,
        description="REQ-5021: Wenn True, Don't Care Reduktion ('-' statt None)",
    )


class ConstraintCreateRequest(BaseModel):
    """REQ-5012: Request-Payload fuer Constraint-Erstellung."""

    project_id: int
    constraint_type: str
    targets: Any  # list fuer E/O/I, dict fuer R/M
    description: Optional[str] = None


@router.post("/generate")
def generate_decision_table_endpoint(
    payload: DecisionTableGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
) -> Dict[str, Any]:
    """Generiert eine Entscheidungstabelle fuer ein Projekt.

    REQ-5000: Button "Entscheidungstabelle"
    REQ-5003: Layout (Ursachen oben, Wirkungen unten)
    REQ-5004: Boolean-Werte (Y/N)
    REQ-5005: Automatische Regelgenerierung
    REQ-5012: Persistente Constraints werden automatisch geladen
    """
    # Pruefe ob Projekt existiert und User Zugriff hat
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # Generiere Tabelle
    # REQ-5016: effect_mode wird an generate_decision_table uebergeben
    result = generate_decision_table(db, payload.project_id, effect_mode=payload.effect_mode)

    # REQ-5012: Lade persistente Constraints (wenn kein Override)
    constraints_to_apply: Optional[List[Dict[str, Any]]] = None
    if payload.constraints:
        # Override: benutzeruebergabe hat Vorrang
        constraints_to_apply = payload.constraints
    else:
        # Lade persistente Constraints aus der Datenbank
        db_constraints = (
            db.query(DecisionTableConstraint)
            .filter(DecisionTableConstraint.project_id == payload.project_id)
            .all()
        )
        if db_constraints:
            constraints_to_apply = []
            for c in db_constraints:
                ctype = c.constraint_type
                if ctype in ("E", "O", "I"):
                    constraints_to_apply.append({
                        "type": ctype,
                        "causes": c.targets,
                    })
                elif ctype in ("R", "M"):
                    constraints_to_apply.append({
                        "type": ctype,
                        "from": c.targets.get("from"),
                        "to": c.targets.get("to"),
                    })

    # Wende Constraints an (falls vorhanden)
    if constraints_to_apply and "rules" in result and result["rules"]:
        result["rules"] = apply_constraints(result["rules"], constraints_to_apply)
        result["rules_after_constraints"] = len(result["rules"])

    # REQ-5021: Wende Prioritaeten an (opt-in)
    if payload.priorities and "rules" in result and result["rules"]:
        # Konvertiere string-keys (aus JSON) zurueck zu int
        int_priorities: Dict[int, int] = {}
        for k, v in payload.priorities.items():
            try:
                int_priorities[int(k)] = v
            except (ValueError, TypeError):
                logger.warning(
                    "REQ-5021: Ungueltiger Prioritaetsschlussel '%s', uebersprungen", k
                )
        result["rules"] = apply_effect_priorities(
            result["rules"],
            result.get("effects", []),
            int_priorities,
            enable_override=payload.enable_override,
        )

    return result


@router.get("/categories/{project_id}")
def get_decision_table_categories(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
) -> Dict[str, Any]:
    """REQ-5000/5002: Hole Ursache- und Wirkungskategorien fuer ein Projekt."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    causes = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "cause",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    effects = (
        db.query(Category)
        .filter(
            Category.project_id == project_id,
            Category.category_type == "effect",
        )
        .order_by(Category.order_index, Category.id)
        .all()
    )

    return {
        "causes": [{"id": c.id, "name": c.name} for c in causes],
        "effects": [{"id": e.id, "name": e.name} for e in effects],
        "can_generate": len(causes) > 0 and len(effects) > 0,
    }


# =============================================================================
# REQ-5018: Cause-Effect-Graph Endpoint
# =============================================================================

@router.get("/graph/{project_id}")
def get_cause_effect_graph_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
) -> Dict[str, Any]:
    """REQ-5018: Cause-Effect-Graph-Daten fuer Visualisierung."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return generate_cause_effect_graph(db, project_id)


# =============================================================================
# REQ-5012: Constraint CRUD Endpoints
# =============================================================================

@router.get("/constraints/{project_id}")
def get_constraints(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
) -> List[Dict[str, Any]]:
    """REQ-5012: Alle Constraints eines Projekts abrufen."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    constraints = (
        db.query(DecisionTableConstraint)
        .filter(DecisionTableConstraint.project_id == project_id)
        .all()
    )
    return [
        {
            "id": c.id,
            "type": c.constraint_type,
            "targets": c.targets,
            "description": c.description,
        }
        for c in constraints
    ]


@router.post("/constraints")
def create_constraint(
    payload: ConstraintCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
) -> Dict[str, Any]:
    """REQ-5012: Neuen Constraint erstellen."""
    # Pruefe ob Projekt existiert
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # Validierung des Constraint-Typs
    if payload.constraint_type not in ("E", "O", "I", "R", "M"):
        raise HTTPException(
            status_code=400,
            detail="Ungueltiger Constraint-Typ. Gueltige Typen: E, O, I, R, M",
        )

    # Validierung der Targets je nach Typ
    if payload.constraint_type in ("E", "O", "I"):
        if not isinstance(payload.targets, list) or len(payload.targets) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Constraint '{payload.constraint_type}' benoetigt mindestens 2 Ursachen als Liste",
            )
    elif payload.constraint_type in ("R", "M"):
        if not isinstance(payload.targets, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Constraint '{payload.constraint_type}' benoetigt ein Dict mit 'from' und 'to'",
            )
        if "from" not in payload.targets or "to" not in payload.targets:
            raise HTTPException(
                status_code=400,
                detail=f"Constraint '{payload.constraint_type}' benoetigt 'from' und 'to' im targets-Objekt",
            )

    constraint = DecisionTableConstraint(
        project_id=payload.project_id,
        constraint_type=payload.constraint_type,
        targets=payload.targets,
        description=payload.description,
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)

    return {
        "id": constraint.id,
        "type": constraint.constraint_type,
        "targets": constraint.targets,
        "description": constraint.description,
    }


@router.delete("/constraints/{constraint_id}")
def delete_constraint(
    constraint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
) -> Dict[str, str]:
    """REQ-5012: Constraint loeschen."""
    constraint = db.get(DecisionTableConstraint, constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint nicht gefunden")

    db.delete(constraint)
    db.commit()

    return {"message": "Constraint geloescht"}


# =============================================================================
# REQ-5013/5014/5019/5020: Optimization Endpoints
# =============================================================================

class CollapseRequest(BaseModel):
    """Request-Payload fuer Collapsing."""
    project_id: int


class ValidateRequest(BaseModel):
    """Request-Payload fuer Validierung."""
    project_id: int


@router.post("/collapse")
def collapse_decision_table_endpoint(
    payload: CollapseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
) -> Dict[str, Any]:
    """REQ-5013: Collapsing anwenden.

    Fasst redundante Regeln automatisch zusammen.
    """
    # Pruefe ob Projekt existiert
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # Generiere Tabelle
    result = generate_decision_table(db, payload.project_id)
    if "rules" not in result or not result["rules"]:
        result["collapsed_count"] = 0
        return result

    rules, reduced = collapse_rules(result["rules"])
    result["rules"] = rules
    result["collapsed_count"] = reduced
    result["total_rules"] = len(rules)

    return result


@router.post("/validate")
def validate_decision_table_endpoint(
    payload: ValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
) -> Dict[str, Any]:
    """REQ-5014/5019/5020: Checksum + Widerspruch + Luecken.

    Fuehrt eine vollstaendige Validierung der Entscheidungstabelle durch.
    """
    # Pruefe ob Projekt existiert
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    # Generiere Tabelle
    result = generate_decision_table(db, payload.project_id)
    if "rules" not in result or not result["rules"]:
        result["checksum"] = None
        result["contradictions"] = []
        result["gaps"] = []
        return result

    num_causes = len(result.get("causes", []))

    # REQ-5014: Checksum
    result["checksum"] = calculate_checksum(result["rules"], num_causes)

    # REQ-5019: Widersprueche
    result["contradictions"] = detect_contradictions(result["rules"])

    # REQ-5020: Luecken
    result["gaps"] = detect_gaps(result["rules"], num_causes)

    return result