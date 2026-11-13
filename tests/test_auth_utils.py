"""REQ-4001: JWT-Token-Hilfsfunktionen Tests.

TDD Slice 2: Token-Erzeugung und -Validierung.
"""
from datetime import datetime, timedelta, timezone
import pytest
import jwt
from app.auth_utils import create_access_token, create_refresh_token, decode_token
from app.config import JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY, JWT_ALGORITHM


class TestCreateAccessToken:
    """REQ-4001: Access-Token-Erzeugung."""

    def test_create_access_token_returns_string(self):
        """create_access_token liefert ein nicht-leeres String-Token."""
        token = create_access_token(user_id=1, username="testuser", role="viewer")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_payload(self):
        """Access-Token enthaelt korrekte Payload (sub, username, role, type)."""
        token = create_access_token(user_id=42, username="admin_user", role="admin")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        assert payload["sub"] == "42"  # PyJWT requires sub as string
        assert payload["username"] == "admin_user"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_access_token_has_expiry(self):
        """Access-Token hat ein Gueltigkeitsdatum in der Zukunft."""
        token = create_access_token(user_id=1, username="testuser", role="viewer")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        assert "exp" in payload
        # Token should expire in the future (within expected window)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp_time > datetime.now(timezone.utc)


class TestCreateRefreshToken:
    """REQ-4001: Refresh-Token-Erzeugung."""

    def test_create_refresh_token_returns_string(self):
        """create_refresh_token liefert ein nicht-leeres String-Token."""
        token = create_refresh_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_payload(self):
        """Refresh-Token enthaelt korrekte Payload (sub, type)."""
        token = create_refresh_token(user_id=99)
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        assert payload["sub"] == "99"  # PyJWT requires sub as string
        assert payload["type"] == "refresh"

    def test_create_refresh_token_has_expiry(self):
        """Refresh-Token hat ein Gueltigkeitsdatum in der Zukunft."""
        token = create_refresh_token(user_id=1)
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp_time > datetime.now(timezone.utc)

    def test_access_and_refresh_tokens_differ(self):
        """Access- und Refresh-Tokens sind unterschiedlich (verschiedene Secrets)."""
        access = create_access_token(user_id=1, username="testuser", role="viewer")
        refresh = create_refresh_token(user_id=1)
        assert access != refresh


class TestDecodeToken:
    """REQ-4001: Token-Validierung."""

    def test_decode_valid_access_token(self):
        """decode_token decodiert gueltigen Access-Token."""
        token = create_access_token(user_id=5, username="testuser", role="editor")
        payload = decode_token(token)
        assert payload["sub"] == "5"
        assert payload["username"] == "testuser"
        assert payload["role"] == "editor"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self):
        """decode_token decodiert gueltigen Refresh-Token."""
        token = create_refresh_token(user_id=5)
        payload = decode_token(token)
        assert payload["sub"] == "5"
        assert payload["type"] == "refresh"

    def test_decode_expired_token_raises(self):
        """decode_token wirft Fehler bei abgelaufenem Token."""
        # Create a token that's already expired
        payload = {
            "sub": "1",  # string sub for PyJWT compatibility
            "username": "testuser",
            "role": "viewer",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # 1 hour ago
            "type": "access",
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        with pytest.raises((jwt.ExpiredSignatureError, jwt.InvalidTokenError)):
            decode_token(token)

    def test_decode_tampered_token_raises(self):
        """decode_token wirft Fehler bei manipuliertem Token."""
        token = create_access_token(user_id=1, username="testuser", role="viewer")
        # Tamper with the token by changing a character
        tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)

    def test_decode_random_string_raises(self):
        """decode_token wirft Fehler bei zufaelligem String."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("not-a-valid-jwt-token")

    def test_decode_empty_string_raises(self):
        """decode_token wirft Fehler bei leerem String."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("")