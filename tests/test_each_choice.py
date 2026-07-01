# REQ-0801 – Each Choice
# TEST-ID: TEST-COMB-002
#
# Each Choice: jeder Wert jeder Kategorie erscheint mindestens einmal.

from combinatorics import each_choice


def test_each_choice_leer():
    """Leere Eingabe liefert leere Liste."""
    assert each_choice.generate({}) == []


def test_each_choice_jeder_wert_mindestens_einmal():
    """Jeder Wert jeder Kategorie muss in mindestens einem Testfall vorkommen."""
    cats = {
        "Versandart": ["Normal", "Express", "Overnight"],
        "Gewicht":    ["Klein", "Mittel", "Groß"],
        "Inland":     ["True", "False"],
    }
    result = each_choice.generate(cats)
    for cat, werte in cats.items():
        vorkommen = {tc[cat] for tc in result}
        assert vorkommen >= set(werte), f"Nicht alle Werte von '{cat}' abgedeckt: {werte}"


def test_each_choice_anzahl_testfaelle():
    """Anzahl der Testfälle = max(len(Werte)) über alle Kategorien."""
    cats = {
        "A": ["a1", "a2", "a3"],  # 3
        "B": ["b1", "b2"],         # 2
        "C": ["c1"],               # 1
    }
    result = each_choice.generate(cats)
    assert len(result) == 3  # max = 3


def test_each_choice_eine_kategorie():
    """Eine Kategorie: jeder Wert genau einmal."""
    cats = {"X": ["x1", "x2", "x3"]}
    result = each_choice.generate(cats)
    assert len(result) == 3
    assert [tc["X"] for tc in result] == ["x1", "x2", "x3"]


def test_each_choice_ein_wert_pro_kategorie():
    """Wenn jede Kategorie nur 1 Wert hat, gibt es nur einen Testfall."""
    cats = {"A": ["a1"], "B": ["b1"], "C": ["c1"]}
    result = each_choice.generate(cats)
    assert len(result) == 1
    assert result[0] == {"A": "a1", "B": "b1", "C": "c1"}


def test_each_choice_werte_werden_zyklisch_verwendet():
    """Kürzere Kategorien werden zyklisch (round-robin) aufgefüllt."""
    cats = {
        "A": ["a1", "a2", "a3"],
        "B": ["b1", "b2"],
    }
    result = each_choice.generate(cats)
    assert len(result) == 3
    # B wird zyklisch: b1, b2, b1
    assert result[0]["B"] == "b1"
    assert result[1]["B"] == "b2"
    assert result[2]["B"] == "b1"


def test_each_choice_ergebnis_sind_dicts():
    """Jeder Testfall ist ein Dict mit allen Kategorien als Schlüssel."""
    cats = {"X": ["x1", "x2"], "Y": ["y1"]}
    result = each_choice.generate(cats)
    for tc in result:
        assert set(tc.keys()) == set(cats.keys())
