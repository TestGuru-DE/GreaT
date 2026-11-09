"""Docs-Auth-Middleware fuer Swagger-UI und OpenAPI-Schema.

RISK-S-006: Swagger-UI ohne Authentifizierung erreichbar (Score 16, HIGH)
RISK-S-007: OpenAPI-Schema offenlegt interne API-Strukturen (Score 12, HIGH)

Diese Middleware schuetzt /docs, /redoc und /openapi.json durch
Authentifizierung und Rollenpruefung (admin/editor).

WICHTIG: In main.py muss diese Middleware ZULETZT hinzugefuegt werden,
weil Starlette-Middleware LIFO (Last-In-First-Out) ausgefuehrt wird.
So laeuft sie als ERSTE Middleware im Request-Flow.
"""
import os
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, Response
from starlette.status import HTTP_403_FORBIDDEN, HTTP_302_FOUND

from ..config import JWT_SECRET_KEY, JWT_ALGORITHM
from ..database import SessionLocal
from ..models.auth import User


# Protected paths
PROTECTED_PATHS = {"/docs", "/redoc", "/openapi.json"}

# Allowed roles for accessing docs
ALLOWED_ROLES = {"admin", "editor"}

# Environment variable to disable docs auth (for development)
DOCS_AUTH_ENABLED = os.getenv("GREAT_DOCS_AUTH", "true").lower() not in ("false", "0", "no")


def _get_user_from_token(token: str, db) -> User | None:
    """Extract user from JWT access token cookie.

    Returns the User object if valid, None otherwise.
    Never raises exceptions — all errors result in None.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, TypeError):
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (ValueError, TypeError):
        return None

    if not user or not user.is_active:
        return None

    return user


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
        finally:
            db.close()

        # Not authenticated or wrong role
        if not user or user.role not in ALLOWED_ROLES:
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