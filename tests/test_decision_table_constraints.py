"""REQ-5012: Constraint CRUD API Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Testet persistente Constraint-Speicherung und CRUD-Endpoints.
"""
import time

import pytest


def _unique_suffix() -> str:
    """Erzeugt einen eindeutigen Suffix fuer Projekt-Namen."""
    return f"{int(time.time() * 1000)}"


def _setup_decision_table_project(auth_client) -> int:
    """Erstellt ein Projekt mit Ursachen und Wirkungen fuer die Entscheidungstabelle."""
    suffix = _unique_suffix()
    project = auth_client.post("/api/projects", json={"name": f"DT_Constraint_Test_{suffix}"})
    assert project.status_code == 200, project.text
    pid = project.json()["id"]

    # Erstelle Ursachen
    for i, name in enumerate([f"Ursache1_{suffix}", f"Ursache2_{suffix}", f"Ursache3_{suffix}"]):
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


def _get_cause_ids(auth_client, project_id: int) -> list:
    """Holt die IDs aller Ursachen eines Projekts."""
    resp = auth_client.get(f"/api/decision-table/categories/{project_id}")
    assert resp.status_code == 200, resp.text
    return [c["id"] for c in resp.json()["causes"]]


def _get_effect_ids(auth_client, project_id: int) -> list:
    """Holt die IDs aller Wirkungen eines Projekts."""
    resp = auth_client.get(f"/api/decision-table/categories/{project_id}")
    assert resp.status_code == 200, resp.text
    return [e["id"] for e in resp.json()["effects"]]


# =============================================================================
# Slice 1: Constraint CRUD Tests
# =============================================================================

class TestConstraintCreate:
    """Tests fuer POST /api/decision-table/constraints (REQ-5012)."""

    def test_create_constraint_E_valid(self, auth_client):
        """REQ-5012: Constraint E mit 2 Ursachen -> 200 OK."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0], cause_ids[1]],
                "description": "Test-Exclusive",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["type"] == "E"
        assert data["targets"] == [cause_ids[0], cause_ids[1]]
        assert data["description"] == "Test-Exclusive"
        assert "id" in data

    def test_create_constraint_E_too_few(self, auth_client):
        """REQ-5012: Constraint E mit 1 Ursache -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0]],
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_O_valid(self, auth_client):
        """REQ-5012: Constraint O mit 2 Ursachen -> 200 OK."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "O",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["type"] == "O"

    def test_create_constraint_O_too_few(self, auth_client):
        """REQ-5012: Constraint O mit 1 Ursache -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "O",
                "targets": [cause_ids[0]],
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_I_valid(self, auth_client):
        """REQ-5012: Constraint I mit 2 Ursachen -> 200 OK."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "I",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["type"] == "I"

    def test_create_constraint_I_too_few(self, auth_client):
        """REQ-5012: Constraint I mit 1 Ursache -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "I",
                "targets": [cause_ids[0]],
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_R_valid(self, auth_client):
        """REQ-5012: Constraint R mit from/to -> 200 OK."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "R",
                "targets": {"from": cause_ids[0], "to": cause_ids[1]},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["type"] == "R"
        assert data["targets"]["from"] == cause_ids[0]
        assert data["targets"]["to"] == cause_ids[1]

    def test_create_constraint_R_missing_from(self, auth_client):
        """REQ-5012: Constraint R ohne 'from' -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "R",
                "targets": {"to": cause_ids[1]},
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_R_missing_to(self, auth_client):
        """REQ-5012: Constraint R ohne 'to' -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "R",
                "targets": {"from": cause_ids[0]},
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_M_valid(self, auth_client):
        """REQ-5012: Constraint M mit from/to -> 200 OK."""
        pid = _setup_decision_table_project(auth_client)
        effect_ids = _get_effect_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "M",
                "targets": {"from": effect_ids[0], "to": effect_ids[1]},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["type"] == "M"

    def test_create_constraint_M_missing_from(self, auth_client):
        """REQ-5012: Constraint M ohne 'from' -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        effect_ids = _get_effect_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "M",
                "targets": {"to": effect_ids[1]},
            },
        )
        assert resp.status_code == 400, resp.text

    def test_create_constraint_invalid_type(self, auth_client):
        """REQ-5012: Ungueltiger Constraint-Typ -> 400 Fehler."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "X",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )
        assert resp.status_code == 400, resp.text


# =============================================================================
# Slice 2: Constraint GET/DELETE Tests
# =============================================================================

class TestConstraintList:
    """Tests fuer GET /api/decision-table/constraints/{project_id} (REQ-5012)."""

    def test_get_empty_constraints(self, auth_client):
        """REQ-5012: GET /constraints bei leerem Projekt -> leere Liste."""
        pid = _setup_decision_table_project(auth_client)

        resp = auth_client.get(f"/api/decision-table/constraints/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data == []

    def test_get_constraints_after_create(self, auth_client):
        """REQ-5012: GET /constraints nach Erstellen -> Liste mit Eintraegen."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        # Erstelle 2 Constraints
        auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0], cause_ids[1]],
                "description": "Test-E",
            },
        )
        auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "R",
                "targets": {"from": cause_ids[0], "to": cause_ids[1]},
            },
        )

        resp = auth_client.get(f"/api/decision-table/constraints/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 2
        types = [c["type"] for c in data]
        assert "E" in types
        assert "R" in types


class TestConstraintDelete:
    """Tests fuer DELETE /api/decision-table/constraints/{constraint_id} (REQ-5012)."""

    def test_delete_constraint(self, auth_client):
        """REQ-5012: Constraint loeschen -> 200 + nicht mehr in Liste."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        # Erstelle Constraint
        create_resp = auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )
        assert create_resp.status_code == 200, create_resp.text
        constraint_id = create_resp.json()["id"]

        # Loesche Constraint
        del_resp = auth_client.delete(f"/api/decision-table/constraints/{constraint_id}")
        assert del_resp.status_code == 200, del_resp.text

        # Pruefe dass Constraint nicht mehr existiert
        list_resp = auth_client.get(f"/api/decision-table/constraints/{pid}")
        assert list_resp.status_code == 200, list_resp.text
        remaining = list_resp.json()
        assert len(remaining) == 0

    def test_delete_nonexistent_constraint(self, auth_client):
        """REQ-5012: Nicht-existenten Constraint loeschen -> 404."""
        resp = auth_client.delete("/api/decision-table/constraints/99999")
        assert resp.status_code == 404, resp.text


# =============================================================================
# Slice 3: Integration - persistente Constraints in /generate
# =============================================================================

class TestConstraintGenerateIntegration:
    """Tests fuer Integration persistenter Constraints in POST /generate (REQ-5012)."""

    def test_generate_uses_persistent_constraints(self, auth_client):
        """REQ-5012: POST /generate ohne constraints uebernimmt persistente Constraints."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        # Erstelle persistenten Constraint E (exklusiv: max 1 Y)
        auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )

        # Generiere OHNE constraints-Parameter
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # 3 Ursachen = 2^3 = 8 Regeln, E-Constraint auf c1,c2 filtert YY-Kombos
        # Ohne Constraint: 8 Regeln
        # Mit E-Constraint auf c1,c2: Regeln wo beide Y sind werden entfernt
        # YYxx: 2 Regeln entfernt (YYN, YYY) -> 6 bleiben
        assert data["total_rules"] == 8  # total_rules zeigt Original-Anzahl
        assert "rules_after_constraints" in data
        assert data["rules_after_constraints"] == 6

    def test_generate_constraints_override_persistent(self, auth_client):
        """REQ-5012: POST /generate mit constraints ueberschreibt persistente."""
        pid = _setup_decision_table_project(auth_client)
        cause_ids = _get_cause_ids(auth_client, pid)

        # Erstelle persistenten Constraint E auf c1,c2
        auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [cause_ids[0], cause_ids[1]],
            },
        )

        # Generiere mit Override-Constraint O auf c1,c2 (exactly 1 Y)
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "constraints": [{"type": "O", "causes": [cause_ids[0], cause_ids[1]]}],
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # O-Constraint: genau 1 Y von c1,c2 -> 4 Regeln (YNN, NYN, YNY, NYY)
        assert "rules_after_constraints" in data
        assert data["rules_after_constraints"] == 4