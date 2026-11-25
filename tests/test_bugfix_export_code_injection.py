"""BUG A-02: Code-Injection ueber Namen in Exporten (pytest, Robot, Gherkin, ...).

Ein Projekt- oder Kategoriename mit Zeilenumbruch durfte bisher eine
Kommentarzeile im Export beenden und ausfuehrbaren Code einschleusen.

Abgesichert in zwei Schichten:
1. Ausgabe: Exporter machen Namen in Kopf-/Kommentarzeilen einzeilig und
   maskieren Werte in Python-Strings vollstaendig (wirkt auch fuer Altdaten).
2. Eingabe: Projekt- und Kategorienamen duerfen keine Steuerzeichen enthalten.
"""
import ast
import uuid

import pytest

from app import models
from app.exporters.base import single_line
from app.exporters.pytest_exporter import escape_python_string

INJECTION = "Inj\nimport os\x0bimport sys\r\nprint('PWNED') x y\x85z"
FORMATS = ["pytest", "robot", "gherkin", "markdown", "xray-csv", "testrail-csv", "azuredevops-csv", "json-data-driven"]


def _project_with_generation(auth_client, db_session, project_name=None, category_name=None, values=("a", "b")):
    """Legt Projekt + Kategorie + Generierung an; setzt Namen danach direkt in der DB
    (simuliert Altdaten, die vor der Eingabevalidierung gespeichert wurden)."""
    r = auth_client.post("/api/projects", json={"name": f"Inj-{uuid.uuid4().hex[:6]}"})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kat"})
    cid = r.json()["id"]
    for v in values:
        assert auth_client.post(f"/api/categories/{cid}/values", json={"value": v}).status_code == 200
    gid = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"}).json()["generation_id"]
    if project_name is not None:
        db_session.get(models.Project, pid).name = project_name
    if category_name is not None:
        db_session.get(models.Category, cid).name = category_name
    db_session.commit()
    return pid, gid


def _export(auth_client, gid, fmt):
    r = auth_client.get(f"/api/generations/{gid}/export/{fmt}")
    assert r.status_code == 200, f"{fmt}: {r.status_code} {r.text[:200]}"
    return r.content.decode("utf-8")


# ---------------------------------------------------------------------------
# Ausgabeschicht
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["a\nb", "a\r\nb", "a\rb", "a\x0bb", "a\x0cb", "a\x00b", "a b", "a b", "a\x85b", "a\x1bb"])
def test_single_line_removes_all_line_breaks_and_controls(raw):
    out = single_line(raw)
    assert out.splitlines() == [out]
    assert all(ord(c) >= 32 and c not in "\x7f\x85  " for c in out)
    assert out.startswith("a") and out.endswith("b")


@pytest.mark.parametrize("fmt", FORMATS)
def test_project_name_with_line_breaks_cannot_inject_lines(auth_client, db_session, fmt):
    _, gid = _project_with_generation(auth_client, db_session, project_name=INJECTION)
    text = _export(auth_client, gid, fmt)
    for line in text.splitlines():
        stripped = line.strip()
        assert not (stripped.startswith("import ") and stripped != "import pytest"), f"{fmt}: eingeschleuste Zeile: {line!r}"
        assert not stripped.startswith("print("), f"{fmt}: eingeschleuste Zeile: {line!r}"
    for sep in ("\x0b", "\x0c", " ", " ", "\x85"):
        assert sep not in text, f"{fmt}: Zeilentrenner {sep!r} im Export"


def test_pytest_export_with_injected_names_is_valid_python_without_extra_statements(auth_client, db_session):
    _, gid = _project_with_generation(auth_client, db_session, project_name=INJECTION, category_name=INJECTION)
    text = _export(auth_client, gid, "pytest")
    tree = ast.parse(text)
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert [a.name for n in imports for a in n.names] == ["pytest"], "nur 'import pytest' erlaubt"
    calls = [n for n in tree.body if isinstance(n, ast.Expr) and not isinstance(n.value, ast.Constant)]
    assert calls == [], "keine ausfuehrbaren Anweisungen auf Modulebene"


@pytest.mark.parametrize("value", ["x\ny", "x\x00y", "x y", "a'b\"c\\d", "\x1b[31mrot", "tab\there", "ümlaut😀"])
def test_pytest_export_values_roundtrip_exactly(auth_client, db_session, value):
    _, gid = _project_with_generation(auth_client, db_session, values=(value, "b"))
    text = _export(auth_client, gid, "pytest")
    consts = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert value in consts, f"Wert {value!r} nicht exakt im Export"


@pytest.mark.parametrize("value", ["x\ny", "x\x00y", "x y", "a'b", "a\\b", "\x7f", "\x85"])
def test_escape_python_string_is_literal_safe(value):
    assert ast.literal_eval("'" + escape_python_string(value) + "'") == value


# ---------------------------------------------------------------------------
# Eingabeschicht
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["a\nb", "a\rb", "a\tb", "a\x00b", "a b", "a\x85b", "a\x1bb"])
def test_project_name_with_control_chars_rejected(auth_client, bad):
    r = auth_client.post("/api/projects", json={"name": bad})
    assert r.status_code == 422, r.text


@pytest.mark.parametrize("bad", ["a\nb", "a\tb", "a b"])
def test_project_rename_with_control_chars_rejected(auth_client, bad):
    pid = auth_client.post("/api/projects", json={"name": f"Ren-{uuid.uuid4().hex[:6]}"}).json()["id"]
    r = auth_client.put(f"/api/projects/{pid}", json={"name": bad})
    assert r.status_code == 422, r.text


@pytest.mark.parametrize("bad", ["a\nb", "a\tb", "a\x00b"])
def test_category_name_with_control_chars_rejected(auth_client, bad):
    pid = auth_client.post("/api/projects", json={"name": f"Cat-{uuid.uuid4().hex[:6]}"}).json()["id"]
    r = auth_client.post(f"/api/projects/{pid}/categories", json={"name": bad})
    assert r.status_code == 422, r.text
    cid = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "ok"}).json()["id"]
    r = auth_client.patch(f"/api/categories/{cid}/rename", json={"name": bad})
    assert r.status_code == 422, r.text


def test_values_may_still_contain_line_breaks(auth_client):
    """Werte sind Testdaten: Zeilenumbrueche bleiben dort bewusst erlaubt."""
    pid = auth_client.post("/api/projects", json={"name": f"Val-{uuid.uuid4().hex[:6]}"}).json()["id"]
    cid = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "K"}).json()["id"]
    r = auth_client.post(f"/api/categories/{cid}/values", json={"value": "Zeile1\nZeile2"})
    assert r.status_code == 200, r.text
