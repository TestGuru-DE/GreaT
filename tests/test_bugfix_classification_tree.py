"""Klassifikationsbaum-Backend: Werte sortieren (C-17) und manuelle Testfaelle pruefen (C-19)."""
import itertools

_counter = itertools.count()


def _project(client):
    pid = client.post("/api/projects", json={"name": f"Baum-{next(_counter)}"}).json()["id"]
    cats = {}
    for idx, (name, vals) in enumerate((("Zahlart", ["Rechnung", "Karte", "Bar"]), ("Versand", ["Post", "Abholung"]))):
        cid = client.post(f"/api/projects/{pid}/categories", json={"name": name, "order_index": idx}).json()["id"]
        cats[name] = {"id": cid, "values": {v: client.post(f"/api/categories/{cid}/values", json={"value": v}).json()["id"] for v in vals}}
    return pid, cats


def test_reorder_values_changes_list_and_generation_order(auth_client):
    pid, cats = _project(auth_client)
    z = cats["Zahlart"]
    order = [z["values"]["Bar"], z["values"]["Rechnung"], z["values"]["Karte"]]
    resp = auth_client.patch(f"/api/categories/{z['id']}/values/reorder", json={"order": order})
    assert resp.status_code == 200, resp.text
    listed = auth_client.get(f"/api/categories/{z['id']}/values").json()
    assert [v["value"] for v in listed] == ["Bar", "Rechnung", "Karte"]
    # neue Werte kommen ans Ende
    auth_client.post(f"/api/categories/{z['id']}/values", json={"value": "Lastschrift"})
    listed = auth_client.get(f"/api/categories/{z['id']}/values").json()
    assert [v["value"] for v in listed][-1] == "Lastschrift"


def test_reorder_values_requires_complete_own_list(auth_client):
    pid, cats = _project(auth_client)
    z, v = cats["Zahlart"], cats["Versand"]
    partial = [z["values"]["Bar"]]
    assert auth_client.patch(f"/api/categories/{z['id']}/values/reorder", json={"order": partial}).status_code == 422
    foreign = list(z["values"].values())[:-1] + [v["values"]["Post"]]
    assert auth_client.patch(f"/api/categories/{z['id']}/values/reorder", json={"order": foreign}).status_code == 422


def test_check_reports_constraint_violation_and_completability(auth_client):
    pid, cats = _project(auth_client)
    z, v = cats["Zahlart"], cats["Versand"]
    auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
        "name": "Bar nur bei Abholung", "kind": "implies",
        "expression": {"op": "eq", "category_id": z["id"], "value_id": z["values"]["Bar"]},
        "consequence": {"op": "eq", "category_id": v["id"], "value_id": v["values"]["Abholung"]},
    })
    bad = auth_client.post(f"/api/projects/{pid}/testcases/check",
                           json={"assignment": {"Zahlart": "Bar", "Versand": "Post"}}).json()
    assert bad == {"valid": False, "completable": False, "violations": ["Constraint: Bar nur bei Abholung"]}

    partial = auth_client.post(f"/api/projects/{pid}/testcases/check", json={"assignment": {"Zahlart": "Bar"}}).json()
    assert partial == {"valid": True, "completable": True, "violations": []}

    unknown = auth_client.post(f"/api/projects/{pid}/testcases/check", json={"assignment": {"Zahlart": "Scheck"}})
    assert unknown.status_code == 422


def test_check_reports_legacy_rules(auth_client):
    pid, cats = _project(auth_client)
    resp = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude", "if_category_id": cats["Zahlart"]["id"], "if_value": "Karte",
        "then_category_id": cats["Versand"]["id"], "then_value": "Abholung"})
    assert resp.status_code in (200, 201), resp.text
    result = auth_client.post(f"/api/projects/{pid}/testcases/check",
                              json={"assignment": {"Zahlart": "Karte", "Versand": "Abholung"}}).json()
    assert result["valid"] is False
    assert result["violations"] == ["Regel: Zahlart=Karte schliesst Versand=Abholung aus"]
