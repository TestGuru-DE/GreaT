"""REQ-4021/REQ-4022: Projekt-Version im Lesemodell (Grundlage fuer Konflikt-Erkennung)."""
from app.main import app  # noqa: F401
from fastapi.testclient import TestClient


def test_project_read_contains_version(auth_client):
    r = auth_client.post("/api/projects", json={"name": "VersionRead_Project"})
    assert r.status_code == 200
    assert "version" in r.json()
    assert r.json()["version"] == 0
    listed = auth_client.get("/api/projects").json()
    assert all("version" in p for p in listed)
