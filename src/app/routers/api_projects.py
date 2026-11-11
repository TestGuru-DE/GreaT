"""
routers/api_projects.py - G.R.E.A.T. REST-API fuer Projekte, Kategorien, Werte und Strategien.
REQ-1206: DELETE-Endpunkte
REQ-1209: Reorder-Endpunkt fuer Kategorien
REQ-1213: Rename-Endpunkte
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field as PydanticField, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth_deps import require_api_capable, require_writer
from .. import models, schemas
from combinatorics.boundary_value import generate_bva_values, BVAError

router = APIRouter(tags=["API"], dependencies=[Depends(require_api_capable)])


def _generation_display_name(g: "models.Generation") -> str:
    """Gibt den gespeicherten Namen zurueck oder generiert einen Default-Namen."""
    if g.name:
        return g.name
    date_str = g.created_at.strftime("%d.%m.%Y")
    # tc_count nicht hier verfuegbar – wird vom Aufrufer hinzugefuegt wenn noetig
    return f"#{g.id} \u2013 {g.strategy} ({date_str})"


@router.get("/strategies", response_model=List[str])
def list_strategies() -> List[str]:
    return ["all", "each", "linear", "pairwise", "risk_based", "t_wise", "mcdc"]  # REQ-3039, REQ-3044


# ---------------------------------------------------------------------------
# Projekte
# ---------------------------------------------------------------------------

@router.get("/projects", response_model=List[schemas.ProjectRead])
def list_projects(db: Session = Depends(get_db), current_user=Depends(require_api_capable)):
    """REQ-4023: Admin sieht alle Projekte; andere Rollen nur Projekte mit Mitgliedschaft."""
    query = db.query(models.Project)
    if current_user.role != "admin":
        from ..models.project_membership import ProjectMembership
        member_ids = db.query(ProjectMembership.project_id).filter(ProjectMembership.user_id == current_user.id)
        query = query.filter(models.Project.id.in_(member_ids))
    return query.order_by(models.Project.id).all()


@router.post("/projects", response_model=schemas.ProjectRead, dependencies=[Depends(require_writer)])
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Project).filter(models.Project.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Project name already exists.")
    p = models.Project(name=payload.name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/projects/{pid}", dependencies=[Depends(require_writer)])
def delete_project(pid: int, db: Session = Depends(get_db)):
    """REQ-1206: Projekt loeschen."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    # Projektbezogene Tabellen ohne ON DELETE CASCADE vorher leeren (keine verwaisten Reste).
    from ..models.decision_table_constraint import DecisionTableConstraint
    from ..models.project_membership import ProjectMembership
    db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id == pid).delete(synchronize_session=False)
    db.query(ProjectMembership).filter(ProjectMembership.project_id == pid).delete(synchronize_session=False)
    db.delete(project)
    db.commit()
    return {"ok": True, "id": pid}


# ---------------------------------------------------------------------------
# Kategorien
# ---------------------------------------------------------------------------

@router.get("/projects/{pid}/categories", response_model=List[schemas.CategoryRead])
def list_categories(pid: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Category)
        .filter(models.Category.project_id == pid)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )


@router.post("/projects/{pid}/categories", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def create_category(pid: int, payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    c = models.Category(
        project_id=pid, 
        name=payload.name, 
        order_index=payload.order_index,
        is_result=payload.is_result,  # REQ-4016
        category_type=payload.category_type,  # REQ-5002
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/categories/{cid}", dependencies=[Depends(require_writer)])
def delete_category(cid: int, db: Session = Depends(get_db)):
    """REQ-1206: Kategorie loeschen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    db.delete(cat)
    db.commit()
    return {"ok": True, "id": cid}


class RenameCategory(BaseModel):
    name: str = PydanticField(min_length=1, max_length=200)


class UpdateCategoryProperties(BaseModel):  # REQ-4016 / REQ-5002
    is_result: Optional[bool] = None
    category_type: Optional[str] = None

    @field_validator("category_type")
    @classmethod
    def _check_type(cls, v):
        if v is not None and v not in schemas.VALID_CATEGORY_TYPES:
            raise ValueError("category_type muss standard, cause oder effect sein.")
        return v


class ReorderRequest(BaseModel):
    order: List[int]



def _stamp_audit(entity, current_user) -> None:
    """REQ-4024: Audit-Trail (last_modified_by / last_modified_at) setzen."""
    from datetime import datetime, timezone
    entity.last_modified_by = current_user.id
    entity.last_modified_at = datetime.now(timezone.utc)


@router.patch("/categories/{cid}/rename", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def rename_category(cid: int, payload: RenameCategory, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-1213: Kategorie umbenennen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    cat.name = payload.name
    _stamp_audit(cat, current_user)
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{cid}/properties", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def update_category_properties(cid: int, payload: UpdateCategoryProperties, db: Session = Depends(get_db)):
    """REQ-4016: Kategorie-Eigenschaften aktualisieren (z.B. is_result)."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    if payload.is_result is not None:
        cat.is_result = payload.is_result
    if payload.category_type is not None:
        cat.category_type = payload.category_type
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/projects/{pid}/categories/reorder", dependencies=[Depends(require_writer)])
def reorder_categories(pid: int, payload: ReorderRequest, db: Session = Depends(get_db)):
    """REQ-1209: Kategorien-Reihenfolge aendern."""
    for idx, cid in enumerate(payload.order):
        cat = db.get(models.Category, cid)
        if cat and cat.project_id == pid:
            cat.order_index = idx
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Werte
# ---------------------------------------------------------------------------

@router.get("/categories/{cid}/values", response_model=List[schemas.ValueRead])
def list_values(cid: int, db: Session = Depends(get_db)):
    return db.query(models.Value).filter(models.Value.category_id == cid).order_by(models.Value.id).all()


@router.post("/categories/{cid}/values", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def create_value(cid: int, payload: schemas.ValueCreate, db: Session = Depends(get_db)):
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    # REQ-3008: Erster Wert einer Kategorie ist automatisch Default
    existing_count = db.query(models.Value).filter(models.Value.category_id == cid).count()
    v = models.Value(
        category_id=cid,
        value=payload.value,
        risk_weight=payload.risk_weight,
        is_default=(existing_count == 0),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/values/{vid}", dependencies=[Depends(require_writer)])
def delete_value(vid: int, db: Session = Depends(get_db)):
    """REQ-1206: Wert loeschen."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    db.delete(val)
    db.commit()
    return {"ok": True, "id": vid}


class RenameValue(BaseModel):
    value: str = PydanticField(min_length=1, max_length=500)


@router.patch("/values/{vid}/rename", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def rename_value(vid: int, payload: RenameValue, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-1213: Wert umbenennen."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    val.value = payload.value
    _stamp_audit(val, current_user)
    db.commit()
    db.refresh(val)
    return val


# REQ-3007: Wert-Eigenschaften aktualisieren
@router.patch("/values/{vid}/properties", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def update_value_properties(vid: int, payload: schemas.ValuePropertiesUpdate, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-3007: Risiko, Datentyp und Fehlerwert eines Werts aktualisieren."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    if payload.risk_weight is not None:
        val.risk_weight = payload.risk_weight
    if payload.vtype is not None:
        val.vtype = payload.vtype
    if payload.allowed is not None:
        val.allowed = payload.allowed
    _stamp_audit(val, current_user)
    db.commit()
    db.refresh(val)
    return val


# REQ-3008: Default-Wert setzen
@router.patch("/values/{vid}/set-default", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def set_default_value(vid: int, db: Session = Depends(get_db)):
    """REQ-3008: Setzt einen Wert als Default für seine Kategorie (nur einer pro Kategorie)."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    # Vorherigen Default in dieser Kategorie zurücksetzen
    db.query(models.Value).filter(
        models.Value.category_id == val.category_id,
        models.Value.is_default == True  # noqa: E712
    ).update({"is_default": False})
    val.is_default = True
    db.commit()
    db.refresh(val)
    return val


# REQ-3008: Default-Wert entfernen
@router.patch("/values/{vid}/unset-default", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def unset_default_value(vid: int, db: Session = Depends(get_db)):
    """REQ-3008: Entfernt die Default-Markierung von einem Wert."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    val.is_default = False
    db.commit()
    db.refresh(val)
    return val


# ---------------------------------------------------------------------------
# Regeln (REST)
# ---------------------------------------------------------------------------

@router.get("/projects/{pid}/rules", response_model=list)
def api_list_rules(pid: int, db: Session = Depends(get_db)):
    rules = db.query(models.Rule).filter(models.Rule.project_id == pid).order_by(models.Rule.id).all()
    return [
        {
            "id": r.id,
            "type": r.type,
            "if_category_id": r.if_category_id,
            "if_value": r.if_value,
            "then_category_id": r.then_category_id,
            "then_value": r.then_value,
            "then_values_json": r.then_values_json,
        }
        for r in rules
    ]


def _detect_conflicts(new_rule: models.Rule, existing: list) -> list[int]:
    """REQ-3004: Prüft ob neue Regel Widersprüche mit bestehenden Regeln hat."""
    conflicts = []
    for r in existing:
        if r.id == new_rule.id:
            continue
        same_trigger = (r.if_category_id == new_rule.if_category_id
                        and r.if_value == new_rule.if_value
                        and r.then_category_id == new_rule.then_category_id)
        if not same_trigger:
            continue
        # exclude vs dependency/combine (gleicher Trigger, gleicher Zielwert)
        if new_rule.type in ("dependency",) and r.type == "exclude":
            if r.then_value == new_rule.then_value:
                conflicts.append(r.id)
        elif new_rule.type == "exclude" and r.type in ("dependency",):
            if r.then_value == new_rule.then_value:
                conflicts.append(r.id)
        # dependency vs dependency (gleicher Trigger, anderer Zielwert)
        elif new_rule.type == "dependency" and r.type == "dependency":
            if r.then_value != new_rule.then_value:
                conflicts.append(r.id)
        # combine vs dependency (Zielwert nicht in allowed_values)
        elif new_rule.type == "dependency" and r.type == "combine":
            import json as _json
            allowed = _json.loads(r.then_values_json or "[]")
            if new_rule.then_value not in allowed:
                conflicts.append(r.id)
        elif new_rule.type == "combine" and r.type == "dependency":
            import json as _json
            allowed = _json.loads(new_rule.then_values_json or "[]")
            if r.then_value not in allowed:
                conflicts.append(r.id)
    return conflicts


@router.post("/projects/{pid}/rules", status_code=201, response_model=schemas.RuleRead, dependencies=[Depends(require_writer)])
def api_create_rule(pid: int, payload: schemas.RuleCreate, db: Session = Depends(get_db)):
    """REQ-3003: Neue Regel anlegen. REQ-3004: Konflikt-Erkennung."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    cat_ids = {c.id for c in db.query(models.Category).filter(models.Category.project_id == pid).all()}
    if payload.if_category_id not in cat_ids or payload.then_category_id not in cat_ids:
        raise HTTPException(status_code=400, detail="Kategorie gehört nicht zu diesem Projekt.")

    rule = models.Rule(
        project_id=pid,
        type=payload.type,
        if_category_id=payload.if_category_id,
        if_value=payload.if_value,
        then_category_id=payload.then_category_id,
        then_value=payload.then_value or "",
    )
    if payload.type == "combine":
        vals = [v.strip() for v in (payload.then_values or []) if v and v.strip()]
        if not vals:
            raise HTTPException(status_code=400, detail="Combine-Regel benötigt mindestens einen Zielwert.")
        import json as _json
        rule.then_values_json = _json.dumps(vals)

    db.add(rule)
    db.flush()

    existing = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    conflicts = _detect_conflicts(rule, existing)

    db.commit()
    db.refresh(rule)

    return schemas.RuleRead(
        id=rule.id,
        type=rule.type,
        if_category_id=rule.if_category_id,
        if_value=rule.if_value,
        then_category_id=rule.then_category_id,
        then_value=rule.then_value,
        then_values_json=rule.then_values_json,
        conflict_with=conflicts,
    )


@router.delete("/projects/{pid}/rules/{rid}", dependencies=[Depends(require_writer)])
def api_delete_rule(pid: int, rid: int, db: Session = Depends(get_db)):
    """REQ-3003: Regel löschen."""
    rule = db.get(models.Rule, rid)
    if not rule or rule.project_id != pid:
        raise HTTPException(status_code=404, detail="Regel nicht gefunden.")
    db.delete(rule)
    db.commit()
    return {"ok": True, "id": rid}


@router.get("/projects/{pid}/generations", response_model=List[schemas.GenerationSummary])
def list_generations(pid: int, db: Session = Depends(get_db)):
    """REQ-2001: Generierungshistorie eines Projekts."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    gens = (
        db.query(models.Generation)
        .filter(models.Generation.project_id == pid)
        .order_by(models.Generation.id.desc())
        .all()
    )
    result = []
    for g in gens:
        tc_count = (
            db.query(models.TestCase)
            .filter(models.TestCase.generation_id == g.id)
            .count()
        )
        result.append(schemas.GenerationSummary(
            id=g.id,
            strategy=g.strategy,
            name=_generation_display_name(g),
            created_at=g.created_at.isoformat(),
            testcase_count=tc_count,
        ))
    return result


@router.post("/projects/bulk-delete", response_model=schemas.BulkDeleteResponse, dependencies=[Depends(require_writer)])
def bulk_delete_projects(payload: schemas.BulkDeleteRequest, db: Session = Depends(get_db)):
    """REQ-2002: Mehrere Projekte auf einmal löschen (blockiert wenn Generierungen vorhanden)."""
    from ..services import project_has_generations
    deleted = 0
    blocked = []
    for pid in payload.project_ids:
        p = db.get(models.Project, pid)
        if not p:
            continue
        if project_has_generations(db, pid):
            blocked.append(pid)
        else:
            db.delete(p)
            deleted += 1
    db.commit()
    return schemas.BulkDeleteResponse(deleted=deleted, blocked=blocked)


@router.post("/projects/bulk-delete-force", response_model=schemas.BulkDeleteResponse, dependencies=[Depends(require_writer)])
def bulk_delete_projects_force(payload: schemas.BulkDeleteRequest, db: Session = Depends(get_db)):
    """REQ-2002: Mehrere Projekte inkl. aller abhängiger Daten löschen."""
    from ..services import force_delete_project
    deleted = 0
    for pid in payload.project_ids:
        p = db.get(models.Project, pid)
        if not p:
            continue
        force_delete_project(db, pid)
        deleted += 1
    db.commit()
    return schemas.BulkDeleteResponse(deleted=deleted, blocked=[])


# REQ-2004: Editierbarer Generierungsname
@router.patch("/generations/{gid}/rename", response_model=schemas.GenerationSummary, dependencies=[Depends(require_writer)])
def rename_generation(gid: int, payload: schemas.GenerationRenameRequest, db: Session = Depends(get_db)):
    """REQ-2004: Setzt einen benutzerdefinierten Namen fuer eine Generierung."""
    g = db.get(models.Generation, gid)
    if not g:
        raise HTTPException(status_code=404, detail="Generation not found.")
    g.name = payload.name
    db.commit()
    db.refresh(g)
    tc_count = db.query(models.TestCase).filter(models.TestCase.generation_id == g.id).count()
    return schemas.GenerationSummary(
        id=g.id,
        strategy=g.strategy,
        name=g.name,
        created_at=g.created_at.isoformat(),
        testcase_count=tc_count,
    )


# REQ-3009: Einzelne Generierung löschen
@router.delete("/generations/{gid}", dependencies=[Depends(require_writer)])
def delete_generation(gid: int, db: Session = Depends(get_db)):
    """REQ-3009: Löscht eine Generierung inkl. aller Testfälle."""
    g = db.get(models.Generation, gid)
    if not g:
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden.")
    db.delete(g)
    db.commit()
    return {"ok": True, "id": gid}


# ---------------------------------------------------------------------------
# Grenzwertanalyse (BVA) - REQ-0306
# ---------------------------------------------------------------------------

class BvaRequest(BaseModel):
    min_val: float
    max_val: float
    points: int = 2
    allowed: bool = True


class BvaResponse(BaseModel):
    values: list[str]
    category_id: int


@router.post("/categories/{cid}/bva", response_model=BvaResponse, dependencies=[Depends(require_writer)])
def generate_bva_for_category(cid: int, payload: BvaRequest, db: Session = Depends(get_db)):
    """REQ-0306: Grenzwertanalyse."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    try:
        bva_values = generate_bva_values(min_val=payload.min_val, max_val=payload.max_val, points=payload.points)
    except BVAError as e:
        raise HTTPException(status_code=400, detail=str(e))
    for val_str in bva_values:
        v = models.Value(category_id=cid, value=val_str, risk_weight=1, allowed=payload.allowed)
        db.add(v)
    db.commit()
    return BvaResponse(values=bva_values, category_id=cid)


class BvaMultiRangeResponse(BaseModel):
    values: list[str]
    category_id: int


@router.post("/categories/{cid}/bva/ranges", response_model=BvaMultiRangeResponse, dependencies=[Depends(require_writer)])
def generate_multi_range_bva_for_category(
    cid: int,
    payload: schemas.BVAMultiRangeRequest,
    db: Session = Depends(get_db),
):
    """REQ-3064: Mehrere BVA-Bereiche direkt erfassen und als Werte übernehmen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    try:
        from ..services import apply_multi_range_bva_to_parameter

        results = apply_multi_range_bva_to_parameter(
            [
                {"min_val": r.min_val, "max_val": r.max_val, "allowed": r.allowed}
                for r in payload.ranges
            ],
            payload.points,
        )
    except BVAError as e:
        raise HTTPException(status_code=400, detail=str(e))

    values = []
    for item in results:
        value = item["name"]
        values.append(value)
        db.add(models.Value(category_id=cid, value=value, risk_weight=1, allowed=item["allowed"]))

    db.commit()
    return BvaMultiRangeResponse(values=values, category_id=cid)


# ---------------------------------------------------------------------------
# REQ-4021/REQ-4024: Projekt aktualisieren mit Optimistic Concurrency + Audit
# ---------------------------------------------------------------------------

class ProjectUpdate(BaseModel):
    name: Optional[str] = PydanticField(default=None, min_length=1, max_length=200)
    version: Optional[int] = None


@router.put("/projects/{pid}", response_model=schemas.ProjectRead)
def update_project(
    pid: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_writer),
):
    """REQ-4021: Projekt aktualisieren; Version-Konflikt -> 409."""
    from ..concurrency import update_with_version
    update_data = payload.model_dump(exclude={"version"}, exclude_unset=True)
    return update_with_version(
        db=db,
        model=models.Project,
        entity_id=pid,
        client_version=payload.version,
        update_data=update_data,
        current_user_id=current_user.id,
    )
