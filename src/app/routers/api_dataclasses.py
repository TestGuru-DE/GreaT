"""
routers/api_dataclasses.py
REQ-2003: Datenklassen – Wiederverwendbare Aequivalenzklassen-Bibliothek.
REQ-4012: BugMagnet-Import.
"""
from __future__ import annotations

from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import httpx

from ..database import get_db
from .. import models, schemas
from ..dataclass_validator import validate_value, DATACLASS_TYPES

router = APIRouter(tags=["Datenklassen"])

BUGMAGNET_URL = "https://raw.githubusercontent.com/gojko/bugmagnet/master/template/config.json"


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


# REQ-4013: Export/Import User Dataclasses

@router.get("/dataclasses/export-user")
def export_user_dataclasses(db: Session = Depends(get_db)):
    """REQ-4013: Exportiert eigene (nicht-System) Datenklassen als JSON."""
    classes = db.query(models.DataClass).filter(models.DataClass.is_system == False).order_by(models.DataClass.name).all()
    result = []
    for dc in classes:
        values = db.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()
        result.append({
            "name": dc.name,
            "value_type": dc.value_type,
            "description": dc.description,
            "values": [v.value for v in values]
        })
    return JSONResponse(
        content={"version": "1.0", "dataclasses": result},
        headers={"Content-Disposition": "attachment; filename=my-dataclasses.json"}
    )


@router.post("/dataclasses/import-user")
async def import_user_dataclasses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """REQ-4013: Importiert eigene Datenklassen aus einer JSON-Datei (Merge-Strategie)."""
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ungültige JSON-Datei")
    
    classes_data = data.get("dataclasses", [])
    if not classes_data:
        # Legacy-Format: direkt dict {name: [values]}
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            classes_data = [{"name": k, "values": v} for k, v in data.items()]
    
    imported = 0
    for item in classes_data:
        name = item.get("name", "").strip()
        values = item.get("values", [])
        value_type = item.get("value_type", "text")
        description = item.get("description", "")
        
        if not name:
            continue
        
        # Prüfe ob bereits vorhanden
        existing = db.query(models.DataClass).filter(
            models.DataClass.name == name,
            models.DataClass.is_system == False
        ).first()
        if existing:
            dc = existing
        else:
            dc = models.DataClass(
                name=name, 
                is_system=False, 
                value_type=value_type,
                description=description or None
            )
            db.add(dc)
            db.flush()
        
        # Werte hinzufügen (nur neue)
        existing_vals = {v.value for v in db.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()}
        for val in values:
            if isinstance(val, str) and val.strip() and val not in existing_vals:
                db.add(models.DataClassValue(dataclass_id=dc.id, value=val))
        imported += 1
    
    db.commit()
    return {"status": "ok", "imported": imported}


# REQ-4012: BugMagnet-Import Endpoints

@router.get("/dataclasses/bugmagnet-status")
def bugmagnet_status(db: Session = Depends(get_db)):
    """REQ-4012: Prüft ob BugMagnet bereits importiert wurde."""
    has_bugmagnet = db.query(models.DataClass).filter(
        models.DataClass.is_system == True
    ).first() is not None
    return {"imported": has_bugmagnet}


@router.post("/dataclasses/bugmagnet-import")
async def import_bugmagnet(db: Session = Depends(get_db)):
    """
    REQ-4012: Importiert BugMagnet-Datenklassen von GitHub.
    Löscht bestehende is_system=True Klassen, legt neue an.
    """
    # 1. JSON von GitHub laden
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(BUGMAGNET_URL)
            if r.status_code != 200:
                raise HTTPException(status_code=502, detail="BugMagnet JSON konnte nicht geladen werden")
            data = r.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Fehler beim Download von GitHub: {str(e)}")

    # 2. Bestehende System-Datenklassen löschen
    existing = db.query(models.DataClass).filter(models.DataClass.is_system == True).all()
    for dc in existing:
        db.delete(dc)
    db.flush()

    # 3. Neue anlegen
    created = 0
    for category_name, values in data.items():
        if not isinstance(values, list):
            continue
        dc = models.DataClass(
            name=category_name,
            is_system=True,
            value_type="text",
            description="BugMagnet Import",
        )
        db.add(dc)
        db.flush()
        for val in values[:50]:  # Max 50 Werte pro Kategorie
            if isinstance(val, str):
                db.add(models.DataClassValue(dataclass_id=dc.id, value=val))
        created += 1

    db.commit()
    return {"status": "ok", "categories_imported": created, "source": "bugmagnet"}
