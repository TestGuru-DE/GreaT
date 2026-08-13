# Archive Log – G.R.E.A.T.
Version: 1.0
Erstellt: 2026-06-10

Dieses Log dokumentiert alle Archivierungsaktionen im Projekt.
**Dateien werden niemals gelöscht – nur archiviert.**

---

## Format

| Datum | Quelle | Ziel | Begründung | Agent |
|---|---|---|---|---|

---

## Einträge

*(noch keine Archivierungen durchgeführt – Aktionen aus ADR-004 stehen aus)*

### Geplante Archivierungen (ADR-004, Status: Accepted)

| Quelle | Ziel | Begründung | Verantwortlich |
|---|---|---|---|
| `src/backend/` | `archive/2026-06-10/backend-getecade/` | Paralleler GeTeCaDe-Prototyp, nicht integriert | Legacy Code Auditor |
| `tests/test_dummy.py` | `archive/2026-06-10/test_dummy.py` | Leerer Platzhalter-Test | Legacy Code Auditor |

## 2026-06-26 – System-Datenklassen eingeführt (REQ-2005)

**Grund**: Legacy-Funktionalität vollständig durch System-Datenklassen (REQ-2005) ersetzt.
Die Werte sind nun als vorinstallierte, löschgeschützte Datenklassen in der DB verfügbar.

**Archivierte Dateien**:
- src/combinatorics/ (Legacy-Katalog)
- src/app/routers/api_*_legacy.py (alte API-Endpunkte)
- tests/test_*_legacy.py (Legacy-Tests)
- frontend/src/components/*Dialog_old.tsx (alte React-Komponente)

**Ersetzt durch**:
- src/app/system_dataclasses.py – System-Datenklassen-Katalog mit deutschen Namen
- System-Datenklassen werden beim App-Start automatisch in die Datenbank geseeded
- Jede System-Datenklasse hat is_system=True und kann nicht gelöscht werden


## 2026-06-29 – REQ-3011: HTMX-Ansicht archiviert

**Grund:** Phase 3 Sprint 3 – Klassische HTMX-Ansicht wird durch React-Frontend abgelöst (REQ-3011).

**Archiviert nach:** rchive/2026-06-29/htmx/

| Datei | Original-Pfad |
|---|---|
| ui_projects.py | src/app/routers/ui_projects.py |
| ui_generate.py | src/app/routers/ui_generate.py |
| ui_rules.py | src/app/routers/ui_rules.py |
| ui_dataclasses.py | src/app/routers/ui_dataclasses.py |
| ui_helpers.py | src/app/ui_helpers.py |
| 	emplates/ | src/app/templates/ |
| 	est_ui_crud.py | 	ests/test_ui_crud.py |
| 	est_ui_delete_rename.py | 	ests/test_ui_delete_rename.py |
| 	est_ui_generate_run.py | 	ests/test_ui_generate_run.py |
| e2e/ | 	ests/e2e/ |

**Änderungen in main.py:** ui_*-Router-Includes entfernt, /ui-Redirect zeigt auf /app.

## 2026-06-30 - Agent-Customization Cleanup
- Archiviert: `.github/agents/great-ux-lead.instructions.md` -> `archive/2026-06-30/agent-customizations/great-ux-lead.instructions.md`
- Grund: Lag im Agenten-Ordner und wurde dadurch als Agent erkannt; aktive Quelle ist jetzt .github/agents/great-ux-lead.agent.md plus .github/instructions/great-ux-lead.instructions.md.

## 2026-06-30 - Agent-Customization Cleanup
- Archiviert: `.github/instructions/great-senior-prompt-engeneer.instructions.md` -> `archive/2026-06-30/agent-customizations/great-senior-prompt-engeneer.instructions.md`
- Grund: Tippfehler im Dateinamen; aktive Quelle ist jetzt .github/instructions/great-senior-prompt-engineer.instructions.md.

## 2026-06-30 - Agent-Customization Cleanup
- Archiviert: `.github/prompts/great-phase0-freigabe.prompt.md` -> `archive/2026-06-30/agent-customizations/great-phase0-freigabe.prompt.md`
- Grund: Phase-0-Freigabe ist historisch; aktive generische Freigabe ist jetzt .github/prompts/great-phase-gate.prompt.md.

## 2026-07-01 – Archive-Verzeichnis aus Public Repository entfernt

**Grund**: Public Repository – Archive-Inhalte lokal verschoben (vertrauliche Informationen und urheberrechtlich geschützte Referenzen).

**Betroffene Verzeichnisse:**
- `archive/2026-06-10/` (GeTeCaDe-Prototyp, test_dummy.py)
- `archive/2026-06-26/` (Legacy-Dateien)
- `archive/2026-06-30/` (Agent-Customizations)

**Lokal gesichert unter**: `C:\Users\georgh\GreaT_archive_local\archive-20260701-*`

**Status**: Archive lokal gesichert, aus Repository entfernt (Public-Release-Hygiene).

## 2026-07-02 – REQ-4006: Alte database.py (db.py) archiviert

**Grund**: REQ-4006 Multi-User Support – Neue `src/app/database.py` mit WAL-Mode und Connection-Pool ersetzt alte `src/app/db.py`.

**Archiviert nach:** `archive/2026-07-02/db_old.py`

| Datei | Grund |
|---|---|
| src/app/db.py | Alte Datenbankverbindung ohne WAL-Mode und Pooling. Ersetzt durch `src/app/database.py` mit SQLite WAL-Mode + PostgreSQL Connection-Pool. |

**Neue Features in database.py:**
- SQLite: WAL-Mode für concurrent reads (verhindert "database is locked")
- Connection-Pool: pool_size=5 (SQLite), pool_size=10 (PostgreSQL)
- PostgreSQL-Support via DATABASE_URL (optional)

## 2026-08-13 – Sprint 8: Single Entry Point (Port 8000)

**Grund**: Single Entry Point Architektur – React-Frontend wird nur noch via Port 8000 ausgeliefert (keine separaten Vite Dev Server Nutzern bekannt).

**Archiviert nach:** `archive/2026-08-13/`

| Datei | Original-Pfad | Grund |
|---|---|---|
| ui_projects.py | src/app/routers/ui_projects.py | HTMX-Legacy, nicht mehr in main.py inkludiert |
| ui_generate.py | src/app/routers/ui_generate.py | HTMX-Legacy, nicht mehr in main.py inkludiert |
| templates/ | src/app/templates/ | HTMX-Templates für ui_*.py, nicht mehr verwendet |

**Änderungen in main.py:**
- Keine Änderung: ui_*-Router waren bereits archiviert (2026-06-29), nicht inkludiert

**Änderungen in api_generate.py:**
- tanos_generation_*.csv → great_generation_*.csv
- tanos_generation_*.json → great_generation_*.json
- tanos_generation_*.xlsx → great_generation_*.xlsx

**Neue Startskripte:**
- `Start.bat` (vereinfacht): Nur Backend auf Port 8000 für Anwender
- `Start-Dev.bat` (neu): Backend (8000) + Vite Dev Server (5173) für Entwickler
- `Start.sh` (aktualisiert): Wie Start.bat für Linux/Raspberry Pi


