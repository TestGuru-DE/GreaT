"""
Boundary Value Analysis (BVA) - ISTQB-konform.

2-Wert: [min-1, min, max, max+1]                              (4 Werte)
3-Wert: [min-1, min, min+1, max-1, max, max+1]                (6 Werte)
4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]  (8 Werte)

Quelle: ISTQB Foundation Level Syllabus, Boundary Value Analysis.
"""
from decimal import Decimal, InvalidOperation
from typing import Union


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
        lo = Decimal(str(min_val))
        hi = Decimal(str(max_val))
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
