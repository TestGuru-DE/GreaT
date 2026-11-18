"""Projekt-Löschen Bugfix-Tests.

- Single-Delete mit Generierungen: 409 ohne force, 200 mit force=true
- Bulk-Delete: keine verwaisten Constraints
- Bulk-Delete mit force: keine verwaisten Reste
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Generation, TestCase, TestCaseValue
from app.models.auth import User
from app.models.decision_table_constraint import DecisionTableConstraint
from app.models.project_membership import ProjectMembership
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


def _create_project_with_generation(client: TestClient, name: str) -> int:
    """Erstellt ein Projekt mit mindestens einer Generierung."""
    r = client.post("/api/projects", json={"name": name})
    assert r.status_code == 200
    pid = r.json()["id"]

    # Kategorie anlegen
    r = client.post(f"/api/projects/{pid}/categories", json={"name": "Cat1", "order_index": 0})
    assert r.status_code == 200
    cid = r.json()["id"]

    # Wert anlegen
    r = client.post(f"/api/categories/{cid}/values", json={"value": "Val1"})
    assert r.status_code == 200

    # Generierung ausfuehren
    r = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 200

    return pid


class TestProjectDelete:
    """Projekt-Löschen mit Generierungs-Prüfung."""

    def test_single_delete_with_generations_requires_force(self, auth_client):
        """Ohne force: 409 bei Generierungen. Mit force=true: 200."""
        pid = _create_project_with_generation(auth_client, "ForceTestProject")

        # Ohne force -> 409
        r = auth_client.delete(f"/api/projects/{pid}")
        assert r.status_code == 409

        # Mit force=true -> 200
        r = auth_client.delete(f"/api/projects/{pid}", params={"force": True})
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_bulk_delete_leaves_no_orphan_constraints(self, auth_client):
        """Bulk-Delete ohne force: Constraints werden mitgeloescht."""
        r = auth_client.post("/api/projects", json={"name": "BulkNoGen"})
        assert r.status_code == 200
        pid = r.json()["id"]

        # Constraint anlegen
        db = SessionLocal()
        try:
            db.add(DecisionTableConstraint(project_id=pid, constraint_type="E", targets=[], description="test"))
            db.commit()
        finally:
            db.close()

        # Bulk-Delete
        r = auth_client.post("/api/projects/bulk-delete", json={"project_ids": [pid]})
        assert r.status_code == 200
        resp = r.json()
        assert resp["deleted"] == 1
        assert resp["blocked"] == []

        # Keine verwaisten Constraints
        db = SessionLocal()
        try:
            assert db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id == pid).count() == 0
        finally:
            db.close()

    def test_bulk_delete_force_leaves_no_orphans(self, auth_client):
        """Bulk-Delete mit force: keine verwaisten Generierungen/Constraints."""
        pid = _create_project_with_generation(auth_client, "BulkForceProject")

        # Constraint anlegen
        db = SessionLocal()
        try:
            db.add(DecisionTableConstraint(project_id=pid, constraint_type="E", targets=[], description="test"))
            db.commit()
        finally:
            db.close()

        # bulk-delete-force
        r = auth_client.post("/api/projects/bulk-delete-force", json={"project_ids": [pid]})
        assert r.status_code == 200
        resp = r.json()
        assert resp["deleted"] == 1

        # Keine verwaisten Reste
        db = SessionLocal()
        try:
            assert db.query(Generation).filter(Generation.project_id == pid).count() == 0
            assert db.query(TestCase).filter(TestCase.generation_id.in_(
                db.query(Generation.id).filter(Generation.project_id == pid)
            )).count() == 0
            assert db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id == pid).count() == 0
            assert db.query(ProjectMembership).filter(ProjectMembership.project_id == pid).count() == 0
        finally:
            db.close()