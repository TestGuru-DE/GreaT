"""REQ-6012: API-Token Management Endpunkte.

POST /api/v1/api-tokens       - Token anlegen (Klartext nur einmal)
GET  /api/v1/api-tokens       - Eigene Tokens auflisten
DELETE /api/v1/api-tokens/{id} - Token widerrufen
GET  /api/v1/admin/api-tokens - Admin: alle Tokens
DELETE /api/v1/admin/api-tokens/{id} - Admin: beliebigen Token widerrufen
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.auth import User, ApiToken
from ..auth_deps import get_current_user, require_admin
from ..api_token_service import (
    create_api_token,
    revoke_token,
    revoke_token_admin,
    VALID_SCOPES,
)

router = APIRouter(prefix="/api/v1/api-tokens", tags=["api-tokens"])
admin_router = APIRouter(prefix="/api/v1/admin/api-tokens", tags=["api-tokens-admin"])


class ApiTokenCreateRequest(BaseModel):
    """Request-Schema fuer Token-Erzeugung."""
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(min_length=1)
    expires_in_days: int = Field(default=90, ge=1, le=365)

    @staticmethod
    def validate_scopes(scopes: list[str]) -> list[str]:
        for scope in scopes:
            if scope not in VALID_SCOPES:
                raise ValueError(f"Ungueltiger Scope: {scope!r}. Erlaubt: {sorted(VALID_SCOPES)}")
        return scopes


class ApiTokenCreateResponse(BaseModel):
    """Response-Schema: Token wird nur hier im Klartext zurueckgegeben."""
    token: str
    prefix: str
    name: str
    scopes: list[str]
    expires_at: str


class ApiTokenRead(BaseModel):
    """Response-Schema: Token-Info OHNE Klartext."""
    id: int
    name: str
    prefix: str
    scopes: list[str]
    created_at: str
    expires_at: str
    last_used_at: str | None = None
    last_used_ip: str | None = None
    revoked_at: str | None = None


def _token_to_dict(token: ApiToken) -> dict:
    """Convert ApiToken ORM object to response dict."""
    import json
    result = {
        "id": token.id,
        "name": token.name,
        "prefix": token.prefix,
        "scopes": json.loads(token.scopes) if isinstance(token.scopes, str) else token.scopes,
        "created_at": token.created_at.isoformat() if token.created_at else None,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
        "last_used_ip": token.last_used_ip,
        "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
    }
    return result


# ---------------------------------------------------------------------------
# Benutzer-Endpunkte (eigene Tokens)
# ---------------------------------------------------------------------------

@router.post("/", response_model=ApiTokenCreateResponse, status_code=201)
def create_token(
    payload: ApiTokenCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ-6012: API-Token anlegen.

    Das Token wird genau einmal im Klartext angezeigt, mit Kopierknopf und Warnhinweis.
    """
    # Validate scopes
    ApiTokenCreateRequest.validate_scopes(payload.scopes)

    raw_token, token_record = create_api_token(
        db, current_user, payload.name, payload.scopes, payload.expires_in_days
    )

    return ApiTokenCreateResponse(
        token=raw_token,
        prefix=token_record.prefix,
        name=token_record.name,
        scopes=token_record.get_scopes_list(),
        expires_at=token_record.expires_at.isoformat(),
    )


@router.get("/", response_model=list[ApiTokenRead])
def list_own_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ-6012: Liste eigener API-Tokens (ohne Klartext)."""
    tokens = (
        db.query(ApiToken)
        .filter(ApiToken.user_id == current_user.id)
        .order_by(ApiToken.created_at.desc())
        .all()
    )
    return [_token_to_dict(t) for t in tokens]


@router.delete("/{token_id}")
def revoke_own_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """REQ-6012: Eigenes API-Token widerrufen."""
    if not revoke_token(db, token_id, current_user.id):
        raise HTTPException(status_code=404, detail="Token nicht gefunden")
    return {"message": "API-Token widerrufen"}


# ---------------------------------------------------------------------------
# Admin-Endpunkte (alle Tokens)
# ---------------------------------------------------------------------------

@admin_router.get("/", response_model=list[ApiTokenRead], dependencies=[Depends(require_admin)])
def list_all_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: Liste aller API-Tokens aller Nutzer."""
    tokens = (
        db.query(ApiToken)
        .order_by(ApiToken.created_at.desc())
        .all()
    )
    return [_token_to_dict(t) for t in tokens]


@admin_router.delete("/{token_id}", dependencies=[Depends(require_admin)])
def admin_revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: Beliebigen API-Token widerrufen."""
    if not revoke_token_admin(db, token_id):
        raise HTTPException(status_code=404, detail="Token nicht gefunden")
    return {"message": "API-Token widerrufen"}