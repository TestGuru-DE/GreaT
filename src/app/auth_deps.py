"""Auth-Dependencies fuer EPIC-18.

REQ-4001: get_current_user Dependency
REQ-4020: Rollen-Pruefung Dependencies
REQ-4025: Neue Rollen-Dependencies fuer api_user-Einfuehrung
REQ-4028: Serverseitige Sperre bei gesetztem Flag default_password_active
REQ-6012: API-Tokens mit Bearer-Auth, Scopes, Rate-Limit
"""
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
import jwt

from .config import JWT_SECRET_KEY, JWT_ALGORITHM
from .database import get_db
from .models.auth import User, ApiToken

# REQ-4028 AK-2: maschinenlesbarer Code fuer die Passwortwechsel-Sperre
PASSWORD_CHANGE_REQUIRED = "password_change_required"


def password_change_required(user: User) -> bool:
    """BUG A-01: Passwortwechsel-Pflicht (REQ-4028) gilt nicht fuer api_user.

    Technische Nutzer koennen sich nicht per Oberflaeche anmelden (REQ-6012) und
    ihr Passwort daher nie aendern; die Pflicht wuerde ihre Tokens dauerhaft sperren.
    """
    return bool(user.default_password_active) and user.role != "api_user"

# REQ-6012: API-Token-Scope-Fehlercode
INSUFFICIENT_SCOPE = "insufficient_scope"

# REQ-6012: Endpunkte, die fuer API-Tokens gesperrt sind (Prefix-Matching)
BLOCKED_API_TOKEN_PATHS = (
    "/api/users",
    "/auth/change-password",
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/api/v1/api-tokens",
    "/api/v1/admin/api-tokens",
    "/api/backup",
)


def _validate_token_and_load_user(
    token: str,
    db: Session,
) -> Tuple[User | None, str | None]:
    """Core token validation shared by auth_deps and docs_auth middleware.

    Decodes the access token, loads the user, checks is_active and token_version.

    Returns:
        (user, None) on success
        (None, error_detail) on any failure
    """
    if not token:
        return None, "no_token"

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        return None, "token_expired"
    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None, "invalid_token"

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, "user_not_found"

    if not user.is_active:
        return None, "account_deactivated"

    # B-06: Token-Version pruefen – Sitzungs-Invalidierung
    token_tv = payload.get("tv", 0)
    if token_tv != user.token_version:
        return None, "session_expired"

    return user, None


# Mapping from internal error codes to HTTP detail messages
_ERROR_DETAILS = {
    "no_token": "Nicht authentifiziert",
    "token_expired": "Token abgelaufen",
    "invalid_token": "Ungultiges Token",
    "user_not_found": "Nutzer nicht gefunden",
    "account_deactivated": "Konto ist deaktiviert",
    "session_expired": "Sitzung abgelaufen, bitte neu anmelden",
}


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def _rate_limit_error(retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={
            "code": "rate_limit_exceeded",
            "detail": "Rate-Limit fuer API-Token ueberschritten",
        },
        headers={"Retry-After": str(retry_after)},
    )


def _authenticate_with_api_token(
    request: Request,
    db: Session,
) -> Tuple[User, ApiToken] | None:
    """REQ-6012: Authenticate via Bearer API token.

    Returns (user, token_record) on success, None on failure.
    Raises HTTPException 403 for deactivated users, 429 when rate-limited.

    BUG A-07: Das Rate-Limit zaehlt erst nach erfolgreicher Pruefung je Token-ID.
    Fehlversuche zaehlen je Client-IP und werden vor der teuren argon2-Pruefung
    abgewiesen. Ein gefaelschtes Token mit fremdem Praefix sperrt so nur den
    Absender, nie das echte Token.
    Das Ergebnis wird je Anfrage zwischengespeichert (eine Pruefung, eine Zaehlung).
    """
    from .api_token_service import verify_api_token
    from .rate_limiter import token_rate_limiter, token_failure_rate_limiter

    cached = getattr(request.state, "api_token_auth", None)
    if cached is not None:
        return cached or None

    raw_token = _extract_bearer_token(request)
    if not raw_token:
        return None

    client_ip = request.client.host if request.client else "unknown"
    is_limited, retry_after = token_failure_rate_limiter.peek(client_ip)
    if is_limited:
        raise _rate_limit_error(retry_after)

    result = verify_api_token(db, raw_token)
    if result is None:
        token_failure_rate_limiter.is_rate_limited(client_ip)  # Fehlversuch zaehlen
        request.state.api_token_auth = False
        return None

    # New signature: (user, token_record, status)
    user, token_record, status = result

    is_limited, retry_after = token_rate_limiter.is_rate_limited(f"token:{token_record.id}")
    if is_limited:
        raise _rate_limit_error(retry_after)

    # REQ-6012: Deactivated user -> 403
    if status == "deactivated":
        raise HTTPException(
            status_code=403,
            detail="Konto ist deaktiviert",
        )

    # REQ-6012 AK: api_user cannot use cookie-based auth (handled in login)
    # But api_user CAN use API tokens – that's their only method

    # REQ-6012: Update last_used_at
    from .api_token_service import update_last_used
    update_last_used(db, token_record, request.client.host if request.client else None)

    request.state.api_token_auth = (user, token_record)
    return user, token_record


def _is_api_token_blocked_path(path: str) -> bool:
    """REQ-6012: Check if path is blocked for API tokens."""
    for blocked in BLOCKED_API_TOKEN_PATHS:
        if path == blocked or path.startswith(blocked + "/") or path.startswith(blocked + "?"):
            return True
    return False


_READ_METHODS = ("GET", "HEAD", "OPTIONS")


def required_scope_for(method: str, path: str) -> Optional[str]:
    """BUG A-03: Scope, den ein API-Token fuer diese Anfrage braucht.

    Gilt fuer alle /api/*-Pfade (REQ-6012: Schnittmenge aus Rolle und Scopes):
    - Modell-Datei (REQ-6013): models:read (lesen) bzw. models:write
    - Testfall-Exporte: export
    - Generierung, Lueckenschluss: generate
    - alles andere: projects:read (lesen) bzw. projects:write (aendern)
    Ausserhalb von /api (z. B. /auth/me) ist kein Scope noetig.
    """
    if not path.startswith("/api/"):
        return None
    method = method.upper()
    is_read = method in _READ_METHODS
    segments = [s for s in path.split("/") if s]
    if "model" in segments or segments[-1] == "import-model":
        return "models:read" if is_read else "models:write"
    if "export" in segments and is_read:
        return "export"
    if not is_read and segments[-1] in ("generate", "gap-fill"):
        return "generate"
    return "projects:read" if is_read else "projects:write"


def _check_token_scope(request: Request, token_record: ApiToken) -> None:
    """BUG A-03: 403 insufficient_scope, wenn dem Token der noetige Scope fehlt."""
    scope = required_scope_for(request.method, request.url.path)
    if scope is not None and not token_record.has_scope(scope):
        raise HTTPException(
            status_code=403,
            detail=f"API-Token hat nicht den erforderlichen Scope: {scope}",
            headers={"X-Error-Code": INSUFFICIENT_SCOPE},
        )


def _load_authenticated_user(request: Request, db: Session) -> User:
    """Liest und validiert das Access-Token. Prueft NICHT die Passwort-Sperre.

    REQ-6012: Zentraler Resolver – Cookie ODER Bearer API-Token.
    """
    # Try cookie first (existing behavior)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        user, error = _validate_token_and_load_user(cookie_token, db)
        if user is not None:
            return user

    # Try Bearer API token
    api_result = _authenticate_with_api_token(request, db)
    if api_result is not None:
        user, token_record = api_result

        # REQ-6012: API tokens blocked on certain endpoints
        if _is_api_token_blocked_path(request.url.path):
            raise HTTPException(
                status_code=403,
                detail="API-Tokens duerfen nicht fuer diesen Endpunkt verwendet werden",
                headers={"X-Error-Code": "api_token_blocked_endpoint"},
            )

        _check_token_scope(request, token_record)  # BUG A-03
        return user

    # Neither worked
    # Determine error from cookie attempt
    if cookie_token:
        _, error = _validate_token_and_load_user(cookie_token, db)
        detail = _ERROR_DETAILS.get(error, "Ungultiges Token")
        status = 403 if error == "account_deactivated" else 401
    else:
        detail = "Nicht authentifiziert"
        status = 401

    raise HTTPException(status_code=status, detail=detail)


def get_current_user_unrestricted(request: Request, db: Session = Depends(get_db)) -> User:
    """Authentifizierter Nutzer OHNE Passwort-Sperre.

    REQ-4028 AK-2: Ausnahmen von der Sperre sind GET /auth/me und POST /auth/change-password.
    Alle anderen geschuetzten Routen verwenden get_current_user (mit Sperre).
    REQ-6012: Akzeptiert auch Bearer API-Tokens.
    """
    return _load_authenticated_user(request, db)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate current user from access token cookie or Bearer API token.

    REQ-4001: Alle bestehenden API-Endpunkte pruefen ein gueltiges Token.
    REQ-4028 AK-2/AK-7: Solange das Flag default_password_active gesetzt ist, wird jede
    Route, die diese Dependency nutzt (direkt oder ueber require_*), mit 403
    password_change_required abgewiesen. Die Pruefung ist serverseitig und zentral.
    REQ-6012: Akzeptiert auch Bearer API-Tokens (ohne Passwort-Sperre).

    Returns:
        The authenticated User object

    Raises:
        HTTPException 401: If no token, invalid token, or user not found
        HTTPException 403: If user account is deactivated
        HTTPException 403: password_change_required (REQ-4028)
    """
    user = _load_authenticated_user(request, db)
    if password_change_required(user):  # BUG A-01
        raise HTTPException(status_code=403, detail=PASSWORD_CHANGE_REQUIRED)
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control.

    REQ-4020: Rollenpruefung erfolgt serverseitig auf allen schreibenden Endpunkten.
    REQ-6012: Bei API-Tokens gilt zusatzlich die Schnittmenge aus Rolle und Scopes.

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


def require_scope(*required_scopes: str):
    """REQ-6012: Dependency factory for API-token scope checking.

    Prueft, ob der API-Token (falls verwendet) die noetigen Scopes hat.
    Seit A-03 prueft get_current_user den Scope je Pfad zentral; diese
    Dependency bleibt fuer zusaetzliche, ausdrueckliche Anforderungen.
    Bei Cookie-Auth (keine API-Token) wird kein Scope-Check durchgefuehrt.

    Die Rolle des Nutzers gilt weiterhin als Obergrenze:
    - Viewer kann nie projects:write nutzen (selbst wenn Scope gesetzt)
    - api_user kann nur per Token zugreifen (kein Cookie-Login)

    Usage:
        @router.post("/generate", dependencies=[Depends(require_scope("generate"))])

    Args:
        *required_scopes: Scopes die der Token haben muss

    Returns:
        Dependency function that checks the current request's token scopes
    """
    def scope_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Token-Ergebnis aus get_current_user (je Anfrage zwischengespeichert)
        api_auth = getattr(request.state, "api_token_auth", None)
        if not api_auth:
            # Cookie auth – no scope check needed (role is the gate)
            return current_user

        _, token_record = api_auth

        # Check each required scope
        for scope in required_scopes:
            if not token_record.has_scope(scope):
                raise HTTPException(
                    status_code=403,
                    detail=f"API-Token hat nicht den erforderlichen Scope: {scope}",
                    headers={"X-Error-Code": INSUFFICIENT_SCOPE},
                )

        # REQ-6012: Rolle schlaegt Scope – Viewer kann nie schreiben
        if current_user.role == "viewer" and any(
            s in required_scopes for s in ("projects:write", "models:write")
        ):
            raise HTTPException(
                status_code=403,
                detail="Viewer-Rolle erlaubt keine Schreiboperationen",
                headers={"X-Error-Code": INSUFFICIENT_SCOPE},
            )

        return current_user
    return scope_checker


# ---------------------------------------------------------------------------
# Pre-built dependencies for common role checks
# ---------------------------------------------------------------------------

# admin only
require_admin = require_role("admin")

# REQ-4025: require_writer – fuer alle Schreib-Operationen (POST/PUT/PATCH/DELETE)
# Erlaubt: admin, editor
# Blockiert: viewer, api_user
require_writer = require_role("admin", "editor")

# Deprecated alias for backward compatibility – use require_writer instead
require_editor_or_admin = require_writer

# REQ-4025: require_api_capable – fuer alle Lese-Operationen (GET)
# Erlaubt: admin, editor, viewer, api_user
require_api_capable = require_role("admin", "editor", "viewer", "api_user")