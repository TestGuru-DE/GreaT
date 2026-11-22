"""
REQ-6008: Abdeckungsanzeige als Matrix/Heatmap — Unit-Tests fuer coverage.py

TEST-ID: TEST-REQ-6008-001 bis TEST-REQ-6008-040

Zuerst RED: Alle Tests failen, weil combinatorics.coverage noch nicht existiert.
Dann GREEN: Implementierung in src/combinatorics/coverage.py.
"""
import pytest
from itertools import combinations, product
from core.rules.rule_engine import RuleEngine, ForbiddenRule, DependencyRule, CombineRule


# ============================================================================
# MOCK-DATEN
# ============================================================================

# Einfaches 2x2 Modell
CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}

TC_2X2_FULL = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    {"A": "a2", "B": "b2"},
]

TC_2X2_MISSING_ONE = [
    {"A": "a1", "B": "b1"},
    {"A": "a1", "B": "b2"},
    {"A": "a2", "B": "b1"},
    # (a2, b2) fehlt
]

TC_2X2_SINGLE = [
    {"A": "a1", "B": "b1"},
]

# 3-Kategorien 2x2x2
CATS_2X2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
    "C": ["c1", "c2"],
}

TC_2X2X2_FULL = [
    {"A": "a1", "B": "b1", "C": "c1"},
    {"A": "a1", "B": "b1", "C": "c2"},
    {"A": "a1", "B": "b2", "C": "c1"},
    {"A": "a1", "B": "b2", "C": "c2"},
    {"A": "a2", "B": "b1", "C": "c1"},
    {"A": "a2", "B": "b1", "C": "c2"},
    {"A": "a2", "B": "b2", "C": "c1"},
    {"A": "a2", "B": "b2", "C": "c2"},
]

# Modell mit Ergebnis-Kategorie
CATS_WITH_RESULT = {
    "Browser": ["Chrome", "Firefox"],
    "OS": ["Windows", "Linux"],
    "Result": ["Pass", "Fail"],
}

TC_WITH_RESULT_FULL = [
    {"Browser": "Chrome", "OS": "Windows", "Result": "Pass"},
    {"Browser": "Chrome", "OS": "Windows", "Result": "Fail"},
    {"Browser": "Chrome", "OS": "Linux", "Result": "Pass"},
    {"Browser": "Chrome", "OS": "Linux", "Result": "Fail"},
    {"Browser": "Firefox", "OS": "Windows", "Result": "Pass"},
    {"Browser": "Firefox", "OS": "Windows", "Result": "Fail"},
    {"Browser": "Firefox", "OS": "Linux", "Result": "Pass"},
    {"Browser": "Firefox", "OS": "Linux", "Result": "Fail"},
]

# Modell mit Fehlerwerten
CATS_WITH_ERROR = {
    "Browser": ["Chrome", "Firefox", "<Fehlerwert>"],
    "OS": ["Windows", "Linux"],
}

TC_WITH_ERROR = [
    {"Browser": "Chrome", "OS": "Windows"},
    {"Browser": "Chrome", "OS": "Linux"},
    {"Browser": "Firefox", "OS": "Windows"},
    {"Browser": "Firefox", "OS": "Linux"},
    {"Browser": "<Fehlerwert>", "OS": "Windows"},
    {"Browser": "<Fehlerwert>", "OS": "Linux"},
]

# 3x3 Modell fuer Bruch-Tests
CATS_3X3 = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2", "b3"],
}

TC_3X3_THREE_COVERED = [
    {"A": "a1", "B": "b1"},
    {"A": "a2", "B": "b2"},
    {"A": "a3", "B": "b3"},
]


# ============================================================================
# TEST-REQ-6008-001 bis 005: 1-Wise Coverage
# ============================================================================

class TestCoverage1Wise:
    """1-Wise: Jeder Wert jeder Kategorie mindestens einmal."""

    def test_1wise_full_coverage(self):
        """TEST-REQ-6008-001: 2x2 Modell, alle Werte abgedeckt -> 100%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_FULL,
            categories=CATS_2X2,
            t=1,
        )

        assert result.t == 1
        assert result.covered == 4       # a1, a2, b1, b2
        assert result.possible == 4
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 0
        assert result.uncovered_tuples == []

    def test_1wise_partial_coverage(self):
        """TEST-REQ-6008-002: Nur ein Testfall -> 50% (a1, b1 abgedeckt)."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_SINGLE,
            categories=CATS_2X2,
            t=1,
        )

        assert result.covered == 2       # a1, b1
        assert result.possible == 4       # a1, a2, b1, b2
        assert result.percentage == 50.0

    def test_1wise_zero_coverage(self):
        """TEST-REQ-6008-003: Keine Testfaelle -> 0%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=[],
            categories=CATS_2X2,
            t=1,
        )

        assert result.covered == 0
        assert result.possible == 4
        assert result.percentage == 0.0

    def test_1wise_empty_categories(self):
        """TEST-REQ-6008-004: Keine Kategorien -> 0/0 = 0%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=[],
            categories={},
            t=1,
        )

        assert result.covered == 0
        assert result.possible == 0
        assert result.percentage == 0.0

    def test_1wise_single_category(self):
        """TEST-REQ-6008-005: Eine Kategorie mit 2 Werten, nur 1 abgedeckt."""
        from combinatorics.coverage import calculate_coverage

        cats = {"A": ["a1", "a2"]}
        tcs = [{"A": "a1"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=1,
        )

        assert result.covered == 1
        assert result.possible == 2
        assert result.percentage == 50.0


# ============================================================================
# TEST-REQ-6008-006 bis 012: 2-Wise Coverage
# ============================================================================

class TestCoverage2Wise:
    """2-Wise: Alle Paare zwischen allen Kategorienpaaren."""

    def test_2wise_full_coverage_2x2(self):
        """TEST-REQ-6008-006: 2x2, alle 4 Paare abgedeckt -> 100%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_FULL,
            categories=CATS_2X2,
            t=2,
        )

        assert result.covered == 4
        assert result.possible == 4
        assert result.percentage == 100.0

    def test_2wise_missing_one_pair(self):
        """TEST-REQ-6008-007: 2x2, ein Paar fehlt -> 75%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            t=2,
        )

        assert result.covered == 3
        assert result.possible == 4
        assert result.percentage == 75.0
        assert len(result.uncovered_tuples) == 1

    def test_2wise_three_categories_full(self):
        """TEST-REQ-6008-008: 2x2x2, alle 12 Paare abgedeckt -> 100%.

        Paare: A-B: 4, A-C: 4, B-C: 4 = 12 gesamt.
        """
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2X2_FULL,
            categories=CATS_2X2X2,
            t=2,
        )

        assert result.covered == 12
        assert result.possible == 12
        assert result.percentage == 100.0

    def test_2wise_three_categories_partial(self):
        """TEST-REQ-6008-009: 2x2x2, nur erste 4 TCs -> 66.67%.

        Manuelle Berechnung:
        TC1: (a1,b1), (a1,c1), (b1,c1)
        TC2: (a1,b1), (a1,c2), (b1,c2)
        TC3: (a1,b2), (a1,c1), (b2,c1)
        TC4: (a1,b2), (a1,c2), (b2,c2)

        Unique A-B: (a1,b1), (a1,b2) = 2 von 4
        Unique A-C: (a1,c1), (a1,c2) = 2 von 4
        Unique B-C: (b1,c1), (b1,c2), (b2,c1), (b2,c2) = 4 von 4
        Summe: 8 von 12 = 66.67%
        """
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2X2_FULL[:4],
            categories=CATS_2X2X2,
            t=2,
        )

        assert result.covered == 8
        assert result.possible == 12
        assert abs(result.percentage - 66.67) < 0.01

    def test_2wise_empty_testcases(self):
        """TEST-REQ-6008-010: Keine Testfaelle -> 0%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=[],
            categories=CATS_2X2,
            t=2,
        )

        assert result.covered == 0
        assert result.possible == 4
        assert result.percentage == 0.0

    def test_2wise_single_value_per_category(self):
        """TEST-REQ-6008-011: 1x1 -> 1 Paar, 100%."""
        from combinatorics.coverage import calculate_coverage

        cats = {"A": ["a1"], "B": ["b1"]}
        tcs = [{"A": "a1", "B": "b1"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=2,
        )

        assert result.covered == 1
        assert result.possible == 1
        assert result.percentage == 100.0

    def test_2wise_fractional_coverage(self):
        """TEST-REQ-6008-012: 3x3, nur 3 von 9 Paaren -> 33.33%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_3X3_THREE_COVERED,
            categories=CATS_3X3,
            t=2,
        )

        assert result.covered == 3
        assert result.possible == 9
        assert abs(result.percentage - 33.33) < 0.01


# ============================================================================
# TEST-REQ-6008-013 bis 015: 3-Wise Coverage
# ============================================================================

class TestCoverage3Wise:
    """3-Wise: Alle Tripel abdecken."""

    def test_3wise_full_coverage(self):
        """TEST-REQ-6008-013: 2x2x2, alle 8 Tripel -> 100%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2X2_FULL,
            categories=CATS_2X2X2,
            t=3,
        )

        assert result.covered == 8
        assert result.possible == 8
        assert result.percentage == 100.0

    def test_3wise_partial(self):
        """TEST-REQ-6008-014: 2x2x2, nur 4 TCs -> 50%."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2X2_FULL[:4],
            categories=CATS_2X2X2,
            t=3,
        )

        assert result.covered == 4
        assert result.possible == 8
        assert result.percentage == 50.0

    def test_3wise_t_greater_than_categories(self):
        """TEST-REQ-6008-015: t=3 bei nur 2 Kategorien -> kartesisches Produkt."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_FULL,
            categories=CATS_2X2,
            t=3,
        )

        # Bei t >= n: kartesisches Produkt (alle Kombinationen)
        assert result.covered == 4
        assert result.possible == 4
        assert result.percentage == 100.0


# ============================================================================
# TEST-REQ-6008-016 bis 022: Regeln und Constraints
# ============================================================================

class TestCoverageWithRules:
    """Coverage mit Forbidden/Combine/Dependency-Regeln."""

    def test_forbidden_pair_excluded_from_possible(self):
        """TEST-REQ-6008-016: Verbotenes Paar zaehlt nicht zum Nenner.

        Regel: (A=a2, B=b2) verboten.
        Testfaelle: alle 4 Paare, aber (a2,b2) fehlt.
        Ergebnis: 3/3 = 100%, excluded=1.
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            ForbiddenRule("A", "a2", "B", "b2"),
        ])

        result = calculate_coverage(
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.covered == 3
        assert result.possible == 3      # (a2,b2) ausgeschlossen
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 1

    def test_forbidden_pair_uncovered_vs_excluded(self):
        """TEST-REQ-6008-017: Fehlendes Paar war verboten -> trotzdem 100%.

        TC_2X2_MISSING_ONE fehlt (a2,b2).
        Regel verbietet (a2,b2).
        -> Das fehlende Paar war ohnehin unmöglich.
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            ForbiddenRule("A", "a2", "B", "b2"),
        ])

        result = calculate_coverage(
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.percentage == 100.0
        assert result.excluded_by_rules == 1

    def test_combine_rule_excludes_pairs(self):
        """TEST-REQ-6008-018: Combine-Regel schliesst Paare aus.

        Regel: Wenn A=a1 -> B darf nur b1 sein.
        Also (a1, b2) ist ausgeschlossen.
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            CombineRule("A", "a1", "B", ["b1"]),
        ])

        # TC ohne (a1, b2)
        tcs_without_a1b2 = [
            {"A": "a1", "B": "b1"},
            {"A": "a2", "B": "b1"},
            {"A": "a2", "B": "b2"},
        ]

        result = calculate_coverage(
            testcases=tcs_without_a1b2,
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.covered == 3
        assert result.possible == 3      # (a1,b2) ausgeschlossen
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 1

    def test_dependency_rule_no_exclusion(self):
        """TEST-REQ-6008-019: Dependency-Regeln schliessen Tupel nicht aus.

        Dependency setzt Werte, verbietet aber keine Kombinationen.
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            DependencyRule("A", "a1", "B", "b1"),
        ])

        result = calculate_coverage(
            testcases=TC_2X2_FULL,
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.covered == 4
        assert result.possible == 4
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 0

    def test_multiple_forbidden_rules(self):
        """TEST-REQ-6008-020: Zwei verbotene Paare.

        Regel 1: (a1, b1) verboten
        Regel 2: (a2, b2) verboten
        TCs: nur (a1,b2) und (a2,b1)
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            ForbiddenRule("A", "a1", "B", "b1"),
            ForbiddenRule("A", "a2", "B", "b2"),
        ])

        tcs = [
            {"A": "a1", "B": "b2"},
            {"A": "a2", "B": "b1"},
        ]

        result = calculate_coverage(
            testcases=tcs,
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.covered == 2
        assert result.possible == 2
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 2

    def test_all_pairs_excluded_by_rules(self):
        """TEST-REQ-6008-021: Alle Paare verboten -> 0/0 = 0%."""
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            ForbiddenRule("A", "a1", "B", "b1"),
            ForbiddenRule("A", "a1", "B", "b2"),
            ForbiddenRule("A", "a2", "B", "b1"),
            ForbiddenRule("A", "a2", "B", "b2"),
        ])

        result = calculate_coverage(
            testcases=[],
            categories=CATS_2X2,
            t=2,
            rule_engine=engine,
        )

        assert result.covered == 0
        assert result.possible == 0
        assert result.percentage == 0.0
        assert result.excluded_by_rules == 4

    def test_forbidden_in_three_categories(self):
        """TEST-REQ-6008-022: Verbotenes Paar in 3-Kategorien-Modell.

        Regel: (A=a1, B=b1) verboten.
        Beeinflusst nur A-B-Paare, nicht A-C oder B-C.
        """
        from combinatorics.coverage import calculate_coverage

        engine = RuleEngine([
            ForbiddenRule("A", "a1", "B", "b1"),
        ])

        # Alle TCs außer (a1,b1,*)
        tcs = [tc for tc in TC_2X2X2_FULL
               if not (tc["A"] == "a1" and tc["B"] == "b1")]

        result = calculate_coverage(
            testcases=tcs,
            categories=CATS_2X2X2,
            t=2,
            rule_engine=engine,
        )

        # A-B: 3/3 (a1,b1 excluded), A-C: 4/4, B-C: 4/4
        assert result.covered == 11
        assert result.possible == 11
        assert result.percentage == 100.0
        assert result.excluded_by_rules == 1


# ============================================================================
# TEST-REQ-6008-023 bis 025: Ergebnis-Kategorien
# ============================================================================

class TestCoverageResultCategories:
    """Ergebnis-Kategorien (is_result=True) werden ignoriert."""

    def test_result_category_ignored_2wise(self):
        """TEST-REQ-6008-023: Result-Kategorie nicht in 2-wise.

        Nur Browser-OS-Paare zaehlen: 2*2 = 4 moeglich.
        """
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_WITH_RESULT_FULL,
            categories=CATS_WITH_RESULT,
            t=2,
            result_category_names=["Result"],
        )

        assert result.covered == 4       # Chrome/Windows, Chrome/Linux, Firefox/Windows, Firefox/Linux
        assert result.possible == 4
        assert result.percentage == 100.0

    def test_result_category_ignored_1wise(self):
        """TEST-REQ-6008-024: Result-Werte nicht in 1-wise.

        Nur Browser+OS Werte: Chrome, Firefox, Windows, Linux = 4.
        """
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_WITH_RESULT_FULL,
            categories=CATS_WITH_RESULT,
            t=1,
            result_category_names=["Result"],
        )

        assert result.covered == 4
        assert result.possible == 4
        assert result.percentage == 100.0

    def test_result_category_only_model(self):
        """TEST-REQ-6008-025: Nur Ergebnis-Kategorien -> 0/0."""
        from combinatorics.coverage import calculate_coverage

        cats = {"Result": ["Pass", "Fail"]}
        tcs = [{"Result": "Pass"}, {"Result": "Fail"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=2,
            result_category_names=["Result"],
        )

        assert result.covered == 0
        assert result.possible == 0
        assert result.percentage == 0.0


# ============================================================================
# TEST-REQ-6008-026 bis 027: Fehlerwerte
# ============================================================================

class TestCoverageErrorValues:
    """Fehlerwerte werden mitgezählt (nicht ignoriert)."""

    def test_error_values_counted_in_coverage(self):
        """TEST-REQ-6008-026: Paar mit Fehlerwert zaehlt als abgedeckt."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_WITH_ERROR,
            categories=CATS_WITH_ERROR,
            t=2,
        )

        # 3 Browser * 2 OS = 6 Paare, alle abgedeckt
        assert result.covered == 6
        assert result.possible == 6
        assert result.percentage == 100.0

    def test_error_value_partial_coverage(self):
        """TEST-REQ-6008-027: Fehlerwert-Paer fehlen -> niedrigerer Prozentsatz."""
        from combinatorics.coverage import calculate_coverage

        # Nur normale Browser, keine Fehlerwert-Kombinationen
        tcs_no_error = [
            {"Browser": "Chrome", "OS": "Windows"},
            {"Browser": "Firefox", "OS": "Linux"},
        ]

        result = calculate_coverage(
            testcases=tcs_no_error,
            categories=CATS_WITH_ERROR,
            t=2,
        )

        # Chrome/Windows, Firefox/Linux = 2 von 6
        assert result.covered == 2
        assert result.possible == 6
        assert result.percentage == 33.33


# ============================================================================
# TEST-REQ-6008-028 bis 031: Heatmap-Berechnung
# ============================================================================

class TestHeatmapCalculation:
    """compute_heatmap: Zellwerte, Symbole, Status."""

    def test_heatmap_basic_2x2(self):
        """TEST-REQ-6008-028: 2x2 Heatmap, alle Zellen covered."""
        from combinatorics.coverage import compute_heatmap

        result = compute_heatmap(
            cat_a="A",
            cat_b="B",
            testcases=TC_2X2_FULL,
            categories=CATS_2X2,
        )

        assert result.rows == ["a1", "a2"]
        assert result.cols == ["b1", "b2"]
        assert len(result.cells) == 4
        for key, cell in result.cells.items():
            assert cell.count >= 1
            assert cell.status == "covered"

    def test_heatmap_uncovered_cell(self):
        """TEST-REQ-6008-029: Zelle ohne Testfall -> status='uncovered', Symbol ✕."""
        from combinatorics.coverage import compute_heatmap

        result = compute_heatmap(
            cat_a="A",
            cat_b="B",
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
        )

        cell = result.cells[("a2", "b2")]
        assert cell.count == 0
        assert cell.status == "uncovered"

    def test_heatmap_excluded_cell(self):
        """TEST-REQ-6008-030: Durch Regel ausgeschlossen -> status='excluded', Symbol ⊘."""
        from combinatorics.coverage import compute_heatmap

        engine = RuleEngine([
            ForbiddenRule("A", "a2", "B", "b2"),
        ])

        result = compute_heatmap(
            cat_a="A",
            cat_b="B",
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            rule_engine=engine,
        )

        cell = result.cells[("a2", "b2")]
        assert cell.count == 0
        assert cell.status == "excluded"

    def test_heatmap_cell_count_multiple(self):
        """TEST-REQ-6008-031: Zelle mit mehreren Testfaellen."""
        from combinatorics.coverage import compute_heatmap

        tcs = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b1"},
            {"A": "a2", "B": "b2"},
        ]

        result = compute_heatmap(
            cat_a="A",
            cat_b="B",
            testcases=tcs,
            categories=CATS_2X2,
        )

        assert result.cells[("a1", "b1")].count == 3
        assert result.cells[("a2", "b2")].count == 1

    def test_heatmap_unknown_category_raises(self):
        """TEST-REQ-6008-032: Unbekannte Kategorie -> ValueError."""
        from combinatorics.coverage import compute_heatmap

        with pytest.raises(ValueError):
            compute_heatmap(
                cat_a="X",
                cat_b="B",
                testcases=TC_2X2_FULL,
                categories=CATS_2X2,
            )

    def test_heatmap_asymmetric_categories(self):
        """TEST-REQ-6008-033: 3x1 Heatmap."""
        from combinatorics.coverage import compute_heatmap

        cats = {"A": ["a1", "a2", "a3"], "B": ["b1"]}
        tcs = [
            {"A": "a1", "B": "b1"},
            {"A": "a2", "B": "b1"},
            {"A": "a3", "B": "b1"},
        ]

        result = compute_heatmap(
            cat_a="A",
            cat_b="B",
            testcases=tcs,
            categories=cats,
        )

        assert result.rows == ["a1", "a2", "a3"]
        assert result.cols == ["b1"]
        assert len(result.cells) == 3

    def test_heatmap_uncovered_tuples_sorted(self):
        """TEST-REQ-6008-034: uncovered_tuples sind sortiert."""
        from combinatorics.coverage import calculate_coverage

        cats = {"B": ["b1", "b2", "b3"], "A": ["a1", "a2"]}
        tcs = [{"A": "a1", "B": "b1"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=2,
        )

        # uncovered_tuples sollte sortiert sein
        assert result.uncovered_tuples == sorted(result.uncovered_tuples)


# ============================================================================
# TEST-REQ-6008-035 bis 040: Edge Cases
# ============================================================================

class TestCoverageEdgeCases:
    """Randfaelle und Sonderfaelle."""

    def test_empty_testcases_any_t(self):
        """TEST-REQ-6008-035: [] bei beliebigen Kategorien."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=[],
            categories=CATS_2X2X2,
            t=2,
        )

        assert result.covered == 0
        assert result.possible == 12
        assert result.percentage == 0.0

    def test_single_testcase_single_category(self):
        """TEST-REQ-6008-036: Ein TC, eine Kategorie, t=2 -> 0/0."""
        from combinatorics.coverage import calculate_coverage

        cats = {"A": ["a1", "a2"]}
        tcs = [{"A": "a1"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=2,
        )

        # Bei nur 1 Kategorie: keine Paare moeglich
        # (oder: Paar (A,a1) mit sich selbst? -> Nein, Paare sind zwischen *verschiedenen* Kategorien)
        assert result.covered == 0
        assert result.possible == 0
        assert result.percentage == 0.0

    def test_percentage_rounding(self):
        """TEST-REQ-6008-037: Prozentsatz auf 2 Dezimalstellen."""
        from combinatorics.coverage import calculate_coverage

        # 1/3 = 33.333...%
        cats = {"A": ["a1", "a2", "a3"], "B": ["b1"]}
        tcs = [{"A": "a1", "B": "b1"}]

        result = calculate_coverage(
            testcases=tcs,
            categories=cats,
            t=2,
        )

        assert result.covered == 1
        assert result.possible == 3
        assert abs(result.percentage - 33.33) < 0.01

    def test_duplicate_testcases_counted_once_for_coverage(self):
        """TEST-REQ-6008-038: Duplizierte TCs zaehlen nicht doppelt fuer Coverage."""
        from combinatorics.coverage import calculate_coverage

        tcs = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b1"},  # Duplikat
        ]

        result = calculate_coverage(
            testcases=tcs,
            categories=CATS_2X2,
            t=2,
        )

        # (a1,b1) ist abgedeckt, aber nur 1 von 4 Paaren
        assert result.covered == 1
        assert result.possible == 4

    def test_coverage_invariant_under_tc_reordering(self):
        """TEST-REQ-6008-039: Coverage ist unabhaengig von TC-Reihenfolge."""
        from combinatorics.coverage import calculate_coverage

        result1 = calculate_coverage(
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            t=2,
        )

        result2 = calculate_coverage(
            testcases=list(reversed(TC_2X2_MISSING_ONE)),
            categories=CATS_2X2,
            t=2,
        )

        assert result1.covered == result2.covered
        assert result1.possible == result2.possible
        assert result1.percentage == result2.percentage

    def test_coverage_with_rule_engine_none(self):
        """TEST-REQ-6008-040: rule_engine=None -> keine Ausschluesse."""
        from combinatorics.coverage import calculate_coverage

        result = calculate_coverage(
            testcases=TC_2X2_MISSING_ONE,
            categories=CATS_2X2,
            t=2,
            rule_engine=None,
        )

        assert result.excluded_by_rules == 0
        assert result.possible == 4