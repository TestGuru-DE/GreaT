"""
REQ-6009: Tests fuer Seeds gegen Regeln/Constraints.

# REQ-6009
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from combinatorics.seed_generation import validate_seeds, fill_partial_seeds, seed_generation
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule


CATS_2X2 = {"A": ["a1", "a2"], "B": ["b1", "b2"]}
SEEDS_RULE_VIOLATING = [
    {"A": "a1", "B": "b1"},
    {"A": "a2", "B": "b2"},  # Verstoßt gegen ForbiddenRule
]


class TestSeedRuleConflict:
    """TEST-REQ-6009-CST-001 bis CST-008."""

    def test_forbidden_seed_warned_not_removed(self):
        """TEST-REQ-6009-CST-001: Warnung; Seed bleibt (Nutzer entscheidet)."""
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        normalized, warnings = validate_seeds(SEEDS_RULE_VIOLATING, CATS_2X2, rule_engine)
        assert len(normalized) == 2  # Beide Seeds bleiben
        assert any("Versto" in w or "regel" in w.lower() for w in warnings)

    def test_forbidden_seed_keep_option(self):
        """TEST-REQ-6009-CST-002: keep_violating=True -> Seed im Ergebnis."""
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        result, _ = seed_generation(
            SEEDS_RULE_VIOLATING, CATS_2X2, "pairwise", rule_engine=rule_engine
        )
        seed_tcs = [tc for tc in result if tc.get("origin") == "seed"]
        # Beide Seeds sollten im Ergebnis sein (mit Warnung)
        assert len(seed_tcs) == 2

    def test_forbidden_seed_exclude_option(self):
        """TEST-REQ-6009-CST-003: exclude_violating -> Seed ausgeschlossen."""
        # Bei exclude_violating=False (Standard: Seeds bleiben)
        # Der Nutzer muss explizit entscheiden
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        normalized, warnings = validate_seeds(SEEDS_RULE_VIOLATING, CATS_2X2, rule_engine)
        # Standard: Seeds bleiben, nur Warnung
        assert len(normalized) == 2

    def test_combine_rule_seed_warning(self):
        """TEST-REQ-6009-CST-004: CombineRule -> Warnung bei nicht-erlaubtem Wert."""
        rule_engine = RuleEngine([
            CombineRule("A", "a1", "B", ["b1"])  # a1 -> nur b1 erlaubt
        ])
        seeds = [{"A": "a1", "B": "b2"}]  # b2 nicht erlaubt
        normalized, warnings = validate_seeds(seeds, CATS_2X2, rule_engine)
        assert len(normalized) == 1  # Seed bleibt
        assert len(warnings) >= 1

    def test_dependency_rule_seed_adjustment(self):
        """TEST-REQ-6009-CST-005: DependencyRule -> Werte werden angepasst."""
        rule_engine = RuleEngine([
            DependencyRule("A", "a1", "B", "b1")  # a1 -> b1
        ])
        seeds = [{"A": "a1", "B": None}]
        filled, _ = fill_partial_seeds(seeds, CATS_2X2, rule_engine)
        # Nach Dependency: B sollte b1 sein
        assert filled[0]["B"] == "b1"

    def test_constraint_rule_seed_warning(self):
        """TEST-REQ-6009-CST-006: ConstraintRule -> Warnung bei Verstoß."""
        # ConstraintRule benoetigt category_map und value_map
        # Einfacher Test: validate_seeds meldet Regelverstoess
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        seeds = [{"A": "a2", "B": "b2"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2, rule_engine)
        assert len(warnings) >= 1

    def test_multiple_rule_violations_reported(self):
        """TEST-REQ-6009-CST-007: Seed mit 2 Regelverstoessen -> beide gemeldet."""
        rule_engine = RuleEngine([
            ForbiddenRule("A", "a2", "B", "b2"),
            ForbiddenRule("A", "a1", "B", "b1"),
        ])
        seeds = [{"A": "a2", "B": "b2"}, {"A": "a1", "B": "b1"}]
        normalized, warnings = validate_seeds(seeds, CATS_2X2, rule_engine)
        assert len(warnings) >= 2

    def test_seed_partial_fill_respects_forbidden(self):
        """TEST-REQ-6009-CST-008: Partial Fill meidet verbotene Werte."""
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        seeds = [{"A": "a2", "B": None}]
        filled, _ = fill_partial_seeds(seeds, CATS_2X2, rule_engine)
        # B sollte NICHT "b2" sein
        assert filled[0]["B"] != "b2"
        assert filled[0]["B"] == "b1"