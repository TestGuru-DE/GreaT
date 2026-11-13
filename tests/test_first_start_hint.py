"""REQ-4027: Erststart-Hinweis auf der Login-Seite (Backend-Anteil).

Abgedeckte Akzeptanzkriterien: AK-1 (Konsistenz Standardpasswort), AK-6 / AK-13
(Statusendpunkt, Schluesselmenge exakt {"show_hint"}), AK-10 (Flag-Lebenszyklus),
AK-11 (Rate-Limit), AK-12 (keine Geheimnisse in Antworten/Logs), Bestandsmigration.
Risikoakzeptanz RISK-S-016 (Projektinhaber). Massnahme: REQ-4028.
REQ-4026 CR-4026-01: Reset-Pfad erzeugt Standard-Admin mit DEFAULT_ADMIN_PASSWORD.

TDD: Tests zuerst (RED), danach Implementierung (GREEN).
"""
import json
import logging
import re
from pathlib import Path

import argon2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, _migrate_db, _add_default_password_active_column
from app.database import SessionLocal, engine, Base
from app.models.auth import User
from app.bootstrap import (
    ensure_first_admin,
    backfill_default_password_flags,
    DEFAULT_ADMIN_PASSWORD,
)
from app.services import reset_database_state
from app.rate_limiter import login_rate_limiter, first_start_hint_rate_limiter
from app.system_dataclasses import seed_system_dataclasses


SRC_APP_DIR = Path(__file__).resolve().parent.parent / "src" / "app"


@pytest.fixture(autouse=True)
def _hint_db():
    """REQ-4027: Saubere Nutzerbasis je Test.

    REQ-1300: Verwendet die gemeinsame Test-DB aus conftest.
    Kein drop_all, da die DB geteilt ist und andere Tests auf demselben
    Schema arbeiten. create_all ist idempotent.
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

def _add_user(username, role, password, *, flag=False, first_admin=False, active=True):
    db = SessionLocal()
    try:
        user = User(
            username=username,
            role=role,
            is_active=active,
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
    """REQ-4020/REQ-4027: Start-Bootstrap legt den Default-Admin an."""
    db = SessionLocal()
    try:
        return ensure_first_admin(db).id
    finally:
        db.close()


def _flag_of(user_id) -> bool:
    db = SessionLocal()
    try:
        return bool(db.query(User).filter(User.id == user_id).first().default_password_active)
    finally:
        db.close()


def _legacy_users_engine():
    """Bestandsinstallation: users-Tabelle ohne Spalte default_password_active (Test-Setup)."""
    eng = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with eng.begin() as conn:
        conn.exec_driver_sql(
            "CREATE TABLE users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "username VARCHAR(50) NOT NULL UNIQUE, "
            "password_hash VARCHAR(255) NOT NULL, "
            "role VARCHAR(20) NOT NULL DEFAULT 'viewer', "
            "is_active BOOLEAN DEFAULT 1, "
            "is_first_admin BOOLEAN DEFAULT 0, "
            "created_at DATETIME NOT NULL)"
        )
    return eng


def _insert_legacy_user(eng, username, role, password, *, is_active=1, is_first_admin=0):
    pw_hash = argon2.PasswordHasher().hash(password)
    with eng.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO users (username, password_hash, role, is_active, is_first_admin, created_at) "
            "VALUES (?, ?, ?, ?, ?, '2026-01-01 00:00:00')",
            (username, pw_hash, role, is_active, is_first_admin),
        )
    return pw_hash


def _legacy_flags(eng):
    with eng.connect() as conn:
        rows = conn.exec_driver_sql(
            "SELECT username, default_password_active FROM users ORDER BY id"
        ).fetchall()
    return {row[0]: bool(row[1]) for row in rows}


# ---------------------------------------------------------------------------
# REQ-4027 AK-6 / AK-13: Statusendpunkt GET /auth/first-start-hint
# ---------------------------------------------------------------------------

class TestFirstStartHintEndpoint:
    """REQ-4027: GET /auth/first-start-hint liefert ausschliesslich show_hint."""

    def test_key_set_is_exactly_show_hint_in_all_states(self):
        """REQ-4027 AK-6/AK-13: Schluesselmenge ist in allen Zustaenden exakt {"show_hint"}."""
        client = TestClient(app)
        responses = [client.get("/auth/first-start-hint")]  # keine Nutzer

        _bootstrap_default_admin()
        responses.append(client.get("/auth/first-start-hint"))  # Default-Admin aktiv

        _add_user("viewer_state", "viewer", "Viewer-Passwort-2026")
        responses.append(client.get("/auth/first-start-hint"))  # gemischter Bestand

        for r in responses:
            assert r.status_code == 200
            body = r.json()
            assert set(body.keys()) == {"show_hint"}
            assert isinstance(body["show_hint"], bool)

    def test_show_hint_false_without_users(self):
        """REQ-4027 AK-4: Ohne Nutzer kein Hinweis."""
        r = TestClient(app).get("/auth/first-start-hint")
        assert r.json() == {"show_hint": False}

    def test_show_hint_true_after_bootstrap(self):
        """REQ-4027 AK-2: Nach Start-Bootstrap ist der Default-Admin mit Flag aktiv -> Hinweis."""
        _bootstrap_default_admin()
        r = TestClient(app).get("/auth/first-start-hint")
        assert r.json() == {"show_hint": True}

    def test_show_hint_false_after_password_change(self):
        """REQ-4027 AK-3/AK-5: Nach Passwortwechsel des Default-Admins verschwindet der Hinweis."""
        _bootstrap_default_admin()
        client = TestClient(app)

        login = client.post(
            "/auth/login",
            data={"username": "admin", "password": DEFAULT_ADMIN_PASSWORD},
        )
        assert login.status_code == 200
        assert client.get("/auth/first-start-hint").json() == {"show_hint": True}

        change = client.post(
            "/auth/change-password",
            json={"current_password": DEFAULT_ADMIN_PASSWORD, "new_password": "Neues-Passwort-2026"},
        )
        assert change.status_code == 200
        assert client.get("/auth/first-start-hint").json() == {"show_hint": False}

    def test_show_hint_false_when_default_admin_inactive(self):
        """REQ-4027 AK-2: Nur AKTIVE Konten mit Flag zaehlen."""
        user_id = _add_user("admin", "admin", DEFAULT_ADMIN_PASSWORD, flag=True, first_admin=True, active=False)
        assert user_id
        r = TestClient(app).get("/auth/first-start-hint")
        assert r.json() == {"show_hint": False}

    def test_show_hint_false_when_no_flagged_user(self):
        """REQ-4027 AK-4: Admin ohne Flag (eigenes Passwort) -> kein Hinweis."""
        _add_user("admin", "admin", "Eigenes-Passwort-2026", flag=False, first_admin=True)
        r = TestClient(app).get("/auth/first-start-hint")
        assert r.json() == {"show_hint": False}

    def test_response_has_no_store_header(self):
        """REQ-4027 AK-6: Antwort darf nicht gecacht werden."""
        _bootstrap_default_admin()
        r = TestClient(app).get("/auth/first-start-hint")
        assert r.headers.get("Cache-Control") == "no-store"

    def test_response_contains_no_user_data(self):
        """REQ-4027 AK-6/AK-12: Keine Namen, IDs, Rollen oder Passwoerter in der Antwort."""
        _bootstrap_default_admin()
        r = TestClient(app).get("/auth/first-start-hint")
        assert "admin" not in r.text
        assert "changeme" not in r.text.lower()
        assert "role" not in r.text

    def test_rate_limit_10_per_minute_then_429(self):
        """REQ-4027 AK-11: 10 Anfragen je Minute und IP, danach 429 ohne Zustandsdaten."""
        _bootstrap_default_admin()
        client = TestClient(app)
        codes = [client.get("/auth/first-start-hint").status_code for _ in range(10)]
        assert codes == [200] * 10

        r = client.get("/auth/first-start-hint")
        assert r.status_code == 429
        assert r.headers.get("Retry-After")
        assert "show_hint" not in r.text


# ---------------------------------------------------------------------------
# REQ-4027 AK-10: Flag-Lebenszyklus default_password_active
# ---------------------------------------------------------------------------

class TestDefaultPasswordFlagLifecycle:
    """REQ-4027 AK-10: Flag wird gesetzt bei Anlage, nie durch Login oder Fehlversuch geaendert."""

    def test_bootstrap_sets_flag_true(self):
        """REQ-4027 AK-10: Start-Bootstrap setzt das Flag."""
        user_id = _bootstrap_default_admin()
        assert _flag_of(user_id) is True

    def test_reset_fallback_sets_flag_true(self):
        """REQ-4027 AK-10 / REQ-4026 CR-4026-01: Reset ohne Admin setzt das Flag."""
        db = SessionLocal()
        try:
            result = reset_database_state(db)
            assert result["default_admin_created"] is True
            admin = db.query(User).filter(User.username == "admin").first()
            assert admin is not None
            assert admin.default_password_active is True
        finally:
            db.close()

    def test_successful_login_with_default_password_keeps_flag(self):
        """REQ-4027 AK-10: Login aendert das Flag nicht."""
        user_id = _bootstrap_default_admin()
        r = TestClient(app).post(
            "/auth/login",
            data={"username": "admin", "password": DEFAULT_ADMIN_PASSWORD},
        )
        assert r.status_code == 200
        assert _flag_of(user_id) is True

    def test_failed_login_keeps_flag(self):
        """REQ-4027 AK-10: Fehlversuch aendert das Flag nicht."""
        user_id = _bootstrap_default_admin()
        r = TestClient(app).post(
            "/auth/login",
            data={"username": "admin", "password": "falsches-passwort"},
        )
        assert r.status_code == 401
        assert _flag_of(user_id) is True

    def test_login_response_password_change_required_true_for_default_admin(self):
        """REQ-4028 AK-1: Login-Antwort meldet password_change_required=True."""
        _bootstrap_default_admin()
        r = TestClient(app).post(
            "/auth/login",
            data={"username": "admin", "password": DEFAULT_ADMIN_PASSWORD},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["password_change_required"] is True
        assert body["username"] == "admin"
        assert body["role"] == "admin"
        assert body["message"] == "Login erfolgreich"

    def test_login_response_password_change_required_false_for_regular_user(self):
        """REQ-4028 AK-1: Normaler Nutzer ohne Flag -> password_change_required=False."""
        _add_user("regular_user", "editor", "Regular-Passwort-2026")
        r = TestClient(app).post(
            "/auth/login",
            data={"username": "regular_user", "password": "Regular-Passwort-2026"},
        )
        assert r.status_code == 200
        assert r.json()["password_change_required"] is False

    def test_me_contains_password_change_required(self):
        """REQ-4028 AK-1: GET /auth/me liefert password_change_required, andere Felder unveraendert."""
        _bootstrap_default_admin()
        client = TestClient(app)
        client.post("/auth/login", data={"username": "admin", "password": DEFAULT_ADMIN_PASSWORD})
        r = client.get("/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["password_change_required"] is True
        assert set(body.keys()) == {"user_id", "username", "role", "is_active", "password_change_required"}


# ---------------------------------------------------------------------------
# REQ-4027 AK-1 / AK-12 / REQ-4026 CR-4026-01: Konsistenz des Standardpassworts
# ---------------------------------------------------------------------------

class TestDefaultPasswordConsistency:
    """REQ-4027 AK-1: Standardpasswort genau einmal definiert, alle Pfade nutzen es."""

    def test_default_password_constant_value(self):
        """REQ-4027 AK-1 / CR-4026-01: Wert ist changeme123!."""
        assert DEFAULT_ADMIN_PASSWORD == "changeme123!"

    def test_bootstrap_admin_uses_default_constant(self):
        """REQ-4027 AK-1: Start-Bootstrap erzeugt Admin mit DEFAULT_ADMIN_PASSWORD."""
        db = SessionLocal()
        try:
            admin = ensure_first_admin(db)
            assert admin.username == "admin"
            assert admin.check_password(DEFAULT_ADMIN_PASSWORD) is True
        finally:
            db.close()

    def test_reset_admin_uses_default_constant(self):
        """REQ-4026 CR-4026-01: Reset-Fallback erzeugt Admin mit DEFAULT_ADMIN_PASSWORD (nicht admin123)."""
        db = SessionLocal()
        try:
            reset_database_state(db)
            admin = db.query(User).filter(User.username == "admin").first()
            assert admin.check_password(DEFAULT_ADMIN_PASSWORD) is True
            assert admin.check_password("admin123") is False
        finally:
            db.close()

    def test_reset_response_contains_no_password(self):
        """REQ-4027 AK-12: Reset-Antwort gibt kein Passwort aus, nur den Benutzernamen."""
        db = SessionLocal()
        try:
            result = reset_database_state(db)
        finally:
            db.close()
        serialized = json.dumps(result)
        assert DEFAULT_ADMIN_PASSWORD not in serialized
        assert "admin123" not in serialized
        assert result["default_admin_username"] == "admin"

    def test_reset_response_username_none_when_no_admin_created(self):
        """REQ-4026: Ohne Neuanlage kein Benutzername in der Antwort."""
        _add_user("keeper_admin", "admin", "Keeper-Passwort-2026", first_admin=True)
        db = SessionLocal()
        try:
            result = reset_database_state(db)
        finally:
            db.close()
        assert result["default_admin_created"] is False
        assert result["default_admin_username"] is None

    def test_literal_default_password_defined_once_in_backend(self):
        """REQ-4027 AK-1: Der Literalwert steht genau einmal in src/app (Konstante)."""
        hits = []
        for path in SRC_APP_DIR.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"[\"']changeme123![\"']", text):
                hits.append(path.name)
        assert hits == ["bootstrap.py"], f"Literal ausserhalb der Konstante gefunden: {hits}"


# ---------------------------------------------------------------------------
# REQ-4027 AK-10: Bestandsmigration (Spalte + Backfill, idempotent)
# ---------------------------------------------------------------------------

class TestDefaultPasswordMigration:
    """REQ-4027 AK-10: Spalte per _migrate_db, Backfill fuer Bestandsinstallationen."""

    def test_migrate_db_is_idempotent(self):
        """Mehrfaches _migrate_db erzeugt keinen Fehler und keine Doppelspalte."""
        _migrate_db()
        _migrate_db()
        with engine.connect() as conn:
            cols = conn.exec_driver_sql("PRAGMA table_info('users')").fetchall()
        names = [c[1] for c in cols]
        assert names.count("default_password_active") == 1

    def test_add_column_helper_adds_column_once(self):
        """Legacy-Tabelle bekommt die Spalte; zweiter Aufruf ist ein No-Op."""
        eng = _legacy_users_engine()
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
            _add_default_password_active_column(conn)
            cols = conn.exec_driver_sql("PRAGMA table_info('users')").fetchall()
        assert [c[1] for c in cols].count("default_password_active") == 1

    def test_backfill_sets_flag_for_first_admin_with_default_password(self):
        """Bestandsinstallation mit changeme123! -> Flag 1."""
        eng = _legacy_users_engine()
        _insert_legacy_user(eng, "admin", "admin", DEFAULT_ADMIN_PASSWORD, is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        try:
            backfill_default_password_flags(session)
        finally:
            session.close()
        assert _legacy_flags(eng)["admin"] is True

    def test_backfill_treats_legacy_admin123_as_default(self):
        """Reset-Altwert admin123 gilt ebenfalls als Standardpasswort -> Flag 1."""
        eng = _legacy_users_engine()
        _insert_legacy_user(eng, "admin", "admin", "admin123", is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        try:
            backfill_default_password_flags(session)
        finally:
            session.close()
        assert _legacy_flags(eng)["admin"] is True

    def test_backfill_sets_flag_zero_for_changed_password(self):
        """Geaendertes Passwort -> Flag 0."""
        eng = _legacy_users_engine()
        _insert_legacy_user(eng, "chef", "admin", "Eigenes-Passwort-2026", is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        try:
            backfill_default_password_flags(session)
        finally:
            session.close()
        assert _legacy_flags(eng)["chef"] is False

    def test_backfill_ignores_non_first_admin_and_inactive_accounts(self):
        """Scope: nur aktive Erst-Admins. Andere Konten bleiben unveraendert (Flag 0)."""
        eng = _legacy_users_engine()
        _insert_legacy_user(eng, "editor_default", "editor", DEFAULT_ADMIN_PASSWORD, is_first_admin=0)
        _insert_legacy_user(eng, "inaktiv", "admin", DEFAULT_ADMIN_PASSWORD, is_active=0, is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        try:
            backfill_default_password_flags(session)
        finally:
            session.close()
        flags = _legacy_flags(eng)
        assert flags["editor_default"] is False
        assert flags["inaktiv"] is False

    def test_backfill_is_idempotent(self):
        """Zweiter Lauf veraendert nichts."""
        eng = _legacy_users_engine()
        _insert_legacy_user(eng, "admin", "admin", DEFAULT_ADMIN_PASSWORD, is_first_admin=1)
        _insert_legacy_user(eng, "chef", "admin", "Eigenes-Passwort-2026", is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        try:
            backfill_default_password_flags(session)
            first = _legacy_flags(eng)
            backfill_default_password_flags(session)
            second = _legacy_flags(eng)
        finally:
            session.close()
        assert first == second == {"admin": True, "chef": False}

    def test_backfill_logs_no_password_or_hash(self, caplog, capsys):
        """REQ-4027 AK-12: Backfill gibt weder Passwort noch Hash aus."""
        eng = _legacy_users_engine()
        pw_hash = _insert_legacy_user(eng, "admin", "admin", DEFAULT_ADMIN_PASSWORD, is_first_admin=1)
        with eng.begin() as conn:
            _add_default_password_active_column(conn)
        session = sessionmaker(bind=eng)()
        caplog.set_level(logging.DEBUG)
        try:
            backfill_default_password_flags(session)
        finally:
            session.close()
        out = capsys.readouterr()
        combined = caplog.text + out.out + out.err
        assert DEFAULT_ADMIN_PASSWORD not in combined
        assert pw_hash not in combined
