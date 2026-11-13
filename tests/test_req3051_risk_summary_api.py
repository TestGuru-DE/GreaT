"""
REQ-3051: Prozentualer Gesamt-Risikoabdeckungswert einer Generierung.

Ergaenzt test_risk_summary.py (Unit-Tests der reinen Berechnungsfunktion)
um Integrationstests auf API-Ebene:
- Das GET /generations/{gid}/testcases-Response enthaelt "risk_summary" mit
  den in schemas.RiskSummary definierten Feldern.
- Der Endpunkt nutzt response_model=schemas.TestcasesResponse (bestehendes
  API-Muster wie bei allen anderen Endpunkten), damit das OpenAPI-Schema
  den Vertrag fuer den Gesamtprozentsatz dokumentiert.
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


def _setup_generation(auth_client, strategy: str = "all") -> int:
    resp = auth_client.post("/api/projects", json={"name": "RiskSummaryProject"})
    pid = resp.json()["id"]

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat1_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat1_id}/values", json={"value": "Chrome", "risk_weight": 5})
    auth_client.post(f"/api/categories/{cat1_id}/values", json={"value": "Firefox", "risk_weight": 1})

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat2_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat2_id}/values", json={"value": "Windows", "risk_weight": 2})
    auth_client.post(f"/api/categories/{cat2_id}/values", json={"value": "Linux", "risk_weight": 1})

    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": strategy})
    assert resp.status_code == 200
    return resp.json()["generation_id"]


def test_risk_summary_present_in_testcases_response(auth_client, clean_db):
    """REQ-3051: Response von GET .../testcases enthaelt risk_summary mit Gesamtprozentsatz."""
    gen_id = _setup_generation(auth_client, strategy="all")

    resp = auth_client.get(f"/api/generations/{gen_id}/testcases")
    assert resp.status_code == 200
    data = resp.json()

    assert "risk_summary" in data
    summary = data["risk_summary"]
    for key in ("total_risk", "max_possible_risk", "risk_coverage_percent", "testcase_count"):
        assert key in summary, f"risk_summary fehlt Feld {key!r}"

    # All-Combinations ("all") deckt 100% des theoretischen Maximums ab.
    assert summary["risk_coverage_percent"] == 100.0
    assert summary["testcase_count"] == len(data["testcases"])


def test_risk_summary_percent_matches_manual_calculation(auth_client, clean_db):
    """REQ-3051: Prozentsatz = Summe risk_coverage / All-Combinations-Maximum * 100."""
    gen_id = _setup_generation(auth_client, strategy="each")

    resp = auth_client.get(f"/api/generations/{gen_id}/testcases")
    data = resp.json()
    summary = data["risk_summary"]
    testcases = data["testcases"]

    total_risk = sum(tc["risk_coverage"] for tc in testcases)
    assert summary["total_risk"] == total_risk

    expected_percent = round(total_risk / summary["max_possible_risk"] * 100, 1)
    assert summary["risk_coverage_percent"] == expected_percent


def test_testcases_endpoint_documents_risk_summary_in_openapi(auth_client, clean_db):
    """REQ-3051: Endpunkt nutzt response_model, damit RiskSummary im OpenAPI-Schema
    dokumentiert ist (bestehendes Muster: alle anderen Endpunkte deklarieren response_model)."""
    schema = app.openapi()
    path_item = schema["paths"]["/api/generations/{gid}/testcases"]["get"]
    response_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]

    # Ohne response_model liefert FastAPI hier ein leeres Schema ({}).
    assert response_schema != {}, "response_model fehlt am /generations/{gid}/testcases-Endpunkt"

    components = schema.get("components", {}).get("schemas", {})
    assert "RiskSummary" in components, "RiskSummary-Schema fehlt im OpenAPI-Dokument"
    risk_summary_props = set(components["RiskSummary"]["properties"].keys())
    assert risk_summary_props == {
        "total_risk",
        "max_possible_risk",
        "risk_coverage_percent",
        "testcase_count",
    }