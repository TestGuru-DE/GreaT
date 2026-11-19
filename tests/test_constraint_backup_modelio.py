"""REQ-6001 AK-10: Tests fuer Constraints in Backup und Modell-Export/Import.

Testet:
1. Export: Constraints werden mit Namen statt IDs exportiert
2. Import: Constraints werden mit IDs wieder importiert
3. Roundtrip: export -> import -> gleiche Daten
4. Backup-Roundtrip: backup -> restore -> gleiche Daten
5. Loesch-Hinweis Kategorie: Constraint wird is_valid=False
6. Loesch-Hinweis Wert: Constraint wird is_valid=False
7. Ungueltige Referenzen beim Import: is_valid=False
"""
from __future__ import annotations

import json
import io
import zipfile
import pytest

from sqlalchemy.orm import Session

from app import models
from app.database import Base, get_db
from app.model_io.exporter import export_model
from app.model_io.applier import apply_model
from app.model_io.models import GreatModel, ModelConstraint
from app.routers.api_backup import _export_data, _restore_data
from app.schemas import BackupSchema
from app.services import force_delete_category, force_delete_value


# ---------------------------------------------------------------------------
# Test-DB-Hilfe
# ---------------------------------------------------------------------------

@pytest.fixture
def db(db_session):
    """Frische Test-DB pro Test."""
    return db_session


def _make_project(db: Session, name: str = "TestProjekt") -> models.Project:
    p = models.Project(name=name)
    db.add(p)
    db.flush()
    return p


def _make_category(db: Session, project: models.Project, name: str,
                   order_index: int = 0) -> models.Category:
    c = models.Category(name=name, project_id=project.id, order_index=order_index)
    db.add(c)
    db.flush()
    return c


def _make_value(db: Session, category: models.Category, value: str,
                order_index: int = 0) -> models.Value:
    v = models.Value(value=value, category_id=category.id, order_index=order_index)
    db.add(v)
    db.flush()
    return v


def _make_constraint(db: Session, project: models.Project, name: str,
                     kind: str, expression: dict,
                     is_valid: bool = True) -> models.Constraint:
    import json as json_mod
    c = models.Constraint(
        project_id=project.id,
        name=name,
        kind=kind,
        expression_json=json_mod.dumps(expression, ensure_ascii=False),
        is_valid=is_valid,
    )
    db.add(c)
    db.flush()
    return c


# ---------------------------------------------------------------------------
# Test 1: Export konvertiert category_id/value_id zu Namen
# ---------------------------------------------------------------------------

def test_export_constraint_ids_to_names(db: Session):
    # REQ-6001 AK-10: Export verwendet Namen statt IDs
    project = _make_project(db, "ExportTest")
    cat_a = _make_category(db, project, "Farbe", 0)
    cat_b = _make_category(db, project, "Groesse", 1)
    val_red = _make_value(db, cat_a, "Rot", 0)
    val_big = _make_value(db, cat_b, "Groß", 0)

    expr = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_red.id,
        },
    }
    _make_constraint(db, project, "Kein Rot", "forbid", expr)
    db.commit()

    model = export_model(db, project.id)

    assert len(model.constraints) == 1
    c = model.constraints[0]
    assert c.name == "Kein Rot"
    assert c.kind == "forbid"
    assert c.is_valid is True
    # category_id und value_id sollten zu Namen konvertiert sein
    assert c.expression["condition"]["category_id"] == "Farbe"
    assert c.expression["condition"]["value_id"] == "Rot"


# ---------------------------------------------------------------------------
# Test 2: Import konvertiert Namen zurueck zu IDs
# ---------------------------------------------------------------------------

def test_import_constraint_names_to_ids(db: Session):
    # REQ-6001 AK-10: Import mappt Namen zurueck zu IDs
    # Import als NEUES Projekt (nicht Update), damit Kategorien vorhanden sind
    model = GreatModel(
        schema_version=1,
        project_name="ImportTestNeu",
        categories=[
            {
                "name": "Farbe",
                "order_index": 0,
                "is_result": False,
                "category_type": "standard",
                "values": [
                    {"value": "Rot", "risk_weight": 1, "vtype": "string", "allowed": True, "order_index": 0, "is_default": False},
                ],
            },
            {
                "name": "Groesse",
                "order_index": 1,
                "is_result": False,
                "category_type": "standard",
                "values": [
                    {"value": "Groß", "risk_weight": 1, "vtype": "string", "allowed": True, "order_index": 0, "is_default": False},
                ],
            },
        ],
        rules=[],
        constraints=[
            ModelConstraint(
                name="Kein Rot",
                kind="forbid",
                expression={
                    "kind": "forbid",
                    "condition": {
                        "op": "eq",
                        "category_id": "Farbe",
                        "value_id": "Rot",
                    },
                },
                is_valid=True,
            ),
        ],
    )

    result = apply_model(db, None, model.model_dump(mode="json"), format="dict")
    db.refresh(result)

    constraints = db.query(models.Constraint).filter(
        models.Constraint.project_id == result.id
    ).all()
    assert len(constraints) == 1
    c = constraints[0]
    assert c.name == "Kein Rot"
    assert c.kind == "forbid"
    assert c.is_valid is True
    # expression_json is stored as JSON string -> parse it
    import json as json_mod
    expr = json_mod.loads(c.expression_json)
    # category_id und value_id sollten IDs sein (nicht Namen)
    assert isinstance(expr["condition"]["category_id"], int)
    assert isinstance(expr["condition"]["value_id"], int)


# ---------------------------------------------------------------------------
# Test 3: Export-Import-Roundtrip
# ---------------------------------------------------------------------------

def test_export_import_roundtrip(db: Session):
    # REQ-6001 AK-10: Roundtrip praeserviert Constraints
    project = _make_project(db, "RoundtripTest")
    cat_a = _make_category(db, project, "Land", 0)
    cat_b = _make_category(db, project, "Zahlart", 1)
    val_de = _make_value(db, cat_a, "DE", 0)
    val_us = _make_value(db, cat_a, "US", 1)
    val_inv = _make_value(db, cat_b, "Rechnung", 0)

    expr = {
        "kind": "implies",
        "condition": {
            "op": "in",
            "category_id": cat_a.id,
            "value_ids": [val_de.id, val_us.id],
        },
        "consequence": {
            "op": "eq",
            "category_id": cat_b.id,
            "value_id": val_inv.id,
        },
    }
    _make_constraint(db, project, "Land->Zahlart", "implies", expr)
    db.commit()

    # Export
    model = export_model(db, project.id)
    assert len(model.constraints) == 1

    # Neue DB: Projekt loeschen und neu importieren
    db.query(models.Constraint).filter(
        models.Constraint.project_id == project.id
    ).delete(synchronize_session=False)
    db.commit()

    # Import
    result = apply_model(db, project.id, model.model_dump(mode="json"), format="dict")
    db.refresh(result)

    constraints = db.query(models.Constraint).filter(
        models.Constraint.project_id == project.id
    ).all()
    assert len(constraints) == 1
    c = constraints[0]
    assert c.name == "Land->Zahlart"
    assert c.kind == "implies"
    assert c.is_valid is True
    import json as json_mod2
    expr = json_mod2.loads(c.expression_json)
    assert expr["condition"]["category_id"] == cat_a.id
    assert expr["condition"]["value_ids"] == [val_de.id, val_us.id]
    assert expr["consequence"]["category_id"] == cat_b.id
    assert expr["consequence"]["value_id"] == val_inv.id


# ---------------------------------------------------------------------------
# Test 4: Backup-Roundtrip
# ---------------------------------------------------------------------------

def test_backup_roundtrip(db: Session):
    # REQ-6001 AK-10: Backup export enthaelt Constraints mit Namen statt IDs
    project = _make_project(db, "BackupTestUnique2")
    cat_a = _make_category(db, project, "Status", 0)
    val_open = _make_value(db, cat_a, "Offen", 0)
    val_closed = _make_value(db, cat_a, "Geschlossen", 1)

    expr = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_open.id,
        },
    }
    _make_constraint(db, project, "Kein Offen", "forbid", expr)
    db.commit()

    # Export via _export_data
    backup_data = _export_data(db)
    # Finde unser Projekt im Backup
    our_project = next((p for p in backup_data["projects"] if p["name"] == "BackupTestUnique2"), None)
    assert our_project is not None
    assert len(our_project["constraints"]) == 1
    c_backup = our_project["constraints"][0]
    assert c_backup["name"] == "Kein Offen"
    assert c_backup["kind"] == "forbid"
    # Namen statt IDs
    assert c_backup["expression"]["condition"]["category_id"] == "Status"
    assert c_backup["expression"]["condition"]["value_id"] == "Offen"

    # Schema-Validierung
    backup_schema = BackupSchema.model_validate(backup_data)
    our_schema = next((p for p in backup_schema.projects if p.name == "BackupTestUnique2"), None)
    assert our_schema is not None
    assert len(our_schema.constraints) == 1
    assert our_schema.constraints[0].name == "Kein Offen"


# ---------------------------------------------------------------------------
# Test 5: Kategorie loeschen -> Constraint wird is_valid=False
# ---------------------------------------------------------------------------

def test_delete_category_invalidates_constraint(db: Session):
    # REQ-6001 AK-10 AK: Loesch-Hinweis
    project = _make_project(db, "DeleteCatTest")
    cat_a = _make_category(db, project, "Farbe", 0)
    val_red = _make_value(db, cat_a, "Rot", 0)

    expr = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_red.id,
        },
    }
    constraint = _make_constraint(db, project, "Kein Rot", "forbid", expr)
    db.commit()

    # Kategorie loeschen
    force_delete_category(db, cat_a.id)
    db.commit()

    # Constraint sollte is_valid=False sein
    db.refresh(constraint)
    assert constraint.is_valid is False


def test_delete_category_does_not_affect_other_constraints(db: Session):
    # REQ-6001 AK-10: Nur betroffene Constraints werden invalidated
    project = _make_project(db, "DeleteCatOtherTest")
    cat_a = _make_category(db, project, "Farbe", 0)
    cat_b = _make_category(db, project, "Groesse", 1)
    val_red = _make_value(db, cat_a, "Rot", 0)
    val_big = _make_value(db, cat_b, "Groß", 0)

    expr_a = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_red.id,
        },
    }
    expr_b = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_b.id,
            "value_id": val_big.id,
        },
    }
    c_a = _make_constraint(db, project, "Kein Rot", "forbid", expr_a)
    c_b = _make_constraint(db, project, "Kein Gross", "forbid", expr_b)
    db.commit()

    # Nur cat_a loeschen
    force_delete_category(db, cat_a.id)
    db.commit()

    db.refresh(c_a)
    db.refresh(c_b)
    assert c_a.is_valid is False
    assert c_b.is_valid is True


# ---------------------------------------------------------------------------
# Test 6: Wert loeschen -> Constraint wird is_valid=False
# ---------------------------------------------------------------------------

def test_delete_value_invalidates_constraint(db: Session):
    # REQ-6001 AK-10 AK: Loesch-Hinweis fuer Werte
    project = _make_project(db, "DeleteValTest")
    cat_a = _make_category(db, project, "Status", 0)
    val_open = _make_value(db, cat_a, "Offen", 0)
    val_closed = _make_value(db, cat_a, "Geschlossen", 1)

    expr = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_open.id,
        },
    }
    constraint = _make_constraint(db, project, "Kein Offen", "forbid", expr)
    db.commit()

    # Wert loeschen
    force_delete_value(db, val_open.id)
    db.commit()

    db.refresh(constraint)
    assert constraint.is_valid is False


def test_delete_value_does_not_affect_other_value_constraint(db: Session):
    # REQ-6001 AK-10: Nur Constraints mit dem geloeschten Wert
    project = _make_project(db, "DeleteValOtherTest")
    cat_a = _make_category(db, project, "Status", 0)
    val_open = _make_value(db, cat_a, "Offen", 0)
    val_closed = _make_value(db, cat_a, "Geschlossen", 1)

    expr_open = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_open.id,
        },
    }
    expr_closed = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_closed.id,
        },
    }
    c_open = _make_constraint(db, project, "Kein Offen", "forbid", expr_open)
    c_closed = _make_constraint(db, project, "Kein Geschlossen", "forbid", expr_closed)
    db.commit()

    force_delete_value(db, val_open.id)
    db.commit()

    db.refresh(c_open)
    db.refresh(c_closed)
    assert c_open.is_valid is False
    assert c_closed.is_valid is True


# ---------------------------------------------------------------------------
# Test 7: Import mit ungueltiger Referenz -> is_valid=False
# ---------------------------------------------------------------------------

def test_import_invalid_reference(db: Session):
    # REQ-6001 AK-10: Ungueltige Referenzen beim Import
    model = GreatModel(
        schema_version=1,
        project_name="InvalidRefTestNeu",
        categories=[
            {
                "name": "Farbe",
                "order_index": 0,
                "is_result": False,
                "category_type": "standard",
                "values": [
                    {"value": "Rot", "risk_weight": 1, "vtype": "string", "allowed": True, "order_index": 0, "is_default": False},
                ],
            },
        ],
        rules=[],
        constraints=[
            ModelConstraint(
                name="Kein Gruen",
                kind="forbid",
                expression={
                    "kind": "forbid",
                    "condition": {
                        "op": "eq",
                        "category_id": "NichtExistierende",  # existiert nicht
                        "value_id": "Grün",
                    },
                },
                is_valid=True,
            ),
        ],
    )

    result = apply_model(db, None, model.model_dump(mode="json"), format="dict")
    db.refresh(result)

    constraints = db.query(models.Constraint).filter(
        models.Constraint.project_id == result.id
    ).all()
    assert len(constraints) == 1
    c = constraints[0]
    assert c.name == "Kein Gruen"
    assert c.is_valid is False  # ungueltige Referenz -> invalid


# ---------------------------------------------------------------------------
# Test 8: Backup Schema Validation
# ---------------------------------------------------------------------------

def test_backup_schema_validates_constraints(db: Session):
    # REQ-6001 AK-10: BackupSchema akzeptiert constraints
    project = _make_project(db, "SchemaTestUnique")
    cat_a = _make_category(db, project, "TestCat", 0)
    val_a = _make_value(db, cat_a, "TestVal", 0)

    expr = {
        "kind": "forbid",
        "condition": {
            "op": "eq",
            "category_id": cat_a.id,
            "value_id": val_a.id,
        },
    }
    _make_constraint(db, project, "TestConstraint", "forbid", expr)
    db.commit()

    backup_data = _export_data(db)
    # Schema-Validierung sollte erfolgreich sein
    backup_schema = BackupSchema.model_validate(backup_data)
    # Finde unser Projekt
    our_project = next((p for p in backup_schema.projects if p.name == "SchemaTestUnique"), None)
    assert our_project is not None
    assert len(our_project.constraints) == 1
    assert our_project.constraints[0].name == "TestConstraint"