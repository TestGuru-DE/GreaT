"""
tests/test_api_delete_endpoints.py
REQ-1206: DELETE-Endpunkte fuer Projekte, Kategorien und Werte

TDD: Tests werden zuerst geschrieben (RED), dann implementiert (GREEN).

REQ-1300: Verwendet die gemeinsame Test-DB aus conftest.py,
nicht eine separate Datei im Projektverzeichnis.
"""
import uuid

import pytest

from app.main import app
from app.database import Base, get_db, SessionLocal


def _override_get_db():
    """Override fuer get_db – verwendet die gemeinsame Test-DB aus conftest."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Stellt sicher, dass die Test-DB-Schema vorhanden ist und ueberschreibt get_db.

    REQ-1300: Verwendet die gemeinsame Test-DB (keine separate Datei).
    Kein drop_all im Teardown, da die DB geteilt ist und andere Tests
    auf demselben Schema arbeiten.
    """
    Base.metadata.create_all(bind=SessionLocal().get_bind())
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(auth_client):
    return auth_client


@pytest.fixture
def project(client):
    r = client.post("/api/projects", json={"name": f"DEL-Testprojekt-{uuid.uuid4().hex[:8]}"})
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def category(client, project):
    r = client.post(f"/api/projects/{project['id']}/categories", json={"name": "KAT-DEL"})
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def value(client, category):
    r = client.post(f"/api/categories/{category['id']}/values", json={"value": "VAL-DEL"})
    assert r.status_code == 200
    return r.json()


class TestDeleteProject:
    def test_delete_existing_project(self, client, project):
        """REQ-1206: DELETE /projects/{pid} loescht Projekt und gibt 200 zurueck."""
        r = client.delete(f"/api/projects/{project['id']}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_deleted_project_not_in_list(self, client, project):
        """REQ-1206: Nach dem Loeschen ist das Projekt nicht mehr in der Liste."""
        client.delete(f"/api/projects/{project['id']}")
        r = client.get("/api/projects")
        ids = [p["id"] for p in r.json()]
        assert project["id"] not in ids

    def test_delete_nonexistent_project_returns_404(self, client):
        """REQ-1206: Loeschen eines nicht vorhandenen Projekts -> 404."""
        r = client.delete("/api/projects/99999")
        assert r.status_code == 404


class TestDeleteCategory:
    def test_delete_existing_category(self, client, category):
        """REQ-1206: DELETE /categories/{cid} loescht Kategorie."""
        r = client.delete(f"/api/categories/{category['id']}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_deleted_category_not_in_project(self, client, project, category):
        """REQ-1206: Kategorie ist nach dem Loeschen nicht mehr im Projekt."""
        client.delete(f"/api/categories/{category['id']}")
        r = client.get(f"/api/projects/{project['id']}/categories")
        ids = [c["id"] for c in r.json()]
        assert category["id"] not in ids

    def test_delete_nonexistent_category_returns_404(self, client):
        """REQ-1206: Loeschen einer nicht vorhandenen Kategorie -> 404."""
        r = client.delete("/api/categories/99999")
        assert r.status_code == 404


class TestDeleteValue:
    def test_delete_existing_value(self, client, value):
        """REQ-1206: DELETE /values/{vid} loescht Wert."""
        r = client.delete(f"/api/values/{value['id']}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_deleted_value_not_in_category(self, client, category, value):
        """REQ-1206: Wert ist nach dem Loeschen nicht mehr in der Kategorie."""
        client.delete(f"/api/values/{value['id']}")
        r = client.get(f"/api/categories/{category['id']}/values")
        ids = [v["id"] for v in r.json()]
        assert value["id"] not in ids

    def test_delete_nonexistent_value_returns_404(self, client):
        """REQ-1206: Loeschen eines nicht vorhandenen Werts -> 404."""
        r = client.delete("/api/values/99999")
        assert r.status_code == 404