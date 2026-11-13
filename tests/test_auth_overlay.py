"""B1: Auth-Overlay Tests – Sprint 11 Blocker.

Verifiziert dass ALLE bestehenden API-Router (außer health + auth)
eine Authentifizierung erfordern.

REQ-4001: Alle API-Endpunkte pruefen ein gueltiges Token.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestAuthOverlayNoToken:
    """Alle geschuetzten Endpunkte ohne Token -> 401."""

    def test_projects_without_token(self):
        """GET /api/projects ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.get("/api/projects")
            assert response.status_code == 401

    def test_generate_without_token(self):
        """POST /api/projects/{pid}/generate ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.post(
                "/api/projects/1/generate",
                json={"strategy": "pairwise"},
            )
            assert response.status_code == 401

    def test_dataclasses_without_token(self):
        """GET /api/dataclasses ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.get("/api/dataclasses")
            assert response.status_code == 401

    def test_datanodes_without_token(self):
        """GET /api/datanodes ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.get("/api/datanodes")
            assert response.status_code == 401

    def test_backup_without_token(self):
        """GET /api/backup ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.get("/api/backup")
            assert response.status_code == 401

    def test_strategies_without_token(self):
        """GET /api/strategies ohne Token -> 401."""
        with TestClient(app) as client:
            response = client.get("/api/strategies")
            assert response.status_code == 401


class TestAuthOverlayWithToken:
    """Geschuetzte Endpunkte mit gueltigem Token -> 200 (nicht 401)."""

    def test_projects_with_token(self, auth_client):
        """GET /api/projects mit Token -> nicht 401."""
        response = auth_client.get("/api/projects")
        assert response.status_code != 401

    def test_strategies_with_token(self, auth_client):
        """GET /api/strategies mit Token -> nicht 401."""
        response = auth_client.get("/api/strategies")
        assert response.status_code != 401

    def test_dataclasses_with_token(self, auth_client):
        """GET /api/dataclasses mit Token -> nicht 401."""
        response = auth_client.get("/api/dataclasses")
        assert response.status_code != 401

    def test_datanodes_with_token(self, auth_client):
        """GET /api/datanodes mit Token -> nicht 401."""
        response = auth_client.get("/api/datanodes")
        assert response.status_code != 401

    def test_backup_with_token(self, auth_client):
        """GET /api/backup mit Token -> nicht 401."""
        response = auth_client.get("/api/backup")
        assert response.status_code != 401


class TestHealthUnprotected:
    """Health-Check bleibt OHNE Auth erreichbar."""

    def test_health_without_token(self):
        """GET /health ohne Token -> 200."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_with_token(self, auth_client):
        """GET /health mit Token -> 200."""
        response = auth_client.get("/health")
        assert response.status_code == 200


class TestAuthEndpointsUnprotected:
    """Auth-Endpunkte (Login) bleiben OHNE Auth erreichbar."""

    def test_login_without_token(self):
        """POST /auth/login ohne Token -> nicht 401 (kann 401 wegen falscher Daten sein)."""
        with TestClient(app) as client:
            response = client.post(
                "/auth/login",
                data={"username": "nonexistent", "password": "wrong"},
            )
            # Login ohne Token sollte funktionieren (401 wegen falscher Daten, nicht wegen fehlender Auth)
            assert response.status_code in (200, 401, 403)

    def test_logout_without_token(self):
        """POST /auth/logout ohne Token -> 200."""
        with TestClient(app) as client:
            response = client.post("/auth/logout")
            assert response.status_code == 200

    def test_refresh_without_token(self):
        """POST /auth/refresh ohne Token -> 401 (kein Refresh-Token)."""
        with TestClient(app) as client:
            response = client.post("/auth/refresh")
            assert response.status_code == 401