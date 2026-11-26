# Ensure the project's src/ is importable in tests
import sys, os, pathlib, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# REQ-1300 Testintegritaet: Schutz der realen great.db.
# Der Snapshot MUSS vor jedem Datenbankzugriff entstehen (siehe tests/db_guard.py).
sys.path.insert(0, os.path.dirname(__file__))
import db_guard  # noqa: E402  (importiert vor app.*, erstellt START_SNAPSHOT)

# REQ-1300: Jeder Testlauf nutzt eine eigene temporaere SQLite-Datei.
# Muss VOR dem ersten Import von app.config/app.database gesetzt werden.
# Wird conftest zusaetzlich als Modul importiert (z. B. "from tests.conftest
# import ..."), darf keine zweite Test-DB entstehen: Pfad einmal pro Prozess.
if getattr(db_guard, "TEST_DB_PATH", None) is None:
    db_guard.TEST_DB_PATH = os.path.join(
        tempfile.mkdtemp(prefix="great-pytest-"), "test_great.db")
_TEST_DB_PATH = db_guard.TEST_DB_PATH
os.environ["DATABASE_URL"] = "sqlite:///" + pathlib.Path(_TEST_DB_PATH).as_posix()
os.environ["GREAT_TEST_DB_PATH"] = _TEST_DB_PATH

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# REQ-2005: System-Datenklassen beim Test-Start sicherstellen
def pytest_configure(config):
    """DB-Migration + System-Datenklassen-Seed vor dem ersten Test."""
    from app.database import engine, Base, SessionLocal
    from app.main import _migrate_db
    from app.system_dataclasses import seed_system_dataclasses

    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
        # REQ-4017: Beispielprojekt wie beim App-Start (Lifespan) anlegen
        from app.seed_example import seed_example_project
        seed_example_project(db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Gemeinsame Fixtures (REQ-4001 / REQ-4025)
# ---------------------------------------------------------------------------

def _make_token_client(username: str, role: str) -> TestClient:
    """TestClient mit gueltigem access_token-Cookie fuer einen Testnutzer.

    Legt den Nutzer bei Bedarf an bzw. setzt Rolle/Status zurueck. Das Token
    wird direkt erzeugt (kein /auth/login), damit das Login-Rate-Limit nicht greift.
    """
    from app.database import SessionLocal
    from app.models.auth import User
    from app.auth_utils import create_access_token

    password = "testpass123"
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username=username, role=role)
            db.add(user)
        user.role = role
        user.is_active = True
        user.default_password_active = False
        user.token_version = 0
        user.set_password(password)
        db.commit()
        db.refresh(user)
        token = create_access_token(user.id, user.username, user.role, user.token_version)
    finally:
        db.close()
    client = TestClient(app_instance())
    client.cookies.set("access_token", token)
    return client


def app_instance():
    from app.main import app
    return app


def pytest_runtest_setup(item):
    """Rate-Limiter je Test leeren (sonst 429 durch Tests untereinander)."""
    from app.rate_limiter import (
        login_rate_limiter,
        first_start_hint_rate_limiter,
        password_change_rate_limiter,
        token_rate_limiter,
        token_failure_rate_limiter,
    )
    for limiter in (login_rate_limiter, first_start_hint_rate_limiter, password_change_rate_limiter,
                    token_rate_limiter, token_failure_rate_limiter):
        limiter._requests.clear()


@pytest.fixture
def client():
    """Anonymer TestClient (z. B. fuer /health)."""
    return TestClient(app_instance())


@pytest.fixture
def auth_client():
    """Angemeldeter Editor (Schreibrechte, kein Admin)."""
    return _make_token_client("testuser", "editor")


@pytest.fixture
def editor_client():
    """Angemeldeter Editor (alias fuer auth_client; explizit benannt)."""
    return _make_token_client("editortest", "editor")


@pytest.fixture
def admin_client():
    """Angemeldeter Admin."""
    return _make_token_client("testadmin", "admin")


@pytest.fixture
def db_session():
    """Datenbank-Session fuer Test-Setup."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def _auth_cookies(auth_client):
    """Cookies des angemeldeten auth_client (access_token)."""
    return {"access_token": auth_client.cookies.get("access_token")}


@pytest.fixture(autouse=True)
def _clean_users_per_test():
    """REQ-4027/REQ-1300: Saubere Nutzerbasis je Test in der temporaeren Test-DB.

    Entfernt Nutzer und Refresh-Tokens (db_cleanup.purge_users).
    """
    from app.database import SessionLocal
    from db_cleanup import purge_users
    db = SessionLocal()
    try:
        purge_users(db, None)
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _purge_test_projects_per_test():
    """Projekte ausser dem Beispielprojekt (REQ-4017) je Test entfernen.

    Verhindert Kollisionen eindeutiger Projektnamen (z. B. 'RiskSummaryProject').
    Abhaengige Tabellen ohne ON DELETE CASCADE werden vorher geleert.
    """
    from app.database import SessionLocal
    from app.models import Project, Constraint
    from app.models.decision_table_constraint import DecisionTableConstraint
    from app.models.project_membership import ProjectMembership
    db = SessionLocal()
    try:
        ids = [p.id for p in db.query(Project.id).filter(Project.name != "Portoberechnung (Beispiel)").all()]
        if ids:
            # Tabellen ohne ON DELETE CASCADE zuerst leeren (sonst FK-Fehler)
            db.query(Constraint).filter(Constraint.project_id.in_(ids)).delete(synchronize_session=False)  # REQ-6001
            db.query(DecisionTableConstraint).filter(DecisionTableConstraint.project_id.in_(ids)).delete(synchronize_session=False)
            db.query(ProjectMembership).filter(ProjectMembership.project_id.in_(ids)).delete(synchronize_session=False)
            db.query(Project).filter(Project.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _purge_datanodes_per_test():
    """B-09: DataNodes und DataNodeValues je Test entfernen."""
    from app.database import SessionLocal
    from app.models import DataNode, DataNodeValue
    db = SessionLocal()
    try:
        db.query(DataNodeValue).delete(synchronize_session=False)
        db.query(DataNode).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _purge_api_tokens_per_test():
    """REQ-6012: API-Tokens je Test entfernen (vor User-Cleanup wegen FK)."""
    from app.database import SessionLocal
    from app.models.auth import ApiToken
    db = SessionLocal()
    try:
        db.query(ApiToken).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _purge_constraints_per_test():
    """REQ-6001: Constraints je Test entfernen (vor Project-Cleanup wegen FK)."""
    from app.database import SessionLocal
    from app.models import Constraint
    db = SessionLocal()
    try:
        db.query(Constraint).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _clear_coverage_cache_per_test():
    """REQ-6008: Coverage-Cache je Test leeren."""
    from app.routers.api_coverage import _coverage_cache
    _coverage_cache.clear()
    yield
    _coverage_cache.clear()


@pytest.fixture(autouse=True)
def _purge_seed_sets_per_test():
    """REQ-6009: Seed-Saetze und Seed-Cases je Test entfernen."""
    from app.database import SessionLocal
    from app.models.seed import SeedCase, SeedSet
    db = SessionLocal()
    try:
        db.query(SeedCase).delete(synchronize_session=False)
        db.query(SeedSet).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# T-6: Test-Router fuer Debug-Auth-Endpunkte (nur in Tests)
# ---------------------------------------------------------------------------

def _setup_test_auth_endpoints():
    """Fuegt Test-Endpunkte fuer Role-Checks zur App hinzu (nur in Tests).

    Diese Endpunkte wurden aus dem Produktivcode entfernt (T-6) und stehen
    hier fuer Tests zur Verfuegung.
    """
    from app.main import app
    from app.auth_deps import require_admin, require_editor_or_admin, require_writer, require_api_capable
    from app.models.auth import User
    from fastapi import Depends, APIRouter

    test_router = APIRouter(prefix="/auth", tags=["auth-test"])

    @test_router.get("/admin-only")
    def admin_only(current_user: User = Depends(require_admin)):
        return {"message": "Zugriff als Admin gewaehrt", "username": current_user.username, "role": current_user.role}

    @test_router.get("/editor-or-admin")
    def editor_or_admin(current_user: User = Depends(require_editor_or_admin)):
        return {"message": "Zugriff als Editor/Admin gewaehrt", "username": current_user.username, "role": current_user.role}

    @test_router.get("/writer-only")
    def writer_only(current_user: User = Depends(require_writer)):
        return {"message": "Zugriff als Writer gewaehrt", "username": current_user.username, "role": current_user.role}

    @test_router.get("/api-capable")
    def api_capable(current_user: User = Depends(require_api_capable)):
        return {"message": "Zugriff als API-Capable gewaehrt", "username": current_user.username, "role": current_user.role}

    app.include_router(test_router)


# Setup test endpoints on first import
_setup_test_auth_endpoints()
