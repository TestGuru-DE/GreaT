"""
tests/test_bugfix_themes_strategies.py
BUG-1, BUG-3, BUG-5, REQ-3063 Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models
from src.app.services import sort_testcases_error_last, load_error_values
from combinatorics.risk_based import sort_by_risk_descending


# --- Isolierte Test-DB ---
TEST_DB = "sqlite:///./test_bugfix.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def session():
    """Gibt eine DB-Session zurück."""
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_project(session):
    """Erstellt ein Test-Projekt."""
    proj = models.Project(name="BUG-Test-Projekt")
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return proj


def test_sort_testcases_error_last_basic():
    """BUG-5: Testfälle mit Fehlerwerten werden ans Ende sortiert."""
    testcases = [
        {"A": "val1", "B": "val2"},
        {"A": "error1", "B": "val2"},  # Enthält Fehlerwert
        {"A": "val1", "B": "val3"},
        {"A": "val1", "B": "error2"},  # Enthält Fehlerwert
    ]
    error_values = {"error1", "error2"}
    
    result = sort_testcases_error_last(testcases, error_values)
    
    # Erste zwei sollten ohne Fehler sein
    assert result[0] == {"A": "val1", "B": "val2"}
    assert result[1] == {"A": "val1", "B": "val3"}
    # Letzte zwei sollten Fehlerwerte enthalten
    assert result[2] == {"A": "error1", "B": "val2"}
    assert result[3] == {"A": "val1", "B": "error2"}


def test_sort_testcases_error_last_no_errors():
    """BUG-5: Edge Case - keine Fehlerwerte."""
    testcases = [
        {"A": "val1", "B": "val2"},
        {"A": "val3", "B": "val4"},
    ]
    error_values = set()
    
    result = sort_testcases_error_last(testcases, error_values)
    
    assert len(result) == 2
    assert result == testcases


def test_sort_testcases_error_last_all_errors():
    """BUG-5: Edge Case - alle Testfälle enthalten Fehlerwerte."""
    testcases = [
        {"A": "error1", "B": "val2"},
        {"A": "val1", "B": "error2"},
    ]
    error_values = {"error1", "error2"}
    
    result = sort_testcases_error_last(testcases, error_values)
    
    assert len(result) == 2
    # Alle sind "Fehler", Reihenfolge bleibt erhalten
    assert result == testcases


def test_load_error_values(session, sample_project):
    """REQ-3063: load_error_values lädt alle allowed=False Werte."""
    cat1 = models.Category(project_id=sample_project.id, name="Cat1", order_index=0)
    session.add(cat1)
    session.flush()
    
    val1 = models.Value(category_id=cat1.id, value="normal", allowed=True, vtype="string")
    val2 = models.Value(category_id=cat1.id, value="fehler1", allowed=False, vtype="string")
    val3 = models.Value(category_id=cat1.id, value="fehler2", allowed=False, vtype="string")
    session.add_all([val1, val2, val3])
    session.commit()
    
    errors = load_error_values(session, sample_project.id)
    
    assert "fehler1" in errors
    assert "fehler2" in errors
    assert "normal" not in errors
    assert len(errors) == 2


def test_risk_sort_dann_error_sort_komposition_fehlerwert_landet_hinten():
    """REQ-3034 + BUG-5/REQ-3018: Komposition auf Funktionsebene.

    sort_by_risk_descending() wird ZUERST angewendet (Risiko-Sortierung),
    danach sort_testcases_error_last() (Fehlerwert-Vorrang). Ein Testfall mit
    hohem Risiko-Score, der aber einen Fehlerwert enthaelt, muss trotzdem am
    Ende der finalen Liste landen.
    """
    category_risk_map = {
        "Browser": [("Chrome", 10), ("Firefox", 1)],
        "OS": [("Windows", 1), ("BrokenOS", 20)],  # BrokenOS ist Fehlerwert
    }
    testcases = [
        {"Browser": "Firefox", "OS": "Windows"},   # Score 2, kein Fehlerwert
        {"Browser": "Chrome", "OS": "BrokenOS"},   # Score 30, ABER Fehlerwert
        {"Browser": "Chrome", "OS": "Windows"},    # Score 11, kein Fehlerwert
    ]
    error_values = {"BrokenOS"}

    risk_sorted = sort_by_risk_descending(testcases, category_risk_map)
    result = sort_testcases_error_last(risk_sorted, error_values)

    # Der Fehlerwert-Testfall (trotz hoechstem Risiko) steht am Ende.
    assert result[-1] == {"Browser": "Chrome", "OS": "BrokenOS"}
    # Die verbleibenden (fehlerfreien) Testfaelle sind weiterhin nach Risiko sortiert.
    assert result[0] == {"Browser": "Chrome", "OS": "Windows"}
    assert result[1] == {"Browser": "Firefox", "OS": "Windows"}

