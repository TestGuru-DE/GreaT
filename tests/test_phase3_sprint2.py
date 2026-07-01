"""
tests/test_phase3_sprint2.py – TDD RED-Phase für Phase 3, Sprint 2
REQ-3003: Regelanlage via REST-API (POST/DELETE /api/projects/{pid}/rules)
REQ-3004: Regelwiderspruch-Erkennung
REQ-3005: Mit-Regeln generieren (apply_rules-Flag)
"""
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def create_project_with_categories():
    """Erstellt Testprojekt mit zwei Kategorien und je zwei Werten."""
    r = client.post("/api/projects", json={"name": f"Regel-Test-{uuid.uuid4().hex[:8]}"})
    pid = r.json()["id"]

    r1 = client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"})
    cid1 = r1.json()["id"]
    r2 = client.post(f"/api/projects/{pid}/categories", json={"name": "OS"})
    cid2 = r2.json()["id"]

    client.post(f"/api/categories/{cid1}/values", json={"value": "Chrome"})
    client.post(f"/api/categories/{cid1}/values", json={"value": "Firefox"})
    client.post(f"/api/categories/{cid2}/values", json={"value": "Windows"})
    client.post(f"/api/categories/{cid2}/values", json={"value": "Linux"})

    return pid, cid1, cid2


# ---------------------------------------------------------------------------
# REQ-3003: Regelanlage via POST
# ---------------------------------------------------------------------------

class TestRuleCreate:
    def test_create_dependency_rule(self):
        """POST /api/projects/{pid}/rules mit type=dependency."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"] > 0
        assert body["type"] == "dependency"
        assert body["if_value"] == "Chrome"

    def test_create_exclude_rule(self):
        """POST /api/projects/{pid}/rules mit type=exclude."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "exclude",
            "if_category_id": cid1,
            "if_value": "Firefox",
            "then_category_id": cid2,
            "then_value": "Linux",
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["type"] == "exclude"

    def test_create_combine_rule(self):
        """POST /api/projects/{pid}/rules mit type=combine."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "combine",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_values": ["Windows"],
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["type"] == "combine"
        assert "Windows" in json.loads(body["then_values_json"])

    def test_create_rule_invalid_type(self):
        """Ungültiger Regeltyp → 422."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "ungueltig",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        assert r.status_code == 422

    def test_create_rule_wrong_project_category(self):
        """Kategorie aus anderem Projekt → 400."""
        pid, cid1, _ = create_project_with_categories()
        pid2, cid_other, _ = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid_other,
            "then_value": "Windows",
        })
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# REQ-3003: Regelläschung via DELETE
# ---------------------------------------------------------------------------

class TestRuleDelete:
    def test_delete_rule(self):
        """DELETE /api/projects/{pid}/rules/{rid}."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        rid = r.json()["id"]

        r2 = client.delete(f"/api/projects/{pid}/rules/{rid}")
        assert r2.status_code == 200

        rules = client.get(f"/api/projects/{pid}/rules").json()
        assert not any(r["id"] == rid for r in rules)

    def test_delete_rule_not_found(self):
        """Nicht vorhandene Regel löschen → 404."""
        pid, _, _ = create_project_with_categories()
        r = client.delete(f"/api/projects/{pid}/rules/99999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# REQ-3004: Regelwiderspruch-Erkennung
# ---------------------------------------------------------------------------

class TestRuleConflict:
    def test_conflict_exclude_vs_dependency(self):
        """exclude(A=X,B=Y) + dependency(A=X→B=Y) → Warnung."""
        pid, cid1, cid2 = create_project_with_categories()
        client.post(f"/api/projects/{pid}/rules", json={
            "type": "exclude",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        assert r.status_code == 201
        body = r.json()
        assert "conflict_with" in body
        assert len(body["conflict_with"]) > 0

    def test_conflict_dependency_same_target(self):
        """dependency(A=X→B=Y1) + dependency(A=X→B=Y2) → Warnung."""
        pid, cid1, cid2 = create_project_with_categories()
        client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Linux",
        })
        assert r.status_code == 201
        body = r.json()
        assert "conflict_with" in body
        assert len(body["conflict_with"]) > 0

    def test_no_conflict(self):
        """Keine widersprechenden Regeln → conflict_with leer."""
        pid, cid1, cid2 = create_project_with_categories()
        r = client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Windows",
        })
        assert r.status_code == 201
        body = r.json()
        assert body.get("conflict_with", []) == []


# ---------------------------------------------------------------------------
# REQ-3005: apply_rules beim Generieren
# ---------------------------------------------------------------------------

class TestGenerateWithRules:
    def test_generate_with_rules_apply(self):
        """apply_rules=true → verbotene Kombination wird gefiltert."""
        pid, cid1, cid2 = create_project_with_categories()
        # Chrome + Linux verboten
        client.post(f"/api/projects/{pid}/rules", json={
            "type": "exclude",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Linux",
        })
        r = client.post(f"/api/projects/{pid}/generate", json={
            "strategy": "all",
            "apply_rules": True,
        })
        assert r.status_code == 200
        gen_id = r.json()["generation_id"]
        cases_r = client.get(f"/api/generations/{gen_id}/testcases")
        assert cases_r.status_code == 200
        cases = cases_r.json()
        for tc in cases:
            vals = tc["assignments"]
            assert not (vals.get("Browser") == "Chrome" and vals.get("OS") == "Linux"), \
                "Verbotene Kombination Chrome+Linux darf nicht vorkommen"

    def test_generate_without_rules(self):
        """apply_rules=false (default) → alle Kombinationen vorhanden."""
        pid, cid1, cid2 = create_project_with_categories()
        client.post(f"/api/projects/{pid}/rules", json={
            "type": "exclude",
            "if_category_id": cid1,
            "if_value": "Chrome",
            "then_category_id": cid2,
            "then_value": "Linux",
        })
        r = client.post(f"/api/projects/{pid}/generate", json={
            "strategy": "all",
            "apply_rules": False,
        })
        assert r.status_code == 200
        gen_id = r.json()["generation_id"]
        cases_r = client.get(f"/api/generations/{gen_id}/testcases")
        cases = cases_r.json()
        found_forbidden = any(
            tc["assignments"].get("Browser") == "Chrome"
            and tc["assignments"].get("OS") == "Linux"
            for tc in cases
        )
        assert found_forbidden, "Ohne Regeln soll Chrome+Linux vorkommen"