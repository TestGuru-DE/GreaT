"""
REQ-6007: Tests fuer BVA Uhrzeit (boundary_value.py - generate_bva_time).

10 Tests: Mitternacht, 24:00, Mitternachtsuebergang, 2/3/4-Punkt-Methode,
Formate, Schrittweite, Zusatzwerte.
"""
import pytest
from combinatorics.boundary_value import generate_bva_time, BVAError


class TestBvaTime2Punkt:
    """2-Punkt-Methode fuer Uhrzeit."""

    def test_standard_range(self):
        """Standardbereich 08:00 bis 18:00."""
        result = generate_bva_time("08:00", "18:00", points=2)
        values = [r.value for r in result]
        assert "07:59" in values  # min-1
        assert "08:00" in values   # min
        assert "18:00" in values   # max
        assert "18:01" in values   # max+1
        assert len(result) == 4

    def test_error_values_marked(self):
        """Werte außerhalb des Bereichs sind Fehlerwerte."""
        result = generate_bva_time("08:00", "18:00", points=2)
        value_map = {r.value: r.is_error for r in result}
        assert value_map["07:59"] is True   # min-1 = Fehler
        assert value_map["08:00"] is False   # min = gueltig
        assert value_map["18:00"] is False   # max = gueltig
        assert value_map["18:01"] is True    # max+1 = Fehler


class TestBvaTime3Punkt:
    """3-Punkt-Methode fuer Uhrzeit."""

    def test_three_points_standard(self):
        result = generate_bva_time("08:00", "18:00", points=3)
        values = [r.value for r in result]
        assert "07:59" in values  # min-1
        assert "08:00" in values   # min
        assert "08:01" in values   # min+1
        assert "17:59" in values   # max-1
        assert "18:00" in values   # max
        assert "18:01" in values   # max+1
        assert len(result) == 6


class TestBvaTime4Punkt:
    """4-Punkt-Methode fuer Uhrzeit."""

    def test_four_points_standard(self):
        result = generate_bva_time("08:00", "18:00", points=4)
        values = [r.value for r in result]
        assert "07:58" in values  # min-2
        assert "07:59" in values  # min-1
        assert "08:00" in values   # min
        assert "08:01" in values   # min+1
        assert "17:59" in values   # max-1
        assert "18:00" in values   # max
        assert "18:01" in values   # max+1
        assert "18:02" in values   # max+2
        assert len(result) == 8


class TestBvaTimeMidnight:
    """Mitternacht-Zusatzwerte."""

    def test_midnight_extra(self):
        """00:00 als Zusatzwert."""
        result = generate_bva_time(
            "08:00", "18:00", points=2,
            extras={"midnight": True}
        )
        values = [r.value for r in result]
        assert "00:00" in values

    def test_end_of_day_extra(self):
        """23:59 als Zusatzwert."""
        result = generate_bva_time(
            "08:00", "18:00", points=2,
            extras={"end_of_day": True}
        )
        values = [r.value for r in result]
        assert "23:59" in values


class TestBvaTimeInvalid2400:
    """24:00 als ungueltiger Wert."""

    def test_invalid_2400(self):
        """24:00 erscheint als Fehlerwert."""
        result = generate_bva_time(
            "08:00", "18:00", points=2,
            extras={"invalid_2400": True}
        )
        error_values = [r for r in result if r.is_error and "24:00" in r.value]
        assert len(error_values) >= 1


class TestBvaTimeMidnightCrossing:
    """Mitternachtsuebergang (Min > Max)."""

    def test_midnight_crossing_detected(self):
        """Bereich 22:00-02:00 wird als Mitternachtsuebergang erkannt."""
        result = generate_bva_time(
            "22:00", "02:00", points=2,
            extras={"midnight_crossing": True}
        )
        # Mitternacht sollte im Ergebnis sein
        values = [r.value for r in result]
        assert "00:00" in values

    def test_midnight_crossing_no_error(self):
        """Mitternachtsuebergang erzeugt keinen Validierungsfehler."""
        result = generate_bva_time("22:00", "02:00", points=2)
        assert len(result) >= 2  # Mindestens min und max


class TestBvaTimeFormat:
    """Uhrzeit-Formate."""

    def test_format_hhmmss(self):
        """Format HH:MM:SS mit Sekunden."""
        result = generate_bva_time(
            "08:00:00", "18:00:00", points=2, fmt="HH:MM:SS"
        )
        for r in result:
            assert ":" in r.value
            parts = r.value.split(":")
            assert len(parts) == 3  # HH:MM:SS


class TestBvaTimeStep:
    """Schrittweite (Minute vs. Sekunde)."""

    def test_step_second(self):
        """Schrittweite Sekunde: min-1 ist 1 Sekunde vor min."""
        result = generate_bva_time(
            "08:00:00", "08:00:10", points=2,
            fmt="HH:MM:SS", step="second"
        )
        values = [r.value for r in result]
        assert "07:59:59" in values  # min-1 (1 Sekunde)


class TestBvaTimeVtype:
    """vtype ist immer 'time'."""

    def test_vtype_is_time(self):
        result = generate_bva_time("08:00", "18:00", points=2)
        for r in result:
            assert r.vtype == "time"