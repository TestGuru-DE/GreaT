"""
tests/test_api_strategies_list.py
REQ-3039, REQ-3044: /api/strategies muss alle implementierten Strategien zurueckgeben,
insbesondere "t_wise" und "mcdc".
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestStrategiesList:
    """GET /api/strategies gibt alle implementierten Strategien zurueck."""

    def test_strategies_includes_t_wise(self, auth_client):
        """REQ-3039: t_wise muss in der Strategienliste enthalten sein."""
        response = auth_client.get("/api/strategies")
        assert response.status_code == 200
        strategies = response.json()
        assert "t_wise" in strategies, f"t_wise fehlt in {strategies}"

    def test_strategies_includes_mcdc(self, auth_client):
        """REQ-3044: mcdc muss in der Strategienliste enthalten sein."""
        response = auth_client.get("/api/strategies")
        assert response.status_code == 200
        strategies = response.json()
        assert "mcdc" in strategies, f"mcdc fehlt in {strategies}"

    def test_strategies_includes_all_original(self, auth_client):
        """Alle urspruenglichen Strategien bleiben erhalten."""
        response = auth_client.get("/api/strategies")
        assert response.status_code == 200
        strategies = response.json()
        for expected in ["all", "each", "linear", "pairwise", "risk_based"]:
            assert expected in strategies, f"{expected} fehlt in {strategies}"

    def test_strategies_count(self, auth_client):
        """Die Strategienliste enthaelt mindestens 7 Eintraege (5 urspruenglich + t_wise + mcdc)."""
        response = auth_client.get("/api/strategies")
        assert response.status_code == 200
        strategies = response.json()
        assert len(strategies) >= 7, f"Erwartet mindestens 7 Strategien, erhalten {len(strategies)}: {strategies}"