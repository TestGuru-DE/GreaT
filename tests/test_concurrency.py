"""REQ-4021: Optimistic Concurrency Control Tests"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.concurrency import check_version, update_with_version


class MockEntity:
    """Minimaler Mock fuer SQLAlchemy-Entity mit version-Feld."""
    def __init__(self, id: int, version: int = 0, name: str = "test"):
        self.id = id
        self.version = version
        self.name = name


class MockQuery:
    """Mock fuer db.query(Model).get(id)"""
    def __init__(self, entity: MockEntity | None):
        self.entity = entity

    def get(self, id: int):
        return self.entity


class MockDB:
    """Mock fuer DB-Session."""
    def __init__(self, entity: MockEntity | None = None):
        self.entity = entity
        self.query_mock = MockQuery(entity)
        self.committed = False
        self.refreshed = False

    def query(self, model):
        return self.query_mock

    def commit(self):
        self.committed = True

    def refresh(self, entity):
        self.refreshed = True


def test_check_version_not_found():
    """check_version mit nicht-existenter ID -> 404."""
    db = MockDB(entity=None)
    with pytest.raises(HTTPException) as exc:
        check_version(db, MockEntity, 999, None)
    assert exc.value.status_code == 404


def test_check_version_no_client_version():
    """check_version ohne client_version -> OK, version inkrementiert."""
    entity = MockEntity(id=1, version=0)
    db = MockDB(entity=entity)
    result = check_version(db, MockEntity, 1, None)
    assert result.version == 1


def test_check_version_correct_version():
    """check_version mit korrekter client_version -> OK, version inkrementiert."""
    entity = MockEntity(id=1, version=5)
    db = MockDB(entity=entity)
    result = check_version(db, MockEntity, 1, 5)
    assert result.version == 6


def test_check_version_wrong_version():
    """check_version mit falscher client_version -> 409."""
    entity = MockEntity(id=1, version=10)
    db = MockDB(entity=entity)
    with pytest.raises(HTTPException) as exc:
        check_version(db, MockEntity, 1, 5)
    assert exc.value.status_code == 409
    detail = exc.value.detail
    assert detail["type"] == "version_conflict"
    assert detail["client_version"] == 5
    assert detail["server_version"] == 10


def test_check_version_no_version_field():
    """check_version ohne version-Feld -> kein Fehler, kein Inkrement."""
    class NoVersionEntity:
        id = 1
        name = "test"
    entity = NoVersionEntity()
    db = MockDB(entity=entity)
    result = check_version(db, NoVersionEntity, 1, None)
    assert result is entity


def test_update_with_version_success():
    """update_with_version mit korrekter version -> Felder aktualisiert."""
    entity = MockEntity(id=1, version=3, name="old")
    db = MockDB(entity=entity)
    result = update_with_version(
        db, MockEntity, 1, 3, {"name": "new"}
    )
    assert result.name == "new"
    assert result.version == 4
    assert db.committed
    assert db.refreshed


def test_update_with_version_conflict():
    """update_with_version mit falscher version -> 409."""
    entity = MockEntity(id=1, version=10, name="test")
    db = MockDB(entity=entity)
    with pytest.raises(HTTPException) as exc:
        update_with_version(db, MockEntity, 1, 5, {"name": "new"})
    assert exc.value.status_code == 409


def test_update_with_version_no_client_version():
    """update_with_version ohne client_version -> OK (erstes Update)."""
    entity = MockEntity(id=1, version=0, name="old")
    db = MockDB(entity=entity)
    result = update_with_version(
        db, MockEntity, 1, None, {"name": "new"}
    )
    assert result.name == "new"
    assert result.version == 1


def test_update_with_version_excludes_id_version():
    """update_with_version setzt nicht id/version/created_at."""
    entity = MockEntity(id=1, version=2, name="old")
    db = MockDB(entity=entity)
    result = update_with_version(
        db, MockEntity, 1, 2, {"name": "new", "id": 999, "version": 999}
    )
    assert result.id == 1  # nicht geaendert
    assert result.version == 3  # inkrementiert, nicht auf 999 gesetzt


def test_concurrent_updates_scenario():
    """Zwei Updates mit gleicher Ausgangsversion -> zweites liefert 409."""
    # Simuliert: Client A und Client B lesen beide version=5
    # Client A aktualisiert zuerst -> version wird 6
    # Client B versucht mit version=5 -> 409
    
    entity = MockEntity(id=1, version=5, name="original")
    db = MockDB(entity=entity)
    
    # Client A aktualisiert (version 5 -> 6)
    result_a = update_with_version(db, MockEntity, 1, 5, {"name": "from_A"})
    assert result_a.version == 6
    assert result_a.name == "from_A"
    
    # Entity hat jetzt version=6
    entity.version = 6
    entity.name = "from_A"
    
    # Client B versucht mit version=5 -> 409
    with pytest.raises(HTTPException) as exc:
        update_with_version(db, MockEntity, 1, 5, {"name": "from_B"})
    assert exc.value.status_code == 409