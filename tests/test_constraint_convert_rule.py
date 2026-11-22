"""
REQ-6001 AK-9: Tests fuer Rules → Constraints umwandeln.
"""
import pytest
from fastapi.testclient import TestClient


class TestRuleToConstraintConversion:
    """AK-9: Bestehende Regeln in Constraints umwandeln."""

    def test_convert_exclude_to_forbid(self, auth_client):
        """exclude-Regel → forbid-Constraint."""
        r = auth_client.post("/api/projects", json={"name": "Convert-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        cat1 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Farbe", "order_index": 0}).json()
        cat2 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Groesse", "order_index": 1}).json()
        v_rot = auth_client.post(f"/api/categories/{cat1['id']}/values",
                                 json={"value": "Rot"}).json()
        v_klein = auth_client.post(f"/api/categories/{cat2['id']}/values",
                                   json={"value": "Klein"}).json()

        # exclude-Regel erstellen (mit IDs)
        rule = auth_client.post(f"/api/projects/{pid}/rules", json={
            "type": "exclude",
            "if_category_id": cat1["id"],
            "if_value": "Rot",
            "then_category_id": cat2["id"],
            "then_value": "Klein",
        }).json()

        # Konvertieren
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints/convert-from-rule/{rule['id']}")
        assert resp.status_code == 201
        data = resp.json()
        assert data["kind"] == "forbid"
        # expression ist jetzt direkt die condition (flaches Format)
        assert data["expression"]["op"] == "eq"
        assert data["expression"]["category_id"] == cat1["id"]
        assert data.get("consequence") is None  # forbid hat keine consequence

    def test_convert_dependency_to_implies(self, auth_client):
        """dependency-Regel → implies-Constraint."""
        r = auth_client.post("/api/projects", json={"name": "Dep-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        cat1 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Transport", "order_index": 0}).json()
        cat2 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Versand", "order_index": 1}).json()
        auth_client.post(f"/api/categories/{cat1['id']}/values", json={"value": "Luftfracht"})
        auth_client.post(f"/api/categories/{cat2['id']}/values", json={"value": "Express"})

        rule = auth_client.post(f"/api/projects/{pid}/rules", json={
            "type": "dependency",
            "if_category_id": cat1["id"],
            "if_value": "Luftfracht",
            "then_category_id": cat2["id"],
            "then_value": "Express",
        }).json()

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints/convert-from-rule/{rule['id']}")
        assert resp.status_code == 201
        data = resp.json()
        assert data["kind"] == "implies"
        # expression ist die condition, consequence ist separates Feld
        assert data["expression"]["op"] == "eq"
        assert data["consequence"]["op"] == "eq"
        assert data["consequence"]["category_id"] == cat2["id"]

    def test_convert_combine_to_implies(self, auth_client):
        """combine-Regel → implies-Constraint mit IN."""
        r = auth_client.post("/api/projects", json={"name": "Combine-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        cat1 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Land", "order_index": 0}).json()
        cat2 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Steuersatz", "order_index": 1}).json()
        auth_client.post(f"/api/categories/{cat1['id']}/values", json={"value": "EU"})
        auth_client.post(f"/api/categories/{cat2['id']}/values", json={"value": "19%"})
        auth_client.post(f"/api/categories/{cat2['id']}/values", json={"value": "7%"})

        rule = auth_client.post(f"/api/projects/{pid}/rules", json={
            "type": "combine",
            "if_category_id": cat1["id"],
            "if_value": "EU",
            "then_category_id": cat2["id"],
            "then_values": ["19%", "7%"],
        }).json()

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints/convert-from-rule/{rule['id']}")
        assert resp.status_code == 201
        data = resp.json()
        assert data["kind"] == "implies"
        # consequence ist separates Feld mit IN-Operator
        assert data["consequence"]["op"] == "in"
        assert len(data["consequence"]["value_ids"]) == 2

    def test_convert_nonexistent_rule_returns_404(self, auth_client):
        """Nicht-existentes Regel-ID → 404."""
        r = auth_client.post("/api/projects", json={"name": "404-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints/convert-from-rule/99999")
        assert resp.status_code == 404