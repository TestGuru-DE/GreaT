"""
Datenbankverbindung mit SQLite WAL-Mode + PostgreSQL Support.

REQ-4006: Multi-User Support
- SQLite: WAL-Mode für concurrent reads
- PostgreSQL: Connection-Pool für Teams
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL


def _create_engine():
    """Engine mit DB-spezifischen Optimierungen erstellen."""
    if DATABASE_URL.startswith("sqlite"):
        # SQLite: Connection-Pool + WAL-Mode
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
        
        # WAL-Mode für concurrent reads + normal sync für Sicherheit
        @event.listens_for(engine, "connect")
        def set_wal_mode(conn, _):
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA foreign_keys=ON")
        
        return engine
    else:
        # PostgreSQL oder andere Datenbanken
        return create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy Basis-Model mit Standard-Typhandling."""
    pass


def get_db():
    """Dependency Injection für FastAPI DB-Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
