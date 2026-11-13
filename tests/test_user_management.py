"""REQ-4025 / REQ-4026: Benutzerverwaltung + Datenbank-Reset Bugfix Tests.

TDD: Tests zuerst (RED), dann Implementierung (GREEN).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.auth import User, RefreshToken
from app.models.project_membership import ProjectMembership
from app.models import Project
from app.auth_utils import create_access_token
from app.rate_limiter import login_rate_limiter
from app.bootstrap import DEFAULT_ADMIN_PASSWORD  # REQ-4027 AK-1: einzige Definition
from db_cleanup import purge_users


client = TestClient(app)


@pytest.fixture(autouse=True)
def _user_mgmt_db():
    """Create a clean DB state with test users for each test.

    REQ-1300: Verwendet die gemeinsame Test-DB aus conftest.
    Kein drop_all, da die DB geteilt ist. create_all ist idempotent.
    """
    # Ensure tables exist (idempotent)
    Base.metadata.create_all(bind=engine)

    # Run migrations
    from app.main import _migrate_db
    _migrate_db()

    # Seed system dataclasses
    from app.system_dataclasses import seed_system_dataclasses
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)

        # REQ-1300: Reste frueherer Tests entfernen (UNIQUE-Konflikt auf users.username)
        purge_users(db)

        # Create test users
        admin = User(username="admin_user", role="admin", is_active=True)
        admin.set_password("admin123")
        db.add(admin)

        editor = User(username="editor_user", role="editor", is_active=True)
        editor.set_password("editor123")
        db.add(editor)

        viewer = User(username="viewer_user", role="viewer", is_active=True)
        viewer.set_password("viewer123")
        db.add(viewer)

        db.commit()
        db.refresh(admin)
        db.refresh(editor)
        db.refresh(viewer)
        yield db, admin, editor, viewer
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        try:
            purge_users(db)
        finally:
            db.close()


@pytest.fixture
def admin_cookies(_user_mgmt_db):
    """Return admin access_token cookies dict."""
    _, admin, _, _ = _user_mgmt_db
    token = create_access_token(admin.id, admin.username, admin.role)
    return {"access_token": token}


@pytest.fixture
def editor_cookies(_user_mgmt_db):
    """Return editor access_token cookies dict."""
    _, _, editor, _ = _user_mgmt_db
    token = create_access_token(editor.id, editor.username, editor.role)
    return {"access_token": token}


@pytest.fixture
def viewer_cookies(_user_mgmt_db):
    """Return viewer access_token cookies dict."""
    _, _, _, viewer = _user_mgmt_db
    token = create_access_token(viewer.id, viewer.username, viewer.role)
    return {"access_token": token}


# ============================================================================
# REQ-4025: Benutzerverwaltung Tests
# ============================================================================

class TestListUsers:
    """REQ-4025: GET /api/users/ – Admin listet alle Nutzer."""

    def test_admin_can_list_users(self, _user_mgmt_db, admin_cookies):
        """Admin kann alle Nutzer auflisten."""
        response = client.get("/api/users/", cookies=admin_cookies)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least our 3 test users
        assert len(data) >= 3
        # Check structure
        user = data[0]
        assert "id" in user
        assert "username" in user
        assert "role" in user
        assert "is_active" in user

    def test_editor_cannot_list_users(self, _user_mgmt_db, editor_cookies):
        """Editor bekommt 403 bei Benutzerliste."""
        response = client.get("/api/users/", cookies=editor_cookies)
        assert response.status_code == 403

    def test_viewer_cannot_list_users(self, _user_mgmt_db, viewer_cookies):
        """Viewer bekommt 403 bei Benutzerliste."""
        response = client.get("/api/users/", cookies=viewer_cookies)
        assert response.status_code == 403


class TestCreateUser:
    """REQ-4025: POST /api/users/ – Admin erstellt neuen Nutzer."""

    def test_admin_can_create_user(self, _user_mgmt_db, admin_cookies):
        """Admin kann neuen Nutzer anlegen."""
        response = client.post(
            "/api/users/",
            cookies=admin_cookies,
            json={
                "username": "newuser",
                "password": "newpass123",
                "role": "editor",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "editor"
        assert "id" in data

        # Verify in DB
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == "newuser").first()
            assert user is not None
            assert user.role == "editor"
            assert user.is_active is True
            assert user.check_password("newpass123")
        finally:
            db.close()

    def test_admin_cannot_create_duplicate_username(self, _user_mgmt_db, admin_cookies):
        """Admin kann keinen Nutzer mit bestehendem Benutzernamen erstellen."""
        response = client.post(
            "/api/users/",
            cookies=admin_cookies,
            json={
                "username": "admin_user",
                "password": "newpass123",
                "role": "editor",
            },
        )
        assert response.status_code == 409  # Conflict

    def test_editor_cannot_create_user(self, _user_mgmt_db, editor_cookies):
        """Editor bekommt 403 bei Nutzer-Erstellung."""
        response = client.post(
            "/api/users/",
            cookies=editor_cookies,
            json={
                "username": "newuser",
                "password": "newpass123",
                "role": "editor",
            },
        )
        assert response.status_code == 403

    def test_create_user_invalid_role(self, _user_mgmt_db, admin_cookies):
        """Admin kann keinen Nutzer mit ungultiger Rolle erstellen."""
        response = client.post(
            "/api/users/",
            cookies=admin_cookies,
            json={
                "username": "newuser",
                "password": "newpass123",
                "role": "superadmin",
            },
        )
        assert response.status_code == 422  # Validation error


class TestUpdateUser:
    """REQ-4025: PUT /api/users/{user_id} – Admin aendert Rolle/Status."""

    def test_admin_can_change_role(self, _user_mgmt_db, admin_cookies):
        """Admin kann Rolle eines anderen Nutzers aendern."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{editor.id}",
            cookies=admin_cookies,
            json={"role": "viewer"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"

        # Verify in DB
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == editor.id).first()
            assert user.role == "viewer"
        finally:
            db.close()

    def test_admin_can_deactivate_user(self, _user_mgmt_db, admin_cookies):
        """Admin kann einen Nutzer deaktivieren."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{editor.id}",
            cookies=admin_cookies,
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_admin_cannot_deactivate_self(self, _user_mgmt_db, admin_cookies):
        """Admin kann sich selbst nicht deaktivieren."""
        _, admin, _, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{admin.id}",
            cookies=admin_cookies,
            json={"is_active": False},
        )
        assert response.status_code == 403

    def test_admin_cannot_change_self_role(self, _user_mgmt_db, admin_cookies):
        """Admin kann seine eigene Rolle nicht aendern."""
        _, admin, _, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{admin.id}",
            cookies=admin_cookies,
            json={"role": "viewer"},
        )
        assert response.status_code == 403

    def test_editor_cannot_update_user(self, _user_mgmt_db, editor_cookies):
        """Editor bekommt 403 bei Nutzer-Update."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{editor.id}",
            cookies=editor_cookies,
            json={"role": "admin"},
        )
        assert response.status_code == 403

    def test_update_nonexistent_user(self, _user_mgmt_db, admin_cookies):
        """Update eines nicht-existenten Nutzers -> 404."""
        response = client.put(
            "/api/users/99999",
            cookies=admin_cookies,
            json={"role": "viewer"},
        )
        assert response.status_code == 404


class TestDeleteUser:
    """REQ-4025: DELETE /api/users/{user_id} – Admin loescht Nutzer."""

    def test_admin_can_delete_user(self, _user_mgmt_db, admin_cookies):
        """Admin kann einen anderen Nutzer loeschen."""
        _, admin, editor, _ = _user_mgmt_db
        editor_id = editor.id
        response = client.delete(
            f"/api/users/{editor_id}",
            cookies=admin_cookies,
        )
        assert response.status_code == 200

        # Verify deleted
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == editor_id).first()
            assert user is None
        finally:
            db.close()

    def test_admin_cannot_delete_self(self, _user_mgmt_db, admin_cookies):
        """Admin kann sich selbst nicht loeschen."""
        _, admin, _, _ = _user_mgmt_db
        response = client.delete(
            f"/api/users/{admin.id}",
            cookies=admin_cookies,
        )
        assert response.status_code == 403

    def test_delete_user_removes_memberships(self, _user_mgmt_db, admin_cookies):
        """Beim Loeschen eines Nutzers werden dessen Projektmitgliedschaften entfernt."""
        _, admin, editor, _ = _user_mgmt_db

        # Create a project and membership
        project = Project(name="TestProject")
        db = SessionLocal()
        db.add(project)
        db.commit()
        db.refresh(project)

        membership = ProjectMembership(
            project_id=project.id,
            user_id=editor.id,
            role="editor",
        )
        db.add(membership)
        db.commit()
        membership_id = membership.id
        db.close()

        # Delete the editor
        response = client.delete(
            f"/api/users/{editor.id}",
            cookies=admin_cookies,
        )
        assert response.status_code == 200

        # Verify membership is gone
        db = SessionLocal()
        try:
            mem = db.query(ProjectMembership).filter(
                ProjectMembership.id == membership_id
            ).first()
            assert mem is None
        finally:
            db.close()

    def test_editor_cannot_delete_user(self, _user_mgmt_db, editor_cookies):
        """Editor bekommt 403 bei Nutzer-Loeschung."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.delete(
            f"/api/users/{editor.id}",
            cookies=editor_cookies,
        )
        assert response.status_code == 403

    def test_delete_nonexistent_user_returns_404(self, _user_mgmt_db, admin_cookies):
        """Loeschen eines nicht-existenten Nutzers -> 404."""
        response = client.delete(
            "/api/users/99999",
            cookies=admin_cookies,
        )
        assert response.status_code == 404


class TestChangePassword:
    """REQ-4025: PUT /api/users/{user_id}/password – Passwort aendern."""

    def test_admin_can_change_other_password(self, _user_mgmt_db, admin_cookies):
        """Admin kann Passwort eines anderen Nutzers aendern."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{editor.id}/password",
            cookies=admin_cookies,
            json={"new_password": "neweditor123"},
        )
        assert response.status_code == 200

        # Verify new password works
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == editor.id).first()
            assert user.check_password("neweditor123")
            assert not user.check_password("editor123")
        finally:
            db.close()

    def test_admin_can_change_own_password(self, _user_mgmt_db, admin_cookies):
        """Admin kann sein eigenes Passwort aendern."""
        _, admin, _, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{admin.id}/password",
            cookies=admin_cookies,
            json={"new_password": "newadmin12345"},  # REQ-4028 AK-4: Mindestlaenge 12 (vorher 11 Zeichen)
        )
        assert response.status_code == 200

        # Verify new password works
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == admin.id).first()
            assert user.check_password("newadmin12345")
        finally:
            db.close()

    def test_user_can_change_own_password(self, _user_mgmt_db, editor_cookies):
        """Ein Nutzer kann sein eigenes Passwort aendern."""
        _, _, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{editor.id}/password",
            cookies=editor_cookies,
            json={"new_password": "neweditorpass"},
        )
        assert response.status_code == 200

        # Verify new password works
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == editor.id).first()
            assert user.check_password("neweditorpass")
        finally:
            db.close()

    def test_cannot_change_nonexistent_user_password(self, _user_mgmt_db, admin_cookies):
        """Passwort-Aenderung fuer nicht-existenten Nutzer -> 404."""
        response = client.put(
            "/api/users/99999/password",
            cookies=admin_cookies,
            json={"new_password": "newpass"},
        )
        assert response.status_code == 404

    def test_nonadmin_cannot_change_other_user_password(self, _user_mgmt_db, admin_cookies, editor_cookies):
        """Editor kann Passwort eines anderen Nutzers nicht aendern -> 403."""
        _, admin, editor, _ = _user_mgmt_db
        response = client.put(
            f"/api/users/{admin.id}/password",
            cookies=editor_cookies,
            json={"new_password": "hackedpassword"},
        )
        assert response.status_code == 403

        # Verify admin password was NOT changed
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == admin.id).first()
            assert user.check_password("admin123"), "Admin-Passwort sollte unveraendert bleiben"
        finally:
            db.close()


# ============================================================================
# REQ-4026: Datenbank-Reset Bugfix Tests
# ============================================================================

class TestDatabaseReset:
    """REQ-4026: Datenbank-Reset behaelt User-Tabelle."""

    def test_reset_preserves_users(self, _user_mgmt_db):
        """Database-Reset loescht keine User-Tabelle."""
        from app.services import reset_database_state

        db, admin, editor, _ = _user_mgmt_db
        admin_id = admin.id
        admin_username = admin.username

        # Execute reset
        result = reset_database_state(db)
        assert result["status"] == "ok"
        assert result["reset"] is True
        assert result["default_admin_created"] is False  # Admin exists already
        assert result["default_admin_username"] is None

        # Verify admin user still exists
        db2 = SessionLocal()
        try:
            user = db2.query(User).filter(User.id == admin_id).first()
            assert user is not None, "Admin-User sollte nach Reset noch existieren"
            assert user.username == admin_username
            assert user.role == "admin"
        finally:
            db2.close()

    def test_reset_preserves_refresh_tokens(self, _user_mgmt_db):
        """Database-Reset behaelt Refresh-Tokens (aktive Sessions bleiben)."""
        from app.services import reset_database_state

        db, admin, _, _ = _user_mgmt_db

        # Create a refresh token
        from datetime import datetime, timedelta, timezone
        rt = RefreshToken(
            user_id=admin.id,
            token="test-refresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(rt)
        db.commit()
        rt_id = rt.id

        # Execute reset
        result = reset_database_state(db)
        assert result["status"] == "ok"
        assert result["default_admin_created"] is False  # Admin exists

        # Verify refresh token still exists
        db2 = SessionLocal()
        try:
            token = db2.query(RefreshToken).filter(RefreshToken.id == rt_id).first()
            assert token is not None, "Refresh-Token sollte nach Reset noch existieren"
        finally:
            db2.close()

    def test_reset_clears_projects(self, _user_mgmt_db):
        """Database-Reset loescht alle Projekte (außer dem Beispielprojekt aus seed)."""
        from app.services import reset_database_state

        db, admin, _, _ = _user_mgmt_db

        # Create a custom project
        project = Project(name="TestProjectToBeDeleted")
        db.add(project)
        db.commit()
        project_name = project.name

        # Execute reset
        result = reset_database_state(db)
        assert result["status"] == "ok"
        assert result["default_admin_created"] is False  # Admin exists

        # Verify our custom project is gone
        db2 = SessionLocal()
        try:
            p = db2.query(Project).filter(Project.name == project_name).first()
            assert p is None, f"Projekt '{project_name}' sollte nach Reset geloescht sein"
        finally:
            db2.close()

    def test_reset_creates_default_admin_if_none_exists(self):
        """Wenn kein Admin existiert, erstellt Reset einen Standard-Admin."""
        from app.services import reset_database_state

        # REQ-1300: Kein drop_all auf der geteilten Test-DB.
        # Stattdessen: alle Nutzer und zugehoerige Daten loeschen.
        db = SessionLocal()
        try:
            # Delete all data in correct order to avoid FK violations
            db.query(RefreshToken).delete()
            db.query(ProjectMembership).delete()
            db.query(User).delete()
            db.query(Project).delete()
            db.commit()

            # Verify no admin exists
            admin = db.query(User).filter(User.role == "admin").first()
            assert admin is None

            # Execute reset
            result = reset_database_state(db)
            assert result["status"] == "ok"
            assert result["default_admin_created"] is True
            # REQ-4027 AK-12: keine Passwort-Ausgabe; nur Benutzername
            assert result["default_admin_username"] == "admin"

            # Verify default admin was created
            admin = db.query(User).filter(User.username == "admin").first()
            assert admin is not None, "Standard-Admin sollte erstellt worden sein"
            assert admin.role == "admin"
            assert admin.is_active is True
            # REQ-4026 CR-4026-01: Standardpasswort = DEFAULT_ADMIN_PASSWORD (vorher admin123)
            assert admin.check_password(DEFAULT_ADMIN_PASSWORD)
        finally:
            db.close()

    def test_reset_does_not_create_default_admin_if_admin_exists(self, _user_mgmt_db):
        """Wenn ein Admin existiert, erstellt Reset KEINEN weiteren Standard-Admin."""
        from app.services import reset_database_state

        db, admin, _, _ = _user_mgmt_db
        admin_count_before = db.query(User).filter(User.role == "admin").count()

        # Execute reset
        result = reset_database_state(db)
        assert result["status"] == "ok"
        assert result["default_admin_created"] is False  # Admin exists already
        assert result["default_admin_username"] is None

        # Verify admin count is the same
        db2 = SessionLocal()
        try:
            admin_count_after = db2.query(User).filter(User.role == "admin").count()
            assert admin_count_after == admin_count_before, (
                "Admin-Anzahl sollte sich nicht aendern, wenn bereits ein Admin existiert"
            )
        finally:
            db2.close()