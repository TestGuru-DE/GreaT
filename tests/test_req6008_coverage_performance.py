"""
REQ-6008: Abdeckungsanzeige — Performance-Tests

TEST-ID: TEST-REQ-6008-PERF-001 bis 004

Leistungsanforderungen:
- 2-wise fuer 30 Kategorien x 10 Werte x 1000 Testfaelle in < 3s
- 3-wise mit Groessenpruefung (Abbruch >5 Mio Tripel)
- Heatmap fuer ein Paar in < 1s
"""
import pytest
import time
import random
from core.rules.rule_engine import RuleEngine, ForbiddenRule


# ============================================================================
# Test-Hilfsfunktionen
# ============================================================================

def _generate_large_model(num_cats=30, vals_per_cat=10, num_testcases=1000):
    """Generiert ein groesses Modell fuer Performance-Tests."""
    rng = random.Random(42)  # Deterministisch fuer Reproduzierbarkeit

    categories = {}
    for i in range(num_cats):
        cat_name = f"Cat{i}"
        categories[cat_name] = [f"v{j}" for j in range(vals_per_cat)]

    testcases = []
    for _ in range(num_testcases):
        tc = {}
        for cat_name, vals in categories.items():
            tc[cat_name] = rng.choice(vals)
        testcases.append(tc)

    return categories, testcases


def _generate_rule_engine(num_cats=30, vals_per_cat=10, num_rules=5):
    """Generiert RuleEngine mit einigen ForbiddenRules."""
    rng = random.Random(42)
    rules = []

    for _ in range(num_rules):
        cat_a_idx = rng.randint(0, num_cats - 1)
        cat_b_idx = rng.randint(0, num_cats - 1)
        while cat_b_idx == cat_a_idx:
            cat_b_idx = rng.randint(0, num_cats - 1)

        val_a = rng.randint(0, vals_per_cat - 1)
        val_b = rng.randint(0, vals_per_cat - 1)

        rules.append(ForbiddenRule(
            f"Cat{cat_a_idx}", f"v{val_a}",
            f"Cat{cat_b_idx}", f"v{val_b}",
        ))

    return RuleEngine(rules)


# ============================================================================
# TEST-REQ-6008-PERF-001 bis 004
# ============================================================================

class TestCoveragePerformance:
    """Performance-Anforderungen aus REQ-6008."""

    def test_2wise_30x10x1000_under_3s(self):
        """TEST-REQ-6008-PERF-001: 2-wise fuer 30x10x1000 in < 3s.

        30 Kategorien, 10 Werte je, 1000 Testfaelle.
        Moegliche 2-wise-Tupel: C(30,2) * 10 * 10 = 435 * 100 = 43,500
        """
        from combinatorics.coverage import calculate_coverage

        categories, testcases = _generate_large_model(30, 10, 1000)

        start = time.perf_counter()
        result = calculate_coverage(
            testcases=testcases,
            categories=categories,
            t=2,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"2-wise calculation took {elapsed:.2f}s (limit: 3.0s)"
        assert result.possible == 43500  # C(30,2) * 10 * 10

    def test_2wise_with_rules_under_3s(self):
        """TEST-REQ-6008-PERF-002: 2-wise mit 5 ForbiddenRules in < 3s."""
        from combinatorics.coverage import calculate_coverage

        categories, testcases = _generate_large_model(30, 10, 1000)
        rule_engine = _generate_rule_engine(30, 10, 5)

        start = time.perf_counter()
        result = calculate_coverage(
            testcases=testcases,
            categories=categories,
            t=2,
            rule_engine=rule_engine,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0, f"2-wise with rules took {elapsed:.2f}s (limit: 3.0s)"
        assert result.excluded_by_rules >= 5  # Mindestens 5 Paare ausgeschlossen

    def test_3wise_size_check_aborts(self):
        """TEST-REQ-6008-PERF-003: 3-wise bei >5 Mio Tripel -> Abbruch mit Hinweis.

        30x10x10: C(30,3) * 1000 = 4060 * 1000 = 4,060,000 Tripel
        Das ist unter 5 Mio, also sollte es laufen.
        Testen wir mit 35x10: C(35,3) * 1000 = 6545 * 1000 = 6,545,000 -> Abbruch
        """
        from combinatorics.coverage import calculate_coverage

        categories, testcases = _generate_large_model(35, 10, 100)

        # 3-wise mit 35 Kategorien sollte abbrechen
        with pytest.raises(ValueError, match="[Aa]bbruch|abort|too large|limit"):
            calculate_coverage(
                testcases=testcases,
                categories=categories,
                t=3,
            )

    def test_heatmap_30x30_pair_under_1s(self):
        """TEST-REQ-6008-PERF-004: Heatmap fuer ein Paar aus 30x10 in < 1s."""
        from combinatorics.coverage import compute_heatmap

        categories, testcases = _generate_large_model(30, 10, 1000)

        start = time.perf_counter()
        result = compute_heatmap(
            cat_a="Cat0",
            cat_b="Cat1",
            testcases=testcases,
            categories=categories,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Heatmap calculation took {elapsed:.2f}s (limit: 1.0s)"
        assert len(result.rows) == 10
        assert len(result.cols) == 10
        assert len(result.cells) == 100

    def test_1wise_30x10x1000_under_1s(self):
        """TEST-REQ-6008-PERF-005: 1-wise sollte sehr schnell sein (< 1s)."""
        from combinatorics.coverage import calculate_coverage

        categories, testcases = _generate_large_model(30, 10, 1000)

        start = time.perf_counter()
        result = calculate_coverage(
            testcases=testcases,
            categories=categories,
            t=1,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"1-wise calculation took {elapsed:.2f}s (limit: 1.0s)"
        assert result.possible == 300  # 30 * 10

    def test_coverage_scaling_linear_with_testcases(self):
        """TEST-REQ-6008-PERF-006: Laufzeit skaaliert linear mit TC-Anzahl.

        1000 TCs -> T1, 2000 TCs -> ~2*T1 (grob).
        """
        from combinatorics.coverage import calculate_coverage

        categories_10, _ = _generate_large_model(10, 5, 1000)
        categories_20, _ = _generate_large_model(10, 5, 2000)

        # Gleiche Kategorien, verschiedene TC-Anzahl (gleicher Seed)
        rng = random.Random(42)
        tcs_1000 = []
        tcs_2000 = []
        for _ in range(2000):
            tc = {f"Cat{i}": rng.choice([f"v{j}" for j in range(5)]) for i in range(10)}
            if _ < 1000:
                tcs_1000.append(tc)
            tcs_2000.append(tc)

        cats = {f"Cat{i}": [f"v{j}" for j in range(5)] for i in range(10)}

        start = time.perf_counter()
        calculate_coverage(testcases=tcs_1000, categories=cats, t=2)
        t1 = time.perf_counter() - start

        start = time.perf_counter()
        calculate_coverage(testcases=tcs_2000, categories=cats, t=2)
        t2 = time.perf_counter() - start

        # 2000 TCs sollte nicht mehr als 3x so lange dauern wie 1000
        ratio = t2 / t1 if t1 > 0 else 0
        assert ratio < 3.0, f"Scaling ratio {ratio:.2f}x is too high (expected ~2x)"