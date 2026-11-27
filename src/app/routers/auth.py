"""Auth-Router fuer EPIC-18.

REQ-4001: Login, Logout, Refresh-Token
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
import jwt

from ..database import get_db
from ..models.auth import User, RefreshToken
from ..auth_utils import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from ..auth_deps import get_current_user, get_current_user_unrestricted, password_change_required, require_admin, require_writer, require_api_capable
from ..config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS, GREAT_COOKIE_SECURE
from ..rate_limiter import login_rate_limiter, first_start_hint_rate_limiter, password_change_rate_limiter
from ..config import GREAT_TRUST_PROXY_HEADERS
from ..schemas import PasswordChangeRequest, UserPreferencesRequest
from ..password_policy import PasswordError
from ..auth_service import change_own_password, is_first_start_hint_active

router = APIRouter(prefix="/auth", tags=["auth"])


# B-26: Hilfsfunktionen fuer Cookie-Secure-Flag
def _set_auth_cookie(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=name,
        value=value,
        httponly=True,
        secure=GREAT_COOKIE_SECURE,
        samesite="strict",
        max_age=max_age,
    )


def _delete_auth_cookie(response: Response, name: str) -> None:
    response.delete_cookie(
        key=name,
        secure=GREAT_COOKIE_SECURE,
        samesite="strict",
    )


def _issue_session(db: Session, response: Response, user: User) -> None:
    """Neues Access- und Refresh-Token (aktuelle token_version) als Cookies setzen."""
    access_token = create_access_token(user.id, user.username, user.role, user.token_version)
    refresh_token = create_refresh_token(user.id)
    db.add(RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    # B-26: httpOnly-Cookies ueber Helper
    _set_auth_cookie(response, "access_token", access_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    _set_auth_cookie(response, "refresh_token", refresh_token, JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)


@router.post("/login")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with username/password, returns access + refresh tokens in httpOnly cookies.

    REQ-4001: POST /auth/login akzeptiert Benutzername/Passwort und liefert JWT Access-Token + Refresh-Token.
    B-08: Rate-Limit pro IP|Username, Reset nach erfolgreichem Login.
    """
    # B-08: Rate limiting pro IP|Username
    client_ip = (
        request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
        if GREAT_TRUST_PROXY_HEADERS
        else request.client.host
    )
    key = f"{client_ip}|{form_data.username.lower()}"
    is_limited, retry_after = login_rate_limiter.is_rate_limited(key, is_failure=True)
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Zu viele Login-Versuche. Bitte versuche es spaeter erneut.",
            headers={"Retry-After": str(retry_after)},
        )

    # B-22: Case-insensitive user lookup
    user = db.query(User).filter(
        func.lower(User.username) == form_data.username.lower()
    ).first()
    if not user or not user.check_password(form_data.password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")

    # Deaktivierte Konten zuerst abweisen: sonst verriete die Antwort die Rolle api_user
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Konto ist deaktiviert")

    # REQ-6012: api_user kann sich nicht per Cookie/Login anmelden (nur per API-Token)
    if user.role == "api_user":
        raise HTTPException(
            status_code=403,
            detail="api_user kann sich nicht per Oberflaeche anmelden. Verwende ein API-Token.",
        )

    # B-08: Reset rate-limiter nach erfolgreichem Login
    login_rate_limiter.is_rate_limited(key, is_failure=False)

    # B-06: Token mit token_version erzeugen
    _issue_session(db, response, user)

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Login erfolgreich",
        "password_change_required": password_change_required(user),  # REQ-4028 AK-1, BUG A-01
        "language": user.language,  # REQ-6005
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

    # B-26: Delete cookies via helper
    _delete_auth_cookie(response, "access_token")
    _delete_auth_cookie(response, "refresh_token")

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
        raise HTTPException(status_code=401, detail="Ungültiger Refresh-Token")

    # Decode and validate
    try:
        payload = decode_refresh_token(refresh_token_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh-Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiger Refresh-Token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Ungültiger Token-Typ")

    # Get user
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Nutzer nicht gefunden")

    # B-06: Deaktivierte Nutzer koennen nicht refreshen
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Konto ist deaktiviert")

    # B-06: Token-Version pruefen (Access-Token im Cookie)
    access_token_str = request.cookies.get("access_token")
    if access_token_str:
        try:
            access_payload = decode_access_token(access_token_str)
            if access_payload.get("type") == "access":
                token_tv = access_payload.get("tv", 0)
                if token_tv != user.token_version:
                    raise HTTPException(status_code=401, detail="Sitzung abgelaufen, bitte neu anmelden")
        except jwt.ExpiredSignatureError:
            pass  # Access-Token abgelaufen ist OK – das ist der Grund fuer den Refresh
        except jwt.InvalidTokenError:
            pass  # Ungueltiger Access-Token ist OK – Refresh soll neuen liefern

    # B2: REVOKE old refresh token (Rotation!)
    rt.is_revoked = True
    db.commit()

    # B2: NEUE Tokens (Rotation)
    _issue_session(db, response, user)

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
    response: Response,
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
    # BUG B-06: Der Wechsel beendet alle Sitzungen (token_version). Die eigene
    # Sitzung erhaelt sofort neue Tokens, damit der Nutzer angemeldet bleibt.
    _issue_session(db, response, current_user)
    return {"message": "Passwort geaendert"}


# ---------------------------------------------------------------------------
# Test/Debug Endpoints (for dependency testing)
# ---------------------------------------------------------------------------

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user_unrestricted)):
    """Return current user info. REQ-4028 AK-1: liefert password_change_required.

    REQ-6005: Liefert auch language (Sprachpraferenz).
    Bewusst ohne Passwort-Sperre, damit das Frontend nach Login weiterleiten kann.
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "password_change_required": password_change_required(current_user),  # BUG A-01
        "language": current_user.language,
    }


# ---------------------------------------------------------------------------
# REQ-6005: Sprachpraferenz speichern
# ---------------------------------------------------------------------------

@router.put("/me/preferences")
def update_preferences(
    payload: UserPreferencesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_unrestricted),
):
    """Sprachpraferenz aktualisieren (REQ-6005).

    Body: {"language": "de" | "en"}
    Erfolg: {"language": "de" | "en" | null}
    """
    current_user.language = payload.language
    db.commit()
    db.refresh(current_user)
    return {"language": current_user.language}