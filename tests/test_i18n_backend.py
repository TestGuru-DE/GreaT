"""REQ-6005: Tests fuer Sprachumschaltung Backend.

Slice 1: Migration, PUT /auth/me/preferences, GET /auth/me mit language.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.auth import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def _i18n_db():
    """Create auth tables, clean up after each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create a test user
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(username="testuser", role="editor")
            user.set_password("testpass123")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
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
            # Clean up
            db.query(User).filter(User.username == "testuser").delete()
            db.commit()
        except Exception:
            pass
        finally:
            db.close()


@pytest.fixture
def _auth_cookies(_i18n_db):
    """Login and return cookies for authenticated requests."""
    login_resp = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert login_resp.status_code == 200
    return login_resp.cookies


# ---------------------------------------------------------------------------
# REQ-6005: GET /auth/me liefert language
# ---------------------------------------------------------------------------

class TestGetMeLanguage:
    """REQ-6005: GET /auth/me liefert language-Feld."""

    def test_get_me_has_language_null(self, _i18n_db, _auth_cookies):
        """GET /auth/me liefert language: null bei neuem User."""
        response = client.get("/auth/me", cookies=_auth_cookies)
        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert data["language"] is None

    def test_get_me_has_language_after_set(self, _i18n_db, _auth_cookies):
        """GET /auth/me liefert language nach PUT /auth/me/preferences."""
        # Set language
        put_resp = client.put(
            "/auth/me/preferences",
            json={"language": "en"},
            cookies=_auth_cookies,
        )
        assert put_resp.status_code == 200

        # Verify language in /me
        response = client.get("/auth/me", cookies=_auth_cookies)
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"


# ---------------------------------------------------------------------------
# REQ-6005: PUT /auth/me/preferences
# ---------------------------------------------------------------------------

class TestPutPreferences:
    """REQ-6005: PUT /auth/me/preferences"""

    def test_set_language_de(self, _i18n_db, _auth_cookies):
        """PUT /auth/me/preferences mit language=de -> 200."""
        response = client.put(
            "/auth/me/preferences",
            json={"language": "de"},
            cookies=_auth_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "de"

    def test_set_language_en(self, _i18n_db, _auth_cookies):
        """PUT /auth/me/preferences mit language=en -> 200."""
        response = client.put(
            "/auth/me/preferences",
            json={"language": "en"},
            cookies=_auth_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

    def test_set_language_invalid(self, _i18n_db, _auth_cookies):
        """PUT /auth/me/preferences mit ungueltiger Sprache -> 422."""
        response = client.put(
            "/auth/me/preferences",
            json={"language": "fr"},
            cookies=_auth_cookies,
        )
        assert response.status_code == 422

    def test_set_language_empty(self, _i18n_db, _auth_cookies):
        """PUT /auth/me/preferences mit leerer Sprache -> 422."""
        response = client.put(
            "/auth/me/preferences",
            json={"language": ""},
            cookies=_auth_cookies,
        )
        assert response.status_code == 422

    def test_set_language_persists(self, _i18n_db, _auth_cookies):
        """Sprache bleibt nach PUT erhalten (DB-Persistenz)."""
        # Set language
        client.put(
            "/auth/me/preferences",
            json={"language": "en"},
            cookies=_auth_cookies,
        )

        # Check in DB directly
        db, user = _i18n_db
        db.refresh(user)
        assert user.language == "en"

    def test_set_language_unauthenticated(self, _i18n_db):
        """PUT /auth/me/preferences ohne Auth -> 401."""
        # Use a fresh client without cookies from previous tests
        fresh_client = TestClient(app)
        response = fresh_client.put(
            "/auth/me/preferences",
            json={"language": "en"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# REQ-6005: Login response includes language
# ---------------------------------------------------------------------------

class TestLoginLanguage:
    """REQ-6005: Login-Response enthaelt language-Feld."""

    def test_login_response_has_language(self, _i18n_db):
        """POST /auth/login liefert language im Response."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert data["language"] is None  # Default

    def test_login_response_has_language_after_set(self, _i18n_db, _auth_cookies):
        """Login liefert language nach vorherigem PUT."""
        # Set language first
        client.put(
            "/auth/me/preferences",
            json={"language": "de"},
            cookies=_auth_cookies,
        )

        # Logout
        client.post("/auth/logout", cookies=_auth_cookies)

        # Login again
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "de"


# ---------------------------------------------------------------------------
# REQ-6005: i18n messages module
# ---------------------------------------------------------------------------

class TestI18nMessages:
    """REQ-6005: src/app/i18n/messages.py"""

    def test_get_error_message_de(self):
        """get_error_message liefert deutschen Text."""
        from app.i18n.messages import get_error_message
        msg = get_error_message("invalid_credentials", "de")
        assert msg == "Ungültige Anmeldedaten"

    def test_get_error_message_en(self):
        """get_error_message liefert englischen Text."""
        from app.i18n.messages import get_error_message
        msg = get_error_message("invalid_credentials", "en")
        assert msg == "Invalid credentials"

    def test_get_error_message_unknown_code(self):
        """Unbekannter Code wird als Fallback zurueckgegeben."""
        from app.i18n.messages import get_error_message
        msg = get_error_message("unknown_code_xyz", "de")
        assert msg == "unknown_code_xyz"

    def test_detect_request_language_de(self):
        """detect_request_language erkennt 'de'."""
        from app.i18n.messages import detect_request_language
        lang = detect_request_language({"accept-language": "de-DE,de;q=0.9,en;q=0.8"})
        assert lang == "de"

    def test_detect_request_language_en(self):
        """detect_request_language erkennt 'en'."""
        from app.i18n.messages import detect_request_language
        lang = detect_request_language({"accept-language": "en-US,en;q=0.9"})
        assert lang == "en"

    def test_detect_request_language_default(self):
        """detect_request_language default 'de' bei leerem Header."""
        from app.i18n.messages import detect_request_language
        lang = detect_request_language({})
        assert lang == "de"