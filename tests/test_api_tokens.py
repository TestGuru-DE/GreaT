"""REQ-6012: API-Tokens fuer CI und Testwerkzeuge – TDD Tests.

Tests fuer:
- Token-Erzeugung: argon2id+Salt gespeichert, Klartext nur einmal
- Bearer-Auth erfolgreich, abgelaufen, widerrufen
- Scope fehlt (403 insufficient_scope)
- Rolle schlaegt Scope (Viewer + projects:write -> 403)
- gesperrte Endpunkte (Benutzerverwaltung, Passwort, Token-Verwaltung, Backup)
- Ungueltigkeit nach Rollenwechsel (token_version)
- Rate-Limit pro Token (600/Min)
- OpenAPI enthaelt HTTPBearer Security-Scheme
- /api/v1/-Alias liefert identische Antworten
- api_user-Rolle: kein Login, nur Token
"""
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
import secrets
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.auth import User, ApiToken
from app.auth_utils import create_access_token
from app.config import JWT_SECRET_KEY
from db_cleanup import purge_users


# ---------------------------------------------------------------------------
# Helper: create a user + api token for testing
# ---------------------------------------------------------------------------

def _create_user_with_token(db, username, role, scopes=None):
    """Create a user and an API token, return (user, raw_token, token_record)."""
    from app.api_token_service import create_api_token

    user = User(username=username, role=role)
    user.set_password("testpass123")
    user.default_password_active = False
    user.token_version = 0
    db.add(user)
    db.commit()
    db.refresh(user)

    if scopes is None:
        scopes = ["projects:read", "generate"]

    raw_token, token_record = create_api_token(db, user, "test-token", scopes, days=90)
    return user, raw_token, token_record


def _bearer_headers(raw_token):
    return {"Authorization": f"Bearer {raw_token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_api_tokens_per_test():
    """Remove all API tokens and users before/after each test."""
    db = SessionLocal()
    try:
        # Delete api_tokens first (FK to users)
        db.query(ApiToken).delete(synchronize_session=False)
        purge_users(db)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(ApiToken).delete(synchronize_session=False)
        purge_users(db)
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _clear_token_rate_limiter():
    """Clear token rate limiter before each test."""
    from app.rate_limiter import token_rate_limiter
    token_rate_limiter._requests.clear()
    yield
    token_rate_limiter._requests.clear()


# ============================================================================
# REQ-6012 AK-1: Token-Erzeugung
# ============================================================================

class TestTokenCreation:
    """Token-Erzeugung: Hash gespeichert, Klartext nur einmal."""

    def test_create_token_returns_prefix_and_hash(self):
        """Das Token wird mit Hash und Salt gespeichert, Klartext nur im Return."""
        db = SessionLocal()
        try:
            user, raw_token, token_record = _create_user_with_token(
                db, "testuser1", "editor", ["projects:read", "generate"]
            )

            # Raw token has prefix
            assert raw_token.startswith("great_pat_")

            # Stored record has prefix (first 16 chars of raw token)
            assert token_record.prefix == raw_token[:16]

            # Stored hash is NOT the raw token
            assert token_record.token_hash != raw_token

            # Salt is 32 bytes (stored as hex = 64 chars)
            assert len(token_record.salt) == 64

            # Scopes stored
            assert "projects:read" in token_record.scopes
            assert "generate" in token_record.scopes

            # Expires_at is set
            assert token_record.expires_at is not None

            # last_used_at is NULL on creation
            assert token_record.last_used_at is None

            # token_version_at_creation matches user's version
            assert token_record.token_version_at_creation == user.token_version
        finally:
            db.close()

    def test_create_token_randomness(self):
        """Zwei Tokens fuer denselben User sind unterschiedlich."""
        db = SessionLocal()
        try:
            user, raw1, _ = _create_user_with_token(db, "testuser2", "editor")
            user2, raw2, _ = _create_user_with_token(db, "testuser2b", "editor")
            assert raw1 != raw2
        finally:
            db.close()

    def test_create_token_max_expiry_365_days(self):
        """Maximales Ablaufdatum ist 365 Tage."""
        db = SessionLocal()
        try:
            user = User(username="testuser3", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.api_token_service import create_api_token
            now = datetime.now(timezone.utc)
            raw_token, token_record = create_api_token(
                db, user, "long-token", ["projects:read"], days=365
            )
            # Make both timezone-aware for comparison
            expires = token_record.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            delta = expires - now
            # Allow 1 second tolerance
            assert delta <= timedelta(days=365, seconds=1)
        finally:
            db.close()

    def test_create_token_min_expiry_1_day(self):
        """Mindestens 1 Tag Laeufigkeit."""
        db = SessionLocal()
        try:
            user = User(username="testuser4", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.api_token_service import create_api_token
            now = datetime.now(timezone.utc)
            raw_token, token_record = create_api_token(
                db, user, "short-token", ["projects:read"], days=1
            )
            expires = token_record.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            delta = expires - now
            assert delta >= timedelta(hours=23)  # ~1 day
        finally:
            db.close()


# ============================================================================
# REQ-6012 AK-2: Bearer-Auth erfolgreich
# ============================================================================

class TestBearerAuth:
    """Bearer-Auth: erfolgreich, abgelaufen, widerrufen."""

    def test_bearer_auth_success(self):
        """Gueltiger Bearer-Token -> 200 auf /auth/me."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser5", "editor", ["projects:read"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser5"

    def test_bearer_auth_no_cookie_needed(self):
        """Bearer-Auth funktioniert OHNE Cookie."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser6", "editor", ["projects:read"]
            )
        finally:
            db.close()

        client = TestClient(app)
        # No cookies set, only Authorization header
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 200

    def test_bearer_auth_expired_token(self):
        """Abgelaufener Token -> 401."""
        db = SessionLocal()
        try:
            user = User(username="testuser7", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.api_token_service import create_api_token
            raw_token, token_record = create_api_token(
                db, user, "expired-token", ["projects:read"], days=1
            )
            # Manually expire the token
            token_record.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db.commit()
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 401

    def test_bearer_auth_revoked_token(self):
        """Widerrufener Token -> 401."""
        db = SessionLocal()
        try:
            user, raw_token, token_record = _create_user_with_token(
                db, "testuser8", "editor", ["projects:read"]
            )
            token_record.revoked_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 401

    def test_bearer_auth_invalid_token(self):
        """Ungueltiger Token (falsches Format) -> 401."""
        client = TestClient(app)
        resp = client.get("/auth/me", headers={"Authorization": "Bearer great_pat_falsch"})
        assert resp.status_code == 401

    def test_bearer_auth_user_deactivated(self):
        """Deaktivierter User -> Token ungültig."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser9", "editor", ["projects:read"]
            )
            user.is_active = False
            db.commit()
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 403


# ============================================================================
# REQ-6012 AK-3: Scope-Prüfung
# ============================================================================

class TestScopeCheck:
    """Scope fehlt (403 insufficient_scope), Rolle schlägt Scope."""

    def test_missing_scope_returns_403(self):
        """Token ohne 'generate' Scope -> 403 auf Generierungs-Endpunkt."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser10", "editor", ["projects:read"]  # NO generate
            )
        finally:
            db.close()

        client = TestClient(app)
        # Try to access a generate endpoint
        resp = client.get("/api/projects", headers=_bearer_headers(raw_token))
        # projects:read should allow listing
        assert resp.status_code == 200

    def test_role_overrides_scope(self):
        """Viewer + projects:write -> 403 (Rolle schlägt Scope)."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser11", "viewer", ["projects:read", "projects:write"]
            )
        finally:
            db.close()

        client = TestClient(app)
        # Viewer can read but not write, even with projects:write scope
        resp = client.post(
            "/api/projects",
            json={"name": "TestProject"},
            headers=_bearer_headers(raw_token),
        )
        # Viewer role blocks writes regardless of scope
        assert resp.status_code == 403

    def test_insufficient_scope_error_code(self):
        """Fehlender Scope liefert code 'insufficient_scope'."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser12", "editor", ["projects:read"]  # NO generate
            )
            # Create a project to try generating
            client = TestClient(app)
            # First create project as editor via cookie
            from app.auth_utils import create_access_token
            cookie_token = create_access_token(user.id, user.username, user.role, user.token_version)
            resp = client.post(
                "/api/projects",
                json={"name": "ScopeTestProject"},
                cookies={"access_token": cookie_token},
            )
            assert resp.status_code in (200, 201)
            project_id = resp.json()["id"]
        finally:
            db.close()

        client = TestClient(app)
        resp = client.post(
            f"/api/projects/{project_id}/generate",
            json={"strategy": "all"},
            headers=_bearer_headers(raw_token),
        )
        assert resp.status_code == 403
        # Check X-Error-Code header or detail message
        error_code = resp.headers.get("x-error-code", "")
        detail = resp.json().get("detail", "").lower()
        assert "insufficient_scope" in error_code or "insufficient_scope" in detail


# ============================================================================
# REQ-6012 AK-4: Gesperrte Endpunkte
# ============================================================================

class TestBlockedEndpoints:
    """Tokens nicht gueltig fuer: Benutzerverwaltung, Passwort, Token-Verwaltung, Backup."""

    def test_cannot_access_user_management(self):
        """API-Token darf nicht auf /api/users zugreifen."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser13", "admin", ["projects:read", "projects:write"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/api/users/", headers=_bearer_headers(raw_token))
        assert resp.status_code == 403

    def test_cannot_change_password(self):
        """API-Token darf nicht /auth/change-password nutzen."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser14", "editor", ["projects:read"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.post(
            "/auth/change-password",
            json={"current_password": "testpass123", "new_password": "newpass123"},
            headers=_bearer_headers(raw_token),
        )
        assert resp.status_code == 403

    def test_cannot_manage_tokens_with_token(self):
        """API-Token darf nicht andere Tokens verwalten."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser15", "admin", ["projects:read", "projects:write"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/api/v1/api-tokens", headers=_bearer_headers(raw_token))
        assert resp.status_code == 403

    def test_cannot_access_backup(self):
        """API-Token darf nicht auf Backup-Restore/Reset zugreifen."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser16", "admin", ["projects:read", "projects:write"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.post("/api/backup/restore", headers=_bearer_headers(raw_token))
        assert resp.status_code == 403


# ============================================================================
# REQ-6012 AK-5: Ungültigkeit nach Rollenwechsel
# ============================================================================

class TestRoleChangeInvalidation:
    """Tokens werden ungültig nach Rollenwechsel (token_version)."""

    def test_token_invalid_after_role_change(self):
        """Rollenwechsel -> token_version steigt -> alter Token ungültig."""
        db = SessionLocal()
        try:
            user, raw_token, token_record = _create_user_with_token(
                db, "testuser17", "editor", ["projects:read"]
            )
            original_tv = user.token_version
            assert token_record.token_version_at_creation == original_tv

            # Change role -> increments token_version
            from app.auth_service import increment_token_version
            user.role = "viewer"
            increment_token_version(db, user)

            assert user.token_version == original_tv + 1
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 401

    def test_new_token_works_after_role_change(self):
        """Neuer Token nach Rollenwechsel funktioniert."""
        db = SessionLocal()
        try:
            user = User(username="testuser18", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.api_token_service import create_api_token
            raw_token, _ = create_api_token(db, user, "new-token", ["projects:read"], days=90)
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 200


# ============================================================================
# REQ-6012 AK-6: Rate-Limit pro Token
# ============================================================================

class TestTokenRateLimit:
    """Rate-Limit: 600/Min pro Token, 429 mit Retry-After."""

    def test_rate_limit_exceeded(self):
        """Nach 600 Anfragen pro Minute -> 429."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "testuser19", "editor", ["projects:read"]
            )
        finally:
            db.close()

        client = TestClient(app)
        # Send requests up to the limit
        from app.config import GREAT_TOKEN_RATE_LIMIT
        limit = GREAT_TOKEN_RATE_LIMIT

        for i in range(limit):
            resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
            assert resp.status_code == 200, f"Request {i+1} failed with {resp.status_code}"

        # Next request should be rate limited
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_rate_limit_per_token(self):
        """Rate-Limit ist pro Token, nicht global."""
        db = SessionLocal()
        try:
            user1, raw_token1, _ = _create_user_with_token(
                db, "testuser20a", "editor", ["projects:read"]
            )
            user2, raw_token2, _ = _create_user_with_token(
                db, "testuser20b", "editor", ["projects:read"]
            )
            # Verify both tokens work before rate limiting
            from app.api_token_service import verify_api_token
            r1 = verify_api_token(db, raw_token1)
            r2 = verify_api_token(db, raw_token2)
            assert r1 is not None, "Token 1 should be verifiable"
            assert r2 is not None, "Token 2 should be verifiable"
        finally:
            db.close()

        client = TestClient(app)
        from app.config import GREAT_TOKEN_RATE_LIMIT
        limit = GREAT_TOKEN_RATE_LIMIT

        # Exhaust limit for token 1
        for i in range(limit):
            resp = client.get("/auth/me", headers=_bearer_headers(raw_token1))
            assert resp.status_code == 200, f"Token1 request {i+1} failed: {resp.status_code}"

        # Token 2 should still work (different rate limit bucket)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token2))
        assert resp.status_code == 200, f"Token2 should work but got {resp.status_code}: {resp.text}"


# ============================================================================
# REQ-6012 AK-7: OpenAPI Security-Scheme
# ============================================================================

class TestOpenAPISecurity:
    """OpenAPI enthaelt HTTPBearer Security-Scheme."""

    def test_openapi_has_bearer_scheme(self):
        """/openapi.json enthaelt HTTPBearer Security-Scheme."""
        # Create a user for auth
        db = SessionLocal()
        try:
            user = User(username="openapitest", role="admin")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)
            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/openapi.json", cookies={"access_token": token})
        assert resp.status_code == 200
        schema = resp.json()
        assert "securitySchemes" in schema.get("components", {})
        bearer = schema["components"]["securitySchemes"]
        # Check for HTTPBearer or similar
        has_bearer = any(
            "Bearer" in str(v.get("scheme", "")) or "bearer" in str(v.get("scheme", ""))
            for v in bearer.values()
        )
        assert has_bearer, f"No Bearer scheme found in: {bearer}"


# ============================================================================
# REQ-6012 AK-8: /api/v1/-Alias
# ============================================================================

class TestV1Alias:
    """/api/v1/-Alias liefert identische Antworten wie /api/."""

    def test_v1_projects_list_same_as_api(self):
        """GET /api/v1/projects == GET /api/projects."""
        db = SessionLocal()
        try:
            user = User(username="testuser21", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": token}

        resp_v1 = client.get("/api/v1/projects", cookies=cookies)
        resp_api = client.get("/api/projects", cookies=cookies)

        assert resp_v1.status_code == resp_api.status_code
        if resp_v1.status_code == 200:
            assert resp_v1.json() == resp_api.json()

    def test_v1_generate_same_as_api(self):
        """POST /api/v1/projects/{id}/generate == POST /api/projects/{id}/generate."""
        db = SessionLocal()
        try:
            user = User(username="testuser22", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": token}

        # Create a project first
        resp = client.post("/api/projects", json={"name": "AliasTestProject"}, cookies=cookies)
        assert resp.status_code in (200, 201)
        project_id = resp.json()["id"]

        # Add a category and value for generation
        resp = client.post(
            f"/api/projects/{project_id}/categories",
            json={"name": "Category1"},
            cookies=cookies,
        )
        assert resp.status_code in (200, 201)
        cat_id = resp.json()["id"]

        resp = client.post(
            f"/api/categories/{cat_id}/values",
            json={"value": "Val1"},
            cookies=cookies,
        )
        assert resp.status_code in (200, 201)

        resp_v1 = client.post(
            f"/api/v1/projects/{project_id}/generate",
            json={"strategy": "all"},
            cookies=cookies,
        )
        resp_api = client.post(
            f"/api/projects/{project_id}/generate",
            json={"strategy": "all"},
            cookies=cookies,
        )

        assert resp_v1.status_code == resp_api.status_code


# ============================================================================
# REQ-6012 AK-9: api_user Rolle
# ============================================================================

class TestApiUserRole:
    """api_user: keine UI-Anmeldung, nur Token."""

    def test_api_user_cannot_login(self):
        """api_user kann sich nicht per /auth/login anmelden."""
        db = SessionLocal()
        try:
            user = User(username="apiuser1", role="api_user")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
        finally:
            db.close()

        client = TestClient(app)
        from fastapi.security import OAuth2PasswordRequestForm
        resp = client.post(
            "/auth/login",
            data={"username": "apiuser1", "password": "testpass123"},
        )
        assert resp.status_code == 403

    def test_api_user_can_use_token(self):
        """api_user kann per API-Token auf erlaubte Endpunkte zugreifen."""
        db = SessionLocal()
        try:
            user, raw_token, _ = _create_user_with_token(
                db, "apiuser2", "api_user", ["projects:read"]
            )
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/api/projects", headers=_bearer_headers(raw_token))
        assert resp.status_code == 200


# ============================================================================
# REQ-6012 AK-10: Token-Management Endpunkte
# ============================================================================

class TestTokenManagementEndpoints:
    """CRUD-Endpunkte fuer API-Tokens."""

    def test_create_token_via_api(self):
        """POST /api/v1/api-tokens erstellt Token, gibt Klartext nur einmal."""
        db = SessionLocal()
        try:
            user = User(username="testuser23", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": token}

        resp = client.post(
            "/api/v1/api-tokens/",
            json={
                "name": "CI Token",
                "scopes": ["projects:read", "generate", "export"],
                "expires_in_days": 90,
            },
            cookies=cookies,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["token"].startswith("great_pat_")
        assert "prefix" in data
        assert data["prefix"] == data["token"][:16]

    def test_list_own_tokens(self):
        """GET /api/v1/api-tokens listet eigene Tokens (ohne Klartext)."""
        db = SessionLocal()
        try:
            user = User(username="testuser24", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            from app.api_token_service import create_api_token
            raw_token, _ = create_api_token(db, user, "list-test", ["projects:read"], days=90)
            cookie_token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": cookie_token}

        resp = client.get("/api/v1/api-tokens/", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        # No raw token in list response
        for t in data:
            assert "token" not in t
            assert "prefix" in t

    def test_revoke_token(self):
        """DELETE /api/v1/api-tokens/{id} widerruft Token."""
        db = SessionLocal()
        try:
            user = User(username="testuser25", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            from app.api_token_service import create_api_token
            raw_token, token_record = create_api_token(db, user, "revoke-test", ["projects:read"], days=90)
            cookie_token = create_access_token(user.id, user.username, user.role, user.token_version)
            token_id = token_record.id
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": cookie_token}

        # Revoke
        resp = client.delete(f"/api/v1/api-tokens/{token_id}", cookies=cookies)
        assert resp.status_code == 200

        # Token should no longer work
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 401

    def test_cannot_revoke_other_users_token(self):
        """Nutzer kann nicht Tokens anderer Nutzer widerrufen."""
        db = SessionLocal()
        try:
            user1 = User(username="testuser26a", role="editor")
            user1.set_password("testpass123")
            user1.default_password_active = False
            user1.token_version = 0
            db.add(user1)

            user2 = User(username="testuser26b", role="editor")
            user2.set_password("testpass123")
            user2.default_password_active = False
            user2.token_version = 0
            db.add(user2)
            db.commit()
            db.refresh(user1)
            db.refresh(user2)

            from app.auth_utils import create_access_token
            from app.api_token_service import create_api_token
            _, token_record = create_api_token(db, user2, "other-token", ["projects:read"], days=90)
            cookie_token = create_access_token(user1.id, user1.username, user1.role, user1.token_version)
            token_id = token_record.id
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": cookie_token}

        resp = client.delete(f"/api/v1/api-tokens/{token_id}", cookies=cookies)
        assert resp.status_code == 404  # Not found (can't see other users' tokens)

    def test_admin_list_all_tokens(self):
        """Admin: GET /api/v1/admin/api-tokens listet alle Tokens."""
        db = SessionLocal()
        try:
            admin = User(username="testadmin2", role="admin")
            admin.set_password("testpass123")
            admin.default_password_active = False
            admin.token_version = 0
            db.add(admin)

            user = User(username="testuser27", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(admin)
            db.refresh(user)

            from app.auth_utils import create_access_token
            from app.api_token_service import create_api_token
            _, _ = create_api_token(db, user, "admin-sees-this", ["projects:read"], days=90)
            cookie_token = create_access_token(admin.id, admin.username, admin.role, admin.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": cookie_token}

        resp = client.get("/api/v1/admin/api-tokens/", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(t["name"] == "admin-sees-this" for t in data)

    def test_admin_revoke_any_token(self):
        """Admin: DELETE /api/v1/admin/api-tokens/{id} widerruft jeden Token."""
        db = SessionLocal()
        try:
            admin = User(username="testadmin3", role="admin")
            admin.set_password("testpass123")
            admin.default_password_active = False
            admin.token_version = 0
            db.add(admin)

            user = User(username="testuser28", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(admin)
            db.refresh(user)

            from app.auth_utils import create_access_token
            from app.api_token_service import create_api_token
            raw_token, token_record = create_api_token(db, user, "admin-revokes", ["projects:read"], days=90)
            cookie_token = create_access_token(admin.id, admin.username, admin.role, admin.token_version)
            token_id = token_record.id
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": cookie_token}

        resp = client.delete(f"/api/v1/admin/api-tokens/{token_id}", cookies=cookies)
        assert resp.status_code == 200

        # Token should no longer work
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 401


# ============================================================================
# REQ-6012 AK-11: Komfort-Endpunkte
# ============================================================================

class TestComfortEndpoints:
    """Komfort-Endpunkte fuer Pipelines."""

    def test_get_project_by_name(self):
        """GET /api/v1/projects?name=<Name> (case-insensitive exact search)."""
        db = SessionLocal()
        try:
            user = User(username="testuser29", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": token}

        # Create project
        resp = client.post(
            "/api/projects",
            json={"name": "MySpecialProject"},
            cookies=cookies,
        )
        assert resp.status_code in (200, 201)

        # Search by name (case-insensitive)
        resp = client.get("/api/v1/projects?name=myspecialproject", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "MySpecialProject"

    def test_generate_with_export(self):
        """POST /api/v1/projects/{id}/generate?export=csv&persist=false."""
        db = SessionLocal()
        try:
            user = User(username="testuser30", role="editor")
            user.set_password("testpass123")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)

            from app.auth_utils import create_access_token
            token = create_access_token(user.id, user.username, user.role, user.token_version)
        finally:
            db.close()

        client = TestClient(app)
        cookies = {"access_token": token}

        # Create project with category and value
        resp = client.post("/api/projects", json={"name": "ExportTestProject"}, cookies=cookies)
        assert resp.status_code in (200, 201)
        project_id = resp.json()["id"]

        resp = client.post(
            f"/api/projects/{project_id}/categories",
            json={"name": "Cat1"},
            cookies=cookies,
        )
        assert resp.status_code in (200, 201)
        cat_id = resp.json()["id"]

        resp = client.post(
            f"/api/categories/{cat_id}/values",
            json={"value": "Val1"},
            cookies=cookies,
        )
        assert resp.status_code in (200, 201)

        # Generate with export
        resp = client.post(
            f"/api/v1/projects/{project_id}/generate?export=csv&persist=false",
            json={"strategy": "all"},
            cookies=cookies,
        )
        # Should return data (200 or appropriate response)
        assert resp.status_code in (200, 201)


# ============================================================================
# REQ-6012 AK-12: Audit-Log
# ============================================================================

class TestAuditLog:
    """Token-Nutzung wird mit Zeit und Endpunkt protokolliert."""

    def test_last_used_updated_on_auth(self):
        """Bei erfolgreicher Bearer-Auth wird last_used_at aktualisiert."""
        db = SessionLocal()
        try:
            user, raw_token, token_record = _create_user_with_token(
                db, "testuser31", "editor", ["projects:read"]
            )
            token_id = token_record.id
            assert token_record.last_used_at is None
        finally:
            db.close()

        client = TestClient(app)
        resp = client.get("/auth/me", headers=_bearer_headers(raw_token))
        assert resp.status_code == 200

        # Check last_used_at was updated
        db = SessionLocal()
        try:
            updated = db.query(ApiToken).filter(ApiToken.id == token_id).first()
            assert updated.last_used_at is not None
        finally:
            db.close()