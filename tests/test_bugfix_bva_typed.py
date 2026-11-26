"""Bugfixes Grenzwertanalyse: C-04, C-05, C-07 bis C-12."""
import itertools
import re
from datetime import date

import pytest

from combinatorics.boundary_value import (
    BVAError, TypedRange,
    generate_multi_range_bva_date, generate_multi_range_bva_time,
    generate_multi_range_bva_datetime, generate_multi_range_bva_strlen,
    generate_bva_strlen, generate_bva_time,
)
from combinatorics.symbolic_values import make_value

_counter = itertools.count()


@pytest.fixture
def category_id(auth_client):
    pid = auth_client.post("/api/projects", json={"name": f"BVA-{next(_counter)}"}).json()["id"]
    return auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Feld", "order_index": 0}).json()["id"]


def _values(result):
    return {v.value: v.is_error for v in result}


# ===========================================================================
# C-04: Randeingaben liefern 400 mit Meldung statt 500
# ===========================================================================

@pytest.mark.parametrize("path,body", [
    ("bva/extended", {"type": "date", "ranges": [{"min_val": "2023-11-15", "max_val": "2024-02-10"}],
                      "options": {"extras": {"month_ends": True}}}),
    ("bva/extended", {"type": "date", "ranges": [{"min_val": "0001-01-01", "max_val": "0001-01-05"}], "points": 4}),
    ("bva/extended", {"type": "date", "ranges": [{"min_val": "9999-12-20", "max_val": "9999-12-31"}],
                      "points": 4, "options": {"extras": {"year_transition": True, "month_ends": True}}}),
    ("bva/extended", {"type": "date", "ranges": [{"min_val": "2024-01-01", "max_val": "2024-03-31"}],
                      "options": {"extras": ["leap_year", "month_ends"]}}),
    ("bva/extended", {"type": "datetime", "ranges": [{"min_val": "2024-01-01T00:00:00", "max_val": "2024-01-02T00:00:00+02:00"}]}),
    ("bva/extended", {"type": "number", "ranges": [{"min_val": "NaN", "max_val": "10"}]}),
    ("bva/extended", {"type": "number", "ranges": [{"min_val": "1", "max_val": "1e999999999"}]}),
    ("bva/ranges", {"ranges": [{"min_val": "2024-01-01", "max_val": "2024-12-31"}]}),
    ("bva", {"min_val": "1", "max_val": "1e999999999"}),
    ("bva/extended", {"type": "date", "ranges": [{"min_val": "2024-01-01", "max_val": "2024-01-31"}],
                      "options": {"extras": "month_ends"}}),
    ("bva/extended", {"type": "time", "ranges": [{"min_val": "08:00", "max_val": "17:00"}],
                      "options": {"format": "HHMM"}}),
])
def test_edge_inputs_never_500(auth_client, category_id, path, body):
    resp = auth_client.post(f"/api/categories/{category_id}/{path}", json=body)
    assert resp.status_code in (200, 400, 422), resp.text
    if resp.status_code != 200:
        assert resp.json().get("detail"), resp.text


def test_date_edges_at_calendar_limits():
    lo_vals = _values(generate_multi_range_bva_date([TypedRange("0001-01-01", "0001-01-05")], points=4))
    assert "0001-01-01" in lo_vals and lo_vals["0001-01-01"] is False
    hi_vals = _values(generate_multi_range_bva_date([TypedRange("9999-12-20", "9999-12-31")], points=4,
                                                    extras={"year_transition": True}))
    assert hi_vals["9999-12-31"] is False


def test_mixed_timezones_rejected_and_timezone_option(auth_client, category_id):
    with pytest.raises(BVAError, match="Zeitzone"):
        generate_multi_range_bva_datetime([TypedRange("2024-01-01T00:00:00", "2024-01-02T00:00:00+02:00")])
    # C-10: Zeitzone als Formatoption
    vals = generate_multi_range_bva_datetime([TypedRange("2024-01-01T08:00:00", "2024-01-01T17:00:00")],
                                             tz="+02:00")
    assert all(v.value.endswith("+02:00") for v in vals), [v.value for v in vals]
    resp = auth_client.post(f"/api/categories/{category_id}/bva/extended", json={
        "type": "datetime", "ranges": [{"min_val": "2024-01-01T08:00", "max_val": "2024-01-01T17:00"}],
        "options": {"timezone": "Z"}})
    assert resp.status_code == 200, resp.text
    assert all(v["value"].endswith("+00:00") for v in resp.json()["values"])


# ===========================================================================
# C-05: mehrere Bereiche gemeinsam
# ===========================================================================

def test_adjacent_ranges_no_conflicting_duplicates():
    vals = generate_multi_range_bva_date(
        [TypedRange("2024-01-01", "2024-01-31", True), TypedRange("2024-02-01", "2024-02-29", False)])
    texts = [v.value for v in vals]
    assert len(texts) == len(set(texts)), texts
    by_value = _values(vals)
    assert by_value["2024-01-31"] is False   # max des gueltigen Bereichs
    assert by_value["2024-02-01"] is True    # liegt im ungueltigen Bereich
    assert by_value["2023-12-31"] is True    # ausserhalb


def test_disallowed_range_marks_errors_for_all_types():
    strlen = _values(generate_multi_range_bva_strlen(
        [TypedRange("1", "10", True), TypedRange("11", "20", False)]))
    assert strlen[make_value(10, "alpha")] is False
    assert strlen[make_value(11, "alpha")] is True
    times = _values(generate_multi_range_bva_time(
        [TypedRange("08:00", "12:00", True), TypedRange("12:01", "13:00", False)]))
    assert times["12:00"] is False and times["12:01"] is True


@pytest.mark.parametrize("ranges", [
    [TypedRange("2024-02-10", "2024-01-01")],                                        # Min > Max
    [TypedRange("2024-01-01", "2024-01-31"), TypedRange("2024-01-15", "2024-02-15")],  # Ueberschneidung
])
def test_invalid_date_ranges_rejected(ranges):
    with pytest.raises(BVAError):
        generate_multi_range_bva_date(ranges)


def test_number_min_greater_max_rejected_via_api(auth_client, category_id):
    resp = auth_client.post(f"/api/categories/{category_id}/bva/ranges",
                            json={"ranges": [{"min_val": "10", "max_val": "1"}]})
    assert resp.status_code == 400
    assert "Min" in resp.json()["detail"]


def test_api_uses_allowed_flag_for_dates(auth_client, category_id):
    resp = auth_client.post(f"/api/categories/{category_id}/bva/extended", json={
        "type": "date",
        "ranges": [{"min_val": "2024-01-01", "max_val": "2024-01-31", "allowed": True},
                   {"min_val": "2024-02-01", "max_val": "2024-02-29", "allowed": False}]})
    assert resp.status_code == 200, resp.text
    flags = {v["value"]: v["is_error"] for v in resp.json()["values"]}
    assert flags["2024-02-01"] is True and flags["2024-01-31"] is False


# ===========================================================================
# C-07: Zusatzwerte nur im Bereich, Jahreszahl unveraendert
# ===========================================================================

def test_extras_stay_inside_range():
    vals = generate_multi_range_bva_date([TypedRange("2023-06-01", "2023-07-31")],
                                         extras={"non_leap_year": True, "invalid_date": True})
    texts = [v.value for v in vals]
    assert "2023-02-29" not in texts       # Februar liegt nicht im Bereich
    assert "2023-04-31" not in texts       # April liegt nicht im Bereich
    assert "2023-06-31" in texts           # Juni hat 30 Tage und liegt im Bereich


def test_non_leap_year_keeps_year():
    vals = generate_multi_range_bva_date([TypedRange("2289-02-01", "2289-03-31")], extras={"non_leap_year": True})
    assert "2289-02-29" in [v.value for v in vals]
    assert not any(v.value.startswith("2299") for v in vals)


# ===========================================================================
# C-08: Monatsenden im Startmonat und ueber den Jahreswechsel
# ===========================================================================

def test_month_ends_include_start_month_and_december():
    vals = generate_multi_range_bva_date([TypedRange("2023-11-15", "2024-02-10")], extras={"month_ends": True})
    texts = [v.value for v in vals]
    for d in ("2023-11-30", "2023-12-31", "2024-01-31"):
        assert d in texts, texts


def test_german_format_sorted_chronologically():
    vals = generate_multi_range_bva_date([TypedRange("2024-01-30", "2024-02-02")], fmt="de", points=3)
    parsed = [date(int(v.value[6:]), int(v.value[3:5]), int(v.value[:2])) for v in vals]
    assert parsed == sorted(parsed)


# ===========================================================================
# C-09: nur gueltige Uhrzeitformate
# ===========================================================================

@pytest.mark.parametrize("fmt,pattern", [("HH:MM", r"^([01]\d|2[0-3]):[0-5]\d$"),
                                         ("HH:MM:SS", r"^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$")])
def test_time_values_are_valid_times(fmt, pattern):
    for lo, hi in (("00:00", "08:00"), ("16:00", "23:59"), ("22:00", "02:00"), ("00:00", "23:59")):
        vals = generate_bva_time(lo, hi, points=4, fmt=fmt, extras={"midnight": True, "end_of_day": True})
        bad = [v.value for v in vals if not re.match(pattern, v.value)]
        assert not bad, (lo, hi, bad)


def test_time_wraps_and_classifies_across_midnight():
    vals = _values(generate_bva_time("00:00", "08:00"))
    assert vals["23:59"] is True and vals["00:00"] is False
    crossing = _values(generate_bva_time("22:00", "02:00", points=3))
    assert crossing["21:59"] is True and crossing["22:01"] is False
    assert crossing["01:59"] is False and crossing["02:01"] is True


def test_invalid_2400_matches_format():
    vals = generate_bva_time("08:00", "17:00", fmt="HH:MM:SS", extras={"invalid_2400": True})
    assert "24:00:00" in [v.value for v in vals]


def test_second_step_uses_seconds_format():
    vals = [v.value for v in generate_bva_time("10:00", "11:00", points=3, step="second")]
    assert "09:59:59" in vals and "10:00:01" in vals and len(vals) == len(set(vals))


# ===========================================================================
# C-11 / C-12: Stringlaenge
# ===========================================================================

def test_min_zero_has_no_negative_length():
    vals = generate_bva_strlen(0, 5, points=4)
    assert not any("len=-" in v.value for v in vals), [v.value for v in vals]
    assert "" in [v.value for v in vals]


@pytest.mark.parametrize("charset,expected_chars", [
    ("alpha_de", set("äöüßÄÖÜ")),
    ("unicode", {"\U0001F600"}),
])
def test_charset_shows_its_characters(charset, expected_chars):
    value = make_value(4, charset)
    assert len(value) == 4
    assert expected_chars & set(value), value


def test_unicode_contains_non_bmp_and_counts_codepoints():
    value = make_value(5, "unicode")
    assert any(ord(c) > 0xFFFF for c in value)
    assert len(value) == 5


def test_whitespace_extras_not_lost_on_length_collision():
    vals = generate_bva_strlen(2, 10, points=3, extras={"leading_whitespace": True,
                                                        "trailing_whitespace": True})
    labels = [v.label for v in vals]
    assert "Fuehrendes Leerzeichen" in labels and "Abschliessendes Leerzeichen" in labels
