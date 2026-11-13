"""REQ-4001: Auth-Router Tests (Login/Logout/Refresh).

TDD Slice 3: Login, Logout, Refresh-Token Endpoints.
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.auth import User, RefreshToken
from app.rate_limiter import RateLimiter, login_rate_limiter


client = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_router_db():
    """Create auth tables, clean up after each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Capture existing user IDs to preserve session-scoped test user
        existing_user_ids = {u.id for u in db.query(User).all()}
        # Create a test user - reuse existing "testuser" if present
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(username="testuser", role="editor")
            user.set_password("testpass123")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Ensure password is correct even if user already exists
            user.set_password("testpass123")
            user.role = "editor"
            user.is_active = True
            db.commit()
        yield db, user
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        try:
            # Only clean up data created during this test
            current_user_ids = {u.id for u in db.query(User).all()}
            new_user_ids = current_user_ids - existing_user_ids
            # Delete refresh tokens for new users
            for uid in new_user_ids:
                db.query(RefreshToken).filter(RefreshToken.user_id == uid).delete()
            # Delete new users
            for uid in new_user_ids:
                user = db.query(User).filter(User.id == uid).first()
                if user:
                    db.delete(user)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset the global rate limiter before each test."""
    login_rate_limiter._requests.clear()
    yield


class TestLogin:
    """REQ-4001: POST /auth/login"""

    def test_login_success(self, _auth_router_db):
        """Login mit korrekten Daten -> 200 + Cookies."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "editor"
        assert "message" in data

        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, _auth_router_db):
        """Login mit falschem Passwort -> 401."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, _auth_router_db):
        """Login mit nicht-existentem User -> 401."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent", "password": "testpass123"},
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, _auth_router_db):
        """Login mit deaktiviertem User -> 403."""
        db, user = _auth_router_db
        user.is_active = False
        db.commit()

        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 403

    def test_login_sets_httponly_cookies(self, _auth_router_db):
        """Login setzt httpOnly-Cookies."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        # Check that cookies are httponly
        access_cookie = response.cookies.get("access_token")
        refresh_cookie = response.cookies.get("refresh_token")
        assert access_cookie is not None
        assert refresh_cookie is not None


class TestLogout:
    """REQ-4001: POST /auth/logout"""

    def test_logout_success(self, _auth_router_db):
        """Logout loescht Cookies + revokiert Refresh-Token."""
        # First login to get cookies
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200

        # Logout with cookies
        response = client.post(
            "/auth/logout",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logout erfolgreich"

        # Verify refresh token is revoked
        db = SessionLocal()
        try:
            rt = db.query(RefreshToken).filter(
                RefreshToken.token == login_resp.cookies.get("refresh_token", "")
            ).first()
            assert rt is not None
            assert rt.is_revoked is True
        finally:
            db.close()

    def test_logout_without_refresh_token(self, _auth_router_db):
        """Logout ohne Refresh-Token funktioniert trotzdem."""
        response = client.post("/auth/logout")
        assert response.status_code == 200


class TestRefresh:
    """REQ-4001: POST /auth/refresh"""

    def test_refresh_success(self, _auth_router_db):
        """Refresh erstellt neuen Access-Token."""
        # First login
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200

        # Refresh with refresh token cookie
        response = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Token erneuert"
        # New access token should be in cookies
        assert "access_token" in response.cookies

    def test_refresh_no_token(self, _auth_router_db):
        """Refresh ohne Refresh-Token -> 401."""
        # Use a fresh client without cookies from previous tests
        fresh_client = TestClient(app)
        response = fresh_client.post("/auth/refresh")
        assert response.status_code == 401

    def test_refresh_revoked_token(self, _auth_router_db):
        """Refresh mit revokiertem Token -> 401."""
        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200

        # Revoke the refresh token
        db = SessionLocal()
        try:
            rt = db.query(RefreshToken).filter(
                RefreshToken.token == login_resp.cookies.get("refresh_token", "")
            ).first()
            if rt:
                rt.is_revoked = True
                db.commit()
        finally:
            db.close()

        # Try to refresh
        response = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 401

    def test_refresh_with_access_token_instead(self, _auth_router_db):
        """Refresh mit Access-Token statt Refresh-Token -> 401."""
        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200

        # Use a fresh client to avoid cookie persistence from login
        fresh_client = TestClient(app)
        # Try to refresh using only the access token (no refresh_token cookie)
        response = fresh_client.post(
            "/auth/refresh",
            cookies={"access_token": login_resp.cookies.get("access_token", "")},
        )
        assert response.status_code == 401

    def test_refresh_rotates_token(self, _auth_router_db):
        """B2: Refresh erstellt NEUEN Refresh-Token (Token-Rotation)."""
        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200
        old_refresh = login_resp.cookies.get("refresh_token", "")

        # Refresh
        response = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200

        # New refresh token should be in response cookies
        new_refresh = response.cookies.get("refresh_token", "")
        assert new_refresh != "", "Neuer Refresh-Token sollte im Response sein"
        assert new_refresh != old_refresh, "Refresh-Token muss sich aendern (Rotation)"

    def test_old_refresh_token_revoked_after_rotation(self, _auth_router_db):
        """B2: Alter Refresh-Token ist nach Rotation revokiert."""
        db, user = _auth_router_db

        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200
        old_refresh = login_resp.cookies.get("refresh_token", "")

        # Refresh (triggers rotation)
        response = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200

        # Old refresh token should be revoked in DB
        rt = db.query(RefreshToken).filter(
            RefreshToken.token == old_refresh
        ).first()
        assert rt is not None
        assert rt.is_revoked is True, "Alter Refresh-Token muss revokiert sein"

    def test_old_refresh_token_cannot_be_reused(self, _auth_router_db):
        """B2: Alter Refresh-Token kann nach Rotation NICHT erneut verwendet werden."""
        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200
        old_cookies = dict(login_resp.cookies)

        # First refresh (triggers rotation)
        response1 = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response1.status_code == 200

        # Try to use the OLD refresh token again
        fresh_client = TestClient(app)
        response2 = fresh_client.post(
            "/auth/refresh",
            cookies=old_cookies,
        )
        assert response2.status_code == 401, "Alter Refresh-Token darf nicht mehr funktionieren"

    def test_new_refresh_token_can_be_used(self, _auth_router_db):
        """B2: Neuer Refresh-Token nach Rotation kann verwendet werden."""
        # Login first
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200

        # First refresh (triggers rotation)
        response1 = client.post(
            "/auth/refresh",
            cookies=login_resp.cookies,
        )
        assert response1.status_code == 200

        # Use the NEW refresh token for another refresh
        fresh_client = TestClient(app)
        new_cookies = dict(response1.cookies)
        response2 = fresh_client.post(
            "/auth/refresh",
            cookies=new_cookies,
        )
        assert response2.status_code == 200, "Neuer Refresh-Token muss funktionieren"


class TestLoginRateLimiting:
    """REQ-4001: Rate-Limiting beim Login."""

    def test_login_rate_limiting(self, _auth_router_db):
        """Login Rate-Limiting -> 429 nach 5 Versuchen."""
        # Use a fresh rate limiter for this test
        login_rate_limiter._requests.clear()

        # 5 failed attempts (should be allowed)
        for i in range(5):
            response = client.post(
                "/auth/login",
                data={"username": "testuser", "password": "wrong"},
            )
            assert response.status_code == 401, f"Attempt {i+1} should return 401"

        # 6th attempt should be rate limited
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrong"},
        )
        assert response.status_code == 429