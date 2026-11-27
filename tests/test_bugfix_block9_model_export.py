"""Restbefunde Themenblock 9b: Modellformat streng, Exporte mit Herkunft/Fehlerwert und Nutzersprache."""
import csv
import io
import itertools
import json
import pathlib

import pytest

_counter = itertools.count()
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _model(**extra):
    data = {
        "schemaVersion": 1,
        "projectName": f"B9b-{next(_counter)}",
        "categories": [
            {"name": "id", "values": [{"value": "a"}]},
            {"name": "B", "values": [{"value": "b"}, {"value": "kaputt", "allowed": False}]},
        ],
    }
    data.update(extra)
    return data


def _import(client, body, content_type="application/json"):
    return client.post("/api/v1/projects/import-model", content=body, headers={"Content-Type": content_type})


# ---------------------------------------------------------------------------
# Modellformat
# ---------------------------------------------------------------------------

def test_schema_version_as_string_rejected(auth_client):
    resp = _import(auth_client, json.dumps(_model(schemaVersion="1")))
    assert resp.status_code == 400
    assert "schemaVersion" in resp.text


def test_missing_schema_version_rejected(auth_client):
    data = _model()
    del data["schemaVersion"]
    resp = _import(auth_client, json.dumps(data))
    assert resp.status_code == 400
    assert "schemaVersion" in resp.text


def test_non_utf8_file_gives_400_not_500(auth_client):
    resp = _import(auth_client, "schemaVersion: 1\nprojectName: Gr\xf6\xdfe\n".encode("latin-1"), "text/yaml")
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "model_not_utf8"


def test_error_paths_contain_index(auth_client):
    data = _model()
    data["categories"].append({"name": "b", "values": [{"value": "x"}]})
    resp = _import(auth_client, json.dumps(data))
    assert resp.status_code == 400
    assert "$.categories[2].name" in resp.json()["detail"]


def test_pydantic_error_path_contains_index(auth_client):
    data = _model()
    data["categories"][1]["values"][0]["riskWeight"] = 99
    resp = _import(auth_client, json.dumps(data))
    assert resp.status_code == 400


def test_examples_import_cleanly(auth_client):
    files = sorted((ROOT / "examples").glob("*.great.yaml"))
    assert files, "examples/ enthaelt keine Modelldatei"
    for path in files:
        resp = _import(auth_client, path.read_bytes(), "text/yaml")
        assert resp.status_code == 200, (path.name, resp.text)
        assert resp.json()["warnings"] == []


# ---------------------------------------------------------------------------
# Exporte
# ---------------------------------------------------------------------------

@pytest.fixture
def generation(auth_client):
    pid = _import(auth_client, json.dumps(_model())).json()["projectId"]
    gid = auth_client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"}).json()["generation_id"]
    return gid


def test_json_data_driven_keeps_testcase_id(auth_client, generation):
    data = json.loads(auth_client.get(f"/api/generations/{generation}/export/json-data-driven").content)
    assert [row["id"] for row in data] == ["TC_1", "TC_2"]
    assert {row["id (2)"] for row in data} == {"a"}
    assert {row["origin"] for row in data} == {"generated"}
    assert sorted(row["has_error_value"] for row in data) == [False, True]


def _rows(content: bytes, delimiter: str):
    return list(csv.DictReader(io.StringIO(content.decode("utf-8")), delimiter=delimiter))


def test_xray_labels_mark_error_value(auth_client, generation):
    rows = _rows(auth_client.get(f"/api/generations/{generation}/export/xray-csv").content, ";")
    assert sorted(r["Labels"] for r in rows) == ["", "error-value"]


def test_testrail_has_error_and_origin_columns(auth_client, generation):
    rows = _rows(auth_client.get(f"/api/generations/{generation}/export/testrail-csv").content, ";")
    assert sorted(r["Error Value"] for r in rows) == ["No", "Yes"]
    assert {r["Origin"] for r in rows} == {"generated"}


def test_azure_tags_on_first_step_only(auth_client, generation):
    rows = _rows(auth_client.get(f"/api/generations/{generation}/export/azuredevops-csv").content, ",")
    tagged = [r for r in rows if r["Tags"]]
    assert [r["Tags"] for r in tagged] == ["error-value"]
    assert all(r["Test Step"] == "1" for r in tagged)


def test_csv_headers_follow_accept_language(auth_client, generation):
    de = auth_client.get(f"/api/generations/{generation}/export/csv", headers={"Accept-Language": "de"})
    en = auth_client.get(f"/api/generations/{generation}/export/csv", headers={"Accept-Language": "en"})
    assert de.content != en.content
    explicit = auth_client.get(f"/api/generations/{generation}/export/csv?lang=de", headers={"Accept-Language": "en"})
    assert explicit.content == de.content


def test_csv_default_without_header_stays_german(auth_client, generation):
    resp = auth_client.get(f"/api/generations/{generation}/export/csv", headers={"Accept-Language": ""})
    explicit = auth_client.get(f"/api/generations/{generation}/export/csv?lang=de")
    assert resp.content == explicit.content
