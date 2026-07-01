# tests/test_bulk_delete.py
# REQ-2002: Bulk-Delete mehrerer Projekte
# TDD: Tests wurden VOR der Implementierung geschrieben (RED-Phase)
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _uid() -> str:
    return uuid.uuid4().hex[:6]


def _create_project(prefix: str) -> int:
    return client.post("/api/projects", json={"name": f"{prefix}-{_uid()}"}).json()["id"]


def _create_project_with_gen(prefix: str) -> int:
    pid = _create_project(prefix)
    c = client.post(f"/api/projects/{pid}/categories", json={"name": "K", "order_index": 0}).json()
    client.post(f"/api/categories/{c['id']}/values", json={"value": "V"})
    client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    return pid


class TestBulkDelete:
    """REQ-2002: Mehrere Projekte gleichzeitig loeschen."""

    def test_bulk_delete_gibt_200(self):
        ids = [_create_project("BulkA") for _ in range(2)]
        r = client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        assert r.status_code == 200

    def test_bulk_delete_loescht_projekte(self):
        ids = [_create_project("BulkB") for _ in range(3)]
        client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        remaining = [p["id"] for p in client.get("/api/projects").json()]
        for pid in ids:
            assert pid not in remaining

    def test_bulk_delete_gibt_deleted_count(self):
        ids = [_create_project("BulkC") for _ in range(2)]
        r = client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        data = r.json()
        assert "deleted" in data
        assert data["deleted"] == 2

    def test_bulk_delete_blockiert_wenn_generierungen_existieren(self):
        pid = _create_project_with_gen("BulkBlocked")
        pid_clean = _create_project("BulkClean")
        r = client.post("/api/projects/bulk-delete", json={"project_ids": [pid, pid_clean]})
        data = r.json()
        assert r.status_code == 200
        # Das Projekt mit Generierungen soll in blocked-Liste stehen
        assert pid in data.get("blocked", [])
        # Das saubere Projekt wird geloescht
        assert data.get("deleted", 0) >= 1

    def test_bulk_delete_leere_liste(self):
        r = client.post("/api/projects/bulk-delete", json={"project_ids": []})
        assert r.status_code == 200
        assert r.json()["deleted"] == 0

    def test_bulk_delete_force_loescht_auch_mit_generierungen(self):
        pid = _create_project_with_gen("BulkForce")
        r = client.post("/api/projects/bulk-delete-force", json={"project_ids": [pid]})
        assert r.status_code == 200
        remaining = [p["id"] for p in client.get("/api/projects").json()]
        assert pid not in remaining

    def test_bulk_delete_force_gibt_deleted_count(self):
        ids = [_create_project_with_gen("BulkForceN") for _ in range(2)]
        r = client.post("/api/projects/bulk-delete-force", json={"project_ids": ids})
        assert r.status_code == 200
        assert r.json()["deleted"] == 2
