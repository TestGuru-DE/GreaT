"""REQ-4017: Beispielprojekt Portoberechnung."""
from fastapi.testclient import TestClient


def test_example_project_exists(client: TestClient):
    """Beispielprojekt sollte nach App-Start existieren."""
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    names = [p["name"] for p in projects]
    assert any("Porto" in n for n in names), f"Expected project with 'Porto' in name. Got: {names}"


def test_example_project_has_five_categories(client: TestClient):
    """Portoberechnung sollte 5 Kategorien haben."""
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    porto = next((p for p in projects if "Porto" in p.get("name", "")), None)
    assert porto is not None, "Portoberechnung project not found"

    r2 = client.get(f"/api/projects/{porto['id']}/categories")
    assert r2.status_code == 200
    categories = r2.json()
    assert len(categories) == 5, f"Expected 5 categories, got {len(categories)}: {[c['name'] for c in categories]}"


def test_example_categories_have_names(client: TestClient):
    """Kategorien sollten korrekte Namen haben."""
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    porto = next((p for p in projects if "Porto" in p.get("name", "")), None)
    assert porto is not None

    r2 = client.get(f"/api/projects/{porto['id']}/categories")
    assert r2.status_code == 200
    categories = r2.json()
    names = {c["name"] for c in categories}
    expected = {"Gewicht", "Größe", "Transportart", "Zielland", "Portopreis (Ergebnis)"}
    assert expected.issubset(names), f"Expected categories {expected}, got {names}"


def test_example_weight_category_values(client: TestClient):
    """Gewicht-Kategorie sollte 4 Werte haben."""
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    porto = next((p for p in projects if "Porto" in p.get("name", "")), None)
    assert porto is not None

    r2 = client.get(f"/api/projects/{porto['id']}/categories")
    assert r2.status_code == 200
    categories = r2.json()
    weight_cat = next((c for c in categories if c["name"] == "Gewicht"), None)
    assert weight_cat is not None, "Gewicht category not found"

    r3 = client.get(f"/api/categories/{weight_cat['id']}/values")
    assert r3.status_code == 200, f"Failed to get values: {r3.status_code} {r3.text}"
    values = r3.json()
    assert len(values) == 4, f"Expected 4 weight values, got {len(values)}: {values}"


def test_example_price_category_values(client: TestClient):
    """Portopreis-Kategorie sollte 6 Werte haben."""
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    porto = next((p for p in projects if "Porto" in p.get("name", "")), None)
    assert porto is not None

    r2 = client.get(f"/api/projects/{porto['id']}/categories")
    assert r2.status_code == 200
    categories = r2.json()
    price_cat = next((c for c in categories if "Portopreis" in c.get("name", "")), None)
    assert price_cat is not None, "Portopreis category not found"

    r3 = client.get(f"/api/categories/{price_cat['id']}/values")
    assert r3.status_code == 200, f"Failed to get values: {r3.status_code} {r3.text}"
    values = r3.json()
    assert len(values) == 6, f"Expected 6 price values, got {len(values)}: {values}"
