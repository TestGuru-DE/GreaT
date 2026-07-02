"""Tests für ISTQB-konforme Grenzwertanalyse.

ISTQB-Spezifikation für Bereich [min, max]:

2-Wert-Methode (4 Werte gesamt):
  Untere Grenze: [min-1, min]
  Obere Grenze: [max, max+1]
  Beispiel 1-100: [0, 1, 100, 101]

3-Wert-Methode (6 Werte gesamt):
  Untere Grenze: [min-1, min, min+1]
  Obere Grenze: [max-1, max, max+1]
  Beispiel 1-100: [0, 1, 2, 99, 100, 101]

4-Wert-Methode (8 Werte gesamt):
  Untere Grenze: [min-2, min-1, min, min+1]
  Obere Grenze: [max-1, max, max+1, max+2]
  Beispiel 1-100: [-1, 0, 1, 2, 99, 100, 101, 102]
"""
import pytest
from combinatorics.boundary_value import generate_bva_values, BVAError


class TestBVA2Wert:
    """2-Wert-Methode: 2 Werte pro Grenze, 4 gesamt."""

    def test_standard_range_1_to_100(self):
        """Beispiel 1-100: [0, 1, 100, 101]."""
        result = generate_bva_values(min_val=1, max_val=100, points=2)
        values = [float(v) for v in result]
        assert 0 in values   # min-1 (außen)
        assert 1 in values   # min   (Grenzwert)
        assert 100 in values # max   (Grenzwert)
        assert 101 in values # max+1 (außen)
        assert len(result) == 4

    def test_returns_exactly_4_values(self):
        """2-Wert-Methode liefert immer 4 Werte (außer Duplikate)."""
        result = generate_bva_values(min_val=10, max_val=20, points=2)
        assert len(result) == 4

    def test_lower_boundary_values(self):
        """Untere Grenze: [min-1, min]."""
        result = generate_bva_values(min_val=1, max_val=100, points=2)
        values = sorted([float(v) for v in result])
        # Erste 2: untere Grenze
        assert values[0] == 0   # min-1 (außen)
        assert values[1] == 1   # min   (Grenzwert)

    def test_upper_boundary_values(self):
        """Obere Grenze: [max, max+1]."""
        result = generate_bva_values(min_val=1, max_val=100, points=2)
        values = sorted([float(v) for v in result])
        # Letzte 2: obere Grenze
        assert values[2] == 100  # max   (Grenzwert)
        assert values[3] == 101  # max+1 (außen)

    def test_decimal_range(self):
        """Dezimalbereich: Epsilon basiert auf Nachkommastellen."""
        result = generate_bva_values(min_val="0.1", max_val="0.9", points=2)
        assert len(result) == 4
        values = sorted([float(v) for v in result])
        assert values[0] == pytest.approx(0.0)   # 0.1 - 0.1
        assert values[1] == pytest.approx(0.1)   # min
        assert values[2] == pytest.approx(0.9)   # max
        assert values[3] == pytest.approx(1.0)   # 0.9 + 0.1


class TestBVA3Wert:
    """3-Wert-Methode: 3 Werte pro Grenze, 6 gesamt."""

    def test_standard_range_1_to_100(self):
        """Beispiel 1-100: [0, 1, 2, 99, 100, 101]."""
        result = generate_bva_values(min_val=1, max_val=100, points=3)
        values = [float(v) for v in result]
        assert 0 in values   # min-1 (außen)
        assert 1 in values   # min   (Grenzwert)
        assert 2 in values   # min+1 (innen)
        assert 99 in values  # max-1 (innen)
        assert 100 in values # max   (Grenzwert)
        assert 101 in values # max+1 (außen)
        assert len(result) == 6

    def test_returns_exactly_6_values(self):
        """3-Wert-Methode liefert 6 Werte (außer Duplikate)."""
        result = generate_bva_values(min_val=10, max_val=20, points=3)
        assert len(result) == 6

    def test_no_duplicates_small_range(self):
        """Duplikat-Entfernung bei kleinem Bereich."""
        # Bereich 1-3: [0, 1, 2, 2, 3, 4]
        # Nach Deduplizierung: [0, 1, 2, 3, 4] = 5 Werte
        result = generate_bva_values(min_val=1, max_val=3, points=3)
        assert len(result) == len(set(result))
        values = sorted([float(v) for v in result])
        assert values == [0, 1, 2, 3, 4]


class TestBVA4Wert:
    """4-Wert-Methode: 4 Werte pro Grenze, 8 gesamt."""

    def test_standard_range_1_to_100(self):
        """Beispiel 1-100: [-1, 0, 1, 2, 99, 100, 101, 102]."""
        result = generate_bva_values(min_val=1, max_val=100, points=4)
        values = [float(v) for v in result]
        assert -1 in values  # min-2 (außen)
        assert 0 in values   # min-1 (außen)
        assert 1 in values   # min   (Grenzwert)
        assert 2 in values   # min+1 (innen)
        assert 99 in values  # max-1 (innen)
        assert 100 in values # max   (Grenzwert)
        assert 101 in values # max+1 (außen)
        assert 102 in values # max+2 (außen)
        assert len(result) == 8

    def test_returns_exactly_8_values(self):
        """4-Wert-Methode liefert 8 Werte (außer Duplikate)."""
        result = generate_bva_values(min_val=10, max_val=50, points=4)
        assert len(result) == 8

    def test_no_duplicates_small_range(self):
        """Duplikat-Entfernung bei kleinem Bereich."""
        # Bereich 1-5: [-1, 0, 1, 2, 4, 5, 6, 7]
        result = generate_bva_values(min_val=1, max_val=5, points=4)
        assert len(result) == len(set(result))
        values = sorted([float(v) for v in result])
        assert values == [-1, 0, 1, 2, 4, 5, 6, 7]


class TestBVAEdgeCases:
    """Randfälle und Fehlerbehandlung."""

    def test_negative_range(self):
        """Negativer Bereich funktioniert korrekt."""
        result = generate_bva_values(min_val=-10, max_val=-1, points=2)
        values = [float(v) for v in result]
        assert -11 in values  # min-1
        assert -10 in values  # min
        assert -1 in values   # max
        assert 0 in values    # max+1

    def test_single_value_range(self):
        """min == max: Grenzwerte rundum, keine Duplikate."""
        result = generate_bva_values(min_val=5, max_val=5, points=2)
        # [4, 5, 5, 6] -> dedupliziert zu [4, 5, 6]
        assert len(result) == len(set(result))
        values = sorted([float(v) for v in result])
        assert 4 in values
        assert 5 in values
        assert 6 in values

    def test_string_input_values(self):
        """API übergibt ggf. Strings (JSON)."""
        result = generate_bva_values(min_val="1", max_val="100", points=2)
        assert len(result) == 4
        values = sorted([float(v) for v in result])
        assert values == [0, 1, 100, 101]

    def test_min_greater_than_max_raises_error(self):
        """min > max wird auto-korrigiert (swap)."""
        result = generate_bva_values(min_val=10, max_val=1, points=2)
        assert len(result) >= 2

    def test_invalid_points_raises_error(self):
        """points muss 2, 3 oder 4 sein."""
        with pytest.raises(BVAError):
            generate_bva_values(min_val=1, max_val=10, points=5)

    def test_result_is_sorted(self):
        """Ergebnis ist aufsteigend sortiert."""
        result = generate_bva_values(min_val=1, max_val=100, points=4)
        values = [float(v) for v in result]
        assert values == sorted(values)

    def test_result_is_string_list(self):
        """API-Kontrakt: Rückgabe ist Liste von Strings."""
        result = generate_bva_values(min_val=0, max_val=100, points=3)
        assert isinstance(result, list)
        assert all(isinstance(v, str) for v in result)
