"""
REQ-6009: Tests fuer seed_report.py — Ergebnisbericht.

Testet:
- seeds_count, supplemented_count, total_testcases
- coverage_before, coverage_after
- impossible_tuples
- strategy, filled_fields
"""
import pytest


# ---------------------------------------------------------------------------
# MOCK-DATEN
# ---------------------------------------------------------------------------

CATS_2X2 = {
    "A": ["a1", "a2"],
    "B": ["b1", "b2"],
}


# ---------------------------------------------------------------------------
# TestSeedReport
# ---------------------------------------------------------------------------

class TestSeedReport:

    def test_report_seeds_count(self):
        """TEST-REQ-6009-RPT-001: seeds_count == 2."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "seed"},
            {"A": "a1", "B": "b2", "origin": "supplemented"},
            {"A": "a2", "B": "b1", "origin": "supplemented"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.seeds_count == 2

    def test_report_supplemented_count(self):
        """TEST-REQ-6009-RPT-002: supplemented_count == 2."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "seed"},
            {"A": "a1", "B": "b2", "origin": "supplemented"},
            {"A": "a2", "B": "b1", "origin": "supplemented"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.supplemented_count == 2

    def test_report_coverage_before(self):
        """TEST-REQ-6009-RPT-003: 2 Seeds in 2x2 -> 50%."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "seed"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.coverage_before == 50.0, f"Got {report.coverage_before}%"

    def test_report_coverage_after(self):
        """TEST-REQ-6009-RPT-004: 2 Seeds + 2 ergaenzt -> 100%."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "seed"},
            {"A": "a1", "B": "b2", "origin": "supplemented"},
            {"A": "a2", "B": "b1", "origin": "supplemented"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.coverage_after == 100.0, f"Got {report.coverage_after}%"

    def test_report_total_testcases(self):
        """TEST-REQ-6009-RPT-006: total == 4."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "seed"},
            {"A": "a1", "B": "b2", "origin": "supplemented"},
            {"A": "a2", "B": "b1", "origin": "supplemented"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.total_testcases == 4

    def test_report_strategy(self):
        """TEST-REQ-6009-RPT-007: report.strategy == 'pairwise'."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        assert report.strategy == "pairwise"

    def test_report_to_dict(self):
        """Serialisierung als JSON-faehiges Dict."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "supplemented"},
        ]

        report = create_seed_report(testcases, CATS_2X2, strategy="pairwise")
        d = report.to_dict()

        assert "seeds_count" in d
        assert "supplemented_count" in d
        assert "coverage_before" in d
        assert "coverage_after" in d
        assert "strategy" in d

    def test_report_partial_seeds_filled(self):
        """TEST-REQ-6009-RPT-008: filled_fields pro Seed."""
        from combinatorics.seed_report import create_seed_report

        testcases = [
            {"A": "a1", "B": "b1", "origin": "seed"},
        ]

        filled_fields = [{"filled_fields": ["B"]}]
        report = create_seed_report(
            testcases, CATS_2X2, strategy="pairwise",
            filled_fields=filled_fields,
        )

        assert len(report.filled_fields) == 1
        assert "B" in report.filled_fields[0]["filled_fields"]


# ---------------------------------------------------------------------------
# TestGapFillReport
# ---------------------------------------------------------------------------

class TestGapFillReport:

    def test_gap_fill_report_before_after(self):
        """TEST-REQ-6009-RPT: coverage_before < coverage_after bei Luecken."""
        from combinatorics.seed_report import create_gap_fill_report

        old_tcs = [
            {"A": "a1", "B": "b1"},
            {"A": "a1", "B": "b2"},
            {"A": "a2", "B": "b1"},
        ]

        new_tcs = [
            {"A": "a1", "B": "b1", "origin": "seed"},
            {"A": "a1", "B": "b2", "origin": "seed"},
            {"A": "a2", "B": "b1", "origin": "seed"},
            {"A": "a2", "B": "b2", "origin": "supplemented"},
        ]

        report = create_gap_fill_report(new_tcs, old_tcs, CATS_2X2, strategy="pairwise")

        assert report.coverage_before < report.coverage_after
        assert report.coverage_after == 100.0
        assert report.seeds_count == 3
        assert report.supplemented_count == 1