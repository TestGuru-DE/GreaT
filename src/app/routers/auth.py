"""Auth-Router fuer EPIC-18.

REQ-4001: Login, Logout, Refresh-Token
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt

from ..database import get_db
from ..models.auth import User, RefreshToken
from ..auth_utils import create_access_token, create_refresh_token, decode_token
from ..auth_deps import get_current_user, get_current_user_unrestricted, require_admin, require_editor_or_admin, require_writer, require_api_capable
from ..config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS
from ..rate_limiter import login_rate_limiter, first_start_hint_rate_limiter, password_change_rate_limiter
from ..schemas import PasswordChangeRequest
from ..password_policy import PasswordError
from ..auth_service import change_own_password, is_first_start_hint_active

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with username/password, returns access + refresh tokens in httpOnly cookies.

    REQ-4001: POST /auth/login akzeptiert Benutzername/Passwort und liefert JWT Access-Token + Refresh-Token.
    """
    # Rate limiting
    client_ip = request.client.host
    is_limited, retry_after = login_rate_limiter.is_rate_limited(client_ip)
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Zu viele Login-Versuche. Bitte versuche es spaeter erneut.",
            headers={"Retry-After": str(retry_after)},
        )

    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.check_password(form_data.password):
        raise HTTPException(status_code=401, detail="Ungultige Anmeldedaten")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Konto ist deaktiviert")

    # Create tokens
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token in DB
    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()

    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True in Production (HTTPS)
        samesite="strict",
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Login erfolgreich",
        "password_change_required": bool(user.default_password_active),  # REQ-4028 AK-1
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Logout: revoke refresh token, clear cookies.

    REQ-4001: Logout invalidiert Refresh-Token serverseitig.
    """
    refresh_token_str = request.cookies.get("refresh_token")
    if refresh_token_str:
        rt = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_str).first()
        if rt:
            rt.is_revoked = True
            db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logout erfolgreich"}


@router.post("/refresh")
def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token. Implements token rotation.

    REQ-4001: Token-Erneuerung mit Refresh-Token.
    B2: Refresh-Token-Rotation – alter Token wird revokiert, neuer generiert.
    """
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(status_code=401, detail="Kein Refresh-Token")

    # Check if token is revoked
    rt = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token_str,
        RefreshToken.is_revoked == False,
    ).first()
    if not rt:
        raise HTTPException(status_code=401, detail="Ungultiger Refresh-Token")

    # Decode and validate
    try:
        payload = decode_token(refresh_token_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh-Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungultiger Refresh-Token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Ungultiger Token-Typ")

    # Get user
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Nutzer nicht gefunden")

    # B2: REVOKE old refresh token (Rotation!)
    rt.is_revoked = True
    db.commit()

    # Create NEW tokens
    new_access_token = create_access_token(user.id, user.username, user.role)
    new_refresh_token = create_refresh_token(user.id)

    # Store new refresh token in DB
    new_rt = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)
    db.commit()

    # Set new httpOnly cookies (BOTH access AND refresh)
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,  # B2: NEUER Token!
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"message": "Token erneuert"}


# ---------------------------------------------------------------------------
# REQ-4027 AK-6 / AK-11 / AK-13: Erststart-Hinweis (ohne Auth, rate-limitiert)
# ---------------------------------------------------------------------------

@router.get("/first-start-hint")
def first_start_hint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Liefert ausschliesslich {"show_hint": bool} (REQ-4027 AK-6, AK-13).

    show_hint ist True, wenn ein aktiver Nutzer mit gesetztem Flag default_password_active existiert.
    Keine Namen, IDs, Rollen oder Anzahlen. Rate-Limit 10/Minute/IP (AK-11).
    """
    response.headers["Cache-Control"] = "no-store"
    client_ip = request.client.host
    is_limited, retry_after = first_start_hint_rate_limiter.is_rate_limited(client_ip)
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="too_many_requests",
            headers={"Retry-After": str(retry_after), "Cache-Control": "no-store"},
        )
    return {"show_hint": is_first_start_hint_active(db)}


# ---------------------------------------------------------------------------
# REQ-4028 AK-3 / AK-8: Selbst-Passwortwechsel (alle Rollen, auch bei Sperre)
# ---------------------------------------------------------------------------

@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_unrestricted),
):
    """Eigenes Passwort aendern (REQ-4028 AK-3).

    Body: {"current_password": str, "new_password": str}
    Fehlercodes (HTTP 400, detail): current_password_invalid, password_is_default,
    password_too_short, password_too_long. Rate-Limit: 429 detail too_many_attempts
    (10 Versuche je Minute und Konto, jeder Versuch zaehlt).
    Erfolg: {"message": "Passwort geaendert"}; Flag default_password_active wird geloescht.
    """
    key = f"user:{current_user.id}"
    is_limited, retry_after = password_change_rate_limiter.is_rate_limited(key)
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="too_many_attempts",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        change_own_password(db, current_user, payload.current_password, payload.new_password)
    except PasswordError as exc:
        raise HTTPException(status_code=400, detail=exc.code)
    return {"message": "Passwort geaendert"}


# ---------------------------------------------------------------------------
# Test/Debug Endpoints (for dependency testing)
# ---------------------------------------------------------------------------

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user_unrestricted)):
    """Return current user info. REQ-4028 AK-1: liefert password_change_required.

    Bewusst ohne Passwort-Sperre, damit das Frontend nach Login weiterleiten kann.
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "password_change_required": bool(current_user.default_password_active),
    }


@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_admin)):
    """Admin-only endpoint. Used for testing require_role dependency."""
    return {
        "message": "Zugriff als Admin gewaehrt",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/editor-or-admin")
def editor_or_admin(current_user: User = Depends(require_editor_or_admin)):
    """Editor-or-admin endpoint. Used for testing require_role dependency."""
    return {
        "message": "Zugriff als Editor/Admin gewaehrt",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/writer-only")
def writer_only(current_user: User = Depends(require_writer)):
    """Writer-only endpoint (admin, editor). Used for testing require_writer dependency."""
    return {
        "message": "Zugriff als Writer gewaehrt",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/api-capable")
def api_capable(current_user: User = Depends(require_api_capable)):
    """API-capable endpoint (admin, editor, viewer, api_user). Used for testing require_api_capable dependency."""
    return {
        "message": "Zugriff als API-Capable gewaehrt",
        "username": current_user.username,
        "role": current_user.role,
    }