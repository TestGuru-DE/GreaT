"""REQ-4021: Router-Integration Tests fuer Optimistic Concurrency Control"""
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app


def _unique_suffix():
    """Erzeugt einen eindeutigen Suffix fuer Test-Namen."""
    return f"{int(time.time() * 1000)}"


class TestProjectConcurrency:
    """Tests fuer PUT /api/projects/{id} mit Version-Pruefung."""

    def test_put_project_correct_version(self, auth_client):
        """PUT /api/projects/{id} mit korrekter version -> 200."""
        suffix = _unique_suffix()
        # Projekt erstellen
        r = auth_client.post("/api/projects", json={"name": f"Concurrency-Test-{suffix}"})
        assert r.status_code == 200
        project = r.json()
        pid = project["id"]

        # Erstes Update ohne version (None) -> OK
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"Updated-{suffix}"})
        assert r.status_code == 200
        assert r.json()["name"] == f"Updated-{suffix}"

    def test_put_project_wrong_version_conflict(self, auth_client):
        """PUT /api/projects/{id} mit falscher version -> 409."""
        suffix = _unique_suffix()
        # Projekt erstellen
        r = auth_client.post("/api/projects", json={"name": f"Conflict-Test-{suffix}"})
        assert r.status_code == 200
        project = r.json()
        pid = project["id"]

        # Erstes Update ohne version -> version wird 1
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"First-{suffix}"})
        assert r.status_code == 200

        # Zweites Update mit version=0 (falsch, server hat 1) -> 409
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"Second-{suffix}", "version": 0})
        assert r.status_code == 409
        detail = r.json()["detail"]
        assert detail["type"] == "version_conflict"
        assert detail["client_version"] == 0
        assert detail["server_version"] == 1

    def test_put_project_nonexistent(self, auth_client):
        """PUT /api/projects/{id} fuer nicht-existentes Projekt -> 404."""
        r = auth_client.put("/api/projects/99999", json={"name": "Ghost"})
        assert r.status_code == 404

    def test_put_project_version_increments(self, auth_client):
        """Mehrere Updates inkrementieren version korrekt."""
        suffix = _unique_suffix()
        r = auth_client.post("/api/projects", json={"name": f"Increment-Test-{suffix}"})
        assert r.status_code == 200
        pid = r.json()["id"]

        # Update 1: version 0 -> 1
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"V1-{suffix}"})
        assert r.status_code == 200

        # Update 2 mit korrekter version=1 -> version 2
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"V2-{suffix}", "version": 1})
        assert r.status_code == 200

        # Update 3 mit korrekter version=2 -> version 3
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"V3-{suffix}", "version": 2})
        assert r.status_code == 200

        # Update 4 mit falscher version=1 -> 409
        r = auth_client.put(f"/api/projects/{pid}", json={"name": f"V4-{suffix}", "version": 1})
        assert r.status_code == 409


class TestDataClassConcurrency:
    """Tests fuer PUT /api/dataclasses/{id} mit Version-Pruefung."""

    def test_put_dataclass_correct_version(self, auth_client):
        """PUT /api/dataclasses/{id} mit korrekter version -> 200."""
        suffix = _unique_suffix()
        r = auth_client.post("/api/dataclasses", json={
            "name": f"DC-Concurrency-{suffix}",
            "value_type": "text",
        })
        assert r.status_code == 200
        dcid = r.json()["id"]

        # Update ohne version -> OK
        r = auth_client.put(f"/api/dataclasses/{dcid}", json={"name": f"DC-Updated-{suffix}"})
        assert r.status_code == 200
        assert r.json()["name"] == f"DC-Updated-{suffix}"

    def test_put_dataclass_wrong_version(self, auth_client):
        """PUT /api/dataclasses/{id} mit falscher version -> 409."""
        suffix = _unique_suffix()
        r = auth_client.post("/api/dataclasses", json={
            "name": f"DC-Conflict-{suffix}",
            "value_type": "text",
        })
        assert r.status_code == 200
        dcid = r.json()["id"]

        # Erstes Update -> version 1
        r = auth_client.put(f"/api/dataclasses/{dcid}", json={"name": f"DC-V1-{suffix}"})
        assert r.status_code == 200

        # Zweites Update mit version=0 -> 409
        r = auth_client.put(f"/api/dataclasses/{dcid}", json={"name": f"DC-V2-{suffix}", "version": 0})
        assert r.status_code == 409


class TestDataNodeConcurrency:
    """Tests fuer PUT /api/datanodes/{id} mit Version-Pruefung."""

    def test_put_datanode_correct_version(self, auth_client):
        """PUT /api/datanodes/{id} mit korrekter version -> 200."""
        suffix = _unique_suffix()
        r = auth_client.post("/api/datanodes", json={"name": f"Node-Test-{suffix}"})
        assert r.status_code == 200
        node_id = r.json()["id"]

        # Update ohne version -> OK
        r = auth_client.put(f"/api/datanodes/{node_id}", json={"name": f"Node-Updated-{suffix}"})
        assert r.status_code == 200
        assert r.json()["name"] == f"Node-Updated-{suffix}"

    def test_put_datanode_wrong_version(self, auth_client):
        """PUT /api/datanodes/{id} mit falscher version -> 409."""
        suffix = _unique_suffix()
        r = auth_client.post("/api/datanodes", json={"name": f"Node-Conflict-{suffix}"})
        assert r.status_code == 200
        node_id = r.json()["id"]

        # Erstes Update -> version 1
        r = auth_client.put(f"/api/datanodes/{node_id}", json={"name": f"Node-V1-{suffix}"})
        assert r.status_code == 200

        # Zweites Update mit version=0 -> 409
        r = auth_client.put(f"/api/datanodes/{node_id}", json={"name": f"Node-V2-{suffix}", "version": 0})
        assert r.status_code == 409