"""Bugfixes Sicherheit/API: A-03, K-05, K-02, A-07.

A-03: Scopes eines API-Tokens gelten fuer alle /api-Endpunkte, nicht nur fuer generate.
K-05: Constraints duerfen nur Kategorien und Werte des eigenen Projekts referenzieren.
K-02: Werte und Kategorien, die ein Constraint referenziert, lassen sich nicht loeschen.
A-07: Das Token-Rate-Limit laesst sich nicht ueber den Token-Praefix missbrauchen.
"""
import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, ApiToken

_counter = itertools.count()


def _unique(name: str) -> str:
    return f"{name}-{next(_counter)}"


@pytest.fixture(autouse=True)
def _clean_tokens():
    def _purge():
        db = SessionLocal()
        try:
            db.query(ApiToken).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
    _purge()
    yield
    _purge()


def _token_for(username: str, scopes, role: str = "editor") -> str:
    from app.api_token_service import create_api_token

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username=username, role=role)
            user.set_password("testpass123")
            db.add(user)
        user.role = role
        user.is_active = True
        user.default_password_active = False
        user.token_version = 0
        db.commit()
        db.refresh(user)
        raw, _ = create_api_token(db, user, _unique("t"), list(scopes), days=30)
        return raw
    finally:
        db.close()


def _bearer(raw: str) -> dict:
    return {"Authorization": f"Bearer {raw}"}


def _project_with_values(client: TestClient) -> dict:
    """Projekt mit zwei Kategorien je zwei Werten."""
    resp = client.post("/api/projects", json={"name": _unique("Sicherheit")})
    assert resp.status_code in (200, 201), resp.text
    pid = resp.json()["id"]
    info = {"pid": pid, "cats": []}
    for cname, vals in (("Zahlart", ("Rechnung", "Karte")), ("Versand", ("Post", "Abholung"))):
        cat = client.post(f"/api/projects/{pid}/categories", json={"name": cname, "order_index": 0}).json()
        vids = [client.post(f"/api/categories/{cat['id']}/values", json={"value": v}).json()["id"] for v in vals]
        info["cats"].append({"id": cat["id"], "values": vids})
    return info


def _assert_insufficient_scope(resp):
    assert resp.status_code == 403, resp.text
    assert resp.headers.get("x-error-code") == "insufficient_scope", resp.headers


# ===========================================================================
# A-03: Scopes werden auf allen Endpunkten geprueft
# ===========================================================================

class TestA03ScopesEverywhere:

    def test_read_scope_cannot_create_project(self):
        raw = _token_for("scope_read", ["projects:read"])
        client = TestClient(app)
        assert client.get("/api/v1/projects", headers=_bearer(raw)).status_code == 200
        _assert_insufficient_scope(
            client.post("/api/v1/projects", json={"name": _unique("X")}, headers=_bearer(raw)))

    def test_read_scope_cannot_change_or_delete(self, auth_client):
        info = _project_with_values(auth_client)
        raw = _token_for("scope_read2", ["projects:read"])
        client = TestClient(app)
        pid = info["pid"]
        _assert_insufficient_scope(
            client.put(f"/api/v1/projects/{pid}", json={"name": _unique("Neu")}, headers=_bearer(raw)))
        _assert_insufficient_scope(
            client.post(f"/api/v1/projects/{pid}/categories", json={"name": "C", "order_index": 0},
                        headers=_bearer(raw)))
        _assert_insufficient_scope(
            client.delete(f"/api/v1/values/{info['cats'][0]['values'][0]}", headers=_bearer(raw)))
        _assert_insufficient_scope(
            client.delete(f"/api/v1/projects/{pid}", headers=_bearer(raw)))

    def test_export_scope_alone_cannot_create_or_list(self):
        raw = _token_for("scope_export", ["export"])
        client = TestClient(app)
        _assert_insufficient_scope(
            client.post("/api/v1/projects", json={"name": _unique("X")}, headers=_bearer(raw)))
        _assert_insufficient_scope(client.get("/api/v1/projects", headers=_bearer(raw)))

    def test_write_scope_can_create_project(self):
        raw = _token_for("scope_write", ["projects:write"])
        resp = TestClient(app).post("/api/v1/projects", json={"name": _unique("W")}, headers=_bearer(raw))
        assert resp.status_code in (200, 201), resp.text

    def test_export_needs_export_scope(self, auth_client):
        info = _project_with_values(auth_client)
        gen = auth_client.post(f"/api/projects/{info['pid']}/generate", json={"strategy": "all"})
        assert gen.status_code == 200, gen.text
        gid = gen.json()["generation_id"]
        client = TestClient(app)
        read_only = _token_for("scope_exp_r", ["projects:read"])
        _assert_insufficient_scope(
            client.get(f"/api/v1/generations/{gid}/export/csv", headers=_bearer(read_only)))
        exporter = _token_for("scope_exp_e", ["projects:read", "export"])
        assert client.get(f"/api/v1/generations/{gid}/export/csv",
                          headers=_bearer(exporter)).status_code == 200

    def test_model_scopes(self, auth_client):
        info = _project_with_values(auth_client)
        pid = info["pid"]
        client = TestClient(app)
        models_read = _token_for("scope_mr", ["models:read"])
        assert client.get(f"/api/v1/projects/{pid}/model", headers=_bearer(models_read)).status_code == 200
        _assert_insufficient_scope(
            client.put(f"/api/v1/projects/{pid}/model", content="schemaVersion: 1\n",
                       headers={**_bearer(models_read), "Content-Type": "application/x-yaml"}))
        projects_read = _token_for("scope_pr", ["projects:read"])
        _assert_insufficient_scope(
            client.get(f"/api/v1/projects/{pid}/model", headers=_bearer(projects_read)))

    def test_constraint_write_needs_projects_write(self, auth_client):
        info = _project_with_values(auth_client)
        cat = info["cats"][0]
        raw = _token_for("scope_cons", ["projects:read"])
        body = {"name": "c", "kind": "forbid",
                "expression": {"op": "eq", "category_id": cat["id"], "value_id": cat["values"][0]}}
        _assert_insufficient_scope(
            TestClient(app).post(f"/api/v1/projects/{info['pid']}/constraints", json=body,
                                 headers=_bearer(raw)))

    def test_auth_me_works_with_any_scope(self):
        raw = _token_for("scope_me", ["export"])
        assert TestClient(app).get("/auth/me", headers=_bearer(raw)).status_code == 200

    def test_cookie_auth_unaffected(self, auth_client):
        resp = auth_client.post("/api/v1/projects", json={"name": _unique("Cookie")})
        assert resp.status_code in (200, 201)


# ===========================================================================
# K-05: Referenzen in Constraints muessen zum Projekt gehoeren
# ===========================================================================

class TestK05ConstraintReferences:

    def _post(self, client, pid, expression, consequence=None, kind="forbid"):
        body = {"name": "c", "kind": kind, "expression": expression}
        if consequence is not None:
            body["consequence"] = consequence
        return client.post(f"/api/v1/projects/{pid}/constraints", json=body)

    def _assert_rejected(self, resp):
        assert resp.status_code == 422, resp.text
        assert resp.json()["detail"]["code"] == "constraint_reference_invalid"

    def test_category_of_other_project_rejected(self, auth_client):
        a = _project_with_values(auth_client)
        b = _project_with_values(auth_client)
        foreign = b["cats"][0]
        self._assert_rejected(self._post(
            auth_client, a["pid"],
            {"op": "eq", "category_id": foreign["id"], "value_id": foreign["values"][0]}))

    def test_value_of_other_project_rejected(self, auth_client):
        a = _project_with_values(auth_client)
        b = _project_with_values(auth_client)
        self._assert_rejected(self._post(
            auth_client, a["pid"],
            {"op": "eq", "category_id": a["cats"][0]["id"], "value_id": b["cats"][0]["values"][0]}))

    def test_unknown_ids_rejected(self, auth_client):
        a = _project_with_values(auth_client)
        self._assert_rejected(self._post(
            auth_client, a["pid"], {"op": "eq", "category_id": 999999, "value_id": 999999}))

    def test_value_of_other_category_rejected(self, auth_client):
        a = _project_with_values(auth_client)
        self._assert_rejected(self._post(
            auth_client, a["pid"],
            {"op": "in", "category_id": a["cats"][0]["id"],
             "value_ids": [a["cats"][0]["values"][0], a["cats"][1]["values"][0]]}))

    def test_nested_and_consequence_checked(self, auth_client):
        a = _project_with_values(auth_client)
        b = _project_with_values(auth_client)
        own = a["cats"][0]
        foreign = b["cats"][1]
        self._assert_rejected(self._post(
            auth_client, a["pid"],
            {"op": "and", "args": [{"op": "eq", "category_id": own["id"], "value_id": own["values"][0]},
                                   {"op": "not", "arg": {"op": "eq", "category_id": own["id"],
                                                         "value_id": own["values"][1]}}]},
            consequence={"op": "eq", "category_id": foreign["id"], "value_id": foreign["values"][0]},
            kind="implies"))

    def test_put_checked(self, auth_client):
        a = _project_with_values(auth_client)
        b = _project_with_values(auth_client)
        own = a["cats"][0]
        created = self._post(auth_client, a["pid"],
                             {"op": "eq", "category_id": own["id"], "value_id": own["values"][0]})
        assert created.status_code == 201, created.text
        foreign = b["cats"][0]
        resp = auth_client.put(
            f"/api/v1/projects/{a['pid']}/constraints/{created.json()['id']}",
            json={"expression": {"op": "eq", "category_id": foreign["id"], "value_id": foreign["values"][0]}})
        self._assert_rejected(resp)

    def test_validate_reports_foreign_reference(self, auth_client):
        a = _project_with_values(auth_client)
        b = _project_with_values(auth_client)
        foreign = b["cats"][0]
        resp = auth_client.post(f"/api/v1/projects/{a['pid']}/constraints/validate", json={
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": foreign["id"], "value_id": foreign["values"][0]}})
        assert resp.status_code == 200
        assert resp.json()["is_valid"] is False
        assert resp.json()["errors"]

    def test_valid_reference_accepted(self, auth_client):
        a = _project_with_values(auth_client)
        own = a["cats"][0]
        resp = self._post(auth_client, a["pid"],
                          {"op": "eq", "category_id": own["id"], "value_id": own["values"][0]})
        assert resp.status_code == 201, resp.text


# ===========================================================================
# K-02 / REQ-6001 AK-10: Vorab-Hinweis, dann Constraints als ungueltig markieren
# ===========================================================================

class TestK02DeleteReferenced:

    def _constraint(self, client, info, name="Keine Rechnung"):
        cat = info["cats"][0]
        resp = client.post(f"/api/v1/projects/{info['pid']}/constraints", json={
            "name": name, "kind": "forbid",
            "expression": {"op": "in", "category_id": cat["id"], "value_ids": [cat["values"][1]]}})
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def _listed(self, client, info, cid):
        items = client.get(f"/api/v1/projects/{info['pid']}/constraints").json()
        return next(c for c in items if c["id"] == cid)

    def test_delete_referenced_value_needs_confirmation(self, auth_client):
        info = _project_with_values(auth_client)
        cid = self._constraint(auth_client, info)
        vid = info["cats"][0]["values"][1]
        resp = auth_client.delete(f"/api/values/{vid}")
        assert resp.status_code == 409, resp.text
        detail = resp.json()["detail"]
        assert detail["code"] == "constraint_reference"
        assert detail["constraints"] == ["Keine Rechnung"]
        # Nichts geaendert: Wert noch da, Constraint gueltig
        vals = auth_client.get(f"/api/categories/{info['cats'][0]['id']}/values").json()
        assert vid in [v["id"] for v in vals]
        assert self._listed(auth_client, info, cid)["is_valid"] is True

    def test_confirmed_delete_marks_constraint_invalid(self, auth_client):
        info = _project_with_values(auth_client)
        cid = self._constraint(auth_client, info)
        vid = info["cats"][0]["values"][1]
        resp = auth_client.delete(f"/api/values/{vid}", params={"force": True})
        assert resp.status_code == 200, resp.text
        assert resp.json()["invalidated_constraints"] == ["Keine Rechnung"]
        # Nicht still geloescht, sondern als ungueltig sichtbar
        assert self._listed(auth_client, info, cid)["is_valid"] is False

    def test_invalid_constraint_not_applied_to_new_value(self, auth_client):
        """Kern von K-02: Auch bei wiederverwendeter ID wirkt das Constraint nicht still weiter."""
        info = _project_with_values(auth_client)
        cat = info["cats"][1]  # zuletzt angelegter Wert hat die hoechste ID
        old_vid = cat["values"][1]
        resp = auth_client.post(f"/api/v1/projects/{info['pid']}/constraints", json={
            "name": "Keine Abholung", "kind": "forbid",
            "expression": {"op": "eq", "category_id": cat["id"], "value_id": old_vid}})
        assert resp.status_code == 201, resp.text
        auth_client.delete(f"/api/values/{old_vid}", params={"force": True})
        new_vid = auth_client.post(f"/api/categories/{cat['id']}/values", json={"value": "Kurier"}).json()["id"]
        assert new_vid == old_vid, "SQLite vergibt die hoechste ID neu (Voraussetzung des Befunds)"
        gen = auth_client.post(f"/api/projects/{info['pid']}/generate",
                               json={"strategy": "all", "apply_rules": True})
        assert gen.status_code == 200, gen.text
        assert gen.json()["count"] == 4  # 2 Zahlarten x 2 Versandarten, nichts ausgeschlossen

    def test_delete_referenced_category_needs_confirmation(self, auth_client):
        info = _project_with_values(auth_client)
        cid = self._constraint(auth_client, info, name="Regel A")
        resp = auth_client.delete(f"/api/categories/{info['cats'][0]['id']}")
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"]["constraints"] == ["Regel A"]
        resp = auth_client.delete(f"/api/categories/{info['cats'][0]['id']}", params={"force": True})
        assert resp.status_code == 200, resp.text
        assert self._listed(auth_client, info, cid)["is_valid"] is False

    def test_edit_makes_invalid_constraint_valid_again(self, auth_client):
        info = _project_with_values(auth_client)
        cid = self._constraint(auth_client, info)
        cat = info["cats"][0]
        auth_client.delete(f"/api/values/{cat['values'][1]}", params={"force": True})
        resp = auth_client.put(f"/api/v1/projects/{info['pid']}/constraints/{cid}", json={
            "expression": {"op": "eq", "category_id": cat["id"], "value_id": cat["values"][0]}})
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_valid"] is True

    def test_unreferenced_value_and_category_deletable(self, auth_client):
        info = _project_with_values(auth_client)
        self._constraint(auth_client, info)
        assert auth_client.delete(f"/api/values/{info['cats'][0]['values'][0]}").status_code == 200
        assert auth_client.delete(f"/api/categories/{info['cats'][1]['id']}").status_code == 200

    def test_delete_allowed_after_constraint_removed(self, auth_client):
        info = _project_with_values(auth_client)
        cid = self._constraint(auth_client, info)
        auth_client.delete(f"/api/v1/projects/{info['pid']}/constraints/{cid}")
        assert auth_client.delete(f"/api/values/{info['cats'][0]['values'][1]}").status_code == 200

    def test_project_delete_still_possible(self, auth_client):
        info = _project_with_values(auth_client)
        self._constraint(auth_client, info)
        resp = auth_client.delete(f"/api/projects/{info['pid']}", params={"force": True})
        assert resp.status_code == 200, resp.text


# ===========================================================================
# A-07: Rate-Limit nicht ueber Token-Praefix missbrauchbar
# ===========================================================================

class TestA07RateLimitPrefix:

    def test_forged_tokens_do_not_block_real_token(self, monkeypatch):
        from app import rate_limiter
        monkeypatch.setattr(rate_limiter.token_rate_limiter, "max_attempts", 5)
        raw = _token_for("ratelimit_victim", ["projects:read"])
        prefix = raw[:16]
        attacker = TestClient(app, client=("10.0.0.66", 5000))
        for i in range(20):
            attacker.get("/api/v1/projects", headers=_bearer(prefix + f"forged{i:040d}"))
        victim = TestClient(app, client=("10.0.0.1", 5000))
        resp = victim.get("/api/v1/projects", headers=_bearer(raw))
        assert resp.status_code == 200, resp.text

    def test_failed_attempts_limited_per_ip(self, monkeypatch):
        from app import rate_limiter
        monkeypatch.setattr(rate_limiter.token_failure_rate_limiter, "max_attempts", 3)
        raw = _token_for("ratelimit_fail", ["projects:read"])
        attacker = TestClient(app, client=("10.0.0.77", 5000))
        codes = [attacker.get("/api/v1/projects", headers=_bearer(raw[:16] + "x" * 30)).status_code
                 for _ in range(5)]
        assert codes[:3] == [401, 401, 401]
        assert codes[3] == 429
        # anderer Client ist nicht betroffen
        other = TestClient(app, client=("10.0.0.2", 5000))
        assert other.get("/api/v1/projects", headers=_bearer(raw)).status_code == 200

    def test_valid_token_limit_still_enforced(self, monkeypatch):
        from app import rate_limiter
        monkeypatch.setattr(rate_limiter.token_rate_limiter, "max_attempts", 3)
        raw = _token_for("ratelimit_ok", ["projects:read"])
        client = TestClient(app)
        codes = [client.get("/api/v1/projects", headers=_bearer(raw)).status_code for _ in range(4)]
        assert codes == [200, 200, 200, 429]
