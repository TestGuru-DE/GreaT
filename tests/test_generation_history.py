# tests/test_generation_history.py
# REQ-2001: Generierungshistorie – GET /api/projects/{pid}/generations
# TDD: Tests wurden VOR der Implementierung geschrieben (RED-Phase)
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)


def _uid() -> str:
    return uuid.uuid4().hex[:6]


def _setup_project_with_generation(prefix: str) -> tuple:
    """Hilfsfunktion: Projekt + Kategorie + Wert + Generierung anlegen."""
    p = client.post("/api/projects", json={"name": f"{prefix}-{_uid()}"}).json()
    pid = p["id"]
    c = client.post(f"/api/projects/{pid}/categories", json={"name": "Farbe", "order_index": 0}).json()
    client.post(f"/api/categories/{c['id']}/values", json={"value": "Rot"})
    client.post(f"/api/categories/{c['id']}/values", json={"value": "Blau"})
    gen = client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"}).json()
    return pid, gen["generation_id"]


class TestGenerationHistory:
    """REQ-2001: Generierungshistorie pro Projekt."""

    def test_history_endpoint_gibt_200(self):
        pid, _ = _setup_project_with_generation("HistTest")
        r = client.get(f"/api/projects/{pid}/generations")
        assert r.status_code == 200

    def test_history_gibt_liste_zurueck(self):
        pid, gen_id = _setup_project_with_generation("HistTest")
        r = client.get(f"/api/projects/{pid}/generations")
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_history_enthaelt_korrekte_felder(self):
        pid, gen_id = _setup_project_with_generation("HistTest")
        r = client.get(f"/api/projects/{pid}/generations")
        entry = r.json()[0]
        assert "id" in entry
        assert "strategy" in entry
        assert "created_at" in entry
        assert "testcase_count" in entry

    def test_history_mehrere_generierungen(self):
        pid, _ = _setup_project_with_generation("HistTest")
        # Zweite Generierung mit anderer Strategie
        client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
        r = client.get(f"/api/projects/{pid}/generations")
        assert len(r.json()) >= 2

    def test_history_nicht_vorhandenes_projekt(self):
        r = client.get("/api/projects/99999/generations")
        assert r.status_code == 404

    def test_history_leeres_projekt_ohne_generierungen(self):
        p = client.post("/api/projects", json={"name": f"HistEmpty-{_uid()}"}).json()
        r = client.get(f"/api/projects/{p['id']}/generations")
        assert r.status_code == 200
        assert r.json() == []