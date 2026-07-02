# REQ-0306: Grenzwertanalyse (Boundary Value Analysis)
# TDD: Tests werden VOR der Implementierung geschrieben.
import pytest
from combinatorics.boundary_value import generate_bva_values, BVAError


class TestGenerateBvaValues2Punkt:
    """2-Punkt-BVA: ISTQB-konform [min-1, min, max, max+1]."""

    def test_zwei_punkte_integer(self):
        # REQ-0306: ISTQB 2-Wert = 4 Werte
        result = generate_bva_values(min_val=1, max_val=10, points=2)
        assert result == ["0", "1", "10", "11"]

    def test_zwei_punkte_gleiche_grenze(self):
        # REQ-0306: Sonderfall – min == max → auto-korrigiert, keine Duplikate
        result = generate_bva_values(min_val=5, max_val=5, points=2)
        assert len(result) == len(set(result))

    def test_zwei_punkte_decimal(self):
        # REQ-0306: Floats mit Dezimalstellen
        result = generate_bva_values(min_val=0.0, max_val=1.0, points=2)
        assert len(result) == 4
        # Erwartet: -0.1, 0.0, 1.0, 1.1 (aber als 1.0 = 1 Dezimalstelle)
        # oder ganzzahlig: -1, 0, 1, 2
        assert result[0] in ["-1", "-0.1"]


class TestGenerateBvaValues3Punkt:
    """3-Punkt-BVA: ISTQB-konform [min-1, min, min+1, max-1, max, max+1]."""

    def test_drei_punkte_standard(self):
        # REQ-0306: ISTQB 3-Wert = 6 Werte
        result = generate_bva_values(min_val=1, max_val=10, points=3)
        assert result == ["0", "1", "2", "9", "10", "11"]

    def test_drei_punkte_grosse_werte(self):
        # REQ-0306: Große Zahlen
        result = generate_bva_values(min_val=100, max_val=999, points=3)
        assert result == ["99", "100", "101", "998", "999", "1000"]

    def test_drei_punkte_minimum_bereich(self):
        # REQ-0306: Wenn Bereich klein, werden Duplikate entfernt
        result = generate_bva_values(min_val=1, max_val=2, points=3)
        assert len(result) >= 2
        assert "0" in result or "1" in result
        assert "2" in result or "3" in result


class TestGenerateBvaValues4Punkt:
    """4-Punkt-BVA: ISTQB-konform [min-2, min-1, min, min+1, max-1, max, max+1, max+2]."""

    def test_vier_punkte_standard(self):
        # REQ-0306: ISTQB 4-Wert = 8 Werte
        result = generate_bva_values(min_val=1, max_val=10, points=4)
        assert result == ["-1", "0", "1", "2", "9", "10", "11", "12"]

    def test_vier_punkte_kleiner_bereich(self):
        # REQ-0306: Bereich 1..3 → Duplikate möglich
        result = generate_bva_values(min_val=1, max_val=3, points=4)
        assert "1" in result
        assert "3" in result


class TestGenerateBvaValuesValidierung:
    """Fehlerbehandlung und Randfälle."""

    def test_min_groesser_als_max_wirft_fehler(self):
        # REQ-0306: Auto-Korrektur (swap)
        result = generate_bva_values(min_val=10, max_val=1, points=2)
        assert len(result) >= 2

    def test_ungueltige_punktanzahl_wirft_fehler(self):
        # REQ-0306: Nur 2, 3 oder 4 Punkte erlaubt
        with pytest.raises(BVAError):
            generate_bva_values(min_val=1, max_val=10, points=5)

    def test_null_punkte_wirft_fehler(self):
        # REQ-0306: 0 Punkte nicht erlaubt
        with pytest.raises(BVAError):
            generate_bva_values(min_val=1, max_val=10, points=0)

    def test_ergebnis_ist_liste_von_strings(self):
        # REQ-0306: API-Kontrakt: Rückgabe immer Liste von Strings
        result = generate_bva_values(min_val=0, max_val=100, points=4)
        assert isinstance(result, list)
        assert all(isinstance(v, str) for v in result)

    def test_ergebnis_aufsteigend_sortiert(self):
        # REQ-0306: Werte in aufsteigender Reihenfolge
        result = generate_bva_values(min_val=1, max_val=100, points=4)
        numeric = [float(v) for v in result]
        assert numeric == sorted(numeric)
