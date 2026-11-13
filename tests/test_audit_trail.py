"""REQ-4024: Audit-Trail Tests (last_modified_by + last_modified_at)"""
import pytest
import time
from datetime import datetime, timezone
from app.main import app
from app.database import SessionLocal
from app.models.auth import User
from app.models import Project, Category, Value
from app.models.project_membership import ProjectMembership


def _unique_suffix():
    """Erzeugt einen eindeutigen Suffix fuer Test-Namen."""
    return f"{int(time.time() * 1000)}"


@pytest.fixture(scope="function")
def audit_project(auth_client, _auth_cookies):
    """Erstellt ein Projekt und stellt Mitgliedschaft sicher."""
    suffix = _unique_suffix()
    r = auth_client.post("/api/projects", json={"name": f"Audit-Test-{suffix}"})
    assert r.status_code == 200
    project = r.json()

    # Hole den aktuellen User aus den Cookies
    from app.database import SessionLocal as _SessionLocal
    from app.models.auth import User as _User
    import jwt
    from app.config import JWT_SECRET_KEY, JWT_ALGORITHM

    token = list(_auth_cookies.values())[0]  # access_token
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    user_id = int(payload.get("sub"))

    # Mitgliedschaft sicherstellen
    db = SessionLocal()
    try:
        existing = db.query(ProjectMembership).filter(
            ProjectMembership.project_id == project["id"],
            ProjectMembership.user_id == user_id,
        ).first()
        if not existing:
            membership = ProjectMembership(
                project_id=project["id"],
                user_id=user_id,
                role="editor",
            )
            db.add(membership)
            db.commit()
    finally:
        db.close()

    return project, user_id


class TestProjectAuditTrail:
    """Tests fuer Audit-Trail bei Projekt-Updates."""

    def test_put_project_sets_audit_fields(self, auth_client, audit_project):
        """PUT /api/projects/{id} setzt last_modified_by und last_modified_at."""
        project, user_id = audit_project
        pid = project["id"]

        # Update ausfuehren
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"Audit-Updated-{_unique_suffix()}"})
        assert r.status_code == 200

        # Audit-Felder pruefen
        db = SessionLocal()
        try:
            project = db.get(Project, pid)
            assert project.last_modified_by == user_id
            assert project.last_modified_at is not None
            # Pruefe dass Timestamp nicht in der Zukunft liegt
            now = datetime.now(timezone.utc)
            # SQLite kann timezone-info verlieren; normalisieren zum Vergleich
            last_mod = project.last_modified_at
            if last_mod.tzinfo is None:
                last_mod = last_mod.replace(tzinfo=timezone.utc)
            assert last_mod <= now
        finally:
            db.close()

    def test_put_project_overwrites_previous_audit(self, auth_client, audit_project):
        """Nachfolgende Updates ueberschreiben vorherige Audit-Werte."""
        project, user_id = audit_project
        pid = project["id"]

        # Erstes Update
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"First-{_unique_suffix()}"})
        assert r.status_code == 200

        db = SessionLocal()
        try:
            project = db.get(Project, pid)
            first_time = project.last_modified_at
        finally:
            db.close()

        # Zweites Update (kurz danach)
        import time as _time
        _time.sleep(0.1)
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"Second-{_unique_suffix()}", "version": 1})
        assert r.status_code == 200

        db = SessionLocal()
        try:
            project = db.get(Project, pid)
            second_time = project.last_modified_at
            # Neuer Timestamp sollte groesser oder gleich sein
            assert second_time >= first_time
            assert project.last_modified_by == user_id
        finally:
            db.close()


class TestCategoryAuditTrail:
    """Tests fuer Audit-Trail bei Kategorie-Updates."""

    def test_rename_category_sets_audit_fields(self, auth_client, audit_project):
        """PATCH /categories/{cid}/rename setzt Audit-Felder."""
        project, user_id = audit_project
        pid = project["id"]
        suffix = _unique_suffix()

        # Kategorie erstellen
        r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": f"Audit-Category-{suffix}"})
        assert r.status_code == 200
        cid = r.json()["id"]

        # Rename ausfuehren
        r = auth_client.patch(f"/api/categories/{cid}/rename", json={"name": f"Renamed-{suffix}"})
        assert r.status_code == 200

        # Audit-Felder pruefen
        db = SessionLocal()
        try:
            cat = db.get(Category, cid)
            assert cat.last_modified_by == user_id
            assert cat.last_modified_at is not None
        finally:
            db.close()


class TestValueAuditTrail:
    """Tests fuer Audit-Trail bei Wert-Updates."""

    def test_rename_value_sets_audit_fields(self, auth_client, audit_project):
        """PATCH /values/{vid}/rename setzt Audit-Felder."""
        project, user_id = audit_project
        pid = project["id"]
        suffix = _unique_suffix()

        # Kategorie und Wert erstellen
        r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": f"Audit-Val-Cat-{suffix}"})
        assert r.status_code == 200
        cid = r.json()["id"]

        r = auth_client.post(f"/api/categories/{cid}/values", json={"value": f"Original-{suffix}"})
        assert r.status_code == 200
        vid = r.json()["id"]

        # Rename ausfuehren
        r = auth_client.patch(f"/api/values/{vid}/rename", json={"value": f"Renamed-{suffix}"})
        assert r.status_code == 200

        # Audit-Felder pruefen
        db = SessionLocal()
        try:
            val = db.get(Value, vid)
            assert val.last_modified_by == user_id
            assert val.last_modified_at is not None
        finally:
            db.close()

    def test_update_value_properties_sets_audit_fields(self, auth_client, audit_project):
        """PATCH /values/{vid}/properties setzt Audit-Felder."""
        project, user_id = audit_project
        pid = project["id"]
        suffix = _unique_suffix()

        # Kategorie und Wert erstellen
        r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": f"Audit-Prop-Cat-{suffix}"})
        assert r.status_code == 200
        cid = r.json()["id"]

        r = auth_client.post(f"/api/categories/{cid}/values", json={"value": f"Prop-Val-{suffix}"})
        assert r.status_code == 200
        vid = r.json()["id"]

        # Properties aktualisieren
        r = auth_client.patch(
            f"/api/values/{vid}/properties",
            json={"risk_weight": 5, "vtype": "number"}
        )
        assert r.status_code == 200

        # Audit-Felder pruefen
        db = SessionLocal()
        try:
            val = db.get(Value, vid)
            assert val.last_modified_by == user_id
            assert val.last_modified_at is not None
            assert val.risk_weight == 5
            assert val.vtype == "number"
        finally:
            db.close()