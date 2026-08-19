"""REQ-4008: Health-Check Endpoint."""
from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient):
    """Health endpoint returns 200 OK."""
    r = client.get("/health")
    assert r.status_code == 200


def test_health_status_ok(client: TestClient):
    """Health status is 'ok' when DB is reachable."""
    r = client.get("/health")
    data = r.json()
    assert data["status"] == "ok"


def test_health_has_required_fields(client: TestClient):
    """Health response contains all required fields."""
    r = client.get("/health")
    data = r.json()
    assert "status" in data
    assert "version" in data
    assert "db" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_health_db_ok(client: TestClient):
    """Health indicates DB is 'ok'."""
    r = client.get("/health")
    assert r.json()["db"] == "ok"


def test_health_version_format(client: TestClient):
    """Version field is present and non-empty."""
    r = client.get("/health")
    version = r.json()["version"]
    assert isinstance(version, str)
    assert len(version) > 0


def test_health_uptime_is_integer(client: TestClient):
    """Uptime is a non-negative integer."""
    r = client.get("/health")
    uptime = r.json()["uptime_seconds"]
    assert isinstance(uptime, int)
    assert uptime >= 0


def test_health_timestamp_iso_format(client: TestClient):
    """Timestamp is in ISO 8601 format with Z suffix."""
    r = client.get("/health")
    timestamp = r.json()["timestamp"]
    assert timestamp.endswith("Z")
    # Basic validation: should be parseable as ISO datetime
    assert "T" in timestamp
