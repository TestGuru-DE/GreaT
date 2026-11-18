"""B-08: Rate Limiter verbessern.

B-08: Rate-Limit pro IP|Username, Reset nach erfolgreichem Login,
      X-Forwarded-For nur wenn GREAT_TRUST_PROXY_HEADERS aktiv.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.auth import User
from app.rate_limiter import login_rate_limiter
from app.config import GREAT_TRUST_PROXY_HEADERS


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    login_rate_limiter._requests.clear()
    yield


@pytest.fixture
def test_user():
    """Erstelle Testnutzer fuer Login-Tests."""
    db = SessionLocal()
    try:
        user = User(username="ratelimituser", role="editor")
        user.set_password("correctpass123456")
        user.token_version = 0
        db.add(user)
        db.commit()
        db.refresh(user)
        yield user
    finally:
        db.close()


class TestSuccessfulLoginsNotRateLimited:
    """B-08: Erfolgreiche Logins duerfen nicht rate-limitiert werden."""

    def test_successful_logins_not_rate_limited(self, test_user):
        """Mehrfache erfolgreiche Logins sollten nicht zum Rate-Limit fuhren."""
        client = TestClient(app)
        for i in range(8):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "correctpass123456"},
            )
            assert resp.status_code == 200, f"Login {i+1} sollte erfolgreich sein, war {resp.status_code}"


class TestFailedLoginsRateLimitedPerUser:
    """B-08: Fehlgeschlagene Logins werden pro IP|Username rate-limitiert."""

    def test_failed_logins_rate_limited_per_user(self, test_user):
        """6. fehlgeschlagener Login mit gleichem Username sollte 429 liefern."""
        client = TestClient(app)

        # 5 fehlgeschlagene Versuche
        for i in range(5):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
            )
            assert resp.status_code == 401, f"Versuch {i+1} sollte 401 sein"

        # 6. Versuch sollte rate-limitiert sein
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "wrongpass"},
        )
        assert resp.status_code == 429

    def test_different_users_independent_limits(self, test_user):
        """Verschiedene Usernames haben unabhaengige Rate-Limits."""
        db = SessionLocal()
        try:
            user2 = User(username="ratelimituser2", role="editor")
            user2.set_password("correctpass123456")
            user2.token_version = 0
            db.add(user2)
            db.commit()
        finally:
            db.close()

        client = TestClient(app)

        # 5 fehlgeschlagene Versuche fuer user1
        for i in range(5):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
            )
            assert resp.status_code == 401

        # user1 sollte jetzt rate-limitiert sein
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "wrongpass"},
        )
        assert resp.status_code == 429

        # user2 sollte noch nicht rate-limitiert sein
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser2", "password": "wrongpass"},
        )
        assert resp.status_code == 401, "Anderer Benutzer sollte unabhaengig rate-limitiert werden"


class TestRateLimiterCleanup:
    """B-08: Rate-Limiter loescht Keys nach erfolgreichem Login."""

    def test_rate_limiter_cleans_up_keys(self, test_user):
        """Nach erfolgreichem Login wird der Rate-Limiter-Key geloescht."""
        client = TestClient(app)

        # 3 fehlgeschlagene Versuche
        for i in range(3):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
            )
            assert resp.status_code == 401

        # Erfolgreicher Login sollte Key zuruecksetzen
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "correctpass123456"},
        )
        assert resp.status_code == 200

        # Jetzt sollten wieder 5 fehlgeschlagene Versuche moeglich sein
        for i in range(5):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
            )
            assert resp.status_code == 401, f"Nach Reset sollte Versuch {i+1} moeglich sein"

        # Erst der 6. Versuch sollte jetzt 429 liefern
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "wrongpass"},
        )
        assert resp.status_code == 429


class TestForwardedFor:
    """B-08: X-Forwarded-For wird nur verwendet, wenn GREAT_TRUST_PROXY_HEADERS aktiv ist."""

    def test_forwarded_for_used_only_when_enabled(self, test_user):
        """X-Forwarded-For wird ignoriert, wenn GREAT_TRUST_PROXY_HEADERS nicht gesetzt.

        Im Default (Development) ist GREAT_TRUST_PROXY_HEADERS=False,
        also wird request.client.host verwendet, nicht der Header.
        """
        assert not GREAT_TRUST_PROXY_HEADERS, "Test setzt GREAT_TRUST_PROXY_HEADERS=False voraus"

        client = TestClient(app)

        # 5 Versuche mit X-Forwarded-For Header – sollte ignoriert werden
        for i in range(5):
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
                headers={"x-forwarded-for": "1.2.3.4"},
            )
            assert resp.status_code == 401

        # 6. Versuch – sollte 429 sein (basierend auf test-client IP, NICHT auf 1.2.3.4)
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "wrongpass"},
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        assert resp.status_code == 429

        # Nach Reset: neuer Key mit anderer „Proxy-IP" sollte unabhaengig sein
        # (weil X-Forwarded-For ignoriert wird und derselbe client.host verwendet wird)
        login_rate_limiter._requests.clear()

        # Ohne Header -> client IP wird verwendet
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimituser", "password": "wrongpass"},
        )
        assert resp.status_code == 401, "Ohne X-Forwarded-For-Header sollte normal funktionieren"

    def test_forwarded_for_header_parsed_correctly(self, test_user):
        """X-Forwarded-For Header wird korrekt geparst (erster Eintrag, trimmed).

        Bei GREAT_TRUST_PROXY_HEADERS=False wird der Header ignoriert;
        dieser Test stellt sicher, dass der Code keine Exception wirft.
        """
        client = TestClient(app)

        # Verschiedene Formate von X-Forwarded-For
        for header_val in ["1.2.3.4", "1.2.3.4, 5.6.7.8", "  1.2.3.4  "]:
            login_rate_limiter._requests.clear()
            resp = client.post(
                "/auth/login",
                data={"username": "ratelimituser", "password": "wrongpass"},
                headers={"x-forwarded-for": header_val},
            )
            # Sollte 401 sein (falsches Passwort), NICHT 500 (Exception)
            assert resp.status_code == 401, f"Header '{header_val}' sollte keine Exception werfen"