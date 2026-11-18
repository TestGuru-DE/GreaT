"""
REQ-6001: Tests fuer dreiwertige Logik (3VL) Evaluator.

Basierend auf der Spezifikation in documentation/3vl-spec-req6001.md.
Testet T01-T27 aus der Test-Fall-Spezifikation.
"""
import pytest

from app.constraints.evaluator_3vl import (
    evaluate_3vl,
    check_constraint,
    check_all_constraints,
)


# ====================================================================
# T01-T06: Atomare Operatoren
# ====================================================================

class TestAtomicOperators:
    """T01-T06: Atomare Operatoren (eq, ne, in, not_in) mit 3VL."""

    def test_t01_eq_match(self):
        """T01: eq – Wert stimmt ueberein -> True."""
        ast = {"op": "eq", "category_id": 1, "value_id": 5}
        assignment = {1: 5}
        assert evaluate_3vl(ast, assignment) is True

    def test_t02_eq_no_match(self):
        """T02: eq – Wert stimmt nicht ueberein -> False."""
        ast = {"op": "eq", "category_id": 1, "value_id": 5}
        assignment = {1: 3}
        assert evaluate_3vl(ast, assignment) is False

    def test_t03_eq_unknown(self):
        """T03: eq – Kategorie nicht gesetzt -> None."""
        ast = {"op": "eq", "category_id": 1, "value_id": 5}
        assignment = {}  # Kategorie 1 nicht gesetzt
        assert evaluate_3vl(ast, assignment) is None

    def test_t04_in_match(self):
        """T04: in – Wert in Menge -> True."""
        ast = {"op": "in", "category_id": 1, "value_ids": [2, 5, 8]}
        assignment = {1: 5}
        assert evaluate_3vl(ast, assignment) is True

    def test_t05_in_no_match(self):
        """T05: in – Wert nicht in Menge -> False."""
        ast = {"op": "in", "category_id": 1, "value_ids": [2, 5, 8]}
        assignment = {1: 3}
        assert evaluate_3vl(ast, assignment) is False

    def test_t06_in_unknown(self):
        """T06: in – Kategorie nicht gesetzt -> None."""
        ast = {"op": "in", "category_id": 1, "value_ids": [2, 5, 8]}
        assignment = {}
        assert evaluate_3vl(ast, assignment) is None


# ====================================================================
# T07-T14: Logische Verknuepfungen
# ====================================================================

class TestLogicalConnectives:
    """T07-T14: and, or, not mit 3VL."""

    def test_t07_and_true_true(self):
        """T07: and(T, T) -> T."""
        ast = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5, 2: 10}
        assert evaluate_3vl(ast, assignment) is True

    def test_t08_and_true_false(self):
        """T08: and(T, F) -> F."""
        ast = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5, 2: 3}
        assert evaluate_3vl(ast, assignment) is False

    def test_t09_and_true_unknown(self):
        """T09: and(T, U) -> U (nicht F!)."""
        ast = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5}  # Kategorie 2 nicht gesetzt
        assert evaluate_3vl(ast, assignment) is None

    def test_t10_or_false_false(self):
        """T10: or(F, F) -> F."""
        ast = {
            "op": "or",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 3, 2: 7}
        assert evaluate_3vl(ast, assignment) is False

    def test_t11_or_true_false(self):
        """T11: or(T, F) -> T."""
        ast = {
            "op": "or",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5, 2: 7}
        assert evaluate_3vl(ast, assignment) is True

    def test_t12_or_false_unknown(self):
        """T12: or(F, U) -> U."""
        ast = {
            "op": "or",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 5},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 3}  # Kategorie 2 nicht gesetzt
        assert evaluate_3vl(ast, assignment) is None

    def test_t13_not_true(self):
        """T13: not(T) -> F."""
        ast = {
            "op": "not",
            "arg": {"op": "eq", "category_id": 1, "value_id": 5},
        }
        assignment = {1: 5}
        assert evaluate_3vl(ast, assignment) is False

    def test_t14_not_unknown(self):
        """T14: not(U) -> U."""
        ast = {
            "op": "not",
            "arg": {"op": "eq", "category_id": 1, "value_id": 5},
        }
        assignment = {}  # Kategorie 1 nicht gesetzt
        assert evaluate_3vl(ast, assignment) is None


# ====================================================================
# T15-T18: Forbid-Constraints
# ====================================================================

class TestForbidConstraints:
    """T15-T18: forbid-Constraints (NICHT Bedingung)."""

    def test_t15_forbid_violated(self):
        """T15: forbid, condition=T -> verletzt (False)."""
        constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
        }
        assignment = {1: 5}
        assert check_constraint(constraint, assignment) is False

    def test_t16_forbid_not_violated(self):
        """T16: forbid, condition=F -> nicht verletzt (True)."""
        constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
        }
        assignment = {1: 3}
        assert check_constraint(constraint, assignment) is True

    def test_t17_forbid_unknown(self):
        """T17: forbid, condition=U -> behalten (True, AK-6)."""
        constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
        }
        assignment = {}  # Kategorie 1 nicht gesetzt
        assert check_constraint(constraint, assignment) is True

    def test_t18_forbid_and_partial(self):
        """T18: forbid mit AND, partieller Testfall -> behalten."""
        constraint = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 5},
                    {"op": "eq", "category_id": 2, "value_id": 10},
                ],
            },
        }
        assignment = {1: 5}  # Nur Kategorie 1 gesetzt, Kategorie 2 fehlt
        # and(T, U) = U -> forbid(U) = True (behalten)
        assert check_constraint(constraint, assignment) is True


# ====================================================================
# T19-T24: Implies-Constraints
# ====================================================================

class TestImpliesConstraints:
    """T19-T24: implies-Constraints (WENN Bedingung DANN Folge)."""

    def test_t19_implies_satisfied(self):
        """T19: implies, condition=T, consequence=T -> nicht verletzt."""
        constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
        }
        assignment = {1: 5, 2: 10}
        assert check_constraint(constraint, assignment) is True

    def test_t20_implies_violated(self):
        """T20: implies, condition=T, consequence=F -> verletzt."""
        constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
        }
        assignment = {1: 5, 2: 3}
        assert check_constraint(constraint, assignment) is False

    def test_t21_implies_condition_false(self):
        """T21: implies, condition=F -> irrelevant (True)."""
        constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
        }
        assignment = {1: 3, 2: 7}
        assert check_constraint(constraint, assignment) is True

    def test_t22_implies_condition_unknown(self):
        """T22: implies, condition=U -> behalten (True, AK-6)."""
        constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
        }
        assignment = {}  # Keine Kategorie gesetzt
        assert check_constraint(constraint, assignment) is True

    def test_t23_implies_consequence_unknown(self):
        """T23: implies, condition=T, consequence=U -> behalten (True)."""
        constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
        }
        assignment = {1: 5}  # Nur condition gesetzt, consequence unbekannt
        # AK-6: consequence=U -> behalten (nicht sicher verletzt)
        assert check_constraint(constraint, assignment) is True

    def test_t24_implies_complex(self):
        """T24: implies mit komplexer condition/consequence."""
        constraint = {
            "kind": "implies",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 5},
                    {"op": "ne", "category_id": 2, "value_id": 3},
                ],
            },
            "consequence": {
                "op": "in",
                "category_id": 3,
                "value_ids": [10, 20, 30],
            },
        }
        assignment = {1: 5, 2: 7, 3: 20}
        assert check_constraint(constraint, assignment) is True


# ====================================================================
# T25-T27: Komplexe verschachtelte Beispiele
# ====================================================================

class TestComplexCases:
    """T25-T27: Komplexe verschachtelte Constraints."""

    def test_t25_nested_forbid(self):
        """T25: Verschachteltes forbid mit not/or/and."""
        constraint = {
            "kind": "forbid",
            "condition": {
                "op": "not",
                "arg": {
                    "op": "or",
                    "args": [
                        {"op": "eq", "category_id": 1, "value_id": 5},
                        {"op": "eq", "category_id": 2, "value_id": 10},
                    ],
                },
            },
        }
        # not(or(T, F)) = not(T) = F -> forbid(F) = True (behalten)
        assignment = {1: 5, 2: 3}
        assert check_constraint(constraint, assignment) is True

    def test_t26_all_constraints_pass(self):
        """T26: check_all_constraints – alle Constraints gueltig."""
        constraints = [
            {
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 99},
            },
            {
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 2, "value_id": 5},
                "consequence": {"op": "ne", "category_id": 3, "value_id": 0},
            },
        ]
        assignment = {1: 5, 2: 5, 3: 10}
        assert check_all_constraints(constraints, assignment) is True

    def test_t27_all_constraints_one_fail(self):
        """T27: check_all_constraints – ein Constraint verletzt."""
        constraints = [
            {
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            {
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 2, "value_id": 5},
                "consequence": {"op": "eq", "category_id": 3, "value_id": 10},
            },
        ]
        assignment = {1: 5, 2: 5, 3: 10}
        # Erstes forbid ist verletzt (category 1 == 5)
        assert check_all_constraints(constraints, assignment) is False


# ====================================================================
# Invarianten-Tests (aus 3VL-Spezifikation)
# ====================================================================

class TestInvariants:
    """Invarianten aus der 3VL-Spezifikation."""

    def test_i1_idempotenz_not(self):
        """I1: not(not(x)) == x."""
        inner = {"op": "eq", "category_id": 1, "value_id": 5}
        double_not = {"op": "not", "arg": {"op": "not", "arg": inner}}
        assignment = {1: 5}
        assert evaluate_3vl(double_not, assignment) == evaluate_3vl(inner, assignment)

    def test_i2_de_morgan_and(self):
        """I2: not(and(a,b)) == or(not(a), not(b))."""
        a = {"op": "eq", "category_id": 1, "value_id": 5}
        b = {"op": "eq", "category_id": 2, "value_id": 10}
        left = {
            "op": "not",
            "arg": {"op": "and", "args": [a, b]},
        }
        right = {
            "op": "or",
            "args": [
                {"op": "not", "arg": a},
                {"op": "not", "arg": b},
            ],
        }
        for assignment in [
            {1: 5, 2: 10},
            {1: 5, 2: 3},
            {1: 3, 2: 10},
            {1: 3, 2: 3},
            {1: 5},
            {2: 10},
            {},
        ]:
            assert evaluate_3vl(left, assignment) == evaluate_3vl(right, assignment)

    def test_i3_kurzschluss_and(self):
        """I3: and(F, ...) -> F (Kurzschluss)."""
        ast = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 999},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5, 2: None}  # Kategorie 1 != 999, Kategorie 2 nicht gesetzt
        # Fix: use correct syntax
        ast = {
            "op": "and",
            "args": [
                {"op": "eq", "category_id": 1, "value_id": 999},
                {"op": "eq", "category_id": 2, "value_id": 10},
            ],
        }
        assignment = {1: 5}  # 1!=999 -> False, 2 nicht gesetzt -> None
        # and(F, U) should short-circuit to F
        assert evaluate_3vl(ast, assignment) is False