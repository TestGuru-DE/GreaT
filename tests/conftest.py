# Ensure the project's src/ is importable in tests
import sys, os, pathlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# REQ-2005: System-Datenklassen beim Test-Start sicherstellen
def pytest_configure(config):
    """DB-Migration + System-Datenklassen-Seed vor dem ersten Test."""
    from app.db import engine, Base, SessionLocal
    from app.main import _migrate_db
    from app.system_dataclasses import seed_system_dataclasses

    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
    finally:
        db.close()

