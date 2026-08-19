"""REQ-4015: BVA is_valid und Fehlerwert."""
import pytest
from src.combinatorics.boundary_value import BVARange, generate_multi_range_bva


def test_bva_range_has_is_valid():
    """BVARange hat das is_valid Attribute."""
    r = BVARange(min_val="0", max_val="10", allowed=True)
    assert hasattr(r, 'is_valid')
    assert r.is_valid is True


def test_bva_range_is_valid_false():
    """BVARange kann mit is_valid=False erstellt werden."""
    r = BVARange(min_val="0", max_val="10", allowed=False, is_valid=False)
    assert r.is_valid is False


def test_bva_invalid_range_produces_errors():
    """Grenzwerte von is_valid=False Ranges → is_error=True."""
    ranges = [
        BVARange(min_val="0", max_val="10", allowed=True, is_valid=True),
        BVARange(min_val="20", max_val="30", allowed=False, is_valid=False),
    ]
    result = generate_multi_range_bva(ranges, points=2)
    
    # Alle Werte sollten mit is_error klassifiziert sein
    assert len(result) > 0
    
    # Werte im ersten (erlaubten) Bereich sollten nicht-Fehler sein
    range1_values = [v for v in result if 0 <= float(v.value) <= 10]
    for v in range1_values:
        assert v.is_error is False, f"Wert {v.value} sollte kein Fehler sein (is_valid=True Bereich)"
    
    # Werte im zweiten (nicht-erlaubten) Bereich sollten Fehler sein
    range2_values = [v for v in result if 20 <= float(v.value) <= 30]
    for v in range2_values:
        assert v.is_error is True, f"Wert {v.value} sollte ein Fehler sein (is_valid=False Bereich)"
