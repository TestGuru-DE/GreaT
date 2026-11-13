"""REQ-5021: Priorisierung von Wirkungen (Override) Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Testet apply_effect_priorities() und die Integration in POST /generate.
"""
import time

import pytest

from app.database import SessionLocal
from app.models import Category, Project


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


# =============================================================================
# Slice 1: Service-Tests fuer apply_effect_priorities
# =============================================================================

class TestApplyEffectPriorities:
    """Tests fuer apply_effect_priorities() (REQ-5021)."""

    def test_two_effects_priority(self):
        """REQ-5021: 2 Wirkungen mit Prioritaet -> nur hoechste bleibt."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        # E1 hat Prioritaet 1 (hoechst), E2 hat Prioritaet 2
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 1
        # E1 (priority 1) bleibt X
        assert result[0]["effects"][10] == "X"
        # E2 (priority 2) wird zu None (Don't Care)
        assert result[0]["effects"][20] is None

    def test_single_effect_no_change(self):
        """REQ-5021: 1 Wirkung -> keine Aenderung."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}]
        priorities = {10: 1}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 1
        assert result[0]["effects"][10] == "X"

    def test_no_priorities_no_change(self):
        """REQ-5021: Keine Prioritaeten -> keine Aenderung."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]

        result = apply_effect_priorities(rules, effects, {})

        assert len(result) == 1
        # Beide bleiben X
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] == "X"

    def test_no_priorities_none(self):
        """REQ-5021: None als Prioritaeten -> keine Aenderung."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]

        result = apply_effect_priorities(rules, effects, None)

        assert len(result) == 1
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] == "X"

    def test_three_effects_priority(self):
        """REQ-5021: 3 Wirkungen -> nur hoechst-priorisierte bleibt."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X", 30: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}, {"id": 30, "name": "E3"}]
        # E2 hat hoechste Prioritaet (1), E1 hat 2, E3 hat 3
        priorities = {10: 2, 20: 1, 30: 3}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 1
        # E2 (priority 1) bleibt X
        assert result[0]["effects"][20] == "X"
        # E1 (priority 2) wird zu None
        assert result[0]["effects"][10] is None
        # E3 (priority 3) wird zu None
        assert result[0]["effects"][30] is None

    def test_multiple_rules_different_effects(self):
        """REQ-5021: Multiple Regeln, unterschiedliche aktive Wirkungen."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},  # Beide X
            },
            {
                "id": 2,
                "causes": {1: "N"},
                "effects": {10: "X", 20: "N"},  # Nur E1 X
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 2
        # Regel 1: E1 bleibt X, E2 wird None
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] is None
        # Regel 2: Nur E1 ist X, keine Aenderung
        assert result[1]["effects"][10] == "X"
        assert result[1]["effects"][20] == "N"

    def test_no_active_effects(self):
        """REQ-5021: Keine aktiven Wirkungen (alle None) -> keine Aenderung."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: None, 20: None},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 1
        assert result[0]["effects"][10] is None
        assert result[0]["effects"][20] is None

    def test_missing_priority_default_low(self):
        """REQ-5021: Wirkung ohne Prioritaet hat default niedrige Prioritaet."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        # Nur E1 hat Prioritaet, E2 fehlt (default 999)
        priorities = {10: 1}

        result = apply_effect_priorities(rules, effects, priorities)

        assert len(result) == 1
        # E1 (priority 1) bleibt X
        assert result[0]["effects"][10] == "X"
        # E2 (default 999) wird zu None
        assert result[0]["effects"][20] is None

    def test_empty_rules(self):
        """REQ-5021: Leere Regel-Liste -> leere Liste zurueck."""
        from app.services_decision_table import apply_effect_priorities

        effects = [{"id": 10, "name": "E1"}]
        priorities = {10: 1}

        result = apply_effect_priorities([], effects, priorities)

        assert result == []


# =============================================================================
# Slice 2: API-Integration Tests
# =============================================================================

class TestPriorityAPI:
    """Tests fuer Prioritaet-Integration in POST /generate (REQ-5021)."""

    def test_generate_with_priorities(self, auth_client):
        """REQ-5021: POST /generate mit priorities -> Wirkungen werden priorisiert."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"Priority_API_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle Ursachen und Wirkungen
        for i, name in enumerate([f"C1_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "cause", "order_index": i},
            )
        for i, name in enumerate([f"E1_{suffix}", f"E2_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "effect", "order_index": i},
            )

        # Hole IDs
        cat_resp = auth_client.get(f"/api/decision-table/categories/{pid}")
        assert cat_resp.status_code == 200
        effects = cat_resp.json()["effects"]
        e1_id = effects[0]["id"]
        e2_id = effects[1]["id"]

        # Generiere mit Prioritaeten
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "priorities": {str(e1_id): 1, str(e2_id): 2},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "rules" in data
        assert len(data["rules"]) == 2  # 2^1 = 2

    def test_generate_without_priorities(self, auth_client):
        """REQ-5021: POST /generate ohne priorities -> normale Generierung."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"Priority_No_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle Ursachen und Wirkungen
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"C1_{suffix}", "category_type": "cause", "order_index": 0},
        )
        for i, name in enumerate([f"E1_{suffix}", f"E2_{suffix}"]):
            auth_client.post(
                f"/api/projects/{pid}/categories",
                json={"name": name, "category_type": "effect", "order_index": i},
            )

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={"project_id": pid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "rules" in data
        assert len(data["rules"]) == 2