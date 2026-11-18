# REQ-1000: CSV-Export via Web-API
#
# Testet den Endpunkt GET /api/generations/{id}/export/csv
# gegen die aktive Web-Anwendung (FastAPI).
#
# Dies ersetzt die alten Tests gegen src/io_handlers/csv_handler.py,
# welche mit dem Desktop-Altcode (TaNoS) archiviert wurden.

import uuid


def test_req1000_csv_export_web(auth_client):
    """REQ-1000: CSV-Export einer Generierung via Web-API."""

    # 1) Projekt anlegen
    project_name = f"REQ1000-{uuid.uuid4().hex[:6]}"
    r = auth_client.post("/api/projects", json={"name": project_name})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    # 2) Kategorien & Werte
    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Gewicht", "order_index": 0})
    assert r.status_code == 200
    cid_w = r.json()["id"]
    r = auth_client.post(f"/api/categories/{cid_w}/values", json={"value": "500g"})
    assert r.status_code == 200
    r = auth_client.post(f"/api/categories/{cid_w}/values", json={"value": "1000g"})
    assert r.status_code == 200

    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Farbe", "order_index": 1})
    assert r.status_code == 200
    cid_f = r.json()["id"]
    r = auth_client.post(f"/api/categories/{cid_f}/values", json={"value": "Rot"})
    assert r.status_code == 200
    r = auth_client.post(f"/api/categories/{cid_f}/values", json={"value": "Blau"})
    assert r.status_code == 200

    # 3) Generieren (each – minimale Testfaelle)
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    assert r.status_code == 200, r.text
    gen_id = r.json()["generation_id"]

    # 4) CSV-Export
    r = auth_client.get(f"/api/generations/{gen_id}/export/csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")

    # CSV enthaelt Kategorienamen als Spalten
    body = r.text
    assert "Gewicht" in body
    assert "Farbe" in body

    # CSV enthaelt mindestens einen Wert pro Kategorie
    assert "500g" in body or "1000g" in body
    assert "Rot" in body or "Blau" in body


def test_req1000_csv_export_web_404(auth_client):
    """REQ-1000: CSV-Export fuer nicht-existenten Generierungs-ID -> 404."""
    r = auth_client.get("/api/generations/999999/export/csv")
    assert r.status_code == 404


def test_req1000_csv_export_web_with_status(auth_client):
    """REQ-1000: CSV-Export mit ?status=1 (Fehlerwert-Spalte)."""

    project_name = f"REQ1000S-{uuid.uuid4().hex[:6]}"
    r = auth_client.post("/api/projects", json={"name": project_name})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "K1", "order_index": 0})
    assert r.status_code == 200
    cid = r.json()["id"]
    r = auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    assert r.status_code == 200
    r = auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    assert r.status_code == 200

    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    assert r.status_code == 200, r.text
    gen_id = r.json()["generation_id"]

    r = auth_client.get(f"/api/generations/{gen_id}/export/csv?status=1")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "K1" in r.text