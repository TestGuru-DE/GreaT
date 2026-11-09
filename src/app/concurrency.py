"""Optimistic Concurrency Control.

REQ-4021: Versionsfeld + Konflikterkennung (HYBRID-Ansatz, ADR-012)
REQ-4024: Audit-Trail (last_modified_by, last_modified_at)
"""
from datetime import datetime, timezone
from typing import Optional, Type, TypeVar
from fastapi import HTTPException
from sqlalchemy.orm import Session

M = TypeVar("M")


def check_version(
    db: Session,
    model: Type[M],
    entity_id: int,
    client_version: Optional[int],
) -> M:
    """Prueft die Version und inkrementiert sie bei Erfolg.

    Args:
        db: Datenbank-Session
        model: SQLAlchemy-Model-Klasse
        entity_id: ID der Entitaet
        client_version: Version vom Client (None bei erstem Zugriff)

    Returns:
        Die aktualisierte Entitaet mit inkrementierter Version

    Raises:
        HTTPException 404: Nicht gefunden
        HTTPException 409: Version-Konflikt
    """
    entity = db.query(model).get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Ressource nicht gefunden")

    current_version = getattr(entity, "version", None)

    # Wenn Client eine Version sendet, pruefe auf Konflikt
    if client_version is not None and current_version is not None:
        if current_version != client_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "version_conflict",
                    "message": "Diese Ressource wurde zwischenzeitlich geaendert",
                    "client_version": client_version,
                    "server_version": current_version,
                }
            )

    # Version inkrementieren
    if current_version is not None:
        entity.version = current_version + 1

    return entity


def update_with_version(
    db: Session,
    model: Type[M],
    entity_id: int,
    client_version: Optional[int],
    update_data: dict,
    current_user_id: Optional[int] = None,  # REQ-4024: Audit-Trail
) -> M:
    """Update mit Version-Pruefung, automatischem Inkrement und Audit-Trail.

    Args:
        db: Datenbank-Session
        model: SQLAlchemy-Model-Klasse
        entity_id: ID der Entitaet
        client_version: Version vom Client (None = kein Konflikt-Check)
        update_data: Dictionary mit Feldern zum Aktualisieren
        current_user_id: ID des aktuellen Users fuer Audit-Trail (REQ-4024)

    Returns:
        Die aktualisierte Entitaet

    Raises:
        HTTPException 404: Nicht gefunden
        HTTPException 409: Version-Konflikt
    """
    entity = check_version(db, model, entity_id, client_version)

    # Update Felder (nur existierende Attribute)
    for key, value in update_data.items():
        if hasattr(entity, key) and key not in ("id", "version", "created_at"):
            setattr(entity, key, value)

    # REQ-4024: Audit-Trail setzen
    if current_user_id is not None:
        if hasattr(entity, "last_modified_by"):
            entity.last_modified_by = current_user_id
        if hasattr(entity, "last_modified_at"):
            entity.last_modified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entity)
    return entity