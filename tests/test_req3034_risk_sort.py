"""
REQ-3034: Risikobasierte Testfall-Sortierung (API-Ebene, End-to-End).

Generierte Testfaelle sollen absteigend nach kumuliertem Risiko-Score
sortiert werden, wobei Fehlerwert-Testfaelle (REQ-3018/BUG-5) weiterhin
Vorrang haben und ans Ende sortiert werden, unabhaengig von ihrem Risiko.
"""
import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from app.database import SessionLocal, engine, Base

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_db():
    """Erstellt saubere Test-DB fuer jeden Test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_testcases_sind_absteigend_nach_risk_coverage_sortiert(clean_db):
    """REQ-3034: Ohne Fehlerwerte ist die Reihenfolge streng nach risk_coverage absteigend."""
    resp = client.post("/api/projects", json={"name": "RiskSortProject"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat1_id = resp.json()["id"]
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Chrome", "risk_weight": 3})
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Firefox", "risk_weight": 1})

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat2_id = resp.json()["id"]
    client.post(f"/api/categories/{cat2_id}/values", json={"value": "Windows", "risk_weight": 1})
    client.post(f"/api/categories/{cat2_id}/values", json={"value": "Linux", "risk_weight": 5})

    resp = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    resp = client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    testcases = resp.json()["testcases"]

    # Reihenfolge wie von der DB persistiert (nach TestCase.id) muss bereits
    # absteigend nach risk_coverage sein (Sortierung erfolgt vor dem Persistieren).
    risk_values = [tc["risk_coverage"] for tc in testcases]
    assert risk_values == sorted(risk_values, reverse=True), (
        f"Testfaelle nicht absteigend nach Risiko sortiert: {risk_values}"
    )
    # Plausibilitaets-Check: hoechster Score zuerst (Chrome+Linux = 3+5=8)
    assert testcases[0]["assignments"]["Browser"] == "Chrome"
    assert testcases[0]["assignments"]["OS"] == "Linux"
    assert testcases[0]["risk_coverage"] == 8.0


def test_fehlerwert_testfall_landet_am_ende_trotz_hohem_risiko(clean_db):
    """REQ-3034 + REQ-3018/BUG-5: Fehlerwert-Vorrang schlaegt reine Risiko-Sortierung."""
    resp = client.post("/api/projects", json={"name": "RiskErrorProject"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat1_id = resp.json()["id"]
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Chrome", "risk_weight": 5})
    client.post(f"/api/categories/{cat1_id}/values", json={"value": "Firefox", "risk_weight": 1})

    resp = client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat2_id = resp.json()["id"]
    client.post(f"/api/categories/{cat2_id}/values", json={"value": "Windows", "risk_weight": 1})
    # BrokenOS ist ein Fehlerwert (allowed=False) mit hohem risk_weight
    resp = client.post(
        f"/api/categories/{cat2_id}/values",
        json={"value": "BrokenOS", "risk_weight": 20},
    )
    broken_value_id = resp.json()["id"]
    resp = client.patch(f"/api/values/{broken_value_id}/properties", json={"allowed": False})
    assert resp.status_code == 200

    resp = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    resp = client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    testcases = resp.json()["testcases"]

    # strategy="all" erzeugt hier 4 Kombinationen: 2x Windows (fehlerfrei),
    # 2x BrokenOS (Fehlerwert, jeweils Chrome+BrokenOS bzw. Firefox+BrokenOS).
    # Trotz hohem Risiko (Chrome+BrokenOS = 5+20 = 25) muessen BEIDE
    # BrokenOS-Testfaelle ans Ende sortiert werden.
    error_flags = [tc["_has_error_value"] for tc in testcases]
    error_count = sum(error_flags)
    assert error_count == 2
    # Alle Fehlerwert-Testfaelle stehen am Ende (kein Fehlerwert vor einem Nicht-Fehlerwert).
    assert error_flags == sorted(error_flags)
    non_error = testcases[:-error_count]
    error = testcases[-error_count:]
    assert all(tc["_has_error_value"] is False for tc in non_error)
    assert all(tc["_has_error_value"] is True for tc in error)
    assert all(tc["assignments"]["OS"] == "BrokenOS" for tc in error)

    # Fehlerfreie Testfaelle bleiben absteigend nach Risiko sortiert (Chrome vor Firefox).
    risk_values = [tc["risk_coverage"] for tc in non_error]
    assert risk_values == sorted(risk_values, reverse=True)
