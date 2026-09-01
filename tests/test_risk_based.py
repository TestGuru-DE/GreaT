# REQ-0805: Risikogewichtete Generierung (Risk-Based Test Case Generation)
# TDD: Tests werden VOR der Implementierung geschrieben.
import pytest
from combinatorics.risk_based import generate, compute_testcase_risk, sort_by_risk_descending


class TestRiskBasedGenerate:
    """Risikogewichtete Testfall-Generierung – REQ-0805."""

    def test_einfaches_beispiel_ohne_gewichtung(self):
        # REQ-0805: Ohne Gewichtung verhält sich risk_based wie each_choice
        categories = {
            "Farbe": [("Rot", 1), ("Blau", 1)],
            "Gewicht": [("500g", 1), ("1000g", 1)],
        }
        result = generate(categories)
        assert len(result) >= 2
        alle_werte = {v for tc in result for v in tc.values()}
        assert "Rot" in alle_werte
        assert "Blau" in alle_werte

    def test_hochrisiko_wert_erscheint_haeufiger(self):
        # REQ-0805: Wert mit risk_weight=3 erscheint öfter als Wert mit risk_weight=1
        categories = {
            "Status": [("Aktiv", 3), ("Inaktiv", 1)],
            "Typ": [("A", 1), ("B", 1)],
        }
        result = generate(categories)
        aktiv_count = sum(1 for tc in result if tc.get("Status") == "Aktiv")
        inaktiv_count = sum(1 for tc in result if tc.get("Status") == "Inaktiv")
        assert aktiv_count >= inaktiv_count

    def test_alle_werte_erscheinen_mindestens_einmal(self):
        # REQ-0805: Jeder Wert erscheint mindestens einmal (Basis Each-Choice-Abdeckung)
        categories = {
            "Farbe": [("Rot", 1), ("Blau", 2), ("Grün", 1)],
            "Größe": [("S", 1), ("L", 3)],
        }
        result = generate(categories)
        alle_werte = {v for tc in result for v in tc.values()}
        assert "Rot" in alle_werte
        assert "Blau" in alle_werte
        assert "Grün" in alle_werte
        assert "S" in alle_werte
        assert "L" in alle_werte

    def test_leere_kategorien_gibt_leere_liste(self):
        # REQ-0805: Leer-Eingabe → leere Ausgabe
        result = generate({})
        assert result == []

    def test_einzelne_kategorie(self):
        # REQ-0805: Eine Kategorie mit gewichteten Werten
        categories = {
            "Prio": [("Hoch", 3), ("Mittel", 2), ("Niedrig", 1)],
        }
        result = generate(categories)
        assert len(result) >= 3
        hoch_count = sum(1 for tc in result if tc.get("Prio") == "Hoch")
        niedrig_count = sum(1 for tc in result if tc.get("Prio") == "Niedrig")
        assert hoch_count >= niedrig_count

    def test_ergebnis_sind_dicts_mit_korrekten_schluesseln(self):
        # REQ-0805: API-Kontrakt: Liste von Dicts mit Kategorienamen als Schlüssel
        categories = {
            "A": [("x", 1)],
            "B": [("y", 2)],
        }
        result = generate(categories)
        assert isinstance(result, list)
        for tc in result:
            assert isinstance(tc, dict)
            assert "A" in tc
            assert "B" in tc

    def test_gewichtung_beeinflusst_anzahl_testfaelle(self):
        # REQ-0805: Höhere Gewichtung → mehr Testfälle als ohne Gewichtung
        categories_gewichtet = {
            "Typ": [("X", 5), ("Y", 1)],
        }
        categories_ungewichtet = {
            "Typ": [("X", 1), ("Y", 1)],
        }
        result_gew = generate(categories_gewichtet)
        result_ungew = generate(categories_ungewichtet)
        assert len(result_gew) >= len(result_ungew)


class TestComputeTestcaseRisk:
    """REQ-3034: Kumulierter Risiko-Score pro Testfall (kategorie-gescoped)."""

    def test_compute_testcase_risk_summiert_pro_kategorie_korrekt(self):
        # REQ-3034: Score = Summe der risk_weight je zugeordneter Kategorie/Wert-Kombination
        category_risk_map = {
            "Browser": [("Chrome", 3), ("Firefox", 2)],
            "OS": [("Windows", 1), ("Linux", 5)],
        }
        tc = {"Browser": "Chrome", "OS": "Linux"}
        assert compute_testcase_risk(tc, category_risk_map) == 8.0

    def test_compute_testcase_risk_fehlender_wert_ergibt_null(self):
        # REQ-3034: Unbekannter Wert/unbekannte Kategorie zaehlt als 0, kein KeyError
        category_risk_map = {
            "Browser": [("Chrome", 3)],
        }
        tc = {"Browser": "Safari", "OS": "Windows"}
        assert compute_testcase_risk(tc, category_risk_map) == 0.0

    def test_compute_testcase_risk_gleicher_wert_verschiedene_kategorien_kollidiert_nicht(self):
        # REQ-3034 Regression: kategorie-gescoptes Lookup, kein globales/flaches Dict
        # Derselbe Wert-String "A" hat in Kategorie1 Gewicht 3, in Kategorie2 Gewicht 9.
        category_risk_map = {
            "Kategorie1": [("A", 3), ("B", 1)],
            "Kategorie2": [("A", 9), ("B", 1)],
        }
        tc = {"Kategorie1": "A", "Kategorie2": "B"}
        # Erwartet: 3 (Kategorie1.A) + 1 (Kategorie2.B) = 4, NICHT 3 + 9 aus einem
        # fehlerhaften flachen Dict das "A" global auf 9 mappen wuerde.
        assert compute_testcase_risk(tc, category_risk_map) == 4.0


class TestSortByRiskDescending:
    """REQ-3034: Eigenstaendige, von generate() getrennte Risiko-Sortierung."""

    def test_sort_by_risk_descending_leere_liste_und_leere_map(self):
        assert sort_by_risk_descending([], {}) == []

    def test_sort_by_risk_descending_tie_break_original_reihenfolge(self):
        # REQ-3034: Bei Punktgleichheit gewinnt der urspruengliche Listenindex (aufsteigend)
        category_risk_map = {
            "A": [("x", 2), ("y", 2)],
        }
        testcases = [
            {"A": "x"},  # Score 2, Index 0
            {"A": "y"},  # Score 2, Index 1
        ]
        result = sort_by_risk_descending(testcases, category_risk_map)
        # Gleicher Score -> Reihenfolge bleibt wie im Original
        assert result == [{"A": "x"}, {"A": "y"}]

    def test_sort_by_risk_descending_hoechstes_risiko_zuerst(self):
        category_risk_map = {
            "Browser": [("Chrome", 3), ("Firefox", 1)],
            "OS": [("Windows", 1), ("Linux", 5)],
        }
        testcases = [
            {"Browser": "Firefox", "OS": "Windows"},  # 1 + 1 = 2
            {"Browser": "Chrome", "OS": "Linux"},      # 3 + 5 = 8
            {"Browser": "Chrome", "OS": "Windows"},    # 3 + 1 = 4
        ]
        result = sort_by_risk_descending(testcases, category_risk_map)
        assert result == [
            {"Browser": "Chrome", "OS": "Linux"},
            {"Browser": "Chrome", "OS": "Windows"},
            {"Browser": "Firefox", "OS": "Windows"},
        ]
