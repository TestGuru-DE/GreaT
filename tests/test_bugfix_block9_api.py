"""Restbefunde Themenblock 9a: Log-Schwaerzung (N-06), Login-Reihenfolge, /api/v1-Aliase."""
import itertools
import logging

import pytest

from app.database import SessionLocal
from app.logging_config import RedactSecretsFilter, redact_secrets
from app.models.auth import User

_counter = itertools.count()


# ===========================================================================
# N-06: Passwort aus der URL erscheint nicht im Zugriffslog
# ===========================================================================

@pytest.mark.parametrize("raw, expected", [
    ("GET /api/backup?password=geheim HTTP/1.1", "GET /api/backup?password=*** HTTP/1.1"),
    ("GET /x?a=1&Password=geheim&b=2", "GET /x?a=1&Password=***&b=2"),
    ("GET /x?token=great_pat_abc", "GET /x?token=***"),
    ("GET /api/projects?name=Shop", "GET /api/projects?name=Shop"),
])
def test_redact_secrets(raw, expected):
    assert redact_secrets(raw) == expected


def test_access_log_record_is_redacted():
    # uvicorn.access loggt: '%s - "%s %s HTTP/%s" %d' mit dem Pfad inkl. Query als Argument
    record = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1,
                               '%s - "%s %s HTTP/%s" %d',
                               ("127.0.0.1:5000", "GET", "/api/backup?password=geheim", "1.1", 400), None)
    RedactSecretsFilter().filter(record)
    assert "geheim" not in record.getMessage()


def test_filter_installed_on_uvicorn_access_logger():
    import app.main  # noqa: F401 - setup_logging() laeuft beim Import
    assert any(isinstance(f, RedactSecretsFilter) for f in logging.getLogger("uvicorn.access").filters)


# ===========================================================================
# Login verraet die Rolle api_user nicht fuer deaktivierte Konten
# ===========================================================================

def _user(role, active):
    name = f"b9-{role}-{next(_counter)}"
    db = SessionLocal()
    try:
        user = User(username=name, role=role, is_active=active)
        user.set_password("Blau-Tanne-Kiesel-47")
        user.default_password_active = False
        db.add(user)
        db.commit()
    finally:
        db.close()
    return name


def test_inactive_api_user_gets_generic_deactivated_message(client):
    name = _user("api_user", active=False)
    resp = client.post("/auth/login", data={"username": name, "password": "Blau-Tanne-Kiesel-47"})
    assert resp.status_code == 403
    assert "api_user" not in resp.text
    assert resp.json()["detail"] == "Konto ist deaktiviert"


def test_active_api_user_still_cannot_login(client):
    name = _user("api_user", active=True)
    resp = client.post("/auth/login", data={"username": name, "password": "Blau-Tanne-Kiesel-47"})
    assert resp.status_code == 403
    assert "API-Token" in resp.json()["detail"]


# ===========================================================================
# /api/v1-Alias fuer alle /api-Pfade
# ===========================================================================

def test_every_api_path_has_v1_alias():
    from app.main import app
    paths = {r.path for r in app.routes if hasattr(r, "methods")}
    missing = sorted(p for p in paths if p.startswith("/api/") and not p.startswith("/api/v1/")
                     and "/api/v1/" + p[len("/api/"):] not in paths)
    assert missing == []


def test_v1_alias_returns_same_answer(admin_client):
    assert admin_client.get("/api/v1/users/").json() == admin_client.get("/api/users/").json()


def test_v1_alias_keeps_role_check(auth_client):
    # Benutzerverwaltung bleibt Admins vorbehalten, auch unter /api/v1
    assert auth_client.get("/api/v1/users/").status_code == 403


@pytest.mark.parametrize("path", ["/api/v1/users/", "/api/v1/backup"])
def test_api_token_blocked_on_v1_alias(client, path):
    from app.api_token_service import create_api_token

    db = SessionLocal()
    try:
        name = _user("admin", active=True)
        user = db.query(User).filter(User.username == name).one()
        raw, _ = create_api_token(db, user, "b9", ["projects:read", "projects:write"])
    finally:
        db.close()
    resp = client.get(path, headers={"Authorization": f"Bearer {raw}"})
    assert resp.status_code == 403
    assert resp.headers.get("X-Error-Code") == "api_token_blocked_endpoint" or "API" in resp.text


# ===========================================================================
# N-04: .env.example nennt jede Umgebungsvariable, die der Server liest
# ===========================================================================

def test_env_example_lists_all_variables():
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[1]
    used = set()
    for path in (root / "src" / "app").rglob("*.py"):
        used |= set(re.findall(r"""os\.(?:getenv|environ\.get)\(\s*["']([A-Z][A-Z0-9_]+)["']""", path.read_text(encoding="utf-8")))
    documented = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", (root / ".env.example").read_text(encoding="utf-8"), re.M))
    assert sorted(used - documented) == []
