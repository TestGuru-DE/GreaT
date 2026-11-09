"""REQ-4023: Projekt-Sharing Endpunkte"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.project_membership import ProjectMembership
from ..models.auth import User
from ..auth_deps import get_current_user, require_editor_or_admin, require_admin, require_api_capable
from ..models import Project
from ..schemas import ProjectMemberRead, AddProjectMemberRequest

router = APIRouter(prefix="/api/sharing", tags=["sharing"])


@router.get("/project/{project_id}/members", response_model=list[ProjectMemberRead])
def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_api_capable),
):
    """Liste aller Mitglieder eines Projekts."""
    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf dieses Projekt")

    members = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id
    ).all()
    return members


@router.post("/project/{project_id}/members", status_code=201, response_model=ProjectMemberRead)
def add_project_member(
    project_id: int,
    payload: AddProjectMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Mitglied zu einem Projekt hinzufuegen."""
    # Pruefe ob Projekt existiert
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    # Pruefe ob current_user Zugriff auf das Projekt hat (editor/admin oder Admin)
    if current_user.role != "admin":
        own_membership = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.role == "editor",
        ).first()
        if not own_membership:
            raise HTTPException(status_code=403, detail="Nur Projekt-Editor oder Admin koennen Mitglieder hinzufuegen.")

    # Pruefe ob User existiert
    target_user = db.get(User, payload.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden.")

    # Pruefe ob bereits Mitglied
    existing = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == payload.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Nutzer ist bereits Mitglied dieses Projekts.")

    membership = ProjectMembership(
        project_id=project_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.delete("/project/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    """Mitglied aus einem Projekt entfernen."""
    # Pruefe ob Projekt existiert
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden.")

    # Pruefe ob current_user Zugriff auf das Projekt hat
    if current_user.role != "admin":
        own_membership = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == current_user.id,
            ProjectMembership.role == "editor",
        ).first()
        if not own_membership:
            raise HTTPException(status_code=403, detail="Nur Projekt-Editor oder Admin koennen Mitglieder entfernen.")

    membership = db.query(ProjectMembership).filter(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Mitgliedschaft nicht gefunden.")

    db.delete(membership)
    db.commit()
    return {"ok": True, "user_id": user_id}