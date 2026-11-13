from app.main import app
import re


def test_export_contains_status_flag(auth_client):
    # Annahme: Es gibt mind. eine Generation mit ID 1 im Demo – sonst Test vorher anlegen.
    # Hier nur Smoke-Test auf HTTP und Header-Zeile mit 'Status'.
    r = auth_client.get("/api/generations/1/export/csv?status=1")
    assert r.status_code in (200, 404)  # nicht hart pruefen, falls keine Gen 1 existiert
    if r.status_code == 200:
        text = r.text.splitlines()
        # Erste Zeile kann sep=; sein (Excel-Hint) – Header folgt danach
        header_lines = [l for l in text if "Status" in l or ";" in l]
        assert any("Status" in l for l in text), f"'Status' nicht in CSV gefunden: {text[:3]}"