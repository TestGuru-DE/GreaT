"""REQ-3051: Risikoabdeckung-Summe pro Generierung.

Testet die generierungsweite Risikoabdeckung als Prozentsatz.
"""
import pytest
from app.services import calculate_generation_risk_summary


def test_risk_summary_basic():
    """Grundlegende Berechnung der Risikoabdeckung."""
    testcases = [
        {"risk_coverage": 4.0},
        {"risk_coverage": 2.0},
        {"risk_coverage": 6.0},
    ]
    value_risk_map = {"A": 3.0, "B": 1.0, "C": 2.0}
    result = calculate_generation_risk_summary(testcases, value_risk_map, num_categories=2)
    
    assert result["total_risk"] == 12.0
    assert result["testcase_count"] == 3
    assert 0.0 <= result["risk_coverage_percent"] <= 100.0
    # max_per_testcase = 2 * 3.0 = 6.0
    # max_possible = 3 * 6.0 = 18.0
    # percent = 12.0 / 18.0 * 100 = 66.7 (gerundet)
    assert result["risk_coverage_percent"] == pytest.approx(66.7, abs=0.1)
    assert result["max_possible_risk"] == 18.0


def test_risk_summary_empty():
    """Leere Generierung ergibt 0% Risikoabdeckung."""
    result = calculate_generation_risk_summary([], {}, 0)
    assert result["risk_coverage_percent"] == 0.0
    assert result["testcase_count"] == 0
    assert result["total_risk"] == 0.0
    assert result["max_possible_risk"] == 0.0


def test_risk_summary_full_coverage():
    """Alle Testfälle haben maximales Risiko = 100%."""
    value_risk_map = {"A": 5.0, "B": 3.0}
    testcases = [
        {"risk_coverage": 5.0},  # max_weight pro Testcase
        {"risk_coverage": 5.0},
    ]
    # num_categories=1 → max_per_testcase = 1 * 5.0 = 5.0
    # max_possible = 2 * 5.0 = 10.0
    # total_risk = 10.0
    # percent = 10.0 / 10.0 * 100 = 100.0
    result = calculate_generation_risk_summary(testcases, value_risk_map, num_categories=1)
    assert result["risk_coverage_percent"] == 100.0
    assert result["total_risk"] == 10.0
    assert result["max_possible_risk"] == 10.0


def test_risk_summary_partial_coverage():
    """50% Risikoabdeckung."""
    value_risk_map = {"A": 10.0, "B": 5.0}
    testcases = [
        {"risk_coverage": 10.0},
        {"risk_coverage": 0.0},
    ]
    # num_categories=2 → max_per_testcase = 2 * 10.0 = 20.0
    # max_possible = 2 * 20.0 = 40.0
    # total_risk = 10.0
    # percent = 10.0 / 40.0 * 100 = 25.0
    result = calculate_generation_risk_summary(testcases, value_risk_map, num_categories=2)
    assert result["risk_coverage_percent"] == 25.0


def test_risk_summary_no_value_map():
    """Keine value_risk_map → 0% Risikoabdeckung."""
    testcases = [{"risk_coverage": 5.0}]
    result = calculate_generation_risk_summary(testcases, {}, num_categories=2)
    assert result["risk_coverage_percent"] == 0.0
    assert result["testcase_count"] == 1


def test_risk_summary_rounding():
    """Prozentsatz wird auf 1 Dezimalstelle gerundet."""
    value_risk_map = {"A": 3.0}
    testcases = [
        {"risk_coverage": 1.0},
        {"risk_coverage": 1.0},
        {"risk_coverage": 1.0},
    ]
    # max_per_testcase = 1 * 3.0 = 3.0
    # max_possible = 3 * 3.0 = 9.0
    # total_risk = 3.0
    # percent = 3.0 / 9.0 * 100 = 33.333... → 33.3
    result = calculate_generation_risk_summary(testcases, value_risk_map, num_categories=1)
    assert result["risk_coverage_percent"] == 33.3
