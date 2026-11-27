"""Bugfixes A-08 (OpenAPI per Bearer), A-09 (generate?export&persist), A-13 (Modell-Import)."""
import csv
import io
import itertools
import json

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models.auth import User

_counter = itertools.count()


def _bearer(scopes, username=None, role="editor"):
    """Header mit frischem API-Token fuer einen eigenen Nutzer."""
    from app.api_token_service import create_api_token

    username = username or f"a08-{next(_counter)}-{role}"
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username=username, role=role)
            user.set_password("Blau-Tanne-Kiesel-47")
            user.default_password_active = False
            user.token_version = 0
            db.add(user)
            db.commit()
            db.refresh(user)
        raw, _ = create_api_token(db, user, "test", scopes)
    finally:
        db.close()
    return {"Authorization": f"Bearer {raw}"}


def _project(client, categories=None):
    pid = client.post("/api/projects", json={"name": f"Hyg-{next(_counter)}"}).json()["id"]
    for order, (name, values) in enumerate((categories or {"A": ["a1", "a2"], "B": ["b1"]}).items()):
        cid = client.post(f"/api/projects/{pid}/categories", json={"name": name, "order_index": order}).json()["id"]
        for value in values:
            client.post(f"/api/categories/{cid}/values", json={"value": value})
    return pid


def _generation_count(client, pid):
    return len(client.get(f"/api/projects/{pid}/generations").json())


# ===========================================================================
# A-08: /openapi.json und /docs per Bearer, Operationen mit security
# ===========================================================================

@pytest.mark.parametrize("path", ["/openapi.json", "/docs"])
def test_docs_reachable_with_any_valid_api_token(client, path):
    resp = client.get(path, headers=_bearer(["projects:read"], role="api_user"))
    assert resp.status_code == 200, resp.text[:200]


def test_docs_rejects_invalid_api_token(client):
    resp = client.get("/openapi.json", headers={"Authorization": "Bearer great_pat_ungueltig"})
    assert resp.status_code == 403


def test_api_operations_declare_bearer_security(admin_client):
    schema = admin_client.get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/projects"]["get"]
    assert {"HTTPBearer": []} in operation["security"]
    assert "security" not in schema["paths"]["/auth/login"]["post"]


# ===========================================================================
# A-09: Komfort-Endpunkt generate?export=…&persist=…
# ===========================================================================

def test_generate_export_csv_without_persist_returns_csv_and_stores_nothing(auth_client):
    pid = _project(auth_client)
    before = _generation_count(auth_client, pid)
    resp = auth_client.post(f"/api/v1/projects/{pid}/generate?export=csv&persist=false", json={"strategy": "all"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    rows = [r for r in csv.reader(io.StringIO(resp.content.decode("utf-8-sig")), delimiter=";")
            if r and not r[0].startswith("sep=")]
    assert len(rows) == 1 + 2  # Kopfzeile + 2 Testfaelle
    assert _generation_count(auth_client, pid) == before


def test_generate_export_json_with_persist_stores_generation(auth_client):
    pid = _project(auth_client)
    before = _generation_count(auth_client, pid)
    resp = auth_client.post(f"/api/v1/projects/{pid}/generate?export=json", json={"strategy": "all"})
    assert resp.status_code == 200
    assert len(json.loads(resp.content)["testcases"]) == 2
    assert _generation_count(auth_client, pid) == before + 1


def test_generate_export_other_format(auth_client):
    pid = _project(auth_client)
    resp = auth_client.post(f"/api/v1/projects/{pid}/generate?export=markdown&persist=false",
                            json={"strategy": "all"})
    assert resp.status_code == 200
    assert "a1" in resp.text


def test_generate_unknown_export_format_rejected_before_generation(auth_client):
    pid = _project(auth_client)
    resp = auth_client.post(f"/api/v1/projects/{pid}/generate?export=pdf", json={"strategy": "all"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_export_format"
    assert _generation_count(auth_client, pid) == 0


def test_persist_false_without_export_rejected(auth_client):
    pid = _project(auth_client)
    resp = auth_client.post(f"/api/v1/projects/{pid}/generate?persist=false", json={"strategy": "all"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "persist_requires_export"


def test_generate_export_needs_export_scope(auth_client):
    pid = _project(auth_client)
    anon = TestClient(auth_client.app)
    headers = _bearer(["projects:read", "generate"], username="testuser")
    resp = anon.post(f"/api/v1/projects/{pid}/generate?export=csv&persist=false",
                     json={"strategy": "all"}, headers=headers)
    assert resp.status_code == 403
    headers = _bearer(["projects:read", "generate", "export"], username="testuser")
    resp = anon.post(f"/api/v1/projects/{pid}/generate?export=csv&persist=false",
                     json={"strategy": "all"}, headers=headers)
    assert resp.status_code == 200


# ===========================================================================
# A-13: Modell-Import
# ===========================================================================

def _model(**extra):
    data = {
        "schemaVersion": 1,
        "projectName": f"Modell-{next(_counter)}",
        "categories": [
            {"name": "Farbe", "values": [{"value": "Rot"}, {"value": "Blau"}]},
            {"name": "Form", "values": [{"value": "Kreis"}]},
        ],
    }
    data.update(extra)
    return data


def _import(client, data):
    return client.post("/api/v1/projects/import-model", content=json.dumps(data),
                       headers={"Content-Type": "application/json"})


def _constraints(client, pid):
    return client.get(f"/api/v1/projects/{pid}/constraints").json()


def test_constraint_with_unknown_category_name_imported_invalid_with_warning(auth_client):
    data = _model(constraints=[{"name": "C1", "kind": "forbid", "expression": {
        "kind": "forbid",
        "condition": {"op": "eq", "category_name": "Grösse", "value_name": "XL"}}}])
    resp = _import(auth_client, data)
    assert resp.status_code == 200, resp.text
    assert any("Grösse" in w for w in resp.json()["warnings"])
    constraints = _constraints(auth_client, resp.json()["projectId"])
    items = constraints if isinstance(constraints, list) else constraints["items"]
    assert [c["is_valid"] for c in items] == [False]


def test_constraint_with_numeric_ids_imported_invalid(auth_client):
    data = _model(constraints=[{"name": "C1", "kind": "forbid", "expression": {
        "kind": "forbid", "condition": {"op": "eq", "category_id": 1, "value_id": 1}}}])
    resp = _import(auth_client, data)
    assert resp.status_code == 200
    assert resp.json()["warnings"]


def test_valid_constraint_imported_valid_without_warning(auth_client):
    data = _model(constraints=[{"name": "C1", "kind": "forbid", "expression": {
        "kind": "forbid", "condition": {"op": "eq", "category_id": "Farbe", "value_id": "Rot"}}}])
    resp = _import(auth_client, data)
    assert resp.status_code == 200
    assert resp.json()["warnings"] == []


def test_categories_differing_only_in_case_rejected(auth_client):
    data = _model()
    data["categories"].append({"name": "farbe", "values": [{"value": "x"}]})
    resp = _import(auth_client, data)
    assert resp.status_code == 400
    assert "Doppelter Kategoriename" in resp.json()["detail"]


def test_unknown_key_rejected(auth_client):
    data = _model()
    data["categoriez"] = data.pop("categories")
    resp = _import(auth_client, data)
    assert resp.status_code == 400
    assert "categoriez" in resp.json()["detail"]


def test_put_cannot_rename_to_existing_project_name(auth_client):
    pid_a = _project(auth_client)
    pid_b = _project(auth_client)
    name_b = next(p["name"] for p in auth_client.get("/api/projects").json() if p["id"] == pid_b)
    data = _model(projectName=name_b.upper())
    resp = auth_client.put(f"/api/v1/projects/{pid_a}/model", json=data)
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "project_name_exists"


def test_seed_sets_roundtrip(auth_client):
    data = _model(seedSets=[{"name": "Pflicht", "cases": [{"Farbe": "Rot", "Form": None}]}])
    resp = _import(auth_client, data)
    assert resp.status_code == 200, resp.text
    pid = resp.json()["projectId"]
    exported = auth_client.get(f"/api/v1/projects/{pid}/model?format=json").json()
    assert exported["seedSets"] == [{"name": "Pflicht", "cases": [{"Farbe": "Rot", "Form": None}]}]


def test_seed_with_unknown_value_rejected(auth_client):
    data = _model(seedSets=[{"name": "Pflicht", "cases": [{"Farbe": "Gelb"}]}])
    resp = _import(auth_client, data)
    assert resp.status_code == 400
    assert "Gelb" in resp.json()["detail"]
