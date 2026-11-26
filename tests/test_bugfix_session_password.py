"""B-06: Eigener Passwortwechsel beendet die eigene Sitzung nicht.

Andere Sitzungen desselben Nutzers werden weiterhin ungueltig (Sicherheitsziel von B-06).
"""
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.auth import User

OLD = "Alt-Passwort-2026!"
NEW = "Neu-Passwort-2026!"


def _user(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username=username, role="editor")
            db.add(user)
        user.is_active = True
        user.default_password_active = False
        user.token_version = 0
        user.set_password(OLD)
        db.commit()
    finally:
        db.close()


def _login(username: str, password: str = OLD) -> TestClient:
    client = TestClient(app)
    resp = client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return client


def test_own_session_survives_password_change():
    _user("pw_self")
    client = _login("pw_self")
    resp = client.post("/auth/change-password", json={"current_password": OLD, "new_password": NEW})
    assert resp.status_code == 200, resp.text
    me = client.get("/auth/me")
    assert me.status_code == 200, me.text
    assert client.get("/api/projects").status_code == 200


def test_refresh_works_after_password_change():
    _user("pw_refresh")
    client = _login("pw_refresh")
    client.post("/auth/change-password", json={"current_password": OLD, "new_password": NEW})
    assert client.post("/auth/refresh").status_code == 200
    assert client.get("/auth/me").status_code == 200


def test_other_sessions_are_ended():
    _user("pw_other")
    other = _login("pw_other")
    me = _login("pw_other")
    me.post("/auth/change-password", json={"current_password": OLD, "new_password": NEW})
    assert other.get("/auth/me").status_code == 401
    assert other.post("/auth/refresh").status_code == 401


def test_failed_change_keeps_session_and_cookies():
    _user("pw_fail")
    client = _login("pw_fail")
    resp = client.post("/auth/change-password",
                       json={"current_password": "falsch-falsch-1", "new_password": NEW})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "current_password_invalid"
    assert "set-cookie" not in resp.headers
    assert client.get("/auth/me").status_code == 200


def test_common_password_reports_code():
    """N-01: password1234 liefert einen auswertbaren Code."""
    _user("pw_common")
    client = _login("pw_common")
    resp = client.post("/auth/change-password",
                       json={"current_password": OLD, "new_password": "password1234"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "password_too_common"
