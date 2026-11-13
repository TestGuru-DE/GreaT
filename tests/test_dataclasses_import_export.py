"""REQ-4013: Eigene Datenklassen Import/Export JSON."""
import json
import io
import time
from fastapi.testclient import TestClient
from app import models


def _unique_suffix():
    """Erzeugt einen eindeutigen Suffix fuer Test-Namen."""
    return f"{int(time.time() * 1000)}"


def test_export_user_dataclasses_empty(auth_client):
    """Export von Datenklassen – leere Liste."""
    r = auth_client.get("/api/dataclasses/export-user")
    assert r.status_code == 200
    data = r.json()
    assert "dataclasses" in data
    assert "version" in data
    assert data["version"] == "1.0"
    assert isinstance(data["dataclasses"], list)


def test_export_includes_only_user_dataclasses(auth_client, db_session):
    """Export soll nur User-Datenklassen (is_system=False) enthalten."""
    suffix = _unique_suffix()
    # System-Datenklasse hinzufügen (soll NICHT exportiert werden)
    system_dc = models.DataClass(name=f"SystemTest{suffix}", is_system=True, value_type="text")
    db_session.add(system_dc)
    db_session.flush()

    # User-Datenklasse
    user_dc = models.DataClass(name=f"UserClass{suffix}", is_system=False, value_type="number")
    db_session.add(user_dc)
    db_session.flush()

    # Werte hinzufügen
    db_session.add(models.DataClassValue(dataclass_id=user_dc.id, value="100"))
    db_session.commit()

    r = auth_client.get("/api/dataclasses/export-user")
    data = r.json()
    names = [d["name"] for d in data["dataclasses"]]

    assert f"UserClass{suffix}" in names
    assert f"SystemTest{suffix}" not in names


def test_import_user_dataclasses_new_class(auth_client, db_session):
    """Import von neuer Datenklasse."""
    suffix = _unique_suffix()
    payload = {
        "version": "1.0",
        "dataclasses": [
            {"name": f"TestKlasse{suffix}", "value_type": "text", "description": "Test", "values": ["A", "B", "C"]}
        ]
    }
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("test.json", f, "application/json")}
    )

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["imported"] == 1

    # Verifizieren dass die Klasse wirklich importiert wurde
    dc = db_session.query(models.DataClass).filter(
        models.DataClass.name == f"TestKlasse{suffix}",
        models.DataClass.is_system == False
    ).first()
    assert dc is not None
    assert dc.value_type == "text"

    values = db_session.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()
    assert len(values) == 3
    value_strs = {v.value for v in values}
    assert value_strs == {"A", "B", "C"}


def test_import_invalid_json(auth_client):
    """Import mit ungültiger JSON-Datei."""
    f = io.BytesIO(b"not json")
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("bad.json", f, "application/json")}
    )
    assert r.status_code == 400
    assert "Ungültige JSON-Datei" in r.json()["detail"]


def test_import_empty_dataclasses(auth_client):
    """Import mit leerer Datenklassen-Liste."""
    payload = {"version": "1.0", "dataclasses": []}
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("empty.json", f, "application/json")}
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 0


def test_import_merge_strategy(auth_client, db_session):
    """Import mit Merge-Strategie: bestehende Klasse nicht überschrieben, Werte ergänzt."""
    suffix = _unique_suffix()
    # Cleanup first
    db_session.query(models.DataClass).filter(models.DataClass.name == f"ExistingClass{suffix}").delete()
    db_session.commit()

    # Bestehende Datenklasse mit einem Wert
    dc = models.DataClass(name=f"ExistingClass{suffix}", is_system=False, value_type="text")
    db_session.add(dc)
    db_session.flush()
    db_session.add(models.DataClassValue(dataclass_id=dc.id, value="ExistingValue"))
    db_session.commit()

    # Import mit gleichem Namen aber neuen Werten
    payload = {
        "version": "1.0",
        "dataclasses": [
            {"name": f"ExistingClass{suffix}", "value_type": "text", "description": "Updated", "values": ["ExistingValue", "NewValue", "AnotherValue"]}
        ]
    }
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("merge.json", f, "application/json")}
    )

    assert r.status_code == 200
    assert r.json()["imported"] == 1

    # Verifizieren: nur neue Werte hinzugefügt
    db_session.refresh(dc)
    values = db_session.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()
    value_strs = {v.value for v in values}
    assert value_strs == {"ExistingValue", "NewValue", "AnotherValue"}


def test_export_round_trip(auth_client, db_session):
    """Round-Trip Test: Import → Export → Verifizierung."""
    suffix = _unique_suffix()
    # Cleanup old data
    db_session.query(models.DataClass).filter(models.DataClass.name == f"RoundTrip{suffix}").delete()
    db_session.commit()

    # Import
    payload = {
        "version": "1.0",
        "dataclasses": [
            {"name": f"RoundTrip{suffix}", "value_type": "email", "description": "RT Test", "values": ["test@example.com", "admin@example.com"]}
        ]
    }
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("rt.json", f, "application/json")}
    )
    assert r.status_code == 200

    # Export und Verifizierung
    r2 = auth_client.get("/api/dataclasses/export-user")
    data = r2.json()

    found = False
    for dc_export in data["dataclasses"]:
        if dc_export["name"] == f"RoundTrip{suffix}":
            found = True
            assert dc_export["value_type"] == "email"
            assert set(dc_export["values"]) == {"test@example.com", "admin@example.com"}
            break

    assert found, f"RoundTrip{suffix} Klasse nicht in Export gefunden"


def test_import_legacy_format(auth_client, db_session):
    """Import von altem Format (direkt {name: [values]})."""
    suffix = _unique_suffix()
    payload = {
        f"LegacyClass{suffix}": ["Value1", "Value2", "Value3"]
    }
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("legacy.json", f, "application/json")}
    )

    assert r.status_code == 200
    assert r.json()["imported"] == 1

    # Verifizieren
    dc = db_session.query(models.DataClass).filter(
        models.DataClass.name == f"LegacyClass{suffix}",
        models.DataClass.is_system == False
    ).first()
    assert dc is not None

    values = db_session.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()
    assert len(values) == 3


def test_import_skips_duplicates_in_values(auth_client, db_session):
    """Import soll doppelte Werte überspringen."""
    suffix = _unique_suffix()
    payload = {
        "version": "1.0",
        "dataclasses": [
            {"name": f"DuplicateTest{suffix}", "value_type": "text", "description": "", "values": ["A", "A", "B", "B", "C"]}
        ]
    }
    f = io.BytesIO(json.dumps(payload).encode())
    r = auth_client.post(
        "/api/dataclasses/import-user",
        files={"file": ("dup.json", f, "application/json")}
    )

    assert r.status_code == 200

    dc = db_session.query(models.DataClass).filter(models.DataClass.name == f"DuplicateTest{suffix}").first()
    values = db_session.query(models.DataClassValue).filter(models.DataClassValue.dataclass_id == dc.id).all()

    value_strs = [v.value for v in values]
    assert "A" in value_strs
    assert "B" in value_strs
    assert "C" in value_strs


def test_export_has_content_disposition(auth_client):
    """Export soll Content-Disposition Header für Download haben."""
    r = auth_client.get("/api/dataclasses/export-user")
    assert r.status_code == 200
    assert "Content-Disposition" in r.headers
    assert "attachment" in r.headers["Content-Disposition"]
    assert "my-dataclasses.json" in r.headers["Content-Disposition"]