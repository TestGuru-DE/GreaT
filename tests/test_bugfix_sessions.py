"""B-06/B-07: Sitzungs-Invalidierung & Admin-only Passwort-Reset.

B-06: Token Versioning – Passwortwechsel, Rollenaeanderung, Deaktivierung
      invalidieren alle anderen Sitzungen.
B-07: PUT /api/users/{id}/password nur fuer Admins.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.auth import User, RefreshToken
from app.auth_utils import create_access_token, create_refresh_token
from app.rate_limiter import login_rate_limiter

# Mindestens 12 Zeichen (password_policy.MIN_PASSWORD_LENGTH)
STRONG_NEW_PASSWORD = "NewPass456!XYZ"


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    login_rate_limiter._requests.clear()
    yield


# ---------------------------------------------------------------------------
# B-06: Token Versioning – Sitzungs-Invalidierung
# ---------------------------------------------------------------------------

class TestPasswordChangeInvalidatesSessions:
    """B-06: Passwortwechsel invalidiert alle anderen Sitzungen."""

    def test_password_change_invalidates_other_sessions(self):
        """Selbst-Passwortwechsel invalidiert andere Sitzungen."""
        db = SessionLocal()
        try:
            user = User(username="sessuser", role="editor")
            user.set_password("oldpass123456")
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            # Zwei Tokens mit token_version=0
            token_v0_a = create_access_token(user.id, user.username, user.role, 0)
            token_v0_b = create_access_token(user.id, user.username, user.role, 0)

            # Session A aendert Passwort via /auth/change-password
            client_a = TestClient(app)
            client_a.cookies.set("access_token", token_v0_a)
            resp = client_a.post(
                "/auth/change-password",
                json={"current_password": "oldpass123456", "new_password": STRONG_NEW_PASSWORD},
            )
            assert resp.status_code == 200, f"Passwortwechsel fehlgeschlagen: {resp.json()}"

            # token_version sollte jetzt 1 sein
            db.refresh(user)
            assert user.token_version == 1

            # Session B (alter Token mit tv=0) sollte abgewiesen werden
            client_b = TestClient(app)
            client_b.cookies.set("access_token", token_v0_b)
            resp = client_b.get("/auth/me")
            assert resp.status_code == 401, "Alte Session sollte nach Passwortwechsel abgewiesen werden"
        finally:
            db.close()

    def test_password_change_keeps_current_session(self):
        """Die Session, die das Passwort aendert, bleibt gueltig bis zum naechsten Request."""
        db = SessionLocal()
        try:
            user = User(username="sessuser2", role="editor")
            user.set_password("oldpass123456")
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            token_v0 = create_access_token(user.id, user.username, user.role, 0)

            client = TestClient(app)
            client.cookies.set("access_token", token_v0)
            resp = client.post(
                "/auth/change-password",
                json={"current_password": "oldpass123456", "new_password": STRONG_NEW_PASSWORD},
            )
            assert resp.status_code == 200

            # B-06: Die aendernde Sitzung erhaelt neue Cookies und bleibt angemeldet.
            assert client.get("/auth/me").status_code == 200

            # Das alte Token (token_version=0) ist dagegen ungueltig.
            stale = TestClient(app)
            stale.cookies.set("access_token", token_v0)
            assert stale.get("/auth/me").status_code == 401, "Alter Token sollte nach Passwortwechsel ungültig sein"
        finally:
            db.close()

    def test_deactivated_user_cannot_refresh(self):
        """Deaktivierter Nutzer kann Refresh-Token nicht verwenden."""
        db = SessionLocal()
        try:
            user = User(username="deactuser", role="editor")
            user.set_password("pass1234567890")
            user.token_version = 0
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)

            refresh_tok = create_refresh_token(user.id)
            rt = RefreshToken(
                user_id=user.id,
                token=refresh_tok,
                expires_at=user.created_at.replace(year=user.created_at.year + 1),
            )
            db.add(rt)
            db.commit()

            client = TestClient(app)
            resp = client.post(
                "/auth/refresh",
                cookies={"refresh_token": refresh_tok},
            )
            assert resp.status_code == 403, "Deaktivierter Nutzer darf nicht refreshen"
        finally:
            db.close()

    def test_role_change_invalidates_sessions(self):
        """Rollenaeanderung via Admin invalidiert Sitzungen des betroffenen Nutzers."""
        db = SessionLocal()
        try:
            admin = User(username="adminrole", role="admin")
            admin.set_password("adminpass123456")
            admin.token_version = 0
            db.add(admin)

            target = User(username="targetrole", role="editor")
            target.set_password("targetpass123456")
            target.token_version = 0
            db.add(target)
            db.commit()
            db.refresh(admin)
            db.refresh(target)

            # Target-Session mit tv=0
            token_v0 = create_access_token(target.id, target.username, target.role, 0)

            # Admin aendert Rolle
            admin_token = create_access_token(admin.id, admin.username, admin.role, 0)
            admin_client = TestClient(app)
            admin_client.cookies.set("access_token", admin_token)

            resp = admin_client.put(
                f"/api/users/{target.id}",
                json={"role": "viewer"},
            )
            assert resp.status_code == 200, f"Rollenaeanderung fehlgeschlagen: {resp.json()}"

            # target.token_version sollte jetzt erhoeht sein
            db.refresh(target)
            assert target.token_version >= 1

            # Alte Session des Targets sollte abgewiesen werden
            target_client = TestClient(app)
            target_client.cookies.set("access_token", token_v0)
            resp = target_client.get("/auth/me")
            assert resp.status_code == 401, "Alte Session sollte nach Rollenaeanderung abgewiesen werden"
        finally:
            db.close()


# ---------------------------------------------------------------------------
# B-07: Passwort-Reset nur fuer Admins
# ---------------------------------------------------------------------------

class TestPasswordResetAdminOnly:
    """B-07: PUT /api/users/{id}/password nur fuer Admins."""

    def test_editor_cannot_set_own_password_via_users_endpoint(self):
        """Editor kann PUT /api/users/{id}/password nicht nutzen (403)."""
        db = SessionLocal()
        try:
            editor = User(username="edpw", role="editor")
            editor.set_password("edpass1234567890")
            editor.token_version = 0
            db.add(editor)
            db.commit()
            db.refresh(editor)

            editor_token = create_access_token(editor.id, editor.username, editor.role, 0)
            client = TestClient(app)
            client.cookies.set("access_token", editor_token)

            resp = client.put(
                f"/api/users/{editor.id}/password",
                json={"new_password": STRONG_NEW_PASSWORD},
            )
            assert resp.status_code == 403, "Editor darf nicht via /api/users Passwort aendern"
        finally:
            db.close()

    def test_admin_can_still_reset_password_via_users_endpoint(self):
        """Admin kann PUT /api/users/{id}/password nutzen."""
        db = SessionLocal()
        try:
            admin = User(username="adminpw", role="admin")
            admin.set_password("adminpass123456")
            admin.token_version = 0
            db.add(admin)

            target = User(username="targetpw", role="editor")
            target.set_password("oldpass123456")
            target.token_version = 0
            db.add(target)
            db.commit()
            db.refresh(admin)
            db.refresh(target)

            admin_token = create_access_token(admin.id, admin.username, admin.role, 0)
            client = TestClient(app)
            client.cookies.set("access_token", admin_token)

            resp = client.put(
                f"/api/users/{target.id}/password",
                json={"new_password": STRONG_NEW_PASSWORD},
            )
            assert resp.status_code == 200, f"Admin sollte Passwort aendern koennen: {resp.json()}"
        finally:
            db.close()