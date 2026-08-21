"""
REQ-4018: Hierarchische Datenklassen API.
Router für Datenknoten mit Baumstruktur und BugMagnet-Import.
"""
from __future__ import annotations

from typing import List, Optional
import json

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import httpx

from ..database import get_db
from .. import models, schemas

router = APIRouter(tags=["DataNodes"])

BUGMAGNET_URL = "https://raw.githubusercontent.com/gojko/bugmagnet/master/template/config.json"


def get_node_depth(node: models.DataNode, db: Session) -> int:
    """Berechnet die Tiefe eines Knotens im Baum."""
    depth = 0
    current = node
    while current.parent_id is not None:
        parent = db.get(models.DataNode, current.parent_id)
        if not parent:
            break
        current = parent
        depth += 1
        if depth > 20:  # Safety
            break
    return depth


def get_node_label(node: models.DataNode, db: Session) -> str:
    """Dynamische Bezeichnung: Kategorie/Gruppe/Klasse."""
    has_children = len(node.children) > 0
    if not has_children:
        return "Klasse"
    depth = get_node_depth(node, db)
    if depth == 0:
        return "Kategorie"
    return "Gruppe"


@router.get("/datanodes/bugmagnet-status")
def bugmagnet_status(db: Session = Depends(get_db)):
    """REQ-4018: Prüft ob BugMagnet bereits importiert wurde."""
    imported = db.query(models.DataNode).filter(
        models.DataNode.source == "bugmagnet"
    ).first() is not None
    return {"imported": imported}


@router.post("/datanodes/bugmagnet-import")
async def import_bugmagnet(db: Session = Depends(get_db)):
    """
    REQ-4018: Importiert BugMagnet vollständig als Baum.
    Unterstützt alle 4 Ebenen und Mischknoten.
    """
    # 1. JSON von GitHub laden
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(BUGMAGNET_URL)
            if r.status_code != 200:
                raise HTTPException(502, "BugMagnet JSON konnte nicht geladen werden")
            data = r.json()
    except httpx.RequestError as e:
        raise HTTPException(502, f"Fehler beim Download: {str(e)}")
    
    # 2. Alle bisherigen BugMagnet-Knoten löschen
    existing = db.query(models.DataNode).filter(
        models.DataNode.source == "bugmagnet",
        models.DataNode.parent_id == None
    ).all()
    for node in existing:
        db.delete(node)
    db.flush()
    
    # 3. Neu importieren
    _import_node_recursive(data, None, db, is_system=True, source="bugmagnet")
    db.commit()
    
    count = db.query(models.DataNode).filter(models.DataNode.source == "bugmagnet").count()
    return {"status": "ok", "nodes_created": count}


@router.get("/datanodes", response_model=List[schemas.DataNodeRead])
def list_root_nodes(db: Session = Depends(get_db)):
    """REQ-4018: Alle Wurzelknoten (parent_id=None)."""
    return db.query(models.DataNode).filter(
        models.DataNode.parent_id == None
    ).order_by(models.DataNode.sort_order, models.DataNode.name).all()


@router.get("/datanodes/tree", response_model=List[schemas.DataNodeRead])
def get_full_tree(db: Session = Depends(get_db)):
    """REQ-4018: Vollständiger Baum (für Frontend-Tree-View)."""
    return db.query(models.DataNode).filter(
        models.DataNode.parent_id == None
    ).order_by(models.DataNode.sort_order, models.DataNode.name).all()


@router.get("/datanodes/{node_id}", response_model=schemas.DataNodeRead)
def get_node(node_id: int, db: Session = Depends(get_db)):
    """REQ-4018: Einzelnen Knoten mit Kindern und Werten laden."""
    node = db.get(models.DataNode, node_id)
    if not node:
        raise HTTPException(404, "Knoten nicht gefunden")
    return node


@router.post("/datanodes", response_model=schemas.DataNodeRead)
def create_node(data: schemas.DataNodeCreate, db: Session = Depends(get_db)):
    """REQ-4018: Neuen Knoten erstellen."""
    node = models.DataNode(**data.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.put("/datanodes/{node_id}", response_model=schemas.DataNodeRead)
def update_node(node_id: int, data: schemas.DataNodeCreate, db: Session = Depends(get_db)):
    """REQ-4018: Knoten aktualisieren."""
    node = db.get(models.DataNode, node_id)
    if not node:
        raise HTTPException(404, "Knoten nicht gefunden")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(node, k, v)
    db.commit()
    db.refresh(node)
    return node


@router.delete("/datanodes/{node_id}")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    """REQ-4018: Knoten löschen (cascade)."""
    node = db.get(models.DataNode, node_id)
    if not node:
        raise HTTPException(404, "Knoten nicht gefunden")
    db.delete(node)
    db.commit()
    return {"status": "ok"}


@router.post("/datanodes/{node_id}/values", response_model=schemas.DataNodeValueRead)
def add_value(node_id: int, data: schemas.DataNodeValueCreate, db: Session = Depends(get_db)):
    """REQ-4018: Wert zu Knoten hinzufügen."""
    node = db.get(models.DataNode, node_id)
    if not node:
        raise HTTPException(404, "Knoten nicht gefunden")
    val = models.DataNodeValue(node_id=node_id, **data.model_dump())
    db.add(val)
    db.commit()
    db.refresh(val)
    return val


@router.delete("/datanodes/{node_id}/values/{value_id}")
def delete_value(node_id: int, value_id: int, db: Session = Depends(get_db)):
    """REQ-4018: Wert von Knoten löschen."""
    val = db.get(models.DataNodeValue, value_id)
    if not val or val.node_id != node_id:
        raise HTTPException(404, "Wert nicht gefunden")
    db.delete(val)
    db.commit()
    return {"status": "ok"}


def _import_node_recursive(
    data, 
    parent_id: Optional[int], 
    db: Session, 
    is_system: bool = True, 
    sort_order: int = 0,
    source: str = "bugmagnet"
):
    """
    REQ-4018: Rekursiver Import: Objekte → Knoten, Arrays → Werte, Strings → Einzelwert.
    Unterstützt Mischknoten (gleichzeitig Kinder und direkte Werte).
    """
    if isinstance(data, dict):
        # Dict → jeder Key wird ein Knoten
        for idx, (key, value) in enumerate(data.items()):
            node = models.DataNode(
                name=key,
                parent_id=parent_id,
                is_system=is_system,
                source=source,
                sort_order=idx,
            )
            db.add(node)
            db.flush()
            # Rekursiv die Werte des Knotens verarbeiten
            _import_node_recursive(value, node.id, db, is_system, 0, source)
    elif isinstance(data, list):
        # Liste → jedes Element als Wert oder Kindknoten
        for idx, item in enumerate(data):
            if isinstance(item, str):
                # String → direkter Wert
                db.add(models.DataNodeValue(node_id=parent_id, value=item, sort_order=idx))
            elif isinstance(item, dict):
                # Objekt in Liste → Kindknoten für jedes Key-Value-Pair
                for k, v in item.items():
                    node = models.DataNode(
                        name=k, 
                        parent_id=parent_id, 
                        is_system=is_system, 
                        source=source,
                        sort_order=idx
                    )
                    db.add(node)
                    db.flush()
                    _import_node_recursive(v, node.id, db, is_system, 0, source)
            else:
                # Andere Typen (Zahlen, Booleans) als String-Wert
                db.add(models.DataNodeValue(
                    node_id=parent_id, 
                    value=str(item), 
                    sort_order=idx
                ))
    elif isinstance(data, str):
        # Einzelner String → direkter Wert
        db.add(models.DataNodeValue(node_id=parent_id, value=data, sort_order=0))
    elif data is not None:
        # Zahlen, Booleans etc. als String
        db.add(models.DataNodeValue(
            node_id=parent_id, 
            value=str(data), 
            sort_order=0
        ))


# REQ-4013: Export/Import User DataNodes (hierarchisch)

def _node_to_dict(node) -> dict:
    """Rekursiv einen DataNode in ein serialisierbares Dict umwandeln."""
    return {
        "name": node.name,
        "values": [v.value for v in sorted(node.values, key=lambda x: x.sort_order)],
        "children": [_node_to_dict(c) for c in sorted(node.children, key=lambda x: x.sort_order)]
    }


@router.get("/export-user")
def export_user_datanodes(db: Session = Depends(get_db)):
    """REQ-4013: Exportiert eigene (nicht-System) DataNodes als JSON."""
    roots = db.query(DataNode).filter(
        DataNode.is_system == False,
        DataNode.parent_id == None
    ).order_by(DataNode.sort_order, DataNode.name).all()
    
    result = [_node_to_dict(node) for node in roots]
    return JSONResponse(
        content={"version": "2.0", "datanodes": result},
        headers={"Content-Disposition": "attachment; filename=my-dataclasses.json"}
    )


def _import_node_from_dict(data: dict, parent_id, db: Session):
    """Rekursiv einen Knoten aus Dict importieren."""
    name = data.get("name", "").strip()
    if not name:
        return
    # Prüfe ob bereits vorhanden (Merge)
    existing = db.query(DataNode).filter(
        DataNode.name == name,
        DataNode.parent_id == parent_id,
        DataNode.is_system == False
    ).first()
    if existing:
        node = existing
    else:
        node = DataNode(name=name, parent_id=parent_id, is_system=False)
        db.add(node)
        db.flush()
    # Werte hinzufügen (nur neue)
    existing_vals = {v.value for v in node.values}
    for val in data.get("values", []):
        if isinstance(val, str) and val.strip() and val not in existing_vals:
            db.add(DataNodeValue(node_id=node.id, value=val))
    # Kinder rekursiv
    for child in data.get("children", []):
        _import_node_from_dict(child, node.id, db)


@router.post("/import-user")
async def import_user_datanodes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """REQ-4013: Importiert eigene DataNodes aus einer JSON-Datei (Merge-Strategie)."""
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ungueltige JSON-Datei")
    
    imported = 0
    # Neues Format v2.0: {"datanodes": [...]}
    nodes_data = data.get("datanodes", [])
    if nodes_data:
        for item in nodes_data:
            _import_node_from_dict(item, None, db)
            imported += 1
    else:
        # Altes Format v1.0: {"dataclasses": [...]}
        classes_data = data.get("dataclasses", [])
        if not classes_data and isinstance(data, dict):
            # Legacy: {name: [values]}
            classes_data = [{"name": k, "values": v} for k, v in data.items() if isinstance(v, list)]
        for item in classes_data:
            name = item.get("name", "").strip()
            if not name:
                continue
            existing = db.query(DataNode).filter(
                DataNode.name == name,
                DataNode.parent_id == None,
                DataNode.is_system == False
            ).first()
            if existing:
                node = existing
            else:
                node = DataNode(name=name, parent_id=None, is_system=False)
                db.add(node)
                db.flush()
            existing_vals = {v.value for v in node.values}
            for val in item.get("values", []):
                if isinstance(val, str) and val.strip() and val not in existing_vals:
                    db.add(DataNodeValue(node_id=node.id, value=val))
            imported += 1
    
    db.commit()
    return {"status": "ok", "imported": imported}