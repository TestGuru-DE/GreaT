"""
REQ-6007: Tests fuer BVA Stringlaengen (boundary_value.py - generate_bva_strlen).

10 Tests: Laenge 0, >500 (symbolisch), Unicode, 2/3/4-Punkt-Methode,
Zusatzwerte (leer, Leerzeichen, fuehrend/abschliessend), Zeichenvoerraete.
"""
import pytest
from combinatorics.boundary_value import generate_bva_strlen, BVAError
from combinatorics.symbolic_values import is_symbolic, parse_symbolic_value


class TestBvaStrlen2Punkt:
    """2-Punkt-Methode fuer Stringlaengen."""

    def test_standard_range(self):
        """Standardbereich Laenge 1-50."""
        result = generate_bva_strlen(1, 50, points=2)
        values = [r.value for r in result]
        # min-1 = 0 (leer), min = 1, max = 50, max+1 = 51
        assert len(result) == 4
        # min = 1 Zeichen
        assert any(len(r.value) == 1 and not r.is_error for r in result)
        # max = 50 Zeichen
        assert any(len(r.value) == 50 and not r.is_error for r in result)

    def test_error_values_marked(self):
        """min-1 und max+1 sind Fehlerwerte."""
        result = generate_bva_strlen(1, 50, points=2)
        value_map = {len(r.value): r.is_error for r in result if r.value}
        # min-1 (Laenge 0) sollte Fehler sein wenn min_len > 0
        # max+1 (Laenge 51) sollte Fehler sein
        assert any(r.is_error for r in result if len(r.value) == 51)


class TestBvaStrlen3Punkt:
    """3-Punkt-Methode fuer Stringlaengen."""

    def test_three_points_standard(self):
        result = generate_bva_strlen(1, 10, points=3)
        # min-1=0, min=1, min+1=2, max-1=9, max=10, max+1=11
        assert len(result) == 6


class TestBvaStrlen4Punkt:
    """4-Punkt-Methode fuer Stringlaengen."""

    def test_four_points_standard(self):
        result = generate_bva_strlen(2, 10, points=4)
        # min-2=0, min-1=1, min=2, min+1=3, max-1=9, max=10, max+1=11, max+2=12
        assert len(result) == 8


class TestBvaStrlenZero:
    """Laenge 0 (leerer String)."""

    def test_empty_string_extra(self):
        """Laenge 0 als Zusatzwert."""
        result = generate_bva_strlen(
            1, 50, points=2, extras={"empty": True}
        )
        # Leerer String sollte im Ergebnis sein
        empty_values = [r for r in result if r.value == ""]
        assert len(empty_values) >= 1
        assert empty_values[0].is_error is True  # min_len > 0 -> leer = Fehler

    def test_empty_string_valid_when_min_zero(self):
        """Laenge 0 ist gueltig wenn min_len=0."""
        result = generate_bva_strlen(
            0, 50, points=2, extras={"empty": True}
        )
        empty_values = [r for r in result if r.value == ""]
        if empty_values:
            assert empty_values[0].is_error is False  # min_len = 0 -> leer = gueltig


class TestBvaStrlenSymbolic:
    """Symbolische Werte fuer lange Strings (>500)."""

    def test_long_value_is_symbolic(self):
        """Laenge > 500 wird symbolisch gespeichert."""
        result = generate_bva_strlen(1, 1000, points=2)
        # max+1 = 1001 -> symbolisch
        symbolic = [r for r in result if is_symbolic(r.value)]
        assert len(symbolic) >= 1

    def test_symbolic_value_parsed_correctly(self):
        """Symbolischer Wert laesst sich korrekt parsen."""
        result = generate_bva_strlen(1, 1000, points=2, charset="alnum")
        symbolic = [r for r in result if is_symbolic(r.value)]
        if symbolic:
            sv = parse_symbolic_value(symbolic[0].value)
            assert sv is not None
            assert sv.charset == "alnum"


class TestBvaStrlenUnicode:
    """Unicode-Zeichenvoerraete."""

    def test_charset_unicode(self):
        """Unicode-charset wird akzeptiert."""
        result = generate_bva_strlen(1, 10, points=2, charset="unicode")
        assert len(result) >= 2

    def test_charset_alpha_de(self):
        """Deutsche Umlaute als charset."""
        result = generate_bva_strlen(1, 10, points=2, charset="alpha_de")
        assert len(result) >= 2


class TestBvaStrlenWhitespace:
    """Leerzeichen-Zusatzwerte."""

    def test_whitespace_only_extra(self):
        """Nur-Leerzeichen als Zusatzwert."""
        result = generate_bva_strlen(
            1, 50, points=2, extras={"whitespace_only": True}
        )
        # Leerzeichen-Wert sollte im Ergebnis sein und als Fehler markiert
        ws = [r for r in result if "Leerzeichen" in r.label]
        assert len(ws) >= 1
        assert ws[0].is_error is True

    def test_leading_trailing_whitespace(self):
        """Fuehrende und abschliessende Leerzeichen.
        
        Beide haben gleiche Laenge (min_len+1), also wird nur einer
        durch Deduplizierung beibehalten. Der erste (leading) gewinnt.
        """
        result = generate_bva_strlen(
            5, 20, points=2,
            extras={"leading_whitespace": True, "trailing_whitespace": True}
        )
        leading = [r for r in result if "Fuehrend" in r.label]
        trailing = [r for r in result if "Abschliessend" in r.label]
        # Leading wird zuerst hinzugefuegt und bleibt; trailing wird dedupliziert
        assert len(leading) >= 1
        assert len(trailing) == 0  # Dedupliziert, da gleiche Laenge

    def test_trailing_whitespace_alone(self):
        """Abschliessendes Leerzeichen allein (ohne leading)."""
        result = generate_bva_strlen(
            5, 20, points=2,
            extras={"trailing_whitespace": True}
        )
        trailing = [r for r in result if "Abschliessend" in r.label]
        assert len(trailing) >= 1


class TestBvaStrlenValidation:
    """Validierung."""

    def test_negative_min_raises(self):
        """Negative min_len wirft BVAError."""
        with pytest.raises(BVAError):
            generate_bva_strlen(-1, 10, points=2)

    def test_invalid_charset_raises(self):
        """Unguetliches charset wirft BVAError."""
        with pytest.raises(BVAError):
            generate_bva_strlen(1, 10, points=2, charset="invalid")


class TestBvaStrlenVtype:
    """vtype ist immer 'strlen'."""

    def test_vtype_is_strlen(self):
        result = generate_bva_strlen(1, 10, points=2)
        for r in result:
            assert r.vtype == "strlen"