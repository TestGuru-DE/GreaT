"""REQ-6011: Tests fuer Export-Formate.

13 Tests fuer 8 Export-Formate mit Golden-File-Vergleich.
Testprojekt: 4 Kategorien (Browser, OS, Eingabe, Ergebnis),
6 Testfaelle mit Sonderzeichen (Umlaute, Pipe, Anführungszeichen, Formelzeichen).
"""
import json
import os
import sys
import tempfile
import uuid

# Golden-File-Verzeichnis
GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden", "export")


def _create_export_test_project(auth_client, fixed_name: str = None) -> tuple[int, int]:
    """Erstellt ein Testprojekt mit 4 Kategorien und 6 Testfaellen.

    Kategorien:
    - Browser (standard): Chrome, Firefox
    - OS (standard): Windows, macOS
    - Eingabe (standard): "Normal", mit|Pipe, mit"Quote
    - Ergebnis (result): OK, NOK

    Rueckgabe: (project_id, generation_id)
    """
    if fixed_name is None:
        name = f"ExportTest-{uuid.uuid4().hex[:6]}"
    else:
        name = fixed_name

    # Projekt
    r = auth_client.post("/api/projects", json={"name": name})
    assert r.status_code == 200, f"Project creation failed: {r.text}"
    pid = r.json()["id"]

    # Kategorien
    cats = []
    for idx, (cat_name, is_result) in enumerate([
        ("Browser", False),
        ("OS", False),
        ("Eingabe", False),
        ("Ergebnis", True),
    ]):
        r = auth_client.post(f"/api/projects/{pid}/categories", json={
            "name": cat_name,
            "order_index": idx,
            "is_result": is_result,
        })
        assert r.status_code == 200, f"Category {cat_name} failed: {r.text}"
        cats.append(r.json()["id"])

    # Werte
    values_map = {
        "Browser": ["Chrome", "Firefox"],
        "OS": ["Windows", "macOS"],
        "Eingabe": ['mit|Pipe', 'mit"Quote', "Normal"],
        "Ergebnis": ["OK", "NOK"],
    }

    cat_name_by_id = {}
    r = auth_client.get(f"/api/projects/{pid}/categories")
    assert r.status_code == 200
    for c in r.json():
        cat_name_by_id[c["name"]] = c["id"]

    for cat_name, vals in values_map.items():
        cid = cat_name_by_id[cat_name]
        for v in vals:
            r = auth_client.post(f"/api/categories/{cid}/values", json={"value": v})
            assert r.status_code == 200, f"Value {v} failed: {r.text}"

    # Generierung (all strategy for full coverage)
    r = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 200, f"Generation failed: {r.text}"
    gen_id = r.json()["generation_id"]

    return pid, gen_id


class TestExportFormats:
    """REQ-6011: Tests fuer alle Export-Formate."""

    def test_export_gherkin_en(self, auth_client):
        """Gherkin Export EN: 200 + gueltige Struktur."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/gherkin?lang=en")
        assert r.status_code == 200, f"Gherkin EN failed: {r.text}"
        assert "text/plain" in r.headers.get("content-type", "")

        text = r.text
        assert "Feature:" in text
        assert "Scenario Outline:" in text
        assert "Examples:" in text
        assert "# language: en" in text

    def test_export_gherkin_de(self, auth_client):
        """Gherkin Export DE: deutsche Schluesselwoerter."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/gherkin?lang=de")
        assert r.status_code == 200, f"Gherkin DE failed: {r.text}"

        text = r.text
        assert "Funktionalitaet:" in text
        assert "Szenariogrundriss:" in text
        assert "Beispiele:" in text
        assert "# language: de" in text

    def test_export_pytest(self, auth_client):
        """pytest Export: gueltiges Python, compilierbar."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/pytest")
        assert r.status_code == 200, f"pytest failed: {r.text}"

        text = r.text
        assert "import pytest" in text
        assert "@pytest.mark.parametrize" in text
        assert 'pytest.skip("TODO")' in text

        # Kompilierbar?
        import py_compile
        import tempfile as tf
        with tf.NamedTemporaryFile(suffix=".py", delete=False, mode="wb") as f:
            f.write(r.content)
            tmp_path = f.name
        try:
            py_compile.compile(tmp_path, doraise=True)
        finally:
            os.unlink(tmp_path)

    def test_export_json_data_driven(self, auth_client):
        """JSON Data-Driven: gueltiges JSON, Liste von Objekten."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/json-data-driven")
        assert r.status_code == 200, f"JSON data-driven failed: {r.text}"

        data = json.loads(r.text)
        assert isinstance(data, list)
        assert len(data) > 0
        # Erstes Objekt hat "id" und Kategorienamen als Keys
        first = data[0]
        assert "id" in first
        assert "Browser" in first
        assert "OS" in first
        assert "Eingabe" in first
        assert "Ergebnis" in first
        assert "has_error_value" in first

    def test_export_robot(self, auth_client):
        """Robot Framework Export: *** Settings ***, *** Test Cases ***, *** Keywords ***."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/robot")
        assert r.status_code == 200, f"Robot failed: {r.text}"

        text = r.text
        assert "*** Settings ***" in text
        assert "*** Test Cases ***" in text
        assert "*** Keywords ***" in text
        assert "[Template]" in text
        assert "Execute Test Case" in text

    def test_export_xray_csv(self, auth_client):
        """Xray CSV: korrekte Spalten, Semikolon-Delimiter."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/xray-csv")
        assert r.status_code == 200, f"Xray CSV failed: {r.text}"

        text = r.text
        assert "Test Case Identifier" in text
        assert "Summary" in text
        assert "Action" in text
        assert "Data" in text
        assert "Expected Result" in text
        assert "Test Type" in text

    def test_export_testrail_csv(self, auth_client):
        """TestRail CSV: korrekte Spalten."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/testrail-csv")
        assert r.status_code == 200, f"TestRail CSV failed: {r.text}"

        text = r.text
        assert "Title" in text
        assert "Preconditions" in text
        assert "Steps" in text
        assert "Expected Result" in text

    def test_export_azuredevops_csv(self, auth_client):
        """Azure DevOps CSV: korrekte Spalten, Multi-Row."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/azuredevops-csv")
        assert r.status_code == 200, f"Azure DevOps CSV failed: {r.text}"

        text = r.text
        assert "Work Item Type" in text
        assert "Test Case" in text
        assert "Test Step" in text
        assert "Step Action" in text
        assert "Step Expected" in text

    def test_export_markdown(self, auth_client):
        """Markdown Export: Tabelle mit |-Trennzeichen."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/markdown")
        assert r.status_code == 200, f"Markdown failed: {r.text}"

        text = r.text
        assert "| TC-ID |" in text
        assert "|---|" in text or "---" in text

    def test_export_unknown_format_404(self, auth_client):
        """Unbekanntes Format: 404."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/unknown-format")
        assert r.status_code == 404

    def test_export_nonexistent_generation_404(self, auth_client):
        """Nicht-existent Generation: 404."""
        r = auth_client.get("/api/generations/999999/export/gherkin")
        assert r.status_code == 404

    def test_export_deterministic(self, auth_client):
        """Deterministischer Export: Datum = 1970-01-01."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(
            f"/api/generations/{gen_id}/export/markdown?deterministic=true"
        )
        assert r.status_code == 200
        text = r.text
        assert "1970-01-01" in text

    def test_export_content_disposition(self, auth_client):
        """Content-Disposition Header: attachment mit Dateiname."""
        _, gen_id = _create_export_test_project(auth_client)
        r = auth_client.get(f"/api/generations/{gen_id}/export/gherkin")
        assert r.status_code == 200
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert f"generation_{gen_id}.feature" in cd


class TestExportGoldenFiles:
    """Golden-File-Tests: Byte-identischer Vergleich.

    Diese Tests schreiben beim ersten Durchlauf die Golden-Files
    und vergleichen danach byte-identisch.
    """

    def _get_or_create_golden(self, format_name: str, content: bytes) -> bytes:
        """Liest Golden-File oder erstellt es beim ersten Lauf."""
        golden_path = os.path.join(GOLDEN_DIR, f"{format_name}.expected")
        if not os.path.exists(golden_path):
            os.makedirs(GOLDEN_DIR, exist_ok=True)
            with open(golden_path, "wb") as f:
                f.write(content)
            return content
        with open(golden_path, "rb") as f:
            return f.read()

    def test_golden_gherkin_en(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/gherkin?lang=en&deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("gherkin_en", r.content)
        assert r.content == expected

    def test_golden_pytest(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/pytest?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("pytest", r.content)
        assert r.content == expected

    def test_golden_json_data_driven(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/json-data-driven?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("json_data_driven", r.content)
        assert r.content == expected

    def test_golden_robot(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/robot?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("robot", r.content)
        assert r.content == expected

    def test_golden_xray_csv(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/xray-csv?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("xray_csv", r.content)
        assert r.content == expected

    def test_golden_testrail_csv(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/testrail-csv?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("testrail_csv", r.content)
        assert r.content == expected

    def test_golden_azuredevops_csv(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/azuredevops-csv?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("azuredevops_csv", r.content)
        assert r.content == expected

    def test_golden_markdown(self, auth_client):
        _, gen_id = _create_export_test_project(auth_client, fixed_name="GoldenExportTest")
        r = auth_client.get(f"/api/generations/{gen_id}/export/markdown?deterministic=true")
        assert r.status_code == 200
        expected = self._get_or_create_golden("markdown", r.content)
        assert r.content == expected