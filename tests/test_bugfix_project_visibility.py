"""Projekt-Sichtbarkeit Bugfix-Tests.

Alle Rollen (editor, viewer, api_user) sehen alle Projekte.
Nur Admin/Editor duerfen Projekte erstellen (require_writer).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.auth import User
from app.auth_utils import create_access_token


def _add_user(username: str, role: str) -> int:
    db = SessionLocal()
    try:
        user = User(
            username=username,
            role=role,
            is_active=True,
            default_password_active=False,
        )
        user.set_password("testpass123")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _client_for(user_id: int) -> TestClient:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        token = create_access_token(user.id, user.username, user.role)
    finally:
        db.close()
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("access_token", token)
    return client


class TestProjectVisibility:
    """Alle api_capable-Rollen sehen alle Projekte."""

    def test_editor_sees_own_created_project(self):
        editor_id = _add_user("vis_editor", "editor")
        client = _client_for(editor_id)

        # Editor erstellt ein Projekt
        r = client.post("/api/projects", json={"name": "EditorProject"})
        assert r.status_code == 200
        pid = r.json()["id"]

        # Editor sieht es in der Liste
        r = client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()
        assert any(p["id"] == pid for p in projects)

    def test_viewer_sees_all_projects(self, admin_client):
        # Admin erstellt ein Projekt
        r = admin_client.post("/api/projects", json={"name": "ViewerTestProject"})
        assert r.status_code == 200
        pid = r.json()["id"]

        # Viewer sieht das Projekt
        viewer_id = _add_user("vis_viewer", "viewer")
        client = _client_for(viewer_id)
        r = client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()
        assert any(p["id"] == pid for p in projects)

    def test_api_user_sees_all_projects(self, admin_client):
        # Admin erstellt ein Projekt
        r = admin_client.post("/api/projects", json={"name": "ApiUserProject"})
        assert r.status_code == 200
        pid = r.json()["id"]

        # api_user sieht das Projekt
        api_id = _add_user("vis_apiuser", "api_user")
        client = _client_for(api_id)
        r = client.get("/api/projects")
        assert r.status_code == 200
        projects = r.json()
        assert any(p["id"] == pid for p in projects)

    def test_viewer_still_cannot_create_project(self):
        viewer_id = _add_user("vis_viewer2", "viewer")
        client = _client_for(viewer_id)
        r = client.post("/api/projects", json={"name": "ViewerShouldNotCreate"})
        assert r.status_code == 403