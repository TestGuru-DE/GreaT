"""
REQ-6008: Abdeckungsanzeige als Matrix/Heatmap — API-Integration-Tests

TEST-ID: TEST-REQ-6008-API-001 bis 012

Endpoint: GET /api/generations/{gid}/coverage
Optional: ?t=1|2|3 fuer 3-wise
"""
import pytest
import json
from app.main import app
from app.database import SessionLocal, engine, Base


@pytest.fixture(scope="function")
def clean_db():
    """Stellt sicher, dass das Test-DB-Schema vorhanden ist."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def project_with_2x2(auth_client, clean_db):
    """Projekt mit 2x2 Modell (A: a1,a2 / B: b1,b2), pairwise-Generierung."""
    resp = auth_client.post("/api/projects", json={"name": "CoverageTest2x2"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # Kategorie A
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "A"})
    cat_a_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_a_id}/values", json={"value": "a1"})
    auth_client.post(f"/api/categories/{cat_a_id}/values", json={"value": "a2"})

    # Kategorie B
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "B"})
    cat_b_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_b_id}/values", json={"value": "b1"})
    auth_client.post(f"/api/categories/{cat_b_id}/values", json={"value": "b2"})

    # Pairwise-Generierung
    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "pairwise"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    return pid, gen_id


@pytest.fixture
def project_with_result_category(auth_client, clean_db):
    """Projekt mit Ergebnis-Kategorie (is_result=True)."""
    resp = auth_client.post("/api/projects", json={"name": "CoverageResultTest"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # Browser
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cat_browser_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_browser_id}/values", json={"value": "Chrome"})
    auth_client.post(f"/api/categories/{cat_browser_id}/values", json={"value": "Firefox"})

    # OS
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cat_os_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_os_id}/values", json={"value": "Windows"})
    auth_client.post(f"/api/categories/{cat_os_id}/values", json={"value": "Linux"})

    # Result (is_result=True)
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Result", "is_result": True})
    cat_result_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_result_id}/values", json={"value": "Pass"})
    auth_client.post(f"/api/categories/{cat_result_id}/values", json={"value": "Fail"})

    # All-Combinations
    resp = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    return pid, gen_id


@pytest.fixture
def project_with_forbidden_rule(auth_client, clean_db):
    """Projekt mit Forbidden-Regel: (A=a2, B=b2) verboten."""
    resp = auth_client.post("/api/projects", json={"name": "CoverageRuleTest"})
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # Kategorien
    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "A"})
    cat_a_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_a_id}/values", json={"value": "a1"})
    auth_client.post(f"/api/categories/{cat_a_id}/values", json={"value": "a2"})

    resp = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "B"})
    cat_b_id = resp.json()["id"]
    auth_client.post(f"/api/categories/{cat_b_id}/values", json={"value": "b1"})
    auth_client.post(f"/api/categories/{cat_b_id}/values", json={"value": "b2"})

    # Forbidden-Regel: A=a2, B=b2
    resp = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cat_a_id,
        "if_value": "a2",
        "then_category_id": cat_b_id,
        "then_value": "b2",
    })
    assert resp.status_code in (200, 201)

    # Pairwise mit Regeln
    resp = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "pairwise",
        "apply_rules": True,
    })
    assert resp.status_code == 200
    gen_id = resp.json()["generation_id"]

    return pid, gen_id


# ============================================================================
# TEST-REQ-6008-API-001 bis 004: Grundlegende Endpoint-Funktionalitaet
# ============================================================================

class TestCoverageAPI:
    """GET /api/generations/{gid}/coverage"""

    def test_coverage_endpoint_returns_200(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-001: Endpoint existiert und antwortet mit 200."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        assert resp.status_code == 200

        data = resp.json()
        assert "coverage_2wise" in data
        assert "generation_id" in data
        assert data["generation_id"] == gen_id

    def test_coverage_endpoint_404(self, auth_client):
        """TEST-REQ-6008-API-002: Nicht-existente Generation -> 404."""
        resp = auth_client.get("/api/generations/99999/coverage")
        assert resp.status_code == 404

    def test_coverage_2wise_values_correct(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-003: 2x2 pairwise -> 100% 2-wise."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        c2 = data["coverage_2wise"]
        assert c2["covered"] == 4
        assert c2["possible"] == 4
        assert c2["percentage"] == 100.0
        assert c2["excluded_by_rules"] == 0

    def test_coverage_1wise_in_response(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-004: 1-wise auch im Standard-Response."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        c1 = data["coverage_1wise"]
        assert c1["covered"] == 4  # a1, a2, b1, b2
        assert c1["possible"] == 4
        assert c1["percentage"] == 100.0


# ============================================================================
# TEST-REQ-6008-API-005 bis 008: Regeln und Constraints
# ============================================================================

class TestCoverageAPIWithRules:
    """Coverage mit Forbidden-Regeln."""

    def test_coverage_with_forbidden_rule(self, auth_client, project_with_forbidden_rule):
        """TEST-REQ-6008-API-005: excluded_by_rules > 0 bei Forbidden-Regel."""
        pid, gen_id = project_with_forbidden_rule

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        c2 = data["coverage_2wise"]
        assert c2["excluded_by_rules"] >= 1
        assert c2["possible"] < 4  # Mindestens 1 Paar ausgeschlossen
        assert c2["percentage"] == 100.0  # Alle gueltigen Paare abgedeckt

    def test_coverage_result_category_excluded(self, auth_client, project_with_result_category):
        """TEST-REQ-6008-API-006: Result-Kategorie nicht in Coverage."""
        pid, gen_id = project_with_result_category

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        c2 = data["coverage_2wise"]
        # Nur Browser-OS-Paare: 2*2 = 4
        assert c2["covered"] == 4
        assert c2["possible"] == 4
        assert c2["percentage"] == 100.0


# ============================================================================
# TEST-REQ-6008-API-009 bis 010: Caching
# ============================================================================

class TestCoverageAPICaching:
    """Coverage wird nach erstem Aufruf gecached."""

    def test_coverage_uncached_first_call(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-009: Erster Aufruf cached=false."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        assert data.get("cached") is False

    def test_coverage_cached_second_call(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-010: Zweiter Aufruf cached=true."""
        pid, gen_id = project_with_2x2

        # Erster Aufruf
        auth_client.get(f"/api/generations/{gen_id}/coverage")

        # Zweiter Aufruf
        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        assert data.get("cached") is True


# ============================================================================
# TEST-REQ-6008-API-011 bis 012: Heatmap & Uncovered Tuples
# ============================================================================

class TestCoverageAPIHeatmap:
    """Heatmap- und Uncovered-Tuples-Daten im API-Response."""

    def test_heatmap_pairs_in_response(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-011: heatmap.pairs hat Eintrag fuer A-B."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        assert "heatmap" in data
        pairs = data["heatmap"].get("pairs", [])
        assert len(pairs) >= 1

        ab_pair = [p for p in pairs if p["cat_a"] == "A" and p["cat_b"] == "B"]
        assert len(ab_pair) == 1
        assert ab_pair[0]["coverage_pct"] == 100.0

    def test_uncovered_tuples_in_response(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-012: uncovered_tuples_2wise bei vollem Coverage leer."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage")
        data = resp.json()

        assert "uncovered_tuples_2wise" in data
        assert data["uncovered_tuples_2wise"] == []

    def test_coverage_3wise_on_request(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-013: ?t=3 liefert coverage_3wise."""
        pid, gen_id = project_with_2x2

        resp = auth_client.get(f"/api/generations/{gen_id}/coverage?t=3")
        data = resp.json()

        assert "coverage_3wise" in data
        # 2 Kategorien -> 3-wise = kartesisch = 4
        c3 = data["coverage_3wise"]
        assert c3["covered"] == 4
        assert c3["possible"] == 4

    def test_generation_list_includes_2wise_pct(self, auth_client, project_with_2x2):
        """TEST-REQ-6008-API-014: Generierungsuebersicht hat 2-wise-%-Spalte."""
        pid, gen_id = project_with_2x2

        # Erst Coverage berechnen (triggert caching)
        auth_client.get(f"/api/generations/{gen_id}/coverage")

        # Dann Generierungsliste abfragen
        resp = auth_client.get(f"/api/projects/{pid}/generations")
        data = resp.json()

        assert isinstance(data, list)  # BUG R-03: Liste statt Objekt
        gens = data
        target = [g for g in gens if g["id"] == gen_id]
        assert len(target) == 1
        assert "coverage_2wise_pct" in target[0]
        assert target[0]["coverage_2wise_pct"] == 100.0