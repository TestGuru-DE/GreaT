"""Bugfixes A-16 (Server-Meldungen nach Accept-Language, mit code) und B-18 (doppelte Spalte)."""
import ast
import itertools
import pathlib

from app.i18n.server_messages import localize_detail, lookup

_counter = itertools.count()
SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "app"


def _static_details():
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "HTTPException":
                for kw in node.keywords:
                    if kw.arg != "detail":
                        continue
                    values = [kw.value]
                    if isinstance(kw.value, ast.Dict):
                        values = [v for k, v in zip(kw.value.keys, kw.value.values)
                                  if isinstance(k, ast.Constant) and k.value in ("detail", "message")]
                    for v in values:
                        if isinstance(v, ast.Constant) and isinstance(v.value, str):
                            yield path.name, v.value


def test_every_static_message_has_code_and_translation():
    missing = sorted({(f, m) for f, m in _static_details()
                      if not (m.replace("_", "").isalnum() and m.islower()) and lookup(m) is None})
    assert missing == [], f"Meldungen ohne Eintrag in i18n/server_messages.py: {missing}"


def test_codes_stay_untouched():
    assert localize_detail("password_change_required", "en") == ("password_change_required", None)


def test_not_found_in_english_with_code(auth_client):
    resp = auth_client.get("/api/projects/999999/categories", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Project not found", "code": "project_not_found"}


def test_default_stays_german_with_code(auth_client):
    resp = auth_client.get("/api/projects/999999/categories")
    assert resp.json() == {"detail": "Projekt nicht gefunden", "code": "project_not_found"}


def test_login_error_in_english(client):
    resp = client.post("/auth/login", data={"username": "niemand", "password": "x"},
                       headers={"Accept-Language": "en"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"
    assert resp.json()["code"] == "invalid_credentials"


def test_dict_details_translated_and_keep_code(auth_client):
    pid = auth_client.post("/api/projects", json={"name": f"I18n-{next(_counter)}"}).json()["id"]
    resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", headers={"Accept-Language": "en"}, json={
        "name": "x", "kind": "forbid", "expression": {"op": "eq", "category_id": 999999, "value_id": 999999}})
    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["code"] == "constraint_reference_invalid"
    assert body["detail"]["detail"].startswith("The constraint refers to")
    assert "code" not in body  # Code steht bereits im Detail-Objekt


# ===========================================================================
# B-18: Umbenannte Kategorie erzeugt keine zweite Spalte
# ===========================================================================

def _gen_with_rename(client):
    pid = client.post("/api/projects", json={"name": f"B18-{next(_counter)}"}).json()["id"]
    cid = client.post(f"/api/projects/{pid}/categories", json={"name": "Eingabe", "order_index": 0}).json()["id"]
    client.post(f"/api/categories/{cid}/values", json={"value": "x"})
    gid = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"}).json()["generation_id"]
    assert client.patch(f"/api/categories/{cid}/rename", json={"name": "Eingabe-neu"}).status_code == 200
    return pid, cid, gid


def test_renamed_category_single_column_in_testcases(auth_client):
    _, _, gid = _gen_with_rename(auth_client)
    tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()["testcases"]
    assert tcs[0]["assignments"] == {"Eingabe-neu": "x"}


def test_renamed_category_single_column_in_csv_and_json(auth_client):
    _, _, gid = _gen_with_rename(auth_client)
    csv_text = auth_client.get(f"/api/generations/{gid}/export/csv").content.decode("utf-8-sig")
    header = next(line for line in csv_text.splitlines() if not line.strip('"').startswith("sep="))
    assert "Eingabe-neu" in header
    assert header.count("Eingabe") == 1, header


def test_deleted_category_keeps_its_column(auth_client):
    pid, cid, gid = _gen_with_rename(auth_client)
    assert auth_client.delete(f"/api/categories/{cid}").status_code == 200
    tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()["testcases"]
    assert tcs[0]["assignments"] == {"Eingabe": "x"}
