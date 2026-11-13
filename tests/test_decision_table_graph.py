"""REQ-5018: Cause-Effect-Graph API Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Testet generate_cause_effect_graph() und GET /graph/{project_id}.
"""
import time

import pytest

from app.database import SessionLocal
from app.models import Category, Project
from app.models.decision_table_constraint import DecisionTableConstraint


def _unique_suffix() -> str:
    """Erzeugt einen eindeutigen Suffix fuer Projekt-Namen."""
    return f"{int(time.time() * 1000000)}"


def _create_test_project(db, name: str) -> int:
    """Hilfsfunktion: Erstellt ein Test-Projekt und gibt die ID zurueck."""
    project = Project(name=f"{name}_{_unique_suffix()}")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.id


def _create_cause_category(db, project_id: int, name: str, order_index: int = 0) -> int:
    """Hilfsfunktion: Erstellt eine Ursache-Kategorie."""
    cat = Category(
        project_id=project_id,
        name=name,
        category_type="cause",
        order_index=order_index,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def _create_effect_category(db, project_id: int, name: str, order_index: int = 0) -> int:
    """Hilfsfunktion: Erstellt eine Wirkung-Kategorie."""
    cat = Category(
        project_id=project_id,
        name=name,
        category_type="effect",
        order_index=order_index,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat.id


def _create_constraint(db, project_id: int, ctype: str, targets, description: str = None) -> int:
    """Hilfsfunktion: Erstellt einen Constraint."""
    c = DecisionTableConstraint(
        project_id=project_id,
        constraint_type=ctype,
        targets=targets,
        description=description,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c.id


# =============================================================================
# Slice 1: Service-Tests fuer generate_cause_effect_graph
# =============================================================================

class TestGenerateCauseEffectGraph:
    """Tests fuer generate_cause_effect_graph() (REQ-5018)."""

    def test_graph_basic_structure(self):
        """REQ-5018: Graph hat causes, effects, edges, constraints."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Basic")
            _create_cause_category(db, pid, "C1", order_index=0)
            _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_effect_category(db, pid, "E2", order_index=1)

            result = generate_cause_effect_graph(db, pid)

            assert "causes" in result
            assert "effects" in result
            assert "edges" in result
            assert "constraints" in result
            assert len(result["causes"]) == 2
            assert len(result["effects"]) == 2
            assert len(result["edges"]) == 0
            assert len(result["constraints"]) == 0
        finally:
            db.close()

    def test_graph_causes_have_id_and_name(self):
        """REQ-5018: Causes im Graph haben id und name."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Causes")
            c1_id = _create_cause_category(db, pid, "Ursache_A", order_index=0)
            c2_id = _create_cause_category(db, pid, "Ursache_B", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_cause_effect_graph(db, pid)

            causes = result["causes"]
            assert len(causes) == 2
            cause_map = {c["id"]: c for c in causes}
            assert cause_map[c1_id]["name"] == "Ursache_A"
            assert cause_map[c2_id]["name"] == "Ursache_B"
        finally:
            db.close()

    def test_graph_effects_have_id_and_name(self):
        """REQ-5018: Effects im Graph haben id und name."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Effects")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "Wirkung_X", order_index=0)
            e2_id = _create_effect_category(db, pid, "Wirkung_Y", order_index=1)

            result = generate_cause_effect_graph(db, pid)

            effects = result["effects"]
            assert len(effects) == 2
            effect_map = {e["id"]: e for e in effects}
            assert effect_map[e1_id]["name"] == "Wirkung_X"
            assert effect_map[e2_id]["name"] == "Wirkung_Y"
        finally:
            db.close()

    def test_graph_empty_no_causes(self):
        """REQ-5018: Graph ohne Ursachen -> leere causes-Liste."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_NoCauses")
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_cause_effect_graph(db, pid)

            assert len(result["causes"]) == 0
            assert len(result["effects"]) == 1
            assert len(result["edges"]) == 0
        finally:
            db.close()

    def test_graph_empty_no_effects(self):
        """REQ-5018: Graph ohne Wirkungen -> leere effects-Liste."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_NoEffects")
            _create_cause_category(db, pid, "C1", order_index=0)

            result = generate_cause_effect_graph(db, pid)

            assert len(result["causes"]) == 1
            assert len(result["effects"]) == 0
            assert len(result["edges"]) == 0
        finally:
            db.close()


# =============================================================================
# Slice 2: Edge-Tests (Constraints -> Edges)
# =============================================================================

class TestGraphEdges:
    """Tests fuer Edge-Generierung aus Constraints (REQ-5018)."""

    def test_edge_E_exclusive(self):
        """REQ-5018: E-Constraint erzeugt cause-cause edge 'Exclusive'."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Edge_E")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_constraint(db, pid, "E", [c1_id, c2_id], "Test-E")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 1
            edge = result["edges"][0]
            assert edge["type"] == "E"
            assert edge["label"] == "Exclusive"
            # Both directions should be covered
            assert f"cause:{c1_id}" in edge["from"]
            assert f"cause:{c2_id}" in edge["to"]
        finally:
            db.close()

    def test_edge_O_one_and_only_one(self):
        """REQ-5018: O-Constraint erzeugt cause-cause edge 'One-and-Only-One'."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Edge_O")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_constraint(db, pid, "O", [c1_id, c2_id], "Test-O")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 1
            edge = result["edges"][0]
            assert edge["type"] == "O"
            assert edge["label"] == "One-and-Only-One"
        finally:
            db.close()

    def test_edge_I_inclusive(self):
        """REQ-5018: I-Constraint erzeugt cause-cause edge 'Inclusive'."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Edge_I")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_constraint(db, pid, "I", [c1_id, c2_id], "Test-I")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 1
            edge = result["edges"][0]
            assert edge["type"] == "I"
            assert edge["label"] == "Inclusive"
        finally:
            db.close()

    def test_edge_R_requires(self):
        """REQ-5018: R-Constraint erzeugt cause-cause edge 'requires'."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Edge_R")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_constraint(db, pid, "R", {"from": c1_id, "to": c2_id}, "Test-R")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 1
            edge = result["edges"][0]
            assert edge["type"] == "requires"
            assert edge["label"] == "Requires"
            assert edge["from"] == f"cause:{c1_id}"
            assert edge["to"] == f"cause:{c2_id}"
        finally:
            db.close()

    def test_edge_M_mask(self):
        """REQ-5018: M-Constraint erzeugt effect-effect edge 'mask'."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Edge_M")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            e2_id = _create_effect_category(db, pid, "E2", order_index=1)
            _create_constraint(db, pid, "M", {"from": e1_id, "to": e2_id}, "Test-M")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 1
            edge = result["edges"][0]
            assert edge["type"] == "mask"
            assert edge["label"] == "Mask"
            assert edge["from"] == f"effect:{e1_id}"
            assert edge["to"] == f"effect:{e2_id}"
        finally:
            db.close()

    def test_edge_multiple_constraints(self):
        """REQ-5018: Multiple Constraints erzeugen multiple Edges."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Multi")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            c3_id = _create_cause_category(db, pid, "C3", order_index=2)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            e2_id = _create_effect_category(db, pid, "E2", order_index=1)

            # E-Constraint auf C1, C2
            _create_constraint(db, pid, "E", [c1_id, c2_id])
            # R-Constraint C2 -> C3
            _create_constraint(db, pid, "R", {"from": c2_id, "to": c3_id})
            # M-Constraint E1 -> E2
            _create_constraint(db, pid, "M", {"from": e1_id, "to": e2_id})

            result = generate_cause_effect_graph(db, pid)

            assert len(result["edges"]) == 3
            types = [e["type"] for e in result["edges"]]
            assert "E" in types
            assert "requires" in types
            assert "mask" in types
        finally:
            db.close()

    def test_edge_E_three_causes(self):
        """REQ-5018: E-Constraint mit 3 Ursachen erzeugt 3 Edges (C1-C2, C1-C3, C2-C3)."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_E_3")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            c3_id = _create_cause_category(db, pid, "C3", order_index=2)
            _create_effect_category(db, pid, "E1", order_index=0)
            _create_constraint(db, pid, "E", [c1_id, c2_id, c3_id])

            result = generate_cause_effect_graph(db, pid)

            # 3 causes -> 3 edges (C1-C2, C1-C3, C2-C3)
            assert len(result["edges"]) == 3
            for edge in result["edges"]:
                assert edge["type"] == "E"
                assert edge["label"] == "Exclusive"
        finally:
            db.close()

    def test_constraints_in_result(self):
        """REQ-5018: Constraints werden im Ergebnis mitgeliefert."""
        from app.services_decision_table import generate_cause_effect_graph

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "Graph_Constraints")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            c2_id = _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)
            cid = _create_constraint(db, pid, "E", [c1_id, c2_id], "Test-Description")

            result = generate_cause_effect_graph(db, pid)

            assert len(result["constraints"]) == 1
            c = result["constraints"][0]
            assert c["id"] == cid
            assert c["type"] == "E"
            assert c["targets"] == [c1_id, c2_id]
            assert c["description"] == "Test-Description"
        finally:
            db.close()


# =============================================================================
# Slice 3: API-Tests fuer GET /graph/{project_id}
# =============================================================================

class TestGraphAPI:
    """Tests fuer GET /api/decision-table/graph/{project_id} (REQ-5018)."""

    def test_graph_api_valid_project(self, auth_client):
        """REQ-5018: GET /graph mit gueltigem Projekt -> 200 mit Graph-Daten."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"Graph_API_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle Ursachen und Wirkungen
        for i, name in enumerate([f"C1_{suffix}", f"C2_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "cause", "order_index": i},
            )
        for i, name in enumerate([f"E1_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "effect", "order_index": i},
            )

        resp = auth_client.get(f"/api/decision-table/graph/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "causes" in data
        assert "effects" in data
        assert "edges" in data
        assert "constraints" in data
        assert len(data["causes"]) == 2
        assert len(data["effects"]) == 1

    def test_graph_api_nonexistent_project(self, auth_client):
        """REQ-5018: GET /graph mit nicht-existentem Projekt -> 404."""
        resp = auth_client.get("/api/decision-table/graph/99999")
        assert resp.status_code == 404, resp.text

    def test_graph_api_with_constraints(self, auth_client):
        """REQ-5018: GET /graph mit Constraints -> Edges im Ergebnis."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"Graph_API_C_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle Ursachen und Wirkungen
        for i, name in enumerate([f"C1_{suffix}", f"C2_{suffix}"]):
            resp = auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "cause", "order_index": i},
            )
            assert resp.status_code == 200, resp.text

        for i, name in enumerate([f"E1_{suffix}", f"E2_{suffix}"]):
            resp = auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "effect", "order_index": i},
            )
            assert resp.status_code == 200, resp.text

        # Hole IDs
        cat_resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert cat_resp.status_code == 200
        causes = cat_resp.json()["causes"]
        effects = cat_resp.json()["effects"]

        # Erstelle E-Constraint
        auth_client.post(
            "/api/decision-table/constraints",
            json={
                "project_id": pid,
                "constraint_type": "E",
                "targets": [causes[0]["id"], causes[1]["id"]],
            },
        )

        resp = auth_client.get(f"/api/decision-table/graph/{pid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert len(data["edges"]) >= 1
        assert len(data["constraints"]) >= 1