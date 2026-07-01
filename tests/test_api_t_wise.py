"""
REQ-3039: API-Integrationstests für T-Wise Strategie
Prüft dass der Endpoint /api/projects/{pid}/generate die t_wise Strategie akzeptiert.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.db import SessionLocal


client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Erzeugt Test-DB mit Projekt und Kategorien."""
    db = SessionLocal()
    try:
        # Projekt
        project = models.Project(name="T-Wise Test Project")
        db.add(project)
        db.flush()
        
        # Kategorien
        cat_os = models.Category(project_id=project.id, name="OS", order_index=1)
        cat_browser = models.Category(project_id=project.id, name="Browser", order_index=2)
        db.add(cat_os)
        db.add(cat_browser)
        db.flush()
        
        # Werte
        for val in ["Windows", "Linux", "Mac"]:
            db.add(models.Value(category_id=cat_os.id, value=val))
        for val in ["Chrome", "Firefox"]:
            db.add(models.Value(category_id=cat_browser.id, value=val))
        
        db.commit()
        
        yield project.id
        
    finally:
        # Cleanup
        db.query(models.Value).delete()
        db.query(models.Category).delete()
        db.query(models.TestCase).delete()
        db.query(models.Generation).delete()
        db.query(models.Project).delete()
        db.commit()
        db.close()


def test_api_accepts_t_wise_strategy(test_db):
    """TEST-API-001: API akzeptiert strategy="t_wise" mit Default t=2."""
    pid = test_db
    
    response = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data
    assert data["count"] > 0


def test_api_accepts_t_strength_parameter(test_db):
    """TEST-API-002: API akzeptiert t_strength Parameter."""
    pid = test_db
    
    # t=1
    response = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise", "t_strength": 1}
    )
    assert response.status_code == 200
    count_t1 = response.json()["count"]
    
    # t=2
    response = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise", "t_strength": 2}
    )
    assert response.status_code == 200
    count_t2 = response.json()["count"]
    
    # t=3 (Cartesian bei 2 Kategorien)
    response = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise", "t_strength": 3}
    )
    assert response.status_code == 200
    count_t3 = response.json()["count"]
    
    # Erwartung: t1 <= t2 <= t3
    assert count_t1 <= count_t2
    assert count_t2 <= count_t3


def test_api_t_wise_default_t_is_2(test_db):
    """TEST-API-003: Default t_strength ist 2 (Pairwise)."""
    pid = test_db
    
    # Ohne t_strength
    response1 = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise"}
    )
    count1 = response1.json()["count"]
    
    # Mit explizitem t=2
    response2 = client.post(
        f"/api/projects/{pid}/generate",
        json={"strategy": "t_wise", "t_strength": 2}
    )
    count2 = response2.json()["count"]
    
    # Sollten gleiche Anzahl erzeugen
    assert count1 == count2
