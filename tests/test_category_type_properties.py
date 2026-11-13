"""REQ-5002: Kategorie-Typ (standard/cause/effect) nachtraeglich setzen; REQ-4016: Ergebnis-Flag."""


def _project_with_category(auth_client, name):
    pid = auth_client.post("/api/projects", json={"name": name}).json()["id"]
    cid = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kat"}).json()["id"]
    return pid, cid


def test_set_category_type_to_cause_and_effect(auth_client):
    _, cid = _project_with_category(auth_client, "CatType_Props_A")
    r = auth_client.patch(f"/api/categories/{cid}/properties", json={"category_type": "cause"})
    assert r.status_code == 200, r.text
    assert r.json()["category_type"] == "cause"
    r = auth_client.patch(f"/api/categories/{cid}/properties", json={"category_type": "effect"})
    assert r.json()["category_type"] == "effect"


def test_invalid_category_type_rejected(auth_client):
    _, cid = _project_with_category(auth_client, "CatType_Props_B")
    r = auth_client.patch(f"/api/categories/{cid}/properties", json={"category_type": "bogus"})
    assert r.status_code == 422


def test_is_result_still_settable(auth_client):
    _, cid = _project_with_category(auth_client, "CatType_Props_C")
    r = auth_client.patch(f"/api/categories/{cid}/properties", json={"is_result": True})
    assert r.status_code == 200
    assert r.json()["is_result"] is True
