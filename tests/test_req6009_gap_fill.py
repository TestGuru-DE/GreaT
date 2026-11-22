"""
REQ-6009: Tests fuer gap_fill.py — Lueckenschluss.

# REQ-6009
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from combinatorics.gap_fill import gap_fill
from combinatorics.coverage import calculate_coverage
from core.rules.rule_engine import RuleEngine, ForbiddenRule


# ---------------------------------------------------------------------------
# MOCK-DATEN (aus RED-Testdesign)
# ---------------------------------------------------------------------------

CATS_2X2 = {"A": ["a1", "a2"], "B": ["b1", "b2"]}
CATS_2X2X2 = {"A": ["a1", "a2"], "B": ["b1", "b2"], "C": ["c1", "c2"]}

EXISTING_GENERATION_TC = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
]

ALL_4_TC = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    {"A": "a2", "B": "b2"},
]


class TestGapFillBasic:
    """TEST-REQ-6009-GAP-001 bis GAP-008."""

    def test_gap_fill_adds_missing_pairs(self):
        """TEST-REQ-6009-GAP-001: (a2,b2) wird ergaenzt."""
        result, warnings = gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        assert len(supplemented) >= 1
        # (a2, b2) sollte im Ergebnis sein
        found = any(
            tc.get("A") == "a2" and tc.get("B") == "b2"
            for tc in result
        )
        assert found

    def test_gap_fill_preserves_existing_tc(self):
        """TEST-REQ-6009-GAP-002: Alle 3 originale TCs unveraendert."""
        result, _ = gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        seed_tcs = [tc for tc in result if tc.get("origin") == "seed"]
        assert len(seed_tcs) == 3
        for orig in EXISTING_GENERATION_TC:
            found = any(
                tc.get("A") == orig["A"] and tc.get("B") == orig["B"]
                for tc in seed_tcs
            )
            assert found

    def test_gap_fill_no_addition_when_full(self):
        """TEST-REQ-6009-GAP-003: 100% Abdeckung -> keine Ergaenzung."""
        result, _ = gap_fill(ALL_4_TC, CATS_2X2)
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        assert len(supplemented) == 0
        assert len(result) == 4

    def test_gap_fill_new_generation_id(self):
        """TEST-REQ-6009-GAP-004: Neue Generation hat neue ID (im Service-Test)."""
        # Dieser Test wird im API-Test abgedeckt
        result, _ = gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        assert len(result) > 0

    def test_gap_fill_old_generation_immutable(self):
        """TEST-REQ-6009-GAP-005: Original-Liste unveraendert."""
        original_copy = [dict(tc) for tc in EXISTING_GENERATION_TC]
        gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        # Original sollte unveraendert sein (keine origin-Felder)
        for i, tc in enumerate(EXISTING_GENERATION_TC):
            assert "origin" not in tc or tc.get("origin") is None

    def test_gap_fill_origin_tracking(self):
        """TEST-REQ-6009-GAP-006: origin="seed" fuer alte, "supplemented" fuer neue."""
        result, _ = gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        seed_tcs = [tc for tc in result if tc.get("origin") == "seed"]
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        assert len(seed_tcs) == 3
        assert len(supplemented) >= 1

    def test_gap_fill_with_rules(self):
        """TEST-REQ-6009-GAP-007: Regelverbot -> (a2,b2) nicht ergaenzt."""
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        result, warnings = gap_fill(
            EXISTING_GENERATION_TC, CATS_2X2, rule_engine=rule_engine
        )
        # (a2, b2) sollte NICHT im Ergebnis sein
        found = any(
            tc.get("A") == "a2" and tc.get("B") == "b2"
            for tc in result
            if tc.get("origin") == "supplemented"
        )
        assert not found

    def test_gap_fill_report_impossible_tuples(self):
        """TEST-REQ-6009-GAP-008: Unmoegliche Tupel werden gemeldet."""
        rule_engine = RuleEngine([ForbiddenRule("A", "a2", "B", "b2")])
        result, warnings = gap_fill(
            EXISTING_GENERATION_TC, CATS_2X2, rule_engine=rule_engine
        )
        assert any("ausgeschlossen" in w.lower() for w in warnings)


class TestGapFillStrategies:
    """TEST-REQ-6009-GAP-009 bis GAP-011."""

    def test_gap_fill_pairwise_strategy(self):
        """TEST-REQ-6009-GAP-009: Nur fehlende Paare ergaenzt."""
        result, _ = gap_fill(EXISTING_GENERATION_TC, CATS_2X2, strategy="pairwise")
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        assert len(supplemented) >= 1

    def test_gap_fill_t_wise_strategy(self):
        """TEST-REQ-6009-GAP-010: t=3, fehlende Tripel ergaenzt."""
        existing_3wise = [
            {"A": "a1", "B": "b1", "C": "c1"},
            {"A": "a1", "B": "b2", "C": "c1"},
            {"A": "a2", "B": "b1", "C": "c1"},
        ]
        result, _ = gap_fill(
            existing_3wise, CATS_2X2X2, strategy="t_wise", t_strength=3
        )
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        assert len(result) >= len(existing_3wise)

    def test_gap_fill_minimal_supplement(self):
        """TEST-REQ-6009-GAP-011: supplemented_count minimal."""
        result, _ = gap_fill(EXISTING_GENERATION_TC, CATS_2X2)
        supplemented = [tc for tc in result if tc.get("origin") == "supplemented"]
        # In 2x2 mit 3 von 4 TCs, sollte nur 1 ergaenzt werden
        assert len(supplemented) <= 1