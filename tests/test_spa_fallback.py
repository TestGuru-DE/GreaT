"""SPA Fallback-Tests (B-28)."""
import pytest


def test_help_route_returns_html(client):
    """GET /help -> 200 HTML."""
    resp = client.get("/help")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_unknown_api_path_returns_404_json(client):
    """GET /api/gibtsnicht -> 404 JSON, keine index.html."""
    resp = client.get("/api/gibtsnicht")
    assert resp.status_code == 404
    assert "application/json" in resp.headers.get("content-type", "")


def test_projects_path_returns_html(client):
    """GET /projects/5 -> 200 HTML."""
    resp = client.get("/projects/5")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_auth_path_not_caught_by_spa(client):
    """GET /auth/gibtsnicht -> 404 JSON, keine index.html."""
    resp = client.get("/auth/gibtsnicht")
    assert resp.status_code == 404
    assert "application/json" in resp.headers.get("content-type", "")


def test_health_path_not_caught_by_spa(client):
    """GET /health -> 200 (health endpoint), keine index.html."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_docs_path_not_caught_by_spa(client):
    """GET /docs/something -> 404 JSON, keine index.html."""
    resp = client.get("/docs/something")
    assert resp.status_code == 404
    assert "application/json" in resp.headers.get("content-type", "")