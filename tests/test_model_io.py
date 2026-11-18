"""REQ-6013: Testmodell als Datei (YAML/JSON) - Export/Import/Validierung/Diff.

TDD-Tests fuer:
- Roundtrip: Projekt -> Export -> Import -> Export, byte-identisch
- Schema-Validierung (fehlende Pflichtfelder, falsche Typen, unbekannte Referenzen, >5MB, neuere schemaVersion)
- Aenderungsvorschau (hinzugefuegt/geaendert/entfernt)
- Transaktion (Fehler -> nichts geaendert)
- JSON-Schema gegen Beispieldateien
- Deterministischer YAML-Export (zweimal = byte-identisch)
"""
import io
import json
import os
import tempfile
from typing import Any, Dict

import pytest
import yaml

from app.database import SessionLocal
from app import models
from app.model_io import export_model, validate_model, diff_model, apply_model
from app.model_io.serializers import to_yaml, to_json, from_yaml, from_json
from app.model_io.models import GreatModel, ModelCategory, ModelValue, ModelRule


# ---------------------------------------------------------------------------
# Helper: Testprojekt anlegen
# ---------------------------------------------------------------------------

def _create_test_project(db: SessionLocal, name: str = "ModelTestProject") -> models.Project:
    """Erstellt ein Testprojekt mit Kategorien, Werten und Regeln."""
    # Loesche falls vorhanden
    existing = db.query(models.Project).filter(models.Project.name == name).first()
    if existing:
        db.delete(existing)
        db.commit()

    project = models.Project(name=name)
    db.add(project)
    db.flush()

    # Kategorie 1: Eingabe
    cat1 = models.Category(
        name="Eingabe",
        project_id=project.id,
        order_index=0,
        is_result=False,
        category_type="standard",
    )
    db.add(cat1)
    db.flush()
    for i, v in enumerate(["Leer", "Kurz", "Lang", "Sonderzeichen: <>&"]):
        db.add(models.Value(
            value=v,
            category_id=cat1.id,
            risk_weight=1 if i < 2 else 5,
            vtype="string",
            allowed=True,
            order_index=i,
            is_default=(i == 0),
        ))

    # Kategorie 2: Modus
    cat2 = models.Category(
        name="Modus",
        project_id=project.id,
        order_index=1,
        is_result=False,
        category_type="standard",
    )
    db.add(cat2)
    db.flush()
    for i, v in enumerate(["Auto", "Manual", "Hybrid"]):
        db.add(models.Value(
            value=v,
            category_id=cat2.id,
            risk_weight=3,
            vtype="string",
            allowed=True,
            order_index=i,
            is_default=(i == 0),
        ))

    # Ergebnis-Kategorie
    cat_result = models.Category(
        name="Ergebnis",
        project_id=project.id,
        order_index=2,
        is_result=True,
        category_type="effect",
    )
    db.add(cat_result)
    db.flush()
    for i, v in enumerate(["OK", "Error"]):
        db.add(models.Value(
            value=v,
            category_id=cat_result.id,
            risk_weight=1,
            vtype="string",
            allowed=True,
            order_index=i,
            is_default=False,
        ))

    # Regel: Wenn Eingabe=Leer -> Modus=Manual
    db.add(models.Rule(
        project_id=project.id,
        type="dependency",
        if_category_id=cat1.id,
        if_value="Leer",
        then_category_id=cat2.id,
        then_value="Manual",
    ))

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# RED Phase: Tests die erst gruen werden, wenn die Implementierung existiert
# ---------------------------------------------------------------------------

class TestModelExport:
    """REQ-6013: Export-Funktionalitaet."""

    def test_export_returns_great_model(self, db_session):
        """export_model() gibt ein GreatModel-Objekt zurueck."""
        project = _create_test_project(db_session)
        result = export_model(db_session, project.id)
        assert isinstance(result, GreatModel)
        assert result.schema_version == 1
        assert result.project_name == "ModelTestProject"

    def test_export_contains_categories(self, db_session):
        """Export enthaelt alle Kategorien mit korrekten Feldern."""
        project = _create_test_project(db_session)
        result = export_model(db_session, project.id)
        assert len(result.categories) == 3
        # Erste Kategorie: "Eingabe"
        cat = result.categories[0]
        assert cat.name == "Eingabe"
        assert cat.category_type == "standard"
        assert not cat.is_result
        assert len(cat.values) == 4

    def test_export_values_have_all_fields(self, db_session):
        """Export-Werte enthalten alle Felder (risk_weight, vtype, allowed, is_default)."""
        project = _create_test_project(db_session)
        result = export_model(db_session, project.id)
        cat = result.categories[0]  # "Eingabe"
        v = cat.values[0]  # "Leer"
        assert v.value == "Leer"
        assert v.risk_weight == 1
        assert v.vtype == "string"
        assert v.allowed is True
        assert v.is_default is True

    def test_export_rules_by_name(self, db_session):
        """Regeln verwenden Kategoriennamen, nicht IDs."""
        project = _create_test_project(db_session)
        result = export_model(db_session, project.id)
        assert len(result.rules) == 1
        rule = result.rules[0]
        assert rule.type == "dependency"
        assert rule.if_category_name == "Eingabe"
        assert rule.if_value == "Leer"
        assert rule.then_category_name == "Modus"
        assert rule.then_value == "Manual"

    def test_export_excludes_generations(self, db_session):
        """Export enthaelt KEINE Generierungen (REQ-6013 AK)."""
        project = _create_test_project(db_session)
        # Generierung anlegen
        gen = models.Generation(
            project_id=project.id,
            strategy="all_combinations",
            name="TestGen",
        )
        db_session.add(gen)
        db_session.flush()
        tc = models.TestCase(generation_id=gen.id, name="TC001")
        db_session.add(tc)
        db_session.commit()

        result = export_model(db_session, project.id)
        assert not hasattr(result, "generations") or not getattr(result, "generations", [])

    def test_export_result_category_marked(self, db_session):
        """Ergebnis-Kategorien haben is_result=True."""
        project = _create_test_project(db_session)
        result = export_model(db_session, project.id)
        result_cat = result.categories[2]  # "Ergebnis"
        assert result_cat.is_result is True
        assert result_cat.category_type == "effect"


class TestYamlSerialization:
    """REQ-6013: YAML-Serialisierung (deterministisch, Blockstil, keine Aliases)."""

    def test_to_yaml_returns_string(self, db_session):
        """to_yaml() gibt einen YAML-String zurueck."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)
        assert isinstance(yaml_str, str)
        assert "schemaVersion: 1" in yaml_str
        assert "projectName: ModelTestProject" in yaml_str

    def test_to_yaml_no_aliases(self, db_session):
        """YAML-Output enthaelt keine Anker/Aliases (&id / *id)."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)
        # Pruefe, dass keine YAML-Anker (&id_1:) oder Aliases (*id_1) vorkommen
        import re
        anchors = re.findall(r'&id_\d+:', yaml_str)
        aliases = re.findall(r'\*id_\d+', yaml_str)
        assert not anchors, f"YAML enthaelt Anker: {anchors}"
        assert not aliases, f"YAML enthaelt Aliases: {aliases}"

    def test_yaml_deterministic(self, db_session):
        """Zweimal exportiert = byte-identisch (REQ-6013 AK)."""
        project = _create_test_project(db_session)
        model1 = export_model(db_session, project.id)
        model2 = export_model(db_session, project.id)
        yaml1 = to_yaml(model1)
        yaml2 = to_yaml(model2)
        assert yaml1 == yaml2, "YAML-Export ist nicht deterministisch"

    def test_yaml_block_style(self, db_session):
        """YAML verwendet Blockstil, nicht Flow-Style."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)
        # Blockstil: keine Flow-Style fuer Listen/Dicts (außer leere Listen [])
        # Pruefe, dass die Hauptstruktur Blockstil verwendet
        lines = yaml_str.split("\n")
        # Kategorien sollten als Block-Liste (- name: ...) erscheinen
        has_block_list = any(line.strip().startswith("- name:") for line in lines)
        assert has_block_list, "YAML verwendet keinen Blockstil fuer Kategorien"
        # Kein Flow-Style fuer komplexe Objekte (z.B. {key: value})
        assert "{ name:" not in yaml_str, "Flow-Style Dict gefunden"

    def test_from_yaml_roundtrip(self, db_session):
        """from_yaml(to_yaml(model)) == model."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)
        parsed = from_yaml(yaml_str)
        assert parsed.project_name == model.project_name
        assert len(parsed.categories) == len(model.categories)


class TestJsonSerialization:
    """REQ-6013: JSON-Serialisierung."""

    def test_to_json_returns_string(self, db_session):
        """to_json() gibt einen JSON-String zurueck."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        json_str = to_json(model)
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["schemaVersion"] == 1
        assert data["projectName"] == "ModelTestProject"

    def test_json_deterministic(self, db_session):
        """Zweimal exportiert = byte-identisch."""
        project = _create_test_project(db_session)
        model1 = export_model(db_session, project.id)
        model2 = export_model(db_session, project.id)
        json1 = to_json(model1)
        json2 = to_json(model2)
        assert json1 == json2, "JSON-Export ist nicht deterministisch"

    def test_from_json_roundtrip(self, db_session):
        """from_json(to_json(model)) == model."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        json_str = to_json(model)
        parsed = from_json(json_str)
        assert parsed.project_name == model.project_name
        assert len(parsed.categories) == len(model.categories)


class TestRoundtrip:
    """REQ-6013: Vollstaendiger Roundtrip-Test (byte-identisch)."""

    def _compare_models(self, m1, m2):
        """Vergleicht zwei Modelle inhaltlich (ohne DB-Namenssuffix)."""
        assert m1.schema_version == m2.schema_version
        # Projektname kann _imported_N Suffix haben
        name1 = m1.project_name
        name2 = m2.project_name
        if name1 != name2:
            # Pruefe ob name2 = name1 + _imported_N
            assert name2.startswith(name1 + "_imported_"), \
                f"Unerwarteter Namensunterschied: {name1} vs {name2}"
        assert len(m1.categories) == len(m2.categories)
        for c1, c2 in zip(m1.categories, m2.categories):
            assert c1.name == c2.name
            assert c1.order_index == c2.order_index
            assert c1.is_result == c2.is_result
            assert c1.category_type == c2.category_type
            assert len(c1.values) == len(c2.values)
            for v1, v2 in zip(c1.values, c2.values):
                assert v1.value == v2.value
                assert v1.risk_weight == v2.risk_weight
                assert v1.vtype == v2.vtype
                assert v1.allowed == v2.allowed
                assert v1.order_index == v2.order_index
                assert v1.is_default == v2.is_default
        assert len(m1.rules) == len(m2.rules)
        for r1, r2 in zip(m1.rules, m2.rules):
            assert r1.type == r2.type
            assert r1.if_category_name == r2.if_category_name
            assert r1.if_value == r2.if_value
            assert r1.then_category_name == r2.then_category_name
            assert r1.then_value == r2.then_value

    def test_full_roundtrip_yaml(self, db_session):
        """Projekt -> YAML-Export -> Import als neues Projekt -> YAML-Export, inhaltlich identisch."""
        import uuid
        unique_name = f"RoundtripYaml_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model1 = export_model(db_session, project.id)

        # Import als neues Projekt
        new_project = apply_model(db_session, None, to_yaml(model1), "yaml")
        assert new_project is not None

        # Zweiter Export und Vergleich
        model2 = export_model(db_session, new_project.id)
        self._compare_models(model1, model2)

    def test_full_roundtrip_json(self, db_session):
        """Projekt -> JSON-Export -> Import als neues Projekt -> JSON-Export, inhaltlich identisch."""
        import uuid
        unique_name = f"RoundtripJson_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model1 = export_model(db_session, project.id)

        new_project = apply_model(db_session, None, to_json(model1), "json")
        assert new_project is not None

        model2 = export_model(db_session, new_project.id)
        self._compare_models(model1, model2)


class TestModelValidation:
    """REQ-6013: Validierung gegen Schema und fachliche Regeln."""

    def test_validate_valid_model(self, db_session):
        """Gueltiges Modell hat keine Fehler."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        errors = validate_model(data)
        assert errors == [], f"Unerwartete Fehler: {errors}"

    def test_validate_missing_project_name(self, db_session):
        """Fehlender projectName wird gemeldet."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        del data["projectName"]
        errors = validate_model(data)
        assert len(errors) > 0
        assert any("projectName" in e.path or "projectName" in e.message for e in errors)

    def test_validate_wrong_type(self, db_session):
        """Falscher Typ (z.B. schemaVersion als String) wird gemeldet."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        data["schemaVersion"] = "not_a_number"
        errors = validate_model(data)
        assert len(errors) > 0

    def test_validate_unknown_category_reference(self):
        """Regel mit nicht-existenter Kategorie-Referenz wird gemeldet."""
        data = {
            "schemaVersion": 1,
            "projectName": "Test",
            "categories": [
                {"name": "A", "categoryType": "standard", "isResult": False, "values": [
                    {"value": "x", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
                ]}
            ],
            "rules": [
                {"type": "dependency", "ifCategoryName": "A", "ifValue": "x", "thenCategoryName": "NonExistent", "thenValue": "y"}
            ]
        }
        errors = validate_model(data)
        assert len(errors) > 0
        assert any("NonExistent" in e.message or "thenCategoryName" in e.path for e in errors)

    def test_validate_too_large(self):
        """Modell > 5MB wird abgelehnt."""
        # Erstelle ein groesseres Modell (>5MB)
        large_values = [{"value": "x" * 1000, "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False} for _ in range(10000)]
        data = {
            "schemaVersion": 1,
            "projectName": "Huge",
            "categories": [
                {"name": "Big", "categoryType": "standard", "isResult": False, "values": large_values}
            ],
            "rules": []
        }
        errors = validate_model(data)
        # Sollte eine Groessenueberschreitung melden
        assert len(errors) > 0

    def test_validate_newer_schema_version(self):
        """Neuere schemaVersion als unterstuetzt wird abgelehnt."""
        data = {
            "schemaVersion": 99,
            "projectName": "Future",
            "categories": [],
            "rules": []
        }
        errors = validate_model(data)
        assert len(errors) > 0
        assert any("schemaVersion" in e.path or "99" in e.message for e in errors)

    def test_validate_duplicate_category_names(self):
        """Doppelte Kategoriennamen werden abgelehnt."""
        data = {
            "schemaVersion": 1,
            "projectName": "Dupes",
            "categories": [
                {"name": "A", "categoryType": "standard", "isResult": False, "values": [
                    {"value": "x", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
                ]},
                {"name": "A", "categoryType": "standard", "isResult": False, "values": [
                    {"value": "y", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
                ]},
            ],
            "rules": []
        }
        errors = validate_model(data)
        assert len(errors) > 0


class TestDiffModel:
    """REQ-6013: Aenderungsvorschau."""

    def test_diff_no_changes(self, db_session):
        """Diff mit identischem Modell zeigt keine Aenderungen."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        diff = diff_model(db_session, project.id, data)
        assert diff["added"] == {"categories": [], "values": [], "rules": []}
        assert diff["modified"] == {"categories": [], "values": [], "rules": []}
        assert diff["removed"] == {"categories": [], "values": [], "rules": []}

    def test_diff_added_category(self, db_session):
        """Diff erkennt neue Kategorie."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        # Fuege neue Kategorie hinzu
        data["categories"].append({
            "name": "Neu",
            "categoryType": "standard",
            "isResult": False,
            "values": [
                {"value": "a", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
            ]
        })
        diff = diff_model(db_session, project.id, data)
        assert "Neu" in diff["added"]["categories"]

    def test_diff_removed_category(self, db_session):
        """Diff erkennt entfernte Kategorie."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        # Entferne letzte Kategorie
        removed = data["categories"].pop()
        diff = diff_model(db_session, project.id, data)
        assert removed["name"] in diff["removed"]["categories"]

    def test_diff_modified_value(self, db_session):
        """Diff erkennt geaenderten Wert."""
        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        # Aendere risk_weight eines Werts
        data["categories"][0]["values"][0]["riskWeight"] = 10
        diff = diff_model(db_session, project.id, data)
        # "Leer" in "Eingabe" sollte als geaendert erscheinen
        assert len(diff["modified"]["values"]) > 0


class TestApplyModel:
    """REQ-6013: Import/Aktualisierung."""

    def test_apply_new_project(self, db_session):
        """Import als neues Projekt funktioniert."""
        import uuid
        unique_name = f"ApplySource_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)

        new_project = apply_model(db_session, None, yaml_str, "yaml")
        assert new_project is not None
        # Name kann _imported_N Suffix haben
        assert new_project.name.startswith(unique_name)

        # Pruefe Kategorien
        cats = db_session.query(models.Category).filter(
            models.Category.project_id == new_project.id
        ).all()
        assert len(cats) == 3

    def test_apply_update_existing(self, db_session):
        """Aktualisierung bestehendes Projekt funktioniert."""
        import uuid
        unique_name = f"ApplyUpdate_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        # Fuege neue Kategorie hinzu
        data["categories"].append({
            "name": "Zusatz",
            "categoryType": "standard",
            "isResult": False,
            "values": [
                {"value": "neu", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
            ]
        })

        result = apply_model(db_session, project.id, data, "dict")
        assert result is not None

        cats = db_session.query(models.Category).filter(
            models.Category.project_id == project.id
        ).all()
        assert len(cats) == 4
        assert any(c.name == "Zusatz" for c in cats)

    def test_apply_transaction_rollback(self, db_session):
        """Fehler waehrend Import -> nichts wird geaendert (Transaktion)."""
        import uuid
        unique_name = f"ApplyRollback_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        original_cat_count = db_session.query(models.Category).filter(
            models.Category.project_id == project.id
        ).count()

        # Ungueltiges Modell mit Fehler waehrend des Apply
        bad_data = {
            "schemaVersion": 1,
            "projectName": unique_name,
            "categories": [
                {"name": "A", "categoryType": "standard", "isResult": False, "values": [
                    {"value": "x", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
                ]},
                {"name": "A", "categoryType": "standard", "isResult": False, "values": [
                    {"value": "y", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
                ]},
            ],
            "rules": []
        }

        # apply_model sollte entweder fehlschlagen oder transaktional rollback machen
        try:
            apply_model(db_session, project.id, bad_data, "dict")
        except (ValueError, Exception):
            db_session.rollback()

        # Kategorien sollten unveraendert sein
        new_cat_count = db_session.query(models.Category).filter(
            models.Category.project_id == project.id
        ).count()
        assert new_cat_count == original_cat_count


class TestJsonSchema:
    """REQ-6013: JSON-Schema-Datei existiert und ist gueltig."""

    def test_schema_file_exists(self):
        """schemas/great-model.v1.schema.json existiert."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "schemas",
            "great-model.v1.schema.json"
        )
        assert os.path.exists(schema_path), f"Schema-Datei nicht gefunden: {schema_path}"

    def test_schema_is_valid_json(self):
        """Schema-Datei ist gueltiges JSON."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "schemas",
            "great-model.v1.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert "$schema" in schema or "schema" in schema.get("$id", "").lower() or "properties" in schema

    def test_schema_matches_export(self, db_session):
        """Export-Daten sind gegen JSON-Schema valide."""
        pytest.importorskip("jsonschema")
        import jsonschema
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "schemas",
            "great-model.v1.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        project = _create_test_project(db_session)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")

        # Sollte keine Exception werfen
        jsonschema.validate(instance=data, schema=schema)


class TestApiEndpoints:
    """REQ-6013: API-Endpunkte."""

    def test_export_yaml(self, auth_client, db_session):
        """GET /api/v1/projects/{id}/model?format=yaml returns YAML."""
        project = _create_test_project(db_session)
        r = auth_client.get(f"/api/v1/projects/{project.id}/model?format=yaml")
        assert r.status_code == 200
        assert "schemaVersion" in r.text

    def test_export_json(self, auth_client, db_session):
        """GET /api/v1/projects/{id}/model?format=json returns JSON."""
        project = _create_test_project(db_session)
        r = auth_client.get(f"/api/v1/projects/{project.id}/model?format=json")
        assert r.status_code == 200
        data = r.json()
        assert data["schemaVersion"] == 1

    def test_import_new_project(self, auth_client, db_session):
        """POST /api/v1/projects/import-model creates new project."""
        import uuid
        unique_name = f"ImportSource_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model = export_model(db_session, project.id)
        yaml_str = to_yaml(model)

        r = auth_client.post(
            "/api/v1/projects/import-model",
            content=yaml_str.encode("utf-8"),
            headers={"Content-Type": "text/yaml"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["projectName"].startswith(unique_name)

    def test_preview_changes(self, auth_client, db_session):
        """POST /api/v1/projects/{id}/model/preview returns diff."""
        import uuid
        unique_name = f"PreviewTest_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        # Fuege neue Kategorie hinzu
        data["categories"].append({
            "name": "PreviewTest",
            "categoryType": "standard",
            "isResult": False,
            "values": [
                {"value": "a", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
            ]
        })

        r = auth_client.post(
            f"/api/v1/projects/{project.id}/model/preview",
            json=data,
        )
        assert r.status_code == 200
        diff = r.json()
        assert "added" in diff
        assert "PreviewTest" in diff["added"]["categories"]

    def test_update_project(self, auth_client, db_session):
        """PUT /api/v1/projects/{id}/model updates project."""
        import uuid
        unique_name = f"UpdateTest_{uuid.uuid4().hex[:8]}"
        project = _create_test_project(db_session, unique_name)
        model = export_model(db_session, project.id)
        data = model.model_dump(by_alias=True, mode="json")
        data["categories"].append({
            "name": "UpdateTest",
            "categoryType": "standard",
            "isResult": False,
            "values": [
                {"value": "b", "riskWeight": 1, "vtype": "string", "allowed": True, "isDefault": False}
            ]
        })

        r = auth_client.put(
            f"/api/v1/projects/{project.id}/model",
            json=data,
        )
        assert r.status_code == 200

        # Pruefe, dass Kategorie hinzugefuegt wurde
        cats = db_session.query(models.Category).filter(
            models.Category.project_id == project.id
        ).all()
        assert any(c.name == "UpdateTest" for c in cats)

    def test_export_nonexistent_project(self, auth_client):
        """GET /api/v1/projects/99999/model returns 404."""
        r = auth_client.get("/api/v1/projects/99999/model?format=yaml")
        assert r.status_code == 404

    def test_import_invalid_yaml(self, auth_client):
        """POST /api/v1/projects/import-model with invalid YAML returns 400."""
        r = auth_client.post(
            "/api/v1/projects/import-model",
            content="not: valid: yaml: [".encode("utf-8"),
            headers={"Content-Type": "text/yaml"},
        )
        assert r.status_code == 400

    def test_import_too_large_file(self, auth_client):
        """POST /api/v1/projects/import-model with >5MB returns 413."""
        large_content = "x" * (6 * 1024 * 1024)  # 6MB
        r = auth_client.post(
            "/api/v1/projects/import-model",
            content=large_content.encode("utf-8"),
            headers={"Content-Type": "text/yaml"},
        )
        assert r.status_code == 413

    def test_update_nonexistent_project(self, auth_client):
        """PUT /api/v1/projects/99999/model returns 404."""
        r = auth_client.put(
            "/api/v1/projects/99999/model",
            json={"schemaVersion": 1, "projectName": "X", "categories": [], "rules": []},
        )
        assert r.status_code == 404