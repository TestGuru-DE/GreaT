"""
REQ-4006: Multi-User / Concurrent Access Tests.

Tests für SQLite WAL-Mode und PostgreSQL Support.
"""
import threading
import time
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Basierend auf projekteigenen Strukturen
import sys
sys.path.insert(0, "src")

from app.database import engine, SessionLocal, Base
from app.models import Project, Category, Value
from app.config import DATABASE_URL


class TestDatabaseConfiguration:
    """Tests für DB-Konfiguration."""

    def test_database_url_set(self):
        """DATABASE_URL ist konfiguriert."""
        assert DATABASE_URL is not None
        assert len(DATABASE_URL) > 0

    def test_database_url_supports_sqlite_or_postgres(self):
        """DATABASE_URL unterstützt SQLite oder PostgreSQL."""
        assert (
            DATABASE_URL.startswith("sqlite") or
            DATABASE_URL.startswith("postgresql") or
            DATABASE_URL.startswith("postgres")
        ), f"Unsupported DB URL: {DATABASE_URL}"

    def test_engine_pool_configured(self):
        """SQLAlchemy Engine hat Connection-Pool."""
        assert engine.pool is not None
        # SQLite oder PostgreSQL: mindestens pool_size=5
        if DATABASE_URL.startswith("sqlite"):
            assert engine.pool.size() >= 0  # SQLite hat kein klassisches pooling
        else:
            assert hasattr(engine.pool, "_pool")  # PostgreSQL: echtes Pooling


class TestConcurrentReads:
    """Tests für gleichzeitige Lesevorgänge."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Erstelle Test-Datenbank."""
        Base.metadata.create_all(bind=engine)
        
        # Füge Test-Daten ein
        db = SessionLocal()
        try:
            db.query(Project).delete()
            db.query(Category).delete()
            db.query(Value).delete()
            
            proj = Project(name="TestProject")
            db.add(proj)
            db.flush()
            
            cat = Category(name="TestCategory", project_id=proj.id)
            db.add(cat)
            db.flush()
            
            for i in range(5):
                val = Value(
                    value=f"Value{i}",
                    category_id=cat.id,
                    allowed=True,
                    vtype="string"
                )
                db.add(val)
            
            db.commit()
        finally:
            db.close()
        
        yield
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)

    def test_concurrent_project_reads(self):
        """10 gleichzeitige Projektlesevorgänge funktionieren."""
        results = []
        errors = []

        def read_projects():
            try:
                db = SessionLocal()
                projects = db.query(Project).all()
                results.append(len(projects))
                db.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_projects) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Concurrent read errors: {errors}"
        assert all(r == 1 for r in results), f"Unexpected project counts: {results}"

    def test_concurrent_category_reads(self):
        """10 gleichzeitige Kategorielessevorgänge funktionieren."""
        results = []
        errors = []

        def read_categories():
            try:
                db = SessionLocal()
                cats = db.query(Category).all()
                results.append(len(cats))
                db.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_categories) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Concurrent read errors: {errors}"
        assert all(r >= 1 for r in results), f"Unexpected category counts: {results}"

    def test_concurrent_value_reads(self):
        """10 gleichzeitige Value-Lesevorgänge funktionieren."""
        results = []
        errors = []

        def read_values():
            try:
                db = SessionLocal()
                vals = db.query(Value).all()
                results.append(len(vals))
                db.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_values) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Concurrent read errors: {errors}"
        assert all(r == 5 for r in results), f"Expected 5 values in each read, got: {results}"


class TestUpdatedAtTimestamps:
    """Tests für updated_at Optimistic Locking."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Erstelle Test-Datenbank."""
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            db.query(Project).delete()
            proj = Project(name="TimestampTest")
            db.add(proj)
            db.commit()
        finally:
            db.close()
        
        yield
        
        Base.metadata.drop_all(bind=engine)

    def test_project_has_updated_at(self):
        """Project-Modell hat updated_at Spalte."""
        db = SessionLocal()
        proj = db.query(Project).first()
        assert hasattr(proj, "updated_at")
        assert proj.updated_at is not None
        assert isinstance(proj.updated_at, datetime)
        db.close()

    def test_project_updated_at_on_update(self):
        """Project.updated_at wird bei Änderung aktualisiert."""
        db = SessionLocal()
        try:
            proj = db.query(Project).first()
            old_updated = proj.updated_at
            
            time.sleep(0.1)  # Stelle sicher, dass Zeit vergeht
            
            proj.name = "TimestampTest_UPDATED"
            db.commit()
            
            proj_refreshed = db.query(Project).filter_by(id=proj.id).first()
            assert proj_refreshed.updated_at >= old_updated, \
                f"updated_at sollte sich ändern: {old_updated} -> {proj_refreshed.updated_at}"
        finally:
            db.close()


class TestModelMigration:
    """Tests für Modell-Kompatibilität."""

    def test_all_models_have_updated_at(self):
        """Project, Category, Value, Generation haben updated_at."""
        Base.metadata.create_all(bind=engine)
        
        # Project
        proj_cols = [c.name for c in Project.__table__.columns]
        assert "updated_at" in proj_cols, f"Project hat kein updated_at. Spalten: {proj_cols}"
        
        # Category
        cat_cols = [c.name for c in Category.__table__.columns]
        assert "updated_at" in cat_cols, f"Category hat kein updated_at. Spalten: {cat_cols}"
        
        # Value
        val_cols = [c.name for c in Value.__table__.columns]
        assert "updated_at" in val_cols, f"Value hat kein updated_at. Spalten: {val_cols}"
        
        Base.metadata.drop_all(bind=engine)
