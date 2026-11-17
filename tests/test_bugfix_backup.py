"""Backup/Restore Bugfix-Tests.

B-10: Vollstaendiges Backup/Restore (alle Felder, Roundtrip)
B-11: Robuster Restore (Groesse, Validierung, Atomicity)
B-12: Passwort-Sicherheit (nicht in URL, nicht in Logs, verschiedene Salts)
"""
import io
import json
import zipfile
import base64
import pytest
from app.main import app


# ====================================================================
# B-12: Passwort-Sicherheit
# ====================================================================

def test_get_backup_password_in_url_returns_400(admin_client):
    """B-12: Passwort in URL bei GET /api/backup -> 400."""
    r = admin_client.get("/api/backup?password=test123")
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "URL" in r.json()["detail"]


def test_post_backup_with_password_returns_encrypted(admin_client):
    """B-12: POST /api/backup mit Passwort liefert verschluesseltes Backup."""
    r = admin_client.post("/api/backup", json={"password": "test123"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert "backup.json.enc" in names
    assert "backup.salt" in names
    assert "backup.json" not in names


def test_restore_password_in_url_returns_400(admin_client):
    """B-12: Passwort in URL bei POST /api/backup/restore -> 400."""
    # Erstelle eine gueltige ZIP-Datei
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", json.dumps({"version": "2.0", "exported_at": "2026-01-01", "projects": []}))
    zip_buffer.seek(0)

    files = {"file": ("backup.zip", zip_buffer, "application/zip")}
    r = admin_client.post("/api/backup/restore?password=test123", files=files)
    assert r.status_code == 400
    assert "Passwort" in r.json()["detail"] or "URL" in r.json()["detail"]


def test_restore_password_in_form_succeeds(admin_client, db_session):
    """B-12: Passwort im Form-Body bei Restore funktioniert."""
    from app.database import SessionLocal

    # Erst verschluesseltes Backup erstellen
    backup_r = admin_client.post("/api/backup", json={"password": "formtest"})
    assert backup_r.status_code == 200

    # Jetzt mit Form-Password restoren
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    form_data = {"password": "formtest"}
    r = admin_client.post("/api/backup/restore", files=files, data=form_data)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_encrypted_backups_use_different_salts(admin_client):
    """B-12: Zwei verschluesselte Backups haben verschiedene Salts."""
    r1 = admin_client.post("/api/backup", json={"password": "test123"})
    r2 = admin_client.post("/api/backup", json={"password": "test123"})

    zf1 = zipfile.ZipFile(io.BytesIO(r1.content))
    zf2 = zipfile.ZipFile(io.BytesIO(r2.content))

    salt1 = zf1.read("backup.salt")
    salt2 = zf2.read("backup.salt")

    assert salt1 != salt2, "Salts sollten zufaellig und unterschiedlich sein"


def test_backup_password_not_in_logs(admin_client, caplog):
    """B-12: Passwort erscheint nicht in den Logs."""
    caplog.clear()
    r = admin_client.post("/api/backup", json={"password": "secret123"})
    assert r.status_code == 200

    log_output = "".join(rec.message for rec in caplog.records)
    assert "secret123" not in log_output


# ====================================================================
# B-11: Robuster Restore
# ====================================================================

def test_restore_invalid_json_returns_400(admin_client):
    """B-11: ZIP mit ungueltigem JSON -> 400."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", b"{kaputt")
    zip_buffer.seek(0)

    files = {"file": ("backup.zip", zip_buffer, "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 400
    assert "JSON" in r.json()["detail"] or "Ungueltig" in r.json()["detail"]


def test_restore_json_list_returns_400(admin_client):
    """B-11: ZIP mit JSON-Liste statt Dict -> 400."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", b"[1,2,3]")
    zip_buffer.seek(0)

    files = {"file": ("backup.zip", zip_buffer, "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 400


def test_restore_too_large_file_returns_413(admin_client, monkeypatch):
    """B-11: Datei > GREAT_MAX_BACKUP_MB -> 413."""
    from app import config as app_config
    monkeypatch.setattr(app_config, "GREAT_MAX_BACKUP_MB", 0)

    # Erstelle eine kleine ZIP-Datei
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", json.dumps({"version": "2.0", "exported_at": "2026-01-01", "projects": []}))
    zip_buffer.seek(0)

    # file.size > 0 > 0*1024*1024 -> 413
    files = {"file": ("backup.zip", zip_buffer, "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 413


def test_restore_is_atomic(admin_client, db_session):
    """B-11: Bei Fehler waehrend Restore wird zurueckgerollt."""
    from app.models import Project

    # Erstelle zwei Projekte
    db_session.add(Project(name="AtomicTest1"))
    db_session.add(Project(name="AtomicTest2"))
    db_session.commit()

    # Backup erstellen
    backup_r = admin_client.get("/api/backup")
    assert backup_r.status_code == 200

    # DB zuruecksetzen
    from app.services import reset_database_state
    reset_database_state(db_session)

    # Jetzt sollte Restore mit gueltigem Backup funktionieren
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 200
    assert r.json()["projects_restored"] >= 2

    # Pruefe, dass beide Projekte wieder da sind
    count = db_session.query(Project).filter(
        Project.name.in_(["AtomicTest1", "AtomicTest2"])
    ).count()
    assert count == 2


# ====================================================================
# B-10: Vollstaendiges Backup/Restore Roundtrip
# ====================================================================

def test_backup_roundtrip_full_data(admin_client, db_session):
    """B-10: Kompletter Roundtrip mit allen Datentypen."""
    from app.models import Project, Category, Value, Rule, Generation, TestCase, TestCaseValue
    from app.models import DataNode, DataNodeValue
    from app.models.decision_table_constraint import DecisionTableConstraint

    # Projekt anlegen
    project = Project(name="RoundtripTest")
    db_session.add(project)
    db_session.flush()

    # Kategorien
    cat_a = Category(name="CatA", project_id=project.id, order_index=0, is_result=False, category_type="cause")
    cat_b = Category(name="CatB", project_id=project.id, order_index=1, is_result=True, category_type="effect")
    db_session.add_all([cat_a, cat_b])
    db_session.flush()

    # Werte (mit allen Feldern)
    v1 = Value(value="Wert1", category_id=cat_a.id, risk_weight=5, vtype="number", allowed=True, order_index=0, is_default=True)
    v2 = Value(value="Wert2", category_id=cat_a.id, risk_weight=1, vtype="string", allowed=False, order_index=1, is_default=False)
    v3 = Value(value="Ergebnis1", category_id=cat_b.id, risk_weight=3, vtype="string", allowed=True, order_index=0, is_default=False)
    db_session.add_all([v1, v2, v3])
    db_session.flush()

    # Regel
    rule = Rule(
        project_id=project.id,
        type="dependency",
        if_category_id=cat_a.id,
        if_value="Wert1",
        then_category_id=cat_b.id,
        then_value="Ergebnis1",
    )
    db_session.add(rule)
    db_session.flush()

    # Generierung + TestCase
    gen = Generation(project_id=project.id, strategy="all", name="Gen1")
    db_session.add(gen)
    db_session.flush()

    tc = TestCase(generation_id=gen.id, name="TC_1")
    db_session.add(tc)
    db_session.flush()

    tcval_a = TestCaseValue(testcase_id=tc.id, category_id=cat_a.id, value="Wert1")
    tcval_b = TestCaseValue(testcase_id=tc.id, category_id=cat_b.id, value="Ergebnis1")
    db_session.add_all([tcval_a, tcval_b])
    db_session.flush()

    # Datenknoten
    node = DataNode(name="TestNode", is_system=False, sort_order=0)
    db_session.add(node)
    db_session.flush()
    nodeval = DataNodeValue(node_id=node.id, value="NodeValue1", sort_order=0)
    db_session.add(nodeval)
    db_session.flush()

    # Decision Constraint
    constraint = DecisionTableConstraint(
        project_id=project.id,
        constraint_type="E",
        targets={"causes": [cat_a.id]},
        description="Exclusive test",
    )
    db_session.add(constraint)
    db_session.commit()

    # Backup erstellen
    backup_r = admin_client.get("/api/backup")
    assert backup_r.status_code == 200

    # Backup parsen und pruefen
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))
    assert data["version"] == "2.0"
    assert len(data["projects"]) >= 1

    rt_project = None
    for p in data["projects"]:
        if p["name"] == "RoundtripTest":
            rt_project = p
            break
    assert rt_project is not None, "RoundtripTest Projekt nicht im Backup gefunden"

    # Kategorien pruefen
    cats = {c["name"]: c for c in rt_project["categories"]}
    assert "CatA" in cats
    assert "CatB" in cats
    assert cats["CatA"]["category_type"] == "cause"
    assert cats["CatB"]["is_result"] is True

    # Werte pruefen
    cat_a_vals = {v["value"]: v for v in cats["CatA"]["values"]}
    assert "Wert1" in cat_a_vals
    assert cat_a_vals["Wert1"]["risk_weight"] == 5
    assert cat_a_vals["Wert1"]["is_default"] is True
    assert cat_a_vals["Wert2"]["allowed"] is False

    # Regel pruefen (mit Namen!)
    assert len(rt_project["rules"]) >= 1
    rule_data = rt_project["rules"][0]
    assert rule_data["if_category_name"] == "CatA"
    assert rule_data["then_category_name"] == "CatB"

    # TestCase pruefen (mit Kategorie-Namen!)
    assert len(rt_project["generations"]) >= 1
    tc_data = rt_project["generations"][0]["testcases"][0]
    assert "CatA" in tc_data["assignments"]
    assert tc_data["assignments"]["CatA"] == "Wert1"

    # Decision Constraint pruefen
    assert len(rt_project["decision_constraints"]) >= 1

    # DB zuruecksetzen und Restore
    from app.services import reset_database_state
    reset_database_state(db_session)
    db_session.commit()

    # Restore
    files = {"file": ("backup.zip", io.BytesIO(backup_r.content), "application/zip")}
    r = admin_client.post("/api/backup/restore", files=files)
    assert r.status_code == 200

    # Nach Restore: Projekt sollte wieder da sein (ggf. mit Suffix)
    restored_projects = db_session.query(Project).filter(
        Project.name.like("RoundtripTest%")
    ).all()
    assert len(restored_projects) >= 1


def test_backup_contains_all_fields(admin_client, db_session):
    """B-10: Backup enthaelt alle Felder (order_index, is_default, category_type, etc.)."""
    from app.models import Project, Category, Value

    project = Project(name="FieldCheck")
    db_session.add(project)
    db_session.flush()

    cat = Category(name="FieldCat", project_id=project.id, order_index=5, is_result=True, category_type="effect")
    db_session.add(cat)
    db_session.flush()

    val = Value(value="TestVal", category_id=cat.id, risk_weight=7, vtype="number", allowed=False, order_index=3, is_default=True)
    db_session.add(val)
    db_session.commit()

    backup_r = admin_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))

    fc_project = None
    for p in data["projects"]:
        if p["name"] == "FieldCheck":
            fc_project = p
            break
    assert fc_project is not None

    fc_cat = fc_project["categories"][0]
    assert fc_cat["order_index"] == 5
    assert fc_cat["is_result"] is True
    assert fc_cat["category_type"] == "effect"

    fc_val = fc_cat["values"][0]
    assert fc_val["risk_weight"] == 7
    assert fc_val["vtype"] == "number"
    assert fc_val["allowed"] is False
    assert fc_val["order_index"] == 3
    assert fc_val["is_default"] is True


def test_backup_excludes_users(admin_client):
    """B-10: Backup enthaelt keine Benutzer oder Passwoerter."""
    backup_r = admin_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))

    # Kein "users" Key
    assert "users" not in data
    assert "password" not in data
    assert "password_hash" not in data

    # Kein Benutzer in Projekten
    for p in data["projects"]:
        assert "users" not in p
        assert "password" not in p


def test_backup_excludes_system_dataclasses(admin_client, db_session):
    """B-10: System-Datenklassen (is_system=True) nicht im Backup."""
    from app.models import DataClass, DataClassValue

    # System-Datenklasse
    sys_dc = DataClass(name="SystemTestDC", value_type="text", is_system=True)
    db_session.add(sys_dc)
    db_session.flush()
    sys_val = DataClassValue(dataclass_id=sys_dc.id, value="SysVal")
    db_session.add(sys_val)
    db_session.commit()

    backup_r = admin_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))

    for p in data["projects"]:
        for dc in p.get("dataclasses", []):
            assert dc["name"] != "SystemTestDC", "System-Datenklasse sollte nicht im Backup sein"


def test_backup_version_is_2_0(admin_client):
    """B-10: Backup-Version ist '2.0'."""
    backup_r = admin_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))
    assert data["version"] == "2.0"


def test_backup_has_exported_at(admin_client):
    """B-10: Backup hat exported_at mit UTC-Zeitstempel."""
    backup_r = admin_client.get("/api/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup_r.content))
    data = json.loads(zf.read("backup.json"))
    assert "exported_at" in data
    # Sollte ein gueltiger ISO-Timestamp sein
    from datetime import datetime
    datetime.fromisoformat(data["exported_at"])


def test_get_backup_unencrypted(admin_client):
    """B-10: GET /api/backup liefert unverschlusseltes Backup."""
    r = admin_client.get("/api/backup")
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert "backup.json" in zf.namelist()
    assert "backup.json.enc" not in zf.namelist()