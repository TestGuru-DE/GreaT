"""Regeln: Validierung bei Anlage, einheitliche Anwendung, GenerateResponse-Warnungen.
B-19: Validierung bei Regel-Anlage
B-20: Einheitliche Regelanwendung + finaler Validierungs-Filter + unreachable values
B-21: GenerateResponse mit Warnungen
"""
import pytest


# =============================================================================
# B-19: Validierung bei Regel-Anlage
# =============================================================================


def test_create_rule_same_category_returns_400(auth_client, db_session):
    """IF- und THEN-Kategorie identisch -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid,
        "then_value": "A",
    })
    assert r.status_code == 400
    assert "identisch" in r.json()["detail"].lower() or "identisch" in r.json()["detail"]


def test_create_rule_nonexistent_if_value_returns_400(auth_client, db_session):
    """if_value existiert nicht in IF-Kategorie -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "GibtsNicht",
        "then_category_id": cid2,
        "then_value": "B",
    })
    assert r.status_code == 400
    assert "GibtsNicht" in r.json()["detail"]


def test_create_rule_nonexistent_then_value_returns_400(auth_client, db_session):
    """then_value existiert nicht in THEN-Kategorie -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "GibtsNicht",
    })
    assert r.status_code == 400
    assert "GibtsNicht" in r.json()["detail"]


def test_create_rule_exclude_no_then_value_returns_400(auth_client, db_session):
    """exclude ohne then_value -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "",
    })
    assert r.status_code == 400
    assert "Zielwert" in r.json()["detail"] or "benötigt" in r.json()["detail"]


def test_create_rule_dependency_no_then_value_returns_400(auth_client, db_session):
    """dependency ohne then_value -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "dependency",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "",
    })
    assert r.status_code == 400


def test_create_rule_duplicate_returns_409(auth_client, db_session):
    """Exakte Duplikate -> 409."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    # Erste Regel
    r1 = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })
    assert r1.status_code == 201

    # Duplikat
    r2 = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })
    assert r2.status_code == 409
    assert "existiert bereits" in r2.json()["detail"]


def test_create_rule_combine_nonexistent_value_returns_400(auth_client, db_session):
    """combine mit nicht-existentem then_value -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "combine",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_values": ["B", "GibtsNicht"],
    })
    assert r.status_code == 400
    assert "GibtsNicht" in r.json()["detail"]


def test_create_rule_combine_empty_values_returns_400(auth_client, db_session):
    """combine ohne then_values -> 400."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "combine",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_values": [],
    })
    assert r.status_code == 400


def test_create_rule_valid_exclude_returns_201(auth_client, db_session):
    """Gueltige exclude-Regel -> 201."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })
    assert r.status_code == 201


def test_create_rule_valid_dependency_returns_201(auth_client, db_session):
    """Gueltige dependency-Regel -> 201."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "dependency",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })
    assert r.status_code == 201


def test_create_rule_valid_combine_returns_201(auth_client, db_session):
    """Gueltige combine-Regel -> 201."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "C"})

    r = auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "combine",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_values": ["B", "C"],
    })
    assert r.status_code == 201


# =============================================================================
# B-19: Wert-Loeschen / Umbenennen -> Regel-Cleanup
# =============================================================================


def test_delete_value_cascades_to_rules(auth_client, db_session):
    """Loeschen eines Werts loescht auch referenzierende Regeln."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    v1 = auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    vid1 = v1.json()["id"]
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    # Regel anlegen
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })

    # Wert loeschen
    r = auth_client.delete(f"/api/values/{vid1}")
    assert r.status_code == 200

    # Regel sollte mitgeloescht sein
    rules = auth_client.get(f"/api/projects/{pid}/rules").json()
    assert len(rules) == 0


def test_rename_value_updates_rules(auth_client, db_session):
    """Umbenennen eines Werts aktualisiert referenzierende Regeln."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    v1 = auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    vid1 = v1.json()["id"]
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "B"})

    # Regel anlegen
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "B",
    })

    # Wert umbenennen
    r = auth_client.patch(f"/api/values/{vid1}/rename", json={"value": "A_NEU"})
    assert r.status_code == 200

    # Regel sollte aktualisiert sein
    rules = auth_client.get(f"/api/projects/{pid}/rules").json()
    assert len(rules) == 1
    assert rules[0]["if_value"] == "A_NEU"


# =============================================================================
# B-20: Einheitliche Regelanwendung
# =============================================================================


def test_apply_business_rules_filters_invalid_combinations(auth_client, db_session):
    """Nach Regelanwendung duerfen keine verbotenen Kombinationen bleiben."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "X"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "Y"})

    # exclude A+X
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "X",
    })

    # Generieren MIT apply_rules
    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": True
    })
    assert r.status_code == 200

    # Testfaelle abrufen
    gen_id = r.json()["generation_id"]
    tc_response = auth_client.get(f"/api/generations/{gen_id}/testcases")
    assert tc_response.status_code == 200
    testcases = tc_response.json()["testcases"]

    # Keine Kombination A+X sollte existieren
    for tc in testcases:
        assignments = tc["assignments"]
        if assignments.get("Kategorie1") == "A":
            assert assignments.get("Kategorie2") != "X", \
                f"Verbotene Kombination A+X gefunden: {assignments}"


def test_apply_business_rules_dependency_overrides_value(auth_client, db_session):
    """Dependency-Regel setzt Wert, auch wenn er urspruenglich anders war."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "X"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "Y"})

    # dependency: wenn A, dann X
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "dependency",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "X",
    })

    # Generieren MIT apply_rules
    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": True
    })
    assert r.status_code == 200

    gen_id = r.json()["generation_id"]
    tc_response = auth_client.get(f"/api/generations/{gen_id}/testcases")
    testcases = tc_response.json()["testcases"]

    # Alle Testfaelle mit A muessen X haben
    for tc in testcases:
        assignments = tc["assignments"]
        if assignments.get("Kategorie1") == "A":
            assert assignments.get("Kategorie2") == "X", \
                f"Dependency nicht angewendet: {assignments}"


# =============================================================================
# B-21: GenerateResponse mit Warnungen
# =============================================================================


def test_generate_response_has_warnings_when_rules_exist(auth_client, db_session):
    """GenerateResponse enthaelt Warnung wenn apply_rules=false und Regeln existieren."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "X"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "Y"})

    # Regel anlegen
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "X",
    })

    # Generieren OHNE apply_rules
    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": False
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("rule_count") == 1
    assert data.get("rules_applied") == False
    assert len(data.get("warnings", [])) > 0
    assert "apply_rules=false" in data["warnings"][0] or "nicht angewendet" in data["warnings"][0]


def test_generate_response_has_rules_applied_true(auth_client, db_session):
    """GenerateResponse enthaelt rules_applied=true und rule_count."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "X"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "Y"})

    # Regel anlegen
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "X",
    })

    # Generieren MIT apply_rules
    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": True
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("rules_applied") == True
    assert data.get("rule_count") == 1


def test_generate_response_no_warnings_without_rules(auth_client, db_session):
    """GenerateResponse hat keine Warnungen wenn keine Regeln existieren."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})

    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": False
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("rule_count") == 0
    assert data.get("rules_applied") == False
    assert data.get("warnings", []) == []


def test_generate_response_unreachable_value_warning(auth_client, db_session):
    """GenerateResponse warnt wenn Werte durch Regeln unerreichbar sind."""
    p = auth_client.post("/api/projects", json={"name": "Testprojekt"})
    pid = p.json()["id"]
    c = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie1"})
    cid = c.json()["id"]
    c2 = auth_client.post(f"/api/projects/{pid}/categories", json={"name": "Kategorie2"})
    cid2 = c2.json()["id"]
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "A"})
    auth_client.post(f"/api/categories/{cid}/values", json={"value": "B"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "X"})
    auth_client.post(f"/api/categories/{cid2}/values", json={"value": "Y"})

    # exclude: A+X und A+Y -> A ist unerreichbar in Kombination mit allen Werten von K2
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "X",
    })
    auth_client.post(f"/api/projects/{pid}/rules", json={
        "type": "exclude",
        "if_category_id": cid,
        "if_value": "A",
        "then_category_id": cid2,
        "then_value": "Y",
    })

    # Generieren MIT apply_rules
    r = auth_client.post(f"/api/projects/{pid}/generate", json={
        "strategy": "all",
        "apply_rules": True
    })
    assert r.status_code == 200
    data = r.json()
    # Wert A sollte als unerreichbar gemeldet werden
    warnings = data.get("warnings", [])
    has_unreachable = any("A" in w and "erreichbar" in w for w in warnings)
    assert has_unreachable, f"Keine Unreachable-Warnung fuer A gefunden: {warnings}"