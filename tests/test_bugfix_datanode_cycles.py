"""B-09: Datenknoten: Zyklen-Pruefung und Reparatur-Tests.

Testet parent_id-Validierung bei create/update und startup-Reparatur.
"""
import pytest

from app.models import DataNode, DataNodeValue


# ---------------------------------------------------------------------------
# RED-GREEN: Zyklen-Pruefung bei update_node
# ---------------------------------------------------------------------------


def test_parent_self_rejected(admin_client, db_session):
    """B-09: Knoten kann nicht unter sich selbst eingeordnet werden."""
    resp = admin_client.post("/api/datanodes", json={"name": "Root"})
    assert resp.status_code == 200
    node_id = resp.json()["id"]
    version = resp.json()["version"]

    # Selbst-Referenz versuchen
    resp = admin_client.put(
        f"/api/datanodes/{node_id}",
        json={"name": "Root", "parent_id": node_id, "version": version},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, dict)
    assert detail.get("code") == "cyclic_parent"

    # Knoten danach noch sichtbar und unveraendert
    resp = admin_client.get(f"/api/datanodes/{node_id}")
    assert resp.status_code == 200
    assert resp.json()["parent_id"] is None


def test_parent_descendant_rejected(admin_client, db_session):
    """B-09: Knoten kann nicht unter einem seiner Nachfahren eingeordnet werden."""
    # Root erstellen
    resp = admin_client.post("/api/datanodes", json={"name": "Root"})
    root_id = resp.json()["id"]

    # Kind erstellen
    resp = admin_client.post(
        "/api/datanodes",
        json={"name": "Child", "parent_id": root_id},
    )
    child_id = resp.json()["id"]

    # Root unter Kind setzen -> Zyklus
    resp = admin_client.get(f"/api/datanodes/{root_id}")
    version = resp.json()["version"]
    resp = admin_client.put(
        f"/api/datanodes/{root_id}",
        json={"name": "Root", "parent_id": child_id, "version": version},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, dict)
    assert detail.get("code") == "cyclic_parent"


def test_parent_grandchild_rejected(admin_client, db_session):
    """B-09: Knoten kann nicht unter Enkelknoten gesetzt werden (tieferer Zyklus)."""
    # A -> B -> C
    resp_a = admin_client.post("/api/datanodes", json={"name": "A"})
    id_a = resp_a.json()["id"]

    resp_b = admin_client.post(
        "/api/datanodes", json={"name": "B", "parent_id": id_a}
    )
    id_b = resp_b.json()["id"]

    resp_c = admin_client.post(
        "/api/datanodes", json={"name": "C", "parent_id": id_b}
    )
    id_c = resp_c.json()["id"]

    # A unter C setzen -> Zyklus A->B->C->A
    resp = admin_client.get(f"/api/datanodes/{id_a}")
    version = resp.json()["version"]
    resp = admin_client.put(
        f"/api/datanodes/{id_a}",
        json={"name": "A", "parent_id": id_c, "version": version},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, dict)
    assert detail.get("code") == "cyclic_parent"


# ---------------------------------------------------------------------------
# RED-GREEN: Parent-Existenz-Pruefung
# ---------------------------------------------------------------------------


def test_parent_unknown_on_create_returns_404(admin_client, db_session):
    """B-09: Create mit nicht-existentem parent_id gibt 404."""
    resp = admin_client.post(
        "/api/datanodes",
        json={"name": "X", "parent_id": 999999},
    )
    assert resp.status_code == 404


def test_parent_unknown_on_update_returns_404(admin_client, db_session):
    """B-09: Update mit nicht-existentem parent_id gibt 404."""
    resp = admin_client.post("/api/datanodes", json={"name": "Root"})
    node_id = resp.json()["id"]
    version = resp.json()["version"]

    resp = admin_client.put(
        f"/api/datanodes/{node_id}",
        json={"name": "Root", "parent_id": 999999, "version": version},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Regression: Gueltige Operationen funktionieren weiterhin
# ---------------------------------------------------------------------------


def test_move_to_valid_parent_still_works(admin_client, db_session):
    """B-09 Regression: Gueltiger Parent-Wechsel funktioniert."""
    resp1 = admin_client.post("/api/datanodes", json={"name": "A"})
    id_a = resp1.json()["id"]

    resp2 = admin_client.post("/api/datanodes", json={"name": "B"})
    id_b = resp2.json()["id"]

    resp3 = admin_client.post("/api/datanodes", json={"name": "C"})
    id_c = resp3.json()["id"]
    version_c = resp3.json()["version"]

    # C unter A bewegen
    resp = admin_client.put(
        f"/api/datanodes/{id_c}",
        json={"name": "C", "parent_id": id_a, "version": version_c},
    )
    assert resp.status_code == 200
    assert resp.json()["parent_id"] == id_a

    # C unter B bewegen
    resp = admin_client.get(f"/api/datanodes/{id_c}")
    version_c = resp.json()["version"]
    resp = admin_client.put(
        f"/api/datanodes/{id_c}",
        json={"name": "C", "parent_id": id_b, "version": version_c},
    )
    assert resp.status_code == 200
    assert resp.json()["parent_id"] == id_b


def test_set_parent_to_null_works(admin_client, db_session):
    """B-09 Regression: parent_id auf NULL setzen (zurueck zur Wurzel) funktioniert."""
    resp1 = admin_client.post("/api/datanodes", json={"name": "Parent"})
    id_parent = resp1.json()["id"]

    resp2 = admin_client.post(
        "/api/datanodes",
        json={"name": "Child", "parent_id": id_parent},
    )
    id_child = resp2.json()["id"]
    version_child = resp2.json()["version"]

    # Child zurueck zur Wurzel
    resp = admin_client.put(
        f"/api/datanodes/{id_child}",
        json={"name": "Child", "parent_id": None, "version": version_child},
    )
    assert resp.status_code == 200
    assert resp.json()["parent_id"] is None


# ---------------------------------------------------------------------------
# Startup-Reparatur
# ---------------------------------------------------------------------------


def test_existing_two_node_cycle_is_repaired(db_session):
    """B-09: Zyklen in Bestandsdaten (2-Knoten) werden repariert."""
    from app.datavalidation import repair_cycles_on_startup

    n1 = DataNode(name="A", parent_id=None)
    db_session.add(n1)
    db_session.flush()  # n1.id muss vor n2-Erzeugung bekannt sein

    n2 = DataNode(name="B", parent_id=n1.id)
    db_session.add(n2)
    db_session.flush()

    # Zyklus: A.parent_id = B.id
    n1.parent_id = n2.id
    db_session.commit()

    repaired = repair_cycles_on_startup(db_session)
    assert repaired >= 1

    n1_fresh = db_session.get(DataNode, n1.id)
    assert n1_fresh.parent_id is None


def test_existing_three_node_cycle_is_repaired(db_session):
    """B-09: Zyklen in Bestandsdaten (3-Knoten) werden repariert."""
    from app.datavalidation import repair_cycles_on_startup

    n1 = DataNode(name="A", parent_id=None)
    db_session.add(n1)
    db_session.flush()

    n2 = DataNode(name="B", parent_id=n1.id)
    db_session.add(n2)
    db_session.flush()

    n3 = DataNode(name="C", parent_id=n2.id)
    db_session.add(n3)
    db_session.flush()

    # Zyklus: A->B->C->A
    n1.parent_id = n2.id
    n2.parent_id = n3.id
    n3.parent_id = n1.id
    db_session.commit()

    repaired = repair_cycles_on_startup(db_session)
    # Mindestens einer der Knoten muss repariert werden
    assert repaired >= 1


def test_repair_is_idempotent(db_session):
    """B-09: Reparatur ist idempotent – zweiter Durchlauf repariert nichts."""
    from app.datavalidation import repair_cycles_on_startup

    n1 = DataNode(name="A", parent_id=None)
    db_session.add(n1)
    db_session.flush()

    n2 = DataNode(name="B", parent_id=n1.id)
    db_session.add(n2)
    db_session.flush()

    n1.parent_id = n2.id
    db_session.commit()

    assert repair_cycles_on_startup(db_session) >= 1
    # Zweiter Durchlauf: nichts mehr zu reparieren
    assert repair_cycles_on_startup(db_session) == 0


def test_repair_clean_data_is_noop(db_session):
    """B-09: Reparatur an sauberen Daten aendert nichts."""
    from app.datavalidation import repair_cycles_on_startup

    n1 = DataNode(name="A", parent_id=None)
    db_session.add(n1)
    db_session.flush()

    n2 = DataNode(name="B", parent_id=n1.id)
    db_session.add(n2)
    db_session.flush()

    db_session.commit()

    assert repair_cycles_on_startup(db_session) == 0