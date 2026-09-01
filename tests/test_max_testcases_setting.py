"""REQ-4018: Maximale Anzahl Testfaelle als Setting (Default 1000).

TDD: Tests werden VOR der Implementierung geschrieben (RED -> GREEN).

Zwei Ebenen werden abgedeckt:
1. Konfigurationsebene (`app.config.GREAT_MAX_TESTCASES`), analog zum
   bestehenden Muster fuer GREAT_PORT (REQ-4007, siehe tests/test_config.py).
2. Verhaltensebene (`POST /projects/{pid}/generate`): Die Generierung muss
   die Obergrenze respektieren, wenn kein expliziter `limit`-Wert
   mitgeschickt wird. Ein expliziter, kleinerer `limit` bleibt unangetastet.
"""
import os

from app.config import get_max_testcases, GREAT_MAX_TESTCASES_DEFAULT


def test_default_max_testcases_is_1000(monkeypatch):
    """Default-Obergrenze ist 1000, wenn keine Env-Variable gesetzt ist."""
    monkeypatch.delenv("GREAT_MAX_TESTCASES", raising=False)
    assert GREAT_MAX_TESTCASES_DEFAULT == 1000
    assert get_max_testcases() == 1000


def test_custom_max_testcases_via_env(monkeypatch):
    """Die Obergrenze kann via Umgebungsvariable ueberschrieben werden (sofort wirksam,
    kein Server-Neustart noetig, da bei jedem Request frisch gelesen wird)."""
    monkeypatch.setenv("GREAT_MAX_TESTCASES", "50")
    value = get_max_testcases()
    assert value == 50
    assert isinstance(value, int)


def test_invalid_max_testcases_env_falls_back_to_default(monkeypatch):
    """Ungueltige Werte (nicht-numerisch oder <= 0) fallen robust auf den Default
    zurueck, statt den Server mit einer stillen Fehlkonfiguration zu betreiben."""
    monkeypatch.setenv("GREAT_MAX_TESTCASES", "not-a-number")
    assert get_max_testcases() == GREAT_MAX_TESTCASES_DEFAULT

    monkeypatch.setenv("GREAT_MAX_TESTCASES", "0")
    assert get_max_testcases() == GREAT_MAX_TESTCASES_DEFAULT

    monkeypatch.setenv("GREAT_MAX_TESTCASES", "-5")
    assert get_max_testcases() == GREAT_MAX_TESTCASES_DEFAULT


def _create_category_with_values(client, project_id: int, name: str, values: list[str]) -> int:
    category = client.post(
        f"/api/projects/{project_id}/categories",
        json={"name": name, "order_index": 0},
    )
    assert category.status_code == 200, category.text
    category_id = category.json()["id"]
    for value in values:
        created = client.post(
            f"/api/categories/{category_id}/values",
            json={"value": value, "risk_weight": 1},
        )
        assert created.status_code == 200, created.text
    return category_id


def _build_project_with_many_combinations(client) -> int:
    """Legt ein Projekt an, dessen Vollkombinatorik (Strategie 'all') die
    Default-Obergrenze von 1000 Testfaellen deutlich ueberschreitet
    (6^4 = 1296 Kombinationen)."""
    project = client.post("/api/projects", json={"name": "REQ4018-MaxTestcases"})
    assert project.status_code == 200, project.text
    project_id = project.json()["id"]

    for cat_name in ["A", "B", "C", "D"]:
        values = [f"{cat_name}{i}" for i in range(1, 7)]  # 6 Werte je Kategorie
        _create_category_with_values(client, project_id, cat_name, values)

    return project_id


# REQ-4018
def test_generate_respects_default_max_testcases_without_explicit_limit(client, monkeypatch):
    """Ohne expliziten 'limit' im Request darf die Generierung nicht mehr
    Testfaelle erzeugen als das Default-Setting (1000) erlaubt."""
    monkeypatch.setenv("GREAT_MAX_TESTCASES", "1000")

    project_id = _build_project_with_many_combinations(client)

    response = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["count"] == 1000

    testcases = client.get(f"/api/generations/{body['generation_id']}/testcases")
    assert testcases.status_code == 200, testcases.text
    assert len(testcases.json()["testcases"]) == 1000


# REQ-4018
def test_generate_respects_custom_max_testcases_setting_via_env(client, monkeypatch):
    """Ein per Env-Variable abgesenktes Setting muss respektiert werden
    (Simuliert eine geaenderte Einstellung ueber das konfigurierbare Setting)."""
    monkeypatch.setenv("GREAT_MAX_TESTCASES", "42")

    project_id = _build_project_with_many_combinations(client)

    response = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 42


# REQ-4018
def test_generate_explicit_limit_still_honored_within_default(client, monkeypatch):
    """Ein expliziter, kleinerer 'limit'-Wert bleibt unveraendert respektiert
    (bestehendes Verhalten darf nicht brechen)."""
    monkeypatch.setenv("GREAT_MAX_TESTCASES", "1000")

    project_id = _build_project_with_many_combinations(client)

    response = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "all", "limit": 5},
    )
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 5


# REQ-4018
def test_generate_limit_still_rejects_non_positive_values(client):
    """Regressionsschutz: Die bestehende Validierung (limit muss positiv sein)
    bleibt unveraendert erhalten."""
    project = client.post("/api/projects", json={"name": "REQ4018-InvalidLimit"})
    assert project.status_code == 200, project.text
    project_id = project.json()["id"]
    _create_category_with_values(client, project_id, "Browser", ["Chrome", "Firefox"])

    response = client.post(
        f"/api/projects/{project_id}/generate",
        json={"strategy": "each", "limit": 0},
    )
    assert response.status_code == 400, response.text
