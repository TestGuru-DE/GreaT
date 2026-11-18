"""
REQ-6001: Tests fuer ConstraintRule in RuleEngine.

Testet die Integration von ConstraintRule (JSON-AST + 3VL) in die
bestehende RuleEngine mit ForbiddenRule, DependencyRule, CombineRule.
"""
import pytest

from core.rules.rule_engine import (
    RuleEngine,
    ForbiddenRule,
    DependencyRule,
    CombineRule,
    ConstraintRule,
)


# ====================================================================
# ConstraintRule: Einfache Tests
# ====================================================================

class TestConstraintRuleBasic:
    """Basis-Tests fuer ConstraintRule."""

    def test_forbid_simple_eq_violated(self):
        """forbid mit eq – verletzt wenn Wert stimmt."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            category_map={"Zahlart": 1},
            value_map={(1, "Rechnung"): 5},
        )
        assert cr.is_violated({"Zahlart": "Rechnung"}) is True

    def test_forbid_simple_eq_not_violated(self):
        """forbid mit eq – nicht verletzt wenn Wert anders."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            category_map={"Zahlart": 1},
            value_map={(1, "Rechnung"): 5, (1, "Lieferschein"): 6},
        )
        assert cr.is_violated({"Zahlart": "Lieferschein"}) is False

    def test_forbid_partial_unknown(self):
        """forbid mit partieller Testfall – unbekannt -> behalten."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            category_map={"Zahlart": 1},
            value_map={(1, "Rechnung"): 5},
        )
        # Kategorie nicht gesetzt -> unbekannt -> NICHT verletzt (AK-6)
        assert cr.is_violated({}) is False

    def test_implies_satisfied(self):
        """implies – condition=T, consequence=T -> nicht verletzt."""
        cr = ConstraintRule(
            expression={
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
                "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Standard"): 10},
        )
        assert cr.is_violated({"Zahlart": "Rechnung", "Versand": "Standard"}) is False

    def test_implies_violated(self):
        """implies – condition=T, consequence=F -> verletzt."""
        cr = ConstraintRule(
            expression={
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
                "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Standard"): 10, (2, "Express"): 11},
        )
        assert cr.is_violated({"Zahlart": "Rechnung", "Versand": "Express"}) is True

    def test_implies_condition_false(self):
        """implies – condition=F -> irrelevant, nicht verletzt."""
        cr = ConstraintRule(
            expression={
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
                "consequence": {"op": "eq", "category_id": 2, "value_id": 10},
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (1, "Lieferschein"): 6, (2, "Standard"): 10},
        )
        assert cr.is_violated({"Zahlart": "Lieferschein", "Versand": "Standard"}) is False


# ====================================================================
# ConstraintRule + RuleEngine Integration
# ====================================================================

class TestConstraintRuleInEngine:
    """ConstraintRule in RuleEngine integriert."""

    def test_engine_with_constraint_only(self):
        """RuleEngine mit nur ConstraintRule."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            category_map={"Zahlart": 1},
            value_map={(1, "Rechnung"): 5, (1, "Lieferschein"): 6},
        )
        engine = RuleEngine([cr])

        # Verletzter Testfall
        assert engine.is_combination_valid({"Zahlart": "Rechnung"}) is False
        # Nicht-verletzter Testfall
        assert engine.is_combination_valid({"Zahlart": "Lieferschein"}) is True
        # Partieller Testfall (unbekannt)
        assert engine.is_combination_valid({}) is True

    def test_engine_with_forbidden_and_constraint(self):
        """RuleEngine mit ForbiddenRule UND ConstraintRule."""
        fr = ForbiddenRule(
            if_category="Zahlart", if_value="Rechnung",
            then_category="Versand", then_value="Express",
        )
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {
                    "op": "and",
                    "args": [
                        {"op": "eq", "category_id": 1, "value_id": 5},
                        {"op": "eq", "category_id": 2, "value_id": 11},
                    ],
                },
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Express"): 11, (2, "Standard"): 10},
        )
        engine = RuleEngine([fr, cr])

        # Beide Regeln verbieten dieselbe Kombination
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "Express",
        }) is False

        # Keine Regel verletzt
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "Standard",
        }) is True

    def test_engine_apply_filters_constraints(self):
        """RuleEngine.apply() filtert Constraints korrekt."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
            },
            category_map={"Zahlart": 1},
            value_map={(1, "Rechnung"): 5, (1, "Lieferschein"): 6},
        )
        engine = RuleEngine([cr])

        testfaelle = [
            {"Zahlart": "Rechnung"},
            {"Zahlart": "Lieferschein"},
            {"Zahlart": "Rechnung"},
        ]
        result = engine.apply(testfaelle)
        # Nur der nicht-verletzte Testfall bleibt
        assert len(result) == 1
        assert result[0] == {"Zahlart": "Lieferschein"}

    def test_engine_partial_testcase_with_constraint(self):
        """Partieller Testfall mit Constraint (3VL)."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {
                    "op": "and",
                    "args": [
                        {"op": "eq", "category_id": 1, "value_id": 5},
                        {"op": "eq", "category_id": 2, "value_id": 11},
                    ],
                },
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Express"): 11},
        )
        engine = RuleEngine([cr])

        # Nur eine Kategorie gesetzt -> and(T, U) = U -> forbid(U) = True (behalten)
        assert engine.is_combination_valid({"Zahlart": "Rechnung"}) is True

        # Beide Kategorien gesetzt -> and(T, T) = T -> forbid(T) = False (verwerfen)
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung",
            "Versand": "Express",
        }) is False


# ====================================================================
# Komplexe Constraints
# ====================================================================

class TestComplexConstraints:
    """Komplexe verschachtelte Constraints in RuleEngine."""

    def test_nested_and_or_forbid(self):
        """Verschachteltes AND/OR in forbid."""
        cr = ConstraintRule(
            expression={
                "kind": "forbid",
                "condition": {
                    "op": "and",
                    "args": [
                        {"op": "eq", "category_id": 1, "value_id": 5},
                        {
                            "op": "or",
                            "args": [
                                {"op": "eq", "category_id": 2, "value_id": 10},
                                {"op": "eq", "category_id": 2, "value_id": 11},
                            ],
                        },
                    ],
                },
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Standard"): 10, (2, "Express"): 11},
        )
        engine = RuleEngine([cr])

        # Rechnung + Standard -> and(T, or(T,F)) = and(T,T) = T -> verletzt
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "Standard",
        }) is False

        # Rechnung + anderer Versand -> and(T, or(F,F)) = and(T,F) = F -> nicht verletzt
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "DHL",
        }) is True

    def test_implies_with_or_consequence(self):
        """implies mit ODER in consequence."""
        cr = ConstraintRule(
            expression={
                "kind": "implies",
                "condition": {"op": "eq", "category_id": 1, "value_id": 5},
                "consequence": {
                    "op": "or",
                    "args": [
                        {"op": "eq", "category_id": 2, "value_id": 10},
                        {"op": "eq", "category_id": 2, "value_id": 11},
                    ],
                },
            },
            category_map={"Zahlart": 1, "Versand": 2},
            value_map={(1, "Rechnung"): 5, (2, "Standard"): 10, (2, "Express"): 11},
        )
        engine = RuleEngine([cr])

        # condition=T, consequence=or(T,F)=T -> nicht verletzt
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "Standard",
        }) is True

        # condition=T, consequence=or(F,F)=F -> verletzt
        assert engine.is_combination_valid({
            "Zahlart": "Rechnung", "Versand": "DHL",
        }) is True  # DHL ist nicht gemappt -> consequence=None -> unbekannt -> behalten