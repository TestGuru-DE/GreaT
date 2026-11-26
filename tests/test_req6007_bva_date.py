"""
REQ-6007: Tests fuer BVA Datum (boundary_value.py - generate_bva_date).

15 Tests: Schaltjahr, Monatsende, Jahreswechsel, ungultige Daten,
2/3/4-Punkt-Methode, Formate.
"""
import pytest
from datetime import date
from combinatorics.boundary_value import generate_bva_date, BVAError


class TestBvaDate2Punkt:
    """2-Punkt-Methode fuer Datum."""

    def test_standard_range(self):
        """Standardbereich 2024-01-01 bis 2024-12-31."""
        result = generate_bva_date("2024-01-01", "2024-12-31", points=2)
        values = [r.value for r in result]
        assert "2023-12-31" in values  # min-1
        assert "2024-01-01" in values   # min
        assert "2024-12-31" in values   # max
        assert "2025-01-01" in values   # max+1
        assert len(result) == 4

    def test_error_values_marked(self):
        """Werte außerhalb des Bereichs sind Fehlerwerte."""
        result = generate_bva_date("2024-01-01", "2024-12-31", points=2)
        value_map = {r.value: r.is_error for r in result}
        assert value_map["2023-12-31"] is True   # min-1 = Fehler
        assert value_map["2024-01-01"] is False   # min = gueltig
        assert value_map["2024-12-31"] is False   # max = gueltig
        assert value_map["2025-01-01"] is True    # max+1 = Fehler

    def test_vtype_is_date(self):
        """Alle Werte haben vtype='date'."""
        result = generate_bva_date("2024-01-01", "2024-06-30", points=2)
        for r in result:
            assert r.vtype == "date"


class TestBvaDate3Punkt:
    """3-Punkt-Methode fuer Datum."""

    def test_three_points_standard(self):
        result = generate_bva_date("2024-01-01", "2024-12-31", points=3)
        values = [r.value for r in result]
        assert "2023-12-31" in values  # min-1
        assert "2024-01-01" in values   # min
        assert "2024-01-02" in values   # min+1
        assert "2024-12-30" in values   # max-1
        assert "2024-12-31" in values   # max
        assert "2025-01-01" in values   # max+1
        assert len(result) == 6

    def test_three_points_small_range(self):
        """Kleiner Bereich: Duplikate werden entfernt."""
        result = generate_bva_date("2024-01-01", "2024-01-02", points=3)
        values = [r.value for r in result]
        assert len(values) == len(set(values)), "Duplikate gefunden!"


class TestBvaDate4Punkt:
    """4-Punkt-Methode fuer Datum."""

    def test_four_points_standard(self):
        result = generate_bva_date("2024-01-01", "2024-12-31", points=4)
        values = [r.value for r in result]
        assert "2023-12-30" in values  # min-2
        assert "2023-12-31" in values  # min-1
        assert "2024-01-01" in values   # min
        assert "2024-01-02" in values   # min+1
        assert "2024-12-30" in values   # max-1
        assert "2024-12-31" in values   # max
        assert "2025-01-01" in values   # max+1
        assert "2025-01-02" in values   # max+2
        assert len(result) == 8


class TestBvaDateLeapYear:
    """Schaltjahr-Sonderfaelle."""

    def test_leap_year_2024_in_range(self):
        """29.02.2024 wird als Zusatzwert erzeugt."""
        result = generate_bva_date(
            "2024-01-01", "2024-12-31", points=2,
            extras={"leap_year": True}
        )
        values = [r.value for r in result]
        assert "2024-02-29" in values

    def test_leap_year_2000_leap(self):
        """Jahr 2000 ist Schaltjahr (durch 400 teilbar)."""
        result = generate_bva_date(
            "2000-01-01", "2000-12-31", points=2,
            extras={"leap_year": True}
        )
        values = [r.value for r in result]
        assert "2000-02-29" in values

    def test_non_leap_year_2100(self):
        """Jahr 2100 ist KEIN Schaltjahr (durch 100, nicht durch 400)."""
        result = generate_bva_date(
            "2100-01-01", "2100-12-31", points=2,
            extras={"non_leap_year": True}
        )
        values = [r.value for r in result]
        # 29.02.2100 ist ungueltig
        assert any(r.is_error and "29.02" in r.label for r in result)

    def test_non_leap_year_2023(self):
        """2023 ist kein Schaltjahr."""
        result = generate_bva_date(
            "2023-01-01", "2023-12-31", points=2,
            extras={"non_leap_year": True}
        )
        # 29.02.2023 ist ungueltig
        error_values = [r for r in result if r.is_error and "29.02" in r.label]
        assert len(error_values) >= 1


class TestBvaDateMonthEnds:
    """Monatsenden-Zusatzwerte."""

    def test_month_ends_january_march(self):
        """Monatsenden in Bereich Jan-Mar."""
        result = generate_bva_date(
            "2024-01-01", "2024-03-31", points=2,
            extras={"month_ends": True}
        )
        values = [r.value for r in result]
        assert "2024-01-31" in values
        assert "2024-02-29" in values  # 2024 ist Schaltjahr
        assert "2024-03-31" in values

    def test_month_ends_non_leap(self):
        """Februar hat 28 Tage in Nicht-Schaltjahr."""
        result = generate_bva_date(
            "2023-01-01", "2023-03-31", points=2,
            extras={"month_ends": True}
        )
        values = [r.value for r in result]
        assert "2023-02-28" in values


class TestBvaDateYearTransition:
    """Jahreswechsel-Zusatzwerte."""

    def test_year_transition_2024_2025(self):
        result = generate_bva_date(
            "2024-12-01", "2025-01-31", points=2,
            extras={"year_transition": True}
        )
        values = [r.value for r in result]
        assert "2024-12-31" in values
        assert "2025-01-01" in values

    def test_year_transition_single_year(self):
        """Innerhalb eines Jahres: 01.01. und 31.12."""
        result = generate_bva_date(
            "2024-01-01", "2024-12-31", points=2,
            extras={"year_transition": True}
        )
        values = [r.value for r in result]
        assert "2024-01-01" in values
        assert "2024-12-31" in values


class TestBvaDateInvalid:
    """Ungultige Daten."""

    def test_invalid_date_april_31(self):
        """31.04. ist ungueltig."""
        result = generate_bva_date(
            "2024-01-01", "2024-12-31", points=2,
            extras={"invalid_date": True}
        )
        error_values = [r for r in result if r.is_error and "31.04" in r.label]
        assert len(error_values) >= 1


class TestBvaDateFormat:
    """Ausgabeformate."""

    def test_format_iso(self):
        result = generate_bva_date("2024-01-01", "2024-06-30", points=2, fmt="iso")
        for r in result:
            assert "-" in r.value  # ISO-Format

    def test_format_de(self):
        result = generate_bva_date("2024-01-01", "2024-06-30", points=2, fmt="de")
        for r in result:
            assert "." in r.value  # Deutsches Format


class TestBvaDateEdgeCases:
    """Randfaelle."""

    def test_invalid_date_input_raises(self):
        with pytest.raises(BVAError):
            generate_bva_date("2024-13-01", "2024-12-31", points=2)

    def test_swapped_dates(self):
        """BUG C-05 / REQ-6007: Min > Max wird gemeldet statt still getauscht."""
        with pytest.raises(BVAError, match="Min"):
            generate_bva_date("2024-12-31", "2024-01-01", points=2)

    def test_single_day_range(self):
        result = generate_bva_date("2024-06-15", "2024-06-15", points=2)
        values = [r.value for r in result]
        assert "2024-06-15" in values
        assert len(values) == len(set(values))