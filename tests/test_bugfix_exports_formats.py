"""Bugfixes Exporte: A-05, A-06, A-10, A-11, A-12.

Die Exporte werden von den Originalwerkzeugen eingelesen (Gherkin-Parser,
Robot Framework, pytest) und die gelesenen Werte mit den Testdaten verglichen.
"""
import csv
import importlib.util
import io
import itertools
import json
import subprocess
import sys

import pytest

gherkin_parser = pytest.importorskip("gherkin.parser")
robot = pytest.importorskip("robot")
robot_api = pytest.importorskip("robot.api")

_counter = itertools.count()

NASTY_VALUES = [
    "Rechnung", "a|b", "back\\slash", "${var}", "#hash", "x=y",
    "  zwei  Leer  ", "Zeile1\nZeile2", 'Quote "doppelt"', "it's", "<tag>",
    "@{list} &{dict} %{ENV}",
]
MODEL = [
    # (Kategorie, Werte, is_result)
    ("Zahlart", NASTY_VALUES, False),
    ("a b", ["1", "2"], False),
    ("a-b", ["x"], False),
    ("Größe", ["groß", "klein"], False),
    ("class", ["c"], False),
    ("Ergebnis", ["ok", "fehler"], True),
]
CATEGORIES = [m[0] for m in MODEL]


def _natural(name):
    return int(name.split("_")[1])


@pytest.fixture
def nasty_generation(auth_client):
    """Projekt mit kollidierenden Namen, Umlauten und Sonderwerten; 12 Testfaelle."""
    pid = auth_client.post("/api/projects", json={"name": f"Export-Grenzfaelle-{next(_counter)}"}).json()["id"]
    for idx, (name, values, is_result) in enumerate(MODEL):
        cat = auth_client.post(f"/api/projects/{pid}/categories",
                               json={"name": name, "order_index": idx, "is_result": is_result})
        assert cat.status_code == 200, cat.text
        for v in values:
            r = auth_client.post(f"/api/categories/{cat.json()['id']}/values", json={"value": v})
            assert r.status_code == 200, r.text
    gen = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"})
    assert gen.status_code == 200, gen.text
    gid = gen.json()["generation_id"]
    truth = json.loads(auth_client.get(f"/api/generations/{gid}/export/json-data-driven").content)
    assert len(truth) == 12
    return gid, {row["id"]: row for row in truth}


def _export(client, gid, fmt, **params):
    r = client.get(f"/api/generations/{gid}/export/{fmt}", params={"deterministic": True, **params})
    assert r.status_code == 200, r.text
    return r.content.decode("utf-8")


# ===========================================================================
# A-05 Gherkin
# ===========================================================================

@pytest.mark.parametrize("lang,feature_kw", [("en", "Feature"), ("de", "Funktionalität")])
def test_gherkin_is_valid_and_roundtrips_values(auth_client, nasty_generation, lang, feature_kw):
    gid, truth = nasty_generation
    text = _export(auth_client, gid, "gherkin", lang=lang)
    doc = gherkin_parser.Parser().parse(text)  # wirft bei Syntaxfehlern
    feature = doc["feature"]
    assert feature["keyword"] == feature_kw
    outline = feature["children"][0]["scenario"]
    examples = outline["examples"][0]
    header = [c["value"] for c in examples["tableHeader"]["cells"]]
    assert header[0] == "TC-ID"
    assert len(set(header)) == len(header), "Spalten muessen eindeutig sein (A-12)"
    assert "Größe" in header, "Umlaute bleiben erhalten (A-12)"
    # Jeder Schritt nutzt einen Platzhalter, der als Spalte existiert
    assert len(outline["steps"]) == len(CATEGORIES)
    for step in outline["steps"]:
        placeholder = step["text"].split("<", 1)[1].rsplit(">", 1)[0]
        assert placeholder in header
    rows = examples["tableBody"]
    assert [r["cells"][0]["value"] for r in rows] == [f"TC_{i}" for i in range(1, 13)]  # A-12
    for row in rows:
        cells = [c["value"] for c in row["cells"]]
        expected = truth[cells[0]]
        for cat, cell in zip(CATEGORIES, cells[1:]):
            # Gherkin entfernt Leerzeichen am Zellenrand immer (Spezifikation)
            assert cell == expected[cat].strip(), (cat, cell, expected[cat])


def test_gherkin_without_testcases_does_not_crash(auth_client, db_session):
    from app import models
    pid = auth_client.post("/api/projects", json={"name": f"Leer-{next(_counter)}"}).json()["id"]
    cat = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "A", "order_index": 0}).json()
    auth_client.post(f"/api/categories/{cat['id']}/values", json={"value": "x"})
    gid = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "each"}).json()["generation_id"]
    for tc in db_session.query(models.TestCase).filter(models.TestCase.generation_id == gid):
        db_session.query(models.TestCaseValue).filter(models.TestCaseValue.testcase_id == tc.id).delete()
        db_session.delete(tc)
    db_session.commit()
    text = _export(auth_client, gid, "gherkin")
    gherkin_parser.Parser().parse(text)


# ===========================================================================
# A-06 Robot Framework
# ===========================================================================

class _Messages(robot_api.ResultVisitor):
    def __init__(self):
        self.by_test, self._current = {}, None

    def start_test(self, test):
        self._current = self.by_test.setdefault(test.name, [])

    def visit_message(self, msg):
        if self._current is not None:
            self._current.append(msg.message)


def test_robot_runs_and_receives_exact_values(auth_client, nasty_generation, tmp_path):
    gid, truth = nasty_generation
    suite = tmp_path / "generated.robot"
    suite.write_text(_export(auth_client, gid, "robot"), encoding="utf-8")
    output = tmp_path / "output.xml"
    rc = robot.run(str(suite), output=str(output), log=None, report=None,
                   console="none", stdout=io.StringIO(), stderr=io.StringIO())
    assert rc == 0, suite.read_text(encoding="utf-8")

    result = robot_api.ExecutionResult(str(output))
    assert [t.name for t in result.suite.tests] == [f"TC_{i}" for i in range(1, 13)]  # A-12
    visitor = _Messages()
    result.visit(visitor)
    for name, messages in visitor.by_test.items():
        for cat in CATEGORIES:
            label = ("Expected " if cat == "Ergebnis" else "") + cat + ": "
            matches = [m[len(label):] for m in messages if m.startswith(label)]
            assert matches == [truth[name][cat]], (name, cat, messages)


def test_robot_varnames_unique_by_robot_rules():
    from app.exporters.robot import RobotExporter
    view = {"project_name": "P", "generation_id": 1, "strategy": "each", "version": "x",
            "categories": ["a b", "a_b", "AB", "1st"], "result_categories": [],
            "testcases": [{"name": "TC_1", "assignments": {"a b": "1", "a_b": "2", "AB": "3", "1st": "4"}}]}
    text = RobotExporter().render(view, {}).decode()
    args_line = next(line for line in text.splitlines() if "[Arguments]" in line)
    normalized = [a.strip("${}").casefold().replace("_", "") for a in args_line.split("    ")[2:]]
    assert len(set(normalized)) == 4, args_line


# ===========================================================================
# A-12 pytest
# ===========================================================================

def test_pytest_export_collects_and_roundtrips(auth_client, nasty_generation, tmp_path):
    gid, truth = nasty_generation
    path = tmp_path / "test_generated_export.py"
    path.write_text(_export(auth_client, gid, "pytest"), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                           str(path)], cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "12 tests collected" in proc.stdout

    spec = importlib.util.spec_from_file_location("generated_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mark = module.test_generated.pytestmark[0]
    argnames = [a.strip() for a in mark.args[0].split(",")]
    assert len(set(argnames)) == len(CATEGORIES), argnames  # a b / a-b kollidieren nicht mehr
    ids = mark.kwargs["ids"]
    assert ids == [f"TC_{i}" for i in range(1, 13)]
    for tc_id, values in zip(ids, mark.args[1]):
        assert list(values) == [truth[tc_id][c] for c in CATEGORIES]


# ===========================================================================
# A-11 Testmanagement-CSV
# ===========================================================================

@pytest.mark.parametrize("fmt,delimiter,first", [
    ("xray-csv", ";", "Test Case Identifier"),
    ("testrail-csv", ";", "Title"),
    ("azuredevops-csv", ",", "ID"),
])
def test_csv_starts_with_header_row(auth_client, nasty_generation, fmt, delimiter, first):
    gid, _ = nasty_generation
    text = _export(auth_client, gid, fmt)
    assert not text.startswith("#")
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    assert rows[0][0] == first


def test_xray_summary_starts_with_tc_id(auth_client, nasty_generation):
    gid, truth = nasty_generation
    rows = list(csv.DictReader(io.StringIO(_export(auth_client, gid, "xray-csv")), delimiter=";"))
    assert [r["Test Case Identifier"] for r in rows] == [f"TC_{i}" for i in range(1, 13)]
    for r in rows:
        assert r["Summary"].startswith(r["Test Case Identifier"] + ": "), r["Summary"]


def test_testrail_title_starts_with_tc_id(auth_client, nasty_generation):
    gid, _ = nasty_generation
    rows = list(csv.DictReader(io.StringIO(_export(auth_client, gid, "testrail-csv")), delimiter=";"))
    assert [r["Title"].split(":")[0] for r in rows] == [f"TC_{i}" for i in range(1, 13)]


def test_azure_creates_new_items(auth_client, nasty_generation):
    """ID leer (sonst Update vorhandener Work Items), Titel je Schrittzeile wiederholt."""
    gid, _ = nasty_generation
    rows = list(csv.DictReader(io.StringIO(_export(auth_client, gid, "azuredevops-csv"))))
    assert rows and all(r["ID"] == "" for r in rows)
    assert all(r["Work Item Type"] == "Test Case" and r["State"] == "Design" for r in rows)
    by_title = {}
    for r in rows:
        by_title.setdefault(r["Title"], []).append(int(r["Test Step"]))
    assert len(by_title) == 12
    assert all(steps == list(range(1, len(steps) + 1)) for steps in by_title.values())
    assert list(by_title)[0].startswith("TC_1: ")


# ===========================================================================
# A-10 Spalten aus der Generierung (unveraenderliche Historie)
# ===========================================================================

def test_columns_follow_generation_not_current_model(auth_client):
    pid = auth_client.post("/api/projects", json={"name": f"Historie-{next(_counter)}"}).json()["id"]
    cats = {}
    for idx, name in enumerate(["Alt", "Bleibt"]):
        cats[name] = auth_client.post(f"/api/projects/{pid}/categories",
                                      json={"name": name, "order_index": idx}).json()["id"]
        auth_client.post(f"/api/categories/{cats[name]}/values", json={"value": f"{name}-Wert"})
    gid = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"}).json()["generation_id"]

    # Modell aendern: Kategorie loeschen, neue anlegen
    assert auth_client.delete(f"/api/categories/{cats['Alt']}").status_code == 200
    neu = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Neu", "order_index": 2}).json()
    auth_client.post(f"/api/categories/{neu['id']}/values", json={"value": "Neu-Wert"})

    data = json.loads(_export(auth_client, gid, "json-data-driven"))
    assert data == [{"id": "TC_1", "has_error_value": False, "origin": "generated", "Bleibt": "Bleibt-Wert", "Alt": "Alt-Wert"}]
    md = _export(auth_client, gid, "markdown")
    header = next(line for line in md.splitlines() if line.startswith("| TC-ID"))
    assert header == "| TC-ID | Bleibt | Alt |"
