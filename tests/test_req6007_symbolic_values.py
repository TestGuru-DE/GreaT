"""
REQ-6007: Tests fuer symbolische Werte (symbolic_values.py).

Testet Parser, Generator, Konkretisierung und Grenzverhalten
bei MAX_VALUE_LENGTH=500.
"""
import pytest
from combinatorics.symbolic_values import (
    parse_symbolic_value,
    is_symbolic,
    generate_symbolic_string,
    concretize_symbolic,
    should_be_symbolic,
    make_value,
    count_codepoints,
    SymbolicValue,
    MAX_VALUE_LENGTH,
    CHARSETS,
)


class TestParseSymbolicValue:
    """Parser fuer symbolische Werte."""

    def test_parse_valid_alnum(self):
        """Gueltiger symbolischer Wert wird korrekt geparst."""
        sv = parse_symbolic_value("<STR len=1001 charset=alnum>")
        assert sv is not None
        assert sv.length == 1001
        assert sv.charset == "alnum"

    def test_parse_valid_alpha(self):
        sv = parse_symbolic_value("<STR len=501 charset=alpha>")
        assert sv is not None
        assert sv.length == 501
        assert sv.charset == "alpha"

    def test_parse_non_symbolic_returns_none(self):
        """Normaler String gibt None zurueck."""
        assert parse_symbolic_value("hallo") is None
        assert parse_symbolic_value("") is None

    def test_parse_invalid_charset_raises(self):
        """Unguetliches charset wirft ValueError."""
        with pytest.raises(ValueError, match="Unbekanntes charset"):
            parse_symbolic_value("<STR len=100 charset=invalid>")

    def test_parse_whitespace_tolerant(self):
        """Whitespace im Format wird toleriert."""
        sv = parse_symbolic_value("  <STR len=100 charset=alpha>  ")
        assert sv is not None
        assert sv.length == 100


class TestIsSymbolic:
    """is_symbolic() Pruefung."""

    def test_symbolic_string(self):
        assert is_symbolic("<STR len=1001 charset=alnum>") is True

    def test_normal_string(self):
        assert is_symbolic("hallo") is False

    def test_empty_string(self):
        assert is_symbolic("") is False

    def test_malformed_symbolic(self):
        assert is_symbolic("<STR len=abc charset=alpha>") is False


class TestGenerateSymbolicString:
    """Generator fuer symbolische Werte."""

    def test_generate_alnum(self):
        result = generate_symbolic_string(1001, "alnum")
        assert result == "<STR len=1001 charset=alnum>"

    def test_generate_alpha_de(self):
        result = generate_symbolic_string(600, "alpha_de")
        assert result == "<STR len=600 charset=alpha_de>"

    def test_generate_unicode(self):
        result = generate_symbolic_string(2000, "unicode")
        assert result == "<STR len=2000 charset=unicode>"

    def test_generate_invalid_charset_raises(self):
        with pytest.raises(ValueError, match="Unbekanntes charset"):
            generate_symbolic_string(100, "invalid")


class TestConcretizeSymbolic:
    """Konkretisierung symbolischer Werte."""

    def test_concretize_reproducible_with_seed(self):
        """Gleicher Seed liefert gleichen String."""
        s1 = concretize_symbolic("<STR len=100 charset=alpha>", seed=42)
        s2 = concretize_symbolic("<STR len=100 charset=alpha>", seed=42)
        assert s1 == s2

    def test_concretize_correct_length(self):
        """Konkretisierter String hat korrekte Laenge."""
        s = concretize_symbolic("<STR len=50 charset=alnum>", seed=1)
        assert len(s) == 50

    def test_concretize_chars_from_charset(self):
        """Alle Zeichen stammen aus dem angegebenen charset."""
        s = concretize_symbolic("<STR len=100 charset=alpha>", seed=99)
        from combinatorics.symbolic_values import CHARSET_ALPHA
        for ch in s:
            assert ch in CHARSET_ALPHA, f"Zeichen {ch!r} nicht in alpha-charset"

    def test_concretize_invalid_raises(self):
        with pytest.raises(ValueError):
            concretize_symbolic("not a symbolic value")


class TestShouldBeSymbolic:
    """should_be_symbolic() Grenzwert-Pruefung."""

    def test_below_threshold(self):
        assert should_be_symbolic(500) is False

    def test_at_threshold(self):
        assert should_be_symbolic(MAX_VALUE_LENGTH) is False

    def test_above_threshold(self):
        assert should_be_symbolic(501) is True

    def test_well_above_threshold(self):
        assert should_be_symbolic(10000) is True


class TestMakeValue:
    """make_value() erzeugt echte oder symbolische Werte."""

    def test_short_value_is_real(self):
        val = make_value(10, "alpha")
        assert not is_symbolic(val)
        assert len(val) == 10

    def test_long_value_is_symbolic(self):
        val = make_value(1001, "alnum")
        assert is_symbolic(val)
        sv = parse_symbolic_value(val)
        assert sv.length == 1001
        assert sv.charset == "alnum"

    def test_fill_char_override(self):
        val = make_value(5, "alpha", fill_char="X")
        assert val == "XXXXX"


class TestCountCodepoints:
    """count_codepoints() zaehlt Unicode-Codepoints."""

    def test_ascii(self):
        assert count_codepoints("hello") == 5

    def test_unicode_german(self):
        assert count_codepoints("äöüß") == 4

    def test_unicode_cjk(self):
        assert count_codepoints("中文") == 2

    def test_emoji(self):
        # Emoji sind einzelne Codepoints in Python 3
        assert count_codepoints("😀") == 1