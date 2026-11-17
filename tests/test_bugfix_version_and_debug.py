"""Tests: Version an einer Stelle, Debug-Endpunkte entfernen, 503 bei fehlendem Frontend.

BUG B-30: /health meldet falsche Version (1.5.2 statt 1.8.0)
BUG B-31: / leitet auf nicht-existenten HTMX-Pfad um
BUG B-41: /whoami ist ungesicherter Debug-Endpunkt
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


class TestVersionCentralization:
    """BUG B-30: Version muss an einer zentralen Stelle definiert sein."""

    def test_health_version_matches_app_version(self):
        """app.version und /health version muessen mit __version__ uebereinstimmen."""
        from app.version import __version__

        assert app.version == __version__, (
            f"app.version={app.version} != __version__={__version__}"
        )

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == __version__, (
            f"/health version={data.get('version')} != {__version__}"
        )

    def test_frontend_package_version_matches_backend(self):
        """frontend/package.json Version muss zu __version__ passen."""
        from app.version import __version__

        pkg_path = Path(__file__).parent.parent / "frontend" / "package.json"
        if not pkg_path.exists():
            pytest.skip("frontend/package.json nicht gefunden")

        pkg = json.loads(pkg_path.read_text())
        assert pkg.get("version") == __version__, (
            f"package.json version={pkg.get('version')} != {__version__}"
        )


class TestDebugEndpointsRemoved:
    """BUG B-41: /whoami Debug-Endpunkt muss entfernt sein."""

    def test_whoami_returns_404(self):
        """GET /whoami muss 404 liefern (Endpunkt entfernt)."""
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/whoami")
        assert r.status_code == 404

    def test_whoami_no_info_leak(self):
        """GET /whoami darf keine internen Pfade oder Routen offenlegen."""
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/whoami")
        assert r.status_code == 404
        # Sicherstellen, dass keine sensiblen Daten im Response koennten
        body = r.text.lower()
        assert "frontend_dist" not in body
        assert "__file__" not in body


class TestRootWithoutFrontend:
    """BUG B-31: / und /ui muessen 503 liefern wenn kein Frontend-Build vorhanden."""

    def test_root_without_frontend_returns_503(self):
        """GET / ohne Frontend-Build liefert 503 statt toter Redirect."""
        import app.main as main_module

        original = main_module.FRONTEND_DIST

        with patch.object(
            main_module,
            "FRONTEND_DIST",
            Path("/nonexistent/frontend/dist"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/")
            assert r.status_code == 503
            data = r.json()
            assert "detail" in data
            assert "nicht gebaut" in data["detail"] or "not built" in data["detail"]

    def test_ui_without_frontend_returns_503(self):
        """GET /ui ohne Frontend-Build liefert 503 statt toter Redirect."""
        import app.main as main_module

        with patch.object(
            main_module,
            "FRONTEND_DIST",
            Path("/nonexistent/frontend/dist"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/ui")
            assert r.status_code == 503
            data = r.json()
            assert "detail" in data

    def test_root_with_frontend_redirects_to_app(self):
        """GET / mit vorhandenem Frontend-Build leitet auf /app weiter."""
        import app.main as main_module

        original = main_module.FRONTEND_DIST

        if not original.exists():
            pytest.skip("Frontend-Build nicht vorhanden, Skip")

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 307
        assert "/app" in r.headers.get("location", "")

    def test_ui_with_frontend_redirects_to_app(self):
        """GET /ui mit vorhandenem Frontend-Build leitet auf /app weiter."""
        import app.main as main_module

        original = main_module.FRONTEND_DIST

        if not original.exists():
            pytest.skip("Frontend-Build nicht vorhanden, Skip")

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/ui", follow_redirects=False)
        assert r.status_code == 307
        assert "/app" in r.headers.get("location", "")

    def test_root_no_htmx_fallback(self):
        """GET / darf nicht mehr auf /ui/projects (HTMX) umleiten."""
        import app.main as main_module

        with patch.object(
            main_module,
            "FRONTEND_DIST",
            Path("/nonexistent/frontend/dist"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/", follow_redirects=False)
            assert r.status_code == 503
            # Kein Redirect auf /ui/projects mehr
            assert "/ui/projects" not in r.headers.get("location", "")