"""BUG-Fix: /health ohne API-Prefix."""
from fastapi.testclient import TestClient


def test_health_at_root_path(client: TestClient):
    """GET /health sollte 200 zurückgeben (nicht 404)."""
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_health_has_status_ok(client: TestClient):
    """Health-Response enthält status='ok' oder 'degraded'."""
    r = client.get("/health")
    data = r.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")


def test_health_has_uptime(client: TestClient):
    """Health-Response hat uptime_seconds."""
    r = client.get("/health")
    data = r.json()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0


def test_health_has_db_status(client: TestClient):
    """Health-Response enthält db-Status."""
    r = client.get("/health")
    data = r.json()
    assert "db" in data
