# B-05: Formel-Injection im Export verhindern
# B-35: CSV-Export akzeptiert encoding=latin-1 Alias
# TDD: Tests VOR der Implementierung.
import io
import uuid

import pytest

# ---------------------------------------------------------------------------
# Unit-Tests fuer escape_spreadsheet_value (B-05)
# ---------------------------------------------------------------------------


class TestEscapeSpreadsheetValue:
    """Unit-Tests fuer escape_spreadsheet_value – B-05."""

    def test_escape_equals_formula(self):
        # Werte mit = am Anfang muessen escaped werden
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('=HYPERLINK("http://evil.com")') == "'=HYPERLINK(\"http://evil.com\")"

    def test_escape_plus_formula(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('+SUM(1,2)') == "'+SUM(1,2)"

    def test_escape_at_formula(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('@cmd') == "'@cmd"

    def test_escape_minus_formula(self):
        # -2+3 ist keine reine Zahl (hat + drin), also escapen
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('-2+3') == "'-2+3"

    def test_escape_tab_start(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('\ttest') == "'\ttest"

    def test_escape_cr_start(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('\rtest') == "'\rtest"

    def test_escape_numbers_unchanged_negative(self):
        # Reine negative Zahl bleibt unveraendert
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('-1') == '-1'

    def test_escape_numbers_unchanged_positive(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('+5') == '+5'

    def test_escape_numbers_unchanged_decimal_comma(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('-0,5') == '-0,5'

    def test_escape_numbers_unchanged_decimal_dot(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('3.14') == '3.14'

    def test_escape_numbers_unchanged_plain(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('123') == '123'

    def test_escape_normal_text_unchanged(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('normal') == 'normal'

    def test_escape_empty_string(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('') == ''

    def test_escape_alphanumeric_unchanged(self):
        # 123abc beginnt mit Ziffer, ist keine reine Zahl -> kein Escape
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value('123abc') == '123abc'

    def test_escape_none_returns_none(self):
        from app.export_utils import escape_spreadsheet_value
        assert escape_spreadsheet_value(None) is None  # type: ignore[arg-type]

    def test_escape_non_string_returns_unchanged(self):
        from app.export_utils import escape_spreadsheet_value
        # Integers etc. werden unveraendert zurueckgegeben
        assert escape_spreadsheet_value(42) == 42  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Integrationstests: CSV-Export (B-05, B-35)
# ---------------------------------------------------------------------------


def _create_project_with_formula_values(auth_client) -> tuple[int, int]:
    """Projekt mit Werten die als Formel interpretiert werden koennen."""
    name = f"FormulaExport-{uuid.uuid4().hex[:6]}"
    r = auth_client.post("/api/projects", json={"name": name})
    assert r.status_code == 200
    pid = r.json()["id"]

    # Kategorie mit Formel-Werten
    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Input", "order_index": 0})
    assert r.status_code == 200
    cid = r.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": '=HYPERLINK("http://evil.com")'})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "+SUM(1,2)"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "normal_value"})

    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    assert r.status_code == 200
    gen_id = r.json()["generation_id"]
    return pid, gen_id


class TestCSVExportFormulaProtection:
    """CSV-Export schuetzt vor Formel-Injection – B-05."""

    def test_csv_formula_values_escaped(self, auth_client):
        # B-05: Werte mit = oder + am Anfang muessen im CSV escaped sein
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/csv")
        assert r.status_code == 200
        text = r.text
        # Der Wert =HYPERLINK... sollte mit Apostroph escaped sein
        assert "'=HYPERLINK" in text
        # Der Wert +SUM... sollte mit Apostroph escaped sein
        assert "'+SUM" in text
        # Normaler Wert bleibt unveraendert
        assert "normal_value" in text

    def test_csv_encoding_latin1_alias_accepted(self, auth_client):
        # B-35: encoding=latin-1 muss akzeptiert werden
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/csv?encoding=latin-1")
        assert r.status_code == 200

    def test_csv_encoding_latin1_without_dash_accepted(self, auth_client):
        # B-35: encoding=latin1 (ohne Bindestrich) muss auch akzeptiert werden
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/csv?encoding=latin1")
        assert r.status_code == 200

    def test_csv_encoding_iso8859_1_accepted(self, auth_client):
        # iso-8859-1 (canonical) muss natuerlich funktionieren
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/csv?encoding=iso-8859-1")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Integrationstests: XLSX-Export (B-05)
# ---------------------------------------------------------------------------


class TestXLSXExportFormulaProtection:
    """XLSX-Export schuetzt vor Formel-Injection – B-05."""

    def test_xlsx_formula_cell_is_string(self, auth_client):
        # B-05: Zellen mit Formel-Startzeichen muessen als String markiert sein
        import openpyxl
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/xlsx")
        assert r.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active

        # Finde die Zellen mit Formel-Werten in den Datenzeilen (ab Zeile 2)
        for row_idx in range(2, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=1)  # Erste Kategorie-Spalte
            if cell.value and str(cell.value).startswith(("=", "+", "@")):
                # Die Zelle sollte als String markiert sein
                assert cell.data_type == "s", f"Cell ({row_idx},1) value '{cell.value}' should be string type, got {cell.data_type}"
            elif cell.value and str(cell.value).startswith("-") and not str(cell.value).lstrip("-").isdigit():
                # Formel-Wert mit -
                assert cell.data_type == "s"

    def test_xlsx_normal_values_work(self, auth_client):
        # Normaler Export sollte weiterhin funktionieren
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/xlsx")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Integrationstests: JSON-Export bleibt unveraendert (B-05)
# ---------------------------------------------------------------------------


class TestJSONExportUnchanged:
    """JSON-Export bleibt unveraendert – B-05 (keine Escape-Logik)."""

    def test_json_export_unchanged(self, auth_client):
        _, gen_id = _create_project_with_formula_values(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/json")
        assert r.status_code == 200
        data = r.json()
        # JSON-Werte sollten roh sein, keine Apostrophe
        for tc in data["testcases"]:
            for val in tc["assignments"].values():
                assert not val.startswith("'"), f"JSON value '{val}' should not be escaped"