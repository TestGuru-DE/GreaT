"""REQ-4025: Benutzerverwaltung API-Endpunkte.

Admin kann Nutzer verwalten (CRUD), Passwort aendern.
Alle Endpunkte erfordern Admin-Rolle (außer Passwort-aendern fuer sich selbst).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.auth import User, RefreshToken
from ..models.project_membership import ProjectMembership
from ..auth_deps import get_current_user, require_admin, require_writer
from ..password_policy import PasswordError
from ..auth_service import admin_set_password
from ..schemas import UserCreate, UserUpdate, UserPasswordChange, UserRead

# Admin-only router fuer CRUD-Operationen
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)


@router.get("/", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """REQ-4025: Listet alle Nutzer (Admin nur)."""
    users = db.query(User).order_by(User.id).all()
    return users


@router.post("/", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """REQ-4025: Erstellt einen neuen Nutzer (Admin nur)."""
    # Pruefe auf Duplikat
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Nutzername '{payload.username}' existiert bereits",
        )

    new_user = User(
        username=payload.username,
        role=payload.role,
        is_active=True,
    )
    new_user.set_password(payload.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """REQ-4025: Aktualisiert Rolle und/oder is_active (Admin nur).

    Admin kann sich selbst nicht deaktivieren oder seine eigene Rolle aendern.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")

    # Admin kann sich selbst nicht deaktivieren
    if target.id == current_user.id and payload.is_active is False:
        raise HTTPException(
            status_code=403,
            detail="Du kannst dich selbst nicht deaktivieren",
        )

    # Admin kann seine eigene Rolle nicht aendern
    if target.id == current_user.id and payload.role is not None:
        raise HTTPException(
            status_code=403,
            detail="Du kannst deine eigene Rolle nicht aendern",
        )

    if payload.role is not None:
        target.role = payload.role
    if payload.is_active is not None:
        target.is_active = payload.is_active

    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """REQ-4025: Loescht einen Nutzer (Admin nur, nicht sich selbst).

    Cascade: Projektmitgliedschaften werden entfernt.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")

    # Kann sich selbst nicht loeschen
    if target.id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Du kannst dich selbst nicht loeschen",
        )

    # Projektmitgliedschaften entfernen
    db.query(ProjectMembership).filter(
        ProjectMembership.user_id == user_id
    ).delete(synchronize_session=False)

    # Refresh-Tokens entfernen
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).delete(synchronize_session=False)

    db.delete(target)
    db.commit()
    return {"message": f"Nutzer '{target.username}' geloescht"}


# ---------------------------------------------------------------------------
# Passwort-Aenderung: Jeder authentifizierte Nutzer kann sein eigenes Passwort
# aendern; Admin kann das Passwort jedes Nutzers aendern.
# Dieser Endpunkt hat KEINE Admin-Dependency auf Router-Ebene.
# ---------------------------------------------------------------------------

password_router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


@password_router.put("/{user_id}/password")
def change_password(
    user_id: int,
    payload: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """REQ-4025: Aendert das Passwort eines Nutzers.

    Admin kann das Passwort jedes Nutzers aendern.
    Editor kann sein eigenes Passwort aendern.
    api_user ist blockiert (require_writer).
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden")

    # Admin kann fuer jeden aendern
    if current_user.role != "admin":
        # Nicht-Admin kann nur sein eigenes Passwort aendern
        if target.id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Du kannst nur dein eigenes Passwort aendern",
            )

    try:
        admin_set_password(db, target, payload.new_password)  # REQ-4028 AK-4/AK-5, Flag-Rueckstellung AK-6
    except PasswordError as exc:
        raise HTTPException(status_code=400, detail=exc.code)
    return {"message": f"Passwort fuer '{target.username}' geaendert"}