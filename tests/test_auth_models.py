"""REQ-4001 / REQ-4020: Auth-Model Tests (User + RefreshToken + Password-Hashing).

TDD Slice 1: User-Modell mit argon2id-Hashing + Rollen.
"""
from datetime import datetime, timedelta, timezone
import pytest
from app.models.auth import User, RefreshToken
from app.database import SessionLocal, engine, Base


@pytest.fixture(autouse=True)
def _auth_test_db():
    """Create auth tables for each test, clean up after."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Capture existing user IDs to preserve session-scoped test user
        existing_user_ids = {u.id for u in db.query(User).all()}
        yield db
    finally:
        # Clean up: first rollback if transaction is in error state
        try:
            db.rollback()
        except Exception:
            pass
        # Now clean up test data in reverse dependency order
        # Only delete users that were created during this test (not existing ones)
        try:
            current_user_ids = {u.id for u in db.query(User).all()}
            new_user_ids = current_user_ids - existing_user_ids
            # Delete refresh tokens for new users
            for uid in new_user_ids:
                db.query(RefreshToken).filter(RefreshToken.user_id == uid).delete()
            # Delete new users
            for uid in new_user_ids:
                user = db.query(User).filter(User.id == uid).first()
                if user:
                    db.delete(user)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()


class TestUserPasswordHashing:
    """REQ-4001: Passwoerder werden gehasht gespeichert (argon2id), niemals im Klartext."""

    def test_set_password_hashes_with_argon2id(self, _auth_test_db):
        """User.set_password haesht Passwort im argon2id-Format."""
        user = User(username="testuser", role="viewer")
        user.set_password("secret123")
        # argon2id hashes start with "$argon2id$"
        assert user.password_hash.startswith("$argon2id$")
        # Hash should NOT be the plaintext
        assert user.password_hash != "secret123"

    def test_check_password_accepts_correct_password(self, _auth_test_db):
        """User.check_password veroefacht korrektes Passwort."""
        user = User(username="testuser", role="viewer")
        user.set_password("correct_password")
        assert user.check_password("correct_password") is True

    def test_check_password_rejects_wrong_password(self, _auth_test_db):
        """User.check_password lehnt falsches Passwort ab."""
        user = User(username="testuser", role="viewer")
        user.set_password("correct_password")
        assert user.check_password("wrong_password") is False

    def test_check_password_rejects_empty_password(self, _auth_test_db):
        """User.check_password lehnt leeres Passwort ab."""
        user = User(username="testuser", role="viewer")
        user.set_password("some_password")
        assert user.check_password("") is False


class TestUserRoles:
    """REQ-4020: Rollen-Modell (Admin/Editor/Viewer)."""

    def test_user_default_role_is_viewer(self, _auth_test_db):
        """User.role Default ist 'viewer'."""
        user = User(username="testuser")
        assert user.role == "viewer"

    def test_user_can_be_admin(self, _auth_test_db):
        """User kann als Admin erstellt werden."""
        user = User(username="admin_user", role="admin")
        assert user.role == "admin"

    def test_user_can_be_editor(self, _auth_test_db):
        """User kann als Editor erstellt werden."""
        user = User(username="editor_user", role="editor")
        assert user.role == "editor"

    def test_user_is_active_by_default(self, _auth_test_db):
        """User.is_active ist standardmaessig True."""
        user = User(username="testuser")
        assert user.is_active is True

    def test_user_is_first_admin_flag(self, _auth_test_db):
        """User.is_first_admin Flag existiert und kann gesetzt werden."""
        user = User(username="first_admin", role="admin", is_first_admin=True)
        assert user.is_first_admin is True


class TestUserPersistence:
    """User kann in der DB gespeichert und gelesen werden."""

    def test_user_save_and_retrieve(self, _auth_test_db):
        """User wird korrekt in DB gespeichert und gelesen."""
        user = User(username="persist_test", role="editor")
        user.set_password("test123")
        _auth_test_db.add(user)
        _auth_test_db.commit()
        _auth_test_db.refresh(user)

        retrieved = _auth_test_db.query(User).filter(User.username == "persist_test").first()
        assert retrieved is not None
        assert retrieved.role == "editor"
        assert retrieved.check_password("test123") is True

    def test_user_unique_username_constraint(self, _auth_test_db):
        """Doppelte Usernames werden abgelehnt."""
        user1 = User(username="unique_test", role="viewer")
        user1.set_password("pass1")
        _auth_test_db.add(user1)
        _auth_test_db.commit()

        user2 = User(username="unique_test", role="viewer")
        user2.set_password("pass2")
        _auth_test_db.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            _auth_test_db.commit()


class TestRefreshToken:
    """REQ-4001: RefreshToken-Modell."""

    def test_refresh_token_creation(self, _auth_test_db):
        """RefreshToken wird erstellt mit expires_at."""
        user = User(username="rt_user", role="viewer")
        user.set_password("pass")
        _auth_test_db.add(user)
        _auth_test_db.commit()
        _auth_test_db.refresh(user)

        rt = RefreshToken(
            user_id=user.id,
            token="test-token-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        _auth_test_db.add(rt)
        _auth_test_db.commit()
        _auth_test_db.refresh(rt)

        assert rt.id is not None
        assert rt.user_id == user.id
        assert rt.token == "test-token-123"
        assert rt.is_revoked is False
        assert rt.expires_at is not None

    def test_refresh_token_revocation(self, _auth_test_db):
        """RefreshToken kann revokiert werden."""
        user = User(username="rt_user2", role="viewer")
        user.set_password("pass")
        _auth_test_db.add(user)
        _auth_test_db.commit()
        _auth_test_db.refresh(user)

        rt = RefreshToken(
            user_id=user.id,
            token="test-token-456",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        _auth_test_db.add(rt)
        _auth_test_db.commit()

        rt.is_revoked = True
        _auth_test_db.commit()

        retrieved = _auth_test_db.query(RefreshToken).filter(RefreshToken.token == "test-token-456").first()
        assert retrieved.is_revoked is True

    def test_refresh_token_multiple_allowed(self, _auth_test_db):
        """B2: Multiple Refresh-Token pro User erlaub (Token-Rotation)."""
        user = User(username="rt_user3", role="viewer")
        user.set_password("pass")
        _auth_test_db.add(user)
        _auth_test_db.commit()
        _auth_test_db.refresh(user)

        rt1 = RefreshToken(
            user_id=user.id,
            token="rotation-token-1",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        _auth_test_db.add(rt1)
        _auth_test_db.commit()

        # B2: Zweiter Token mit anderem Wert sollte funktionieren (Rotation)
        rt2 = RefreshToken(
            user_id=user.id,
            token="rotation-token-2",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        _auth_test_db.add(rt2)
        _auth_test_db.commit()

        # Beide Tokens sollten in der DB sein
        count = _auth_test_db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count()
        assert count == 2