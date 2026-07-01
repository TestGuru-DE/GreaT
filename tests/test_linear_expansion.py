# REQ-0803 – Lineare Expansion
# TEST-ID: TEST-COMB-004
#
# Algorithmus: Ein Basisfall (alle Standard-/ersten Werte) +
#              je ein Testfall pro abweichendem Wert (genau ein Wert weicht ab).

from combinatorics import linear_expansion


def test_linear_expansion_leer():
    """Leere Eingabe liefert leere Liste."""
    assert linear_expansion.generate({}) == []


def test_linear_expansion_eine_kategorie():
    """Eine Kategorie: Basisfall + alle weiteren Werte einzeln."""
    cats = {"Gewicht": ["500g", "1000g", "2000g"]}
    result = linear_expansion.generate(cats)
    # Basisfall: Gewicht=500g
    # Abweichung 1: Gewicht=1000g
    # Abweichung 2: Gewicht=2000g
    assert len(result) == 3
    assert result[0] == {"Gewicht": "500g"}  # Basisfall
    assert result[1] == {"Gewicht": "1000g"}
    assert result[2] == {"Gewicht": "2000g"}


def test_linear_expansion_zwei_kategorien():
    """Zwei Kategorien: Basisfall + je eine Abweichung pro nicht-Standard-Wert."""
    cats = {
        "Versandart": ["Normal", "Express", "Overnight"],
        "Gewicht":    ["Klein", "Mittel"],
    }
    result = linear_expansion.generate(cats)
    # Basisfall: Normal, Klein
    basisfall = {"Versandart": "Normal", "Gewicht": "Klein"}
    assert result[0] == basisfall
    # Abweichungen von Versandart: Express, Overnight (Gewicht = Klein = Standard)
    assert {"Versandart": "Express", "Gewicht": "Klein"} in result
    assert {"Versandart": "Overnight", "Gewicht": "Klein"} in result
    # Abweichung von Gewicht: Mittel (Versandart = Normal = Standard)
    assert {"Versandart": "Normal", "Gewicht": "Mittel"} in result


def test_linear_expansion_anzahl_testfaelle():
    """Anzahl TF = 1 + Summe aller (len(Werte)-1) je Kategorie."""
    cats = {
        "A": ["a1", "a2", "a3"],   # 2 Abweichungen
        "B": ["b1", "b2"],          # 1 Abweichung
        "C": ["c1", "c2", "c3", "c4"],  # 3 Abweichungen
    }
    result = linear_expansion.generate(cats)
    expected = 1 + (3 - 1) + (2 - 1) + (4 - 1)  # 1 + 2 + 1 + 3 = 7
    assert len(result) == expected


def test_linear_expansion_ein_wert_pro_kategorie():
    """Wenn jede Kategorie nur 1 Wert hat, gibt es nur den Basisfall."""
    cats = {"A": ["x"], "B": ["y"], "C": ["z"]}
    result = linear_expansion.generate(cats)
    assert len(result) == 1
    assert result[0] == {"A": "x", "B": "y", "C": "z"}


def test_linear_expansion_basisfall_immer_erster_eintrag():
    """Der Basisfall enthält immer den ersten Wert jeder Kategorie."""
    cats = {
        "X": ["x1", "x2"],
        "Y": ["y1", "y2", "y3"],
    }
    result = linear_expansion.generate(cats)
    assert result[0] == {"X": "x1", "Y": "y1"}


def test_linear_expansion_keine_doppelten_testfaelle():
    """Es dürfen keine doppelten Testfälle entstehen."""
    cats = {
        "A": ["a1", "a2"],
        "B": ["b1", "b2"],
    }
    result = linear_expansion.generate(cats)
    assert len(result) == len(set(frozenset(tc.items()) for tc in result))
