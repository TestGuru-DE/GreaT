"""
routers/api_dataclasses.py
REQ-2003: Datenklassen – Wiederverwendbare Aequivalenzklassen-Bibliothek.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..dataclass_validator import validate_value, DATACLASS_TYPES

router = APIRouter(tags=["Datenklassen"])


@router.get("/dataclasses", response_model=List[schemas.DataClassRead])
def list_dataclasses(db: Session = Depends(get_db)):
    """REQ-2003: Alle Datenklassen auflisten."""
    return db.query(models.DataClass).order_by(models.DataClass.name).all()


@router.post("/dataclasses", response_model=schemas.DataClassRead)
def create_dataclass(payload: schemas.DataClassCreate, db: Session = Depends(get_db)):
    """REQ-2003: Neue Datenklasse erstellen."""
    if payload.value_type not in DATACLASS_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unbekannter Typ '{payload.value_type}'. Erlaubt: {list(DATACLASS_TYPES)}"
        )
    existing = db.query(models.DataClass).filter(models.DataClass.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Datenklasse mit diesem Namen existiert bereits.")
    dc = models.DataClass(
        name=payload.name,
        value_type=payload.value_type,
        description=payload.description,
    )
    db.add(dc)
    db.commit()
    db.refresh(dc)
    return dc


# REQ-2006: Bulk-Delete Datenklassen (VOR /{dcid} registriert um Routing-Konflikte zu vermeiden)
@router.post("/dataclasses/bulk-delete", response_model=schemas.DataclassBulkDeleteResponse)
def bulk_delete_dataclasses(payload: schemas.DataclassBulkDeleteRequest, db: Session = Depends(get_db)):
    """REQ-2006: Mehrere Datenklassen gleichzeitig loeschen. System-Klassen werden uebersprungen."""
    deleted = 0
    blocked = 0
    for dcid in payload.dataclass_ids:
        dc = db.get(models.DataClass, dcid)
        if not dc:
            continue
        if dc.is_system:
            blocked += 1
            continue
        db.delete(dc)
        deleted += 1
    db.commit()
    return schemas.DataclassBulkDeleteResponse(deleted=deleted, blocked=blocked)


@router.delete("/dataclasses/{dcid}")
def delete_dataclass(dcid: int, db: Session = Depends(get_db)):
    """REQ-2003: Datenklasse loeschen. System-Datenklassen sind geschuetzt (REQ-2005)."""
    dc = db.get(models.DataClass, dcid)
    if not dc:
        raise HTTPException(status_code=404, detail="Datenklasse nicht gefunden.")
    if dc.is_system:
        raise HTTPException(status_code=403, detail="System-Datenklassen koennen nicht geloescht werden.")
    db.delete(dc)
    db.commit()
    return {"ok": True, "id": dcid}


@router.get("/dataclasses/{dcid}/values", response_model=List[schemas.DataClassValueRead])
def list_dataclass_values(dcid: int, db: Session = Depends(get_db)):
    """REQ-2003: Alle Werte einer Datenklasse auflisten."""
    dc = db.get(models.DataClass, dcid)
    if not dc:
        raise HTTPException(status_code=404, detail="Datenklasse nicht gefunden.")
    return db.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dcid).order_by(models.DataClassValue.id).all()


@router.post("/dataclasses/{dcid}/values", response_model=schemas.DataClassValueRead)
def add_dataclass_value(dcid: int, payload: schemas.DataClassValueCreate, db: Session = Depends(get_db)):
    """REQ-2003: Wert zu Datenklasse hinzufuegen (mit Typvalidierung)."""
    dc = db.get(models.DataClass, dcid)
    if not dc:
        raise HTTPException(status_code=404, detail="Datenklasse nicht gefunden.")
    ok, msg = validate_value(payload.value, dc.value_type)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    v = models.DataClassValue(dataclass_id=dcid, value=payload.value)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/dataclasses/values/{vid}")
def delete_dataclass_value(vid: int, db: Session = Depends(get_db)):
    """REQ-2003: Einzelnen Wert aus Datenklasse loeschen."""
    v = db.get(models.DataClassValue, vid)
    if not v:
        raise HTTPException(status_code=404, detail="Wert nicht gefunden.")
    db.delete(v)
    db.commit()
    return {"ok": True, "id": vid}


@router.post("/categories/{cid}/apply-dataclass")
def apply_dataclass_to_category(cid: int, payload: schemas.ApplyDataClassRequest, db: Session = Depends(get_db)):
    """REQ-2003: Alle Werte einer Datenklasse als Kategorie-Werte hinzufuegen."""
    cat = db.get(models.Category, cid)
    if not cat:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden.")
    dc = db.get(models.DataClass, payload.dataclass_id)
    if not dc:
        raise HTTPException(status_code=404, detail="Datenklasse nicht gefunden.")

    # Bereits vorhandene Werte (Duplikate vermeiden)
    existing_vals = {
        v.value for v in db.query(models.Value).filter(models.Value.category_id == cid).all()
    }
    added = 0
    for dcv in dc.dc_values:
        if dcv.value not in existing_vals:
            db.add(models.Value(
                category_id=cid,
                value=dcv.value,
                risk_weight=1,
                vtype=dc.value_type,
            ))
            existing_vals.add(dcv.value)
            added += 1
    db.commit()
    return {"added": added, "dataclass_id": dc.id, "dataclass_name": dc.name}