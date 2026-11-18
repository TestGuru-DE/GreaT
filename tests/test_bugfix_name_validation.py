"""Tests: Eindeutige Namen und Eingabevalidierung.

BUG B-04: Doppelte Kategorienamen werden bei Generierung verschmolzen
BUG B-15: Keine Validierung bei Projekt/Kategorie/Wert
BUG B-16: risk_weight wird beim Anlegen nicht geprueft
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app, _migrate_db
from app.database import SessionLocal, engine, Base
from app.models.auth import User
from app.auth_utils import create_access_token
from app.bootstrap import ensure_first_admin
from app.system_dataclasses import seed_system_dataclasses


def _add_user(username, role, password):
    db = SessionLocal()
    try:
        user = User(username=username, role=role, is_active=True)
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _client_for(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        token = create_access_token(user.id, user.username, user.role)
    finally:
        db.close()
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("access_token", token)
    return client


@pytest.fixture(autouse=True)
def _nv_db():
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# B-15: Projektname-Validierung
# ---------------------------------------------------------------------------

def test_project_name_whitespace_only_rejected():
    """Projektname nur Leerzeichen -> 422."""
    admin_id = _add_user("test_pw_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    r = c.post("/api/projects", json={"name": "   "})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"


def test_project_name_case_insensitive_unique():
    """Projektname 'Edge' neben 'edge' -> 409."""
    admin_id = _add_user("test_ci_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    c.post("/api/projects", json={"name": "Edge"})
    r = c.post("/api/projects", json={"name": "edge"})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    r2 = c.post("/api/projects", json={"name": "EDGE"})
    assert r2.status_code == 409, f"Expected 409, got {r2.status_code}: {r2.text}"


# ---------------------------------------------------------------------------
# B-15: Kategoriename-Validierung
# ---------------------------------------------------------------------------

def test_category_name_empty_rejected():
    """Kategoriename leer -> 422."""
    admin_id = _add_user("test_cn_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "CatNameProj"}).json()["id"]
    r = c.post(f"/api/projects/{pid}/categories", json={"name": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"


def test_category_name_whitespace_rejected():
    """Kategoriename nur Leerzeichen -> 422."""
    admin_id = _add_user("test_cn2_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "CatNameProj2"}).json()["id"]
    r = c.post(f"/api/projects/{pid}/categories", json={"name": "   "})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"


def test_duplicate_category_name_rejected():
    """Doppelte Kategoriename -> 409, auch mit anderer Schreibweise."""
    admin_id = _add_user("test_dc_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "DupCatProj"}).json()["id"]
    c.post(f"/api/projects/{pid}/categories", json={"name": "Farbe"})
    r = c.post(f"/api/projects/{pid}/categories", json={"name": "farbe"})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    r2 = c.post(f"/api/projects/{pid}/categories", json={"name": " Farbe "})
    assert r2.status_code == 409, f"Expected 409, got {r2.status_code}: {r2.text}"


# ---------------------------------------------------------------------------
# B-04: Generierung lehnt doppelte Kategorienamen ab
# ---------------------------------------------------------------------------

def test_generate_rejects_existing_duplicate_categories():
    """Duplikat direkt per DB einfuegen, generate liefert 409."""
    admin_id = _add_user("test_gen_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "GenDupProj"}).json()["id"]
    # Zwei Kategorien mit gleichem Namen direkt in DB einfuegen
    from app.models import Project, Category, Value
    db = SessionLocal()
    try:
        db.add(Category(project_id=pid, name="Farbe", order_index=0))
        db.add(Category(project_id=pid, name="Farbe", order_index=1))
        db.flush()
        c1 = db.query(Category).filter(Category.project_id == pid, Category.order_index == 0).first()
        c2 = db.query(Category).filter(Category.project_id == pid, Category.order_index == 1).first()
        db.add(Value(category_id=c1.id, value="rot"))
        db.add(Value(category_id=c2.id, value="gruen"))
        db.commit()
    finally:
        db.close()
    r = c.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    assert "Doppelte" in r.text or "doppelte" in r.text


# ---------------------------------------------------------------------------
# B-15: Wert-Validierung
# ---------------------------------------------------------------------------

def test_value_empty_rejected():
    """Wert leer -> 422."""
    admin_id = _add_user("test_v_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "ValProj"}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie"}).json()["id"]
    r = c.post(f"/api/categories/{cid}/values", json={"value": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"


def test_value_whitespace_only_allowed():
    """Wert nur aus Leerzeichen ist erlaubt (gewollte Testdaten)."""
    admin_id = _add_user("test_vw_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "ValWProj"}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie"}).json()["id"]
    r = c.post(f"/api/categories/{cid}/values", json={"value": "   "})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_duplicate_value_in_category_rejected():
    """Doppelte Wert in Kategorie -> 409."""
    admin_id = _add_user("test_dv_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "DupValProj"}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie"}).json()["id"]
    c.post(f"/api/categories/{cid}/values", json={"value": "rot"})
    r = c.post(f"/api/categories/{cid}/values", json={"value": "rot"})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"


def test_value_case_variants_allowed():
    """'A' und 'a' duerfen beide existieren (exakter Vergleich)."""
    admin_id = _add_user("test_vc_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "ValCaseProj"}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie"}).json()["id"]
    r1 = c.post(f"/api/categories/{cid}/values", json={"value": "A"})
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}: {r1.text}"
    r2 = c.post(f"/api/categories/{cid}/values", json={"value": "a"})
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"


# ---------------------------------------------------------------------------
# B-16: risk_weight-Validierung beim Anlegen
# ---------------------------------------------------------------------------

def test_risk_weight_on_create_validated():
    """risk_weight 0/-99/11 -> 422, 5 -> ok."""
    admin_id = _add_user("test_rw_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "RWProj"}).json()["id"]
    cid = c.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie"}).json()["id"]

    r = c.post(f"/api/categories/{cid}/values", json={"value": "v0", "risk_weight": 0})
    assert r.status_code == 422, f"Expected 422 for 0, got {r.status_code}: {r.text}"

    r = c.post(f"/api/categories/{cid}/values", json={"value": "vneg", "risk_weight": -99})
    assert r.status_code == 422, f"Expected 422 for -99, got {r.status_code}: {r.text}"

    r = c.post(f"/api/categories/{cid}/values", json={"value": "v11", "risk_weight": 11})
    assert r.status_code == 422, f"Expected 422 for 11, got {r.status_code}: {r.text}"

    r = c.post(f"/api/categories/{cid}/values", json={"value": "v5", "risk_weight": 5})
    assert r.status_code == 200, f"Expected 200 for 5, got {r.status_code}: {r.text}"


# ---------------------------------------------------------------------------
# Rename-Duplikate
# ---------------------------------------------------------------------------

def test_rename_category_to_existing_name_rejected():
    """Kategorie umbenennen zu bestehendem Namen -> 409."""
    admin_id = _add_user("test_rc_admin", "admin", "Testpasswort-123!")
    c = _client_for(admin_id)
    pid = c.post("/api/projects", json={"name": "RenameCatProj"}).json()["id"]
    c1 = c.post(f"/api/projects/{pid}/categories", json={"name": "Alpha"}).json()["id"]
    c2 = c.post(f"/api/projects/{pid}/categories", json={"name": "Beta"}).json()["id"]
    r = c.patch(f"/api/categories/{c2}/rename", json={"name": "Alpha"})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    # casefold: "alpha" sollte auch abgelehnt werden
    r2 = c.patch(f"/api/categories/{c2}/rename", json={"name": "alpha"})
    assert r2.status_code == 409, f"Expected 409 for 'alpha', got {r2.status_code}: {r2.text}"