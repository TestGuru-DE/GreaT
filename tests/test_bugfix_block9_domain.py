"""Restbefunde Themenblock 9c: Constraint-Tiefe, Seed-Import, Grenzwertanalyse, symbolische Werte."""
import csv
import io
import itertools
import json

import pytest

_counter = itertools.count()


def _project(client, categories):
    pid = client.post("/api/projects", json={"name": f"B9c-{next(_counter)}"}).json()["id"]
    ids = {}
    for order, (name, values) in enumerate(categories.items()):
        cid = client.post(f"/api/projects/{pid}/categories", json={"name": name, "order_index": order}).json()["id"]
        ids[name] = (cid, [client.post(f"/api/categories/{cid}/values", json={"value": v}).json()["id"] for v in values])
    return pid, ids


# ---------------------------------------------------------------------------
# Constraint-Tiefe: /validate meldet dieselbe Tiefe, die die Pruefung verwendet
# ---------------------------------------------------------------------------

def _nested(levels, leaf):
    expr = leaf
    for _ in range(levels):
        expr = {"op": "not", "arg": expr}
    return expr


@pytest.mark.parametrize("levels, valid", [(5, True), (6, False)])
def test_validate_depth_matches_create(auth_client, levels, valid):
    pid, ids = _project(auth_client, {"A": ["a"]})
    cid, (vid,) = ids["A"]
    expr = _nested(levels, {"op": "eq", "category_id": cid, "value_id": vid})
    check = auth_client.post(f"/api/v1/projects/{pid}/constraints/validate",
                             json={"kind": "forbid", "expression": expr}).json()
    create = auth_client.post(f"/api/v1/projects/{pid}/constraints",
                              json={"name": f"c{levels}", "kind": "forbid", "expression": expr})
    assert check["depth"] == levels
    assert check["is_valid"] is valid
    assert (create.status_code == 201) is valid


# ---------------------------------------------------------------------------
# Seed-CSV-Import: doppelter Satzname wird abgelehnt
# ---------------------------------------------------------------------------

def test_csv_import_rejects_duplicate_seed_set_name(auth_client):
    pid, _ = _project(auth_client, {"A": ["a"]})
    upload = lambda: auth_client.post(  # noqa: E731
        f"/api/projects/{pid}/seed-sets/import-csv",
        data={"name": "Pflicht"}, files={"csv_content": ("s.csv", b"A\na\n", "text/csv")})
    assert upload().status_code in (200, 201)
    assert upload().status_code == 409


# ---------------------------------------------------------------------------
# Aufgefuellte Seed-Felder werden gekennzeichnet
# ---------------------------------------------------------------------------

def test_filled_seed_fields_are_marked(auth_client):
    pid, _ = _project(auth_client, {"A": ["a1", "a2"], "B": ["b1", "b2"]})
    ssid = auth_client.post(f"/api/projects/{pid}/seed-sets",
                            json={"name": "S", "seeds": [{"A": "a2", "B": None}]}).json()["id"]
    gid = auth_client.post(f"/api/projects/{pid}/generate",
                           json={"strategy": "pairwise", "seed_set_id": ssid}).json()["generation_id"]
    tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()["testcases"]
    seeds = [tc for tc in tcs if tc["origin"] == "seed"]
    assert len(seeds) == 1
    assert seeds[0]["assignments"]["A"] == "a2"
    assert seeds[0]["filled_categories"] == ["B"]
    assert all(tc["filled_categories"] == [] for tc in tcs if tc["origin"] != "seed")


# ---------------------------------------------------------------------------
# Grenzwertanalyse: Typ und Optionen werden nicht still ignoriert (C-13, C-14)
# ---------------------------------------------------------------------------

def test_bva_ranges_rejects_non_number_type(auth_client):
    _, ids = _project(auth_client, {"Datum": []})
    cid = ids["Datum"][0]
    resp = auth_client.post(f"/api/categories/{cid}/bva/ranges", json={
        "type": "date", "ranges": [{"min_val": "2026-01-01", "max_val": "2026-12-31", "allowed": True}]})
    assert resp.status_code == 422
    assert "/bva/extended" in resp.text


def test_bva_extended_rejects_mismatching_range_type(auth_client):
    _, ids = _project(auth_client, {"Datum": []})
    cid = ids["Datum"][0]
    resp = auth_client.post(f"/api/categories/{cid}/bva/extended", json={
        "type": "date", "ranges": [{"min_val": "1", "max_val": "5", "type": "number"}]})
    assert resp.status_code == 422


def test_bva_extended_rejects_unknown_option(auth_client):
    _, ids = _project(auth_client, {"Datum": []})
    cid = ids["Datum"][0]
    resp = auth_client.post(f"/api/categories/{cid}/bva/extended", json={
        "type": "date", "ranges": [{"min_val": "2026-01-01", "max_val": "2026-12-31"}],
        "options": {"charset": "alpha"}})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "bva_unknown_option"


# ---------------------------------------------------------------------------
# Symbolische Langwerte werden im Testfall-Export aufgeloest (REQ-6007)
# ---------------------------------------------------------------------------

SYMBOLIC = "<STR len=1001 charset=alnum>"


@pytest.fixture
def symbolic_generation(auth_client):
    pid, _ = _project(auth_client, {"Text": [SYMBOLIC, "kurz"]})
    return auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"}).json()["generation_id"]


def test_csv_export_resolves_symbolic_value(auth_client, symbolic_generation):
    text = auth_client.get(f"/api/generations/{symbolic_generation}/export/csv?lang=de").content.decode("utf-8-sig")
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=";") if r and not r[0].startswith("sep=")]
    values = [r[0] for r in rows[1:]]
    assert SYMBOLIC not in text
    long_values = [v for v in values if len(v) == 1001]
    assert len(long_values) == 1 and long_values[0].isalnum()


def test_symbolic_resolution_is_deterministic(auth_client, symbolic_generation):
    url = f"/api/generations/{symbolic_generation}/export/json-data-driven"
    assert auth_client.get(url).content == auth_client.get(url).content
    data = json.loads(auth_client.get(url).content)
    assert any(len(row["Text"]) == 1001 for row in data)


def test_testcase_view_keeps_symbolic_placeholder(auth_client, symbolic_generation):
    tcs = auth_client.get(f"/api/generations/{symbolic_generation}/testcases").json()["testcases"]
    assert SYMBOLIC in {tc["assignments"]["Text"] for tc in tcs}
