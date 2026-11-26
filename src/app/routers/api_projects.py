"""
routers/api_projects.py - G.R.E.A.T. REST-API fuer Projekte, Kategorien, Werte und Strategien.
REQ-1206: DELETE-Endpunkte
REQ-1209: Reorder-Endpunkt fuer Kategorien
REQ-1213: Rename-Endpunkte
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field as PydanticField, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..name_validation import reject_control_chars  # BUG A-02
from ..auth_deps import require_api_capable, require_writer
from ..api_types import DbId
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
def list_projects(
    db: Session = Depends(get_db),
    current_user=Depends(require_api_capable),
    name: Optional[str] = None,  # REQ-6012: Komfort-Endpunkt fuer Pipelines
):
    """Alle Projekte listen. Projektbezogene Sichtbarkeit folgt mit REQ-4023.

    REQ-6012: Optionaler name-Parameter fuer exakte Suche (Groß-/Kleinschreibung egal).
    """
    query = db.query(models.Project)
    if name:
        query = query.filter(func.lower(models.Project.name) == name.lower())
    return query.order_by(models.Project.id).all()


@router.post("/projects", response_model=schemas.ProjectRead, dependencies=[Depends(require_writer)])
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Project).filter(
        func.lower(models.Project.name) == payload.name.lower()
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ein Projekt mit dem Namen '{payload.name}' existiert bereits.")
    p = models.Project(name=payload.name)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/projects/{pid}", dependencies=[Depends(require_writer)])
def delete_project(pid: DbId, db: Session = Depends(get_db), force: bool = False):
    """REQ-1206: Projekt loeschen. force=true ignoriert Generierungen."""
    from ..services import delete_project as svc_delete_project
    svc_delete_project(db, pid, force=force)
    return {"ok": True, "id": pid}


# ---------------------------------------------------------------------------
# Kategorien
# ---------------------------------------------------------------------------

@router.get("/projects/{pid}/categories", response_model=List[schemas.CategoryRead])
def list_categories(pid: DbId, db: Session = Depends(get_db)):
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return (
        db.query(models.Category)
        .filter(models.Category.project_id == pid)
        .order_by(models.Category.order_index, models.Category.id)
        .all()
    )


@router.post("/projects/{pid}/categories", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def create_category(pid: DbId, payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    exists = db.query(models.Category).filter(
        models.Category.project_id == pid,
        func.lower(models.Category.name) == payload.name.lower()
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Eine Kategorie mit dem Namen '{payload.name}' existiert in diesem Projekt bereits.")
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


def _invalidate_referencing_constraints(
    db: Session, project_id: int, force: bool, category_id=None, value_ids=None
) -> list[str]:
    """BUG K-02 / REQ-6001 AK-10: Betroffene Constraints vor dem Loeschen melden.

    Ohne force: 409 mit den Namen der betroffenen Constraints (Hinweis vorab).
    Mit force: Constraints werden als ungueltig markiert (nicht geloescht).
    """
    from ..constraints.references import referencing_constraints

    affected = referencing_constraints(db, project_id, category_id=category_id, value_ids=value_ids)
    names = [c.name for c in affected]
    if affected and not force:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "constraint_reference",
                "detail": "Constraints verweisen auf diesen Eintrag: " + ", ".join(names)
                          + ". Beim Loeschen werden sie als ungueltig markiert.",
                "constraints": names,
            },
        )
    for c in affected:
        c.is_valid = False
    return names


@router.delete("/categories/{cid}", dependencies=[Depends(require_writer)])
def delete_category(cid: DbId, force: bool = False, db: Session = Depends(get_db)):
    """REQ-1206: Kategorie loeschen. REQ-6001 AK-10: betroffene Constraints siehe oben."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    invalidated = _invalidate_referencing_constraints(
        db, cat.project_id, force, category_id=cid, value_ids=[v.id for v in cat.values])
    # B-18: TestCaseValue-Referenzen auf NULL setzen (nicht CASCADE-Loeschen)
    db.query(models.TestCaseValue).filter(
        models.TestCaseValue.category_id == cid
    ).update(
        {models.TestCaseValue.category_id: None},
        synchronize_session=False
    )
    db.delete(cat)
    db.commit()
    return {"ok": True, "id": cid, "invalidated_constraints": invalidated}


class RenameCategory(BaseModel):
    name: str = PydanticField(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def _no_control_chars(cls, v: str) -> str:
        return reject_control_chars(v)  # BUG A-02


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
def rename_category(cid: DbId, payload: RenameCategory, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-1213: Kategorie umbenennen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    # Duplikatpruefung (casefold, gleiche Kategorie ausschliessen)
    exists = db.query(models.Category).filter(
        models.Category.id != cid,
        models.Category.project_id == cat.project_id,
        func.lower(models.Category.name) == payload.name.lower()
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Eine Kategorie mit dem Namen '{payload.name}' existiert in diesem Projekt bereits.")
    cat.name = payload.name
    _stamp_audit(cat, current_user)
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{cid}/properties", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def update_category_properties(cid: DbId, payload: UpdateCategoryProperties, db: Session = Depends(get_db)):
    """REQ-4016: Kategorie-Eigenschaften aktualisieren (z.B. is_result)."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    if payload.is_result is not None:
        cat.is_result = payload.is_result
    if payload.category_type is not None:
        cat.category_type = payload.category_type
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/projects/{pid}/categories/reorder", dependencies=[Depends(require_writer)])
def reorder_categories(pid: DbId, payload: ReorderRequest, db: Session = Depends(get_db)):
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
def list_values(cid: DbId, db: Session = Depends(get_db)):
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    return db.query(models.Value).filter(models.Value.category_id == cid).order_by(models.Value.id).all()


@router.post("/categories/{cid}/values", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def create_value(cid: DbId, payload: schemas.ValueCreate, db: Session = Depends(get_db)):
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    exists = db.query(models.Value).filter(
        models.Value.category_id == cid,
        models.Value.value == payload.value
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ein Wert '{payload.value}' existiert in dieser Kategorie bereits.")
    # REQ-6016: Validate parent_value_id if provided
    parent_value_id = payload.parent_value_id
    if parent_value_id is not None:
        parent = db.get(models.Value, parent_value_id)
        if not parent or parent.category_id != cid:
            raise HTTPException(status_code=400, detail="parent_value_id gehoert nicht zu dieser Kategorie.")
        # REQ-6016: Max 3 levels deep
        depth = 0
        current = parent
        while current.parent_value_id is not None:
            depth += 1
            if depth >= 3:
                raise HTTPException(status_code=400, detail="Maximale Hierarchie-Tiefe (3 Ebenen) erreicht.")
            current = db.get(models.Value, current.parent_value_id)
    # REQ-3008: Erster Wert einer Kategorie ist automatisch Default
    existing_count = db.query(models.Value).filter(models.Value.category_id == cid).count()
    v = models.Value(
        category_id=cid,
        value=payload.value,
        risk_weight=payload.risk_weight,
        is_default=(existing_count == 0),
        parent_value_id=parent_value_id,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/values/{vid}", dependencies=[Depends(require_writer)])
def delete_value(vid: int, force: bool = False, db: Session = Depends(get_db)):
    """REQ-1206: Wert loeschen. B-19: Regeln die diesen Wert referenzieren mitloeschen.

    REQ-6001 AK-10: Constraints werden nicht geloescht, sondern als ungueltig markiert
    (erst nach Bestaetigung per force=true).
    """
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Wert nicht gefunden")
    cid = val.category_id
    invalidated = _invalidate_referencing_constraints(
        db, val.category.project_id, force, value_ids=[vid])
    # B-19: Regeln die diesen Wert referenzieren (als if_value oder then_value) mitloeschen
    rules_to_delete = db.query(models.Rule).filter(
        models.Rule.project_id == val.category.project_id,
        (
            (models.Rule.if_category_id == cid) & (models.Rule.if_value == val.value)
        ) | (
            (models.Rule.then_category_id == cid) & (models.Rule.then_value == val.value)
        )
    ).all()
    for r in rules_to_delete:
        db.delete(r)
    db.delete(val)
    db.commit()
    return {"ok": True, "id": vid, "invalidated_constraints": invalidated}


class RenameValue(BaseModel):
    value: str = PydanticField(min_length=1, max_length=500)


@router.patch("/values/{vid}/rename", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def rename_value(vid: int, payload: RenameValue, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-1213: Wert umbenennen. B-19: Regeln die diesen Wert referenzieren aktualisieren."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Wert nicht gefunden")
    exists = db.query(models.Value).filter(
        models.Value.id != vid,
        models.Value.category_id == val.category_id,
        models.Value.value == payload.value
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ein Wert '{payload.value}' existiert in dieser Kategorie bereits.")
    cid = val.category_id
    old_value = val.value
    val.value = payload.value
    _stamp_audit(val, current_user)
    # B-19: Regeln die diesen Wert referenzieren aktualisieren
    if old_value != payload.value:
        # if_value aktualisieren
        db.query(models.Rule).filter(
            models.Rule.if_category_id == cid,
            models.Rule.if_value == old_value
        ).update({"if_value": payload.value}, synchronize_session=False)
        # then_value aktualisieren
        db.query(models.Rule).filter(
            models.Rule.then_category_id == cid,
            models.Rule.then_value == old_value
        ).update({"then_value": payload.value}, synchronize_session=False)
        # then_values_json aktualisieren (combine rules)
        rules_with_json = db.query(models.Rule).filter(
            models.Rule.then_category_id == cid,
            models.Rule.then_values_json.isnot(None)
        ).all()
        for r in rules_with_json:
            import json as _json
            try:
                vals = _json.loads(r.then_values_json or "[]")
                if old_value in vals:
                    vals = [payload.value if v == old_value else v for v in vals]
                    r.then_values_json = _json.dumps(vals)
            except Exception:
                pass
    db.commit()
    db.refresh(val)
    return val


# REQ-3007: Wert-Eigenschaften aktualisieren
@router.patch("/values/{vid}/properties", response_model=schemas.ValueRead, dependencies=[Depends(require_writer)])
def update_value_properties(vid: int, payload: schemas.ValuePropertiesUpdate, db: Session = Depends(get_db), current_user=Depends(require_writer)):
    """REQ-3007: Risiko, Datentyp und Fehlerwert eines Werts aktualisieren."""
    val = db.get(models.Value, vid)
    if not val:
        raise HTTPException(status_code=404, detail="Wert nicht gefunden")
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
        raise HTTPException(status_code=404, detail="Wert nicht gefunden")
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
        raise HTTPException(status_code=404, detail="Wert nicht gefunden")
    val.is_default = False
    db.commit()
    db.refresh(val)
    return val


# ---------------------------------------------------------------------------
# REQ-6016: Hierarchische Klassen (Verfeinerung)
# ---------------------------------------------------------------------------

class RefineRequest(BaseModel):
    """REQ-6016: Request zum Erstellen einer Unter-Kategorie (Verfeinerung)."""
    name: str = PydanticField(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name darf nicht leer oder nur Leerzeichen sein.")
        return reject_control_chars(v.strip())  # BUG A-02


class HierarchyNode(BaseModel):
    """REQ-6016: Rekursiver Knoten in der Hierarchie."""
    id: int
    value: str
    children: list["HierarchyNode"] = []

    model_config = ConfigDict(from_attributes=True)


HierarchyNode.model_rebuild()


class CategoryHierarchyResponse(BaseModel):
    """REQ-6016: Response fuer Hierarchie-Endpunkt."""
    category_id: int
    category_name: str
    roots: list[HierarchyNode] = []


@router.post("/categories/{cid}/refine", response_model=schemas.CategoryRead, dependencies=[Depends(require_writer)])
def refine_category(cid: DbId, payload: RefineRequest, db: Session = Depends(get_db)):
    """REQ-6016: Unter-Kategorie (Verfeinerung) fuer einen Wert erstellen.

    Erstellt eine neue Kategorie als 'Unter-Kategorie' eines bestehenden Werts.
    Die neue Kategorie gehoert zum selben Projekt wie die Eltern-Kategorie.
    """
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")

    # Check if a category with this name already exists in the project
    exists = db.query(models.Category).filter(
        models.Category.project_id == cat.project_id,
        func.lower(models.Category.name) == payload.name.lower()
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Eine Kategorie mit dem Namen '{payload.name}' existiert in diesem Projekt bereits.")

    # Create the new sub-category
    max_order = db.query(func.max(models.Category.order_index)).filter(
        models.Category.project_id == cat.project_id
    ).scalar() or -1

    new_cat = models.Category(
        project_id=cat.project_id,
        name=payload.name,
        order_index=max_order + 1,
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.get("/categories/{cid}/hierarchy", response_model=CategoryHierarchyResponse)
def get_category_hierarchy(cid: DbId, db: Session = Depends(get_db)):
    """REQ-6016: Hierarchie einer Kategorie abrufen (Werte mit child_values)."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")

    # Get all values for this category
    all_values = db.query(models.Value).filter(
        models.Value.category_id == cid
    ).all()

    # Build hierarchy: find root values (no parent) and their children
    val_map = {v.id: v for v in all_values}

    def build_tree(value_id: int) -> HierarchyNode:
        val = val_map.get(value_id)
        if not val:
            return HierarchyNode(id=value_id, value="unknown")
        children = [build_tree(cv.id) for cv in val.child_values if cv.id in val_map]
        return HierarchyNode(id=val.id, value=val.value, children=children)

    roots = []
    for v in all_values:
        if v.parent_value_id is None:
            roots.append(build_tree(v.id))

    return CategoryHierarchyResponse(
        category_id=cid,
        category_name=cat.name,
        roots=roots,
    )


# ---------------------------------------------------------------------------
# Regeln (REST)
# ---------------------------------------------------------------------------

@router.get("/projects/{pid}/rules", response_model=list)
def api_list_rules(pid: DbId, db: Session = Depends(get_db)):
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
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
def api_create_rule(pid: DbId, payload: schemas.RuleCreate, db: Session = Depends(get_db)):
    """REQ-3003: Neue Regel anlegen. REQ-3004: Konflikt-Erkennung. B-19: Validierung."""
    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    cat_ids = {c.id: c for c in db.query(models.Category).filter(models.Category.project_id == pid).all()}

    # IF- und THEN-Kategorie müssen zum Projekt gehören
    if payload.if_category_id not in cat_ids or payload.then_category_id not in cat_ids:
        raise HTTPException(status_code=400, detail="Kategorie gehört nicht zu diesem Projekt.")

    # B-19: IF- und THEN-Kategorie dürfen nicht identisch sein
    if payload.if_category_id == payload.then_category_id:
        raise HTTPException(status_code=400, detail="IF- und THEN-Kategorie dürfen nicht identisch sein.")

    if_cat = cat_ids[payload.if_category_id]
    then_cat = cat_ids[payload.then_category_id]

    # B-19: Wert-Existenz prüfen
    if_values = [v.value for v in if_cat.values]
    then_values = [v.value for v in then_cat.values]

    if payload.if_value not in if_values:
        raise HTTPException(status_code=400, detail=f"Wert '{payload.if_value}' existiert nicht in Kategorie '{if_cat.name}'.")

    if payload.type in ("exclude", "dependency"):
        if not payload.then_value or not payload.then_value.strip():
            raise HTTPException(status_code=400, detail="Exclude-/Dependency-Regel benötigt einen Zielwert (then_value).")
        if payload.then_value not in then_values:
            raise HTTPException(status_code=400, detail=f"Wert '{payload.then_value}' existiert nicht in Kategorie '{then_cat.name}'.")

    if payload.type == "combine":
        vals = [v.strip() for v in (payload.then_values or []) if v and v.strip()]
        if not vals:
            raise HTTPException(status_code=400, detail="Combine-Regel benötigt mindestens einen Zielwert.")
        for v in vals:
            if v not in then_values:
                raise HTTPException(status_code=400, detail=f"Wert '{v}' existiert nicht in Kategorie '{then_cat.name}'.")

    # B-19: Duplikat-Prüfung
    existing = db.query(models.Rule).filter(models.Rule.project_id == pid).all()
    is_duplicate = False
    for r in existing:
        if r.type != payload.type:
            continue
        if r.if_category_id != payload.if_category_id or r.then_category_id != payload.then_category_id:
            continue
        if r.if_value != payload.if_value:
            continue
        if payload.type == "combine":
            import json as _json
            existing_vals = _json.loads(r.then_values_json or "[]")
            if sorted(existing_vals) == sorted(vals):
                is_duplicate = True
                break
        else:
            if r.then_value == (payload.then_value or ""):
                is_duplicate = True
                break
    if is_duplicate:
        raise HTTPException(status_code=409, detail="Diese Regel existiert bereits.")

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
def api_delete_rule(pid: DbId, rid: DbId, db: Session = Depends(get_db)):
    """REQ-3003: Regel löschen."""
    rule = db.get(models.Rule, rid)
    if not rule or rule.project_id != pid:
        raise HTTPException(status_code=404, detail="Regel nicht gefunden")
    db.delete(rule)
    db.commit()
    return {"ok": True, "id": rid}


@router.get("/projects/{pid}/generations", response_model=List[schemas.GenerationSummary])
def list_generations(pid: DbId, db: Session = Depends(get_db)):
    """REQ-2001: Generierungshistorie eines Projekts (neueste zuerst).

    REQ-6008: Enthaelt coverage_2wise_pct aus Cache.
    BUG R-03: Antwort ist wieder eine Liste (wie dokumentiert und von
    bestehenden API-Nutzern erwartet), nicht {"generations": [...]}.
    """
    from .api_coverage import _coverage_cache
    from ..schemas import GenerationSummary

    project = db.get(models.Project, pid)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
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
        # REQ-6008: 2-wise Coverage % aus Cache
        coverage_pct: Optional[float] = None
        if g.id in _coverage_cache:
            c2 = _coverage_cache[g.id].get("coverage_2wise", {})
            coverage_pct = c2.get("percentage")

        result.append(GenerationSummary(
            id=g.id,
            strategy=g.strategy,
            name=_generation_display_name(g),
            created_at=g.created_at.isoformat(),
            testcase_count=tc_count,
            coverage_2wise_pct=coverage_pct,
        ))
    return result


@router.post("/projects/bulk-delete", response_model=schemas.BulkDeleteResponse, dependencies=[Depends(require_writer)])
def bulk_delete_projects(payload: schemas.BulkDeleteRequest, db: Session = Depends(get_db)):
    """REQ-2002: Mehrere Projekte loeschen (blockiert wenn Generierungen vorhanden)."""
    from ..services import delete_project as svc_delete_project
    deleted = 0
    blocked = []
    for pid in payload.project_ids:
        p = db.get(models.Project, pid)
        if not p:
            continue
        try:
            svc_delete_project(db, pid, force=False)
            deleted += 1
        except HTTPException as e:
            if e.status_code == 409:
                blocked.append(pid)
            else:
                raise
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
        raise HTTPException(status_code=404, detail="Generierung nicht gefunden")
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
def generate_bva_for_category(cid: DbId, payload: BvaRequest, db: Session = Depends(get_db)):
    """REQ-0306: Grenzwertanalyse."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
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
    cid: DbId,
    payload: schemas.BVAMultiRangeRequest,
    db: Session = Depends(get_db),
):
    """REQ-3064: Mehrere BVA-Bereiche direkt erfassen und als Werte übernehmen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
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
# REQ-6007: Extended BVA for date, time, datetime, string length
# ---------------------------------------------------------------------------

@router.post("/categories/{cid}/bva/extended", response_model=schemas.BVAExtendedResponse, dependencies=[Depends(require_writer)])
def generate_extended_bva_for_category(
    cid: DbId,
    payload: schemas.BVAExtendedRequest,
    db: Session = Depends(get_db),
):
    """REQ-6007: Erweiterte BVA mit Datentypen (Datum, Uhrzeit, Stringlaenge).

    Unterstuetzt type: 'number', 'date', 'time', 'datetime', 'strlen'.
    Typspezifische Optionen ueber 'options'-Feld.
    """
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")

    bva_type = payload.type
    points = payload.points
    options = payload.options or {}
    results_list = []

    try:
        if bva_type == "number":
            # Bestehende Logik fuer Zahlen
            from ..services import apply_multi_range_bva_to_parameter
            results = apply_multi_range_bva_to_parameter(
                [{"min_val": r.min_val, "max_val": r.max_val, "allowed": r.allowed}
                 for r in payload.ranges],
                points,
            )
            for item in results:
                results_list.append(schemas.BVAExtendedResult(
                    value=item["name"],
                    is_error=item["is_error"],
                    vtype="number",
                    label="",
                ))

        else:
            # BUG C-05: alle Bereiche gemeinsam berechnen (gueltig/ungueltig, Ueberschneidung,
            # Min > Max) statt jeden Bereich isoliert
            from combinatorics.boundary_value import TypedRange, generate_multi_range_bva_typed
            bva_vals = generate_multi_range_bva_typed(
                bva_type,
                [TypedRange(r.min_val, r.max_val, r.allowed) for r in payload.ranges],
                points,
                options,
            )
            for bv in bva_vals:
                results_list.append(schemas.BVAExtendedResult(
                    value=bv.value,
                    is_error=bv.is_error,
                    vtype=bv.vtype,
                    label=bv.label,
                ))

    except BVAError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Werte in DB speichern
    for item in results_list:
        db.add(models.Value(
            category_id=cid,
            value=item.value,
            risk_weight=1,
            allowed=not item.is_error,
            # BUG C-06: Typ uebernehmen, soweit das Wertmodell ihn kennt
            # (number/date/time); strlen und datetime bleiben "string".
            vtype=item.vtype if item.vtype in schemas.VALID_VTYPES else "string",
        ))
    db.commit()

    return schemas.BVAExtendedResponse(values=results_list, category_id=cid)


# ---------------------------------------------------------------------------
# REQ-4021/REQ-4024: Projekt aktualisieren mit Optimistic Concurrency + Audit
# ---------------------------------------------------------------------------

class ProjectUpdate(BaseModel):
    name: Optional[str] = PydanticField(default=None, min_length=1, max_length=200)
    version: Optional[int] = None

    @field_validator("name")
    @classmethod
    def _no_control_chars(cls, v: Optional[str]) -> Optional[str]:
        return reject_control_chars(v)  # BUG A-02


@router.put("/projects/{pid}", response_model=schemas.ProjectRead)
def update_project(
    pid: DbId,
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
