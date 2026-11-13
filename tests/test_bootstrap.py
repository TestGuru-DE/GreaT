"""REQ-4020: First-Admin-Bootstrapping Tests.

TDD Slice 5: Erste registrierte Person wird automatisch Admin.
"""
import pytest
from app.database import SessionLocal, engine, Base
from app.models.auth import User
from app.bootstrap import ensure_first_admin


@pytest.fixture(autouse=True)
def _bootstrap_db():
    """Create auth tables, clean up after each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.rollback()
        except Exception:
            pass
        try:
            db.query(User).delete()
            db.commit()
        except Exception:
            pass
        finally:
            db.close()


class TestEnsureFirstAdmin:
    """REQ-4020: Erste registrierte Person wird automatisch Admin."""

    def test_creates_admin_when_no_users_exist(self, _bootstrap_db):
        """ensure_first_admin erstellt Admin wenn keine Users existieren."""
        admin = ensure_first_admin(_bootstrap_db)
        assert admin is not None
        assert admin.username == "admin"
        assert admin.role == "admin"
        assert admin.is_first_admin is True
        assert admin.is_active is True

    def test_default_admin_can_verify_password(self, _bootstrap_db):
        """Default-Admin kann mit Default-Passwort verifiziert werden."""
        admin = ensure_first_admin(_bootstrap_db)
        assert admin.check_password("changeme123!") is True

    def test_returns_existing_admin_when_users_exist(self, _bootstrap_db):
        """ensure_first_admin returns existing admin wenn Users existieren."""
        # Create a non-admin user first
        viewer = User(username="first_user", role="viewer")
        viewer.set_password("somepass")
        _bootstrap_db.add(viewer)
        _bootstrap_db.commit()
        _bootstrap_db.refresh(viewer)

        # Create an admin
        admin = User(username="real_admin", role="admin")
        admin.set_password("adminpass")
        _bootstrap_db.add(admin)
        _bootstrap_db.commit()
        _bootstrap_db.refresh(admin)

        # ensure_first_admin should return the existing admin
        result = ensure_first_admin(_bootstrap_db)
        assert result is not None
        assert result.username == "real_admin"
        assert result.role == "admin"

    def test_no_default_admin_created_when_admin_exists(self, _bootstrap_db):
        """Kein Default-Admin wenn bereits ein Admin existiert."""
        # Create an admin first
        admin = User(username="existing_admin", role="admin")
        admin.set_password("adminpass")
        _bootstrap_db.add(admin)
        _bootstrap_db.commit()

        # ensure_first_admin should NOT create another admin
        result = ensure_first_admin(_bootstrap_db)
        assert result is not None
        assert result.username == "existing_admin"

        # Verify no "admin" username was created
        default_admin = _bootstrap_db.query(User).filter(User.username == "admin").first()
        assert default_admin is None

    def test_default_admin_has_correct_username(self, _bootstrap_db):
        """Default-Admin hat username='admin' und role='admin'."""
        admin = ensure_first_admin(_bootstrap_db)
        assert admin.username == "admin"
        assert admin.role == "admin"

    def test_idempotent_call_creates_only_one_admin(self, _bootstrap_db):
        """Mehrfacher Aufruf erstellt nur einen Admin."""
        admin1 = ensure_first_admin(_bootstrap_db)
        admin2 = ensure_first_admin(_bootstrap_db)

        # Both should return the same admin
        assert admin1.id == admin2.id
        assert admin1.username == admin2.username

        # Only one admin user should exist
        count = _bootstrap_db.query(User).filter(User.role == "admin").count()
        assert count == 1