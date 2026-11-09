"""First-Admin-Bootstrapping fuer EPIC-18.

REQ-4020: Erste registrierte Person wird automatisch Admin.
REQ-4027: Standardpasswort-Konstante (einzige Definition) und Flag default_password_active.
REQ-4028: Flag steuert die serverseitige Passwortwechsel-Sperre.
"""
from sqlalchemy.orm import Session

from .models.auth import User

# REQ-4027 AK-1: einzige Definition des Standardpassworts (CR-4026-01).
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "changeme123!"
# REQ-4027 AK-10: Altwert vor CR-4026-01. Wird nur fuer die Bestandsmigration erkannt.
LEGACY_DEFAULT_ADMIN_PASSWORD = "admin123"


def ensure_first_admin(db: Session) -> User:
    """Create first admin user if no users exist.

    REQ-4020: Erste registrierte Person wird automatisch Admin.
    REQ-4027 AK-10: Der neu angelegte Default-Admin erhaelt das Flag default_password_active.

    Returns the first admin user. If no users exist, creates a default
    admin (username DEFAULT_ADMIN_USERNAME, password DEFAULT_ADMIN_PASSWORD).
    The password MUST be changed (REQ-4028 erzwingt dies serverseitig).

    Args:
        db: SQLAlchemy database session

    Returns:
        The first admin user (existing or newly created)
    """
    # Check if any users exist
    first_user = db.query(User).first()
    if first_user is not None:
        # Users exist, return first admin
        admin = db.query(User).filter(User.role == "admin").first()
        if admin:
            return admin
        # No admin exists but other users do - this shouldn't happen in normal flow
        # but we return None to signal the issue
        return None  # type: ignore

    # Create default admin
    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        role="admin",
        is_first_admin=True,
        is_active=True,
        default_password_active=True,
    )
    admin.set_password(DEFAULT_ADMIN_PASSWORD)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def backfill_default_password_flags(db: Session) -> None:
    """REQ-4027 AK-10: Bestandsmigration des Flags default_password_active.

    Prueft aktive Erst-Admins gegen die Standardpasswoerter und setzt das Flag
    entsprechend (True bei Standardpasswort, sonst False). Idempotent.
    Das Ergebnis wird weder ausgegeben noch geloggt (AK-12).
    """
    admins = db.query(User).filter(User.is_first_admin == True, User.is_active == True).all()  # noqa: E712
    changed = False
    for admin in admins:
        is_default = admin.check_password(DEFAULT_ADMIN_PASSWORD) or admin.check_password(
            LEGACY_DEFAULT_ADMIN_PASSWORD
        )
        if bool(admin.default_password_active) != is_default:
            admin.default_password_active = is_default
            changed = True
    if changed:
        db.commit()
