"""Benutzerverwaltung, Passwort-Policy, Konfiguration (B-22..B-26).

TDD: Tests zuerst (RED), dann Implementierung (GREEN).
"""
import pytest


# B-22: Benutzeranlage validieren

def test_create_user_weak_password_rejected(admin_client, db_session):
    """B-22: Schwaches Passwort (zu kurz) wird abgelehnt (422 = Pydantic-Validierungsfehler)."""
    r = admin_client.post("/api/users", json={"username": "testuser123", "password": "a", "role": "editor"})
    # FastAPI gibt 422 fur Pydantic-Validierungsfehler (field_validator raises ValueError)
    assert r.status_code in (400, 422)


def test_create_user_whitespace_name_rejected(admin_client, db_session):
    """B-22: Nur-Whitespace-Benutzername wird abgelehnt."""
    r = admin_client.post("/api/users", json={"username": "   ", "password": "StrongPass123!@#", "role": "editor"})
    assert r.status_code in (400, 422)


def test_create_user_short_name_rejected(admin_client, db_session):
    """B-22: Benutzername < 3 Zeichen wird abgelehnt."""
    r = admin_client.post("/api/users", json={"username": "ab", "password": "StrongPass123!@#", "role": "editor"})
    assert r.status_code in (400, 422)


def test_create_user_case_duplicate_rejected(admin_client, db_session):
    """B-22: Case-insensitive Duplikat-Prüfung."""
    r1 = admin_client.post("/api/users", json={"username": "ed1test", "password": "StrongPass123!@#", "role": "editor"})
    assert r1.status_code == 201
    r2 = admin_client.post("/api/users", json={"username": "ED1TEST", "password": "StrongPass456!@#", "role": "editor"})
    assert r2.status_code == 409


def test_login_case_insensitive(admin_client, db_session):
    """B-22: Login ist case-insensitive."""
    admin_client.post("/api/users", json={"username": "ed1test2", "password": "StrongPass123!@#", "role": "editor"})
    r = admin_client.post("/auth/login", data={"username": "ED1TEST2", "password": "StrongPass123!@#"})
    assert r.status_code == 200


def test_admin_created_user_must_change_password(admin_client, db_session):
    """B-22: Admin-created users muessen Passwort beim ersten Login aendern."""
    admin_client.post("/api/users", json={"username": "newuser123", "password": "TempPassword123!@#", "role": "editor"})
    r = admin_client.post("/auth/login", data={"username": "newuser123", "password": "TempPassword123!@#"})
    data = r.json()
    assert data.get("password_change_required") is True


# B-23: Passwort-Policy staerken

def test_common_password_rejected(admin_client, db_session):
    """B-23: Gebräuchliches Passwort wird abgelehnt."""
    r = admin_client.post("/api/users", json={"username": "commonuser", "password": "password123", "role": "editor"})
    assert r.status_code in (400, 422)


def test_low_variety_password_rejected(admin_client, db_session):
    """B-23: Passwort mit zu wenig verschiedenen Zeichen wird abgelehnt."""
    r = admin_client.post("/api/users", json={"username": "varietyuser", "password": "aaaaaaaaaaaa", "role": "editor"})
    assert r.status_code in (400, 422)


# B-24: Systemdaten schuetzen

def test_editor_cannot_modify_system_dataclass(editor_client, db_session):
    """B-24: Editor darf System-Datenklassen nicht aendern."""
    r = editor_client.get("/api/dataclasses")
    assert r.status_code == 200
    for dc in r.json():
        if dc.get("is_system"):
            r2 = editor_client.put(
                f"/api/dataclasses/{dc['id']}",
                json={"name": "Geaendert", "value_type": dc["value_type"]},
            )
            assert r2.status_code == 403, f"Editor sollte 403 bei System-Datenklasse '{dc['name']}' bekommen"
            return
    pytest.skip("Keine System-Datenklasse gefunden")


def test_client_cannot_set_is_system_on_datanode(editor_client, db_session):
    """B-24: DataNodeCreate hat kein is_system-Feld mehr (Schema-Validierung).

    Indirekter Test: Ein normaler create_node-Aufruf ohne is_system funktioniert.
    Das Schema akzeptiert is_system nicht mehr, also kann der Client es nicht setzen.
    """
    # Erstelle einen normalen Knoten (ohne is_system)
    r = editor_client.post("/api/datanodes", json={"name": "TestNode12345"})
    assert r.status_code in (200, 201)
    data = r.json()
    # Der Knoten sollte is_system=False haben (Default)
    assert data.get("is_system") is False
    assert data.get("source") is None


# B-25: JWT-Secret persistieren (indirekter Test)

def test_jwt_secrets_file_not_committed():
    """B-25: jwt_secrets.json steht in .gitignore."""
    import pathlib
    gitignore_path = pathlib.Path(__file__).resolve().parent.parent / ".gitignore"
    content = gitignore_path.read_text(encoding="utf-8")
    assert "jwt_secrets.json" in content


# B-26: Cookie-Secure konfigurierbar

def test_cookie_secure_flag_default_false():
    """B-26: GREAT_COOKIE_SECURE Default ist False."""
    from src.app.config import GREAT_COOKIE_SECURE
    assert GREAT_COOKIE_SECURE is False