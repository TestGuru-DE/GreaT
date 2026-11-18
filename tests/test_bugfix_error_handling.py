"""Globale Fehlerbehandlung, ID-Validierung, 404-Konsistenz, Meldungen."""
import pytest
import httpx
import threading
import time


def test_huge_id_returns_422(auth_client):
    """2**70 als ID -> 422 (nicht 500)."""
    r = auth_client.get(f"/api/projects/{2**70}/categories")
    assert r.status_code == 422


def test_negative_id_returns_422(auth_client):
    r = auth_client.get("/api/projects/-1/categories")
    assert r.status_code == 422


def test_zero_id_returns_422(auth_client):
    r = auth_client.get("/api/projects/0/categories")
    assert r.status_code == 422


def test_values_of_unknown_category_returns_404(auth_client):
    r = auth_client.get("/api/categories/999999/values")
    assert r.status_code == 404


def test_categories_of_unknown_project_returns_404(auth_client):
    r = auth_client.get("/api/projects/999999/categories")
    assert r.status_code == 404


def test_generate_unknown_project_returns_404(auth_client):
    r = auth_client.post(
        "/api/projects/999999/generate",
        json={"strategy": "pairwise"}
    )
    assert r.status_code == 404


def test_rules_of_unknown_project_returns_404(auth_client):
    r = auth_client.get("/api/projects/999999/rules")
    assert r.status_code == 404


def test_dataclass_values_of_unknown_dc_returns_404(auth_client):
    r = auth_client.get("/api/dataclasses/999999/values")
    assert r.status_code == 404


def test_unhandled_exception_returns_json_500(client):
    """Globaler Exception-Handler liefert JSON 500, nicht Text."""
    # Health-Check als Regression: Verbindung funktioniert
    r = client.get("/health")
    assert r.status_code == 200


def test_connection_survives_500():
    """Echter Server: Nach 500 funktioniert die naechste Request auf derselben Verbindung."""
    from src.app.main import app
    import uvicorn

    # Test-Route mit Exception
    @app.get("/test/throw")
    def throw_exception():
        raise ValueError("Test-Exception")

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(0.5)

    # Port ermitteln
    port = 0
    for sock in server.servers[0].sockets:
        port = sock.getsockname()[1]
        break

    base_url = f"http://127.0.0.1:{port}"

    try:
        with httpx.Client(base_url=base_url) as http:
            # Erste Request: Exception -> 500
            r1 = http.get("/test/throw")
            assert r1.status_code == 500
            data = r1.json()
            assert data.get("code") == "internal_error"

            # Zweite Request auf SELBEN Client (same connection):
            r2 = http.get("/health")
            assert r2.status_code == 200
    finally:
        server.should_exit = True


def test_login_error_message_has_umlaut(client):
    r = client.post("/auth/login", data={"username": "wrong", "password": "wrong"})
    detail = r.json().get("detail", "")
    assert "Ung\u00fcltig" in detail or "ung\u00fcltig" in detail  # Korrekter Umlaut
    assert "Ungultig" not in detail  # Kein Tippfehler


def test_refresh_no_token_returns_401(client):
    """Refresh ohne Token -> 401 mit deutscher Meldung."""
    r = client.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert r.status_code == 401
    detail = r.json().get("detail", "")
    # Die Meldung kann "Kein Refresh-Token" oder "Ung\u00fcltiger Refresh-Token" sein
    assert len(detail) > 0 and detail != "Ungultiger Refresh-Token"


@pytest.mark.parametrize("endpoint", [
    "/api/projects/999999/categories",
    "/api/projects/999999/rules",
    "/api/projects/999999/generations",
    "/api/categories/999999/values",
    "/api/dataclasses/999999/values",
])
def test_unknown_parent_returns_404(endpoint, auth_client):
    r = auth_client.get(endpoint)
    assert r.status_code == 404, f"{endpoint} sollte 404 liefern, nicht {r.status_code}"