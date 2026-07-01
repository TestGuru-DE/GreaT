# REQ-0306: Grenzwertanalyse (Boundary Value Analysis)
# Berechnet 2, 3 oder 4 Grenzwert-Testwerte für numerische Äquivalenzklassen.
#
# Formale Korrektheit:
#   2-Punkt: {min, max}
#   3-Punkt: {min, min+1, max}
#   4-Punkt: {min, min+1, max-1, max}
#
# Alle Werte werden als Strings zurückgegeben (API-Kontrakt für Äquivalenzklassen).
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class BVAError(ValueError):
    """Wird geworfen bei ungültigen BVA-Parametern."""


def generate_bva_values(
    min_val: int | float,
    max_val: int | float,
    points: int = 2,
) -> list[str]:
    """Berechnet Grenzwert-Testwerte nach ISTQB-BVA-Methode.

    Args:
        min_val: Untere Grenze der Äquivalenzklasse.
        max_val: Obere Grenze der Äquivalenzklasse.
        points: Anzahl der Grenzwerte (2, 3 oder 4).

    Returns:
        Aufsteigend sortierte Liste von Grenzwerten als Strings.

    Raises:
        BVAError: Bei ungültigen Parametern (min > max, ungültige Punktanzahl).
    """
    if points not in (2, 3, 4):
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points}")
    if min_val > max_val:
        raise BVAError(
            f"min_val ({min_val}) darf nicht größer als max_val ({max_val}) sein"
        )

    is_integer = isinstance(min_val, int) and isinstance(max_val, int)
    # Auch Floats die ganzzahlig sind (z.B. 18.0 aus JSON) als Integer behandeln
    if not is_integer and isinstance(min_val, float) and isinstance(max_val, float):
        if min_val == int(min_val) and max_val == int(max_val):
            is_integer = True
            min_val = int(min_val)
            max_val = int(max_val)
    step = 1 if is_integer else _smallest_step(min_val, max_val)

    values: list[float | int]
    if points == 2:
        values = [min_val, max_val]
    elif points == 3:
        values = [min_val, min_val + step, max_val]
    else:  # points == 4
        values = [min_val, min_val + step, max_val - step, max_val]

    # Deduplizieren, Sortierung beibehalten
    seen: list[float | int] = []
    for v in values:
        if v not in seen:
            seen.append(v)

    return [_format_value(v, is_integer) for v in sorted(seen)]


def _smallest_step(min_val: float, max_val: float) -> float:
    """Bestimmt den kleinsten sinnvollen Schritt basierend auf den Nachkommastellen."""
    min_dec = Decimal(str(min_val))
    max_dec = Decimal(str(max_val))
    # Verwende die Präzision des genaueren Wertes
    min_places = abs(min_dec.as_tuple().exponent)
    max_places = abs(max_dec.as_tuple().exponent)
    places = max(min_places, max_places)
    return float(Decimal("1") / Decimal("10") ** places)


def _format_value(value: float | int, is_integer: bool) -> str:
    """Formatiert einen Wert als String (Integer ohne Dezimalpunkt)."""
    if is_integer:
        return str(int(value))
    return str(value)
