"""REQ-4023: Projekt-Sharing / Mitgliederverwaltung Tests"""
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.auth import User
from app.models import Project
from app.models.project_membership import ProjectMembership


def _unique_suffix():
    """Erzeugt einen eindeutigen Suffix fuer Test-Namen."""
    return f"{int(time.time() * 1000)}"


@pytest.fixture(scope="function")
def admin_user():
    """Erstellt einen Admin-User fuer Tests."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin_test").first()
        if not user:
            user = User(username="admin_test", role="admin")
            user.set_password("adminpass")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.role = "admin"
            user.is_active = True
            user.set_password("adminpass")
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="function")
def viewer_user():
    """Erstellt einen Viewer-User fuer Tests."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "viewer_test").first()
        if not user:
            user = User(username="viewer_test", role="viewer")
            user.set_password("viewerpass")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.role = "viewer"
            user.is_active = True
            user.set_password("viewerpass")
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="function")
def admin_cookies(admin_user):
    """Login-Cookies fuer Admin-User."""
    from app.rate_limiter import login_rate_limiter
    login_rate_limiter._requests.clear()
    with TestClient(app) as tc:
        resp = tc.post(
            "/auth/login",
            data={"username": "admin_test", "password": "adminpass"},
        )
        assert resp.status_code == 200
        return dict(tc.cookies)


@pytest.fixture(scope="function")
def viewer_cookies(viewer_user):
    """Login-Cookies fuer Viewer-User."""
    from app.rate_limiter import login_rate_limiter
    login_rate_limiter._requests.clear()
    with TestClient(app) as tc:
        resp = tc.post(
            "/auth/login",
            data={"username": "viewer_test", "password": "viewerpass"},
        )
        assert resp.status_code == 200
        return dict(tc.cookies)


@pytest.fixture(scope="function")
def admin_client(admin_cookies):
    tc = TestClient(app)
    for name, value in admin_cookies.items():
        tc.cookies.set(name, value)
    return tc


@pytest.fixture(scope="function")
def viewer_client(viewer_cookies):
    tc = TestClient(app)
    for name, value in viewer_cookies.items():
        tc.cookies.set(name, value)
    return tc


@pytest.fixture(scope="function")
def test_project(admin_client, admin_user):
    """Erstellt ein Test-Projekt und gibt es zurueck."""
    suffix = _unique_suffix()
    r = admin_client.post("/api/projects", json={"name": f"Sharing-Test-{suffix}"})
    assert r.status_code == 200
    project = r.json()

    # Admin automatisch als Mitglied hinzufuegen
    db = SessionLocal()
    try:
        existing = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project["id"],
            ProjectMembership.user_id == admin_user.id,
        ).first()
        if not existing:
            membership = ProjectMembership(
                project_id=project["id"],
                user_id=admin_user.id,
                role="editor",
            )
            db.add(membership)
            db.commit()
    finally:
        db.close()

    return project


class TestProjectVisibility:
    """Tests fuer projektbasierte Sichtbarkeit."""

    def test_admin_sees_all_projects(self, admin_client, test_project):
        """Admin sieht alle Projekte."""
        r = admin_client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()
        project_ids = [p["id"] for p in projects]
        assert test_project["id"] in project_ids

    def test_viewer_without_membership_sees_no_projects(self, viewer_client, viewer_user):
        """Viewer ohne Mitgliedschaft sieht keine Projekte."""
        # Stelle sicher, dass keine Mitgliedschaft existiert
        db = SessionLocal()
        try:
            db.query(ProjectMembership).filter(
                ProjectMembership.user_id == viewer_user.id
            ).delete()
            db.commit()
        finally:
            db.close()

        r = viewer_client.get("/api/projects")
        assert r.status_code == 200
        assert r.json() == []

    def test_viewer_with_membership_sees_project(self, viewer_client, viewer_user, test_project):
        """Viewer mit Mitgliedschaft sieht das Projekt."""
        # Mitgliedschaft hinzufuegen
        db = SessionLocal()
        try:
            existing = db.query(ProjectMembership).filter(
                ProjectMembership.project_id == test_project["id"],
                ProjectMembership.user_id == viewer_user.id,
            ).first()
            if not existing:
                membership = ProjectMembership(
                    project_id=test_project["id"],
                    user_id=viewer_user.id,
                    role="viewer",
                )
                db.add(membership)
                db.commit()
        finally:
            db.close()

        r = viewer_client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()
        project_ids = [p["id"] for p in projects]
        assert test_project["id"] in project_ids


class TestSharingEndpoints:
    """Tests fuer die Sharing-Endpunkte."""

    def test_get_members_no_access(self, viewer_client, viewer_user, test_project):
        """GET /api/sharing/project/{id}/members ohne Zugriff -> 403."""
        # Stelle sicher, dass keine Mitgliedschaft existiert
        db = SessionLocal()
        try:
            db.query(ProjectMembership).filter(
                ProjectMembership.user_id == viewer_user.id,
                ProjectMembership.project_id == test_project["id"],
            ).delete()
            db.commit()
        finally:
            db.close()

        r = viewer_client.get(f"/api/sharing/project/{test_project['id']}/members")
        assert r.status_code == 403

    def test_add_member_success(self, admin_client, admin_user, viewer_user, test_project):
        """POST /api/sharing/project/{id}/members -> 201."""
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": viewer_user.id, "role": "viewer"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["user_id"] == viewer_user.id
        assert data["role"] == "viewer"

    def test_add_member_duplicate(self, admin_client, admin_user, viewer_user, test_project):
        """POST /api/sharing/project/{id}/members mit bestehendem Mitglied -> 409."""
        # Erstes Mal hinzufuegen
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": viewer_user.id, "role": "viewer"},
        )
        assert r.status_code == 201

        # Zweites Mal -> 409
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": viewer_user.id, "role": "editor"},
        )
        assert r.status_code == 409

    def test_add_member_invalid_role(self, admin_client, viewer_user, test_project):
        """POST /api/sharing/project/{id}/members mit ungueltiger Rolle -> 422."""
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": viewer_user.id, "role": "superadmin"},
        )
        assert r.status_code == 422

    def test_add_member_nonexistent_user(self, admin_client, test_project):
        """POST /api/sharing/project/{id}/members mit nicht-existentem User -> 404."""
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": 99999, "role": "viewer"},
        )
        assert r.status_code == 404

    def test_remove_member_success(self, admin_client, admin_user, viewer_user, test_project):
        """DELETE /api/sharing/project/{id}/members/{user_id} -> 200."""
        # Erst hinzufuegen
        r = admin_client.post(
            f"/api/sharing/project/{test_project['id']}/members",
            json={"user_id": viewer_user.id, "role": "viewer"},
        )
        assert r.status_code == 201

        # Dann entfernen
        r = admin_client.delete(
            f"/api/sharing/project/{test_project['id']}/members/{viewer_user.id}"
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_remove_nonexistent_member(self, admin_client, viewer_user, test_project):
        """DELETE /api/sharing/project/{id}/members/{user_id} ohne Mitgliedschaft -> 404."""
        r = admin_client.delete(
            f"/api/sharing/project/{test_project['id']}/members/{viewer_user.id}"
        )
        assert r.status_code == 404