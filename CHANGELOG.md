# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

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
