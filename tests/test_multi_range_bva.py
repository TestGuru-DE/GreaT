"""
REQ-3064: Multi-Range Boundary Value Analysis Tests.

Testet mehrere angrenzende Äquivalenzklassen mit erlaubt/nicht-erlaubt-Markierung.
"""
import pytest
from combinatorics.boundary_value import generate_multi_range_bva, BVARange


def test_single_range_equals_standard_bva():
    """Ein Bereich sollte wie Standard-BVA funktionieren."""
    ranges = [BVARange("1", "100", True)]
    result = generate_multi_range_bva(ranges, 2)
    values = [r.value for r in result]
    assert "0" in values
    assert "1" in values
    assert "100" in values
    assert "101" in values


def test_single_range_all_valid():
    """Ein erlaubter Bereich: nur Werte außerhalb sind Fehler."""
    ranges = [BVARange("1", "100", True)]
    result = generate_multi_range_bva(ranges, 2)
    value_map = {r.value: r.is_error for r in result}
    
    # Werte außerhalb sind Fehler
    assert value_map["0"] is True
    assert value_map["101"] is True
    # Grenzwerte drin sind gültig
    assert value_map["1"] is False
    assert value_map["100"] is False


def test_multi_range_no_duplicates():
    """Grenzwerte zwischen Bereichen nur einmal."""
    ranges = [
        BVARange("1", "100", True),
        BVARange("101", "200", False),
        BVARange("201", "300", True),
    ]
    result = generate_multi_range_bva(ranges, 2)
    values = [r.value for r in result]
    assert len(values) == len(set(values)), "Duplikate gefunden!"


def test_multi_range_not_allowed_region_is_error():
    """Werte in nicht-erlaubten Bereichen sind Fehlerwerte."""
    ranges = [
        BVARange("1", "100", True),
        BVARange("101", "200", False),
    ]
    result = generate_multi_range_bva(ranges, 2)
    value_map = {r.value: r.is_error for r in result}
    
    # Werte im nicht-erlaubten Bereich sind Fehler
    assert value_map.get("101") is True
    assert value_map.get("200") is True
    # Werte im erlaubten Bereich sind OK
    assert value_map.get("1") is False
    assert value_map.get("100") is False


def test_multi_range_outside_all_ranges_is_error():
    """Werte außerhalb aller Bereiche sind Fehlerwerte."""
    ranges = [BVARange("1", "100", True)]
    result = generate_multi_range_bva(ranges, 2)
    value_map = {r.value: r.is_error for r in result}
    assert value_map["0"] is True    # unterhalb
    assert value_map["101"] is True  # oberhalb


def test_multi_range_three_ranges():
    """Drei Bereiche: erlaubt - nicht erlaubt - erlaubt."""
    ranges = [
        BVARange("1", "100", True),
        BVARange("101", "200", False),
        BVARange("201", "300", True),
    ]
    result = generate_multi_range_bva(ranges, 2)
    value_map = {r.value: r.is_error for r in result}
    
    # Erster Bereich: erlaubt
    assert value_map.get("1") is False
    assert value_map.get("100") is False
    
    # Zweiter Bereich: nicht erlaubt (Fehler)
    assert value_map.get("101") is True
    assert value_map.get("200") is True
    
    # Dritter Bereich: erlaubt
    assert value_map.get("201") is False
    assert value_map.get("300") is False
    
    # Außerhalb aller Bereiche
    assert value_map.get("0") is True     # unterhalb
    assert value_map.get("301") is True   # oberhalb


def test_multi_range_points_3():
    """3-Wert-BVA mit mehreren Bereichen."""
    ranges = [
        BVARange("1", "100", True),
        BVARange("101", "200", False),
    ]
    result = generate_multi_range_bva(ranges, 3)
    
    # Sollte mehr Werte haben als 2-Wert
    assert len(result) > 4
    
    # Innen-Werte sollten existieren
    values = [r.value for r in result]
    assert "2" in values or "1.1" in values  # min+1 vom ersten Bereich


def test_empty_ranges():
    """Leere Range-Liste sollte leere Ergebnisse liefern."""
    result = generate_multi_range_bva([], 2)
    assert result == []


def test_source_range_metadata():
    """Jedes Ergebnis sollte source_range-Metadaten haben."""
    ranges = [
        BVARange("1", "100", True),
        BVARange("101", "200", False),
    ]
    result = generate_multi_range_bva(ranges, 2)
    
    for r in result:
        assert r.source_range, "source_range sollte gesetzt sein"
        assert "-" in r.source_range, "source_range sollte Format 'min-max (...)' haben"
