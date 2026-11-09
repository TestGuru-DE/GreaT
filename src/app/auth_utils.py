"""JWT-Token-Hilfsfunktionen fuer EPIC-18.

REQ-4001: Token-Erzeugung und -Validierung
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import jwt  # PyJWT

from .config import (
    JWT_SECRET_KEY,
    JWT_REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Create JWT access token.

    Args:
        user_id: Database ID of the user
        username: Username for identification
        role: User role (admin, editor, viewer)

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # B2: Eindeutige Token-ID fuer Rotation
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create JWT refresh token.

    Args:
        user_id: Database ID of the user

    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),  # B2: Eindeutige Token-ID fuer Rotation
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token.

    Tries access token secret first, then refresh token secret.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or tampered
    """
    if not token:
        raise jwt.InvalidTokenError("Empty token")

    # Try access token first
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        # Re-raise expired signature so caller can distinguish
        raise
    except jwt.InvalidTokenError:
        pass

    # Then try refresh token
    try:
        return jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        # Re-raise expired signature so caller can distinguish
        raise
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {e}")