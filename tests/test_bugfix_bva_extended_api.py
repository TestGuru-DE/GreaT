"""BUG C-02/C-06: Vertrag der erweiterten Grenzwertanalyse (REQ-6007).

Der Dialog sendet Format, Schrittweite, Zeichenvorrat und Zusatzwerte mit
snake_case-Schluesseln. Gespeicherte Werte tragen den passenden Typ.
"""
import pytest


@pytest.fixture
def category(auth_client):
    p = auth_client.post("/api/projects", json={"name": "BVA erweitert"}).json()
    c = auth_client.post(f"/api/projects/{p['id']}/categories", json={"name": "Termin"}).json()
    return c["id"]


def _run(auth_client, cid, type_, lo, hi, **options):
    r = auth_client.post(f"/api/categories/{cid}/bva/extended", json={
        "type": type_, "points": 2,
        "ranges": [{"min_val": lo, "max_val": hi, "allowed": True}],
        "options": options,
    })
    assert r.status_code == 200, r.text
    return r.json()["values"]


def _stored(auth_client, cid):
    return {v["value"]: v for v in auth_client.get(f"/api/categories/{cid}/values").json()}


def test_date_format_de_and_snake_case_extras(auth_client, category):
    vals = _run(auth_client, category, "date", "2024-02-01", "2024-03-31",
                format="de", extras={"leap_year": True})
    names = [v["value"] for v in vals]
    assert "01.02.2024" in names and "31.03.2024" in names
    assert "29.02.2024" in names  # Zusatzwert greift nur mit snake_case-Schluessel
    assert all(v["vtype"] == "date" for v in vals)


def test_date_values_stored_with_type_and_error_flag(auth_client, category):
    _run(auth_client, category, "date", "2024-02-01", "2024-03-31")
    stored = _stored(auth_client, category)
    assert stored["2024-02-01"]["vtype"] == "date" and stored["2024-02-01"]["allowed"] is True
    assert stored["2024-01-31"]["allowed"] is False


def test_time_format_and_step(auth_client, category):
    vals = _run(auth_client, category, "time", "08:00:00", "17:00:00", format="HH:MM:SS", step="second")
    names = [v["value"] for v in vals]
    assert "07:59:59" in names and "17:00:01" in names
    assert _stored(auth_client, category)["08:00:00"]["vtype"] == "time"


def test_strlen_charset_and_string_type(auth_client, category):
    vals = _run(auth_client, category, "strlen", "1", "3", charset="alnum")
    assert vals
    assert all(v["vtype"] == "string" for v in _stored(auth_client, category).values())


def test_datetime_stored_as_string(auth_client, category):
    _run(auth_client, category, "datetime", "2024-01-01T08:00", "2024-01-02T08:00")
    assert {v["vtype"] for v in _stored(auth_client, category).values()} == {"string"}
