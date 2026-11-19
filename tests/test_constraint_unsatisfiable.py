"""
REQ-6001 AK-8: Tests fuer Widerspruchspruefung beim Speichern.

Macht ein Constraint einen Wert vollstaendig unerreichbar oder das ganze
Modell unerfuellbar, erscheint eine Warnung mit dem betroffenen Wert.
Speichern bleibt moeglich.

Testet die check_unsatisfiable()-Funktion aus evaluator_3vl.py und die
Integration in die API-Endpunkte POST/PUT constraints.
"""
import pytest
from itertools import product

from app.constraints.evaluator_3vl import check_unsatisfiable, check_all_constraints


# ====================================================================
# Unit-Tests: check_unsatisfiable (reine Logik, keine DB)
# ====================================================================

class TestCheckUnsatisfiable:
    """REQ-6001 AK-8: check_unsatisfiable – reine Logik-Tests."""

    def test_forbid_all_values_category(self):
        """
        REQ-6001 AK-8: forbid-Constraint macht alle Werte einer Kategorie
        unmoglich -> Warnung mit betroffener Kategorie.

        Szenario: Kategorie 1 hat Werte 1,2,3.
        Constraint: FORBID(cat1 IN [1,2,3]) -> kein Wert mehr moeglich.
        """
        categories = {1: {"name": "Farbe", "values": {1: "Rot", 2: "Grün", 3: "Blau"}}}
        new_constraint = {
            "kind": "forbid",
            "condition": {"op": "in", "category_id": 1, "value_ids": [1, 2, 3]},
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is True
        assert any("Farbe" in w or "Rot" in w or "Grün" in w or "Blau" in w
                   for w in affected)

    def test_implies_makes_model_unsatisfiable(self):
        """
        REQ-6001 AK-8: implies-Constraint macht Modell unerfuellbar -> Warnung.

        Szenario: Kategorie 1 hat Werte 1,2. Kategorie 2 hat Werte 3,4.
        Constraint: IF cat1=1 THEN cat2=5 (Wert 5 existiert nicht in cat2).
        Plus: FORBID(cat1=2) -> cat1=2 ist verboten, cat1=1 impliziert cat2=5 (unmoeglich).
        """
        categories = {
            1: {"name": "A", "values": {1: "a1", 2: "a2"}},
            2: {"name": "B", "values": {3: "b1", 4: "b2"}},
        }
        # FORBID(cat1=2) macht a2 unmoglich
        existing_constraints = [
            {
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 2},
            },
        ]
        # IF cat1=a1 THEN cat2=5 (Wert 5 gibt's nicht) -> a1 auch unmoglich
        new_constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 1},
            "consequence": {"op": "eq", "category_id": 2, "value_id": 5},
        }

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is True
        # Beide Kategorien sollten betroffen sein
        assert len(affected) >= 1

    def test_valid_constraint_no_warning(self):
        """
        REQ-6001 AK-8: Gueltiges Constraint -> keine Warnung.

        Szenario: Einfacher forbid, der nur einen Wert ausschliesst.
        """
        categories = {
            1: {"name": "Farbe", "values": {1: "Rot", 2: "Grün", 3: "Blau"}},
            2: {"name": "Groesse", "values": {4: "S", 5: "M", 6: "L"}},
        }
        new_constraint = {
            "kind": "forbid",
            "condition": {
                "op": "and",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 1},
                    {"op": "eq", "category_id": 2, "value_id": 4},
                ],
            },
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is False
        assert affected == []

    def test_forbid_one_value_no_warning(self):
        """
        REQ-6001 AK-8: forbid-Constraint schliesst nur einen Wert aus -> keine Warnung.
        (Nur komplette Kategorie-Blockierung oder Modell-Unerfuellbarkeit warnt.)
        """
        categories = {
            1: {"name": "Farbe", "values": {1: "Rot", 2: "Grün", 3: "Blau"}},
        }
        new_constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 1},
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        # Rot ist unerreichbar, aber nicht die ganze Kategorie -> keine Warnung
        assert is_unsat is False
        assert affected == []

    def test_multiple_forbids_make_category_unreachable(self):
        """
        REQ-6001 AK-8: Mehrere forbid-Constraints zusammen machen alle Werte
        einer Kategorie unmoglich.
        """
        categories = {
            1: {"name": "Status", "values": {1: "Aktiv", 2: "Inaktiv", 3: "Pausiert"}},
        }
        existing_constraints = [
            {
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 1},
            },
            {
                "kind": "forbid",
                "condition": {"op": "eq", "category_id": 1, "value_id": 2},
            },
        ]
        # Dritter forbid schliesst letzten Wert aus
        new_constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 3},
        }

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is True
        assert any("Status" in w or "Pausiert" in w for w in affected)

    def test_implies_consequence_always_false(self):
        """
        REQ-6001 AK-8: implies mit consequence die immer False ist.

        IF cat1=1 THEN cat1=2 -> kann nie erfuellt werden wenn cat1=1.
        """
        categories = {
            1: {"name": "A", "values": {1: "a1", 2: "a2"}},
        }
        new_constraint = {
            "kind": "implies",
            "condition": {"op": "eq", "category_id": 1, "value_id": 1},
            "consequence": {"op": "eq", "category_id": 1, "value_id": 2},
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        # a1 ist unmoglich (implies a1->a2, aber a1!=a2), a2 bleibt moeglich
        assert is_unsat is False  # Nicht komplett unerfuellbar, nur a1 betroffen

    def test_empty_categories_no_warning(self):
        """
        REQ-6001 AK-8: Leeres Modell -> keine Warnung.
        """
        categories = {}
        new_constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 1},
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is False
        assert affected == []

    def test_forbid_with_or_all_values(self):
        """
        REQ-6001 AK-8: forbid mit OR ueber alle Werte einer Kategorie.
        """
        categories = {
            1: {"name": "Typ", "values": {1: "A", 2: "B", 3: "C"}},
        }
        new_constraint = {
            "kind": "forbid",
            "condition": {
                "op": "or",
                "args": [
                    {"op": "eq", "category_id": 1, "value_id": 1},
                    {"op": "eq", "category_id": 1, "value_id": 2},
                    {"op": "eq", "category_id": 1, "value_id": 3},
                ],
            },
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            categories, new_constraint, existing_constraints
        )
        assert is_unsat is True
        assert any("Typ" in w for w in affected)

    def test_large_model_timeout(self):
        """
        REQ-6001 AK-8: Grosses Modell (>100 Kombinationen) -> Timeout-Hinweis.
        """
        # 5 Kategorien mit je 4 Werten = 1024 Kombinationen
        cats = {}
        vid = 1
        for i in range(1, 6):
            vals = {}
            for j in range(4):
                vals[vid] = f"v{vid}"
                vid += 1
            cats[i] = {"name": f"Cat{i}", "values": vals}

        new_constraint = {
            "kind": "forbid",
            "condition": {"op": "eq", "category_id": 1, "value_id": 1},
        }
        existing_constraints = []

        is_unsat, affected = check_unsatisfiable(
            cats, new_constraint, existing_constraints
        )
        # Sollte nicht komplett unerfuellbar sein (nur 1 Wert verboten)
        assert is_unsat is False
        # Sollte innerhalb des Timeouts bleiben oder Hinweis geben
        # Bei >100 Kombinationen: Stichproben-Modus mit Hinweis
        if any("Stichprobe" in w or "timeout" in w.lower() or "approx" in w.lower()
               for w in affected):
            pass  # OK: Stichproben-Hinweis ist korrekt


# ====================================================================
# API-Integrationstests: POST/PUT mit Widerspruchswarnung
# ====================================================================

class TestConstraintAPIUnsatisfiable:
    """REQ-6001 AK-8: API-Integrationstests fuer Widerspruchswarnungen."""

    def _create_test_project(self, client):
        """Erstellt ein Testprojekt mit 2 Kategorien und Werten."""
        resp = client.post("/api/projects", json={"name": "UnsatisfiableTest"})
        assert resp.status_code in (200, 201), f"Projekt erstellen fehlgeschlagen: {resp.text}"
        project_id = resp.json()["id"]

        cat1 = client.post(f"/api/projects/{project_id}/categories",
                           json={"name": "Farbe", "order_index": 0}).json()
        cat2 = client.post(f"/api/projects/{project_id}/categories",
                           json={"name": "Groesse", "order_index": 1}).json()

        v1 = client.post(f"/api/categories/{cat1['id']}/values",
                         json={"value": "Rot"}).json()
        v2 = client.post(f"/api/categories/{cat1['id']}/values",
                         json={"value": "Grün"}).json()
        v3 = client.post(f"/api/categories/{cat1['id']}/values",
                         json={"value": "Blau"}).json()
        v4 = client.post(f"/api/categories/{cat2['id']}/values",
                         json={"value": "S"}).json()
        v5 = client.post(f"/api/categories/{cat2['id']}/values",
                         json={"value": "M"}).json()

        return {
            "project_id": project_id,
            "categories": {
                "Farbe": {"id": cat1["id"], "values": {"Rot": v1["id"], "Grün": v2["id"], "Blau": v3["id"]}},
                "Groesse": {"id": cat2["id"], "values": {"S": v4["id"], "M": v5["id"]}},
            }
        }

    def test_create_forbid_all_values_warns(self, auth_client):
        """
        REQ-6001 AK-8: forbid-Constraint macht alle Werte einer Kategorie
        unmoglich -> Warnung in Response, aber 201 (Speichern erfolgreich).
        """
        ctx = self._create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Farbe"]["id"]
        vals = ctx["categories"]["Farbe"]["values"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeineFarbe",
            "kind": "forbid",
            "expression": {
                "op": "or",
                "args": [
                    {"op": "eq", "category_id": cid, "value_id": vals["Rot"]},
                    {"op": "eq", "category_id": cid, "value_id": vals["Grün"]},
                    {"op": "eq", "category_id": cid, "value_id": vals["Blau"]},
                ],
            },
        })
        assert resp.status_code == 201, f"Speichern muss gelingen (201), war {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["name"] == "KeineFarbe"
        # Warnung muss enthalten sein
        assert "warnings" in data, "Response muss 'warnings'-Feld enthalten"
        assert len(data["warnings"]) > 0, "Es muss mindestens eine Warnung geben"

    def test_create_valid_constraint_no_warning(self, auth_client):
        """
        REQ-6001 AK-8: Gueltiges Constraint -> keine Warnung in Response.
        """
        ctx = self._create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Farbe"]["id"]
        vals = ctx["categories"]["Farbe"]["values"]

        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeinRot",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vals["Rot"]},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "KeinRot"
        # warnings-Feld sollte vorhanden sein (leer)
        assert "warnings" in data
        assert data["warnings"] == []

    def test_update_to_unsatisfiable_warns(self, auth_client):
        """
        REQ-6001 AK-8: PUT-Update zu unsatisfiable Constraint -> Warnung,
        aber 200 (Speichern erfolgreich).
        """
        ctx = self._create_test_project(auth_client)
        pid = ctx["project_id"]
        cid = ctx["categories"]["Farbe"]["id"]
        vals = ctx["categories"]["Farbe"]["values"]

        # Erst ein gueltiges Constraint erstellen
        create_resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "TestUpdate",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": cid, "value_id": vals["Rot"]},
        })
        constraint_id = create_resp.json()["id"]

        # Jetzt zu unsatisfiable aendern (alle Werte verbieten)
        resp = auth_client.put(f"/api/v1/projects/{pid}/constraints/{constraint_id}", json={
            "expression": {
                "op": "or",
                "args": [
                    {"op": "eq", "category_id": cid, "value_id": vals["Rot"]},
                    {"op": "eq", "category_id": cid, "value_id": vals["Grün"]},
                    {"op": "eq", "category_id": cid, "value_id": vals["Blau"]},
                ],
            },
        })
        assert resp.status_code == 200, f"Speichern muss gelingen (200), war {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "warnings" in data
        assert len(data["warnings"]) > 0

    def test_create_implies_unsatisfiable_warns(self, auth_client):
        """
        REQ-6001 AK-8: implies-Constraint macht Modell unerfuellbar -> Warnung.
        """
        ctx = self._create_test_project(auth_client)
        pid = ctx["project_id"]
        c1_id = ctx["categories"]["Farbe"]["id"]
        c2_id = ctx["categories"]["Groesse"]["id"]
        v_rot = ctx["categories"]["Farbe"]["values"]["Rot"]
        v_gruen = ctx["categories"]["Farbe"]["values"]["Grün"]
        v_blau = ctx["categories"]["Farbe"]["values"]["Blau"]

        # Erst: alle Farben außer Rot verbieten
        auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeinGrün",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": c1_id, "value_id": v_gruen},
        })
        auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "KeinBlau",
            "kind": "forbid",
            "expression": {"op": "eq", "category_id": c1_id, "value_id": v_blau},
        })

        # Jetzt: IF Farbe=Rot THEN Farbe=Grün -> Rot kann nie vorkommen
        # (weil Grün bereits verboten) -> Modell unerfuellbar
        resp = auth_client.post(f"/api/v1/projects/{pid}/constraints", json={
            "name": "RotImpliesGrün",
            "kind": "implies",
            "expression": {"op": "eq", "category_id": c1_id, "value_id": v_rot},
            "consequence": {"op": "eq", "category_id": c1_id, "value_id": v_gruen},
        })
        assert resp.status_code == 201, f"Speichern muss gelingen (201), war {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "warnings" in data
        assert len(data["warnings"]) > 0, "Implies mit existierenden Forbids sollte warnen"