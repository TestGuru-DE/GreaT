# tests/test_dataclasses.py
# REQ-2003: Datenklassen – Wiederverwendbare Aequivalenzklassen-Bibliothek
# TDD: Tests VOR Implementierung (RED-Phase)
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)


def _uid() -> str:
    return uuid.uuid4().hex[:6]


# ---------------------------------------------------------------------------
# Typvalidierung (Unit-Tests)
# ---------------------------------------------------------------------------

class TestDataclassValidator:
    """REQ-2003: Typvalidierung fuer Datenklassen-Werte."""

    def test_text_gueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("Hallo", "text")
        assert ok is True

    def test_text_leer_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("", "text")
        assert ok is False
        assert msg != ""

    def test_number_gueltig_ganzzahl(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("42", "number")
        assert ok is True

    def test_number_gueltig_dezimal(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("-3.14", "number")
        assert ok is True

    def test_number_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("abc", "number")
        assert ok is False

    def test_date_gueltig_iso(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("2024-01-15", "date")
        assert ok is True

    def test_date_gueltig_deutsch(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("15.01.2024", "date")
        assert ok is True

    def test_date_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("kein-datum", "date")
        assert ok is False

    def test_time_gueltig_hhmm(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("08:30", "time")
        assert ok is True

    def test_time_gueltig_hhmmss(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("23:59:59", "time")
        assert ok is True

    def test_time_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("25:00", "time")
        assert ok is False

    def test_boolean_gueltig(self):
        from src.app.dataclass_validator import validate_value
        for v in ("true", "false", "1", "0", "ja", "nein"):
            ok, _ = validate_value(v, "boolean")
            assert ok is True, f"{v} sollte gueltig sein"

    def test_boolean_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("vielleicht", "boolean")
        assert ok is False

    def test_email_gueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, _ = validate_value("test@example.com", "email")
        assert ok is True

    def test_email_ungueltig(self):
        from src.app.dataclass_validator import validate_value
        ok, msg = validate_value("kein-at-zeichen", "email")
        assert ok is False

    def test_freetext_immer_gueltig(self):
        from src.app.dataclass_validator import validate_value
        for v in ("", "abc", "123", "!@#"):
            ok, _ = validate_value(v, "freetext")
            assert ok is True


# ---------------------------------------------------------------------------
# API-Tests
# ---------------------------------------------------------------------------

class TestDataclassAPI:
    """REQ-2003: CRUD-Endpunkte fuer Datenklassen."""

    def test_list_dataclasses_gibt_200(self):
        r = client.get("/api/dataclasses")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_dataclass(self):
        r = client.post("/api/dataclasses", json={"name": f"DC-{_uid()}", "value_type": "text"})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["value_type"] == "text"

    def test_create_dataclass_mit_beschreibung(self):
        r = client.post("/api/dataclasses", json={"name": f"DC-{_uid()}", "value_type": "number", "description": "Zahlen"})
        assert r.status_code == 200
        assert r.json()["description"] == "Zahlen"

    def test_create_dataclass_doppelter_name_gibt_409(self):
        name = f"DC-dup-{_uid()}"
        client.post("/api/dataclasses", json={"name": name, "value_type": "text"})
        r = client.post("/api/dataclasses", json={"name": name, "value_type": "text"})
        assert r.status_code == 409

    def test_create_dataclass_unbekannter_typ_gibt_422(self):
        r = client.post("/api/dataclasses", json={"name": f"DC-{_uid()}", "value_type": "unbekannt"})
        assert r.status_code == 422

    def test_delete_dataclass(self):
        dc = client.post("/api/dataclasses", json={"name": f"DC-del-{_uid()}", "value_type": "text"}).json()
        r = client.delete(f"/api/dataclasses/{dc['id']}")
        assert r.status_code == 200
        remaining = [d["id"] for d in client.get("/api/dataclasses").json()]
        assert dc["id"] not in remaining

    def test_add_value_gueltig(self):
        dc = client.post("/api/dataclasses", json={"name": f"DC-val-{_uid()}", "value_type": "number"}).json()
        r = client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "42"})
        assert r.status_code == 200
        assert r.json()["value"] == "42"

    def test_add_value_ungueltig_typ_gibt_422(self):
        dc = client.post("/api/dataclasses", json={"name": f"DC-inv-{_uid()}", "value_type": "number"}).json()
        r = client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "kein_wert"})
        assert r.status_code == 422

    def test_list_values(self):
        dc = client.post("/api/dataclasses", json={"name": f"DC-lv-{_uid()}", "value_type": "text"}).json()
        client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "Alpha"})
        client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "Beta"})
        vals = client.get(f"/api/dataclasses/{dc['id']}/values").json()
        assert len(vals) == 2
        assert any(v["value"] == "Alpha" for v in vals)

    def test_delete_value(self):
        dc = client.post("/api/dataclasses", json={"name": f"DC-dv-{_uid()}", "value_type": "text"}).json()
        v = client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "ZuLoeschen"}).json()
        r = client.delete(f"/api/dataclasses/values/{v['id']}")
        assert r.status_code == 200
        vals = client.get(f"/api/dataclasses/{dc['id']}/values").json()
        assert not any(x["id"] == v["id"] for x in vals)

    def test_apply_dataclass_zu_kategorie(self):
        # Projekt + Kategorie anlegen
        pid = client.post("/api/projects", json={"name": f"DC-Proj-{_uid()}"}).json()["id"]
        cid = client.post(f"/api/projects/{pid}/categories", json={"name": "Farbe", "order_index": 0}).json()["id"]
        # Datenklasse mit Werten
        dc = client.post("/api/dataclasses", json={"name": f"DC-apply-{_uid()}", "value_type": "text"}).json()
        client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "Rot"})
        client.post(f"/api/dataclasses/{dc['id']}/values", json={"value": "Blau"})
        # Anwenden
        r = client.post(f"/api/categories/{cid}/apply-dataclass", json={"dataclass_id": dc["id"]})
        assert r.status_code == 200
        assert r.json()["added"] == 2
        # Werte in Kategorie pruefen
        vals = client.get(f"/api/categories/{cid}/values").json()
        val_strings = [v["value"] for v in vals]
        assert "Rot" in val_strings
        assert "Blau" in val_strings