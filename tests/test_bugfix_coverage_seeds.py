"""Bugfixes Constraints/Abdeckung/Seeds: R-05, K-04, K-06, K-07, K-08, K-10, K-11, K-12."""
import itertools
import time

import pytest

from app.database import SessionLocal
from app import models

_counter = itertools.count()


def _project(client, model, prefix="Block5"):
    """model: [(Kategorie, [Werte])] -> (pid, {Kategorie: {"id", "values": {Wert: id}}})"""
    pid = client.post("/api/projects", json={"name": f"{prefix}-{next(_counter)}"}).json()["id"]
    info = {}
    for idx, (name, values) in enumerate(model):
        cid = client.post(f"/api/projects/{pid}/categories", json={"name": name, "order_index": idx}).json()["id"]
        vids = {v: client.post(f"/api/categories/{cid}/values", json={"value": v}).json()["id"] for v in values}
        info[name] = {"id": cid, "values": vids}
    return pid, info


def _implies(client, pid, info, name, if_cat, if_val, then_cat, then_val):
    resp = client.post(f"/api/v1/projects/{pid}/constraints", json={
        "name": name, "kind": "implies",
        "expression": {"op": "eq", "category_id": info[if_cat]["id"], "value_id": info[if_cat]["values"][if_val]},
        "consequence": {"op": "eq", "category_id": info[then_cat]["id"], "value_id": info[then_cat]["values"][then_val]},
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _generate(client, pid, **body):
    resp = client.post(f"/api/projects/{pid}/generate", json={"apply_rules": True, **body})
    assert resp.status_code == 200, resp.text
    return resp.json()


CHAIN = [("A", ["a1", "a2"]), ("B", ["b1", "b2"]), ("C", ["c1", "c2"])]


# ===========================================================================
# K-06: indirekt unmoegliche Paare, einzelne unerreichbare Werte
# ===========================================================================

def test_indirectly_impossible_pairs_not_counted(auth_client):
    pid, info = _project(auth_client, CHAIN)
    _implies(auth_client, pid, info, "A1->B1", "A", "a1", "B", "b1")
    _implies(auth_client, pid, info, "B1->C1", "B", "b1", "C", "c1")
    gid = _generate(auth_client, pid, strategy="all")["generation_id"]
    cov = auth_client.get(f"/api/generations/{gid}/coverage").json()
    assert cov["coverage_2wise"]["percentage"] == 100.0, cov["coverage_2wise"]
    excluded = {tuple(zip(t["categories"], t["values"])) for t in cov["excluded_tuples_2wise"]}
    assert (("A", "a1"), ("C", "c2")) in excluded  # nur ueber die Kette unmoeglich


def test_single_unreachable_value_warns_on_save(auth_client):
    pid, info = _project(auth_client, CHAIN)
    _implies(auth_client, pid, info, "A1->B1", "A", "a1", "B", "b1")
    # A=a1 -> B=b2 widerspricht A1->B1: a1 ist danach unerreichbar
    created = _implies(auth_client, pid, info, "A1->B2", "A", "a1", "B", "b2")
    assert created["warnings"] == ["Wert 'a1' (A) ist durch die Regeln in keinem Testfall erreichbar."]


# ===========================================================================
# K-07: risk_based regelbewusst, keine falsche Warnung
# ===========================================================================

def test_risk_based_respects_constraints(auth_client):
    pid, info = _project(auth_client, CHAIN)
    # Die Rundlauf-Zuordnung paart a1 mit b1; das Constraint verlangt b2
    _implies(auth_client, pid, info, "A1->B2", "A", "a1", "B", "b2")
    result = _generate(auth_client, pid, strategy="risk_based")
    assert not any("erreichbar" in w for w in result["warnings"]), result["warnings"]
    tcs = auth_client.get(f"/api/generations/{result['generation_id']}/testcases").json()
    rows = tcs["testcases"] if isinstance(tcs, dict) else tcs
    seen = {(cat, val) for row in rows for cat, val in (row.get("assignments") or row.get("values") or {}).items()}
    for cat, vals in CHAIN:
        for v in vals:
            assert (cat, v) in seen, (cat, v, rows)


# ===========================================================================
# R-05: nicht angewendete Constraints werden gemeldet
# ===========================================================================

def test_invalid_constraint_reported_on_generate(auth_client):
    pid, info = _project(auth_client, CHAIN)
    _implies(auth_client, pid, info, "Regel X", "A", "a1", "B", "b1")
    auth_client.delete(f"/api/values/{info['B']['values']['b1']}", params={"force": True})
    warnings = _generate(auth_client, pid, strategy="all")["warnings"]
    assert any("Regel X" in w and "nicht angewendet" in w for w in warnings), warnings


# ===========================================================================
# K-04: 3-wise-Groessenpruefung
# ===========================================================================

def test_three_wise_size_uses_real_triple_count():
    from combinatorics.coverage import calculate_coverage
    cats = {f"K{i}": [f"v{j}" for j in range(5)] for i in range(9)}  # 84 Tripel x 125 = 10.500
    result = calculate_coverage([], cats, 3)
    assert result.possible == 10_500


def test_missing_three_wise_too_large_is_422(auth_client, monkeypatch):
    from combinatorics import coverage
    pid, _ = _project(auth_client, CHAIN)
    gid = _generate(auth_client, pid, strategy="each")["generation_id"]
    monkeypatch.setattr(coverage, "MAX_COVERAGE_TUPLES", 1)
    resp = auth_client.get(f"/api/generations/{gid}/coverage/missing", params={"t": 3})
    assert resp.status_code == 422, resp.text


# ===========================================================================
# K-08: Abdeckung dauerhaft gespeichert und bei Modellaenderung neu berechnet
# ===========================================================================

def test_coverage_persisted_and_invalidated(auth_client):
    pid, info = _project(auth_client, CHAIN)
    gid = _generate(auth_client, pid, strategy="all")["generation_id"]
    first = auth_client.get(f"/api/generations/{gid}/coverage").json()
    assert first["coverage_2wise"]["excluded_by_rules"] == 0

    # ueberlebt einen "Neustart": gespeichert in der Datenbank
    db = SessionLocal()
    try:
        assert db.get(models.Generation, gid).coverage_meta
    finally:
        db.close()
    listing = auth_client.get(f"/api/projects/{pid}/generations").json()
    assert next(g for g in listing if g["id"] == gid)["coverage_2wise_pct"] == 100.0

    # neues Constraint -> Ergebnis nicht mehr aus dem Cache
    _implies(auth_client, pid, info, "A1->B1", "A", "a1", "B", "b1")
    second = auth_client.get(f"/api/generations/{gid}/coverage").json()
    assert second["cached"] is False
    assert second["coverage_2wise"]["excluded_by_rules"] == 1


def test_coverage_performance_30x10x1000(auth_client, db_session):
    """REQ-6008: 2-wise fuer 30 x 10 x 1.000 Testfaelle in < 3 s (Toleranz fuer CI: 6 s)."""
    import random
    pid = auth_client.post("/api/projects", json={"name": f"Perf-{next(_counter)}"}).json()["id"]
    cats = []
    for i in range(30):
        cat = models.Category(project_id=pid, name=f"K{i:02d}", order_index=i)
        db_session.add(cat)
        db_session.flush()
        for j in range(10):
            db_session.add(models.Value(category_id=cat.id, value=f"w{j}"))
        cats.append(cat)
    gen = models.Generation(project_id=pid, strategy="pairwise")
    db_session.add(gen)
    db_session.flush()
    rng = random.Random(6008)
    for n in range(1000):
        tc = models.TestCase(generation_id=gen.id, name=f"TC_{n + 1}")
        db_session.add(tc)
        db_session.flush()
        for cat in cats:
            db_session.add(models.TestCaseValue(testcase_id=tc.id, category_id=cat.id,
                                                category_name=cat.name, value=f"w{rng.randrange(10)}"))
    db_session.commit()
    start = time.perf_counter()
    resp = auth_client.get(f"/api/generations/{gen.id}/coverage")
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed < 6.0, f"{elapsed:.1f} s"


# ===========================================================================
# K-10 / K-11 / K-12: Seeds und Lueckenschluss
# ===========================================================================

GRID = [("A", ["a1", "a2", "a3"]), ("B", ["b1", "b2", "b3"]), ("C", ["c1", "c2", "c3"])]
SEEDS = [{"A": "a1", "B": "b1", "C": "c1"}, {"A": "a2", "B": "b2", "C": "c2"},
         {"A": "a3", "B": "b3", "C": "c3"}, {"A": "a1", "B": "b2", "C": "c3"}]


def _pairs(rows):
    return {frozenset(p) for r in rows for p in itertools.combinations(sorted(r.items()), 2)}


def test_seed_generation_only_supplements_missing_pairs(auth_client):
    pid, _ = _project(auth_client, GRID)
    result = _generate(auth_client, pid, strategy="pairwise", seeds=SEEDS)
    assert result["seeds_count"] == 4
    assert result["coverage_after"] == 100.0
    # 27 Paare, Seeds decken 12 ab; jede Ergaenzung deckt hoechstens 3 neue -> mind. 5, bisher deutlich mehr
    assert result["supplemented_count"] <= 7, result
    assert result["count"] == 4 + result["supplemented_count"]


def test_gap_fill_three_wise_and_impossible_tuples(auth_client):
    pid, info = _project(auth_client, GRID)
    _implies(auth_client, pid, info, "A1->B1", "A", "a1", "B", "b1")
    gid = _generate(auth_client, pid, strategy="each")["generation_id"]
    resp = auth_client.post(f"/api/generations/{gid}/gap-fill", params={"strategy": "t_wise", "t_strength": 3})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["coverage_after"] == 100.0
    # K-11: unmoeglich sind nur Tupel mit A=a1 und B!=b1
    for tup in data["impossible_tuples"]:
        as_dict = dict(map(tuple, tup))
        assert as_dict.get("A") == "a1" and as_dict.get("B") in ("b2", "b3"), tup
    assert data["impossible_tuples"]


def test_gap_fill_unknown_strategy_rejected(auth_client):
    pid, _ = _project(auth_client, GRID)
    gid = _generate(auth_client, pid, strategy="each")["generation_id"]
    resp = auth_client.post(f"/api/generations/{gid}/gap-fill", params={"strategy": "foo"})
    assert resp.status_code == 422


def test_limit_never_cuts_seeds(auth_client):
    pid, _ = _project(auth_client, GRID)
    result = _generate(auth_client, pid, strategy="pairwise", seeds=SEEDS, limit=2)
    assert result["count"] == 4
    assert any("Seeds" in w for w in result["warnings"]), result["warnings"]


def test_seed_with_unknown_value_not_generated(auth_client):
    pid, _ = _project(auth_client, GRID)
    seeds = SEEDS[:1] + [{"A": "unbekannt", "B": "b1", "C": "c1"}]
    result = _generate(auth_client, pid, strategy="each", seeds=seeds)
    assert result["seeds_count"] == 1
    assert any("unbekannte Werte" in w for w in result["warnings"]), result["warnings"]
