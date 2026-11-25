"""IPOG-Pairwise: Groesse, Abdeckung und Laufzeit (BUG B-02, K-03).

Die Grenzen sind die Akzeptanzkriterien und werden exakt geprueft
(frueher stand im Kommentar "<= 60", geprueft wurde aber "<= 1000").
"""
import itertools
import time
import uuid

import pytest

from combinatorics import ipo
from core.rules.rule_engine import ForbiddenRule, RuleEngine


def _model(sizes):
    return {f"K{i:02d}": [f"v{i}_{j}" for j in range(s)] for i, s in enumerate(sizes)}


def _pair_coverage(cases, cats, valid=lambda a: True):
    keys = list(cats)
    possible, covered = set(), set()
    for i, j in itertools.combinations(keys, 2):
        for x in cats[i]:
            for y in cats[j]:
                if valid({i: x, j: y}):
                    possible.add((i, x, j, y))
    for c in cases:
        for i, j in itertools.combinations(keys, 2):
            covered.add((i, c[i], j, c[j]))
    return len(possible & covered) / len(possible)


# (Modell, max. Testfaelle, max. Sekunden). Theoretisches Minimum = Produkt der
# beiden groessten Werteanzahlen. 50x5: Grenze 100 statt urspruenglich
# geschaetzter 80 (gemessen 93, siehe Commit-Beschreibung).
LIMITS = [
    ("3x3", [3] * 3, 10, 0.5),
    ("4x3", [3] * 4, 12, 0.5),
    ("8x6", [6] * 8, 60, 2.0),
    ("10x10", [10] * 10, 180, 3.0),
    ("20x10", [10] * 20, 260, 10.0),
    ("50x5", [5] * 50, 100, 10.0),
    ("gemischt", [2, 3, 4, 5, 10, 2, 3], 70, 1.0),
]


@pytest.mark.parametrize("name,sizes,max_cases,max_seconds", LIMITS, ids=[x[0] for x in LIMITS])
def test_pairwise_size_coverage_and_time(name, sizes, max_cases, max_seconds):
    cats = _model(sizes)
    start = time.perf_counter()
    result = ipo.generate(cats)
    elapsed = time.perf_counter() - start
    assert len(result) <= max_cases, f"{name}: {len(result)} Testfaelle (Grenze {max_cases})"
    assert _pair_coverage(result, cats) == 1.0, f"{name}: Paarabdeckung unvollstaendig"
    assert elapsed < max_seconds, f"{name}: {elapsed:.2f}s (Grenze {max_seconds}s)"
    assert all(set(tc) == set(cats) for tc in result), "jeder Testfall belegt alle Kategorien"


def test_pairwise_small_deterministic():
    """IPOG liefert bei gleichen Eingaben immer gleiche Ausgabe."""
    cats = {"A": ["a1", "a2", "a3"], "B": ["b1", "b2"], "C": ["c1", "c2", "c3"]}
    assert ipo.generate(cats) == ipo.generate(cats)


@pytest.mark.parametrize("seed", range(30))
def test_pairwise_random_models_full_coverage(seed):
    import random
    rng = random.Random(seed)
    cats = _model([rng.randint(1, 7) for _ in range(rng.randint(2, 12))])
    result = ipo.generate(cats)
    assert _pair_coverage(result, cats) == 1.0
    # Plausibilitaet: nie groesser als das Doppelte des theoretischen Minimums + Puffer
    sizes = sorted((len(v) for v in cats.values()), reverse=True)
    assert len(result) <= 2 * sizes[0] * sizes[1] + 10


def test_pairwise_with_constraints_covers_all_possible_pairs_and_no_violation():
    """BUG K-03: Mit Regeln fehlten moegliche Paare (67/69)."""
    cats = {
        "Zahlart": ["Rechnung", "Karte", "PayPal"],
        "Land": ["DE", "AT", "CH"],
        "Versand": ["Standard", "Express"],
        "Kunde": ["Neu", "Bestand"],
    }
    engine = RuleEngine([
        ForbiddenRule("Zahlart", "Rechnung", "Land", "CH"),
        ForbiddenRule("Land", "CH", "Versand", "Express"),
        ForbiddenRule("Zahlart", "PayPal", "Kunde", "Neu"),
    ])
    result = ipo.generate(cats, rule_engine=engine)
    assert all(engine.is_combination_valid(tc) for tc in result), "Regelverstoss"
    assert _pair_coverage(result, cats, engine.is_combination_valid) == 1.0


def test_pairwise_api_20x10_complete_without_truncation(auth_client):
    """BUG B-02: Ueber die API wurde auf 1000 gekappt -> nur 10,9 % Paarabdeckung."""
    pid = auth_client.post("/api/projects", json={"name": f"PW-{uuid.uuid4().hex[:6]}"}).json()["id"]
    cats = {}
    for i in range(20):
        cid = auth_client.post(f"/api/projects/{pid}/categories", json={"name": f"K{i:02d}"}).json()["id"]
        cats[f"K{i:02d}"] = []
        for j in range(10):
            auth_client.post(f"/api/categories/{cid}/values", json={"value": f"v{i}_{j}"})
            cats[f"K{i:02d}"].append(f"v{i}_{j}")
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "pairwise"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["truncated"] is False
    assert body["count"] <= 260
    tcs = auth_client.get(f"/api/generations/{body['generation_id']}/testcases").json()["testcases"]
    assert _pair_coverage([t["assignments"] for t in tcs], cats) == 1.0
