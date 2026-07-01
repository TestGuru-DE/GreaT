# Current Test State – G.R.E.A.T.
Version: 1.0
Phase: 0 – Bestandsaufnahme
Erstellt: 2026-06-10
Erstellt von: Senior QA Director Agent

---

## 1. Übersicht Testlandschaft

### 1.1 Testinfrastruktur

| Tool | Version | Einsatz |
|---|---|---|
| pytest | >=7.4 | Testrunner |
| httpx | aktuell | HTTP-Client für FastAPI-Tests |
| TestClient (Starlette) | via FastAPI | Integration-Tests |
| conftest.py | vorhanden | sys.path-Setup für `src/` |

### 1.2 Test-Dateien

| Datei | Kategorie | Getesteter Bereich | Qualität |
|---|---|---|---|
| `test_backend_mvp.py` | Integrationstest | FastAPI CRUD (Projekte, Kategorien, Werte, Generierung) | ⭐⭐⭐ |
| `test_csv_handler.py` | Unit Test | CSV Export/Import Grundfunktionen | ⭐⭐⭐⭐ |
| `test_csv_handler_names.py` | Unit Test | CSV Export mit optionalen Spaltennamen | ⭐⭐⭐⭐ |
| `test_csv_handler_roundtrip.py` | Unit Test | CSV Export → Import Roundtrip | ⭐⭐⭐⭐ |
| `test_export_status.py` | Unit Test | CSV Export mit Status-Spalte | ⭐⭐⭐⭐ |
| `test_pairwise.py` | Unit Test | Orthogonal/Pairwise-Generator | ⭐⭐⭐⭐ |
| `test_ui_crud.py` | Integrationstest | Browser-UI CRUD via HTMX | ⭐⭐⭐ |
| `test_ui_delete_rename.py` | Integrationstest | Umbenennen & Löschen UI | ⭐⭐⭐ |
| `test_ui_generate_run.py` | Integrationstest | UI Generierungsworkflow | ⭐⭐⭐ |
| `test_values_reorder.py` | Integrationstest | Werte-Sortierung via Drag&Drop | ⭐⭐⭐ |
| `test_dummy.py` | Dummy | Platzhalter | ⭐ (archivieren) |

---

## 2. Testabdeckung nach Domänenbereichen

### 2.1 Abgedeckte Bereiche ✅

| Bereich | Testtyp | Status |
|---|---|---|
| CSV Export (Basis) | Unit | ✅ Gut abgedeckt |
| CSV Export mit Status | Unit | ✅ Gut abgedeckt |
| CSV Export mit Spaltennamen | Unit | ✅ Gut abgedeckt |
| CSV Import Roundtrip | Unit | ✅ Gut abgedeckt |
| Pairwise/Orthogonal-Generierung | Unit | ✅ Gut abgedeckt |
| Projekt CRUD (API) | Integration | ✅ Abgedeckt |
| Kategorien CRUD (API) | Integration | ✅ Abgedeckt |
| Werte CRUD (API) | Integration | ✅ Abgedeckt |
| Testfall-Generierung (API) | Integration | ✅ Abgedeckt |
| UI Rename/Delete (HTMX) | Integration | ✅ Abgedeckt |
| Werte-Sortierung | Integration | ✅ Abgedeckt |

### 2.2 Nicht abgedeckte Bereiche ❌

| Bereich | Fehlender Testtyp | Priorität |
|---|---|---|
| Geschäftsregeln (forbidden, combine) | Unit + Integration | HOCH |
| Linear (Lineare Expansion) Strategie | Unit | HOCH |
| MCDC Strategie | Unit | HOCH |
| Risikogewichtete Strategie | Unit | HOCH |
| T-Wise / 3-Wise Strategie | Unit | MITTEL |
| All-Combinations vollständige Abdeckung | Unit | MITTEL |
| JSON Export/Import | Unit | MITTEL |
| Excel Export/Import | Unit | MITTEL |
| XML Export/Import | Unit | MITTEL |
| Fehlerbehandlung (4xx/5xx) | Integration | HOCH |
| Grenzwertanalyse | Unit | HOCH |
| System-Datenklassen | Unit | NIEDRIG |
| End-to-End Systemtest | System | MITTEL |
| Performance-Tests | NFR | NIEDRIG |
| Sicherheits-Tests (OWASP) | Security | MITTEL |

---

## 3. Traceability Requirements → Tests

| REQ-ID | Beschreibung | Testfall vorhanden | Test-Datei |
|---|---|---|---|
| REQ-0800 | Pairwise | ✅ | test_pairwise.py |
| REQ-0801 | Orthogonal Array | ✅ (als Pairwise) | test_pairwise.py |
| REQ-0802 | Each Choice | ⚠️ Implizit | test_backend_mvp.py |
| REQ-0806 | All Combinations | ⚠️ Implizit | test_backend_mvp.py |
| REQ-1000 | CSV Export | ✅ | test_csv_handler.py |
| REQ-1100 | CSV Import | ✅ | test_csv_handler.py |
| REQ-0200 | Projekt anlegen | ✅ | test_backend_mvp.py |
| REQ-0300 | Kategorie anlegen | ✅ | test_backend_mvp.py |
| REQ-0400 | Äquivalenzklasse | ✅ | test_backend_mvp.py |
| REQ-0700 | Regeltyp Verboten | ❌ | – |
| REQ-0701 | Regeltyp Abhängig | ⚠️ Teilweise | test_backend_mvp.py |
| REQ-0702 | Regeltyp Kombinierbar | ❌ | – |
| REQ-0803 | Lineare Expansion | ❌ | – |
| REQ-0804 | MCDC | ❌ | – |
| REQ-0805 | Risikogewichtet | ❌ | – |

---

## 4. Qualitätsbewertung

### 4.1 Stärken
- ✅ **CSV-Handler vollständig getestet** – Roundtrip, Sonderfälle, Status-Spalte
- ✅ **Pairwise-Algorithmus mit mathematischer Überprüfung** (alle Paare abgedeckt)
- ✅ **Integration-Tests mit echten HTTP-Requests** (nicht gemockt)
- ✅ **conftest.py** löst Importprobleme sauber

### 4.2 Schwächen
- ❌ **Coverage-Messung fehlt** – kein pytest-cov konfiguriert
- ❌ **TDD nicht nachweisbar** – Test-Reihenfolge (Test-First) nicht dokumentiert
- ❌ **Keine Systemtests** – kein End-to-End Szenario
- ❌ **Keine Regressionssuite** – kein expliziter Regressionstest-Run
- ❌ **test_dummy.py** ohne Inhalt (Archivieren)
- ❌ **Mutation Testing** fehlt (Ziel: >= 90%)

---

## 5. Empfehlungen

| Priorität | Maßnahme |
|---|---|
| SOFORT | pytest-cov einrichten, Coverage-Report automatisch |
| SOFORT | Geschäftsregeln (forbidden/combine) testen |
| HOCH | TDD für alle neuen Features verpflichtend |
| HOCH | test_dummy.py archivieren |
| MITTEL | Systemtest-Suite einrichten (E2E) |
| MITTEL | Mutation Testing (mutmut oder cosmic-ray) |
| NIEDRIG | Performance Benchmarks für Kombinatorik |

---

## 6. Definition of Done (Testing)

Für jeden neuen Feature-Zweig gilt:

```
[ ] Unit Tests vorhanden (TDD: Test zuerst)
[ ] Integration Tests vorhanden
[ ] Coverage >= 100% für neuen Code
[ ] Keine bestehenden Tests gebrochen (Regression)
[ ] Traceability: Test-ID → REQ-ID dokumentiert
[ ] pytest läuft ohne Warnungen
```
