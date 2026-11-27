"""Docs-Auth-Middleware fuer Swagger-UI und OpenAPI-Schema.

RISK-S-006: Swagger-UI ohne Authentifizierung erreichbar (Score 16, HIGH)
RISK-S-007: OpenAPI-Schema offenlegt interne API-Strukturen (Score 12, HIGH)

Diese Middleware schuetzt /docs, /redoc und /openapi.json durch
Authentifizierung und Rollenpruefung (admin/editor).
BUG A-08 (REQ-6012): Zusaetzlich genuegt ein beliebiges gueltiges API-Token
(`Authorization: Bearer great_pat_...`), damit Pipelines das Schema laden koennen.

WICHTIG: In main.py muss diese Middleware ZULETZT hinzugefuegt werden,
weil Starlette-Middleware LIFO (Last-In-First-Out) ausgefuehrt wird.
So laeuft sie als ERSTE Middleware im Request-Flow.
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, Response
from starlette.status import HTTP_403_FORBIDDEN, HTTP_302_FOUND

from ..database import SessionLocal
from ..auth_deps import _extract_bearer_token, _validate_token_and_load_user
from ..models.auth import User


# Protected paths
PROTECTED_PATHS = {"/docs", "/redoc", "/openapi.json"}

# Allowed roles for accessing docs
ALLOWED_ROLES = {"admin", "editor"}

# Environment variable to disable docs auth (for development)
DOCS_AUTH_ENABLED = os.getenv("GREAT_DOCS_AUTH", "true").lower() not in ("false", "0", "no")


def _get_user_from_token(token: str, db) -> User | None:
    """Extract user from JWT access token cookie.

    Uses the shared _validate_token_and_load_user from auth_deps.
    Returns the User object if valid, None otherwise.
    Never raises exceptions — all errors result in None.
    """
    user, _ = _validate_token_and_load_user(token, db)
    return user


def _has_valid_api_token(request: Request, db) -> bool:
    """BUG A-08: Gueltiges, aktives API-Token im Authorization-Header?"""
    from ..api_token_service import verify_api_token
    from ..rate_limiter import token_failure_rate_limiter

    raw = _extract_bearer_token(request)
    if not raw:
        return False
    client_ip = request.client.host if request.client else "unknown"
    if token_failure_rate_limiter.peek(client_ip)[0]:
        return False
    result = verify_api_token(db, raw)
    if result is None:
        token_failure_rate_limiter.is_rate_limited(client_ip)  # Fehlversuch zaehlen
        return False
    return result[2] == "ok"


class DocsAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect Swagger-UI and OpenAPI endpoints.

    - Browser requests (Accept: text/html) are redirected to /login
    - API requests receive a 403 JSON response
    - Only users with role 'admin' or 'editor' can access
    - Can be disabled via GREAT_DOCS_AUTH=false environment variable
    """

    async def dispatch(self, request: Request, call_next):
        # Skip if disabled
        if not DOCS_AUTH_ENABLED:
            return await call_next(request)

        path = request.url.path

        # Only intercept protected paths
        if path not in PROTECTED_PATHS:
            return await call_next(request)

        # Extract and validate token
        token = request.cookies.get("access_token")
        db = SessionLocal()
        try:
            user = _get_user_from_token(token, db)
            allowed = bool(user and user.role in ALLOWED_ROLES) or _has_valid_api_token(request, db)
        finally:
            db.close()

        # Not authenticated or wrong role
        if not allowed:
            # Browser request? Redirect to login
            accept = request.headers.get("accept", "")
            if "text/html" in accept:
                return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

            # API request: return 403
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={
                    "detail": "Zugriff auf API-Dokumentation erfordert Authentifizierung mit Rolle admin oder editor"
                },
            )

        # Authenticated with correct role — proceed
        return await call_next(request)