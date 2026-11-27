"""Beispielprojekte (REQ-4017): beim ersten Start und nach dem Zuruecksetzen vorhanden,
vom Nutzer loeschbar, fachlich vollstaendig (Ergebnis-Kategorie, Regeln, Constraints, Entscheidungstabelle)."""
import pytest

from app.database import SessionLocal
from app.models import AppState, Category, Constraint, Project, Rule
from app.seed_example import EXAMPLE_PROJECT_NAME, seed_example_project

PORTO = EXAMPLE_PROJECT_NAME
RULES = "Lieferbedingungen – Regeln (Beispiel)"
CONSTRAINTS = "Versandkosten – Constraints (Beispiel)"
DECISION = "Retourenabwicklung – Entscheidungstabelle (Beispiel)"
ALL = [PORTO, RULES, CONSTRAINTS, DECISION]


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fresh_examples(db):
    """Zustand wie nach dem Zuruecksetzen: alle Beispiele frisch angelegt."""
    from app.services import reset_database_state
    reset_database_state(db)
    return {p.name: p.id for p in db.query(Project).filter(Project.name.in_(ALL))}


def _project(db, name):
    return db.query(Project).filter(Project.name == name).one()


def test_all_examples_exist_after_reset(fresh_examples):
    assert sorted(fresh_examples) == sorted(ALL)


def test_first_start_seeds_examples_and_sets_marker(db, fresh_examples):
    assert db.get(AppState, "examples_version") is not None


def test_deleted_example_is_not_recreated_on_restart(db, fresh_examples, admin_client):
    assert admin_client.delete(f"/api/projects/{fresh_examples[RULES]}").status_code == 200
    created = seed_example_project(db)  # wie beim naechsten Start
    assert created == []
    assert db.query(Project).filter(Project.name == RULES).first() is None


def test_reset_brings_deleted_examples_back(db, fresh_examples, admin_client):
    admin_client.delete(f"/api/projects/{fresh_examples[PORTO]}")
    from app.services import reset_database_state
    reset_database_state(db)
    assert db.query(Project).filter(Project.name == PORTO).count() == 1


def test_porto_price_is_a_real_result_category(db, fresh_examples):
    category = db.query(Category).filter(Category.project_id == fresh_examples[PORTO],
                                         Category.name == "Portopreis").one()
    assert category.is_result is True


def test_legacy_porto_result_category_is_fixed(db, fresh_examples):
    category = db.query(Category).filter(Category.project_id == fresh_examples[PORTO],
                                         Category.name == "Portopreis").one()
    category.name, category.is_result = "Portopreis (Ergebnis)", False
    db.get(AppState, "examples_version").value = "1"
    db.commit()
    seed_example_project(db)
    db.refresh(category)
    assert (category.name, category.is_result) == ("Portopreis", True)


def test_porto_generation_leaves_price_for_the_tester(auth_client, fresh_examples):
    gid = auth_client.post(f"/api/projects/{fresh_examples[PORTO]}/generate",
                           json={"strategy": "pairwise"}).json()["generation_id"]
    tcs = auth_client.get(f"/api/generations/{gid}/testcases").json()["testcases"]
    assert tcs and all(tc["assignments"]["Portopreis"] == "" for tc in tcs)


def test_rules_example_has_four_or_more_rules_of_all_types(db, fresh_examples, auth_client):
    rules = db.query(Rule).filter(Rule.project_id == fresh_examples[RULES]).all()
    assert len(rules) >= 4
    assert {r.type for r in rules} == {"dependency", "exclude", "combine"}
    resp = auth_client.post(f"/api/projects/{fresh_examples[RULES]}/generate",
                            json={"strategy": "pairwise", "apply_rules": True})
    assert resp.status_code == 200
    tcs = auth_client.get(f"/api/generations/{resp.json()['generation_id']}/testcases").json()["testcases"]
    for tc in tcs:
        a = tc["assignments"]
        assert not (a["Zahlungsart"] == "Nachnahme" and a["Zielland"] == "Schweiz")
        assert a["Versandart"] != "Abholung im Laden" or a["Zielland"] == "Deutschland"


def test_constraints_example_has_three_or_more_valid_constraints(db, fresh_examples, auth_client):
    constraints = db.query(Constraint).filter(Constraint.project_id == fresh_examples[CONSTRAINTS]).all()
    assert len(constraints) >= 3
    assert all(c.is_valid for c in constraints)
    assert {c.kind for c in constraints} == {"forbid", "implies"}
    resp = auth_client.post(f"/api/projects/{fresh_examples[CONSTRAINTS]}/generate",
                            json={"strategy": "pairwise", "apply_rules": True})
    assert resp.status_code == 200
    assert resp.json()["warnings"] == []
    tcs = auth_client.get(f"/api/generations/{resp.json()['generation_id']}/testcases").json()["testcases"]
    for tc in tcs:
        a = tc["assignments"]
        assert a["Gewicht"] != "über 10 kg" or a["Versandart"] == "Spedition"
        assert not (a["Gutschein"] == "versandkostenfrei" and a["Zielland"] == "Weltweit")


def test_decision_table_example_generates_eight_rules(fresh_examples, auth_client):
    resp = auth_client.post("/api/decision-table/generate", json={"project_id": fresh_examples[DECISION]})
    assert resp.status_code == 200, resp.text
    table = resp.json()
    assert len(table["causes"]) == 3
    assert len(table["effects"]) == 3
    assert len(table["rules"]) == 8
