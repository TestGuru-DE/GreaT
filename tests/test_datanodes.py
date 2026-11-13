"""
REQ-4018: Hierarchische Datenklassen.
Tests für DataNode und DataNodeValue Modelle sowie API-Endpunkte.
"""
import pytest


def test_create_root_node(auth_client):
    """REQ-4018: Wurzelknoten (Kategorie) erstellen."""
    r = auth_client.post("/api/datanodes", json={"name": "TestKategorie"})
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "TestKategorie"
    assert d["parent_id"] is None
    assert d["is_system"] is False
    assert d["children"] == []
    assert d["values"] == []


def test_create_child_node(auth_client):
    """REQ-4018: Unterknoten (Gruppe) erstellen."""
    root = auth_client.post("/api/datanodes", json={"name": "Root"}).json()
    child = auth_client.post("/api/datanodes", json={"name": "Gruppe1", "parent_id": root["id"]}).json()
    assert child["parent_id"] == root["id"]
    assert child["name"] == "Gruppe1"


def test_get_tree_structure(auth_client):
    """REQ-4018: Baumstruktur abrufen."""
    root = auth_client.post("/api/datanodes", json={"name": "A"}).json()
    child = auth_client.post("/api/datanodes", json={"name": "B", "parent_id": root["id"]}).json()
    auth_client.post(f"/api/datanodes/{child['id']}/values", json={"value": "Wert1"})
    
    r = auth_client.get("/api/datanodes/tree")
    assert r.status_code == 200
    tree = r.json()
    # A muss in Baum sein
    a = next((n for n in tree if n["name"] == "A"), None)
    assert a is not None
    assert len(a["children"]) >= 1
    # B muss Kind von A sein
    b = a["children"][0] if a["children"] else None
    assert b is not None
    assert b["name"] == "B"
    assert len(b["values"]) >= 1


def test_mixed_node_values_and_children(auth_client):
    """REQ-4018: Ein Knoten darf gleichzeitig Werte UND Kinder haben (Mischknoten)."""
    root = auth_client.post("/api/datanodes", json={"name": "Misch"}).json()
    # Direkter Wert hinzufügen
    auth_client.post(f"/api/datanodes/{root['id']}/values", json={"value": "DirektWert"})
    # Kind hinzufügen
    auth_client.post("/api/datanodes", json={"name": "Kind", "parent_id": root["id"]})
    
    r = auth_client.get(f"/api/datanodes/{root['id']}")
    node = r.json()
    assert len(node["values"]) >= 1
    assert len(node["children"]) >= 1
    assert node["values"][0]["value"] == "DirektWert"
    assert node["children"][0]["name"] == "Kind"


def test_delete_node_cascades(auth_client):
    """REQ-4018: Löschen eines Knotens löscht alle Kinder (cascade)."""
    root = auth_client.post("/api/datanodes", json={"name": "ToDelete"}).json()
    child = auth_client.post("/api/datanodes", json={"name": "Child", "parent_id": root["id"]}).json()
    
    r = auth_client.delete(f"/api/datanodes/{root['id']}")
    assert r.status_code == 200
    
    # Root sollte nicht mehr existieren
    r2 = auth_client.get(f"/api/datanodes/{root['id']}")
    assert r2.status_code == 404
    
    # Kind sollte auch nicht mehr existieren
    r3 = auth_client.get(f"/api/datanodes/{child['id']}")
    assert r3.status_code == 404


def test_add_and_delete_value(auth_client):
    """REQ-4018: Werte zu Knoten hinzufügen und löschen."""
    node = auth_client.post("/api/datanodes", json={"name": "TestNode"}).json()
    
    # Wert hinzufügen
    val = auth_client.post(f"/api/datanodes/{node['id']}/values", json={"value": "TestWert"}).json()
    assert val["value"] == "TestWert"
    assert val["node_id"] == node["id"]
    
    # Wert löschen
    r = auth_client.delete(f"/api/datanodes/{node['id']}/values/{val['id']}")
    assert r.status_code == 200
    
    # Überprüfen dass Wert gelöscht ist
    node_updated = auth_client.get(f"/api/datanodes/{node['id']}").json()
    assert len(node_updated["values"]) == 0


def test_update_node(auth_client):
    """REQ-4018: Knoten umbenennen."""
    node = auth_client.post("/api/datanodes", json={"name": "AlterName"}).json()
    
    r = auth_client.put(f"/api/datanodes/{node['id']}", json={"name": "NeuerName"})
    assert r.status_code == 200
    updated = r.json()
    assert updated["name"] == "NeuerName"


def test_sort_order(auth_client):
    """REQ-4018: Sortierung nach sort_order."""
    root = auth_client.post("/api/datanodes", json={"name": "Root"}).json()
    
    # Kinder mit sort_order erstellen
    child1 = auth_client.post("/api/datanodes", json={"name": "Zweiter", "parent_id": root["id"], "sort_order": 2}).json()
    child2 = auth_client.post("/api/datanodes", json={"name": "Erster", "parent_id": root["id"], "sort_order": 1}).json()
    
    # Tree abrufen
    r = auth_client.get(f"/api/datanodes/{root['id']}")
    node = r.json()
    
    # Sollte nach sort_order sortiert sein
    assert len(node["children"]) == 2
    assert node["children"][0]["name"] == "Erster"  # sort_order=1
    assert node["children"][1]["name"] == "Zweiter"  # sort_order=2


def test_bugmagnet_status_before_import(auth_client):
    """REQ-4018: BugMagnet-Status vor Import."""
    r = auth_client.get("/api/datanodes/bugmagnet-status")
    assert r.status_code == 200
    # Kann True oder False sein, je nachdem ob schon importiert
    assert "imported" in r.json()


def test_system_flag(auth_client):
    """REQ-4018: is_system Flag wird korrekt gesetzt."""
    user_node = auth_client.post("/api/datanodes", json={"name": "UserNode"}).json()
    assert user_node["is_system"] is False
    
    system_node = auth_client.post("/api/datanodes", json={"name": "SystemNode", "is_system": True}).json()
    assert system_node["is_system"] is True