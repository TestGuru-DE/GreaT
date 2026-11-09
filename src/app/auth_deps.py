"""Auth-Dependencies fuer EPIC-18.

REQ-4001: get_current_user Dependency
REQ-4020: Rollen-Pruefung Dependencies
REQ-4025: Neue Rollen-Dependencies fuer api_user-Einfuehrung
REQ-4028: Serverseitige Sperre bei gesetztem Flag default_password_active
"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
import jwt

from .config import JWT_SECRET_KEY, JWT_ALGORITHM
from .database import get_db
from .models.auth import User

# REQ-4028 AK-2: maschinenlesbarer Code fuer die Passwortwechsel-Sperre
PASSWORD_CHANGE_REQUIRED = "password_change_required"


def _load_authenticated_user(request: Request, db: Session) -> User:
    """Liest und validiert das Access-Token. Prueft NICHT die Passwort-Sperre."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Ungultiges Token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Nutzer nicht gefunden")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Konto ist deaktiviert")

    return user


def get_current_user_unrestricted(request: Request, db: Session = Depends(get_db)) -> User:
    """Authentifizierter Nutzer OHNE Passwort-Sperre.

    REQ-4028 AK-2: Ausnahmen von der Sperre sind GET /auth/me und POST /auth/change-password.
    Alle anderen geschuetzten Routen verwenden get_current_user (mit Sperre).
    """
    return _load_authenticated_user(request, db)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate current user from access token cookie.

    REQ-4001: Alle bestehenden API-Endpunkte pruefen ein gueltiges Token.
    REQ-4028 AK-2/AK-7: Solange das Flag default_password_active gesetzt ist, wird jede
    Route, die diese Dependency nutzt (direkt oder ueber require_*), mit 403
    password_change_required abgewiesen. Die Pruefung ist serverseitig und zentral.

    Returns:
        The authenticated User object

    Raises:
        HTTPException 401: If no token, invalid token, or user not found
        HTTPException 403: If user account is deactivated
        HTTPException 403: password_change_required (REQ-4028)
    """
    user = _load_authenticated_user(request, db)
    if user.default_password_active:
        raise HTTPException(status_code=403, detail=PASSWORD_CHANGE_REQUIRED)
    return user



def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control.

    REQ-4020: Rollenpruefung erfolgt serverseitig auf allen schreibenden Endpunkten.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        or
        @router.get("/admin")
        def admin_endpoint(current_user: User = Depends(require_role("admin"))):
            ...

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks the current user's role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Diese Aktion erfordert die Rolle: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


# ---------------------------------------------------------------------------
# Pre-built dependencies for common role checks
# ---------------------------------------------------------------------------

# Legacy: Nur admin, editor, viewer (ohne api_user) – fuer UI-Endpunkte
require_any_authenticated_user = require_role("admin", "editor", "viewer")

# admin only
require_admin = require_role("admin")

# editor + admin (legacy alias, bleibt erhalten)
require_editor_or_admin = require_role("editor", "admin")

# REQ-4025: require_writer – fuer alle Schreib-Operationen (POST/PUT/PATCH/DELETE)
# Erlaubt: admin, editor
# Blockiert: viewer, api_user
require_writer = require_role("admin", "editor")

# REQ-4025: require_api_capable – fuer alle Lese-Operationen (GET)
# Erlaubt: admin, editor, viewer, api_user
require_api_capable = require_role("admin", "editor", "viewer", "api_user")