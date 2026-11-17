"""IPOG-Pairwise Coverage-Tests.

50 zufaellige Modelle (Seed 42, 2-12 Kategorien, 1-8 Werte).
Jedes Paar muss in mindestens einem Testfall vorkommen.
"""
import random
from itertools import combinations, product

from combinatorics import ipo


def _check_pairwise_coverage(cats: dict) -> bool:
    """Prueft, ob alle Paare zwischen allen Kategorien abgedeckt sind."""
    suite = ipo.generate(cats)
    if not suite:
        return True  # Keine Kategorien oder keine Werte → trivial

    keys = sorted(cats.keys())
    if len(keys) < 2:
        return True

    # Alle erforderlichen Paare
    required_pairs = set()
    for k1, k2 in combinations(keys, 2):
        for v1 in cats[k1]:
            for v2 in cats[k2]:
                required_pairs.add((k1, k2, v1, v2))

    # Abgedeckte Paare
    covered = set()
    for tc in suite:
        for k1, k2 in combinations(keys, 2):
            if k1 in tc and k2 in tc:
                covered.add((k1, k2, tc[k1], tc[k2]))

    missing = required_pairs - covered
    if missing:
        print(f"  Missing pairs ({len(missing)}): {sorted(missing)[:5]}...")
        return False
    return True


def test_pairwise_coverage_random_models():
    """50 zufaellige Modelle: jedes Paar muss abgedeckt sein."""
    rng = random.Random(42)
    passed = 0
    failed = 0

    for i in range(50):
        num_cats = rng.randint(2, 12)
        cats = {}
        for j in range(num_cats):
            num_vals = rng.randint(1, 8)
            cat_name = f"Cat{j}"
            cats[cat_name] = [f"v{k}" for k in range(num_vals)]

        if _check_pairwise_coverage(cats):
            passed += 1
        else:
            failed += 1
            print(f"  Model {i+1} ({num_cats} cats) FAILED")

    assert failed == 0, f"{failed}/50 models failed pairwise coverage"
    assert passed == 50, f"Only {passed}/50 models passed"