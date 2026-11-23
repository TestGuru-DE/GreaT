"""
Boundary Value Analysis (BVA) - ISTQB-konform.

2-Wert: [min-1, min, max, max+1]                              (4 Werte)
3-Wert: [min-1, min, min+1, max-1, max, max+1]                (6 Werte)
4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]  (8 Werte)

Quelle: ISTQB Foundation Level Syllabus, Boundary Value Analysis.

REQ-6007: Erweiterung fuer Datum, Uhrzeit, Datum+Uhrzeit und Stringlaengen.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
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


# ---------------------------------------------------------------------------
# REQ-6007: BVA fuer Datum, Uhrzeit, Datum+Uhrzeit und Stringlaengen
# ---------------------------------------------------------------------------

@dataclass
class BVAValue:
    """Ein BVA-Wert mit Metadaten (REQ-6007)."""
    value: str
    is_error: bool
    vtype: str  # 'date', 'time', 'datetime', 'strlen', 'number'
    label: str = ""  # Beschreibung, z.B. "min", "29.02. Schaltjahr"


def _parse_date(raw: str) -> date:
    """Parsiert ein Datum im Format 'YYYY-MM-DD'."""
    try:
        parts = raw.strip().split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return date(y, m, d)
    except (ValueError, IndexError) as exc:
        raise BVAError(f"Ungültiges Datum: {raw!r}. Format: YYYY-MM-DD") from exc


def _format_date(d: date, fmt: str = "iso") -> str:
    """Formatiert ein Datum."""
    if fmt == "de":
        return d.strftime("%d.%m.%Y")
    return d.isoformat()  # YYYY-MM-DD


def _is_leap_year(year: int) -> bool:
    """Gregorianischer Schaltjahr-Test."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _last_day_of_month(year: int, month: int) -> int:
    """Letzer Tag eines Monats."""
    if month == 12:
        return 31
    return date(year, month + 1, 1) - timedelta(days=1)  # type: ignore[operator]


def _month_ends_in_range(start: date, end: date) -> list[date]:
    """Alle Monatsenden (30./31.) im Bereich [start, end]."""
    results = []
    current = start.replace(day=1)
    if current < start:
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)

    while current <= end:
        last = _last_day_of_month(current.year, current.month)
        if last >= start and last <= end and last not in results:
            results.append(last)
        # Next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1, day=1)
        else:
            current = current.replace(month=current.month + 1, day=1)
    return results


def _year_transitions_in_range(start: date, end: date) -> list[date]:
    """31.12. und 01.01. im Bereich [start, end]."""
    results = []
    for y in range(start.year, end.year + 2):
        dec31 = date(y, 12, 31)
        jan01 = date(y, 1, 1)
        if dec31 >= start and dec31 <= end:
            results.append(dec31)
        if jan01 >= start and jan01 <= end:
            results.append(jan01)
    return sorted(set(results))


def generate_bva_date(
    min_date: str,
    max_date: str,
    points: int = 2,
    fmt: str = "iso",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """
    REQ-6007: BVA fuer Datumsbereiche.

    2/3/4-Punkt-Methode mit Schritt=1 Tag.
    Zusatzwerte (optional): 29.02 (Schaltjahr/Nicht-Schaltjahr), Monatsenden,
    Jahreswechsel, ungultiges Datum.

    Args:
        min_date: Untere Grenze (YYYY-MM-DD)
        max_date: Obere Grenze (YYYY-MM-DD)
        points: 2, 3 oder 4
        fmt: 'iso' (JJJJ-MM-TT) oder 'de' (TT.MM.JJJJ)
        extras: Dict mit Booleans:
            - 'leap_year': 29.02. eines Schaltjahrs (gultig)
            - 'non_leap_year': 29.02. eines Nicht-Schaltjahrs (ungultig)
            - 'month_ends': Monatsenden 30./31.
            - 'year_transition': Jahreswechsel 31.12./01.01.
            - 'invalid_date': Ungultiges Datum (z.B. 31.04.)

    Returns:
        Liste von BVAValue-Objekten (dedupliziert, sortiert nach Datum).
    """
    if extras is None:
        extras = {}

    lo = _parse_date(min_date)
    hi = _parse_date(max_date)
    if lo > hi:
        lo, hi = hi, lo

    results: dict[str, BVAValue] = {}

    # --- BVA-Grenzwerte ---
    if points == 2:
        date_candidates = [
            (lo - timedelta(days=1), "min-1", True),
            (lo, "min", False),
            (hi, "max", False),
            (hi + timedelta(days=1), "max+1", True),
        ]
    elif points == 3:
        date_candidates = [
            (lo - timedelta(days=1), "min-1", True),
            (lo, "min", False),
            (lo + timedelta(days=1), "min+1", False),
            (hi - timedelta(days=1), "max-1", False),
            (hi, "max", False),
            (hi + timedelta(days=1), "max+1", True),
        ]
    elif points == 4:
        date_candidates = [
            (lo - timedelta(days=2), "min-2", True),
            (lo - timedelta(days=1), "min-1", True),
            (lo, "min", False),
            (lo + timedelta(days=1), "min+1", False),
            (hi - timedelta(days=1), "max-1", False),
            (hi, "max", False),
            (hi + timedelta(days=1), "max+1", True),
            (hi + timedelta(days=2), "max+2", True),
        ]
    else:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    for d, label, is_err in date_candidates:
        key = _format_date(d, fmt)
        if key not in results:
            results[key] = BVAValue(value=key, is_error=is_err, vtype="date", label=label)

    # --- Zusatzwerte ---
    if extras.get("leap_year"):
        # Finde ein Schaltjahr im Bereich
        for y in range(lo.year, hi.year + 1):
            if _is_leap_year(y):
                feb29 = date(y, 2, 29)
                if feb29 >= lo and feb29 <= hi:
                    key = _format_date(feb29, fmt)
                    if key not in results:
                        results[key] = BVAValue(
                            value=key, is_error=False, vtype="date",
                            label=f"29.02. {y} (Schaltjahr)"
                        )
                    break

    if extras.get("non_leap_year"):
        # Finde ein Nicht-Schaltjahr im Bereich
        for y in range(lo.year, hi.year + 1):
            if not _is_leap_year(y):
                # 29.02 ist in Nicht-Schaltjahren ungueltig
                feb_start = date(y, 2, 1)
                if feb_start >= lo or feb_start <= hi:
                    key = _format_date(date(y, 2, 28), fmt).replace("28", "29")
                    if key not in results:
                        results[key] = BVAValue(
                            value=key, is_error=True, vtype="date",
                            label=f"29.02. {y} (Nicht-Schaltjahr, ungueltig)"
                        )
                    break

    if extras.get("month_ends"):
        for d in _month_ends_in_range(lo, hi):
            key = _format_date(d, fmt)
            if key not in results:
                results[key] = BVAValue(
                    value=key, is_error=False, vtype="date",
                    label=f"Monatsende {d.day}.{d.month:02d}"
                )

    if extras.get("year_transition"):
        for d in _year_transitions_in_range(lo, hi):
            key = _format_date(d, fmt)
            if key not in results:
                results[key] = BVAValue(
                    value=key, is_error=False, vtype="date",
                    label="Jahreswechsel"
                )

    if extras.get("invalid_date"):
        # 31.04. als Beispiel fuer ungultiges Datum
        invalid = date(lo.year, 4, 30) + timedelta(days=1)  # 31.04. -> wird zu 30.04. + 1 = 1.5. in Python
        # Wir muessen ein explizit ungultiges Datum als String erzeugen
        invalid_str = f"{lo.year}-04-31" if fmt == "iso" else f"31.04.{lo.year}"
        if invalid_str not in results:
            results[invalid_str] = BVAValue(
                value=invalid_str, is_error=True, vtype="date",
                label="Ungultiges Datum (31.04.)"
            )

    # Sortieren: BVAValue nach Datum (ISO-Format sortiert lexikalisch korrekt)
    sorted_results = sorted(results.values(), key=lambda v: v.value)
    return sorted_results


# ---------------------------------------------------------------------------
# BVA fuer Uhrzeit
# ---------------------------------------------------------------------------

def _parse_time(raw: str) -> time:
    """Parsiert eine Uhrzeit im Format 'HH:MM' oder 'HH:MM:SS'."""
    try:
        parts = raw.strip().split(":")
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            return time(h, m)
        elif len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return time(h, m, s)
        raise ValueError
    except (ValueError, IndexError) as exc:
        raise BVAError(f"Ungültige Uhrzeit: {raw!r}. Format: HH:MM oder HH:MM:SS") from exc


def _format_time(t: time, fmt: str = "HH:MM") -> str:
    """Formatiert eine Uhrzeit."""
    if fmt == "HH:MM:SS":
        return t.strftime("%H:%M:%S")
    return t.strftime("%H:%M")


def _time_to_seconds(t: time) -> int:
    """Konvertiert time zu Sekunden seit Mitternacht."""
    return t.hour * 3600 + t.minute * 60 + t.second


def _seconds_to_time(sec: int) -> Optional[time]:
    """Konvertiert Sekunden seit Mitternacht zu time. None bei ungültigen Werten."""
    if sec < 0 or sec >= 86400:
        return None  # Ungültig
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return time(h, m, s)


def generate_bva_time(
    min_time: str,
    max_time: str,
    points: int = 2,
    fmt: str = "HH:MM",
    step: str = "minute",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """
    REQ-6007: BVA fuer Uhrzeitbereiche.

    2/3/4-Punkt-Methode mit Schritt=Sekunde oder Minute.
    Zusatzwerte: 00:00, 23:59(:59), 24:00 (ungultig), Mitternachtsuebergang.

    Args:
        min_time: Untere Grenze (HH:MM oder HH:MM:SS)
        max_time: Obere Grenze
        points: 2, 3 oder 4
        fmt: 'HH:MM' oder 'HH:MM:SS'
        step: 'minute' (60s) oder 'second' (1s)
        extras: Dict mit Booleans:
            - 'midnight': 00:00
            - 'end_of_day': 23:59(:59)
            - 'invalid_2400': 24:00 (ungultig)
            - 'midnight_crossing': Bereich ueber Mitternacht

    Returns:
        Liste von BVAValue-Objekten.
    """
    if extras is None:
        extras = {}

    lo = _parse_time(min_time)
    hi = _parse_time(max_time)

    step_seconds = 60 if step == "minute" else 1

    lo_sec = _time_to_seconds(lo)
    hi_sec = _time_to_seconds(hi)

    # Mitternachtsuebergang: wenn min > max, Bereich geht ueber Mitternacht
    crosses_midnight = lo_sec > hi_sec

    results: dict[str, BVAValue] = {}

    if points == 2:
        candidates = [
            (lo_sec - step_seconds, "min-1", True),
            (lo_sec, "min", False),
            (hi_sec, "max", False),
            (hi_sec + step_seconds, "max+1", True),
        ]
    elif points == 3:
        candidates = [
            (lo_sec - step_seconds, "min-1", True),
            (lo_sec, "min", False),
            (lo_sec + step_seconds, "min+1", False),
            (hi_sec - step_seconds, "max-1", False),
            (hi_sec, "max", False),
            (hi_sec + step_seconds, "max+1", True),
        ]
    elif points == 4:
        candidates = [
            (lo_sec - step_seconds * 2, "min-2", True),
            (lo_sec - step_seconds, "min-1", True),
            (lo_sec, "min", False),
            (lo_sec + step_seconds, "min+1", False),
            (hi_sec - step_seconds, "max-1", False),
            (hi_sec, "max", False),
            (hi_sec + step_seconds, "max+1", True),
            (hi_sec + step_seconds * 2, "max+2", True),
        ]
    else:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    for sec, label, is_err in candidates:
        t = _seconds_to_time(sec)
        if t is not None:
            key = _format_time(t, fmt)
            if key not in results:
                results[key] = BVAValue(value=key, is_error=is_err, vtype="time", label=label)
        else:
            # Ungültige Uhrzeit (z.B. < 0 oder >= 86400)
            if sec < 0:
                # Vor Mitternacht: negativer Offset
                abs_sec = abs(sec)
                h = abs_sec // 3600
                m = (abs_sec % 3600) // 60
                fake = f"-{h:02d}:{m:02d}"
                if fake not in results:
                    results[fake] = BVAValue(
                        value=fake, is_error=True, vtype="time",
                        label=f"{label} (vor Mitternacht, ungueltig)"
                    )
            elif sec >= 86400:
                h = sec // 3600
                m = (sec % 3600) // 60
                fake = f"{h:02d}:{m:02d}"
                if fake not in results:
                    results[fake] = BVAValue(
                        value=fake, is_error=True, vtype="time",
                        label=f"{label} (ungueltig)"
                    )

    # --- Zusatzwerte ---
    if extras.get("midnight"):
        t = time(0, 0)
        key = _format_time(t, fmt)
        if key not in results:
            results[key] = BVAValue(value=key, is_error=False, vtype="time", label="00:00 (Mitternacht)")

    if extras.get("end_of_day"):
        if fmt == "HH:MM:SS":
            t = time(23, 59, 59)
        else:
            t = time(23, 59)
        key = _format_time(t, fmt)
        if key not in results:
            results[key] = BVAValue(value=key, is_error=False, vtype="time", label="23:59 (Ende des Tages)")

    if extras.get("invalid_2400"):
        invalid = "24:00:00" if fmt == "HH:MM:SS" else "24:00"
        if invalid not in results:
            results[invalid] = BVAValue(
                value=invalid, is_error=True, vtype="time",
                label="24:00 (ungueltig)"
            )

    if extras.get("midnight_crossing") and crosses_midnight:
        # Mitternacht ist im Bereich enthalten
        t = time(0, 0)
        key = _format_time(t, fmt)
        if key not in results:
            results[key] = BVAValue(
                value=key, is_error=False, vtype="time",
                label="Mitternachtsuebergang"
            )

    sorted_results = sorted(results.values(), key=lambda v: v.value)
    return sorted_results


# ---------------------------------------------------------------------------
# BVA fuer Datum+Uhrzeit
# ---------------------------------------------------------------------------

def _parse_datetime(raw: str) -> datetime:
    """Parsiert ein Datum+Uhrzeit im ISO-Format."""
    try:
        return datetime.fromisoformat(raw.strip())
    except (ValueError, AttributeError) as exc:
        raise BVAError(f"Ungültiges Datum+Uhrzeit: {raw!r}. Format: ISO 8601") from exc


def generate_bva_datetime(
    min_dt: str,
    max_dt: str,
    points: int = 2,
    step: str = "minute",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """
    REQ-6007: BVA fuer Datum+Uhrzeit.

    Kombination aus Datum- und Uhrzeit-BVA.
    Grenzwerte an den Bereichsgrenzen mit der kleinsten gewaehlten Einheit.

    Args:
        min_dt: Untere Grenze (ISO 8601)
        max_dt: Obere Grenze
        points: 2, 3 oder 4
        step: 'minute' (60s) oder 'second' (1s)
        extras: Dict mit Booleans (wie bei Datum und Uhrzeit kombiniert)

    Returns:
        Liste von BVAValue-Objekten.
    """
    if extras is None:
        extras = {}

    lo = _parse_datetime(min_dt)
    hi = _parse_datetime(max_dt)
    if lo > hi:
        lo, hi = hi, lo

    step_seconds = 60 if step == "minute" else 1

    results: dict[str, BVAValue] = {}

    if points == 2:
        candidates = [
            (lo - timedelta(seconds=step_seconds), "min-1", True),
            (lo, "min", False),
            (hi, "max", False),
            (hi + timedelta(seconds=step_seconds), "max+1", True),
        ]
    elif points == 3:
        candidates = [
            (lo - timedelta(seconds=step_seconds), "min-1", True),
            (lo, "min", False),
            (lo + timedelta(seconds=step_seconds), "min+1", False),
            (hi - timedelta(seconds=step_seconds), "max-1", False),
            (hi, "max", False),
            (hi + timedelta(seconds=step_seconds), "max+1", True),
        ]
    elif points == 4:
        candidates = [
            (lo - timedelta(seconds=step_seconds * 2), "min-2", True),
            (lo - timedelta(seconds=step_seconds), "min-1", True),
            (lo, "min", False),
            (lo + timedelta(seconds=step_seconds), "min+1", False),
            (hi - timedelta(seconds=step_seconds), "max-1", False),
            (hi, "max", False),
            (hi + timedelta(seconds=step_seconds), "max+1", True),
            (hi + timedelta(seconds=step_seconds * 2), "max+2", True),
        ]
    else:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    for dt, label, is_err in candidates:
        key = dt.isoformat()
        if key not in results:
            results[key] = BVAValue(value=key, is_error=is_err, vtype="datetime", label=label)

    # Zusatzwerte aus Datum- und Uhrzeit-BVA kombinieren
    if extras.get("leap_year"):
        for y in range(lo.year, hi.year + 1):
            if _is_leap_year(y):
                feb29 = datetime(y, 2, 29, lo.hour, lo.minute, lo.second)
                if feb29 >= lo and feb29 <= hi:
                    key = feb29.isoformat()
                    if key not in results:
                        results[key] = BVAValue(
                            value=key, is_error=False, vtype="datetime",
                            label=f"29.02. {y} (Schaltjahr)"
                        )
                    break

    if extras.get("midnight"):
        midnight = datetime(lo.year, lo.month, lo.day, 0, 0, 0)
        if midnight >= lo and midnight <= hi:
            key = midnight.isoformat()
            if key not in results:
                results[key] = BVAValue(
                    value=key, is_error=False, vtype="datetime",
                    label="00:00 (Mitternacht)"
                )

    sorted_results = sorted(results.values(), key=lambda v: v.value)
    return sorted_results


# ---------------------------------------------------------------------------
# BVA fuer Stringlaengen
# ---------------------------------------------------------------------------

def generate_bva_strlen(
    min_len: int,
    max_len: int,
    points: int = 2,
    charset: str = "alpha",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """
    REQ-6007: BVA fuer Stringlaengen.

    min-1, min, max, max+1 nach gewaehlter Methode.
    Zusatzwerte: Laenge 0 (leer), nur Leerzeichen, fuehrende/abschliessende Leerzeichen.
    Lange Werte (>500) als symbolisch.

    Args:
        min_len: Minimale Laenge (>= 0)
        max_len: Maximale Laenge (>= min_len)
        points: 2, 3 oder 4
        charset: Zeichenvorrat ('alpha', 'alnum', 'alpha_de', 'special', 'unicode')
        extras: Dict mit Booleans:
            - 'empty': Laenge 0 (leerer String)
            - 'whitespace_only': Nur Leerzeichen
            - 'leading_whitespace': Fuehrende Leerzeichen
            - 'trailing_whitespace': Abschliessende Leerzeichen

    Returns:
        Liste von BVAValue-Objekten.
    """
    from .symbolic_values import (
        should_be_symbolic,
        generate_symbolic_string,
        make_value,
        MAX_VALUE_LENGTH,
        CHARSETS,
    )

    if extras is None:
        extras = {}

    if min_len < 0:
        raise BVAError(f"min_len muss >= 0 sein, nicht {min_len}")
    if max_len < min_len:
        min_len, max_len = max_len, min_len
    if charset not in CHARSETS:
        raise BVAError(f"Unbekanntes charset: {charset!r}. Erlaubt: {list(CHARSETS.keys())}")

    results: dict[int, BVAValue] = {}  # key = length

    def _add_length(length: int, label: str, is_err: bool):
        if length in results:
            return
        if length < 0:
            # Negative Laenge: ungultig
            results[length] = BVAValue(
                value=f"<STR len={length} charset={charset}>",
                is_error=True,
                vtype="strlen",
                label=f"{label} (negative Laenge, ungueltig)"
            )
        elif length == 0:
            results[length] = BVAValue(
                value="",
                is_error=is_err,
                vtype="strlen",
                label=label
            )
        elif should_be_symbolic(length):
            results[length] = BVAValue(
                value=generate_symbolic_string(length, charset),
                is_error=is_err,
                vtype="strlen",
                label=label
            )
        else:
            results[length] = BVAValue(
                value=make_value(length, charset),
                is_error=is_err,
                vtype="strlen",
                label=label
            )

    # --- BVA-Grenzwerte ---
    if points == 2:
        _add_length(min_len - 1, "min-1", True)
        _add_length(min_len, "min", False)
        _add_length(max_len, "max", False)
        _add_length(max_len + 1, "max+1", True)
    elif points == 3:
        _add_length(min_len - 1, "min-1", True)
        _add_length(min_len, "min", False)
        _add_length(min_len + 1, "min+1", False)
        _add_length(max_len - 1, "max-1", False)
        _add_length(max_len, "max", False)
        _add_length(max_len + 1, "max+1", True)
    elif points == 4:
        _add_length(min_len - 2, "min-2", True)
        _add_length(min_len - 1, "min-1", True)
        _add_length(min_len, "min", False)
        _add_length(min_len + 1, "min+1", False)
        _add_length(max_len - 1, "max-1", False)
        _add_length(max_len, "max", False)
        _add_length(max_len + 1, "max+1", True)
        _add_length(max_len + 2, "max+2", True)
    else:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")

    # --- Zusatzwerte ---
    if extras.get("empty"):
        _add_length(0, "Leerer String (Laenge 0)", min_len > 0)

    if extras.get("whitespace_only"):
        # Leerzeichen-String innerhalb des gueltigen Bereichs,
        # aber nicht an einer Boundary (min oder max)
        ws_len = (min_len + max_len) // 2
        if ws_len < min_len:
            ws_len = min_len + 1
        if ws_len > max_len:
            ws_len = max_len - 1
        if ws_len < 1:
            ws_len = 1
        if ws_len > 0 and not should_be_symbolic(ws_len):
            val = " " * ws_len
            if ws_len not in results:
                results[ws_len] = BVAValue(
                    value=val,
                    is_error=True,
                    vtype="strlen",
                    label="Nur Leerzeichen"
                )

    if extras.get("leading_whitespace"):
        # min_len + 1 fuehrendes Leerzeichen
        lead_len = min_len + 1
        if lead_len not in results:
            if should_be_symbolic(lead_len):
                val = generate_symbolic_string(lead_len, charset)
            else:
                val = " " + make_value(min_len, charset)
            results[lead_len] = BVAValue(
                value=val,
                is_error=True,
                vtype="strlen",
                label="Fuehrendes Leerzeichen"
            )

    if extras.get("trailing_whitespace"):
        trail_len = min_len + 1
        label = "Abschliessendes Leerzeichen"
        if trail_len not in results:
            if should_be_symbolic(trail_len):
                val = generate_symbolic_string(trail_len, charset)
            else:
                val = make_value(min_len, charset) + " "
            results[trail_len] = BVAValue(
                value=val,
                is_error=True,
                vtype="strlen",
                label=label
            )

    # Sortieren nach Laenge (key)
    sorted_results = sorted(results.values(), key=lambda v: (len(v.value) if not v.is_error else 0, v.value))
    return sorted_results
