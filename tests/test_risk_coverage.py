"""
REQ-3050: Risikoabdeckung pro Testfall
Jeder generierte Testfall erhält ein risk_coverage-Feld (Summe der risk_weight-Werte).
"""
import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.db import SessionLocal, engine, Base

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_db():
    """Erstellt saubere Test-DB für jeden Test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_risk_coverage_calculation(clean_db):
    """REQ-3050: risk_coverage summiert risk_weight korrekt."""
    # Projekt erstellen
    resp = client.post("/api/projects", json={"name": "RiskProject"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # Kategorien + Werte mit verschiedenen risk_weights
    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat1_id = resp.json()["id"]
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Chrome", "risk_weight": 3})
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Firefox", "risk_weight": 2})

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat2_id = resp.json()["id"]
    client.post(f"/api/categories/{cat2_id}/values", json={"value": "Windows", "risk_weight": 1})
    client.post(f"/api/categories/{cat2_id}/values", json={"value": "Linux", "risk_weight": 5})

    # All-Combinations generieren
    resp = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    # Testfälle abrufen
    resp = client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    testcases = resp.json()

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


def test_risk_coverage_zero_when_default_weights(clean_db):
    """REQ-3050: risk_coverage = Anzahl Werte wenn alle risk_weight=1 (Default)."""
    resp = client.post("/api/projects", json={"name": "DefaultRisk"})
    pid = resp.json()["id"]

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "Color"})
    cat_id = resp.json()["id"]
    # Default risk_weight = 1
    client.post(f"/api/categories/{cat_id}/values", json={"value": "Red"})
    client.post(f"/api/categories/{cat_id}/values", json={"value": "Blue"})

    resp = client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    gen_id = resp.json()["generation_id"]

    resp = client.get(f"/api/generations/{gen_id}/testcases")
    testcases = resp.json()

    # Each-Choice generiert 2 Testfälle (Red, Blue)
    assert len(testcases) == 2
    for tc in testcases:
        # Jeder Testfall hat 1 Wert mit risk_weight=1
        assert tc["risk_coverage"] == 1.0


def test_risk_coverage_in_response(clean_db):
    """REQ-3050: risk_coverage ist im API-Response vorhanden."""
    resp = client.post("/api/projects", json={"name": "Test"})
    pid = resp.json()["id"]

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "A"})
    cat_id = resp.json()["id"]
    client.post(f"/api/categories/{cat_id}/values", json={"value": "X", "risk_weight": 7})

    resp = client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    gen_id = resp.json()["generation_id"]

    resp = client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    testcases = resp.json()

    assert len(testcases) == 1
    tc = testcases[0]
    assert "risk_coverage" in tc
    assert tc["risk_coverage"] == 7.0
