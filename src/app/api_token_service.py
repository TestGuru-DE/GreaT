"""REQ-6012: API-Token Service.

Token-Erzeugung mit argon2id + Salt, Verifikation, Scopes.
Keine HTTP-Konzepte in dieser Schicht.
"""
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import argon2
from sqlalchemy.orm import Session

from .models.auth import User, ApiToken


# Valid scopes as defined in REQ-6012
VALID_SCOPES = {
    "projects:read",
    "projects:write",
    "generate",
    "export",
    "models:read",
    "models:write",
}

TOKEN_PREFIX = "great_pat_"
TOKEN_RANDOM_BYTES = 32  # 256 bits
TOKEN_PREFIX_LENGTH = 16  # First 16 chars for DB lookup (10 prefix + 6 random)


def create_api_token(
    db: Session,
    user: User,
    name: str,
    scopes: list[str],
    days: int = 90,
) -> Tuple[str, ApiToken]:
    """Erzeugt ein neues API-Token.

    Args:
        db: Datenbank-Session
        user: User, dem das Token gehoert
        name: Menschlesbarer Name (z. B. "Jenkins Nightly")
        scopes: Liste von Scopes (z. B. ["projects:read", "generate"])
        days: Gueltigkeit in Tagen (1-365)

    Returns:
        (raw_token, token_record) - raw_token ist der Klartext-Token (einmalig!)

    Raises:
        ValueError: Bei ungueltigen Scopes oder Tagen
    """
    # Validate scopes
    for scope in scopes:
        if scope not in VALID_SCOPES:
            raise ValueError(f"Ungueltiger Scope: {scope!r}. Erlaubt: {sorted(VALID_SCOPES)}")

    # Validate days
    if not (1 <= days <= 365):
        raise ValueError("expires_in_days muss zwischen 1 und 365 liegen")

    # Generate random token
    random_bytes = secrets.token_urlsafe(TOKEN_RANDOM_BYTES)
    raw_token = f"{TOKEN_PREFIX}{random_bytes}"

    # Generate salt (32 bytes, stored as hex)
    salt_bytes = secrets.token_bytes(32)
    salt_hex = salt_bytes.hex()

    # Hash: argon2id(salt + token)
    ph = argon2.PasswordHasher()
    token_hash = ph.hash(salt_hex + raw_token)

    # Create record
    token_record = ApiToken(
        user_id=user.id,
        name=name,
        prefix=raw_token[:TOKEN_PREFIX_LENGTH],
        salt=salt_hex,
        token_hash=token_hash,
        scopes=json.dumps(scopes),
        expires_at=datetime.now(timezone.utc) + timedelta(days=days),
        token_version_at_creation=user.token_version,
    )

    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return raw_token, token_record


def verify_api_token(
    db: Session,
    raw_token: str,
) -> Optional[Tuple[User, ApiToken, str]]:
    """Verifiziert ein API-Token.

    Args:
        db: Datenbank-Session
        raw_token: Der komplette Token aus dem Authorization-Header

    Returns:
        (user, token_record, status) wenn gueltig: status="ok"
        (user, token_record, status) bei deaktiviertem User: status="deactivated"
        None bei sonstigem Fehler (falscher Hash, abgelaufen, widerrufen)
    """
    if not raw_token.startswith(TOKEN_PREFIX):
        return None

    # Extract prefix to find the token record
    prefix = raw_token[:TOKEN_PREFIX_LENGTH]

    token_record = db.query(ApiToken).filter(ApiToken.prefix == prefix).first()
    if not token_record:
        return None

    # Check if revoked
    if token_record.revoked_at is not None:
        return None

    # Check if expired
    now = datetime.now(timezone.utc)
    expires = token_record.expires_at
    # Handle naive datetime from SQLite
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        return None

    # Verify hash: argon2id(salt + token)
    try:
        ph = argon2.PasswordHasher()
        ph.verify(token_record.token_hash, token_record.salt + raw_token)
    except argon2.exceptions.VerifyMismatchError:
        return None
    except Exception:
        return None

    # Load user
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        return None

    # Check if user is active – return special status for deactivated
    if not user.is_active:
        return user, token_record, "deactivated"

    # Check token version (role change invalidation)
    if user.token_version != token_record.token_version_at_creation:
        return None

    return user, token_record, "ok"


def revoke_token(db: Session, token_id: int, user_id: int) -> bool:
    """Widerruft ein API-Token.

    Args:
        db: Datenbank-Session
        token_id: ID des Tokens
        user_id: ID des Users (zum Besitz-Nachweis)

    Returns:
        True wenn Token gefunden und widerrufen, False sonst
    """
    token = db.query(ApiToken).filter(
        ApiToken.id == token_id,
        ApiToken.user_id == user_id,
    ).first()

    if not token:
        return False

    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_token_admin(db: Session, token_id: int) -> bool:
    """Admin widerruft ein beliebiges API-Token.

    Args:
        db: Datenbank-Session
        token_id: ID des Tokens

    Returns:
        True wenn Token gefunden und widerrufen, False sonst
    """
    token = db.query(ApiToken).filter(ApiToken.id == token_id).first()

    if not token:
        return False

    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def update_last_used(db: Session, token_record: ApiToken, ip: Optional[str] = None) -> None:
    """Aktualisiert last_used_at und last_used_ip nach erfolgreicher Auth.

    REQ-6012 AK: Audit-Log (Zeit + Endpunkt, kein Inhalt).
    """
    token_record.last_used_at = datetime.now(timezone.utc)
    if ip:
        token_record.last_used_ip = ip
    db.commit()