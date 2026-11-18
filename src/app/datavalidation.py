"""Validierungshilfen fuer Datenknoten.

B-09: Zyklen-Pruefung und Reparatur fuer parent_id-Referenzen.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import DataNode

logger = logging.getLogger("great.datavalidation")


def validate_parent_id(
    db: Session,
    node_id: int,
    parent_id: Optional[int],
) -> None:
    """Prueft parent_id vor dem Speichern.

    Args:
        db: Datenbank-Session
        node_id: ID des zu aendernden Knotens
        parent_id: Neue parent_id (None = Wurzel)

    Raises:
        HTTPException 404: Elternknoten existiert nicht
        HTTPException 422: Zyklus erkannt
    """
    if parent_id is None:
        return  # Wurzel ist immer ok

    # Existiert der Elternknoten?
    parent = db.get(DataNode, parent_id)
    if not parent:
        raise HTTPException(
            status_code=404,
            detail="Elternknoten nicht gefunden",
        )

    # Zyklus-Pruefung: parent_id == node_id (Selbstreferenz)
    if parent_id == node_id:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "cyclic_parent",
                "detail": (
                    "Ein Knoten kann nicht unter sich selbst oder einem "
                    "seiner Unterknoten eingeordnet werden."
                ),
            },
        )

    # Iterative Nachfahren-Pruefung mit besuchten-Knoten-Schutz:
    # Laufe die Parent-Kette des gewaehlten Elternknotens nach oben.
    # Trifft der Pfad auf node_id, waere ein Zyklus.
    visited: set[int] = set()
    current = parent_id
    while current is not None:
        if current == node_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "cyclic_parent",
                    "detail": (
                        "Ein Knoten kann nicht unter sich selbst oder einem "
                        "seiner Unterknoten eingeordnet werden."
                    ),
                },
            )
        if current in visited:
            # Bereits vorhandener Zyklus in Bestandsdaten – abbrechen
            break
        visited.add(current)
        node = db.get(DataNode, current)
        current = node.parent_id if node else None


def repair_cycles_on_startup(db: Session) -> int:
    """Repariert vorhandene Zyklen in Bestandsdaten.

    Setzt Knoten mit zyklischen parent_id-Referenzen auf parent_id=NULL (Wurzel).
    Idempotent. Gibt Anzahl reparierter Knoten zurueck.
    """
    all_nodes = db.query(DataNode).all()
    node_map = {n.id: n for n in all_nodes}

    repaired = 0
    for node in all_nodes:
        if node.parent_id is None:
            continue

        # Iterative Pruefung: folgt parent_id-Kette, merkt besuchte Knoten
        visited: set[int] = set()
        current = node.parent_id
        while current is not None:
            if current == node.id:
                # Zyklus erkannt – reparieren
                logger.warning(
                    "Cycle detected for node %s (%s), setting parent_id=NULL",
                    node.id,
                    node.name,
                )
                node.parent_id = None
                repaired += 1
                break
            if current in visited:
                # Zyklus in der Kette (nicht direkt zu diesem Knoten) –
                # Sicherheitsnetz: parent_id=NULL
                logger.warning(
                    "Node %s (%s) references a cyclic chain, setting parent_id=NULL",
                    node.id,
                    node.name,
                )
                node.parent_id = None
                repaired += 1
                break
            visited.add(current)
            parent = node_map.get(current)
            current = parent.parent_id if parent else None

    if repaired:
        db.commit()

    return repaired