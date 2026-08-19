"""
REQ-4016: Ergebnis-Typ (Expected Result) für Kategorien.

is_result=True Kategorien werden aus der Kombinatorik ausgeschlossen
und dienen als separate Spalten für manuelle Test-Ergebnis-Angaben.
"""

import pytest


def test_category_has_is_result_field(client, db_session):
    """is_result Feld in Category-Schema vorhanden."""
    # Create project
    resp = client.post("/api/projects", json={"name": "TestProjectIsResult"})
    project_id = resp.json()["id"]
    
    # Create normal category
    cat = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Normal", "order_index": 0, "is_result": False}
    ).json()
    
    assert cat["id"]
    assert cat["name"] == "Normal"
    assert cat["is_result"] is False


def test_category_is_result_true(client):
    """is_result kann auf True gesetzt werden."""
    resp = client.post("/api/projects", json={"name": "TestProjectResult"})
    project_id = resp.json()["id"]
    
    cat = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Expected Result", "order_index": 1, "is_result": True}
    ).json()
    
    assert cat["is_result"] is True


def test_category_is_result_default_false(client):
    """is_result Default ist False."""
    resp = client.post("/api/projects", json={"name": "TestProjectDefault"})
    project_id = resp.json()["id"]
    
    cat = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "NoResult", "order_index": 0}
    ).json()
    
    assert cat.get("is_result", False) is False


def test_update_category_is_result(client):
    """is_result via PATCH aktualisierbar."""
    resp = client.post("/api/projects", json={"name": "TestProjectUpdate"})
    project_id = resp.json()["id"]
    
    # Create normal
    cat = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "TestCat", "order_index": 0, "is_result": False}
    ).json()
    cat_id = cat["id"]
    
    # Update to is_result
    updated = client.patch(
        f"/api/categories/{cat_id}/properties",
        json={"is_result": True}
    ).json()
    
    assert updated["is_result"] is True


def test_is_result_excluded_from_combinatorics(client):
    """is_result=True Kategorien werden aus Kombinatorik ausgeschlossen.
    
    Sie erscheinen aber in der API mit leeren Werten.
    """
    resp = client.post("/api/projects", json={"name": "CombinatoricsTest"})
    project_id = resp.json()["id"]
    
    # Create normal category with values
    cat1 = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Feature", "order_index": 0, "is_result": False}
    ).json()
    
    client.post(
        f"/api/categories/{cat1['id']}/values",
        json={"value": "A", "risk_weight": 1}
    )
    client.post(
        f"/api/categories/{cat1['id']}/values",
        json={"value": "B", "risk_weight": 1}
    )
    
    # Create result category with values
    cat2 = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Result", "order_index": 1, "is_result": True}
    ).json()
    
    client.post(
        f"/api/categories/{cat2['id']}/values",
        json={"value": "Pass", "risk_weight": 1}
    )
    client.post(
        f"/api/categories/{cat2['id']}/values",
        json={"value": "Fail", "risk_weight": 1}
    )
    
    # Generate testcases
    gen = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all"}
    ).json()
    
    # Get testcases
    tcs_raw = client.get(f"/api/generations/{gen['generation_id']}/testcases").json()
    
    # tcs_raw ist bereits ein Array von TestCase-Objekten
    tcs = tcs_raw if isinstance(tcs_raw, list) else tcs_raw.get("testcases", [])
    
    # Testcases sollten Feature-Werte haben (aus Kombinatorik)
    # UND Result-Spalte mit leerem Wert (nicht in Kombinatorik, sondern manuell befüllbar)
    assert len(tcs) == 2  # A und B = 2 Kombinationen
    for tc in tcs:
        assignments = tc.get("assignments", {})
        # Feature sollte dabei sein (A oder B)
        assert "Feature" in assignments
        assert assignments["Feature"] in ["A", "B"]
        # Result SOLLTE dabei sein mit leerem Wert (für manuelle Eingabe)
        assert "Result" in assignments
        assert assignments["Result"] == ""  # Leer!


def test_result_categories_in_api_list(client):
    """is_result Kategorien sind in der Kategorieliste sichtbar."""
    resp = client.post("/api/projects", json={"name": "ListTest"})
    project_id = resp.json()["id"]
    
    # Create normal
    client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Normal", "order_index": 0, "is_result": False}
    )
    
    # Create result
    client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": "Result", "order_index": 1, "is_result": True}
    )
    
    # List all
    cats = client.get(f"/api/projects/{project_id}/categories").json()
    
    assert len(cats) == 2
    assert any(c["name"] == "Normal" and not c["is_result"] for c in cats)
    assert any(c["name"] == "Result" and c["is_result"] for c in cats)
