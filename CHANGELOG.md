# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [Unreleased]

### ✨ Neue Features
- **REQ-3034**: Generierte Testfälle werden absteigend nach kumuliertem Risiko-Score sortiert (Summe der `risk_weight` aller zugewiesenen Werte je Testfall). Testfälle mit Fehlerwerten behalten weiterhin Vorrang (REQ-3018/BUG-5) und werden unabhängig von ihrem Risiko-Score ans Ende der Liste sortiert.
- **REQ-4018**: Neue Einstellung "Maximale Anzahl Testfälle" (Default 1000) begrenzt die Anzahl generierter Testfälle pro Kombination, wenn kein expliziter `limit`-Wert im Request angegeben ist. Konfigurierbar über die Umgebungsvariable `GREAT_MAX_TESTCASES` (Backend) sowie über eine neue Karte auf der Einstellungen-Seite (Frontend, lokal gespeichert, ohne Server-Neustart wirksam).

## [1.5.1] - 2026-09-01

### 🐛 Bugfixes – Sprintabschluss
- **REQ-3041 / REQ-3042**: Dezimaltrennzeichen mit Punkt oder Komma werden in der Grenzwertanalyse jetzt konsistent akzeptiert (`10.01`, `10,01`).
- BVA-Validierung erkennt numerische Eingaben korrekt und vermeidet unnötige Fehlermeldungen beim Dateneingang.
- Sprint-Release abgeschlossen und für den nächsten Sprint vorbereitet.

## [1.5.0] - 2026-08-19

### ✨ Neue Features – Sprint 9

#### REQ-4012: Datenklassen-Überarbeitung + BugMagnet-Import
- System-Datenklassen umbenannt in "Beispiele"
- Settings-Seite: Neuer "Datenklassen"-Bereich mit Import-Button
- Live-Import von BugMagnet GitHub (https://github.com/gojko/bugmagnet)
- Nach Import: Bezeichnung wechselt zu "Bug Magnet Import"
- Endpoints: `POST /api/dataclasses/bugmagnet-import`, `GET /api/dataclasses/bugmagnet-status`

#### REQ-4013: Eigene Datenklassen Import/Export JSON
- Export: eigene Datenklassen als JSON herunterladen
- Import: JSON-Datei hochladen (Merge-Strategie, Legacy-Format unterstützt)
- UI-Kasten oben in "Meine Datenklassen"
- Endpoints: `GET /api/dataclasses/export-user`, `POST /api/dataclasses/import-user`

#### REQ-4014: Kategorien & Werte – Tabellarische Ansicht + Drag & Drop
- Spalten-Header in Werte-Tabelle (Reihenfolge, Wert, Aktionen)
- Werte per Drag & Drop umsortierbar (Reihenfolge wird gespeichert)
- BVA-Symbol größer mit "BVA"-Label
- Default-Markierung als ★ (statt ?)
- Endpoint: `PUT /api/dataclasses/{id}/values/reorder`

#### REQ-4015: BVA-Visualisierung überarbeitet + Fehlerwert-Bug-Fix
- Symbolischer Zahlenstrahl: gleichmäßige Abstände (Lesbarkeit > Maßstab)
- Multi-Range: jede Äquivalenzklasse farbig unterschieden, Lücken ausgegraut
- `BVARange.is_valid`: erlaubte/unerlaubte Äquivalenzklassen explizit markierbar
- Fehlerwert-Bug behoben: `is_error` korrekt in Kategorien & Werte angezeigt

#### REQ-4016: Neuer Typ "Ergebnis" für Kategorien (ISTQB Expected Result)
- Kategorien als "Ergebnis-Kategorie" markierbar (`is_result` Flag)
- Ergebnis-Kategorien werden **nicht** automatisch in Kombinatorik einbezogen
- Nur durch Regeln oder manuelle Eingabe befüllbar (ISTQB-konform)
- Testfall-Tabelle: Ergebnis-Spalte immer sichtbar, leere Felder farblich markiert
- `ResultCellEditor`: Dropdown + Freitext nach Generierung editierbar

### 🔧 Qualität
- 340 Backend-Tests (+7 seit v1.4.0)
- 5 PRs (#36–#40) sauber gemergt

---

## [1.1.0] - 2026-07-02 – Sprint 5: UX, Risikoabdeckung, BVA-ISTQB

### Neue Features
- **REQ-3045–3049**: Theme-System (Normal, Dark, Steampunk, Rainbow, Heavy Metal)
- **REQ-3050**: Risikoabdeckung pro Testfall (Summe `risk_weight`)
- **REQ-3051**: Risikoabdeckung-Prozentsatz pro Generierung (farbiges Badge)
- **REQ-3052**: Tabellenansicht Testfälle – sortierbare Spalten, Sticky Header, CSV-Export
- **REQ-3053**: Undo/Redo (Strg+Z / Strg+Y, max. 50 Schritte)
- **REQ-3054**: Tastaturnavigation (Pfeiltasten, Enter, Delete, F2, Escape, ARIA)
- **REQ-3062**: Dark-Mode System-Sync (OS `prefers-color-scheme`)
- **REQ-3063**: Fehlerwert-Testfälle rot markiert in Tabelle
- **REQ-3064**: Multi-Range BVA (mehrere Äquivalenzklassen, erlaubt/nicht erlaubt)

### Bugfixes
- **BUG-2**: Start.bat Timeout erhöht – Backend startet vor Frontend-Proxy
- **BUG-4**: BVA ISTQB-konform korrigiert (2/3/4-Wert-Methode nach ISTQB-Standard)

### Chores
- `.gitignore` aktualisiert – `test_bugmagnet.py` lokal erhalten

---

## [1.0.0] – 2026-07-01 – Initial Public Release

**Erstes öffentliches Release nach kompletter Neuentwicklung.**

### Grundlegende Änderungen
- Vollständige Neuentwicklung als Web-App (vormals Desktop-Lösung „Tanos")
- Umbenennung: Tanos → G.R.E.A.T. (Georg Radikal Einfacher Automatisierter TestcaseDesigner)
- Neue Architektur: Python/FastAPI Backend + React/TypeScript Frontend
- Lizenzwechsel auf AGPL-3.0 mit Dual-Licensing (kommerzielle Nutzung genehmigungspflichtig – siehe NOTICE.md)

### Backend (Python/FastAPI/SQLite)
- Projekt-Management mit Kategorien und typisierten Werten
- Wert-Eigenschaften: Risiko, Datentyp, Fehlerwert, Default-Markierung
- Regellogik: Verboten (Paar), Abhängig (Wenn-Dann), Kombinieren (Fan-out)
- Widerspruchs-Erkennung bei Regeln
- Kombinatorik-Strategien: Each-Choice, Pairwise, Lineare Expansion, Manuell
- Grenzwertanalyse (BVA) als Backend-Endpoint
- System-Datenklassen (typisierte Äquivalenzklassen)
- User-Datenklassen (custom, mit Typ-Validierung)
- REST-API mit OpenAPI-Dokumentation

### Frontend (React/TypeScript/Vite)
- Office-ähnliche Bedienung mit Zwei-Pane-Layout
- Kategorie-Baumansicht mit Inline-Bearbeitung
- Regeleditor mit Live-Konflikt-Warnung
- Testfall-Generierung mit optionaler Regel-Anwendung
- Generierungs-Historie pro Projekt (mit editierbaren Namen)
- Datenklassen-Verwaltung (System + User)
- Export: CSV, JSON, Excel
- Einheitliche Top-Navigation

### Governance
- Requirements-Traceability (REQ-IDs)
- Test-Driven Development mit 179+ Tests
- Architecture Decision Records (ADRs)

### Bekannte Einschränkungen
- Single-User-App (kein Multi-User)
- Keine Authentifizierung (lokaler Betrieb)
- Nur SQLite (kein PostgreSQL)

### Roadmap
Siehe [RELEASE_NOTES.md](RELEASE_NOTES.md) für geplante Features (Phase 3 Sprint 4+ und Phase 4).

---

# Changelog � G.R.E.A.T.

Alle wichtigen �nderungen werden in dieser Datei dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Phase 1 Sprint 3] � 2026-06-23

### Added
- E2E-Tests mit Playwright/Chromium (tests/e2e/)
- Start.sh � Startskript f�r Linux / Raspberry Pi (REQ-0010)
- INSTALLATION.md � Schritt-f�r-Schritt Installation (Windows + RPi)
- TESTING_GUIDE.md � TDD-Workflow, Coverage, Teststruktur
- requirements-rpi.txt � Abh�ngigkeiten ohne PySide6 f�r RPi
- pytest-playwright zu requirements.txt erg�nzt

### Fixed
- boundary_value.py: Ganzzahlige Floats (18.0) als Integer formatiert

---

## [Phase 1 Sprint 2] � 2026-06-23

### Added
- Grenzwertanalyse / BVA (REQ-0306): src/combinatorics/boundary_value.py
  - API-Endpunkt: POST /categories/{cid}/bva
- Risikogewichtete Generierung (REQ-0805): src/combinatorics/risk_based.py
- JSON Export (REQ-1001): GET /generations/{id}/export/json
- Excel Export (REQ-1002): GET /generations/{id}/export/xlsx
- python-multipart in requirements.txt

### Fixed
- test_ui_crud.py: Projektname durch UUID eindeutig
- test_backend_mvp.py: CSV-Assertion korrigiert
- test_export_status.py: sep=-Zeile �bersprungen

---

## [Phase 1 Sprint 1] � 2026-06-10 / 2026-06-23

### Added
- Router-Refactoring DEBT-001: main.py von ~1400 auf 80 Zeilen
  - services.py, ui_helpers.py, templates_config.py, routers/ (5 Module)
- Lineare Expansion (REQ-0803): src/combinatorics/linear_expansion.py
- RuleEngine (REQ-0700/0701/0702): src/core/rules/rule_engine.py
- Alembic-Migrationen: src/db/migrations/
- pytest-cov + .coveragerc

---

## [Phase 0] � 2026-06-10

### Added
- Bestandsanalyse der Codebasis
- requirements_v1.1.md (~60 REQs)
- project-assessment.md, risk-log.md, decision-log.md (ADRs 001-006)
- MIT-Lizenz (c) Georg Haupt
- Technologieentscheidung Python/FastAPI (ADR-001)
- Frontend-Entscheidung React/TypeScript (ADR-003)

---

## [5.8.1] � 2025-10-07 (Legacy/MVP)

### Added
- Vollst�ndiges Datenmodell SQLite + SQLAlchemy
- HTMX-Weboberfl�che (Projektverwaltung, Kategorien, Werte, Regeln)
- Pairwise/Orthogonal Generator
- CSV Export/Import
- FastAPI mit Swagger-Dokumentation
