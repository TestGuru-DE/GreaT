from fastapi.testclient import TestClient

from app.main import app


def test_production_frontend_uses_no_cache_headers_for_html():
    # REQ-1202
    with TestClient(app) as client:
        response = client.get('/app')
        assert response.status_code == 200
        cache = response.headers.get('Cache-Control', '').lower()
        assert 'no-cache' in cache or 'no-store' in cache
        assert 'must-revalidate' in cache
