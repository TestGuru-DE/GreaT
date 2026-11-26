"""
Boundary Value Analysis (BVA) - ISTQB-konform.

2-Wert: [min-1, min, max, max+1]                              (4 Werte)
3-Wert: [min-1, min, min+1, max-1, max, max+1]                (6 Werte)
4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]  (8 Werte)

Quelle: ISTQB Foundation Level Syllabus, Boundary Value Analysis.

REQ-6007: Erweiterung fuer Datum, Uhrzeit, Datum+Uhrzeit und Stringlaengen.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Union, Optional


def _normalize_decimal_text(raw: Union[str, int, float]) -> str:
    return str(raw).strip().replace(",", ".")


class BVAError(ValueError):
    """Wird geworfen bei ungültigen BVA-Parametern (Rückwärtskompatibilität)."""


# BUG C-04: Grenzen fuer Zahlen. Darueber rundet Decimal (28 Stellen) min-1 zu min
# bzw. str(int(...)) erzeugt riesige Zeichenketten.
_MAX_DECIMALS = 10


def _parse_number(raw: Union[str, int, float]) -> Decimal:
    """Zahl fuer die BVA lesen; BVAError statt 500 bei NaN, Unendlich, Riesenwerten, Text."""
    try:
        value = Decimal(_normalize_decimal_text(raw))
    except ArithmeticError as exc:  # InvalidOperation, aber auch Overflow (z. B. 1e999999999)
        raise BVAError(f"Ungültige Zahl: {raw!r}") from exc
    if not value.is_finite():
        raise BVAError(f"Ungültige Zahl: {raw!r} (NaN/Unendlich nicht erlaubt)")
    # Groesse ueber den Exponenten pruefen: abs() wuerde bei 1e999999999 selbst ueberlaufen
    if value != 0 and value.adjusted() >= 15:
        raise BVAError(f"Zahl zu groß: {raw!r} (Betrag maximal 10^15)")
    if value != 0 and value.as_tuple().exponent < -_MAX_DECIMALS:
        raise BVAError(f"Zu viele Nachkommastellen: {raw!r} (maximal {_MAX_DECIMALS})")
    return value


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
    lo = _parse_number(min_val)  # BUG C-04
    hi = _parse_number(max_val)

    if lo > hi:  # REQ-0306: Einzelbereich wird automatisch korrigiert
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
    return _parse_number(text)  # BUG C-04: z. B. Datum an /bva/ranges -> 400 statt 500


def _format_bound(raw: str, is_min: bool) -> str:
    if raw is None or str(raw).strip() == "":
        return "-∞" if is_min else "∞"
    return str(raw)


def _normalize_range(r: BVARange) -> tuple[Optional[Decimal], Optional[Decimal], str, str]:
    lo = _parse_optional_decimal(r.min_val)
    hi = _parse_optional_decimal(r.max_val)
    if lo is not None and hi is not None and lo > hi:
        # BUG C-05 / REQ-6007: Min > Max wird gemeldet statt still vertauscht
        raise BVAError(f"Min ist größer als Max: {r.min_val} > {r.max_val}")
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
#
# Alle Typen nutzen dieselbe Mehrbereichs-Logik wie Zahlen (REQ-3064):
# - Jeder Bereich hat Min/Max und gueltig/ungueltig (allowed).
# - Min > Max und ueberlappende Bereiche werden abgelehnt (BUG C-05).
#   Ausnahme Uhrzeit: Min > Max ist ein Bereich ueber Mitternacht.
# - Kandidaten (min-1, min, ... je nach 2/3/4-Punkt-Methode) werden je Bereich
#   erzeugt, dedupliziert und nach ZUGEHOERIGKEIT eingestuft: in einem gueltigen
#   Bereich = gueltig, sonst Fehlerwert (keine widerspruechlichen Doppelwerte).
# - Werte ausserhalb des darstellbaren Bereichs (vor 0001-01-01, nach 9999-12-31,
#   negative Laengen) entfallen statt einen Fehler 500 auszuloesen (BUG C-04).
# - Zusatzwerte entstehen nur im bzw. an einem Bereich (BUG C-07).
# ---------------------------------------------------------------------------

@dataclass
class BVAValue:
    """Ein BVA-Wert mit Metadaten (REQ-6007)."""
    value: str
    is_error: bool
    vtype: str  # 'date', 'time', 'datetime', 'strlen', 'number'
    label: str = ""  # Beschreibung, z.B. "min", "29.02. Schaltjahr"


@dataclass
class TypedRange:
    """Ein Bereich fuer die typisierte BVA (Grenzen als Text wie im Dialog)."""
    min_val: str
    max_val: str
    allowed: bool = True


# Methode -> (Offset, Label, liegt an der Untergrenze?)
_OFFSETS = {
    2: [(-1, "min-1", True), (0, "min", True), (0, "max", False), (1, "max+1", False)],
    3: [(-1, "min-1", True), (0, "min", True), (1, "min+1", True),
        (-1, "max-1", False), (0, "max", False), (1, "max+1", False)],
    4: [(-2, "min-2", True), (-1, "min-1", True), (0, "min", True), (1, "min+1", True),
        (-1, "max-1", False), (0, "max", False), (1, "max+1", False), (2, "max+2", False)],
}

# Obergrenze fuer aufzaehlende Zusatzwerte (Monatsenden, Jahreswechsel): je Bereich
# die ersten und letzten 12, damit lange Bereiche nicht tausende Werte erzeugen.
_MAX_ENUM_EXTRAS = 12


def _offsets(points: int):
    if points not in _OFFSETS:
        raise BVAError(f"points muss 2, 3 oder 4 sein, nicht {points!r}")
    return _OFFSETS[points]


def _normalize_extras(extras) -> dict:
    """BUG C-04: Zusatzwerte als Dict {name: bool} oder Liste von Namen."""
    if extras is None:
        return {}
    if isinstance(extras, dict):
        return {str(k): bool(v) for k, v in extras.items()}
    if isinstance(extras, (list, tuple, set)):
        return {str(k): True for k in extras}
    raise BVAError("extras muss ein Objekt {Name: true/false} oder eine Liste von Namen sein")


def _limit_enum(values: list) -> list:
    if len(values) <= 2 * _MAX_ENUM_EXTRAS:
        return values
    return values[:_MAX_ENUM_EXTRAS] + values[-_MAX_ENUM_EXTRAS:]


def _check_overlaps(intervals: list[tuple]) -> None:
    """Intervalle (lo, hi) eines geordneten Typs duerfen sich nicht ueberschneiden."""
    ordered = sorted(intervals)
    for (lo1, hi1), (lo2, hi2) in zip(ordered, ordered[1:]):
        if lo2 <= hi1:
            raise BVAError("Bereiche dürfen sich nicht überschneiden.")


class _Collector:
    """Sammelt Werte je Schluessel; Einstufung per Zugehoerigkeit zu den Bereichen."""

    def __init__(self, vtype: str, classify, render, sort_key):
        self.vtype, self.classify, self.render, self.sort_key = vtype, classify, render, sort_key
        self.items: dict = {}

    def add(self, key, label: str, force_error: bool = False, text: Optional[str] = None) -> None:
        value = text if text is not None else self.render(key)
        if value in self.items:
            return
        is_error = True if force_error else self.classify(key)
        self.items[value] = (self.sort_key(key), BVAValue(value=value, is_error=is_error,
                                                          vtype=self.vtype, label=label))

    def result(self) -> list[BVAValue]:
        return [v for _, v in sorted(self.items.values(), key=lambda item: item[0])]


def _in_allowed(intervals_with_flag: list[tuple], key) -> bool:
    """True, wenn key in einem gueltigen Bereich liegt (sonst Fehlerwert)."""
    for lo, hi, allowed in intervals_with_flag:
        if lo <= key <= hi:
            return allowed
    return False


# --- Datum ----------------------------------------------------------------

def _parse_date(raw: str) -> date:
    """Parsiert ein Datum im Format 'YYYY-MM-DD'."""
    try:
        parts = str(raw).strip().split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return date(y, m, d)
    except (ValueError, IndexError, TypeError, OverflowError) as exc:
        raise BVAError(f"Ungültiges Datum: {raw!r}. Format: YYYY-MM-DD") from exc


_DATE_FORMATS = ("iso", "de")


def _format_date_parts(y: int, m: int, d: int, fmt: str) -> str:
    # Ohne strftime: Jahre < 1000 werden plattformunabhaengig vierstellig ausgegeben
    return f"{d:02d}.{m:02d}.{y:04d}" if fmt == "de" else f"{y:04d}-{m:02d}-{d:02d}"


def _format_date(d: date, fmt: str = "iso") -> str:
    """Formatiert ein Datum."""
    return _format_date_parts(d.year, d.month, d.day, fmt)


def _is_leap_year(year: int) -> bool:
    """Gregorianischer Schaltjahr-Test."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _last_day_of_month(year: int, month: int) -> date:
    """Letzter Tag eines Monats (BUG C-04: auch fuer Dezember ein Datum)."""
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _months_in_range(start: date, end: date):
    """(Jahr, Monat) fuer jeden Monat, der den Bereich beruehrt (inkl. Startmonat)."""
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def _month_ends_in_range(start: date, end: date) -> list[date]:
    """Alle Monatsenden im Bereich [start, end] (BUG C-08: inkl. Startmonat)."""
    return [last for y, m in _months_in_range(start, end)
            if start <= (last := _last_day_of_month(y, m)) <= end]


def _year_transitions_in_range(start: date, end: date) -> list[date]:
    """31.12. und 01.01. im Bereich [start, end]."""
    results = []
    for y in range(start.year, end.year + 1):
        for d in (date(y, 1, 1), date(y, 12, 31)):
            if start <= d <= end:
                results.append(d)
    return results


def generate_multi_range_bva_date(
    ranges: list[TypedRange],
    points: int = 2,
    fmt: str = "iso",
    extras=None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer Datumsbereiche (Schritt 1 Tag), mehrere Bereiche.

    Zusatzwerte (extras): leap_year, non_leap_year, month_ends,
    year_transition, invalid_date. Sie entstehen nur im/an einem Bereich.
    """
    extras = _normalize_extras(extras)
    if fmt not in _DATE_FORMATS:
        raise BVAError(f"Unbekanntes Datumsformat: {fmt!r}. Erlaubt: iso, de")
    parsed = []
    for r in ranges:
        lo, hi = _parse_date(r.min_val), _parse_date(r.max_val)
        if lo > hi:
            raise BVAError(f"Min ist größer als Max: {r.min_val} > {r.max_val}")
        parsed.append((lo.toordinal(), hi.toordinal(), r.allowed))
    _check_overlaps([(lo, hi) for lo, hi, _ in parsed])

    first, last = date.min.toordinal(), date.max.toordinal()
    out = _Collector(
        "date",
        classify=lambda key: not _in_allowed(parsed, key),
        render=lambda key: _format_date(date.fromordinal(key), fmt),
        sort_key=lambda key: (key, 0),
    )
    for lo, hi, _ in parsed:
        for offset, label, at_min in _offsets(points):
            key = (lo if at_min else hi) + offset
            if first <= key <= last:  # BUG C-04: vor 0001-01-01 / nach 9999-12-31 gibt es nichts
                out.add(key, label)

    for lo_o, hi_o, _ in parsed:
        lo, hi = date.fromordinal(lo_o), date.fromordinal(hi_o)
        if extras.get("leap_year"):
            for y in range(lo.year, hi.year + 1):
                if _is_leap_year(y) and lo <= date(y, 2, 29) <= hi:
                    out.add(date(y, 2, 29).toordinal(), f"29.02. {y} (Schaltjahr)")
                    break
        if extras.get("non_leap_year"):
            # BUG C-07: nur ein Jahr, dessen Februarende im Bereich liegt; Jahreszahl bleibt unveraendert
            for y in range(lo.year, hi.year + 1):
                feb28 = date(y, 2, 28)
                if not _is_leap_year(y) and lo <= feb28 <= hi:
                    out.add(feb28.toordinal(), f"29.02. {y} (Nicht-Schaltjahr, ungueltig)",
                            force_error=True, text=_format_date_parts(y, 2, 29, fmt))
                    break
        if extras.get("month_ends"):
            for d in _limit_enum(_month_ends_in_range(lo, hi)):
                out.add(d.toordinal(), f"Monatsende {d.day}.{d.month:02d}.")
        if extras.get("year_transition"):
            for d in _limit_enum(_year_transitions_in_range(lo, hi)):
                out.add(d.toordinal(), "Jahreswechsel")
        if extras.get("invalid_date"):
            # BUG C-07: 31. eines 30-Tage-Monats, dessen 30. im Bereich liegt
            for y, m in _months_in_range(lo, hi):
                last_day = _last_day_of_month(y, m)
                if last_day.day == 30 and lo <= last_day <= hi:
                    out.add(last_day.toordinal(), f"Ungueltiges Datum (31.{m:02d}.)",
                            force_error=True, text=_format_date_parts(y, m, 31, fmt))
                    break
    return out.result()


def generate_bva_date(
    min_date: str,
    max_date: str,
    points: int = 2,
    fmt: str = "iso",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer einen Datumsbereich (siehe generate_multi_range_bva_date)."""
    return generate_multi_range_bva_date([TypedRange(min_date, max_date)], points, fmt, extras)


# --- Uhrzeit ----------------------------------------------------------------

_DAY = 86400
_TIME_FORMATS = ("HH:MM", "HH:MM:SS")
_STEPS = {"minute": 60, "second": 1}


def _parse_time(raw: str) -> time:
    """Parsiert eine Uhrzeit im Format 'HH:MM' oder 'HH:MM:SS'."""
    try:
        parts = str(raw).strip().split(":")
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        if len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
        raise ValueError
    except (ValueError, IndexError, TypeError) as exc:
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
    if sec < 0 or sec >= _DAY:
        return None
    return time(sec // 3600, (sec % 3600) // 60, sec % 60)


def _step_seconds(step: str) -> int:
    if step not in _STEPS:
        raise BVAError(f"Unbekannte Schrittweite: {step!r}. Erlaubt: minute, second")
    return _STEPS[step]


def generate_multi_range_bva_time(
    ranges: list[TypedRange],
    points: int = 2,
    fmt: str = "HH:MM",
    step: str = "minute",
    extras=None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer Uhrzeiten, mehrere Bereiche.

    Min > Max bedeutet einen Bereich ueber Mitternacht (z. B. 22:00-02:00).
    Nachbarwerte werden ueber Mitternacht fortgesetzt (BUG C-09: 00:00 minus
    1 Minute = 23:59 statt "-00:01"; 23:59 plus 1 Minute = 00:00 statt "24:00").
    Zusatzwerte: midnight, end_of_day, invalid_2400, midnight_crossing.
    """
    extras = _normalize_extras(extras)
    if fmt not in _TIME_FORMATS:
        raise BVAError(f"Unbekanntes Zeitformat: {fmt!r}. Erlaubt: HH:MM, HH:MM:SS")
    step_sec = _step_seconds(step)
    if step_sec == 1:
        fmt = "HH:MM:SS"  # Sekundenschritte brauchen Sekunden im Format

    parsed = []    # (lo, hi, allowed) in Sekunden; lo > hi = ueber Mitternacht
    intervals = []  # fuer die Ueberschneidungspruefung, Mitternachtsbereiche geteilt
    for r in ranges:
        lo, hi = _time_to_seconds(_parse_time(r.min_val)), _time_to_seconds(_parse_time(r.max_val))
        parsed.append((lo, hi, r.allowed))
        intervals += [(lo, hi)] if lo <= hi else [(lo, _DAY - 1), (0, hi)]
    _check_overlaps(intervals)

    def contains(lo, hi, sec):
        return lo <= sec <= hi if lo <= hi else (sec >= lo or sec <= hi)

    def classify(sec):
        for lo, hi, allowed in parsed:
            if contains(lo, hi, sec):
                return not allowed
        return True

    out = _Collector("time", classify=classify,
                     render=lambda sec: _format_time(_seconds_to_time(sec), fmt),
                     sort_key=lambda sec: (sec, 0))
    for lo, hi, _ in parsed:
        for offset, label, at_min in _offsets(points):
            out.add(((lo if at_min else hi) + offset * step_sec) % _DAY, label)

    if extras.get("midnight"):
        out.add(0, "00:00 (Mitternacht)")
    if extras.get("end_of_day"):
        out.add(_DAY - (1 if fmt == "HH:MM:SS" else 60), "23:59 (Ende des Tages)")
    if extras.get("invalid_2400"):
        text = "24:00:00" if fmt == "HH:MM:SS" else "24:00"
        out.add(_DAY, "24:00 (ungueltig)", force_error=True, text=text)
    if extras.get("midnight_crossing") and any(lo > hi for lo, hi, _ in parsed):
        out.add(0, "Mitternachtsuebergang")
    return out.result()


def generate_bva_time(
    min_time: str,
    max_time: str,
    points: int = 2,
    fmt: str = "HH:MM",
    step: str = "minute",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer einen Uhrzeitbereich (siehe generate_multi_range_bva_time)."""
    return generate_multi_range_bva_time([TypedRange(min_time, max_time)], points, fmt, step, extras)


# --- Datum+Uhrzeit -----------------------------------------------------------

def _parse_tz(raw: Optional[str]):
    """BUG C-10: Zeitzone als ISO-8601-Offset (+02:00, -05:30, Z)."""
    if raw is None or str(raw).strip() == "":
        return None
    text = str(raw).strip()
    if text.upper() == "Z":
        return timezone.utc
    try:
        return datetime.fromisoformat("2000-01-01T00:00:00" + text).tzinfo
    except ValueError as exc:
        raise BVAError(f"Ungültige Zeitzone: {raw!r}. Format: +HH:MM, -HH:MM oder Z") from exc


def _parse_datetime(raw: str, tz=None) -> datetime:
    """Parsiert ein Datum+Uhrzeit im ISO-Format; ohne Offset gilt die Zeitzone tz."""
    try:
        dt = datetime.fromisoformat(str(raw).strip())
    except (ValueError, AttributeError, TypeError) as exc:
        raise BVAError(f"Ungültiges Datum+Uhrzeit: {raw!r}. Format: ISO 8601") from exc
    if tz is not None:
        dt = dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)
    return dt


def generate_multi_range_bva_datetime(
    ranges: list[TypedRange],
    points: int = 2,
    step: str = "minute",
    extras=None,
    tz: Optional[str] = None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer Datum+Uhrzeit, mehrere Bereiche.

    tz (Formatoption): Werte werden mit diesem Offset ausgegeben; Eingaben ohne
    Offset erhalten ihn. Ohne tz duerfen Eingaben nicht gemischt mit und ohne
    Offset sein (BUG C-04).
    Zusatzwerte: leap_year (29.02. im Bereich), midnight (erste Mitternacht im Bereich).
    """
    extras = _normalize_extras(extras)
    step_td = timedelta(seconds=_step_seconds(step))
    tzinfo = _parse_tz(tz)

    parsed = []
    for r in ranges:
        lo, hi = _parse_datetime(r.min_val, tzinfo), _parse_datetime(r.max_val, tzinfo)
        if (lo.tzinfo is None) != (hi.tzinfo is None) or (
                parsed and (parsed[0][0].tzinfo is None) != (lo.tzinfo is None)):
            raise BVAError("Angaben mit und ohne Zeitzone gemischt. Bitte einheitlich angeben "
                           "oder die Zeitzonen-Option setzen.")
        if lo > hi:
            raise BVAError(f"Min ist größer als Max: {r.min_val} > {r.max_val}")
        parsed.append((lo, hi, r.allowed))
    _check_overlaps([(lo, hi) for lo, hi, _ in parsed])

    out = _Collector("datetime", classify=lambda dt: not _in_allowed(parsed, dt),
                     render=lambda dt: dt.isoformat(), sort_key=lambda dt: (dt, 0))
    for lo, hi, _ in parsed:
        for offset, label, at_min in _offsets(points):
            try:
                out.add((lo if at_min else hi) + offset * step_td, label)
            except OverflowError:
                pass  # BUG C-04: jenseits von 0001/9999 gibt es keinen Wert

    for lo, hi, _ in parsed:
        if extras.get("leap_year"):
            for y in range(lo.year, hi.year + 1):
                if _is_leap_year(y):
                    feb29 = lo.replace(year=y, month=2, day=29)
                    if lo <= feb29 <= hi:
                        out.add(feb29, f"29.02. {y} (Schaltjahr)")
                        break
        if extras.get("midnight"):
            try:
                midnight = lo.replace(hour=0, minute=0, second=0, microsecond=0)
                if midnight < lo:
                    midnight += timedelta(days=1)
            except OverflowError:
                continue
            if midnight <= hi:
                out.add(midnight, "00:00 (Mitternacht)")
    return out.result()


def generate_bva_datetime(
    min_dt: str,
    max_dt: str,
    points: int = 2,
    step: str = "minute",
    extras: Optional[dict] = None,
    tz: Optional[str] = None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer einen Datum+Uhrzeit-Bereich."""
    return generate_multi_range_bva_datetime([TypedRange(min_dt, max_dt)], points, step, extras, tz)


# --- Stringlaenge -------------------------------------------------------------

_MAX_STRLEN = 10 ** 9


def _parse_length(raw) -> int:
    text = str(raw).strip()
    if not text.isdigit():
        raise BVAError(f"Stringlänge muss eine ganze Zahl >= 0 sein, nicht {raw!r}")
    value = int(text)
    if value > _MAX_STRLEN:
        raise BVAError(f"Stringlänge zu groß: {value} (maximal {_MAX_STRLEN})")
    return value


def generate_multi_range_bva_strlen(
    ranges: list[TypedRange],
    points: int = 2,
    charset: str = "alpha",
    extras=None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer Stringlaengen, mehrere Bereiche.

    Negative Laengen entfallen (BUG C-11, frueher "<STR len=-1>").
    Zusatzwerte: empty, whitespace_only, leading_whitespace, trailing_whitespace.
    Lange Werte (> 500 Zeichen) werden symbolisch gespeichert.
    """
    from .symbolic_values import should_be_symbolic, generate_symbolic_string, make_value, CHARSETS

    extras = _normalize_extras(extras)
    if charset not in CHARSETS:
        raise BVAError(f"Unbekanntes charset: {charset!r}. Erlaubt: {list(CHARSETS.keys())}")
    parsed = []
    for r in ranges:
        lo, hi = _parse_length(r.min_val), _parse_length(r.max_val)
        if lo > hi:
            raise BVAError(f"Min ist größer als Max: {r.min_val} > {r.max_val}")
        parsed.append((lo, hi, r.allowed))
    _check_overlaps([(lo, hi) for lo, hi, _ in parsed])

    def render(length: int) -> str:
        return "" if length == 0 else make_value(length, charset)

    # Sortierung nach Laenge; Zusatzwerte gleicher Laenge danach
    out = _Collector("strlen", classify=lambda n: not _in_allowed(parsed, n), render=render,
                     sort_key=lambda n: (n, 0))
    for lo, hi, _ in parsed:
        for offset, label, at_min in _offsets(points):
            length = (lo if at_min else hi) + offset
            if 0 <= length <= _MAX_STRLEN:
                out.add(length, label)

    min_len = min(lo for lo, _, _ in parsed)
    if extras.get("empty"):
        out.add(0, "Leerer String (Laenge 0)")
    # Leerzeichen-Varianten: eigener Wert, auch wenn die Laenge schon belegt ist
    for name, label, build in (
        ("whitespace_only", "Nur Leerzeichen", lambda n: " " * n),
        ("leading_whitespace", "Fuehrendes Leerzeichen", lambda n: " " + make_value(n - 1, charset)),
        ("trailing_whitespace", "Abschliessendes Leerzeichen", lambda n: make_value(n - 1, charset) + " "),
    ):
        if not extras.get(name):
            continue
        length = max(min_len, 1) if name == "whitespace_only" else min_len + 1
        if should_be_symbolic(length):
            continue  # symbolische Werte koennen keine Leerzeichen-Variante abbilden
        value = build(length)
        out.items.setdefault(value, ((length, 1), BVAValue(value=value, is_error=True,
                                                            vtype="strlen", label=label)))
    return out.result()


def generate_bva_strlen(
    min_len: int,
    max_len: int,
    points: int = 2,
    charset: str = "alpha",
    extras: Optional[dict] = None,
) -> list[BVAValue]:
    """REQ-6007: BVA fuer einen Stringlaengen-Bereich."""
    if int(min_len) < 0:
        raise BVAError(f"min_len muss >= 0 sein, nicht {min_len}")
    return generate_multi_range_bva_strlen([TypedRange(str(min_len), str(max_len))], points, charset, extras)


def generate_multi_range_bva_typed(
    bva_type: str,
    ranges: list[TypedRange],
    points: int = 2,
    options: Optional[dict] = None,
) -> list[BVAValue]:
    """REQ-6007: Einstieg fuer die API (type: date, time, datetime, strlen)."""
    options = options or {}
    if not isinstance(options, dict):
        raise BVAError("options muss ein Objekt sein")
    extras = options.get("extras")
    if bva_type == "date":
        return generate_multi_range_bva_date(ranges, points, options.get("format", "iso"), extras)
    if bva_type == "time":
        return generate_multi_range_bva_time(ranges, points, options.get("format", "HH:MM"),
                                             options.get("step", "minute"), extras)
    if bva_type == "datetime":
        return generate_multi_range_bva_datetime(ranges, points, options.get("step", "minute"),
                                                 extras, options.get("timezone"))
    if bva_type == "strlen":
        return generate_multi_range_bva_strlen(ranges, points, options.get("charset", "alpha"), extras)
    raise BVAError(f"Unbekannter BVA-Typ: {bva_type!r}")
