"""REQ-3063: Fehlerwert-Spalte in Export-Formaten (JSON, CSV, Excel)."""

import uuid


def _create_project_with_error_value(auth_client) -> tuple[int, int]:
    """Erstellt Projekt mit Kategorie (einen Fehlerwert) und Generierung. Gibt (pid, gen_id)."""
    name = f"ExportFehlerwert-{uuid.uuid4().hex[:6]}"
    r = auth_client.post("/api/projects", json={"name": name})
    assert r.status_code == 200
    pid = r.json()["id"]

    # Kategorie anlegen
    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "OS", "order_index": 0})
    assert r.status_code == 200
    cid = r.json()["id"]

    # Normalen Wert und Fehlerwert anlegen
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "Windows"})
    r = auth_client.post(f"/api/categories/{cid}/values", json={"value": "BrokenOS"})
    assert r.status_code == 200
    broken_val_id = r.json()["id"]

    # Fehlerwert markieren (allowed=False)
    r = auth_client.patch(f"/api/values/{broken_val_id}/properties", json={"allowed": False})
    assert r.status_code == 200

    # Generiere Testfaelle (All Combinations = 2 Testfaelle)
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 200, f"Generierung fehlgeschlagen: {r.text}"
    gen_id = r.json()["generation_id"]
    return pid, gen_id


def test_json_export_enthaelt_has_error_value(auth_client):
    """REQ-3063: JSON-Export enthaelt has_error_value pro Testfall."""
    pid, gen_id = _create_project_with_error_value(auth_client)

    resp = auth_client.get(f"/api/generations/{gen_id}/export/json")
    assert resp.status_code == 200
    data = resp.json()

    assert "testcases" in data
    assert len(data["testcases"]) == 2

    # Pruefe has_error_value Feld
    error_cases = [tc for tc in data["testcases"] if tc.get("has_error_value")]
    normal_cases = [tc for tc in data["testcases"] if not tc.get("has_error_value")]

    assert len(error_cases) == 1, "Genau ein Testfall sollte als Fehlerwert markiert sein"
    assert len(normal_cases) == 1, "Genau ein Testfall sollte normal sein"

    # Der Fehlerwert-Testfall sollte 'BrokenOS' enthalten
    assert "BrokenOS" in error_cases[0]["assignments"].values()


def test_csv_export_enthaelt_fehlerwert_spalte(auth_client):
    """REQ-3063: CSV-Export enthaelt 'Fehlerwert'-Spalte."""
    pid, gen_id = _create_project_with_error_value(auth_client)

    resp = auth_client.get(f"/api/generations/{gen_id}/export/csv")
    assert resp.status_code == 200

    content = resp.text
    lines = [l for l in content.split("\r\n") if l.strip()]

    # Erste Zeile ist 'sep=;' fuer Excel
    header_line = lines[1]  # Zweite Zeile ist der Header
    assert "Fehlerwert" in header_line, f"Header sollte 'Fehlerwert' enthalten: {header_line}"

    # Pruefe dass 'JA' und 'NEIN' in den Datenzeilen vorkommen
    data_lines = [l for l in lines[2:] if l.strip()]
    ja_count = sum(1 for l in data_lines if "JA" in l)
    nein_count = sum(1 for l in data_lines if "NEIN" in l)

    assert ja_count == 1, "Genau eine Zeile sollte 'JA' haben"
    assert nein_count == 1, "Genau eine Zeile sollte 'NEIN' haben"


def test_excel_export_enthaelt_fehlerwert_spalte(auth_client):
    """REQ-3063: Excel-Export enthaelt 'Fehlerwert'-Spalte."""
    import io
    try:
        import openpyxl
    except ImportError:
        import pytest
        pytest.skip("openpyxl nicht installiert")

    pid, gen_id = _create_project_with_error_value(auth_client)

    resp = auth_client.get(f"/api/generations/{gen_id}/export/xlsx")
    assert resp.status_code == 200

    wb = openpyxl.load_workbook(io.BytesIO(resp.content))
    ws = wb.active

    # Header-Zeile lesen
    headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    assert "Fehlerwert" in headers, f"'Fehlerwert' sollte in Header sein: {headers}"

    # Datenzeilen lesen
    error_col_idx = headers.index("Fehlerwert") + 1
    ja_count = 0
    nein_count = 0
    for row_idx in range(2, ws.max_row + 1):
        val = ws.cell(row=row_idx, column=error_col_idx).value
        if val == "JA":
            ja_count += 1
        elif val == "NEIN":
            nein_count += 1

    assert ja_count == 1, "Genau eine Zeile sollte 'JA' haben"
    assert nein_count == 1, "Genau eine Zeile sollte 'NEIN' haben"