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

## 2026-09-01 – Sprint 10, Aufgabe 7 (p3-dc-ux): Legacy-DataClassDialog archiviert

**Grund**: Tech-Debt-Cleanup aus der ToDo-Sichtung (Sprint 10, Aufgabe 1 → Aufgabe 7). Der alte
`DataClassDialog` in `CategoryTree.tsx` war toter Code: der zugehörige State `dataClassCat` wurde
nirgends mehr per `setDataClassCat(...)` mit einem Wert befüllt (nur `onClose` setzte ihn zurück auf
`null`), der Dialog war für Nutzer:innen unerreichbar. Der Kontextmenü-Eintrag „Datenklasse
anwenden...“ öffnet bereits seit REQ-4018 ausschließlich den DataNode-Baum-Dialog
(`setDataNodeMenuOpen(...)`).

**Archiviert nach:** `archive/2026-09-01/frontend-legacy/DataClassDialog.tsx`

| Datei | Original-Pfad | Grund |
|---|---|---|
| DataClassDialog.tsx | frontend/src/components/DataClassDialog.tsx | Unerreichbarer Legacy-Dialog (REQ-2003), vollständig ersetzt durch DataNode-Baum-Dialog (REQ-4018) |

**Änderungen in `CategoryTree.tsx`:**
- Import `import DataClassDialog from "./DataClassDialog";` entfernt
- Toter State `dataClassCat` / `setDataClassCat` entfernt
- Render-Block „Datenklassen-Dialog (Legacy)“ entfernt

**Traceability:** REQ-3010 (Datenklassen-Ansicht), REQ-4018 (DataNode-Kontextmenü) – Bezug siehe
`documentation/project-assessment.md` Sprint-10-Abschnitt (Aufgabe 7).

**Regressionsschutz:** `frontend/src/components/__tests__/CategoryTree.test.tsx` – neue Testgruppe
„CategoryTree - Legacy-DataClassDialog entfernt" mit (a) Guard-Test gegen Wiedereinführung des
Legacy-Imports und (b) Verhaltenstest, dass der Kontextmenü-Pfad weiterhin den DataNode-Dialog öffnet.

## 2026-10-05 – OpenCode/OpenChamber Agent-Konfiguration korrigiert

**Grund**: Die alten `.opencode/agents/*.agent.md`-Dateien nutzten ein veraltetes Format
(VS Code / GitHub Copilot Frontmatter mit ungueltigen Keys wie `name:`, `agents:`,
`argument-hint:`, `user-invocable:` und einer Liste-basierten `tools:`). OpenCode/OpenChamber
erwartet ein anderes Frontmatter-Format mit `description:`, `mode:`, `permission:` und
einem Markdown-Body als System-Prompt.

**Massnahme**: 14 neue korrekte Agent-Dateien in `.opencode/agents/*.md` erstellt.
Alte Dateien nach `archive/2026-10-05/opencode-agents-legacy/` verschoben.
Zusaetzlich `opencode.json` angelegt mit `default_agent: "great-orchestrator"`.

| Datei | Original-Pfad | Grund |
|---|---|---|
| great-orchestrator.agent.md | .opencode/agents/great-orchestrator.agent.md | Veraltetes Frontmatter (doppelte YAML-Delimiter, ungueltige Keys) |
| great-senior-developer.agent.md | .opencode/agents/great-senior-developer.agent.md | Gleiche Probleme |
| great-qa-director.agent.md | .opencode/agents/great-qa-director.agent.md | Gleiche Probleme |
| great-program-manager.agent.md | .opencode/agents/great-program-manager.agent.md | Gleiche Probleme |
| great-architect.agent.md | .opencode/agents/great-architect.agent.md | Gleiche Probleme |
| great-requirements-engineer.agent.md | .opencode/agents/great-requirements-engineer.agent.md | Gleiche Probleme |
| great-combinatorics-expert.agent.md | .opencode/agents/great-combinatorics-expert.agent.md | Gleiche Probleme |
| great-ux-lead.agent.md | .opencode/agents/great-ux-lead.agent.md | Gleiche Probleme |
| great-security-architect.agent.md | .opencode/agents/great-security-architect.agent.md | Gleiche Probleme |
| great-devops-engineer.agent.md | .opencode/agents/great-devops-engineer.agent.md | Gleiche Probleme |
| great-legacy-auditor.agent.md | .opencode/agents/great-legacy-auditor.agent.md | Gleiche Probleme |
| great-technical-writer.agent.md | .opencode/agents/great-technical-writer.agent.md | Gleiche Probleme |
| great-web-research.agent.md | .opencode/agents/great-web-research.agent.md | Gleiche Probleme |
| great-senior-prompt-engineer.agent.md | .opencode/agents/great-senior-prompt-engineer.agent.md | Gleiche Probleme |

**Neue korrekte Dateien:** `.opencode/agents/great-*.md` (14 Dateien, korrigiertes Frontmatter)
**Neue Konfiguration:** `opencode.json` (default_agent: great-orchestrator)

**Korrekturen pro Datei:**
- `name:` entfernt (Dateiname wird zum Agent-Namen)
- `mode:` gesetzt (`primary` fuer Orchestrator, `subagent` fuer alle anderen)
- `permission:` mit granularer Berechtigungssteuerung (read, edit, bash mit Glob-Patterns, task, skill, webfetch, websearch, glob, grep)
- `tools:` (Liste) durch `permission:` (Object) ersetzt
- `agents:`, `argument-hint:`, `user-invocable:` aus Frontmatter entfernt (in Body als System-Prompt-Info integriert)
- Doppelte YAML-Delimiter (`---`) entfernt
- Skills-Pfade von `.github/skills/` auf `.opencode/skills/` aktualisiert
- Instructions-Pfade auf `.github/instructions/` (korrekte Source of Truth)




## 2026-11-08 - Veraltete models.py

| Datum | Quelle | Ziel | Begruendung | Agent |
|---|---|---|---|---|
| 2026-11-08 | src/app/models.py | archive/2026-11-08/models.py | Vom Paket src/app/models/ ueberdeckt (Python laedt das Paket). Veralteter Stand ohne is_result, category_type, DataNode, Versionsfelder. Entscheidung des Nutzers. | GREAT Senior Developer |

