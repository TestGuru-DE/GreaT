"""
tests/test_phase3_sprint3.py – TDD RED-Phase für Phase 3, Sprint 3
REQ-3007: Wert-Eigenschaften (PATCH /api/values/{vid}/properties)
REQ-3008: Default-Wert-Markierung (PATCH /api/values/{vid}/set-default)
REQ-3010: DataClassesPage – System vs. User getrennt (API-seitig bereits korrekt)
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_project_with_category():
    """Hilfsfunktion: Projekt + Kategorie + 3 Werte."""
    pid = client.post("/api/projects", json={"name": f"s3-test-{uuid.uuid4().hex[:8]}"}).json()["id"]
    cid = client.post(f"/api/projects/{pid}/categories", json={"name": "Browser"}).json()["id"]
    v1 = client.post(f"/api/categories/{cid}/values", json={"value": "Chrome"}).json()["id"]
    v2 = client.post(f"/api/categories/{cid}/values", json={"value": "Firefox"}).json()["id"]
    v3 = client.post(f"/api/categories/{cid}/values", json={"value": "Safari"}).json()["id"]
    return pid, cid, v1, v2, v3


# ---------------------------------------------------------------------------
# REQ-3007: ValueRead enthält alle Eigenschaften
# ---------------------------------------------------------------------------

class TestValueRead:
    def test_value_read_has_all_fields(self):
        """GET /categories/{cid}/values liefert risk_weight, vtype, allowed, is_default."""
        _, cid, v1, _, _ = make_project_with_category()
        vals = client.get(f"/api/categories/{cid}/values").json()
        assert len(vals) == 3
        v = vals[0]
        assert "risk_weight" in v
        assert "vtype" in v
        assert "allowed" in v
        assert "is_default" in v


# ---------------------------------------------------------------------------
# REQ-3007: PATCH /api/values/{vid}/properties
# ---------------------------------------------------------------------------

class TestValueProperties:
    def test_patch_risk_weight(self):
        """PATCH properties: risk_weight ändern."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"risk_weight": 7})
        assert r.status_code == 200, r.text
        assert r.json()["risk_weight"] == 7

    def test_patch_vtype(self):
        """PATCH properties: vtype ändern."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"vtype": "number"})
        assert r.status_code == 200, r.text
        assert r.json()["vtype"] == "number"

    def test_patch_allowed(self):
        """PATCH properties: allowed (Fehlerwert) setzen."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"allowed": False})
        assert r.status_code == 200, r.text
        assert r.json()["allowed"] is False

    def test_patch_multiple_fields(self):
        """PATCH properties: mehrere Felder gleichzeitig."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"risk_weight": 9, "vtype": "date", "allowed": False})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["risk_weight"] == 9
        assert body["vtype"] == "date"
        assert body["allowed"] is False

    def test_patch_invalid_risk_weight(self):
        """Ungültiger risk_weight (außerhalb 1-10) → 422."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"risk_weight": 99})
        assert r.status_code == 422

    def test_patch_invalid_vtype(self):
        """Ungültiger vtype → 422."""
        _, _, v1, _, _ = make_project_with_category()
        r = client.patch(f"/api/values/{v1}/properties", json={"vtype": "ungueltig"})
        assert r.status_code == 422

    def test_patch_not_found(self):
        """Wert nicht gefunden → 404."""
        r = client.patch("/api/values/99999/properties", json={"risk_weight": 5})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# REQ-3008: Default-Wert-Markierung
# ---------------------------------------------------------------------------

class TestDefaultValue:
    def test_first_value_is_default(self):
        """Erster Wert in Kategorie ist automatisch Default."""
        _, cid, v1, v2, v3 = make_project_with_category()
        vals = client.get(f"/api/categories/{cid}/values").json()
        # Der erste Wert soll is_default=True haben
        first = next((v for v in vals if v["id"] == v1), None)
        assert first is not None
        assert first["is_default"] is True

    def test_other_values_not_default(self):
        """Nur der Default-Wert hat is_default=True."""
        _, cid, v1, v2, v3 = make_project_with_category()
        vals = client.get(f"/api/categories/{cid}/values").json()
        defaults = [v for v in vals if v["is_default"]]
        assert len(defaults) == 1

    def test_set_default(self):
        """PATCH /api/values/{vid}/set-default setzt neuen Default."""
        _, cid, v1, v2, v3 = make_project_with_category()
        r = client.patch(f"/api/values/{v2}/set-default")
        assert r.status_code == 200, r.text
        vals = client.get(f"/api/categories/{cid}/values").json()
        for v in vals:
            if v["id"] == v2:
                assert v["is_default"] is True
            else:
                assert v["is_default"] is False

    def test_set_default_not_found(self):
        """Wert nicht gefunden → 404."""
        r = client.patch("/api/values/99999/set-default")
        assert r.status_code == 404

    def test_set_default_clears_previous(self):
        """Set-default räumt vorherigen Default auf."""
        _, cid, v1, v2, v3 = make_project_with_category()
        # v2 zum Default
        client.patch(f"/api/values/{v2}/set-default")
        # v3 zum Default
        client.patch(f"/api/values/{v3}/set-default")
        vals = client.get(f"/api/categories/{cid}/values").json()
        defaults = [v for v in vals if v["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["id"] == v3
