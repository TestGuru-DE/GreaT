# Ensure the project's src/ is importable in tests
import sys, os, pathlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, SessionLocal, get_db, engine
from app.main import app, _migrate_db
from app.system_dataclasses import seed_system_dataclasses


# REQ-2005: System-Datenklassen beim Test-Start sicherstellen
def pytest_configure(config):
    """DB-Migration + System-Datenklassen-Seed vor dem ersten Test."""
    Base.metadata.create_all(bind=engine)
    _migrate_db(engine)
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def db_transaction_rollback():
    """Autouse-Fixture: Jeder Test läuft in einer Transaktion, die nach dem Test rollback wird."""
    connection = engine.connect()
    transaction = connection.begin()
    
    # Überschreibe SessionLocal für diesen Test
    session = sessionmaker(bind=connection)()
    
    # Patch get_db Dependency für diesen Test
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session():
    """DB-Session pro Test mit Rollback nach Test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient mit Override der get_db Dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
