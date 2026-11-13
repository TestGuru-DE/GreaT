# tests/test_bulk_delete.py
# REQ-2002: Bulk-Delete mehrerer Projekte
# TDD: Tests wurden VOR der Implementierung geschrieben (RED-Phase)
import uuid
import pytest
from app.main import app


def _uid() -> str:
    return uuid.uuid4().hex[:6]


def _create_project(auth_client, prefix: str) -> int:
    return auth_client.post("/api/projects", json={"name": f"{prefix}-{_uid()}"}).json()["id"]


def _create_project_with_gen(auth_client, prefix: str) -> int:
    pid = _create_project(auth_client, prefix)
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "K", "order_index": 0}).json()
    auth_client.post(f"/api/categories/{c['id']}/values", json={"value": "V"})
    auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    return pid


class TestBulkDelete:
    """REQ-2002: Mehrere Projekte gleichzeitig loeschen."""

    def test_bulk_delete_gibt_200(self, auth_client):
        ids = [_create_project(auth_client, "BulkA") for _ in range(2)]
        r = auth_client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        assert r.status_code == 200

    def test_bulk_delete_loescht_projekte(self, auth_client):
        ids = [_create_project(auth_client, "BulkB") for _ in range(3)]
        auth_client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        remaining = [p["id"] for p in auth_client.get("/api/projects").json()]
        for pid in ids:
            assert pid not in remaining

    def test_bulk_delete_gibt_deleted_count(self, auth_client):
        ids = [_create_project(auth_client, "BulkC") for _ in range(2)]
        r = auth_client.post("/api/projects/bulk-delete", json={"project_ids": ids})
        data = r.json()
        assert "deleted" in data
        assert data["deleted"] == 2

    def test_bulk_delete_blockiert_wenn_generierungen_existieren(self, auth_client):
        pid = _create_project_with_gen(auth_client, "BulkBlocked")
        pid_clean = _create_project(auth_client, "BulkClean")
        r = auth_client.post("/api/projects/bulk-delete", json={"project_ids": [pid, pid_clean]})
        data = r.json()
        assert r.status_code == 200
        # Das Projekt mit Generierungen soll in blocked-Liste stehen
        assert pid in data.get("blocked", [])
        # Das saubere Projekt wird geloescht
        assert data.get("deleted", 0) >= 1

    def test_bulk_delete_leere_liste(self, auth_client):
        r = auth_client.post("/api/projects/bulk-delete", json={"project_ids": []})
        assert r.status_code == 200
        assert r.json()["deleted"] == 0

    def test_bulk_delete_force_loescht_auch_mit_generierungen(self, auth_client):
        pid = _create_project_with_gen(auth_client, "BulkForce")
        r = auth_client.post("/api/projects/bulk-delete-force", json={"project_ids": [pid]})
        assert r.status_code == 200
        remaining = [p["id"] for p in auth_client.get("/api/projects").json()]
        assert pid not in remaining

    def test_bulk_delete_force_gibt_deleted_count(self, auth_client):
        ids = [_create_project_with_gen(auth_client, "BulkForceN") for _ in range(2)]
        r = auth_client.post("/api/projects/bulk-delete-force", json={"project_ids": ids})
        assert r.status_code == 200
        assert r.json()["deleted"] == 2