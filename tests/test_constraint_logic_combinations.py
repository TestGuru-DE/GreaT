"""
REQ-6001: Tests fuer verschiedene logische Constraint-Kombinationen.

Prueft AST-Validierung, API-Speichern und Generierung fuer:
- Einfache eq/ne
- AND/OR Kombinationen
- NOT Verneinungen
- IN/NOT_IN
- Gemischte AND/OR/NOT
- Edge Cases (max Tiefe, max Leaves)
"""
import pytest
import json
from fastapi.testclient import TestClient


def create_categories_and_values(client, pid, cat_values: dict[str, list[str]]):
    """Hilfsfunktion: erstellt Kategorien und Werte."""
    cat_ids = {}
    val_ids: dict[int, dict[str, int]] = {}
    for idx, (cat_name, values) in enumerate(cat_values.items()):
        cat = client.post(f"/api/projects/{pid}/categories", json={"name": cat_name, "order_index": idx}).json()
        cat_ids[cat_name] = cat["id"]
        val_ids[cat["id"]] = {}
        for v in values:
            val = client.post(f"/api/categories/{cat['id']}/values", json={"value": v}).json()
            val_ids[cat["id"]][v] = val["id"]
    return cat_ids, val_ids


def make_constraint_payload(name: str, kind: str, condition: dict, consequence: dict | None = None):
    """Erzeugt ConstraintCreate-Payload."""
    payload: dict = {"name": name, "kind": kind, "expression": condition}
    if consequence is not None:
        payload["consequence"] = consequence
    return payload


def atom(cat_id: int, val_id: int, op: str = "eq") -> dict:
    """Erzeugt Atom-Node."""
    if op in ("in", "not_in"):
        return {"op": op, "category_id": cat_id, "value_ids": [val_id]}
    return {"op": op, "category_id": cat_id, "value_id": val_id}


def group(op: str, children: list[dict]) -> dict:
    """Erzeugt AND/OR Gruppe."""
    return {"op": op, "args": children}


def not_node(child: dict) -> dict:
    """Erzeugt NOT Node."""
    return {"op": "not", "arg": child}


class TestConstraintLogicCombinations:
    """20+ Testfaelle fuer verschiedene logische Constraint-Kombinationen."""

    def test_forbid_single_eq(self, auth_client):
        """1. forbid: eq (einfach)"""
        r = auth_client.post("/api/projects", json={"name": "T1"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"Farbe": ["rot", "blau"]})
        c_id, v_id = cats["Farbe"], vals[cats["Farbe"]]["rot"]

        payload = make_constraint_payload("test1", "forbid", atom(c_id, v_id))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_eq_to_eq(self, auth_client):
        """2. implies: eq → eq"""
        r = auth_client.post("/api/projects", json={"name": "T2"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]
        ax_id = vals[a_id]["x"]
        by_id = vals[b_id]["y"]

        payload = make_constraint_payload("test2", "implies", atom(a_id, ax_id), atom(b_id, by_id))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_ne(self, auth_client):
        """3. forbid: ne"""
        r = auth_client.post("/api/projects", json={"name": "T3"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"Farbe": ["rot"]})
        c_id, v_id = cats["Farbe"], vals[cats["Farbe"]]["rot"]

        payload = make_constraint_payload("test3", "forbid", atom(c_id, v_id, "ne"))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_ne_to_ne(self, auth_client):
        """4. implies: ne → ne"""
        r = auth_client.post("/api/projects", json={"name": "T4"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test4", "implies",
            atom(a_id, vals[a_id]["x"], "ne"), atom(b_id, vals[b_id]["y"], "ne"))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_and_2_eq(self, auth_client):
        """5. forbid: AND (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T5"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test5", "forbid",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_2_eq_to_eq(self, auth_client):
        """6. implies: AND (2 eq) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T6"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test6", "implies",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
            atom(c_id, vals[c_id]["z"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_eq_to_and_2_eq(self, auth_client):
        """7. implies: eq → AND (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T7"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test7", "implies",
            atom(a_id, vals[a_id]["x"]),
            group("and", [atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_to_and(self, auth_client):
        """8. implies: AND (2 eq) → AND (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T8"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"], "D": ["w"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test8", "implies",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
            group("and", [atom(c_id, vals[c_id]["z"]), atom(d_id, vals[d_id]["w"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_and_3_eq(self, auth_client):
        """9. forbid: AND (3 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T9"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test9", "forbid",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_mixed_to_eq(self, auth_client):
        """10. implies: AND (eq, ne) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T10"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test10", "implies",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"], "ne")]),
            atom(c_id, vals[c_id]["z"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_or_2_eq(self, auth_client):
        """11. forbid: OR (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T11"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test11", "forbid",
            group("or", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_or_to_eq(self, auth_client):
        """12. implies: OR (2 eq) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T12"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test12", "implies",
            group("or", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
            atom(c_id, vals[c_id]["z"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_eq_to_or(self, auth_client):
        """13. implies: eq → OR (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T13"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test13", "implies",
            atom(a_id, vals[a_id]["x"]),
            group("or", [atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_or_to_or(self, auth_client):
        """14. implies: OR (2 eq) → OR (2 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T14"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"], "D": ["w"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test14", "implies",
            group("or", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
            group("or", [atom(c_id, vals[c_id]["z"]), atom(d_id, vals[d_id]["w"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_or_3_eq(self, auth_client):
        """15. forbid: OR (3 eq)"""
        r = auth_client.post("/api/projects", json={"name": "T15"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test15", "forbid",
            group("or", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_or_mixed_to_eq(self, auth_client):
        """16. implies: AND (eq, OR (eq, eq)) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T16"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"], "D": ["w"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test16", "implies",
            group("and", [
                atom(a_id, vals[a_id]["x"]),
                group("or", [atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])])
            ]),
            atom(d_id, vals[d_id]["w"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_or_and_mixed_to_eq(self, auth_client):
        """17. implies: OR (eq, AND (eq, eq)) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T17"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"], "D": ["w"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test17", "implies",
            group("or", [
                atom(a_id, vals[a_id]["x"]),
                group("and", [atom(b_id, vals[b_id]["y"]), atom(c_id, vals[c_id]["z"])])
            ]),
            atom(d_id, vals[d_id]["w"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_and_or_nested(self, auth_client):
        """18. forbid: AND (OR (eq, eq), eq)"""
        r = auth_client.post("/api/projects", json={"name": "T18"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test18", "forbid",
            group("and", [
                group("or", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
                atom(c_id, vals[c_id]["z"])
            ]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_to_or(self, auth_client):
        """19. implies: AND (eq, eq) → OR (eq, eq)"""
        r = auth_client.post("/api/projects", json={"name": "T19"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"], "D": ["w"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test19", "implies",
            group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])]),
            group("or", [atom(c_id, vals[c_id]["z"]), atom(d_id, vals[d_id]["w"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_not_eq(self, auth_client):
        """20. forbid: NOT (eq)"""
        r = auth_client.post("/api/projects", json={"name": "T20"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"]})
        a_id = cats["A"]

        payload = make_constraint_payload("test20", "forbid",
            not_node(atom(a_id, vals[a_id]["x"])))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_not_eq_to_eq(self, auth_client):
        """21. implies: NOT (eq) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T21"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test21", "implies",
            not_node(atom(a_id, vals[a_id]["x"])),
            atom(b_id, vals[b_id]["y"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_not_to_eq(self, auth_client):
        """22. implies: AND (NOT (eq), eq) → eq"""
        r = auth_client.post("/api/projects", json={"name": "T22"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x"], "B": ["y"], "C": ["z"]})
        a_id, b_id, c_id = cats["A"], cats["B"], cats["C"]

        payload = make_constraint_payload("test22", "implies",
            group("and", [not_node(atom(a_id, vals[a_id]["x"])), atom(b_id, vals[b_id]["y"])]),
            atom(c_id, vals[c_id]["z"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_not_and(self, auth_client):
        """23. forbid: NOT (AND (eq, eq))"""
        r = auth_client.post("/api/projects", json={"name": "T23"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test23", "forbid",
            not_node(group("and", [atom(a_id, vals[a_id]["x"]), atom(b_id, vals[b_id]["y"])])))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_forbid_in(self, auth_client):
        """24. forbid: in"""
        r = auth_client.post("/api/projects", json={"name": "T24"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x", "y", "z"]})
        a_id = cats["A"]

        payload = make_constraint_payload("test24", "forbid",
            {"op": "in", "category_id": a_id, "value_ids": [vals[a_id]["x"], vals[a_id]["y"]]})
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_in_to_eq(self, auth_client):
        """25. implies: in → eq"""
        r = auth_client.post("/api/projects", json={"name": "T25"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x", "y"], "B": ["z"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test25", "implies",
            {"op": "in", "category_id": a_id, "value_ids": [vals[a_id]["x"], vals[a_id]["y"]]},
            atom(b_id, vals[b_id]["z"]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_eq_to_not_in(self, auth_client):
        """26. implies: eq → not_in"""
        r = auth_client.post("/api/projects", json={"name": "T26"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"], "B": ["y", "z"]})
        a_id, b_id = cats["A"], cats["B"]

        payload = make_constraint_payload("test26", "implies",
            atom(a_id, vals[a_id]["x"]),
            {"op": "not_in", "category_id": b_id, "value_ids": [vals[b_id]["y"], vals[b_id]["z"]]})
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_implies_and_in_to_or(self, auth_client):
        """27. implies: AND (in, eq) → OR (eq, eq)"""
        r = auth_client.post("/api/projects", json={"name": "T27"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid,
            {"A": ["x", "y"], "B": ["z"], "C": ["w"], "D": ["v"]})
        a_id, b_id, c_id, d_id = cats["A"], cats["B"], cats["C"], cats["D"]

        payload = make_constraint_payload("test27", "implies",
            group("and", [
                {"op": "in", "category_id": a_id, "value_ids": [vals[a_id]["x"], vals[a_id]["y"]]},
                atom(b_id, vals[b_id]["z"])
            ]),
            group("or", [atom(c_id, vals[c_id]["w"]), atom(d_id, vals[d_id]["v"])]))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_depth_5_max_ok(self, auth_client):
        """28. Tiefe 5 (max) sollte funktionieren"""
        r = auth_client.post("/api/projects", json={"name": "T28"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"]})
        a_id = cats["A"]
        v_id = vals[a_id]["x"]

        # 5-fach verschachtelt: NOT(NOT(NOT(NOT(NOT(eq)))))
        deep = atom(a_id, v_id)
        for _ in range(5):
            deep = not_node(deep)

        payload = make_constraint_payload("test28", "forbid", deep)
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_depth_6_too_deep_error(self, auth_client):
        """29. Tiefe 6 sollte Error geben"""
        r = auth_client.post("/api/projects", json={"name": "T29"})
        pid = r.json()["id"]
        cats, vals = create_categories_and_values(auth_client, pid, {"A": ["x"]})
        a_id = cats["A"]
        v_id = vals[a_id]["x"]

        # 6-fach verschachtelt
        deep = atom(a_id, v_id)
        for _ in range(6):
            deep = not_node(deep)

        payload = make_constraint_payload("test29", "forbid", deep)
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}: {resp.text}"

    def test_20_leaves_max_ok(self, auth_client):
        """30. 20 Leaves (max) sollte funktionieren"""
        r = auth_client.post("/api/projects", json={"name": "T30"})
        pid = r.json()["id"]
        # 20 Kategorien mit je 1 Wert
        cat_vals = {f"K{i}": [f"v{i}"] for i in range(20)}
        cats, vals = create_categories_and_values(auth_client, pid, cat_vals)

        atoms = [atom(cats[f"K{i}"], vals[cats[f"K{i}"]][f"v{i}"]) for i in range(20)]
        # Verschachtle in AND-Gruppen um 20 Leaves zu bekommen
        payload = make_constraint_payload("test30", "forbid", group("and", atoms))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code == 201, f"Failed: {resp.text}"

    def test_21_leaves_too_many_error(self, auth_client):
        """31. 21 Leaves sollte Error geben"""
        r = auth_client.post("/api/projects", json={"name": "T31"})
        pid = r.json()["id"]
        cat_vals = {f"K{i}": [f"v{i}"] for i in range(21)}
        cats, vals = create_categories_and_values(auth_client, pid, cat_vals)

        atoms = [atom(cats[f"K{i}"], vals[cats[f"K{i}"]][f"v{i}"]) for i in range(21)]
        payload = make_constraint_payload("test31", "forbid", group("and", atoms))
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json=payload)
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}: {resp.text}"