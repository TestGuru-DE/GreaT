"""BUG B-03 / K-01 / K-03 / N-03: Zeitbudget und Groessenpruefung.

- Jede Strategie bricht bei ueberschrittenem Zeitbudget ab (statt den Server
  minuten- bis stundenlang zu blockieren).
- T-Wise/Pairwise pruefen die Anzahl der t-Tupel vor dem Start.
- Zu grosse Modelle und Zeitueberschreitungen liefern 422 mit stabilem Code.
- Das Speichern eines Constraints blockiert auch bei grossen Modellen nicht.
"""
import time
import uuid

import pytest

from combinatorics import all_combinations, each_choice, ipo, linear_expansion, mcdc, t_wise
from combinatorics.budget import BudgetExceeded, checkpoint, count_t_tuples, time_budget


def _model(n_cats, n_vals):
    return {f"K{i:02d}": [f"v{i}_{j}" for j in range(n_vals)] for i in range(n_cats)}


# ---------------------------------------------------------------------------
# Bibliothek
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cats,t,expected", [
    ([3, 3, 3], 2, 27),              # 3 Paare x 9
    ([2, 3, 4], 2, 2*3 + 2*4 + 3*4),
    ([2, 3, 4], 3, 24),
    ([10] * 20, 2, 190 * 100),
    ([10] * 20, 4, 4845 * 10**4),
    ([5, 5], 3, 25),                 # t >= n -> kartesisches Produkt
])
def test_count_t_tuples(cats, t, expected):
    model = {f"K{i}": [str(j) for j in range(n)] for i, n in enumerate(cats)}
    assert count_t_tuples(model, t) == expected


def test_checkpoint_without_budget_is_noop():
    checkpoint()


def test_checkpoint_raises_after_deadline():
    with time_budget(time.time() - 1):
        with pytest.raises(BudgetExceeded):
            checkpoint()
    checkpoint()  # Budget nach dem Block wieder aufgehoben


@pytest.mark.parametrize("gen", [
    lambda m: t_wise.generate(m, t=3),
    lambda m: t_wise.generate(m, t=2),
    lambda m: ipo.generate(m),
    lambda m: each_choice.generate(m),
    lambda m: linear_expansion.generate(m),
    lambda m: mcdc.generate(m),
    lambda m: all_combinations.generate(_model(4, 4)),
], ids=["t_wise3", "t_wise2", "pairwise", "each", "linear", "mcdc", "all"])
def test_every_generator_respects_budget(gen):
    with time_budget(time.time() - 1):
        with pytest.raises(BudgetExceeded):
            gen(_model(8, 6))


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _api_project(auth_client, n_cats, n_vals):
    pid = auth_client.post("/api/projects", json={"name": f"Budget-{uuid.uuid4().hex[:6]}"}).json()["id"]
    for i in range(n_cats):
        cid = auth_client.post(f"/api/projects/{pid}/categories", json={"name": f"K{i:02d}"}).json()["id"]
        for j in range(n_vals):
            assert auth_client.post(f"/api/categories/{cid}/values", json={"value": f"v{i}_{j}"}).status_code == 200
    return pid


def test_t_wise_too_many_tuples_rejected_fast(auth_client):
    pid = _api_project(auth_client, 20, 10)
    t0 = time.time()
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "t_wise", "t_strength": 4})
    assert time.time() - t0 < 2
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "too_many_combinations"


def test_all_too_many_combinations_is_422_with_code(auth_client):
    pid = _api_project(auth_client, 8, 6)
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "too_many_combinations"


def test_max_tuples_configurable(auth_client, monkeypatch):
    pid = _api_project(auth_client, 6, 4)
    monkeypatch.setenv("GREAT_MAX_TUPLES", "10")
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "pairwise"})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "too_many_combinations"


def test_timeout_returns_422_generation_timeout_quickly(auth_client, monkeypatch):
    pid = _api_project(auth_client, 8, 6)
    monkeypatch.setenv("GREAT_GENERATION_TIMEOUT_S", "0.3")
    t0 = time.time()
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "t_wise", "t_strength": 3})
    elapsed = time.time() - t0
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "generation_timeout"
    assert elapsed < 3, f"Abbruch dauerte {elapsed:.1f}s"


def test_normal_generation_unaffected(auth_client):
    pid = _api_project(auth_client, 4, 3)
    for strategy in ("all", "each", "pairwise", "linear", "t_wise", "risk_based", "mcdc"):
        r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": strategy})
        assert r.status_code == 200, f"{strategy}: {r.text}"
        assert r.json()["count"] > 0


def test_saving_constraint_on_large_model_does_not_hang(auth_client):
    """BUG K-01: Widerspruchspruefung zaehlte den ganzen Raum auf (10^12)."""
    pid = _api_project(auth_client, 12, 10)
    cats = auth_client.get(f"/api/projects/{pid}/categories").json()
    cid = cats[0]["id"]
    vid = auth_client.get(f"/api/categories/{cid}/values").json()[0]["id"]
    t0 = time.time()
    r = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
        "name": "Gross",
        "kind": "forbid",
        "expression": {"op": "eq", "category_id": cid, "value_id": vid},
    })
    elapsed = time.time() - t0
    assert r.status_code == 201, r.text
    assert elapsed < 5, f"Speichern dauerte {elapsed:.1f}s"
