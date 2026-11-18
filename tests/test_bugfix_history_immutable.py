"""
tests/test_bugfix_history_immutable.py
B-18: Generierungshistorie unveraenderlich machen.

Wenn eine Kategorie geloescht oder umbenannt wird, bleiben die Spaltennamen
in bereits gespeicherten Generierungen erhalten (via category_name-Schnappschuss).
"""
import uuid

import pytest

from app.main import app
from app.database import Base, get_db, SessionLocal
from app import models


def _override_get_db():
    """Override fuer get_db – verwendet die gemeinsame Test-DB aus conftest."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Stellt sicher, dass die Test-DB-Schema vorhanden ist und ueberschreibt get_db."""
    Base.metadata.create_all(bind=SessionLocal().get_bind())
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(auth_client):
    return auth_client


@pytest.fixture
def project_with_gen(client):
    """Erstellt ein Projekt mit 2 Kategorien, Werten und einer Generierung."""
    project_name = f"B18-{uuid.uuid4().hex[:8]}"
    r = client.post("/api/projects", json={"name": project_name})
    assert r.status_code == 200
    pid = r.json()["id"]

    # Kategorie A
    r = client.post(f"/api/projects/{pid}/categories", json={"name": "KategorieA", "order_index": 0})
    assert r.status_code == 200
    cid_a = r.json()["id"]
    for val in ["A1", "A2"]:
        r = client.post(f"/api/categories/{cid_a}/values", json={"value": val})
        assert r.status_code == 200

    # Kategorie B
    r = client.post(f"/api/projects/{pid}/categories", json={"name": "KategorieB", "order_index": 1})
    assert r.status_code == 200
    cid_b = r.json()["id"]
    for val in ["B1", "B2"]:
        r = client.post(f"/api/categories/{cid_b}/values", json={"value": val})
        assert r.status_code == 200

    # Generieren
    r = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
    assert r.status_code == 200
    gen_id = r.json()["generation_id"]

    return {"project_id": pid, "gen_id": gen_id, "cat_a_id": cid_a, "cat_b_id": cid_b}


class TestCategoryDeleteKeepsHistory:
    """B-18: Loeschen einer Kategorie behaltet alte Generierungsspalten."""

    def test_deleting_category_keeps_old_generation_columns(self, client, project_with_gen):
        """Nach Loeschen von KategorieA bleiben deren Werte in alten Generierungen sichtbar."""
        pid = project_with_gen["project_id"]
        gen_id = project_with_gen["gen_id"]
        cid_a = project_with_gen["cat_a_id"]

        # Vor dem Loeschen: KategorieA ist in den Testfaellen
        r = client.get(f"/api/generations/{gen_id}/testcases")
        assert r.status_code == 200
        tc0 = r.json()["testcases"][0]
        assert "KategorieA" in tc0["assignments"]

        # Kategorie A loeschen
        r = client.delete(f"/api/categories/{cid_a}")
        assert r.status_code == 200

        # Nach dem Loeschen: Testfaelle der alten Generierung zeigen noch "KategorieA"
        r = client.get(f"/api/generations/{gen_id}/testcases")
        assert r.status_code == 200
        tc0_after = r.json()["testcases"][0]
        assert "KategorieA" in tc0_after["assignments"], \
            f"KategorieA sollte in assignments sein, ist aber: {list(tc0_after['assignments'].keys())}"
        # Der Wert sollte unveraendert sein
        assert tc0_after["assignments"]["KategorieA"] == tc0["assignments"]["KategorieA"]

    def test_renaming_category_keeps_old_name_in_old_generation(self, client, project_with_gen):
        """Umbenennen einer Kategorie aendert NICHT den Namen in alten Generierungen."""
        pid = project_with_gen["project_id"]
        gen_id = project_with_gen["gen_id"]
        cid_a = project_with_gen["cat_a_id"]

        # Vor dem Umbenennen
        r = client.get(f"/api/generations/{gen_id}/testcases")
        assert r.status_code == 200
        tc0_before = r.json()["testcases"][0]
        assert "KategorieA" in tc0_before["assignments"]

        # Kategorie A umbenennen
        r = client.patch(f"/api/categories/{cid_a}/rename", json={"name": "NeuerNameA"})
        assert r.status_code == 200

        # Alte Generierung sollte den alten Namen behalten
        r = client.get(f"/api/generations/{gen_id}/testcases")
        assert r.status_code == 200
        tc0_after = r.json()["testcases"][0]
        assert "KategorieA" in tc0_after["assignments"], \
            f"Alter Name 'KategorieA' sollte erhalten bleiben, ist aber: {list(tc0_after['assignments'].keys())}"

    def test_new_generation_uses_new_name(self, client, project_with_gen):
        """Neue Generierung nach Umbenennung verwendet den neuen Kategorienamen."""
        pid = project_with_gen["project_id"]
        cid_a = project_with_gen["cat_a_id"]

        # Kategorie A umbenennen
        r = client.patch(f"/api/categories/{cid_a}/rename", json={"name": "NeuerNameA"})
        assert r.status_code == 200

        # Neue Generierung
        r = client.post(f"/api/projects/{pid}/generate", json={"strategy": "all"})
        assert r.status_code == 200
        new_gen_id = r.json()["generation_id"]

        # Neue Generierung sollte den neuen Namen verwenden
        r = client.get(f"/api/generations/{new_gen_id}/testcases")
        assert r.status_code == 200
        tc0 = r.json()["testcases"][0]
        assert "NeuerNameA" in tc0["assignments"], \
            f"Neuer Name 'NeuerNameA' sollte in neuer Generierung sein, ist aber: {list(tc0['assignments'].keys())}"


class TestExportAfterCategoryDelete:
    """B-18: Export-Funktionen behalten geloeschte Kategorienamen."""

    def test_export_csv_of_old_generation_after_category_delete(self, client, project_with_gen):
        """CSV-Export einer alten Generierung nach Kategorie-Loeschung."""
        gen_id = project_with_gen["gen_id"]
        cid_a = project_with_gen["cat_a_id"]

        # Kategorie A loeschen
        r = client.delete(f"/api/categories/{cid_a}")
        assert r.status_code == 200

        # CSV-Export
        r = client.get(f"/api/generations/{gen_id}/export/csv")
        assert r.status_code == 200
        csv_text = r.text

        # "KategorieA" sollte als Spaltenueberschrift im CSV erscheinen
        assert "KategorieA" in csv_text, \
            f"KategorieA sollte im CSV-Export sein. CSV: {csv_text[:500]}"

    def test_risk_summary_old_generation_after_category_delete(self, client, project_with_gen):
        """Risikoabdeckung einer alten Generierung nach Kategorie-Loeschung."""
        gen_id = project_with_gen["gen_id"]
        cid_a = project_with_gen["cat_a_id"]

        # Kategorie A loeschen
        r = client.delete(f"/api/categories/{cid_a}")
        assert r.status_code == 200

        # Testfaelle mit risk_summary lesen
        r = client.get(f"/api/generations/{gen_id}/testcases")
        assert r.status_code == 200
        data = r.json()
        assert "risk_summary" in data
        assert "testcases" in data
        assert len(data["testcases"]) > 0

        # Jeder Testfall sollte "KategorieA" in assignments haben
        for tc in data["testcases"]:
            assert "KategorieA" in tc["assignments"], \
                f"KategorieA sollte in allen Testfaellen sein, ist aber: {list(tc['assignments'].keys())}"