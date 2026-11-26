"""
REQ-6001: API-Tests fuer logische Constraints.

Testet alle CRUD-Endpunkte + Validate von api_constraints.py:
- GET list, POST create, GET single, PUT update, DELETE delete, POST validate
- forbid und implies Constraints
- Fehlerfaelle: 404, 400 (ungueltiger AST), Auth
"""
import pytest
import json

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper: Testprojekt mit Kategorien+Werten erstellen
# ---------------------------------------------------------------------------

def _create_test_project(client: TestClient, name: str = "TestProjekt") -> dict:
    """Erstellt ein Testprojekt mit 2 Kategorien und Werten.

    Gibt dict zurueck mit project_id und categories-Info.
    POST /api/projects gibt 200 (nicht 201).
    """
    # Projekt erstellen
    resp = client.post("/api/projects", json={"name": name})
    assert resp.status_code in (200, 201), f"Projekt erstellen fehlgeschlagen: {resp.text}"
    project_id = resp.json()["id"]

    # Kategorien erstellen
    cat1 = client.post(f"/api/projects/{project_id}/categories",
                       json={"name": "Zahlart", "order_index": 0}).json()
    cat2 = client.post(f"/api/projects/{project_id}/categories",
                       json={"name": "Versand", "order_index": 1}).json()

    # Werte fuer cat1
    v1 = client.post(f"/api/categories/{cat1['id']}/values",
                     json={"value": "Rechnung"}).json()
    v2 = client.post(f"/api/categories/{cat1['id']}/values",
                     json={"value": "Lieferschein"}).json()

    # Werte fuer cat2
    v3 = client.post(f"/api/categories/{cat2['id']}/values",
                     json={"value": "Standard"}).json()
    v4 = client.post(f"/api/categories/{cat2['id']}/values",
                     json={"value": "Express"}).json()

    return {
        "project_id": project_id,
        "categories": {
            "Zahlart": {"id": cat1["id"], "values": {"Rechnung": v1["id"], "Lieferschein": v2["id"]}},
            "Versand": {"id": cat2["id"], "values": {"Standard": v3["id"], "Express": v4["id"]}},
        }
    }


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{pid}/constraints/ – Liste
# ---------------------------------------------------------------------------

class TestConstraintList:
    """GET /constraints – Constraints listen."""

    def test_list_empty(self, auth_client):
        """Leere Liste bei neuem Projekt."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.get(f"/api/v1/projects/{ctx['project_id']}/constraints")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, auth_client):
        """Liste zeigt erstellte Constraints."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        # Constraint erstellen
        auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "TestForbid",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })

        resp = auth_client.get(f"/api/v1/projects/{pid}/constraints")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "TestForbid"
        assert data[0]["kind"] == "forbid"

    def test_list_project_not_found(self, auth_client):
        """404 bei nicht-existentem Projekt."""
        resp = auth_client.get("/api/v1/projects/99999/constraints")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{pid}/constraints/ – Erstellen
# ---------------------------------------------------------------------------

class TestConstraintCreate:
    """POST /constraints – Constraint erstellen."""

    def test_create_forbid(self, auth_client):
        """forbid-Constraint erstellen."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeineRechnung",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "KeineRechnung"
        assert data["kind"] == "forbid"
        assert data["is_valid"] is True
        assert "expression" in data

    def test_create_implies(self, auth_client):
        """implies-Constraint erstellen mit consequence."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        c1_id = ctx["categories"]["Zahlart"]["id"]
        v1_id = ctx["categories"]["Zahlart"]["values"]["Rechnung"]
        c2_id = ctx["categories"]["Versand"]["id"]
        v2_id = ctx["categories"]["Versand"]["values"]["Standard"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "RechnungDannStandard",
            "kind": "implies",
            "expression": {"op": "eq", "category_id": c1_id, "value_id": v1_id},
            "consequence": {"op": "eq", "category_id": c2_id, "value_id": v2_id},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "RechnungDannStandard"
        assert data["kind"] == "implies"

    def test_create_implies_without_consequence(self, auth_client):
        """implies ohne consequence -> 400."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "BadImplies",
            "kind": "implies",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        assert resp.status_code == 400

    def test_create_forbid_with_consequence(self, auth_client):
        """forbid mit consequence -> 400."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "BadForbid",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
            "consequence": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        assert resp.status_code == 400

    def test_create_invalid_ast(self, auth_client):
        """Ungueltiger AST -> 400."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "BadAST",
            "kind": "forbid",
            "expression": {"op": "invalid_op", "category_id": 1, "value_id": 2},
        })
        assert resp.status_code == 400

    def test_create_project_not_found(self, auth_client):
        """404 bei nicht-existentem Projekt."""
        resp = auth_client.post("/api/v1/projects/99999/constraints", json={
            "name": "Test",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": 1, "value_id": 2},
        })
        assert resp.status_code == 404

    def test_create_too_many_leaves(self, auth_client):
        """Mehr als 20 atomare Vergleiche -> 400."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        # 21 eq-Knoten in einem OR
        args = [{"op": "eq", "category_id": cid, "value_id": vid} for _ in range(21)]
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "TooMany",
            "kind": "forbid",
            "expression": {"op": "or", "args": args},
        })
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/projects/{pid}/constraints/{cid} – Einzelnes lesen
# ---------------------------------------------------------------------------

class TestConstraintGet:
    """GET /constraints/{id} – Einzelnes Constraint lesen."""

    def test_get_existing(self, auth_client):
        """Existierendes Constraint lesen."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "TestGet",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        constraint_id = create_resp.json()["id"]

        resp = auth_client.get(f"/api/v1/projects/{pid}/constraints/{constraint_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "TestGet"
        assert data["id"] == constraint_id

    def test_get_not_found(self, auth_client):
        """404 bei nicht-existentem Constraint."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.get(f"/api/v1/projects/{ctx['project_id']}/constraints/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/projects/{pid}/constraints/{cid} – Aktualisieren
# ---------------------------------------------------------------------------

class TestConstraintUpdate:
    """PUT /constraints/{id} – Constraint aktualisieren."""

    def test_update_name(self, auth_client):
        """Nur Namen aendern."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "OldName",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        constraint_id = create_resp.json()["id"]

        resp = auth_client.put(f"/api/v1/projects/{pid}/constraints/{constraint_id}", json={
            "name": "NewName",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewName"

    def test_update_expression(self, auth_client):
        """Expression aendern."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Lieferschein"]

        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "TestUpdate",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        constraint_id = create_resp.json()["id"]

        # Auf ne aendern
        new_vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]
        resp = auth_client.put(f"/api/v1/projects/{pid}/constraints/{constraint_id}", json={
            "expression": {"op": "ne", "category_id": cid, "value_id": new_vid},
        })
        assert resp.status_code == 200

    def test_update_implies_add_consequence(self, auth_client):
        """implies: consequence hinzufuegen."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        c1_id = ctx["categories"]["Zahlart"]["id"]
        v1_id = ctx["categories"]["Zahlart"]["values"]["Rechnung"]
        c2_id = ctx["categories"]["Versand"]["id"]
        v2_id = ctx["categories"]["Versand"]["values"]["Standard"]

        # Zuerst implies ohne consequence (sollte 400 sein)
        # Stattdessen: forbid zu implies aendern mit consequence
        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "ToImplies",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": c1_id, "value_id": v1_id},
        })
        constraint_id = create_resp.json()["id"]

        # Zu implies mit consequence aendern
        resp = auth_client.put(f"/api/v1/projects/{pid}/constraints/{constraint_id}", json={
            "kind": "implies",
            "consequence": {"op": "eq", "category_id": c2_id, "value_id": v2_id},
        })
        assert resp.status_code == 200
        assert resp.json()["kind"] == "implies"

    def test_update_not_found(self, auth_client):
        """404 bei nicht-existentem Constraint."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.put(f"/api/v1/projects/{ctx['project_id']}/constraints/99999", json={
            "name": "Test",
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/projects/{pid}/constraints/{cid} – Loeschen
# ---------------------------------------------------------------------------

class TestConstraintDelete:
    """DELETE /constraints/{id} – Constraint loeschen."""

    def test_delete_existing(self, auth_client):
        """Existierendes Constraint loeschen."""
        ctx = _create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Zahlart"]["id"]
        vid = ctx["categories"]["Zahlart"]["values"]["Rechnung"]

        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "ToDelete",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vid},
        })
        constraint_id = create_resp.json()["id"]

        resp = auth_client.delete(f"/api/v1/projects/{pid}/constraints/{constraint_id}")
        assert resp.status_code == 204

        # Muss nicht mehr existieren
        get_resp = auth_client.get(f"/api/v1/projects/{pid}/constraints/{constraint_id}")
        assert get_resp.status_code == 404

    def test_delete_not_found(self, auth_client):
        """404 bei nicht-existentem Constraint."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.delete(f"/api/v1/projects/{ctx['project_id']}/constraints/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/projects/{pid}/constraints/validate – Validierung
# ---------------------------------------------------------------------------

class TestConstraintValidate:
    """POST /constraints/validate – AST validieren ohne zu speichern."""

    def test_validate_valid_forbid(self, auth_client):
        """Gueltiges forbid-AST validieren."""
        ctx = _create_test_project(auth_client)
        zahlart = ctx["categories"]["Zahlart"]
        resp = auth_client.post(f"/api/v1/projects/{ctx['project_id']}/constraints/validate", json={
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": zahlart["id"], "value_id": zahlart["values"]["Rechnung"]},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["errors"] == []

    def test_validate_valid_implies(self, auth_client):
        """Gueltiges implies-AST validieren."""
        ctx = _create_test_project(auth_client)
        zahlart = ctx["categories"]["Zahlart"]
        versand = ctx["categories"]["Versand"]
        resp = auth_client.post(f"/api/v1/projects/{ctx['project_id']}/constraints/validate", json={
            "kind": "implies",
            "expression": {"op": "eq", "category_id": zahlart["id"], "value_id": zahlart["values"]["Rechnung"]},
            "consequence": {"op": "ne", "category_id": versand["id"], "value_id": versand["values"]["Express"]},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True

    def test_validate_invalid_ast(self, auth_client):
        """Ungueltiges AST -> is_valid=False mit Errors."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.post(f"/api/v1/projects/{ctx['project_id']}/constraints/validate", json={
            "kind": "forbid",
            "expression": {"op": "invalid_op", "category_id": 1, "value_id": 2},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_leaf_count_and_depth(self, auth_client):
        """leaf_count und depth werden zurueckgegeben."""
        ctx = _create_test_project(auth_client)
        resp = auth_client.post(f"/api/v1/projects/{ctx['project_id']}/constraints/validate", json={
            "kind": "forbid",
            "expression": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {"op": "eq", "category_id": 3, "value_id": 4},
                ],
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["leaf_count"] == 2
        assert data["depth"] >= 1

    def test_validate_project_not_found(self, auth_client):
        """404 bei nicht-existentem Projekt."""
        resp = auth_client.post("/api/v1/projects/99999/constraints/validate", json={
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": 1, "value_id": 2},
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth-Tests
# ---------------------------------------------------------------------------

class TestConstraintAuth:
    """Auth-Checks fuer Constraint-Endpunkte."""

    def test_create_requires_auth(self, client, auth_client):
        """POST ohne Auth -> 401/403."""
        # Erst ein Projekt mit auth_client erstellen
        ctx = _create_test_project(auth_client)

        # Dann mit unauthentifiziertem client versuchen zu erstellen
        resp = client.post(f"/api/v1/projects/{ctx['project_id']}/constraints", json={
            "name": "Test",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": 1, "value_id": 2},
        })
        assert resp.status_code in (401, 403)

    def test_delete_requires_writer(self, client, auth_client):
        """DELETE ohne Auth -> 401/403."""
        ctx = _create_test_project(auth_client)
        resp = client.delete(f"/api/v1/projects/{ctx['project_id']}/constraints/1")
        assert resp.status_code in (401, 403)