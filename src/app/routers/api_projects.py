"""
routers/api_projects.py - G.R.E.A.T. REST-API fuer Projekte, Kategorien, Werte und Strategien.
REQ-1206: DELETE-Endpunkte
REQ-1209: Reorder-Endpunkt fuer Kategorien
REQ-1213: Rename-Endpunkte
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from combinatorics.boundary_value import generate_bva_values, BVAError

router = APIRouter(tags=["API"])


def _generation_display_name(g: "models.Generation") -> str:
    """Gibt den gespeicherten Namen zurueck oder generiert einen Default-Namen."""
    if g.name:
        return g.name
    date_str = g.created_at.strftime("%d.%m.%Y")
    # tc_count nicht hier verfuegbar – wird vom Aufrufer hinzugefuegt wenn noetig
    return f"#{g.id} \u2013 {g.strategy} ({date_str})"


@router.get("/strategies", response_model=List[str])
def list_strategies() -> List[str]:
    return ["all", "each", "linear", "pairwise", "risk_based"]


# ---------------------------------------------------------------------------
# Projekte
# ---------------------------------------------------------------------------

@router.get("/projects", response_model=List[schemas.ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.id).all()


@router.post("/projects", response_model=schemas.ProjectRead)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Project).filter(models.Project.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Project name already exists.")
    p = models.Project(name=payload.name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/projects/{pid}")
def delete_project(pid: int, db: Session = Depends(get_db)):
    """REQ-1206: Projekt loeschen."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
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


@router.post("/projects/{pid}/categories", response_model=schemas.CategoryRead)
def create_category(pid: int, payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    c = models.Category(project_id=pid, name=payload.name, order_index=payload.order_index)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/categories/{cid}")
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


class ReorderRequest(BaseModel):
    order: List[int]


@router.patch("/categories/{cid}/rename", response_model=schemas.CategoryRead)
def rename_category(cid: int, payload: RenameCategory, db: Session = Depends(get_db)):
    """REQ-1213: Kategorie umbenennen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    cat.name = payload.name
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/projects/{pid}/categories/reorder")
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


@router.post("/categories/{cid}/values", response_model=schemas.ValueRead)
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


@router.delete("/values/{vid}")
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


@router.patch("/values/{vid}/rename", response_model=schemas.ValueRead)
def rename_value(vid: int, payload: RenameValue, db: Session = Depends(get_db)):
    """REQ-1213: Wert umbenennen."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Value not found.")
    val.value = payload.value
    db.commit()
    db.refresh(val)
    return val


# REQ-3007: Wert-Eigenschaften aktualisieren
@router.patch("/values/{vid}/properties", response_model=schemas.ValueRead)
def update_value_properties(vid: int, payload: schemas.ValuePropertiesUpdate, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(val)
    return val


# REQ-3008: Default-Wert setzen
@router.patch("/values/{vid}/set-default", response_model=schemas.ValueRead)
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


@router.post("/projects/{pid}/rules", status_code=201, response_model=schemas.RuleRead)
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


@router.delete("/projects/{pid}/rules/{rid}")
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


@router.post("/projects/bulk-delete", response_model=schemas.BulkDeleteResponse)
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


@router.post("/projects/bulk-delete-force", response_model=schemas.BulkDeleteResponse)
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
@router.patch("/generations/{gid}/rename", response_model=schemas.GenerationSummary)
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
@router.delete("/generations/{gid}")
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


class BvaResponse(BaseModel):
    values: list[str]
    category_id: int


@router.post("/categories/{cid}/bva", response_model=BvaResponse)
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
        v = models.Value(category_id=cid, value=val_str, risk_weight=1)
        db.add(v)
    db.commit()
    return BvaResponse(values=bva_values, category_id=cid)
