"""REQ-4028: Pflicht-Passwortwechsel nach Erstanmeldung (serverseitige Sperre).

Abgedeckte Akzeptanzkriterien: AK-2 (Sperre 403 password_change_required, Endpunkt-Matrix),
AK-3 (Selbst-Wechsel fuer alle Rollen, aktuelles Passwort), AK-4 (Mindestlaenge 12),
AK-5 (Default-Ablehnung, case-insensitive, nach Trim), AK-6 (Flag loeschen),
AK-7 (serverseitig, kein Umgehen), AK-8 (Fehlversuche rate-limitiert), AK-9 (keine Geheimnisse).
Zusatz: REQ-4025 PUT /api/users/{id}/password nutzt dieselbe Policy (Entscheidung Projektinhaber).
Massnahme zu RISK-S-016.

TDD: Tests zuerst (RED), danach Implementierung (GREEN).
"""
import json
import re

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app, _migrate_db
from app.database import SessionLocal, engine, Base
from app.models.auth import User
from app.auth_utils import create_access_token
from app.auth_deps import get_current_user
from app.bootstrap import ensure_first_admin, DEFAULT_ADMIN_PASSWORD
from app.rate_limiter import login_rate_limiter, first_start_hint_rate_limiter, password_change_rate_limiter
from app.system_dataclasses import seed_system_dataclasses


GOOD_NEW = "Neues-Passwort-2026"  # 19 Zeichen, kein Standardpasswort
OLD_PASSWORD = "Alt-Passwort-2026"
EXEMPT_PATHS = {
    "/auth/me",
    "/auth/logout",
    "/auth/refresh",
    "/auth/change-password",
    "/auth/first-start-hint",
    "/auth/login",
}


@pytest.fixture(autouse=True)
def _pw_db():
    """REQ-4028: Saubere Nutzerbasis je Test.

    REQ-1300: Verwendet die gemeinsame Test-DB aus conftest.
    Kein drop_all, da die DB geteilt ist und andere Tests auf demselben
    Schema arbeiten. create_all ist idempotent (tut nichts, wenn Tabellen
    bereits existieren).
    """
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
    finally:
        db.close()
    # Limiter werden bereits in conftest.py::pytest_runtest_setup geleaert
    yield


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------

def _add_user(username, role, password, *, flag=False, first_admin=False):
    db = SessionLocal()
    try:
        user = User(
            username=username,
            role=role,
            is_active=True,
            is_first_admin=first_admin,
            default_password_active=flag,
        )
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _bootstrap_default_admin():
    db = SessionLocal()
    try:
        return ensure_first_admin(db).id
    finally:
        db.close()


def _client_for(user_id) -> TestClient:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        token = create_access_token(user.id, user.username, user.role)
    finally:
        db.close()
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("access_token", token)
    return client


def _state(user_id):
    """Liefert (flag, hash) aus der DB."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return bool(user.default_password_active), user.password_hash
    finally:
        db.close()


def _verify(user_id, password) -> bool:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first().check_password(password)
    finally:
        db.close()


def _detail(response):
    try:
        return response.json().get("detail")
    except Exception:
        return None


def _uses_locked_dependency(dependant) -> bool:
    if dependant.call is get_current_user:
        return True
    return any(_uses_locked_dependency(sub) for sub in dependant.dependencies)


def _protected_route_calls():
    """Alle Routen, die ueber get_current_user (gesperrt) laufen: (Methode, konkreter Pfad, Vorlage)."""
    calls = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not _uses_locked_dependency(route.dependant):
            continue
        concrete = re.sub(r"\{[^}]+\}", "1", route.path)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            calls.append((method, concrete, route.path))
    return calls


# ---------------------------------------------------------------------------
# REQ-4028 AK-2 / AK-7: serverseitige Sperre
# ---------------------------------------------------------------------------

class TestPasswordChangeLock:
    """REQ-4028 AK-2: Solange default_password_active gesetzt ist, liefern geschuetzte Routen 403."""

    @pytest.mark.parametrize(
        "role,path",
        [
            ("admin", "/auth/admin-only"),
            ("editor", "/auth/writer-only"),
            ("viewer", "/auth/api-capable"),
            ("api_user", "/auth/api-capable"),
        ],
    )
    def test_each_role_is_locked_with_password_change_required(self, role, path):
        """REQ-4028 AK-2: Mindestens eine Route je Rolle liefert 403 password_change_required."""
        user_id = _add_user(f"locked_{role}", role, OLD_PASSWORD, flag=True)
        r = _client_for(user_id).get(path)
        assert r.status_code == 403
        assert r.json() == {"detail": "password_change_required"}

    def test_every_protected_route_is_locked_for_flagged_admin(self):
        """REQ-4028 AK-2: Endpunkt-Matrix – alle geschuetzten Routen x Flag gesetzt -> 403."""
        calls = _protected_route_calls()
        assert len(calls) >= 20, "Endpunkt-Matrix unvollstaendig (zu wenige geschuetzte Routen gefunden)"
        assert not [t for _, _, t in calls if t in EXEMPT_PATHS], "Ausnahmepfad in der Sperr-Matrix"

        user_id = _bootstrap_default_admin()
        client = _client_for(user_id)
        failures = []
        for method, concrete, template in calls:
            r = client.request(method, concrete)
            if r.status_code != 403 or _detail(r) != "password_change_required":
                failures.append(f"{method} {template} -> {r.status_code}")
        assert not failures, "Nicht gesperrt: " + "; ".join(failures)

    def test_unflagged_admin_is_not_locked_on_get_routes(self):
        """REQ-4028 AK-2 (Gegenprobe): Ohne Flag greift die Sperre nicht."""
        user_id = _add_user("free_admin", "admin", OLD_PASSWORD, flag=False)
        client = _client_for(user_id)
        for method, concrete, template in _protected_route_calls():
            if method != "GET":
                continue
            r = client.get(concrete)
            assert _detail(r) != "password_change_required", template

    def test_exempt_routes_are_reachable_for_flagged_user(self):
        """REQ-4028 AK-2: Login/Refresh/Logout/Statusendpunkt/eigener Wechsel/Me sind nicht gesperrt."""
        user_id = _bootstrap_default_admin()
        client = _client_for(user_id)

        me = client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["password_change_required"] is True

        hint = client.get("/auth/first-start-hint")
        assert hint.status_code == 200

        change = client.post(
            "/auth/change-password",
            json={"current_password": "falsch-passwort-1", "new_password": GOOD_NEW},
        )
        assert change.status_code == 400
        assert _detail(change) == "current_password_invalid"

        refresh = client.post("/auth/refresh")
        assert refresh.status_code == 401  # kein Refresh-Cookie, aber nicht gesperrt

        logout = client.post("/auth/logout")
        assert logout.status_code == 200

    def test_flagged_admin_cannot_use_admin_password_route_on_self(self):
        """REQ-4028 AK-7: Auch der Admin-Passwort-Pfad ist fuer den gesperrten Nutzer zu."""
        user_id = _bootstrap_default_admin()
        r = _client_for(user_id).put(
            f"/api/users/{user_id}/password",
            json={"new_password": GOOD_NEW},
        )
        assert r.status_code == 403
        assert _detail(r) == "password_change_required"
        assert _verify(user_id, DEFAULT_ADMIN_PASSWORD)


# ---------------------------------------------------------------------------
# REQ-4028 AK-3 / AK-4 / AK-5 / AK-6 / AK-8 / AK-9: Selbst-Wechsel
# ---------------------------------------------------------------------------

class TestSelfChangePassword:
    """REQ-4028 AK-3: POST /auth/change-password (eingeloggt, alle Rollen)."""

    def test_requires_authentication(self):
        """Ohne Token -> 401."""
        r = TestClient(app, raise_server_exceptions=False).post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": GOOD_NEW},
        )
        assert r.status_code == 401

    @pytest.mark.parametrize("role", ["admin", "editor", "viewer", "api_user"])
    def test_every_role_can_change_own_password(self, role):
        """REQ-4028 AK-3: Selbst-Wechsel fuer alle Rollen -> 200, Passwort gesetzt."""
        user_id = _add_user(f"self_{role}", role, OLD_PASSWORD, flag=False)
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": GOOD_NEW},
        )
        assert r.status_code == 200
        assert _verify(user_id, GOOD_NEW)
        assert not _verify(user_id, OLD_PASSWORD)

    def test_wrong_current_password_is_rejected_and_flag_kept(self):
        """REQ-4028 AK-3/AK-8: Falsches aktuelles Passwort -> 400, Flag und Hash unveraendert."""
        user_id = _bootstrap_default_admin()
        flag_before, hash_before = _state(user_id)
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": "falsch-passwort-1", "new_password": GOOD_NEW},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "current_password_invalid"}
        flag_after, hash_after = _state(user_id)
        assert flag_after is True
        assert hash_after == hash_before

    @pytest.mark.parametrize(
        "candidate",
        [
            DEFAULT_ADMIN_PASSWORD,          # changeme123!
            "CHANGEME123!",                  # case-insensitive
            "  Changeme123!  ",              # nach Trim
            "admin123",
            "ADMIN123",
            "admin",
            "Password",
        ],
    )
    def test_known_default_passwords_are_rejected(self, candidate):
        """REQ-4028 AK-5 / REQ-4027 AK-14: Bekannte Standardpasswoerter abgelehnt, Flag bleibt."""
        user_id = _bootstrap_default_admin()
        client = _client_for(user_id)
        r = client.post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": candidate},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "password_is_default"}
        assert candidate.strip() not in r.text  # REQ-4028 AK-9: kein Echo des abgelehnten Passworts
        assert _state(user_id)[0] is True

    def test_rejected_default_does_not_echo_password(self):
        """REQ-4028 AK-9: Fehlermeldung gibt das abgelehnte Passwort nicht zurueck."""
        user_id = _bootstrap_default_admin()
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": "CHANGEME123!"},
        )
        assert "CHANGEME123!" not in r.text
        assert "changeme" not in r.text.lower()

    def test_minimum_length_12_rejects_11_chars(self):
        """REQ-4028 AK-4: 11 Zeichen -> 400 password_too_short."""
        user_id = _bootstrap_default_admin()
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": "Abcdefghij1"},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "password_too_short"}
        assert _state(user_id)[0] is True

    def test_minimum_length_accepts_exactly_12_chars(self):
        """REQ-4028 AK-4: Genau 12 Zeichen ist zulaessig."""
        user_id = _add_user("edge_user", "editor", OLD_PASSWORD)
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": "Abcdefghij12"},
        )
        assert r.status_code == 200

    def test_maximum_length_128_rejected(self):
        """Schutz gegen ueberlange Eingaben: 129 Zeichen -> 400 password_too_long."""
        user_id = _add_user("long_user", "editor", OLD_PASSWORD)
        r = _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": "A" * 129},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "password_too_long"}

    def test_success_clears_flag_and_unlocks_routes(self):
        """REQ-4028 AK-6/AK-2: Erfolg -> Flag 0, gesperrte Route danach erreichbar."""
        user_id = _bootstrap_default_admin()
        client = _client_for(user_id)
        assert client.get("/api/users/").status_code == 403

        r = client.post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": GOOD_NEW},
        )
        assert r.status_code == 200
        assert r.json() == {"message": "Passwort geaendert"}

        flag, _ = _state(user_id)
        assert flag is False
        assert _verify(user_id, GOOD_NEW)
        assert client.get("/api/users/").status_code == 200
        assert client.get("/auth/me").json()["password_change_required"] is False

    def test_success_response_and_errors_do_not_echo_passwords(self):
        """REQ-4028 AK-9: Weder Erfolg noch Fehler geben Passwoerter aus."""
        user_id = _add_user("echo_user", "editor", OLD_PASSWORD)
        client = _client_for(user_id)
        bad = client.post(
            "/auth/change-password",
            json={"current_password": "falsch-passwort-1", "new_password": "kurz"},
        )
        assert "falsch-passwort-1" not in bad.text
        assert "kurz" not in bad.text
        ok = client.post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": GOOD_NEW},
        )
        assert GOOD_NEW not in ok.text
        assert OLD_PASSWORD not in ok.text

    def test_failed_policy_attempt_keeps_flag(self):
        """REQ-4028 AK-6: Abgelehntes neues Passwort loescht das Flag nicht."""
        user_id = _bootstrap_default_admin()
        _client_for(user_id).post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": "zu-kurz"},
        )
        assert _state(user_id)[0] is True

    def test_failed_attempts_are_rate_limited_per_account(self):
        """REQ-4028 AK-8: 10 Versuche je Minute je Konto, danach 429 (auch mit richtigem Passwort)."""
        user_id = _add_user("rl_user", "editor", OLD_PASSWORD)
        client = _client_for(user_id)
        for _ in range(10):
            r = client.post(
                "/auth/change-password",
                json={"current_password": "falsch-passwort-1", "new_password": GOOD_NEW},
            )
            assert r.status_code == 400

        r = client.post(
            "/auth/change-password",
            json={"current_password": OLD_PASSWORD, "new_password": GOOD_NEW},
        )
        assert r.status_code == 429
        assert r.headers.get("Retry-After")
        assert _detail(r) == "too_many_attempts"
        assert _verify(user_id, OLD_PASSWORD)


# ---------------------------------------------------------------------------
# REQ-4025 PUT /api/users/{id}/password: gleiche Policy + Flag-Rueckstellung
# ---------------------------------------------------------------------------

class TestAdminSetPasswordPolicy:
    """REQ-4028 AK-4/AK-5/AK-6 gelten auch fuer die Admin-Passwortsetzung (REQ-4025)."""

    def test_admin_rejects_default_password_for_other_user(self):
        """Admin kann einem Nutzer kein bekanntes Standardpasswort setzen -> 400."""
        admin_id = _add_user("adm_pol", "admin", OLD_PASSWORD)
        target_id = _add_user("tgt_pol", "editor", OLD_PASSWORD)
        r = _client_for(admin_id).put(
            f"/api/users/{target_id}/password",
            json={"new_password": DEFAULT_ADMIN_PASSWORD},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "password_is_default"}
        assert _verify(target_id, OLD_PASSWORD)

    def test_admin_rejects_short_password(self):
        """Mindestlaenge 12 gilt auch fuer Admin-Setzung -> 400."""
        admin_id = _add_user("adm_short", "admin", OLD_PASSWORD)
        target_id = _add_user("tgt_short", "editor", OLD_PASSWORD)
        r = _client_for(admin_id).put(
            f"/api/users/{target_id}/password",
            json={"new_password": "kurz"},
        )
        assert r.status_code == 400
        assert r.json() == {"detail": "password_too_short"}

    def test_admin_sets_valid_password_and_clears_flag_of_default_admin(self):
        """REQ-4027 AK-10: Fremdsetzung eines gueltigen Passworts loescht das Flag des Default-Admins."""
        default_id = _bootstrap_default_admin()
        other_admin_id = _add_user("adm_other", "admin", OLD_PASSWORD)
        r = _client_for(other_admin_id).put(
            f"/api/users/{default_id}/password",
            json={"new_password": GOOD_NEW},
        )
        assert r.status_code == 200
        assert _state(default_id)[0] is False
        assert _verify(default_id, GOOD_NEW)

    def test_admin_password_route_still_denied_for_editor(self):
        """Bestehende Rechteregel bleibt: Editor darf fremdes Passwort nicht setzen -> 403."""
        editor_id = _add_user("ed_pol", "editor", OLD_PASSWORD)
        admin_id = _add_user("adm_pol2", "admin", OLD_PASSWORD)
        r = _client_for(editor_id).put(
            f"/api/users/{admin_id}/password",
            json={"new_password": GOOD_NEW},
        )
        assert r.status_code == 403
        assert _verify(admin_id, OLD_PASSWORD)
