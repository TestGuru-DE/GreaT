"""REQ-5003/5004/5005: Decision Table Generation Tests

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).
"""
import time

import pytest

from app.database import SessionLocal
from app.models import Category, Project
from app.services_decision_table import apply_constraints, generate_decision_table


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


class TestGenerateDecisionTable:
    """Tests fuer generate_decision_table()."""

    def test_two_causes_four_rules(self):
        """2 Ursachen -> 4 Regeln (2^2)."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_2Causes")
            _create_cause_category(db, pid, "C1", order_index=0)
            _create_cause_category(db, pid, "C2", order_index=1)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" not in result
            assert result["total_rules"] == 4
            assert len(result["rules"]) == 4
            assert len(result["causes"]) == 2
            assert len(result["effects"]) == 1
        finally:
            db.close()

    def test_three_causes_eight_rules(self):
        """3 Ursachen -> 8 Regeln (2^3)."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_3Causes")
            _create_cause_category(db, pid, "C1", order_index=0)
            _create_cause_category(db, pid, "C2", order_index=1)
            _create_cause_category(db, pid, "C3", order_index=2)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" not in result
            assert result["total_rules"] == 8
            assert len(result["rules"]) == 8
        finally:
            db.close()

    def test_causes_have_y_n_values(self):
        """Ursachen haben Y/N Werte in jeder Regel."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_YN")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" not in result
            # Jede Regel hat fuer jede Ursache entweder 'Y' oder 'N'
            for rule in result["rules"]:
                assert rule["causes"][c1_id] in ("Y", "N")

            # Bei 1 Ursache: genau 1 Regel mit Y, 1 mit N
            y_count = sum(1 for r in result["rules"] if r["causes"][c1_id] == "Y")
            n_count = sum(1 for r in result["rules"] if r["causes"][c1_id] == "N")
            assert y_count == 1
            assert n_count == 1
        finally:
            db.close()

    def test_effects_initially_none(self):
        """Wirkungen sind initial None (leer)."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_EffectsNone")
            _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" not in result
            for rule in result["rules"]:
                assert rule["effects"][e1_id] is None
        finally:
            db.close()

    def test_zero_causes_error(self):
        """0 Ursachen -> Fehlermeldung."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_NoCauses")
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" in result
            assert result["rules"] == []
            assert result["total_rules"] == 0
        finally:
            db.close()

    def test_zero_effects_error(self):
        """0 Wirkungen -> Fehlermeldung."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_NoEffects")
            _create_cause_category(db, pid, "C1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" in result
            assert result["rules"] == []
            assert result["total_rules"] == 0
        finally:
            db.close()

    def test_max_testcases_limit_respected(self, monkeypatch):
        """Max-Testfaelle-Limit wird respektiert."""
        monkeypatch.setenv("GREAT_MAX_TESTCASES", "4")

        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_Limit")
            # 3 Ursachen = 8 Kombinationen, aber Limit=4
            _create_cause_category(db, pid, "C1", order_index=0)
            _create_cause_category(db, pid, "C2", order_index=1)
            _create_cause_category(db, pid, "C3", order_index=2)
            _create_effect_category(db, pid, "E1", order_index=0)

            result = generate_decision_table(db, pid)

            assert "error" in result
            assert result["rules"] == []
            assert result["total_rules"] == 0
            assert "8" in result["error"]  # 2^3 = 8
        finally:
            db.close()

    def test_one_cause_two_effects(self):
        """1 Ursache, 2 Wirkungen -> 2 Regeln, beide Wirkungen None."""
        db = SessionLocal()
        try:
            pid = _create_test_project(db, "DT_1C2E")
            c1_id = _create_cause_category(db, pid, "C1", order_index=0)
            e1_id = _create_effect_category(db, pid, "E1", order_index=0)
            e2_id = _create_effect_category(db, pid, "E2", order_index=1)

            result = generate_decision_table(db, pid)

            assert "error" not in result
            assert result["total_rules"] == 2
            assert len(result["causes"]) == 1
            assert len(result["effects"]) == 2

            for rule in result["rules"]:
                assert rule["causes"][c1_id] in ("Y", "N")
                assert rule["effects"][e1_id] is None
                assert rule["effects"][e2_id] is None
        finally:
            db.close()


class TestApplyConstraints:
    """Tests fuer apply_constraints()."""

    def _make_rules(self, cause_ids, effect_ids):
        """Erstellt Test-Regeln mit allen Y/N Kombinationen."""
        import itertools

        rules = []
        for i, combo in enumerate(itertools.product(["Y", "N"], repeat=len(cause_ids)), 1):
            rule = {
                "id": i,
                "causes": {cid: val for cid, val in zip(cause_ids, combo)},
                "effects": {eid: None for eid in effect_ids},
            }
            rules.append(rule)
        return rules

    def test_constraint_e_exclusive(self):
        """Constraint E (Exclusive) filtert korrekt: max 1 cause can be Y."""
        rules = self._make_rules([1, 2], [10])
        # 4 rules: YY, YN, NY, NN
        # E: max 1 Y -> YN, NY, NN remain (3 rules)
        result = apply_constraints(rules, [{"type": "E", "causes": [1, 2]}])
        assert len(result) == 3
        # YY should be filtered out
        for r in result:
            y_count = sum(1 for c_id in [1, 2] if r["causes"][c_id] == "Y")
            assert y_count <= 1

    def test_constraint_o_one_and_only_one(self):
        """Constraint O (One-and-Only-One) filtert korrekt: exactly 1 cause must be Y."""
        rules = self._make_rules([1, 2], [10])
        # 4 rules: YY, YN, NY, NN
        # O: exactly 1 Y -> YN, NY remain (2 rules)
        result = apply_constraints(rules, [{"type": "O", "causes": [1, 2]}])
        assert len(result) == 2
        for r in result:
            y_count = sum(1 for c_id in [1, 2] if r["causes"][c_id] == "Y")
            assert y_count == 1

    def test_constraint_i_inclusive(self):
        """Constraint I (Inclusive) filtert korrekt: at least 1 cause must be Y."""
        rules = self._make_rules([1, 2], [10])
        # 4 rules: YY, YN, NY, NN
        # I: at least 1 Y -> YY, YN, NY remain (3 rules)
        result = apply_constraints(rules, [{"type": "I", "causes": [1, 2]}])
        assert len(result) == 3
        for r in result:
            assert any(r["causes"][c_id] == "Y" for c_id in [1, 2])

    def test_constraint_r_requires(self):
        """Constraint R (Requires) filtert korrekt: if c1=Y then c2=Y."""
        rules = self._make_rules([1, 2], [10])
        # 4 rules: YY, YN, NY, NN
        # R: if 1=Y then 2=Y -> YY, NY, NN remain (3 rules, YN filtered)
        result = apply_constraints(rules, [{"type": "R", "from": 1, "to": 2}])
        assert len(result) == 3
        for r in result:
            # If cause 1 is Y, cause 2 must also be Y
            if r["causes"][1] == "Y":
                assert r["causes"][2] == "Y"

    def test_constraint_m_mask(self):
        """Constraint M (Mask) setzt korrekt: if effect1=X then effect2=None."""
        rules = [
            {"id": 1, "causes": {1: "Y"}, "effects": {10: "X", 20: "Y"}},
            {"id": 2, "causes": {1: "N"}, "effects": {10: "N", 20: "Y"}},
        ]
        result = apply_constraints(rules, [{"type": "M", "from": 10, "to": 20}])
        assert len(result) == 2
        # Rule 1: effect 10=X -> effect 20 should be None
        assert result[0]["effects"][20] is None
        # Rule 2: effect 10=N -> effect 20 unchanged
        assert result[1]["effects"][20] == "Y"

    def test_no_constraints_returns_all(self):
        """Ohne Constraints werden alle Regeln zurueckgegeben."""
        rules = self._make_rules([1, 2], [10])
        result = apply_constraints(rules, [])
        assert len(result) == 4

    def test_multiple_constraints_combined(self):
        """Multiple Constraints werden kombiniert angewendet."""
        rules = self._make_rules([1, 2, 3], [10])
        # 8 rules
        # E on [1, 2]: max 1 of 1,2 is Y -> 4 rules remain
        # I on [3]: at least 1 of 3 is Y -> further filter
        result = apply_constraints(
            rules,
            [
                {"type": "E", "causes": [1, 2]},
                {"type": "I", "causes": [3]},
            ],
        )
        # After E: rules where at most 1 of (1,2) is Y
        # After I: rules where cause 3 is Y
        # Remaining: (N,N,Y), (Y,N,Y), (N,Y,Y) = 3 rules
        assert len(result) == 3
        for r in result:
            y_12 = sum(1 for c_id in [1, 2] if r["causes"][c_id] == "Y")
            assert y_12 <= 1
            assert r["causes"][3] == "Y"