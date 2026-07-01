# REQ-0802 – All Combinations
# TEST-ID: TEST-COMB-003
#
# All Combinations: kartesisches Produkt aller Werte.

import itertools
from combinatorics import all_combinations


def test_all_combinations_leer():
    """Leere Eingabe liefert leere Liste."""
    assert all_combinations.generate({}) == []


def test_all_combinations_ein_wert_pro_kategorie():
    """Wenn jede Kategorie genau 1 Wert hat, gibt es genau 1 Testfall."""
    cats = {"A": ["x"], "B": ["y"], "C": ["z"]}
    result = all_combinations.generate(cats)
    assert len(result) == 1
    assert result[0] == {"A": "x", "B": "y", "C": "z"}


def test_all_combinations_kartesisches_produkt():
    """Ergebnis ist das vollständige kartesische Produkt."""
    cats = {
        "Versandart": ["Normal", "Express"],
        "Gewicht":    ["Klein", "Groß"],
    }
    result = all_combinations.generate(cats)
    assert len(result) == 4  # 2 × 2
    expected = [
        {"Versandart": "Normal", "Gewicht": "Klein"},
        {"Versandart": "Normal", "Gewicht": "Groß"},
        {"Versandart": "Express", "Gewicht": "Klein"},
        {"Versandart": "Express", "Gewicht": "Groß"},
    ]
    for tc in expected:
        assert tc in result


def test_all_combinations_drei_kategorien():
    """3 Kategorien mit 2, 3, 2 Werten: 2×3×2 = 12 Testfälle."""
    cats = {
        "A": ["a1", "a2"],
        "B": ["b1", "b2", "b3"],
        "C": ["c1", "c2"],
    }
    result = all_combinations.generate(cats)
    assert len(result) == 12


def test_all_combinations_keine_duplikate():
    """Es dürfen keine doppelten Testfälle entstehen."""
    cats = {"X": ["x1", "x2"], "Y": ["y1", "y2"]}
    result = all_combinations.generate(cats)
    as_frozensets = [frozenset(tc.items()) for tc in result]
    assert len(as_frozensets) == len(set(as_frozensets))


def test_all_combinations_alle_kombinationen_vorhanden():
    """Jede mögliche Kombination muss im Ergebnis vorhanden sein."""
    cats = {"A": ["a1", "a2", "a3"], "B": ["b1", "b2"]}
    result = all_combinations.generate(cats)
    keys = list(cats.keys())
    expected_combos = list(itertools.product(*[cats[k] for k in keys]))
    assert len(result) == len(expected_combos)
    for combo in expected_combos:
        tc = dict(zip(keys, combo))
        assert tc in result


def test_all_combinations_ergebnis_sind_dicts():
    """Jeder Testfall ist ein Dict mit allen Kategorien als Schlüssel."""
    cats = {"X": ["x1"], "Y": ["y1", "y2"]}
    result = all_combinations.generate(cats)
    for tc in result:
        assert set(tc.keys()) == set(cats.keys())
