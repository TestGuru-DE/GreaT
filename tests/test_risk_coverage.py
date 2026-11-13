"""
REQ-3050: Risikoabdeckung pro Testfall
Jeder generierte Testfall erhaelt ein risk_coverage-Feld (Summe der risk_weight-Werte).
"""
import pytest
from app.main import app
from app.database import SessionLocal, engine, Base


@pytest.fixture(scope="function")
def clean_db():
    """Stellt sicher, dass das Test-DB-Schema vorhanden ist.

    REQ-1300: Verwendet die gemeinsame Test-DB aus conftest.
    Kein drop_all, da die DB geteilt ist. create_all ist idempotent.
    """
    Base.metadata.create_all(bind=engine)
    yield


def test_risk_coverage_calculation(auth_client, clean_db):
    """REQ-3050: risk_coverage summiert risk_weight korrekt."""
    # Projekt erstellen
    resp = auth_client.post("/api/projects", json={"name": "RiskProject"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # Kategorien + Werte mit verschiedenen risk_weights
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat1_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat1_id}/values", json={"value": "Chrome", "risk_weight": 3})
    auth_client.post(f"/api/categories/{cat1_id}/values", json={"value": "Firefox", "risk_weight": 2})

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat2_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat2_id}/values", json={"value": "Windows", "risk_weight": 1})
    auth_client.post(f"/api/categories/{cat2_id}/values", json={"value": "Linux", "risk_weight": 5})

    # All-Combinations generieren
    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    # Testfaelle abrufen
    resp = auth_client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    data = resp.json()
    testcases = data["testcases"]  # REQ-3051: Response hat jetzt testcases und risk_summary

    # Erwartete Kombinationen und risk_coverage
    expected = {
        ("Chrome", "Windows"): 4.0,  # 3 + 1
        ("Chrome", "Linux"): 8.0,    # 3 + 5
        ("Firefox", "Windows"): 3.0, # 2 + 1
        ("Firefox", "Linux"): 7.0,   # 2 + 5
    }

    found = {}
    for tc in testcases:
        browser = tc["assignments"]["Browser"]
        os = tc["assignments"]["OS"]
        risk = tc["risk_coverage"]
        found[(browser, os)] = risk

    assert found == expected, f"risk_coverage falsch: {found}"


def test_risk_coverage_zero_when_default_weights(auth_client, clean_db):
    """REQ-3050: risk_coverage = Anzahl Werte wenn alle risk_weight=1 (Default)."""
    resp = auth_client.post("/api/projects", json={"name": "DefaultRisk"})
    pid = resp.json()["id"]

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Color"})
    cat_id = resp.json()["id"]
    # Default risk_weight = 1
    auth_client.post(f"/api/categories/{cat_id}/values", json={"value": "Red"})
    auth_client.post(f"/api/categories/{cat_id}/values", json={"value": "Blue"})

    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    gen_id = resp.json()["generation_id"]

    resp = auth_client.get(f"/api/generations/{gen_id}/testcases")
    data = resp.json()
    testcases = data["testcases"]  # REQ-3051: Response hat jetzt testcases und risk_summary

    # Each-Choice generiert 2 Testfaelle (Red, Blue)
    assert len(testcases) == 2
    for tc in testcases:
        # Jeder Testfall hat 1 Wert mit risk_weight=1
        assert tc["risk_coverage"] == 1.0


def test_risk_coverage_in_response(auth_client, clean_db):
    """REQ-3050: risk_coverage ist im API-Response vorhanden."""
    resp = auth_client.post("/api/projects", json={"name": "Test"})
    pid = resp.json()["id"]

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "A"})
    cat_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_id}/values", json={"value": "X", "risk_weight": 7})

    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    gen_id = resp.json()["generation_id"]

    resp = auth_client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    data = resp.json()
    testcases = data["testcases"]  # REQ-3051: Response hat jetzt testcases und risk_summary

    assert len(testcases) == 1
    tc = testcases[0]
    assert "risk_coverage" in tc
    assert tc["risk_coverage"] == 7.0