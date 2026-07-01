"""
tests/test_api_rename_reorder.py
REQ-1213: Rename-Endpunkte fuer Kategorien und Werte
REQ-1209: Reorder-Endpunkt fuer Kategorien
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db

TEST_DB = "sqlite:///./test_rename_reorder.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture
def client(): return TestClient(app)

@pytest.fixture
def project(client):
    r = client.post("/api/projects", json={"name": "Rename-Test"})
    return r.json()

@pytest.fixture
def category(client, project):
    r = client.post(f"/api/projects/{project['id']}/categories", json={"name": "KAT-A"})
    return r.json()

@pytest.fixture
def value(client, category):
    r = client.post(f"/api/categories/{category['id']}/values", json={"value": "VAL-1"})
    return r.json()


class TestRenameCategory:
    def test_rename_category(self, client, category):
        """REQ-1213: PATCH /categories/{cid}/rename aendert den Namen."""
        r = client.patch(f"/api/categories/{category['id']}/rename", json={"name": "KAT-B"})
        assert r.status_code == 200
        assert r.json()["name"] == "KAT-B"

    def test_rename_category_empty_name_rejected(self, client, category):
        """REQ-1213: Leerer Name wird abgelehnt."""
        r = client.patch(f"/api/categories/{category['id']}/rename", json={"name": ""})
        assert r.status_code == 422

    def test_rename_nonexistent_category(self, client):
        """REQ-1213: Umbenennen einer nicht vorhandenen Kategorie -> 404."""
        r = client.patch("/api/categories/99999/rename", json={"name": "NEU"})
        assert r.status_code == 404


class TestRenameValue:
    def test_rename_value(self, client, value):
        """REQ-1213: PATCH /values/{vid}/rename aendert den Wert."""
        r = client.patch(f"/api/values/{value['id']}/rename", json={"value": "VAL-2"})
        assert r.status_code == 200
        assert r.json()["value"] == "VAL-2"

    def test_rename_nonexistent_value(self, client):
        """REQ-1213: Umbenennen eines nicht vorhandenen Werts -> 404."""
        r = client.patch("/api/values/99999/rename", json={"value": "NEU"})
        assert r.status_code == 404


class TestReorderCategories:
    def test_reorder_categories(self, client, project):
        """REQ-1209: PATCH /projects/{pid}/categories/reorder setzt order_index."""
        r1 = client.post(f"/api/projects/{project['id']}/categories", json={"name": "A"})
        r2 = client.post(f"/api/projects/{project['id']}/categories", json={"name": "B"})
        id1, id2 = r1.json()["id"], r2.json()["id"]
        # Reihenfolge umkehren
        r = client.patch(f"/api/projects/{project['id']}/categories/reorder",
                         json={"order": [id2, id1]})
        assert r.status_code == 200
        # Kategorien in neuer Reihenfolge pruefen
        cats = client.get(f"/api/projects/{project['id']}/categories").json()
        assert cats[0]["id"] == id2
        assert cats[1]["id"] == id1