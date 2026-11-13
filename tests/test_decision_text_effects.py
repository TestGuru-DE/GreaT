"""REQ-5016/5021: Text-Effekte + Don't Care Reduktion Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Slice 1 (REQ-5016):
- effect_mode="text" laedt Werte der Wirkungskategorie
- effect_mode="binary" verwendet X/-
- Fallback-Werte wenn keine Werte existieren

Slice 2 (REQ-5021):
- enable_override=True setzt Don't Care (-)
- enable_override=False setzt None
- Keine Prioritaeten -> keine Aenderung
"""
import time

import pytest

from app.database import SessionLocal
from app.models import Category, Project, Value


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


def _create_effect_values(db, effect_id: int, values: list) -> None:
    """Hilfsfunktion: Erstellt Werte fuer eine Wirkung-Kategorie."""
    for i, v in enumerate(values):
        val = Value(
            category_id=effect_id,
            value=v,
            allowed=True,
            vtype="string",
            order_index=i,
        )
        db.add(val)
    db.commit()


# =============================================================================
# Slice 1: REQ-5016 - Wirkungen als Text (Backend)
# =============================================================================

class TestEffectModeText:
    """Tests fuer effect_mode="text" (REQ-5016)."""

    def test_effect_mode_text_loads_values(self):
        """REQ-5016: effect_mode="text" laedt Werte der Wirkungskategorie."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_Text")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            _create_effect_values(db, e1_id, ["Genehmigen", "Ablehnen", "Manuelle Pruefung"])

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" not in result
            assert len(result["effects"]) == 1
            # Die Wirkung sollte die Werte aus der Kategorie haben
            assert result["effects"][0]["id"] == e1_id
            assert result["effects"][0]["name"] == "E1"
            assert "values" in result["effects"][0]
            assert result["effects"][0]["values"] == ["Genehmigen", "Ablehnen", "Manuelle Pruefung"]
        finally:
            db.close()

    def test_effect_mode_text_multiple_effects(self):
        """REQ-5016: Mehrere Wirkungen mit eigenen Werten."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_Multi")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            e2_id = _create_effect_category(db, pid, "E2", order_index=1)
            _create_effect_values(db, e1_id, ["Ja", "Nein"])
            _create_effect_values(db, e2_id, ["Pass", "Fail"])

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" not in result
            assert len(result["effects"]) == 2
            assert result["effects"][0]["values"] == ["Ja", "Nein"]
            assert result["effects"][1]["values"] == ["Pass", "Fail"]
        finally:
            db.close()

    def test_effect_mode_text_fallback_values(self):
        """REQ-5016: Fallback-Werte wenn keine Werte existieren."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_Fallback")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1_NoValues", order_index=0)
            # Keine Werte erstellen!

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" not in result
            assert len(result["effects"]) == 1
            # Fallback-Werte sollten verwendet werden
            assert result["effects"][0]["values"] == ["Genehmigen", "Ablehnen", "Manuelle Pruefung"]
        finally:
            db.close()

    def test_effect_mode_binary_default(self):
        """REQ-5016: effect_mode="binary" (Default) verwendet X/- ohne Werte."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_Binary")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            _create_effect_values(db, e1_id, ["Genehmigen", "Ablehnen"])

            result = generate_decision_table(db, pid, effect_mode="binary")

            assert "error" not in result
            assert len(result["effects"]) == 1
            # Im binary-Modus: nur id und name, keine values
            assert result["effects"][0]["id"] == e1_id
            assert result["effects"][0]["name"] == "E1"
            assert "values" not in result["effects"][0]
        finally:
            db.close()

    def test_effect_mode_binary_no_values_key(self):
        """REQ-5016: binary-Modus hat kein 'values'-Feld."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_NoValues")
            _create_cause_category(db, pid, "C1", order_index=0)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid, effect_mode="binary")

            assert "error" not in result
            for effect in result["effects"]:
                assert "values" not in effect
        finally:
            db.close()

    def test_effect_mode_text_rules_still_none(self):
        """REQ-5016: Wirkungszellen in Regeln bleiben initial None (freier Text)."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_Rules")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            _create_effect_values(db, e1_id, ["Genehmigen", "Ablehnen"])

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" not in result
            # Wirkungszellen in Regeln sind initial None (freier Text)
            for rule in result["rules"]:
                assert rule["effects"][e1_id] is None
        finally:
            db.close()

    def test_effect_mode_text_zero_causes_error(self):
        """REQ-5016: 0 Ursachen -> Fehler, aber effects haben values."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_NoCauses")
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            _create_effect_values(db, e1_id, ["Ja", "Nein"])

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" in result
            assert result["rules"] == []
            # Effects sollten trotzdem values haben
            assert len(result["effects"]) == 1
            assert result["effects"][0]["values"] == ["Ja", "Nein"]
        finally:
            db.close()

    def test_effect_mode_text_zero_effects_error(self):
        """REQ-5016: 0 Wirkungen -> Fehler, leere effects-Liste."""
        from app.services_decision_table import generate_decision_table

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "REQ5016_NoEffects")
            _create_cause_category(db, pid, "C1", order_index=0)

            result = generate_decision_table(db, pid, effect_mode="text")

            assert "error" in result
            assert result["effects"] == []
            assert result["rules"] == []
        finally:
            db.close()


# =============================================================================
# Slice 2: REQ-5021 - Don't Care Reduktion + opt-in Toggle
# =============================================================================

class TestEnableOverride:
    """Tests fuer enable_override Toggle (REQ-5021)."""

    def test_enable_override_true_sets_dont_care(self):
        """REQ-5021: enable_override=True setzt Don't Care (-) statt None."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 1
        # E1 (priority 1) bleibt X
        assert result[0]["effects"][10] == "X"
        # E2 (priority 2) wird zu "-" (Don't Care) statt None
        assert result[0]["effects"][20] == "-"

    def test_enable_override_false_sets_none(self):
        """REQ-5021: enable_override=False (Default) setzt None."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities, enable_override=False)

        assert len(result) == 1
        # E1 (priority 1) bleibt X
        assert result[0]["effects"][10] == "X"
        # E2 (priority 2) wird zu None
        assert result[0]["effects"][20] is None

    def test_no_priorities_no_change_override_true(self):
        """REQ-5021: Keine Prioritaeten -> keine Aenderung, auch mit enable_override=True."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]

        result = apply_effect_priorities(rules, effects, None, enable_override=True)

        assert len(result) == 1
        # Beide bleiben X
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] == "X"

    def test_no_priorities_no_change_empty_dict(self):
        """REQ-5021: Leeres Dict als Prioritaeten -> keine Aenderung."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]

        result = apply_effect_priorities(rules, effects, {}, enable_override=True)

        assert len(result) == 1
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] == "X"

    def test_three_effects_override(self):
        """REQ-5021: 3 Wirkungen mit enable_override=True."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X", 30: "X"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}, {"id": 30, "name": "E3"}]
        priorities = {10: 2, 20: 1, 30: 3}

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 1
        # E2 (priority 1) bleibt X
        assert result[0]["effects"][20] == "X"
        # E1 (priority 2) wird zu "-"
        assert result[0]["effects"][10] == "-"
        # E3 (priority 3) wird zu "-"
        assert result[0]["effects"][30] == "-"

    def test_single_effect_no_change_override(self):
        """REQ-5021: 1 Wirkung -> keine Aenderung, auch mit enable_override=True."""
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

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 1
        assert result[0]["effects"][10] == "X"

    def test_multiple_rules_override(self):
        """REQ-5021: Multiple Regeln mit enable_override=True."""
        from app.services_decision_table import apply_effect_priorities

        rules = [
            {
                "id": 1,
                "causes": {1: "Y"},
                "effects": {10: "X", 20: "X"},
            },
            {
                "id": 2,
                "causes": {1: "N"},
                "effects": {10: "X", 20: "N"},
            },
        ]
        effects = [{"id": 10, "name": "E1"}, {"id": 20, "name": "E2"}]
        priorities = {10: 1, 20: 2}

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 2
        # Regel 1: E1 bleibt X, E2 wird "-"
        assert result[0]["effects"][10] == "X"
        assert result[0]["effects"][20] == "-"
        # Regel 2: Nur E1 ist X, keine Aenderung
        assert result[1]["effects"][10] == "X"
        assert result[1]["effects"][20] == "N"

    def test_no_active_effects_override(self):
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

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 1
        assert result[0]["effects"][10] is None
        assert result[0]["effects"][20] is None

    def test_empty_rules_override(self):
        """REQ-5021: Leere Regel-Liste -> leere Liste zurueck."""
        from app.services_decision_table import apply_effect_priorities

        effects = [{"id": 10, "name": "E1"}]
        priorities = {10: 1}

        result = apply_effect_priorities([], effects, priorities, enable_override=True)

        assert result == []

    def test_missing_priority_default_low_override(self):
        """REQ-5021: Wirkung ohne Prioritaet hat default niedrige Prioritaet + override."""
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

        result = apply_effect_priorities(rules, effects, priorities, enable_override=True)

        assert len(result) == 1
        # E1 (priority 1) bleibt X
        assert result[0]["effects"][10] == "X"
        # E2 (default 999) wird zu "-"
        assert result[0]["effects"][20] == "-"


# =============================================================================
# Slice 3: API-Integration Tests
# =============================================================================

class TestEffectModeAPI:
    """Tests fuer effect_mode und enable_override in POST /generate (REQ-5016/5021)."""

    def test_generate_with_effect_mode_text(self, auth_client):
        """REQ-5016: POST /generate mit effect_mode="text"."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"EffectText_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        # Erstelle Ursachen und Wirkungen mit Werten
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"C1_{suffix}", "category_type": "cause", "order_index": 0},
        )
        cat_resp = auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"E1_{suffix}", "category_type": "effect", "order_index": 0},
        )
        assert cat_resp.status_code == 200
        e1_id = cat_resp.json()["id"]

        # Fuege Werte hinzu
        for val in ["Genehmigen", "Ablehnen"]:
            auth_client.post(
                f"/api/categories/{e1_id}/values",
                json={"value": val, "allowed": True, "vtype": "string"},
            )

        # Generiere mit effect_mode="text"
        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "effect_mode": "text",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "effects" in data
        assert len(data["effects"]) == 1
        assert "values" in data["effects"][0]

    def test_generate_with_effect_mode_binary(self, auth_client):
        """REQ-5016: POST /generate mit effect_mode="binary" (Default)."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"EffectBinary_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"C1_{suffix}", "category_type": "cause", "order_index": 0},
        )
        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"E1_{suffix}", "category_type": "effect", "order_index": 0},
        )

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "effect_mode": "binary",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "effects" in data
        assert len(data["effects"]) == 1
        # Im binary-Modus: kein values-Feld
        assert "values" not in data["effects"][0]

    def test_generate_with_enable_override(self, auth_client):
        """REQ-5021: POST /generate mit enable_override=True."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"Override_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

        auth_client.post(
            f"/api/projects/{pid}/categories",
            json={"name": f"C1_{suffix}", "category_type": "cause", "order_index": 0},
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

        resp = auth_client.post(
            "/api/decision-table/generate",
            json={
                "project_id": pid,
                "priorities": {str(e1_id): 1, str(e2_id): 2},
                "enable_override": True,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "rules" in data
        assert len(data["rules"]) == 2

    def test_generate_default_no_override(self, auth_client):
        """REQ-5021: POST /generate ohne enable_override -> Default False."""
        suffix = _unique_suffix()
        project = auth_client.post("/api/projects", json={"name": f"NoOverride_{suffix}"})
        assert project.status_code == 200, project.text
        pid = project.json()["id"]

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
            json={
                "project_id": pid,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "rules" in data
        assert len(data["rules"]) == 2