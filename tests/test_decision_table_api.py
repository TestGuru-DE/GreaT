"""REQ-5000: Decision Table API Endpoint Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).
"""
import time

import pytest


def _unique_suffix() -> str:
    """Erzeugt einen eindeutigen Suffix fuer Projekt-Namen."""
    return f"{int(time.time() * 1000)}"


def _setup_decision_table_project(auth_client) -> int:
    """Erstellt ein Projekt mit Ursachen und Wirkungen fuer die Entscheidungstabelle."""
    suffix = _unique_suffix()
    project = auth_client.post("/api/projects", json={"name": f"DT_API_Test_{suffix}"})
    assert project.status_code == 200, project.text
    pid = project.json()["id"]

    # Erstelle Ursachen
    for i, name in enumerate([f"Ursache1_{suffix}", f"Ursache2_{suffix}"]):
        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": name, "category_type": "cause", "order_index": i},
        )
        assert resp.status_code == 200, resp.text

    # Erstelle Wirkungen
    for i, name in enumerate([f"Wirkung1_{suffix}", f"Wirkung2_{suffix}"]):
        resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": name, "category_type": "effect", "order_index": i},
        )
        assert resp.status_code == 200, resp.text

    return pid


class TestDecisionTableGenerate:
    """Tests fuer POST /api/decision-table/generate."""

    def test_generate_valid_project(self, auth_client):
        """POST /generate mit gueltigem Projekt -> 200 mit Regeln."""
        pid = _setup_decision_table_project(auth_client)

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "causes" in data
        assert "effects" in data
        assert "rules" in data
        assert "total_rules" in data
        assert data["total_rules"] == 4  # 2^2 = 4
        assert len(data["causes"]) == 2
        assert len(data["effects"]) == 2

    def test_generate_no_causes(self, auth_client):
        """POST /generate ohne Ursachen -> Fehlermeldung."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_NoCauses_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        # Nur Wirkungen, keine Ursachen
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung1_{suffix}", "category_type": "effect"},
        )

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "error" in data
        assert data["rules"] == []

    def test_generate_no_effects(self, auth_client):
        """POST /generate ohne Wirkungen -> Fehlermeldung."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_NoEffects_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        # Nur Ursachen, keine Wirkungen
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Ursache1_{suffix}", "category_type": "cause"},
        )

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "error" in data
        assert data["rules"] == []

    def test_generate_nonexistent_project(self, auth_client):
        """POST /generate mit nicht-existentem Projekt -> 404."""
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": 99999},
        )
        assert resp.status_code == 404, resp.text

    def test_generate_with_constraints(self, auth_client):
        """POST /generate mit Constraints -> Regeln werden gefiltert."""
        pid = _setup_decision_table_project(auth_client)

        # Hole cause IDs
        cat_resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert cat_resp.status_code == 200, cat_resp.text
        causes = cat_resp.json()["causes"]
        c1_id = causes[0]["id"]
        c2_id = causes[1]["id"]

        # Constraint E: max 1 of c1, c2 can be Y
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "constraints": [{"type": "E", "causes": [c1_id, c2_id]}],
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "rules_after_constraints" in data
        assert data["rules_after_constraints"] == 3  # YY filtered out
        assert len(data["rules"]) == 3

    def test_generate_rules_have_correct_structure(self, auth_client):
        """Regeln haben die korrekte Struktur mit causes und effects."""
        pid = _setup_decision_table_project(auth_client)

        # Hole IDs
        cat_resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        causes = cat_resp.json()["causes"]
        effects = cat_resp.json()["effects"]

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        for rule in data["rules"]:
            assert "id" in rule
            assert "causes" in rule
            assert "effects" in rule

            # Ursachen haben Y oder N (JSON serialisiert integer keys als strings)
            for c in causes:
                cause_key = str(c["id"])
                assert cause_key in rule["causes"], f"cause {cause_key} nicht in rule {rule['id']}"
                assert rule["causes"][cause_key] in ("Y", "N")

            # Wirkungen sind initial None (null in JSON)
            for e in effects:
                effect_key = str(e["id"])
                assert effect_key in rule["effects"], f"effect {effect_key} nicht in rule {rule['id']}"
                assert rule["effects"][effect_key] is None


class TestDecisionTableCategories:
    """Tests fuer GET /api/decision-table/categories/{project_id}."""

    def test_get_categories_valid_project(self, auth_client):
        """GET /categories mit gueltigem Projekt -> causes + effects."""
        pid = _setup_decision_table_project(auth_client)

        resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "causes" in data
        assert "effects" in data
        assert "can_generate" in data
        assert len(data["causes"]) == 2
        assert len(data["effects"]) == 2
        assert data["can_generate"] is True

    def test_can_generate_true_when_both_present(self, auth_client):
        """can_generate ist True wenn sowohl Ursachen als auch Wirkungen vorhanden."""
        pid = _setup_decision_table_project(auth_client)

        resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["can_generate"] is True

    def test_can_generate_false_no_causes(self, auth_client):
        """can_generate ist False wenn keine Ursachen vorhanden."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_CanGen_False_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Wirkung1_{suffix}", "category_type": "effect"},
        )

        resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["can_generate"] is False
        assert len(data["causes"]) == 0
        assert len(data["effects"]) == 1

    def test_can_generate_false_no_effects(self, auth_client):
        """can_generate ist False wenn keine Wirkungen vorhanden."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"DT_CanGen_False2_{suffix}"})
        assert project.status_code == 200
        pid = project.json()["id"]

        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"Ursache1_{suffix}", "category_type": "cause"},
        )

        resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["can_generate"] is False
        assert len(data["causes"]) == 1
        assert len(data["effects"]) == 0

    def test_get_categories_nonexistent_project(self, auth_client):
        """GET /categories mit nicht-existentem Projekt -> 404."""
        resp = auth_client.get("/api/decision-table/categories/99999")
        assert resp.status_code == 404, resp.text

    def test_categories_include_ids_and_names(self, auth_client):
        """Kategorien enthalten id und name."""
        pid = _setup_decision_table_project(auth_client)

        resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        for cause in data["causes"]:
            assert "id" in cause
            assert "name" in cause
            assert isinstance(cause["id"], int)
            assert isinstance(cause["name"], str)

        for effect in data["effects"]:
            assert "id" in effect
            assert "name" in effect
            assert isinstance(effect["id"], int)
            assert isinstance(effect["name"], str)