"""REQ-4025: Tests fuer neue Rollen-Dependencies (api_user-Einfuehrung).

Tests fuer:
- require_writer (admin, editor only)
- require_api_capable (admin, editor, viewer, api_user)
- BLOCKER B2: backup/reset nur fuer admin
- BLOCKER B3: backup/restore nur fuer admin
- api_user kann lesen (require_api_capable), aber nicht schreiben (require_writer)
"""
from datetime import datetime, timedelta, timezone
import pytest
import jwt
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.auth import User, RefreshToken
from app.auth_deps import require_writer, require_api_capable, get_current_user
from app.auth_utils import create_access_token
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM


@pytest.fixture(autouse=True)
def _api_user_db():
    """Create auth tables with api_user, clean up after each test.

    Uses merge to handle existing users from other fixtures (e.g. admin_client).
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create or update test users with different roles (idempotent)
        def get_or_create_user(username: str, role: str, password: str) -> User:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(username=username, role=role)
                user.set_password(password)
                db.add(user)
            else:
                user.role = role
                user.is_active = True
                user.set_password(password)
            db.flush()
            return user

        admin = get_or_create_user("admin_user", "admin", "pass123")
        editor = get_or_create_user("editor_user", "editor", "pass123")
        viewer = get_or_create_user("viewer_user", "viewer", "pass123")
        api_user = get_or_create_user("api_user_user", "api_user", "pass123")

        db.commit()
        db.refresh(admin)
        db.refresh(editor)
        db.refresh(viewer)
        db.refresh(api_user)
        yield db, admin, editor, viewer, api_user
    finally:
        db.close()


class TestRequireWriter:
    """REQ-4025: require_writer – nur admin und editor duerfen schreiben."""

    def test_writer_allows_admin(self, _api_user_db):
        """require_writer mit Admin-User -> OK."""
        db, admin, _, _, _ = _api_user_db
        token = create_access_token(admin.id, admin.username, admin.role)

        client = TestClient(app)
        response = client.get(
            "/auth/writer-only",
            cookies={"access_token": token},
        )
        assert response.status_code == 200

    def test_writer_allows_editor(self, _api_user_db):
        """require_writer mit Editor-User -> OK."""
        db, _, editor, _, _ = _api_user_db
        token = create_access_token(editor.id, editor.username, editor.role)

        client = TestClient(app)
        response = client.get(
            "/auth/writer-only",
            cookies={"access_token": token},
        )
        assert response.status_code == 200

    def test_writer_blocks_viewer(self, _api_user_db):
        """require_writer mit Viewer-User -> 403."""
        db, _, _, viewer, _ = _api_user_db
        token = create_access_token(viewer.id, viewer.username, viewer.role)

        client = TestClient(app)
        response = client.get(
            "/auth/writer-only",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_writer_blocks_api_user(self, _api_user_db):
        """require_writer mit api_user -> 403 (BLOCKER B1 fix)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.get(
            "/auth/writer-only",
            cookies={"access_token": token},
        )
        assert response.status_code == 403


class TestRequireApiCapable:
    """REQ-4025: require_api_capable – admin, editor, viewer, api_user duerfen lesen."""

    def test_api_capable_allows_admin(self, _api_user_db):
        """require_api_capable mit Admin-User -> OK."""
        db, admin, _, _, _ = _api_user_db
        token = create_access_token(admin.id, admin.username, admin.role)

        client = TestClient(app)
        response = client.get(
            "/auth/api-capable",
            cookies={"access_token": token},
        )
        assert response.status_code == 200

    def test_api_capable_allows_editor(self, _api_user_db):
        """require_api_capable mit Editor-User -> OK."""
        db, _, editor, _, _ = _api_user_db
        token = create_access_token(editor.id, editor.username, editor.role)

        client = TestClient(app)
        response = client.get(
            "/auth/api-capable",
            cookies={"access_token": token},
        )
        assert response.status_code == 200

    def test_api_capable_allows_viewer(self, _api_user_db):
        """require_api_capable mit Viewer-User -> OK."""
        db, _, _, viewer, _ = _api_user_db
        token = create_access_token(viewer.id, viewer.username, viewer.role)

        client = TestClient(app)
        response = client.get(
            "/auth/api-capable",
            cookies={"access_token": token},
        )
        assert response.status_code == 200

    def test_api_capable_allows_api_user(self, _api_user_db):
        """require_api_capable mit api_user -> OK (api_user darf lesen)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.get(
            "/auth/api-capable",
            cookies={"access_token": token},
        )
        assert response.status_code == 200


class TestApiUserReadAccess:
    """REQ-4025: api_user kann GET-Endpunkte nutzen."""

    def test_api_user_can_list_projects(self, _api_user_db):
        """api_user kann Projekte auflisten (GET /api/projects)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.get(
            "/api/projects",
            cookies={"access_token": token},
        )
        # api_user hat keine Projektmitgliedschaften, also empty list
        assert response.status_code == 200

    def test_api_user_cannot_create_project(self, _api_user_db):
        """api_user kann keine Projekte erstellen (POST /api/projects -> 403)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.post(
            "/api/projects",
            json={"name": "Testprojekt"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_api_user_cannot_delete_project(self, _api_user_db):
        """api_user kann keine Projekte loeschen (DELETE /api/projects/{pid} -> 403)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.delete(
            "/api/projects/99999",
            cookies={"access_token": token},
        )
        assert response.status_code == 403


class TestBackupBlockers:
    """BLOCKER B2 & B3: Backup-Endpunkte nur fuer Admin."""

    def test_backup_reset_blocks_editor(self, _api_user_db):
        """BLOCKER B2: Editor kann DB nicht zuruecksetzen."""
        db, _, editor, _, _ = _api_user_db
        token = create_access_token(editor.id, editor.username, editor.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/reset",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_backup_reset_blocks_viewer(self, _api_user_db):
        """BLOCKER B2: Viewer kann DB nicht zuruecksetzen."""
        db, _, _, viewer, _ = _api_user_db
        token = create_access_token(viewer.id, viewer.username, viewer.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/reset",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_backup_reset_blocks_api_user(self, _api_user_db):
        """BLOCKER B2: api_user kann DB nicht zuruecksetzen."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/reset",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_backup_reset_allows_admin(self, _api_user_db):
        """BLOCKER B2: Admin kann DB zuruecksetzen."""
        db, admin, _, _, _ = _api_user_db
        token = create_access_token(admin.id, admin.username, admin.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/reset",
            cookies={"access_token": token},
        )
        # Admin darf reset aufrufen (200 OK, da reset_database_state funktioniert)
        assert response.status_code == 200

    def test_backup_restore_blocks_editor(self, _api_user_db):
        """BLOCKER B3: Editor kann kein Backup wiederherstellen."""
        db, _, editor, _, _ = _api_user_db
        token = create_access_token(editor.id, editor.username, editor.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/restore",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_backup_restore_blocks_api_user(self, _api_user_db):
        """BLOCKER B3: api_user kann kein Backup wiederherstellen."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.post(
            "/api/backup/restore",
            cookies={"access_token": token},
        )
        assert response.status_code == 403


class TestPasswordChangeBlocksApiUser:
    """REQ-4025: api_user kann kein Passwort aendern."""

    def test_password_change_blocks_api_user(self, _api_user_db):
        """api_user kann kein Passwort aendern (PUT /api/users/{id}/password -> 403)."""
        db, _, _, _, api_user = _api_user_db
        token = create_access_token(api_user.id, api_user.username, api_user.role)

        client = TestClient(app)
        response = client.put(
            f"/api/users/{api_user.id}/password",
            json={"new_password": "newpass123"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    def test_password_change_allows_editor(self, _api_user_db):
        """Editor kann eigenes Passwort aendern."""
        db, _, editor, _, _ = _api_user_db
        token = create_access_token(editor.id, editor.username, editor.role)

        client = TestClient(app)
        response = client.put(
            f"/api/users/{editor.id}/password",
            json={"new_password": "newpass123456"},  # REQ-4028 AK-4: Mindestlaenge 12 (vorher 10 Zeichen)
            cookies={"access_token": token},
        )
        assert response.status_code == 200