"""
Boundary Value Analysis (BVA) - ISTQB-konform.

2-Wert: [min-1, min, max, max+1]                              (4 Werte)
3-Wert: [min-1, min, min+1, max-1, max, max+1]                (6 Werte)
4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]  (8 Werte)

Quelle: ISTQB Foundation Level Syllabus, Boundary Value Analysis.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Union, Optional


def _normalize_decimal_text(raw: Union[str, int, float]) -> str:
    return str(raw).strip().replace(",", ".")


class BVAError(ValueError):
    """Wird geworfen bei ungültigen BVA-Parametern (Rückwärtskompatibilität)."""


def _epsilon(lo: Decimal, hi: Decimal) -> Decimal:
    """Kleinste sinnvolle Einheit basierend auf der Präzision der Eingaben."""
    lo_str = str(lo)
    hi_str = str(hi)
    dec_lo = len(lo_str.split(".")[1]) if "." in lo_str else 0
    dec_hi = len(hi_str.split(".")[1]) if "." in hi_str else 0
    decimals = max(dec_lo, dec_hi)
    return Decimal("0.1") ** decimals if decimals > 0 else Decimal("1")


def generate_bva_values(
    min_val: Union[str, int, float],
    max_val: Union[str, int, float],
    points: int = 2,
) -> list[str]:
    """
    Generiert ISTQB-konforme Grenzwert-Testdaten für einen Bereich [min_val, max_val].

    Args:
        min_val: Untere Grenze (inklusiv)
        max_val: Obere Grenze (inklusiv)
        points:  2, 3 oder 4 Werte pro Grenze

    Returns:
        Deduplizierte, aufsteigend sortierte Liste von Wert-Strings.
    """
    try:
        lo = Decimal(_normalize_decimal_text(min_val))
        hi = Decimal(_normalize_decimal_text(max_val))
    except InvalidOperation as exc:
        raise BVAError(f"Ungültige Grenzwerte: min={min_val!r}, max={max_val!r}") from exc

    if lo > hi:
        lo, hi = hi, lo

    eps = _epsilon(lo, hi)

    if points == 2:
        candidates = [lo - eps, lo, hi, hi + eps]
    elif points == 3:
        candidates = [lo - eps, lo, lo + eps, hi - eps, hi, hi + eps]
    elif points == 4:
        candidates = [lo - 2*eps, lo - eps, lo, lo + eps,
                      hi - eps,   hi,        hi + eps, hi + 2*eps]
    else:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    # Deduplizieren + sortieren
    seen: set[Decimal] = set()
    result: list[str] = []
    for v in sorted(candidates):
        if v not in seen:
            seen.add(v)
            # Ganze Zahlen ohne Dezimalpunkt ausgeben
            if eps == Decimal("1") and v == v.to_integral_value():
                result.append(str(int(v)))
            else:
                result.append(str(v))
    return result


# ---------------------------------------------------------------------------
# REQ-3064: Multi-Range Boundary Value Analysis
# ---------------------------------------------------------------------------

@dataclass
class BVARange:
    """Repräsentiert einen Äquivalenzklassen-Bereich."""
    min_val: str
    max_val: str
    allowed: bool  # True = erlaubt, False = nicht erlaubt (=Fehlerwerte)
    is_valid: bool = True  # REQ-4015: Explizites Flag für erlaubte/unerlaubte Äquivalenzklassen


@dataclass  
class BVAMultiRangeResult:
    """Ergebnis einer Multi-Range-BVA."""
    value: str
    is_error: bool
    source_range: str  # z.B. "1-100 (erlaubt)"


def _parse_optional_decimal(raw: str) -> Optional[Decimal]:
    if raw is None:
        return None
    text = _normalize_decimal_text(raw)
    if text == "":
        return None
    return Decimal(text)


def _format_bound(raw: str, is_min: bool) -> str:
    if raw is None or str(raw).strip() == "":
        return "-∞" if is_min else "∞"
    return str(raw)


def _normalize_range(r: BVARange) -> tuple[Optional[Decimal], Optional[Decimal], str, str]:
    lo = _parse_optional_decimal(r.min_val)
    hi = _parse_optional_decimal(r.max_val)
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
    return lo, hi, _format_bound(r.min_val, True), _format_bound(r.max_val, False)


def _range_sort_key(lo: Optional[Decimal], hi: Optional[Decimal]) -> tuple[int, Decimal, Decimal]:
    low_key = lo if lo is not None else Decimal("-Infinity")
    high_key = hi if hi is not None else Decimal("Infinity")
    return (0, low_key, high_key)


def _range_overlaps(left: tuple[Optional[Decimal], Optional[Decimal]], right: tuple[Optional[Decimal], Optional[Decimal]]) -> bool:
    left_lo, left_hi = left
    right_lo, right_hi = right
    left_hi_cmp = left_hi if left_hi is not None else Decimal("Infinity")
    right_lo_cmp = right_lo if right_lo is not None else Decimal("-Infinity")
    return left_hi_cmp >= right_lo_cmp


def _generate_range_candidates(lo: Optional[Decimal], hi: Optional[Decimal], points: int) -> list[Decimal]:
    if lo is None and hi is None:
        return []

    if lo is None:
        eps = _epsilon(hi, hi)
        if points == 2:
            return [hi - eps, hi]
        if points == 3:
            return [hi - (eps * 2), hi - eps, hi]
        if points == 4:
            return [hi - (eps * 3), hi - (eps * 2), hi - eps, hi]
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    if hi is None:
        eps = _epsilon(lo, lo)
        if points == 2:
            return [lo, lo + eps]
        if points == 3:
            return [lo, lo + eps, lo + (eps * 2)]
        if points == 4:
            return [lo, lo + eps, lo + (eps * 2), lo + (eps * 3)]
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    eps = _epsilon(lo, hi)
    if points == 2:
        return [lo - eps, lo, hi, hi + eps]
    if points == 3:
        return [lo - eps, lo, lo + eps, hi - eps, hi, hi + eps]
    if points == 4:
        return [
            lo - (eps * 2), lo - eps, lo, lo + eps,
            hi - eps, hi, hi + eps, hi + (eps * 2),
        ]
    raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")


def generate_multi_range_bva(
    ranges: list[BVARange],
    points: int = 2,
) -> list[BVAMultiRangeResult]:
    """
    Generiert ISTQB-konforme Grenzwert-Testdaten für mehrere Äquivalenzklassen.
    
    REQ-3064: Mehrere angrenzende Bereiche mit erlaubt/nicht-erlaubt-Markierung.
    
    Regeln:
    - Werte in nicht-erlaubten Bereichen → is_error=True
    - Werte außerhalb aller Bereiche → is_error=True  
    - Keine Redundanz bei angrenzenden Grenzen
    - Aufsteigend sortiert
    
    Args:
        ranges: Liste von BVARange-Objekten
        points: 2, 3 oder 4 Werte pro Grenze
        
    Returns:
        Liste von BVAMultiRangeResult-Objekten (dedupliziert, sortiert)
    """
    if not ranges:
        return []

    normalized_ranges = [_normalize_range(r) for r in ranges]
    ordered = sorted(enumerate(normalized_ranges), key=lambda item: _range_sort_key(item[1][0], item[1][1]))

    for idx in range(1, len(ordered)):
        prev = ordered[idx - 1][1][:2]
        current = ordered[idx][1][:2]
        if _range_overlaps(prev, current):
            raise BVAError("Bereiche dürfen sich nicht überschneiden oder berühren.")

    all_candidates: dict[Decimal, BVAMultiRangeResult] = {}

    for index, (lo, hi, min_label, max_label) in ordered:
        raw_values = _generate_range_candidates(lo, hi, points)
        source_range = f"{min_label}-{max_label} ({'erlaubt' if ranges[index].allowed else 'nicht erlaubt'})"

        for candidate in raw_values:
            value_str = str(candidate)
            if candidate in all_candidates:
                continue
            all_candidates[candidate] = BVAMultiRangeResult(
                value=value_str,
                is_error=_classify_value(candidate, ranges),
                source_range=source_range,
            )

    return [all_candidates[k] for k in sorted(all_candidates.keys())]


def _classify_value(v: Decimal, ranges: list[BVARange]) -> bool:
    """
    Gibt True zurück wenn v ein Fehlerwert ist.
    
    Regeln:
    - In nicht-erlaubtem Bereich: True
    - Außerhalb aller Bereiche: True
    - In erlaubtem Bereich: False
    """
    for r in ranges:
        lo = _parse_optional_decimal(r.min_val)
        hi = _parse_optional_decimal(r.max_val)
        if lo is not None and hi is not None and lo > hi:
            lo, hi = hi, lo
        if lo is None and hi is None:
            continue
        lower_ok = lo is None or lo <= v
        upper_ok = hi is None or v <= hi
        if lower_ok and upper_ok:
            return not r.allowed  # In nicht-erlaubtem Bereich = Fehler
    return True  # Außerhalb aller Bereiche = Fehler
