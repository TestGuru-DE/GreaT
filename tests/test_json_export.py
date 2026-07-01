# REQ-1001: JSON Export
# TDD: Tests werden VOR der Implementierung geschrieben.
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _create_project_with_testcases() -> tuple[int, int]:
    """Hilfsfunktion: Projekt mit Kategorien + Generierung anlegen. Gibt (pid, gen_id) zurück."""
    name = f"JSONExport-{uuid.uuid4().hex[:6]}"
    r = client.post("/api/projects", json={"name": name})
    assert r.status_code == 200
    pid = r.json()["id"]

    r = client.post(f"/api/projects/{pid}/categories", json={"name": "Farbe", "order_index": 0})
    assert r.status_code == 200
    cid = r.json()["id"]
    client.post(f"/api/categories/{cid}/values", json={"value": "Rot"})
    client.post(f"/api/categories/{cid}/values", json={"value": "Blau"})

    r = client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    assert r.status_code == 200
    gen_id = r.json()["generation_id"]
    return pid, gen_id


class TestJsonExport:
    """JSON Export – REQ-1001."""

    def test_export_json_gibt_200(self):
        # REQ-1001: Endpunkt erreichbar
        _, gen_id = _create_project_with_testcases()
        r = client.get(f"/api/generations/{gen_id}/export/json")
        assert r.status_code == 200

    def test_export_json_content_type(self):
        # REQ-1001: Content-Type muss application/json sein
        _, gen_id = _create_project_with_testcases()
        r = client.get(f"/api/generations/{gen_id}/export/json")
        assert "application/json" in r.headers["content-type"]

    def test_export_json_struktur(self):
        # REQ-1001: Strukturiertes JSON mit generation_id, strategy, testcases
        _, gen_id = _create_project_with_testcases()
        r = client.get(f"/api/generations/{gen_id}/export/json")
        data = r.json()
        assert "generation_id" in data
        assert "strategy" in data
        assert "testcases" in data
        assert isinstance(data["testcases"], list)

    def test_export_json_testcases_haben_assignments(self):
        # REQ-1001: Jeder Testfall hat assignments mit Kategorie→Wert
        _, gen_id = _create_project_with_testcases()
        r = client.get(f"/api/generations/{gen_id}/export/json")
        data = r.json()
        assert len(data["testcases"]) > 0
        for tc in data["testcases"]:
            assert "name" in tc
            assert "assignments" in tc
            assert isinstance(tc["assignments"], dict)

    def test_export_json_enthaelt_kategorienamen(self):
        # REQ-1001: assignments enthalten den Kategorienamen als Schlüssel
        _, gen_id = _create_project_with_testcases()
        r = client.get(f"/api/generations/{gen_id}/export/json")
        data = r.json()
        for tc in data["testcases"]:
            assert "Farbe" in tc["assignments"]

    def test_export_json_nicht_existierende_generation(self):
        # REQ-1001: 404 bei unbekannter Generation
        r = client.get("/api/generations/999999/export/json")
        assert r.status_code == 404
