"""BUG A-01: Rolle api_user war unbenutzbar.

- Login per Oberflaeche ist fuer api_user gesperrt (gewollt, REQ-6012).
- Ein Admin konnte aber kein Token fuer einen api_user anlegen (Token gehoerte
  immer dem Aufrufer), und selbst ein Token scheiterte an
  403 password_change_required, weil das Passwort-Flag beim Anlegen gesetzt
  wurde und vom api_user nie zurueckgesetzt werden kann.

PO-Entscheidung: Admin legt Tokens fuer technische Nutzer an; fuer api_user gilt
keine Passwortwechsel-Pflicht.
"""
import uuid

import pytest

from app.database import SessionLocal
from app.models.auth import ApiToken, User


@pytest.fixture(autouse=True)
def _cleanup_tokens():
    yield
    db = SessionLocal()
    try:
        db.query(ApiToken).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _create_user(admin_client, role):
    name = f"tech{uuid.uuid4().hex[:6]}"
    r = admin_client.post("/api/users/", json={"username": name, "password": "Techn-Pass-2026!x", "role": role})
    assert r.status_code == 201, r.text
    return r.json()["id"], name


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_creates_token_for_api_user_and_token_works(admin_client, client):
    uid, _ = _create_user(admin_client, "api_user")
    r = admin_client.post("/api/v1/api-tokens/", json={
        "name": "Jenkins", "scopes": ["projects:read", "generate"], "expires_in_days": 30, "user_id": uid,
    })
    assert r.status_code == 201, r.text
    token = r.json()["token"]
    assert r.json()["user_id"] == uid

    r = client.get("/api/v1/projects", headers=_bearer(token))
    assert r.status_code == 200, r.text


def test_new_api_user_has_no_password_change_flag(admin_client):
    uid, _ = _create_user(admin_client, "api_user")
    db = SessionLocal()
    try:
        assert db.get(User, uid).default_password_active is False
    finally:
        db.close()


def test_new_human_user_still_must_change_password(admin_client):
    """Regression B-22: fuer Menschen bleibt die Pflicht bestehen."""
    uid, _ = _create_user(admin_client, "editor")
    db = SessionLocal()
    try:
        assert db.get(User, uid).default_password_active is True
    finally:
        db.close()


def test_legacy_api_user_with_flag_is_not_blocked(admin_client, client):
    """Bestandsdaten: api_user mit gesetztem Flag (vor dem Fix angelegt)."""
    uid, _ = _create_user(admin_client, "api_user")
    db = SessionLocal()
    try:
        db.get(User, uid).default_password_active = True
        db.commit()
    finally:
        db.close()
    token = admin_client.post("/api/v1/api-tokens/", json={
        "name": "Legacy", "scopes": ["projects:read"], "user_id": uid,
    }).json()["token"]
    r = client.get("/api/v1/projects", headers=_bearer(token))
    assert r.status_code == 200, r.text


def test_admin_password_reset_of_api_user_keeps_flag_off(admin_client):
    uid, _ = _create_user(admin_client, "api_user")
    r = admin_client.put(f"/api/users/{uid}/password", json={"password": "Neues-Techn-2026!x"})
    assert r.status_code == 200, r.text
    db = SessionLocal()
    try:
        assert db.get(User, uid).default_password_active is False
    finally:
        db.close()


def test_api_user_login_still_forbidden(admin_client, client):
    _, name = _create_user(admin_client, "api_user")
    r = client.post("/auth/login", data={"username": name, "password": "Techn-Pass-2026!x"})
    assert r.status_code == 403


def test_non_admin_cannot_create_token_for_other_user(admin_client, auth_client):
    uid, _ = _create_user(admin_client, "api_user")
    r = auth_client.post("/api/v1/api-tokens/", json={"name": "x", "scopes": ["projects:read"], "user_id": uid})
    assert r.status_code == 403, r.text


@pytest.mark.parametrize("role", ["editor", "viewer", "admin"])
def test_admin_cannot_create_token_for_human_user(admin_client, role):
    uid, _ = _create_user(admin_client, role)
    r = admin_client.post("/api/v1/api-tokens/", json={"name": "x", "scopes": ["projects:read"], "user_id": uid})
    assert r.status_code == 400, r.text


def test_token_for_unknown_or_inactive_user(admin_client):
    r = admin_client.post("/api/v1/api-tokens/", json={"name": "x", "scopes": ["projects:read"], "user_id": 999999})
    assert r.status_code == 404, r.text
    uid, _ = _create_user(admin_client, "api_user")
    admin_client.put(f"/api/users/{uid}", json={"is_active": False})
    r = admin_client.post("/api/v1/api-tokens/", json={"name": "x", "scopes": ["projects:read"], "user_id": uid})
    assert r.status_code == 400, r.text


def test_own_token_without_user_id_unchanged(admin_client):
    r = admin_client.post("/api/v1/api-tokens/", json={"name": "eigen", "scopes": ["projects:read"]})
    assert r.status_code == 201, r.text


def test_admin_token_list_shows_owner(admin_client):
    uid, name = _create_user(admin_client, "api_user")
    admin_client.post("/api/v1/api-tokens/", json={"name": "Owned", "scopes": ["projects:read"], "user_id": uid})
    rows = admin_client.get("/api/v1/admin/api-tokens/").json()
    owned = [t for t in rows if t["name"] == "Owned"]
    assert owned and owned[0]["user_id"] == uid and owned[0]["username"] == name


def test_invalid_scope_is_400_not_500(admin_client):
    """Nebenbefund A-17: ungueltiger Scope fuehrte zu 500."""
    r = admin_client.post("/api/v1/api-tokens/", json={"name": "x", "scopes": ["root"]})
    assert r.status_code in (400, 422), r.text
