# REQ-0306: Grenzwertanalyse (Boundary Value Analysis)
# TDD: Tests werden VOR der Implementierung geschrieben.
import pytest
from combinatorics.boundary_value import generate_bva_values, BVAError


class TestGenerateBvaValues2Punkt:
    """2-Punkt-BVA: Minimum und Maximum."""

    def test_zwei_punkte_integer(self):
        # REQ-0306: Unterer und oberer Grenzwert
        result = generate_bva_values(min_val=1, max_val=10, points=2)
        assert result == ["1", "10"]

    def test_zwei_punkte_gleiche_grenze(self):
        # REQ-0306: Sonderfall – min == max → nur ein einzigartiger Grenzwert
        result = generate_bva_values(min_val=5, max_val=5, points=2)
        assert result == ["5"]

    def test_zwei_punkte_decimal(self):
        # REQ-0306: Ganzzahlige Floats (0.0, 1.0) werden als Integer formatiert
        result = generate_bva_values(min_val=0.0, max_val=1.0, points=2)
        assert "0" in result
        assert "1" in result


class TestGenerateBvaValues3Punkt:
    """3-Punkt-BVA: min, min+1, max."""

    def test_drei_punkte_standard(self):
        # REQ-0306: Untere Grenze, direkt darüber, obere Grenze
        result = generate_bva_values(min_val=1, max_val=10, points=3)
        assert result == ["1", "2", "10"]

    def test_drei_punkte_grosse_werte(self):
        # REQ-0306: Große Zahlen
        result = generate_bva_values(min_val=100, max_val=999, points=3)
        assert result == ["100", "101", "999"]

    def test_drei_punkte_minimum_bereich(self):
        # REQ-0306: Wenn min+1 == max, werden Duplikate entfernt → 2 eindeutige Werte
        result = generate_bva_values(min_val=1, max_val=2, points=3)
        assert len(result) >= 2
        assert "1" in result
        assert "2" in result


class TestGenerateBvaValues4Punkt:
    """4-Punkt-BVA: min, min+1, max-1, max."""

    def test_vier_punkte_standard(self):
        # REQ-0306: Alle vier Grenzwerte
        result = generate_bva_values(min_val=1, max_val=10, points=4)
        assert result == ["1", "2", "9", "10"]

    def test_vier_punkte_kleiner_bereich(self):
        # REQ-0306: Bereich 1..3 → min=1, min+1=2, max-1=2, max=3 (Duplikate möglich)
        result = generate_bva_values(min_val=1, max_val=3, points=4)
        assert "1" in result
        assert "3" in result


class TestGenerateBvaValuesValidierung:
    """Fehlerbehandlung und Randfälle."""

    def test_min_groesser_als_max_wirft_fehler(self):
        # REQ-0306: Ungültige Eingabe → BVAError
        with pytest.raises(BVAError):
            generate_bva_values(min_val=10, max_val=1, points=2)

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
