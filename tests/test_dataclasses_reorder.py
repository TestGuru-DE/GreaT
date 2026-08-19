"""REQ-4014: Werte-Reihenfolge per Drag & Drop (sort_order)."""
import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.database import SessionLocal
from src.app import models


@pytest.fixture
def client():
    """Test-Client mit DB-Session."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Datenbank vor jedem Test zurücksetzen."""
    db = SessionLocal()
    # Clean up dataclasses table
    db.query(models.DataClassValue).delete()
    db.query(models.DataClass).delete()
    db.commit()
    yield
    db.close()


def test_list_values_ordered_by_sort_order(client):
    """REQ-4014: GET /dataclasses/{id}/values sortiert nach sort_order."""
    # Erstelle eine Datenklasse
    r = client.post("/api/dataclasses", json={"name": "OrderTest", "value_type": "text"})
    dc_id = r.json()["id"]
    
    # Füge 3 Werte hinzu
    v1 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "A"}).json()["id"]
    v2 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "B"}).json()["id"]
    v3 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "C"}).json()["id"]
    
    # Reorder: C, A, B
    r = client.put(f"/api/dataclasses/{dc_id}/values/reorder", json={"value_ids": [v3, v1, v2]})
    assert r.status_code == 200
    
    # Prüfe Reihenfolge
    r = client.get(f"/api/dataclasses/{dc_id}/values")
    values = r.json()
    assert len(values) == 3
    assert values[0]["id"] == v3
    assert values[1]["id"] == v1
    assert values[2]["id"] == v2


def test_reorder_values_success(client):
    """REQ-4014: PUT /api/dataclasses/{id}/values/reorder speichert neue Reihenfolge."""
    # Erstelle eine Datenklasse mit 3 Werten
    r = client.post("/api/dataclasses", json={"name": "ReorderTest", "value_type": "text"})
    dc_id = r.json()["id"]
    
    v1 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "A"}).json()["id"]
    v2 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "B"}).json()["id"]
    v3 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "C"}).json()["id"]
    
    # Reorder
    r = client.put(f"/api/dataclasses/{dc_id}/values/reorder", json={"value_ids": [v3, v1, v2]})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_reorder_values_invalid_dataclass(client):
    """REQ-4014: Reorder bei ungültiger Datenklasse."""
    r = client.put("/api/dataclasses/99999/values/reorder", json={"value_ids": [1, 2, 3]})
    assert r.status_code == 404


def test_reorder_values_invalid_ids(client):
    """REQ-4014: Reorder ignoriert IDs die nicht zur Datenklasse gehören."""
    r = client.post("/api/dataclasses", json={"name": "ReorderTest2", "value_type": "text"})
    dc_id = r.json()["id"]
    
    v1 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "A"}).json()["id"]
    
    # Reorder mit nicht-existent ID
    r = client.put(f"/api/dataclasses/{dc_id}/values/reorder", json={"value_ids": [v1, 99999]})
    assert r.status_code == 200
    
    # Prüfe dass v1 trotzdem die erste Position hat
    values = client.get(f"/api/dataclasses/{dc_id}/values").json()
    assert values[0]["id"] == v1


def test_sort_order_persists_after_reload(client):
    """REQ-4014: sort_order bleibt nach Reload erhalten."""
    r = client.post("/api/dataclasses", json={"name": "PersistTest", "value_type": "text"})
    dc_id = r.json()["id"]
    
    v1 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "First"}).json()["id"]
    v2 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "Second"}).json()["id"]
    v3 = client.post(f"/api/dataclasses/{dc_id}/values", json={"value": "Third"}).json()["id"]
    
    # Reorder: Third, First, Second
    client.put(f"/api/dataclasses/{dc_id}/values/reorder", json={"value_ids": [v3, v1, v2]})
    
    # Erste Anfrage
    values1 = client.get(f"/api/dataclasses/{dc_id}/values").json()
    
    # Zweite Anfrage (simulating Reload)
    values2 = client.get(f"/api/dataclasses/{dc_id}/values").json()
    
    # Beide sollten die gleiche Reihenfolge haben
    assert [v["id"] for v in values1] == [v["id"] for v in values2]
    assert [v["id"] for v in values1] == [v3, v1, v2]
