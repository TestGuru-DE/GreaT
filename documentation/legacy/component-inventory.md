# Component Inventory – G.R.E.A.T.
Version: 1.0
Phase: 0 – Bestandsaufnahme
Erstellt: 2026-06-10
Erstellt von: Legacy Code Auditor Agent

---

## 1. Überblick der Codebasis

Die bestehende Codebasis ist eine FastAPI-basierte Webanwendung (Python) mit SQLite-Datenbank,
Jinja2-Templates und HTMX-Frontend. Sie wurde als Prototyp entwickelt und trägt intern den
Projektnamen „TaNoS" (TestcaseNoSense → abgelöst durch G.R.E.A.T.).

---

## 2. Webkomponenten (src/)

### 2.1 src/app/ – FastAPI Hauptanwendung

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/app/main.py` | FastAPI App, alle API-Endpunkte, UI-Routen (HTMX/Jinja2), Migrationslogik | **Refactor** | Zu groß (monolithisch, ~56KB), Migrationslogik gehört in eigenes Modul, doppelter `on_startup` Handler |
| `src/app/models.py` | SQLAlchemy ORM-Modelle (Project, Category, Value, Generation, TestCase, Rule) | **Reuse** | Gut strukturiert, vollständige Domänenmodelle, leicht erweiterbar |
| `src/app/db.py` | Datenbankverbindung, Session-Management | **Reuse** | Standardmuster, funktioniert |
| `src/app/schemas.py` | Pydantic Schemas für API | **Reuse** | Vorhanden, muss ggf. erweitert werden |
| `src/app/templates/` | Jinja2 HTML-Templates (HTMX-UI) | **Replace** | Langfristig durch React/TypeScript ersetzen (laut Zielarchitektur), kurzfristig weiter nutzbar |

### 2.2 src/combinatorics/ – Kombinatorik-Engine

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/combinatorics/__init__.py` | Modul-Init, exportiert Strategien | **Reuse** | Sauber |
| `src/combinatorics/all_combinations.py` | Alle-mit-Allem Strategie | **Reuse** | Kern-Algorithmus, getestet |
| `src/combinatorics/each_choice.py` | Each-Choice Strategie | **Reuse** | Kern-Algorithmus |
| `src/combinatorics/orthogonal.py` | Pairwise/Orthogonal-Strategie (2-Wege) | **Refactor** | Implementiert als Pairwise, muss auf vollständige Orthogonalarray-Unterstützung erweitert werden |

**Fehlende Kombinatorik-Strategien (zu implementieren):**
- Linear (Lineare Expansion)
- MCDC
- Risikogewichtet
- T-Wise / 3-Wise
- Business Rule Based
- Freie Benutzerkombination

### 2.3 src/io_handlers/ – Import/Export

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/io_handlers/csv_handler.py` | CSV Export/Import (Semikolon-Trennzeichen) | **Reuse** | Funktioniert, getestet inkl. Roundtrip |

**Fehlende IO-Handler (zu implementieren):**
- JSON Export/Import
- Excel Export/Import (openpyxl vorhanden)
- XML Export/Import

### 2.4 src/rules/ – Geschäftsregeln

| Ordner | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/rules/` | Regelverarbeitung für Kombinatorik | **Refactor** | Regeltypen (Verboten, Abhängig, Kombinierbar) teilweise implementiert (nur `dependency` in DB), muss vervollständigt werden |

### 2.5 src/backend/ – Zweites Backend (GeTeCaDe)

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/backend/main.py` | Separates FastAPI-Backend (GeTeCaDe DB-Backend) | **Archive** | Paralleler Prototyp, wird von der Haupt-App nicht verwendet, zu archivieren |
| `src/backend/db/` | Eigene DB-Schicht | **Archive** | Redundant zu src/app/ |
| `src/backend/services/` | Eigene Services | **Archive** | Redundant |
| `src/backend/getecade.db` | Eigene SQLite-Datenbank | **Archive** | Separate DB-Datei, nicht integriert |

### 2.6 Sonstige src-Dateien

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `src/main.py` | Entry-Point (top-level) | **Refactor** | Muss mit app/main.py konsolidiert werden |
| `src/api_client.py` | HTTP-Client Hilfsklasse | **Reuse** | Nützlich für Integration/Tests |
| `src/project_handler.py` | Projekt-Hilfsfunktionen | **Refactor** | Logik gehört in Service-Layer |
| `src/tree_view.py` | Baumansicht-Logik | **Refactor** | Gehört in UI-Schicht |

---

## 3. Desktopkomponenten

Keine eigenständige Desktopanwendung vorhanden. Die Anwendung läuft im Browser (localhost).
Ein `Start.bat` startet den uvicorn-Server.

| Datei | Beschreibung | Klassifizierung |
|---|---|---|
| `Start.bat` | Windows-Startskript für uvicorn | **Reuse** | Einfacher Launcher, für Endbenutzer ausreichend |

---

## 4. Buildsystem

| Datei | Beschreibung | Klassifizierung | Begründung |
|---|---|---|---|
| `requirements.txt` | Python-Abhängigkeiten | **Refactor** | Keine Versionspinning bei fastapi/uvicorn/sqlalchemy, Risiko für Inkompatibilitäten |

**Fehlende Build-Infrastruktur:**
- CI/CD Pipeline (GitHub Actions)
- Docker/Container-Setup
- Installationspaket (GREAT.exe oder Installer)
- pyproject.toml / setup.py

---

## 5. Tests

| Datei | Beschreibung | Klassifizierung |
|---|---|---|
| `tests/conftest.py` | pytest Fixtures | **Reuse** |
| `tests/test_backend_mvp.py` | Backend MVP Tests | **Reuse** |
| `tests/test_csv_handler.py` | CSV Export/Import Unit Tests | **Reuse** |
| `tests/test_csv_handler_names.py` | CSV mit Spaltennamen Tests | **Reuse** |
| `tests/test_csv_handler_roundtrip.py` | CSV Roundtrip Tests | **Reuse** |
| `tests/test_export_status.py` | Export mit Status Tests | **Reuse** |
| `tests/test_pairwise.py` | Pairwise/Orthogonal Tests | **Reuse** |
| `tests/test_ui_crud.py` | UI CRUD Integration Tests | **Reuse** |
| `tests/test_ui_delete_rename.py` | UI Delete/Rename Tests | **Reuse** |
| `tests/test_ui_generate_run.py` | UI Generierungstest | **Reuse** |
| `tests/test_values_reorder.py` | Werte Sortierung Tests | **Reuse** |
| `tests/test_dummy.py` | Dummy-Test | **Archive** |

---

## 6. Dokumentation

| Datei | Beschreibung | Klassifizierung |
|---|---|---|
| `README.md` | Startanleitung, Kurzübersicht | **Refactor** | Unvollständig, kein Installationsguide |
| `CHANGELOG.md` | Änderungshistorie | **Refactor** | Nicht vollständig (fehlt Markdown-Wrapper) |
| `Agenten und basisinfos/SYSTEM_v1.0.md` | Governance-Dokument | **Reuse** | Verbindlich, gut strukturiert |
| `Agenten und basisinfos/requirements_v1.0.md` | Requirements v1.0 | **Reuse** | Basis, wird zu v1.1 konsolidiert |
| `Agenten und basisinfos/requirements.md` | Erweiterter Backlog | **Reuse** | Ergänzt v1.0 |
| `Agenten und basisinfos/projektbeschreibung.md` | Fachliche Vision | **Reuse** | Wichtige Fachquelle |
| `Agenten und basisinfos/PROJECT_ASSESSMENT_CHECKLIST_v1.0.md` | Phase-0 Checkliste | **Reuse** | Verbindlich |
| `Agenten und basisinfos/AGENT_BOOTSTRAP_PROMPT_v1.0.md` | Agent Start-Prompt | **Reuse** | Verbindlich |

---

## 7. Zusammenfassung

| Klassifizierung | Anzahl | Anteil |
|---|---|---|
| Reuse | 18 | ~50% |
| Refactor | 9 | ~25% |
| Replace | 1 | ~3% |
| Archive | 5 | ~14% |
| Fehlend (neu) | ~15 | ~8% |

**Wiederverwendungspotenzial: HOCH**
Der Kombinatorik-Kern, die Datenmodelle und die Test-Suite sind solid.
Der größte Handlungsbedarf liegt in der Architektur (monolithischer main.py) und den fehlenden Kombinatorik-Strategien.
