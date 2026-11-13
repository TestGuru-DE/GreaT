"""REQ-1206 / Sprint-Fix: Projekt loeschen entfernt projektbezogene Artefakte vollstaendig.

Entscheidungstabellen-Constraints und Projekt-Mitgliedschaften haben keinen
ON DELETE CASCADE. Ohne Aufraeumen scheitert das Loeschen (FK-Fehler) bzw.
verbleiben verwaiste Eintraege. Dieser Test prueft: Loeschen klappt, und es
bleiben keine Reste zurueck.
"""
from app.database import SessionLocal
from app.models import Project
from app.models.auth import User
from app.models.decision_table_constraint import DecisionTableConstraint
from app.models.project_membership import ProjectMembership


def test_delete_project_removes_constraints_and_memberships(auth_client):
    r = auth_client.post("/api/projects", json={"name": "DeleteCleanup_Project"})
    assert r.status_code == 200
    pid = r.json()["id"]

    db = SessionLocal()
    try:
        user = User(username="cleanup_member", role="viewer")
        user.set_password("pass123")
        db.add(user)
        db.flush()
        db.add(ProjectMembership(project_id=pid, user_id=user.id, role="viewer"))
        db.add(DecisionTableConstraint(project_id=pid, constraint_type="E", targets=[], description="x"))
        db.commit()
    finally:
        db.close()

    resp = auth_client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 200, resp.text

    db = SessionLocal()
    try:
        assert db.query(Project).filter(Project.id == pid).first() is None
        assert db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id == pid).count() == 0
        assert db.query(ProjectMembership).filter(ProjectMembership.project_id == pid).count() == 0
    finally:
        db.close()

def test_bulk_force_delete_removes_constraints_and_memberships(auth_client):
    r = auth_client.post("/api/projects", json={"name": "DeleteCleanup_Bulk"})
    assert r.status_code == 200
    pid = r.json()["id"]

    db = SessionLocal()
    try:
        user = User(username="cleanup_bulk_member", role="viewer")
        user.set_password("pass123")
        db.add(user)
        db.flush()
        db.add(ProjectMembership(project_id=pid, user_id=user.id, role="viewer"))
        db.add(DecisionTableConstraint(project_id=pid, constraint_type="E", targets=[], description="x"))
        db.commit()
    finally:
        db.close()

    resp = auth_client.post("/api/projects/bulk-delete-force", json={"project_ids": [pid]})
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted"] == 1

    db = SessionLocal()
    try:
        assert db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id == pid).count() == 0
        assert db.query(ProjectMembership).filter(ProjectMembership.project_id == pid).count() == 0
    finally:
        db.close()
