# TESTING_GUIDE.md – G.R.E.A.T.

## Übersicht

G.R.E.A.T. verwendet **pytest** als Test-Framework mit TDD-Pflicht:
Jede Implementierung wird durch Tests abgesichert, die **zuerst rot** laufen müssen.

---

## Tests ausführen

### Alle Tests (Windows)

```cmd
set PYTHONPATH=src
python -m pytest tests/ -v
```

### Alle Tests (Linux / Mac)

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

### Nur Unit-Tests (ohne E2E)

```bash
PYTHONPATH=src python -m pytest tests/ --ignore=tests/e2e -v
```

### Nur E2E-Tests

```bash
# Chromium muss installiert sein (einmalig):
playwright install chromium

PYTHONPATH=src python -m pytest tests/e2e/ -v
```

---

## Coverage messen

### Statement + Branch Coverage

```bash
PYTHONPATH=src python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
```

### HTML-Report (im Browser öffnen)

```bash
PYTHONPATH=src python -m pytest --cov=src --cov-report=html --cov-branch tests/
# Report öffnen:
open htmlcov/index.html   # Mac/Linux
start htmlcov/index.html  # Windows
```

---

## TDD-Workflow

```
1. REQ-ID aus requirements_v1.1.md wählen
2. Test schreiben → tests/test_<feature>.py
3. Test ausführen → MUSS ROT sein (ModuleNotFoundError oder AssertionError)
4. Minimale Implementierung schreiben
5. Test ausführen → MUSS GRÜN sein
6. Refactoring (Clean Architecture, keine Logik in Routern)
7. Coverage prüfen: 100% für neuen Code
8. Commit: feat(sprintN): <beschreibung> – REQ-XXXX
```

---

## Teststruktur

```
tests/
  conftest.py              ← sys.path Setup für src/
  test_each_choice.py      ← REQ-0801 Each Choice Algorithmus
  test_all_combinations.py ← REQ-0802 All Combinations Algorithmus
  test_linear_expansion.py ← REQ-0803 Lineare Expansion Algorithmus
  test_risk_based.py       ← REQ-0805 Risikogewichtete Generierung
  test_boundary_value.py   ← REQ-0306 Grenzwertanalyse
  test_rule_engine.py      ← REQ-0700/0701/0702 RuleEngine
  test_backend_mvp.py      ← End-to-End Pairwise Generation
  test_json_export.py      ← REQ-1001 JSON Export
  test_excel_export.py     ← REQ-1002 Excel Export
  test_export_status.py    ← REQ-1000 CSV Export mit Status
  test_ui_crud.py          ← UI-Smoke Tests (HTMX-Endpunkte)
  test_ui_delete_rename.py ← UI Umbenennen/Löschen
  test_ui_generate_run.py  ← UI Generierungsseite
  e2e/
    conftest.py            ← Playwright Server-Fixture (Port 8011)
    test_workflows.py      ← Browser-basierte User-Flow-Tests
```

---

## Release Gate (QA-Director-Kriterien)

Ein Release ist **BLOCKIERT** wenn:

- [ ] Statement Coverage < 100% für neuen Code
- [ ] Branch Coverage < 100% für neuen Code
- [ ] Irgendein Test schlägt fehl
- [ ] REQ-ID fehlt als Kommentar in der Testdatei

---

## Bekannte Einschränkungen

| Test | Einschränkung |
|---|---|
| E2E HTMX-Tests | HTMX lädt von CDN – DOM-Update nicht in headless-Tests verlässlich; Verifikation über REST-API |
| `test_backend_mvp.py` | Benötigt leere oder neue DB; bei wiederholtem Lauf Projektname eindeutig (UUID) |
| E2E-Tests | Benötigen Port 8011 frei |
