"""
REQ-6001: Integrationstest – Constraints wirken in der Generierung.

Testet:
1. Constraint erstellen (forbid)
2. Generierung ausfuehren
3. Pruefen ob verbotener Wert gefiltert wird
"""
import pytest
from fastapi.testclient import TestClient


class TestConstraintGenerationIntegration:
    """Constraints wirken bei Generierung."""

    def test_forbid_constraint_filters_value(self, auth_client):
        """forbid-Constraint verhindert dass verbotener Wert in Testfaellen erscheint."""
        # Projekt erstellen
        r = auth_client.post("/api/projects", json={"name": "Constraint-Gen-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        # Kategorien + Werte
        cat1 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Farbe", "order_index": 0}).json()
        cat2 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Groesse", "order_index": 1}).json()

        v_rot = auth_client.post(f"/api/categories/{cat1['id']}/values",
                                 json={"value": "Rot"}).json()
        v_blau = auth_client.post(f"/api/categories/{cat1['id']}/values",
                                  json={"value": "Blau"}).json()
        v_klein = auth_client.post(f"/api/categories/{cat2['id']}/values",
                                   json={"value": "Klein"}).json()
        v_gross = auth_client.post(f"/api/categories/{cat2['id']}/values",
                                   json={"value": "Groß"}).json()

        # Constraint: NICHT Farbe=Rot
        auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeinRot",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cat1["id"], "value_id": v_rot["id"]},
        })

        # Generierung
        r = auth_client.post(f"/api/projects/{pid}/generate",
                             json={"strategy": "pairwise", "limit": 20})
        assert r.status_code == 200
        gen = r.json()

        # Pruefen: "Rot" darf in keinem Testfall vorkommen
        for tc in gen.get("testcases", []):
            tc_str = str(tc)
            assert "Rot" not in tc_str, f"Verbotener Wert 'Rot' in Testfall: {tc}"

        print(f"✅ {len(gen.get('testcases', []))} Testfaelle generiert, 'Rot' korrekt gefiltert")

    def test_implies_constraint_enforces_consequence(self, auth_client):
        """implies-Constraint erzwingt Folge wenn Bedingung zutrifft."""
        # Projekt erstellen
        r = auth_client.post("/api/projects", json={"name": "Implies-Gen-Test"})
        assert r.status_code in (200, 201)
        pid = r.json()["id"]

        # Kategorien + Werte
        cat1 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Transport", "order_index": 0}).json()
        cat2 = auth_client.post(f"/api/projects/{pid}/categories",
                                json={"name": "Versand", "order_index": 1}).json()

        v_luft = auth_client.post(f"/api/categories/{cat1['id']}/values",
                                  json={"value": "Luftfracht"}).json()
        v_see = auth_client.post(f"/api/categories/{cat1['id']}/values",
                                 json={"value": "See"}).json()
        v_express = auth_client.post(f"/api/categories/{cat2['id']}/values",
                                     json={"value": "Express"}).json()
        v_standard = auth_client.post(f"/api/categories/{cat2['id']}/values",
                                      json={"value": "Standard"}).json()

        # Constraint: WENN Transport=Luftfracht DANN Versand=Express
        auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "LuftfrachtDannExpress",
            "kind": "implies",
            "expression": {"op": "eq", "category_id": cat1["id"], "value_id": v_luft["id"]},
            "consequence": {"op": "eq", "category_id": cat2["id"], "value_id": v_express["id"]},
        })

        # Generierung
        r = auth_client.post(f"/api/projects/{pid}/generate",
                             json={"strategy": "pairwise", "limit": 20})
        assert r.status_code == 200
        gen = r.json()

        # Pruefen: Wenn Transport=Luftfracht, dann muss Versand=Express sein
        for tc in gen.get("testcases", []):
            tc_str = str(tc)
            if "Luftfracht" in tc_str:
                assert "Express" in tc_str, f"Implikation verletzt: Luftfracht ohne Express in {tc}"

        print(f"✅ {len(gen.get('testcases', []))} Testfaelle, Implikation korrekt enforced")