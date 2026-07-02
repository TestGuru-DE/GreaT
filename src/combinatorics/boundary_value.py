"""
Boundary Value Analysis (BVA) - ISTQB-konform.

2-Wert: [min-1, min, max, max+1]                              (4 Werte)
3-Wert: [min-1, min, min+1, max-1, max, max+1]                (6 Werte)
4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]  (8 Werte)

Quelle: ISTQB Foundation Level Syllabus, Boundary Value Analysis.
"""
from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# REQ-3064: Multi-Range Boundary Value Analysis
# ---------------------------------------------------------------------------

@dataclass
class BVARange:
    """Repräsentiert einen Äquivalenzklassen-Bereich."""
    min_val: str
    max_val: str
    allowed: bool  # True = erlaubt, False = nicht erlaubt (=Fehlerwerte)


@dataclass  
class BVAMultiRangeResult:
    """Ergebnis einer Multi-Range-BVA."""
    value: str
    is_error: bool
    source_range: str  # z.B. "1-100 (erlaubt)"


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
    
    # Alle Kandidaten mit Metadaten sammeln
    all_candidates: dict[Decimal, BVAMultiRangeResult] = {}
    
    for r in ranges:
        lo = Decimal(str(r.min_val))
        hi = Decimal(str(r.max_val))
        
        raw_values = generate_bva_values(str(lo), str(hi), points)
        
        for v_str in raw_values:
            v = Decimal(v_str)
            if v in all_candidates:
                continue  # Duplikat aus anderem Bereich überspringen
            
            # Bestimme ob Fehler
            is_err = _classify_value(v, ranges)
            
            source = f"{r.min_val}-{r.max_val} ({'erlaubt' if r.allowed else 'nicht erlaubt'})"
            all_candidates[v] = BVAMultiRangeResult(
                value=v_str,
                is_error=is_err,
                source_range=source,
            )
    
    # Aufsteigend sortiert
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
        lo = Decimal(str(r.min_val))
        hi = Decimal(str(r.max_val))
        if lo <= v <= hi:
            return not r.allowed  # In nicht-erlaubtem Bereich = Fehler
    return True  # Außerhalb aller Bereiche = Fehler
