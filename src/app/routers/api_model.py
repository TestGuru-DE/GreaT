"""REQ-6013: API-Endpunkte fuer Modell-Export/Import.

- GET  /api/v1/projects/{id}/model?format=yaml|json
- POST /api/v1/projects/import-model (neues Projekt)
- POST /api/v1/projects/{id}/model/preview (Aenderungsvorschau)
- PUT  /api/v1/projects/{id}/model (Aktualisierung)
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth_deps import require_editor_or_admin
from app.database import get_db
from app.logging_config import get_logger
from app.models.auth import User

from app import model_io

router = APIRouter(prefix="/api/v1/projects", tags=["model-io"])
log = get_logger(__name__)

# Maximalgroesse fuer Upload (5 MB)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.get("/{project_id}/model")
def export_project_model(
    project_id: int,
    format: str = Query(default="yaml", description="yaml oder json"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Exportiert das Testmodell eines Projekts als YAML oder JSON.

    REQ-6013: GET /api/v1/projects/{id}/model?format=yaml|json
    """
    if format not in ("yaml", "json"):
        raise HTTPException(status_code=400, detail="format muss 'yaml' oder 'json' sein")

    try:
        model = model_io.export_model(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if format == "yaml":
        content = model_io.to_yaml(model)
        media_type = "text/yaml"
        filename = f"{model.project_name}.great.yaml"
    else:
        content = model_io.to_json(model)
        media_type = "application/json"
        filename = f"{model.project_name}.great.json"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/import-model")
async def import_model_new_project(
    request: Request,
    content_type: str = Query(default="text/yaml"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Importiert ein Modell als neues Projekt.

    REQ-6013: POST /api/v1/projects/import-model
    Bei Namenskonflikt: Suffix _imported_{n}.
    """
    body = await request.body()

    # Groessenpruefung
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu gross. Maximum: {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    content = body.decode("utf-8")

    # Format ermitteln (aus Content-Type Header oder Query-Param)
    req_content_type = request.headers.get("content-type", content_type)
    if "yaml" in req_content_type or req_content_type == "text/yaml":
        fmt = "yaml"
    elif "json" in req_content_type or req_content_type == "application/json":
        fmt = "json"
    else:
        raise HTTPException(status_code=400, detail="Content-Type muss 'text/yaml' oder 'application/json' sein")

    try:
        project = model_io.apply_model(db, None, content, fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.exception("import_model_failed")
        raise HTTPException(status_code=400, detail=f"Import fehlgeschlagen: {e}")

    return {
        "status": "ok",
        "projectId": project.id,
        "projectName": project.name,
    }


@router.post("/{project_id}/model/preview")
def preview_model_changes(
    project_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Zeigt Aenderungsvorschau fuer bestehendes Projekt.

    REQ-6013: POST /api/v1/projects/{id}/model/preview
    Gibt Diff mit hinzugefuegt/geaendert/entfernt zurueck.
    """
    # Pruefe ob Projekt existiert
    from app import models as db_models
    project = db.query(db_models.Project).filter(db_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Validieren
    errors = model_io.validate_model(data)
    if errors:
        error_msgs = [f"{e.path}: {e.message}" for e in errors]
        raise HTTPException(status_code=400, detail="; ".join(error_msgs))

    try:
        diff = model_io.diff_model(db, project_id, data)
    except Exception as e:
        log.exception("diff_model_failed")
        raise HTTPException(status_code=500, detail=f"Diff-Berechnung fehlgeschlagen: {e}")

    return diff


@router.put("/{project_id}/model")
def update_project_model(
    project_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Aktualisiert ein bestehendes Projekt aus einem Modell.

    REQ-6013: PUT /api/v1/projects/{id}/model
    Bestehende Generierungen bleiben unveraendert.
    Transaktion: bei Fehler -> Rollback.
    """
    # Pruefe ob Projekt existiert
    from app import models as db_models
    project = db.query(db_models.Project).filter(db_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Validieren
    errors = model_io.validate_model(data)
    if errors:
        error_msgs = [f"{e.path}: {e.message}" for e in errors]
        raise HTTPException(status_code=400, detail="; ".join(error_msgs))

    try:
        updated = model_io.apply_model(db, project_id, data, "dict")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        log.exception("update_model_failed")
        raise HTTPException(status_code=500, detail=f"Aktualisierung fehlgeschlagen: {e}")

    return {
        "status": "ok",
        "projectId": updated.id,
        "projectName": updated.name,
    }