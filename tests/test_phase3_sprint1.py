# tests/test_phase3_sprint1.py
# REQ-3001: Top-Navigation
# REQ-3009: Karteireiter Generierte Testfaelle (Backend)
# REQ-3012: Alt+N Shortcut entfernen (nur Smoke-Test auf Frontend-Build)
# TDD RED-Phase
import uuid
import pytest
from app.main import app


def _uid():
    return uuid.uuid4().hex[:6]


def _make_project_with_generation(auth_client):
    p = auth_client.post("/api/projects", json={"name": f"P3-{_uid()}"}).json()
    pid = p["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "K", "order_index": 0}).json()
    auth_client.post(f"/api/categories/{c['id']}/values", json={"value": "V1"})
    auth_client.post(f"/api/categories/{c['id']}/values", json={"value": "V2"})
    gen = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"}).json()
    return pid, gen["generation_id"]


# --------------------------------------------------------------------------
# REQ-3009: Generierungs-Export (wird als Tab gebraucht)
# --------------------------------------------------------------------------

class TestGenerationExport:
    """REQ-3009: Generierungen koennen einzeln exportiert werden."""

    def test_export_json(self, auth_client):
        pid, gid = _make_project_with_generation(auth_client)
        r = auth_client.get(f"/api/generations/{gid}/export/json")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_export_csv(self, auth_client):
        pid, gid = _make_project_with_generation(auth_client)
        r = auth_client.get(f"/api/generations/{gid}/export/csv")
        assert r.status_code == 200

    def test_export_excel(self, auth_client):
        pid, gid = _make_project_with_generation(auth_client)
        r = auth_client.get(f"/api/generations/{gid}/export/xlsx")
        assert r.status_code == 200

    def test_generation_delete(self, auth_client):
        """REQ-3009: Einzelne Generierung kann geloescht werden."""
        pid, gid = _make_project_with_generation(auth_client)
        r = auth_client.delete(f"/api/generations/{gid}")
        assert r.status_code == 200
        # Nicht mehr in der Liste
        gens = auth_client.get(f"/api/projects/{pid}/generations").json()
        assert all(g["id"] != gid for g in gens)

    def test_generation_delete_not_found(self, auth_client):
        r = auth_client.delete("/api/generations/99999")
        assert r.status_code == 404

    def test_generation_list_after_delete(self, auth_client):
        """Nach Loeschen einer Generierung werden andere nicht beeintraechtig."""
        pid, gid1 = _make_project_with_generation(auth_client)
        gen2 = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "pairwise"}).json()
        gid2 = gen2["generation_id"]
        auth_client.delete(f"/api/generations/{gid1}")
        gens = auth_client.get(f"/api/projects/{pid}/generations").json()
        assert len(gens) == 1
        assert gens[0]["id"] == gid2