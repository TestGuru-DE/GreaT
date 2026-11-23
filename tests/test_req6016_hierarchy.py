"""
REQ-6016: Tests fuer hierarchische Klassen (Verfeinerung im Klassifikationsbaum)

TEST-ID: TEST-REQ-6016-001 bis TEST-REQ-6016-015

Deckt ab:
- Property-Tests (Invarianten)
- Generierung (Each Choice, Linear, All, Pairwise, T-Wise)
- Coverage (REQ-6008 mit Hierarchie)
- Edge Cases (max depth, flache Projekte, zyklenfreie Hierarchie)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule
from combinatorics import coverage
from combinatorics.hierarchy_constraints import (
    generate_hierarchy_constraints,
    create_hierarchy_rule_engine,
    prepare_hierarchy_categories,
    is_valid_hierarchical_testcase,
    enforce_hierarchy,
    generate_with_hierarchy,
)
from app.models.hierarchy import (
    HierarchyDescriptor,
    HIERARCHY_NOT_APPLICABLE,
    MAX_HIERARCHY_DEPTH,
)


# ---------------------------------------------------------------------------
# Test Data: 2-level hierarchy
# ---------------------------------------------------------------------------
# Parent: PaymentMethod = [CreditCard, PayPal, None]
# Child:  CardType      = [Visa, MC, Amex, "-"]  (nur bei CreditCard aktiv)

CATEGORIES_FLAT = {
    "PaymentMethod": ["CreditCard", "PayPal", "None"],
    "Amount": ["Low", "High"],
}

CATEGORIES_WITH_CHILD = {
    "PaymentMethod": ["CreditCard", "PayPal", "None"],
    "CardType": ["Visa", "MC", "Amex", "-"],
    "Amount": ["Low", "High"],
}

# Hierarchy: CardType is child of PaymentMethod=CreditCard
HIERARCHY_2LEVEL = HierarchyDescriptor.from_categories(
    categories=CATEGORIES_WITH_CHILD,
    parent_value_ids={
        "CardType": "CreditCard",
        "Amount": None,
        "PaymentMethod": None,
    },
)


# ---------------------------------------------------------------------------
# Test Data: 3-level hierarchy
# ---------------------------------------------------------------------------
# Level 1: PaymentMethod = [CreditCard, PayPal]
# Level 2: CardType      = [Visa, MC, "-"]       (nur bei CreditCard)
# Level 3: CardFeature   = [Contactless, Chip, "-"] (nur bei Visa)

CATEGORIES_3LEVEL = {
    "PaymentMethod": ["CreditCard", "PayPal"],
    "CardType": ["Visa", "MC", "-"],
    "CardFeature": ["Contactless", "Chip", "-"],
}

HIERARCHY_3LEVEL = HierarchyDescriptor.from_categories(
    categories=CATEGORIES_3LEVEL,
    parent_value_ids={
        "PaymentMethod": None,
        "CardType": "CreditCard",
        "CardFeature": "Visa",
    },
)


# ---------------------------------------------------------------------------
# TEST-REQ-6016-001 bis 004: Property-Tests (Invarianten)
# ---------------------------------------------------------------------------

class TestHierarchyProperty:
    """Property-Tests: Invarianten fuer alle Strategien."""

    def test_no_child_without_parent(self):
        """
        TEST-REQ-6016-001: Kein Testfall enthaelt einen Unter-Wert ohne
        passenden Eltern-Wert.
        """
        result = generate_with_hierarchy(
            "each_choice", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        for tc in result:
            parent_val = tc.get("PaymentMethod")
            child_val = tc.get("CardType")
            if parent_val == "CreditCard":
                assert child_val != "-", (
                    f"Child '-' when parent active: {tc}"
                )
            else:
                assert child_val == "-", (
                    f"Child '{child_val}' when parent not active: {tc}"
                )

    def test_all_testcases_valid_hierarchically(self):
        """
        TEST-REQ-6016-002: is_valid_hierarchical_testcase() kehrt True
        fuer alle generierten Testfaelle (Pairwise).
        """
        result = generate_with_hierarchy(
            "pairwise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
            ), f"Invalid hierarchy in testcase: {tc}"

    def test_enforce_hierarchy_sets_na(self):
        """
        TEST-REQ-6016-003: enforce_hierarchy() setzt '-' bei nicht-aktivierten Kindern.
        """
        tc = {
            "PaymentMethod": "PayPal",
            "CardType": "Visa",
            "Amount": "Low",
        }
        result = enforce_hierarchy(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
        assert result["CardType"] == "-"
        assert result["PaymentMethod"] == "PayPal"

    def test_enforce_hierarchy_preserves_active_child(self):
        """
        TEST-REQ-6016-004: enforce_hierarchy() laesst aktive Kinder unveraendert.
        """
        tc = {
            "PaymentMethod": "CreditCard",
            "CardType": "Visa",
            "Amount": "High",
        }
        result = enforce_hierarchy(tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
        assert result["CardType"] == "Visa"


# ---------------------------------------------------------------------------
# TEST-REQ-6016-005 bis 009: Generierung pro Strategie
# ---------------------------------------------------------------------------

class TestHierarchyGeneration:
    """Generierung aller 5 Strategien mit Hierarchie."""

    def test_each_choice_covers_all_parent_values(self):
        """
        TEST-REQ-6016-005: Each Choice deckt alle Eltern-Werte ab,
        mit korrekten Kind-Werten.
        """
        result = generate_with_hierarchy(
            "each_choice", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        parent_values = {tc["PaymentMethod"] for tc in result}
        assert "CreditCard" in parent_values
        assert "PayPal" in parent_values
        assert "None" in parent_values

        for tc in result:
            if tc["PaymentMethod"] == "CreditCard":
                assert tc["CardType"] != "-"

    def test_linear_expansion_hierarchy(self):
        """
        TEST-REQ-6016-006: Linear Expansion mit Hierarchie-Constraints.
        """
        result = generate_with_hierarchy(
            "linear", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
            )
        assert len(result) > 0

    def test_all_combinations_hierarchy(self):
        """
        TEST-REQ-6016-007: All Combinations mit Hierarchie-Constraints.
        Nur gueltige Kombinationen duerfen im Ergebnis sein.
        """
        result = generate_with_hierarchy(
            "all_combinations", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
            )

        assert len(result) > 0

        for tc in result:
            if tc["PaymentMethod"] in ("PayPal", "None"):
                assert tc["CardType"] == "-", f"Invalid: {tc}"

    def test_pairwise_hierarchy_coverage(self):
        """
        TEST-REQ-6016-008: Pairwise deckt alle gueltigen Paare ab.
        """
        result = generate_with_hierarchy(
            "pairwise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
            )

        pairs = {(tc["PaymentMethod"], tc["CardType"]) for tc in result}

        for ct in ["Visa", "MC", "Amex"]:
            assert ("CreditCard", ct) in pairs, f"Missing pair: CreditCard + {ct}"

        for tc in result:
            if tc["PaymentMethod"] in ("PayPal", "None"):
                assert tc["CardType"] == "-"

    def test_twise_hierarchy(self):
        """
        TEST-REQ-6016-009: T-Wise (t=2) mit Hierarchie-Constraints.
        """
        result = generate_with_hierarchy(
            "twise", HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD, t=2
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD
            )

        assert len(result) > 0


# ---------------------------------------------------------------------------
# TEST-REQ-6016-010 bis 011: Coverage mit Hierarchie
# ---------------------------------------------------------------------------

class TestHierarchyCoverage:
    """REQ-6008 + REQ-6016: Coverage-Berechnung mit Hierarchie."""

    def test_coverage_excludes_invalid_pairs(self):
        """
        TEST-REQ-6016-010: Coverage zaehlt Paare mit Unter-Kategorien
        nur in Kombination mit Eltern-Wert als "moeglich".
        """
        testcases = [
            {"PaymentMethod": "CreditCard", "CardType": "Visa", "Amount": "Low"},
            {"PaymentMethod": "CreditCard", "CardType": "MC", "Amount": "High"},
        ]

        cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)

        result = coverage.calculate_coverage(
            testcases=testcases,
            categories=cats,
            t=2,
            hierarchy=HIERARCHY_2LEVEL,
        )

        assert result.possible > 0
        assert result.covered > 0

    def test_coverage_heatmap_hierarchy(self):
        """
        TEST-REQ-6016-011: Heatmap markiert ungueltige Hierarchie-Paare
        als "excluded".
        """
        testcases = [
            {"PaymentMethod": "CreditCard", "CardType": "Visa", "Amount": "Low"},
        ]

        cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)

        heatmap = coverage.compute_heatmap(
            cat_a="PaymentMethod",
            cat_b="CardType",
            testcases=testcases,
            categories=cats,
            hierarchy=HIERARCHY_2LEVEL,
        )

        cell = heatmap.cells.get(("PayPal", "Visa"))
        assert cell is not None
        assert cell.status == "excluded", f"Expected excluded, got {cell.status}"

        cell2 = heatmap.cells.get(("CreditCard", "Visa"))
        assert cell2 is not None
        assert cell2.status == "covered", f"Expected covered, got {cell2.status}"

        cell3 = heatmap.cells.get(("CreditCard", "-"))
        assert cell3 is not None
        assert cell3.status == "excluded", (
            f"Expected excluded for active parent + N/A child, got {cell3.status}"
        )


# ---------------------------------------------------------------------------
# TEST-REQ-6016-012 bis 015: Edge Cases
# ---------------------------------------------------------------------------

class TestHierarchyEdgeCases:
    """Edge Cases und Grenzbedingungen."""

    def test_max_depth_validation(self):
        """
        TEST-REQ-6016-012: Max 3 Ebenen — 4. Ebene wirft ValueError.
        """
        cats = {
            "A": ["a1", "a2"],
            "B": ["b1", "-"],
            "C": ["c1", "-"],
            "D": ["d1", "-"],
        }
        with pytest.raises(ValueError, match="exceeds max depth"):
            HierarchyDescriptor.from_categories(
                categories=cats,
                parent_value_ids={
                    "A": None,
                    "B": "a1",
                    "C": "b1",
                    "D": "c1",
                },
            )

    def test_flat_project_unchanged(self):
        """
        TEST-REQ-6016-013: Bestehende flache Projekte (keine Hierarchie)
        bleiben unveraendert gueltig.
        """
        hierarchy = HierarchyDescriptor.from_categories(
            categories=CATEGORIES_FLAT,
            parent_value_ids={"PaymentMethod": None, "Amount": None},
        )

        result = generate_with_hierarchy(
            "each_choice", hierarchy, CATEGORIES_FLAT
        )

        assert len(result) > 0

    def test_three_level_hierarchy_generation(self):
        """
        TEST-REQ-6016-014: 3-Ebenen-Hierarchie (Parent -> Child -> Grandchild).
        """
        result = generate_with_hierarchy(
            "pairwise", HIERARCHY_3LEVEL, CATEGORIES_3LEVEL
        )

        for tc in result:
            assert is_valid_hierarchical_testcase(
                tc, HIERARCHY_3LEVEL, CATEGORIES_3LEVEL
            )

        for tc in result:
            if tc["PaymentMethod"] == "PayPal":
                assert tc["CardType"] == "-"
                assert tc["CardFeature"] == "-"

        for tc in result:
            if tc.get("CardType") == "MC":
                assert tc["CardFeature"] == "-"

    def test_hierarchy_constraint_generation(self):
        """
        TEST-REQ-6016-015: generate_hierarchy_constraints() erzeugt
        korrekte Regeln (Dependency + Forbidden).
        """
        cats = prepare_hierarchy_categories(HIERARCHY_2LEVEL, CATEGORIES_WITH_CHILD)
        rules = generate_hierarchy_constraints(HIERARCHY_2LEVEL, cats)

        assert len(rules) > 0

        dep_rules = [r for r in rules if isinstance(r, DependencyRule)]
        forb_rules = [r for r in rules if isinstance(r, ForbiddenRule)]

        assert len(dep_rules) >= 2  # PayPal->-, None->-
        assert len(forb_rules) >= 1  # CreditCard->-

        has_paypal_dep = any(
            r.if_category == "PaymentMethod"
            and r.if_value == "PayPal"
            and r.then_category == "CardType"
            and r.then_value == "-"
            for r in dep_rules
        )
        assert has_paypal_dep, "PayPal->'-' DependencyRule fehlt"

        has_cc_forbidden = any(
            r.if_category == "PaymentMethod"
            and r.if_value == "CreditCard"
            and r.then_category == "CardType"
            and r.then_value == "-"
            for r in forb_rules
        )
        assert has_cc_forbidden, "CreditCard+'-' ForbiddenRule fehlt"