"""
REQ-6009: Property-Tests fuer Seed-Generierung.

# REQ-6009
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import random
import pytest
from combinatorics.seed_generation import seed_generation, fill_partial_seeds
from combinatorics.gap_fill import gap_fill
from combinatorics.coverage import calculate_coverage


def _random_model(min_cats=2, max_cats=5, min_vals=2, max_vals=4):
    """Erzeugt ein zufaelliges Modell."""
    num_cats = random.randint(min_cats, max_cats)
    cats = {}
    for i in range(num_cats):
        cat_name = f"Cat{i}"
        num_vals = random.randint(min_vals, max_vals)
        cats[cat_name] = [f"v{j}" for j in range(num_vals)]
    return cats


def _random_seeds(categories, min_seeds=1, max_seeds=5):
    """Erzeugt zufaellige Seeds."""
    num_seeds = random.randint(min_seeds, max_seeds)
    seeds = []
    cat_names = list(categories.keys())
    for _ in range(num_seeds):
        seed = {}
        for cat in cat_names:
            seed[cat] = random.choice(categories[cat])
        seeds.append(seed)
    return seeds


class TestSeedProperty:
    """TEST-REQ-6009-PROP-001 bis PROP-007."""

    def test_random_model_seeds_preserved(self):
        """TEST-REQ-6009-PROP-001: Alle Seeds (nach Auffuellung) im Ergebnis."""
        random.seed(42)
        for _ in range(20):
            categories = _random_model()
            seeds = _random_seeds(categories)
            result, _ = seed_generation(seeds, categories, "pairwise")
            seed_tcs = [tc for tc in result if tc.get("origin") == "seed"]
            # Jeder Seed sollte im Ergebnis sein
            for seed in seeds:
                found = any(
                    all(tc.get(k) == v for k, v in seed.items())
                    for tc in seed_tcs
                )
                assert found, f"Seed {seed} nicht im Ergebnis"

    def test_random_model_pair_coverage_100(self):
        """TEST-REQ-6009-PROP-002: Paarabdeckung 100% (außer regelbedingt)."""
        random.seed(43)
        for _ in range(20):
            categories = _random_model()
            seeds = _random_seeds(categories)
            result, _ = seed_generation(seeds, categories, "pairwise")
            assignments = [
                {k: v for k, v in tc.items() if k != "origin"}
                for tc in result
            ]
            cov = calculate_coverage(assignments, categories, t=2)
            assert cov.percentage == 100.0, f"Coverage {cov.percentage}% < 100%"

    def test_result_size_bounded(self):
        """TEST-REQ-6009-PROP-003: len(result) <= len(seeds) + len(pairwise)."""
        random.seed(44)
        for _ in range(20):
            categories = _random_model()
            seeds = _random_seeds(categories)
            result, _ = seed_generation(seeds, categories, "pairwise")
            # Normal pairwise ohne Seeds
            normal, _ = seed_generation([], categories, "pairwise")
            assert len(result) <= len(seeds) + len(normal), (
                f"Result {len(result)} > seeds {len(seeds)} + pairwise {len(normal)}"
            )

    def test_seeds_preserved_with_rules(self):
        """TEST-REQ-6009-PROP-004: Gueltige Seeds unveraendert mit Regeln."""
        random.seed(45)
        from core.rules.rule_engine import RuleEngine, ForbiddenRule
        for _ in range(20):
            categories = _random_model(2, 3, 2, 3)
            seeds = _random_seeds(categories, 1, 3)
            # Einfache Regel: erster Wert Cat0 + erster Wert Cat1 verboten
            cat_names = list(categories.keys())
            if len(cat_names) >= 2:
                rule_engine = RuleEngine([
                    ForbiddenRule(cat_names[0], categories[cat_names[0]][0],
                                  cat_names[1], categories[cat_names[1]][0])
                ])
            else:
                rule_engine = None
            result, _ = seed_generation(seeds, categories, "pairwise", rule_engine=rule_engine)
            seed_tcs = [tc for tc in result if tc.get("origin") == "seed"]
            assert len(seed_tcs) == len(seeds)

    def test_partial_seeds_filled_validly(self):
        """TEST-REQ-6009-PROP-005: Alle None-Werte durch gueltige Werte ersetzt."""
        random.seed(46)
        for _ in range(20):
            categories = _random_model()
            cat_names = list(categories.keys())
            # Erzeuge Seeds mit zufaelligen None-Werten
            seeds = []
            for _ in range(random.randint(1, 3)):
                seed = {}
                for cat in cat_names:
                    if random.random() < 0.5:
                        seed[cat] = None
                    else:
                        seed[cat] = random.choice(categories[cat])
                seeds.append(seed)
            filled, _ = fill_partial_seeds(seeds, categories)
            for fc in filled:
                for cat in cat_names:
                    assert fc[cat] is not None, f"None in {cat} nach Auffuellung"
                    assert fc[cat] in categories[cat], f"Ungueltiger Wert {fc[cat]} in {cat}"

    def test_gap_fill_coverage_monotonic(self):
        """TEST-REQ-6009-PROP-006: coverage_after >= coverage_before."""
        random.seed(47)
        for _ in range(20):
            categories = _random_model()
            cat_names = list(categories.keys())
            # Unvollstaendige Generierung
            num_tc = random.randint(1, 3)
            existing = []
            for _ in range(num_tc):
                tc = {}
                for cat in cat_names:
                    tc[cat] = random.choice(categories[cat])
                existing.append(tc)
            result, _ = gap_fill(existing, categories, strategy="pairwise")
            old_assignments = existing
            new_assignments = [
                {k: v for k, v in tc.items() if k != "origin"}
                for tc in result
            ]
            cov_before = calculate_coverage(old_assignments, categories, t=2)
            cov_after = calculate_coverage(new_assignments, categories, t=2)
            assert cov_after.percentage >= cov_before.percentage, (
                f"Coverage sank: {cov_before.percentage}% -> {cov_after.percentage}%"
            )

    def test_origin_consistency(self):
        """TEST-REQ-6009-PROP-007: Jeder TC hat origin; seed-TCs == seeds."""
        random.seed(48)
        for _ in range(20):
            categories = _random_model()
            seeds = _random_seeds(categories)
            result, _ = seed_generation(seeds, categories, "pairwise")
            for tc in result:
                assert tc.get("origin") in ("seed", "supplemented", "generated")
            seed_count = sum(1 for tc in result if tc.get("origin") == "seed")
            assert seed_count == len(seeds)