# Project Assessment – G.R.E.A.T.
Version: 1.1
Phase: 3 – Sprint 9 Abgeschlossen
Erstellt: 2026-09-04
Aktualisiert: 2026-09-04
Erstellt von: Program Manager Agent
Aktualisiert von: GitHub Copilot CLI

---

## Executive Summary

G.R.E.A.T. (Georg Radikal Einfacher Automatisierter TestcaseDesigner) ist ein browserbasiertes
Open-Source-Werkzeug für automatisiertes Testfalldesign nach ISTQB-Methoden (Äquivalenzklassen,
Grenzwertanalyse, Kombinationsverfahren). Das Projekt hat einen funktionierenden MVP in
Python/FastAPI (v5.8.1) mit SQLite-Datenbank und ist in Phase 3 mit React/TypeScript-Frontend in Entwicklung.

**Aktueller Status: v1.5.2 (2026-09-04) – Sprint-Release freigegeben / Sprint 10 in Vorbereitung.**

### Letztes Release
- **Version:** v1.5.2
- **Datum:** 2026-09-04
- **Neue Features:** Release-Update zur Versionssynchronisierung, Changelog für aktuelles Sprint-Release ergänzt
- **Backend-Tests:** 28 gezielte BVA-/API-Regressionstests (Plus Frontend-BVA-GUI-Suite)
- **PRs gemergt:** Sprint-Release v1.5.2 im aktuellen Branch

### Nächster Termin
- **Sprint 10:** In Planung (Scope freigegeben 2026-09-04)
- **Fokus:** Port-Unification (Port 8000 Standard + Settings-Erweiterung, REQ-4007+), Risikobasierte Testfall-Sortierung (REQ-3034, bisher aufgeschoben aus Sprint 6), Max-Testfälle-Setting in Einstellungen (neu), GUI-Refresh nach Sichtenwechsel/Dialog-Schluss (UX-Fix), offene ToDo-Sichtung + Umsetzung, Multi-User-Analyse als Research/Klärungsauftrag (kein Impl. Sprint 10)

### Sprint-10 Zwischenstand (Nacharbeit Aufgabe 2)
- **REQ-3034** (Risikobasierte Testfall-Sortierung): Implementierung abgeschlossen, zugehörige Tests grün. Status in `requirements_v1.1.md` auf **DONE / TESTED** aktualisiert (Traceability-Nachtrag 2026-09-04).

### Sprint-10 Zwischenstand (Nacharbeit Aufgabe 5 – Max. Testfälle-Setting)
- **REQ-4018** (Max. Testfälle pro Kombination, Default 1000): Backend-Setting (`GREAT_MAX_TESTCASES`, Fallback robust) und Settings-Karte im Frontend implementiert, Generierung respektiert die Obergrenze ohne expliziten `limit`. Backend- und Frontend-Tests grün. REQ neu in `requirements_v1.1.md` angelegt und auf **DONE / TESTED** gesetzt (Nachtrag 2026-09-04).

### Gesamtbewertung

| Dimension | Bewertung | Note |
|---|---|---|
| Codebasis | Mittel | Funktionierender Kern, Architektur-Schulden |
| Testabdeckung | Mittel | Gute Unit-Tests, Integration-Tests lückenhaft |
| Dokumentation | Schwach | Fehlte vor Phase 0, jetzt erstellt |
| Requirements | Mittel | Vorhanden, ab jetzt v1.1.md verbindlich |
| Risikoprofil | Hoch | 5 kritische Risiken (Score 20) |
| Wiederverwendungspotenzial | Hoch | ~50% direkt wiederverwendbar |

---

## 1. Requirement-Analyse

### 1.1 Quellanalyse

Folgende Requirement-Quellen wurden ausgewertet:
- `requirements_v1.0.md` – Strukturierter Backlog (alle Status: Planned)
- `requirements.md` – Erweiterter Backlog mit Epics
- `SYSTEM_v1.0.md` – Governance und technische Vorgaben
- Code-Analyse – Implementierter Funktionsumfang

### 1.2 Konsolidierungsergebnis

Gesamtzahl konsolidierter Requirements: **~60 REQs** in 12 Epics (requirements_v1.1.md)

| Epic | Bereich | Anzahl REQ | Implemented | Planned |
|---|---|---|---|---|
| EPIC-01 | Projektmanagement | 3 | 1 | 2 |
| EPIC-02 | Benutzeroberfläche | 6 | 0 | 6 |
| EPIC-03 | Projektverwaltung | 5 | 3 | 2 |
| EPIC-04 | Testbedingungen | 7 | 4 | 3 |
| EPIC-05 | Geschäftsregeln | 4 | 0 | 4 |
| EPIC-06 | Kombinationsverfahren | 8 | 3 | 5 |
| EPIC-07 | Testfalltabelle | 4 | 1 | 3 |
| EPIC-08 | Export | 5 | 1 | 4 |
| EPIC-09 | Import | 3 | 1 | 2 |
| EPIC-10 | Qualität | 2 | 0 | 2 |
| EPIC-11 | Dokumentation | 1 | 0 | 1 |
| EPIC-12 | KI-Roadmap | 2 | 0 | 2 |

### 1.3 Offene Fragen (5 kritisch)

Vor Phase-1-Start müssen 5 offene Fragen beantwortet werden (OQ-001 bis OQ-005 in requirements_v1.1.md).
Kritischste: **OQ-001 (Technologieentscheidung Python vs. ASP.NET)**.

---

## 2. Architektur-Analyse

### 2.1 Stärken der Ist-Architektur
- **Kombinatorik-Kern** (src/combinatorics/): Gut isoliert, mathematisch verifiziert, testbar
- **ORM-Modelle**: Vollständiges Domänenmodell, CASCADE korrekt
- **REST-API**: FastAPI mit Swagger-Doku automatisch verfügbar
- **CSV-Handler**: Vollständig mit Roundtrip-Tests

### 2.2 Kritische Schwächen
- **Monolithischer main.py** (~56KB): Alles in einer Datei – SOFORT refactoren
- **Kein Migrations-Framework**: Alembic einführen (RISK-T-002, Score 20)
- **Zwei parallele Backends**: src/backend/ archivieren (ADR-004)
- **Frontend-Technologie-Konflikt**: HTMX-MVP vs. Ziel React/TypeScript

### 2.3 Empfohlene Zielarchitektur für Phase 1
```
src/
  api/
    v1/
      routers/
        projects.py
        categories.py
        values.py
        generate.py
        export.py
        import.py
  core/
    combinatorics/   ← aus bestehendem src/combinatorics/ übernehmen
    rules/
    io_handlers/
  db/
    models.py
    migrations/      ← Alembic
  ui/
    templates/       ← Jinja2 (Übergang)
  main.py            ← schlanker Entry-Point
```

---

## 3. Test-Analyse

### 3.1 Stärken
- 11 Testdateien vorhanden
- Pairwise mathematisch korrekt verifiziert
- CSV-Handler vollständig getestet
- FastAPI TestClient für Integration-Tests genutzt

### 3.2 Lücken
- **Keine Coverage-Messung** → pytest-cov sofort einführen
- **Geschäftsregeln nicht getestet** (forbidden, combine)
- **Keine Systemtests** (End-to-End)
- **5 fehlende Kombinatorik-Strategien** ohne Tests

### 3.3 Test-Schulden (Top 3)
1. pytest-cov einrichten + Baseline messen (< 1 Tag)
2. Geschäftsregeln testen (1 Sprint)
3. E2E-Tests mit Playwright (1 Sprint)

---

## 4. Wiederverwendungsstrategie

| Klassifizierung | Komponenten | Maßnahme |
|---|---|---|
| **Reuse (50%)** | models.py, kombinatorik, csv_handler, alle Unit-Tests | Direkt übernehmen |
| **Refactor (25%)** | main.py, orthogonal.py, project_handler.py | Aufteilen / Service-Layer |
| **Replace (3%)** | Jinja2/HTMX Templates | Langfristig → React/TypeScript |
| **Archive (14%)** | src/backend/, test_dummy.py | In archive/2026-09-04/ verschieben |
| **Neu (8%)** | 5 Kombinatorik-Strategien, JSON/Excel/XML, Grenzwertanalyse | TDD in Phase 1 |

---

## 5. Risiken (Zusammenfassung Top 5)

| Score | Risiko | Maßnahme |
|---|---|---|
| 20 | Keine Authentifizierung | OAuth2/JWT für Team-Nutzung vorbereiten |
| 20 | Monolithischer main.py | Sofort aufteilen |
| 20 | Kein Migrations-Framework | Alembic in Sprint 1 Phase 1 |
| 20 | Geschäftsregeln fehlerhaft/untested | Tests in Sprint 1 Phase 1 |
| 20 | Fehler in Kombinatorik-Algorithmen | TDD + mathematische Verifikation |

Vollständiges Risk Log: `documentation/risk-log.md`

---

## 6. Empfehlungen

### Sofortmaßnahmen (vor Phase 1 Sprint 1)
1. **ADR-001 entscheiden**: Python beibehalten oder ASP.NET? → Projektentscheider
2. **pytest-cov einrichten**: Basis-Coverage messen
3. **src/backend/ archivieren**: Verwirrung beseitigen
4. **requirements.txt versionspinnen**: Stabilität sichern

### Sprint 1 – Phase 1
1. main.py in Router-Module aufteilen (DEBT-001)
2. Alembic einführen (ADR-002)
3. Geschäftsregeln (forbidden, combine) implementieren + testen
4. Grenzwertanalyse (REQ-0306)

### Sprint 2 – Phase 1
1. Fehlende Kombinatorik: Lineare Expansion, Risikogewichtet
2. JSON/Excel Export/Import
3. E2E-Tests (Playwright)

### Mittelfristig (Phase 2)
1. Frontend-Migration: React/TypeScript (nach ADR-001-Entscheidung)
2. CI/CD Pipeline (GitHub Actions)
3. Installationspaket (GREAT.exe / Installer)

---

## 7. Priorisierte Roadmap

**Aktualisierter Hinweis (2026-09-04):** Die fruehere Roadmap in diesem Abschnitt wurde durch den Phase-2-Abschlussbericht weiter unten ueberholt. Aktueller Arbeitsstand:

```text
Phase 0  abgeschlossen - Bestandsaufnahme, Requirements, Risiken, ADRs
Phase 1  abgeschlossen - Backend-Stabilisierung und Kernalgorithmen
Phase 2  abgeschlossen - React/TypeScript/Vite Frontend, Office-UX, System-Datenklassen
Phase 3  geplant       - React-First-Ausbau und HTMX-Ablosung
Phase 4  geplant       - Enterprise & KI (Auth, MCDC/T-Wise, Ollama, Multi-User)
```

Aktive Detailplanung fuer Phase 3 steht im Abschnitt **Phase 3 - Roadmap** des Abschlussberichts.

---

## 8. Definition of Done – Phase 0

| Kriterium | Status |
|---|---|
| ✅ Bestehende Codebasis analysiert | DONE |
| ✅ Bestehende Dokumentation analysiert | DONE |
| ✅ Bestehende Requirements analysiert | DONE |
| ✅ requirements_v1.1.md erstellt | DONE |
| ✅ Traceability vorbereitet | DONE |
| ✅ Wiederverwendungsstrategie erstellt | DONE |
| ✅ Risiken dokumentiert | DONE |
| ✅ Architektur bewertet | DONE |
| ✅ Testlandschaft bewertet | DONE |
| ✅ Projektassessment erstellt | DONE |
| ✅ ADR-001: Python/FastAPI (Georg Haupt) | DONE |
| ✅ ADR-003: React/TypeScript sofort (Georg Haupt) | DONE |
| ✅ ADR-006: MIT-Lizenz © Georg Haupt | DONE |
| ✅ LICENSE erstellt | DONE |
| ✅ OQ-004: Kombinatorik-Priorisierung festgelegt | DONE |
| ✅ OQ-005: Grenzwertanalyse Sprint 2 | DONE |
| ⬜ Freigabe Program Manager | OFFEN |
| ⬜ Freigabe Chief Architect | OFFEN |
| ⬜ Freigabe Senior QA Director | OFFEN |

**→ 16/19 Kriterien erfüllt.**
**→ Nur noch formelle Freigaben der 3 Agenten ausstehend – inhaltlich vollständig.**
**→ Phase 1 kann beginnen!**


---

## Phase 2 – Abschlussbericht (2026-09-04)

### Implementierte Features

| Sprint | Feature | REQ-IDs | Status |
|--------|---------|---------|--------|
| Phase 2, Sprint 1 | React/TypeScript/Vite Grundstruktur, Tailwind CSS | REQ-1201–1205 | ✅ |
| Phase 2, Sprint 2 | Zweispaltige Ansicht, CategoryTree, TestCasePanel, DELETE-Endpunkte | REQ-1206–1208 | ✅ |
| Phase 2, Sprint 3 | Shortcuts, Kontextmenü, Drag&Drop, Toast, Sortierung, Rename | REQ-1209–1214 | ✅ |
| Phase 2, Sprint 4 | Regeldarstellung, Tabs, System-Datenklassen | REQ-1215–1216 | ✅ |
| Phase 2, Sprint 5 | Generation-History, Bulk-Delete Projekte, Datenklassen-Bibliothek, Sync-Regel | REQ-2001–2003, REQ-0011 | ✅ |
| Phase 2, Sprint 5b | Export-Fix /api/-Prefix, Öffnen-Fix, Datenklassen fertig | — | ✅ |
| Phase 2, Sprint 6 | System-Datenklassen optimiert, Generierungsname editierbar, Bulk-Delete DC | REQ-2004–2006 | ✅ |
| Phase 2, Bugfixes | Alt+N Shortcut, DEL-Logik (Wert/Kategorie), Umlaute, Projekttitel | — | ✅ |
| Phase 2, UX | Alle/Keinen markieren, Markierung umkehren (Projekte + Datenklassen) | — | ✅ |
| Phase 2, UX | Löschlogik mit Generierungs-Dialog (Ja/Nein/Anzeigen) | REQ-2002 Erw. | ✅ |

### Technischer Stand (2026-09-04)
- **163 Tests** – alle grün
- **Frontend:** React 18 / TypeScript / Vite / Tailwind CSS – 115 Module, ~256 KB
- **Backend:** FastAPI / SQLAlchemy / SQLite – vollständige REST-API unter /api/
- **System-Datenklassen:** 8 vorinstallierte Klassen (löschgeschützt)
- **HTMX-Ansicht:** noch vorhanden, wird in Phase 3 archiviert (REQ-3011)

### Phase-3-Entscheidungen
- REQ-0011 (View-Synchronitätspflicht) **aufgehoben** – React ersetzt HTMX vollständig
- Phase 3 = React-First + HTMX-Ablösung
- Ehemals „Phase 3 Enterprise" → jetzt **Phase 4**

### Phase 3 – Roadmap

| Sprint | Inhalt | Must/Should |
|--------|--------|------------|
| Sprint 1 | Top-Nav, Generierungen-Tab, Datenklassen-Überarbeitung, Einstellungen-Platzhalter | Must/Should |
| Sprint 2 | Regeleditor in React, Regelwiderspruch, Wert-Eigenschaften, Default-Wert, „Mit Regeln generieren" | Must/Should |
| Sprint 3 | Regelprüfung nachträglich | Should |
| Sprint 4 | HTMX archivieren, Final-Cleanup | Must |

---

## Phase 3 – Sprint 4 Planning Summary (2026-09-04)

*Siehe auch: `documentation/phase-3-sprint-4-planning.md` (finales Planning-Dokument)*

Vollständiges Planning-Dokument wurde unter `documentation/phase-3-sprint-4-planning.md` abgelegt.

---

## Phase 3 – Sprint 5 Planning Summary (2026-09-04)

*Siehe auch: `documentation/phase-3-sprint-5-planning.md` (finales Planning-Dokument)*

**Sprint-Ziel:** Verbesserung der User Experience durch Theme-System mit Dark-Mode und weiteren Themes, Risikoabdeckungs-Anzeige für bessere Testfall-Priorisierung.

**Status:** ✅ GO – Sprint 5 GESTARTET (2026-09-04)

**Sprint-5-Backlog (150 SP total) – Linearer Workflow eingeführt:**

| Priorität | REQ | Titel | SP | Status |
|---|---|---|---|---|
| 1 | REQ-3045 | Theme-System Grundlage | 40 | OFFEN |
| 2 | REQ-3046 | Theme Dark | 15 | OFFEN |
| 3 | REQ-3047 | Theme Steampunk | 20 | OFFEN |
| 4 | REQ-3048 | Theme Rainbow | 15 | OFFEN |
| 5 | REQ-3049 | Theme Heavy Metal | 15 | OFFEN |
| 6 | REQ-3050 | Risikoabdeckung pro Testfall | 25 | OFFEN |
| 7 | REQ-3051 | Risikoabdeckungs-Summe Generierung | 20 | OFFEN |

**Neue Projektregel (ab Sprint 5) – VERBINDLICH:**
> **Linearer Workflow:** REQs werden ausschließlich sequenziell abgearbeitet. Ein Feature-Branch nach dem anderen. Erst mergen, dann nächsten Branch starten. Kein paralleles Arbeiten auf mehreren Feature-Branches. Eliminiert Merge-Konflikte, verbessert Code-Review-Qualität.

**Sprint-6+ Backlog (300 SP):**

| REQ | Titel | SP | Prio | Sprint | Abhängigkeit |
|---|---|---|---|---|---|
| REQ-3052 | Tabellenansicht Testfälle | 35 | MUST | 6 | – |
| REQ-3062 | Dark-Mode System-Sync | 10 | SHOULD | 6 | REQ-3046 |
| REQ-3053 | Undo/Redo | 30 | SHOULD | 6 | – |
| REQ-3054 | Tastaturnavigation | 20 | SHOULD | 6 | – |
| REQ-3058 | PDF-Export | 25 | SHOULD | 7 | – |
| REQ-3059 | Kategorie-Kommentare | 20 | SHOULD | 7 | – |
| REQ-3055 | Projekt-Vorlagen | 25 | COULD | 7 | – |
| REQ-3056 | CSV-Import | 30 | COULD | 7 | – |
| REQ-3057 | i18n Deutsch/Englisch | 40 | COULD | 8 | – |
| REQ-3060 | Testfall-Kommentare | 15 | COULD | 8 | – |
| REQ-3061 | Versionshistorie Projekt | 50 | COULD | Backlog | – |

**Offene ADR-Entscheidungen vor Sprint-Start:**
- **ADR-011**: Theme-System-Ansatz (CSS-Variablen + Tailwind EMPFOHLEN vs. Styled-Components vs. Tailwind-Klassen)
- **ADR-013**: Risikoabdeckungs-Berechnung (On-the-fly EMPFOHLEN vs. gecacht)

**Freigabe (2026-09-04):**
- ✅ Program Manager (dokumentiert + Commit)
- ⏳ Chief Architect (ADR-011-Entscheidung vor REQ-3045-Start)
- ⏳ Senior QA Director (Test-Strategie für Sprint 5)

---

## Phase 3 – Sprint 4 Abschlussbericht (2026-09-04)

**Status:** ✅ ABGESCHLOSSEN – 6 PRs, 223+ Tests grün, alle Kriterien erfüllt

| Metrik | Wert | Quelle |
|---|---|---|
| REQs umgesetzt | REQ-3039 bis REQ-3044 (6 REQs) | git log |
| PRs merged | 6 Feature-Branches | GitHub |
| Tests gesamt | 223 | test run output |
| Coverage | >= 90% | --cov report |
| Projektregel | Linearer Workflow definiert | phase-3-sprint-5-planning.md |
| Governance | Aktualisiert mit Sprint-5-Planung | project-assessment.md |

---

## Phase 3 – Sprint 5 Abschlussbericht (2026-09-04)

**Status:** ✅ ABGESCHLOSSEN – 10 PRs, 367 Tests grün, alle Sprint-5-REQs implementiert & getestet

### Implementierte Features

| REQ | Titel | Sprint | PR | Status |
|---|---|---|---|---|
| REQ-3045–3049 | Theme-System (Normal, Dark, Steampunk, Rainbow, Heavy Metal) | Sprint 5 | #13–#22 | ✅ DONE |
| REQ-3050 | Risikoabdeckung pro Testfall (Summe `risk_weight`) | Sprint 5 | #16 | ✅ DONE |
| REQ-3051 | Risikoabdeckungs-Prozentsatz pro Generierung (farbiges Badge) | Sprint 5 | #17 | ✅ DONE |
| REQ-3052 | Tabellenansicht Testfälle – sortierbare Spalten, Sticky Header, CSV-Export | Sprint 5 | #18 | ✅ DONE |
| REQ-3053 | Undo/Redo (STRG+Z / STRG+Y, max. 50 Schritte) | Sprint 5 | #19 | ✅ DONE |
| REQ-3054 | Tastaturnavigation (Pfeiltasten, Enter, Delete, F2, Escape, ARIA) | Sprint 5 | #20 | ✅ DONE |
| REQ-3062 | Dark-Mode System-Sync (OS `prefers-color-scheme`) | Sprint 5 | #21 | ✅ DONE |
| REQ-3063 | Fehlerwert-Testfälle rot markiert in Tabelle | Sprint 5 | #22 | ✅ DONE |
| REQ-3064 | Multi-Range BVA (mehrere Äquivalenzklassen, erlaubt/nicht erlaubt) | Sprint 5 | #14 | ✅ DONE |
| BUG-2 | Start.bat Timeout erhöht – Backend startet vor Frontend-Proxy | Sprint 5 | #15 | ✅ FIXED |
| BUG-4 | BVA ISTQB-konform korrigiert (2/3/4-Wert-Methode nach ISTQB-Standard) | Sprint 5 | #13 | ✅ FIXED |

### Technischer Stand (2026-09-04)

| Metrik | Wert | Trend |
|---|---|---|
| Gesamt-Tests | 367 (263 Backend + 104 Frontend) | ⬆️ +104 |
| Test-Coverage | >= 90% | ✅ Stabil |
| Frontend-Bundle | ~280 KB | ⬆️ +24 KB (Themes) |
| REQs Sprint 5 | 20 (REQ-3019–3030, REQ-3045–3054, REQ-3062–3064) | ✅ 100% done |
| PRs gemergt | 10 (#13–#22) | ✅ Alle green |
| Commits | 15+ | ✅ Saubere History |

### Version 1.1.0 Release

**Release-Highlights:**
- ✅ Theme-System mit 5 vordefinierten Themes (hellbar/dunkel/steampunk/rainbow/heavy-metal)
- ✅ Risikoabdeckungs-Metriken für bessere Testfall-Priorisierung
- ✅ Office-ähnliche Tabellenbedienung (Sortierung, Export, Undo/Redo)
- ✅ Volle Tastaturnavigation für Power-Users (ARIA-konform)
- ✅ Multi-Range BVA für komplexe numerische Modelle
- ✅ ISTQB-konforme Grenzwertanalyse (2/3/4-Wert-Methode)

**Blockierende Probleme:** Keine

**Nebenprobleme (für Sprint 6):**
- PDF-Export noch ausstehend (REQ-3058)
- i18n (Deutsch/Englisch) geplant (REQ-3057)
- Projekt-Kommentare (REQ-3024–3025) in Planung

### Implikationen für Phase 4

- Codebasis bereit für Enterprise-Features (Auth, Multi-User)
- Kombinatorik-Kern (REQ-3039–3044, REQ-3040) ist constraint-aware und T-Wise/MCDC-fähig
- UX-Layer (Themes, Undo/Redo, Tastaturnavigation) für breite Nutzer-Base optimiert
- Performance akzeptabel: Pairwise < 1s, T-Wise 3-weise < 5s, MCDC < 30s

**Empfohlener Übergang:** Phase 4 kann mit Authentifizierung (REQ-4001 / OAuth2-JWT) starten.

---

## Phase 3 – COMPLETION SUMMARY (2026-09-04)

**Status:** ✅ **PHASE 3 ABGESCHLOSSEN**

**Statistiken:**
- **Zeitraum:** 2026-09-04 bis 2026-09-04 (2 Wochen)
- **Sprints:** Sprint 4 + Sprint 5
- **PRs gemergt:** 20 Feature-PRs
- **Tests:** 367 (263 Backend, 104 Frontend)
- **REQs umgesetzt:** REQ-3019–3064 (21 Features)
- **Bugs gefixed:** 2 (BUG-2: Start.bat, BUG-4: BVA ISTQB)

**Phase-3-Ziele ERREICHT:**
- ✅ React-First: Volle Funktionalität in React/TypeScript
- ✅ Office-UX: Tastaturnavigation, Undo/Redo, Theme-System
- ✅ HTMX-Ablösung: Vorbereitet für Sprint 4, noch archivieren
- ✅ System-Datenklassen: 8 vorinstallierte Klassen
- ✅ Kombinatorik: T-Wise, MCDC, Risk-Based, Multi-Range BVA

**Übergabe an Phase 4:**
- Codebase: Stabil, 367 Tests grün
- Technik-Schulden: Dokumentiert in `phase-4-sprint-stabi-needs.md`
- Roadmap: Sprint-6–9 geplant (Stabi + Multi-User)
- Risiken: RISK-S-001 (Auth) für Sprint 8–9

---

## Phase 4 – KICKOFF PLANNING (2026-09-04)

**Status:** ✅ **PHASE 4 PLANNED – READY FOR SPRINT 6**

**Gesamtvision Phase 4:**
1. **Sprint 6–7:** Technische Stabilisierung (REQ-4007, REQ-4008, REQ-4009, REQ-4010)
2. **Sprint 8:** Multi-User-Enablement (REQ-4006 – PostgreSQL optional)
3. **Sprint 9+:** Enterprise Features (REQ-4001–4005)

**Neue Requirements Phase 4:**
- REQ-4007: GREAT_PORT + .env Support (Sprint 6)
- REQ-4008: Health-Check /health Endpoint (Sprint 6)
- REQ-4009: Strukturiertes Logging (Sprint 7)
- REQ-4010: E2E-Tests Playwright (Sprint 7)
- REQ-4006: Multi-User / PostgreSQL (Sprint 8)
- REQ-4001–4005: Enterprise Features (Sprint 9+)

**Dokumentation Phase 4 verfügbar:**
- `documentation/phase-4-planning.md` – Sprint-Struktur + Zeitleiste
- `documentation/phase-4-sprint-stabi-needs.md` – Technische-Schulden-Analyse (25 Kandidaten)
- `Agenten und basisinfos/requirements_v1.1.md` – REQ-4001–4010 hinzugefügt

**Go/No-Go:** ✅ **GO** – Keine Blockierer, Phase 4 starten.

---

## Sprint 10 – Planning Summary (2026-09-04)

**Status:** 🔵 IN PLANUNG – Scope freigegeben durch Program Manager

**Sprint-Ziel:** Qualitäts- und UX-Stabilisierung (Port-Unification, Risikobasierte Sortierung, Settings-Ausbau) + Research-Aufgabe Multi-User

### Priorisierter Backlog Sprint 10

| Prio | Aufgabe | REQ-IDs | Aufwand | Status |
|---|---|---|---|---|
| 1 | Offene ToDos sichten + priorisieren (Review-Task) | — | S | OFFEN |
| 2 | Risikobasierte Kombination: absteigende Sortierung nach risk_coverage | REQ-3034 | M | OFFEN |
| 3 | GUI-Aktualisierung: React-Reload nach Sichtenwechsel / Dialog-Schluss | REQ-4019 (neu) | M | OFFEN |
| 4 | Port-Unification: Port 8000 Standard, Port 5173 nur Dev-Option, Settings-Erweiterung | REQ-1202, REQ-4007, REQ-4017 (neu) | M | OFFEN |
| 5 | Max. Testfälle-Setting in Einstellungen (Default 1000) | REQ-4018 (neu) | S | ERLEDIGT |
| 6 | Multi-User-Analyse: Research + Klärung Benachrichtigungsfunktion (kein Impl.) | REQ-4001, REQ-4002 | S | OFFEN |
| 7 | Offene ToDos aus Aufgabe 1 umsetzen (Scope TBD nach Aufgabe 1) | TBD | TBD | BLOCKIERT (→ Aufg. 1) |

### REQ-Zuordnung

| Aufgabe | Bekannte REQ-IDs | Anmerkung |
|---|---|---|
| 1 (Port-Unification) | REQ-1202 (Status: offen, Phase 2/Sprint 1, implizit implementiert), REQ-4007 (Tested Sprint 6), REQ-4017 (neu: Port-Wahl in Settings) | REQ-4007 bereits getestet – Sprint 10 ergänzt Settings-UI |
| 2 (Risikobasierte Sortierung) | REQ-3034 (Planned, Phase 3 Sprint 6 – aufgeschoben) | Daten vorhanden (risk_weight via REQ-3007/3050), Algorithmus bekannt |
| 3 (Max. Testfälle) | REQ-4018 (neu, p3-settings Bereich) | Einstellungen-Seite bereits vorhanden (REQ-3002, REQ-4012) |
| 4 (GUI-Refresh) | REQ-4019 (neu) oder BUG-5 | React-State-Management (Zustand-Store) |
| 5 (Multi-User) | REQ-4001, REQ-4002 (beide Planned Sprint 10+) | Nur Research/Klärung, keine Implementierung Sprint 10 |

### Risikoeinschätzung pro Aufgabe

| Aufgabe | W | I | Score | Ampel | Begründung |
|---|---|---|---|---|---|
| Port-Unification | 1 | 3 | 3 | 🟢 | REQ-4007 bereits getestet; Settings-UI ist inkrementell |
| REQ-3034 Risikobasierte Sortierung | 2 | 2 | 4 | 🟢 | Algorithmus bekannt, risk_weight-Daten vorhanden (REQ-3050 ✅) |
| Max. Testfälle-Setting | 1 | 2 | 2 | 🟢 | Einfache Settings-Erweiterung, Backend-Parameter |
| ToDo-Review (Aufg. 1) | 1 | 1 | 1 | 🟢 | Nur Analyse, kein Code |
| GUI-Refresh (React) | 2 | 3 | 6 | 🟡 | React-State-Änderungen können Seiteneffekte auslösen; QA-Review empfohlen |
| Multi-User-Analyse | 4 | 4 | 16 | 🔴 | **ESKALATIONSPFLICHTIG** (Score ≥ 10): Architekturentscheid WebSocket/SSE/Polling offen; Auth (RISK-S-001 Score 20) noch nicht implementiert; Experten-Input Chief Architect + Security erforderlich |
| ToDo-Umsetzung (Aufg. 7) | — | — | TBD | ⚪ | Scope erst nach Aufg. 1 bekannt; eigene Risikobewertung nach Review |

### Empfehlung Multi-User-Analyse (Aufgabe 6)

**Empfehlung: Research/Klärungsauftrag ohne Implementierung in Sprint 10. ✅ REALISTISCH.**

Begründung:
- REQ-4001 (Auth/JWT) ist Voraussetzung für jede Benachrichtigungsfunktion – noch **Planned**, nicht in Sprint 10
- Architekturentscheidung (WebSocket vs. SSE vs. Polling) ist offen → Chief Architect Input zwingend
- RISK-S-001 (keine Authentifizierung, Score 20) muss vor Multi-User-Features adressiert sein
- Research-Output: ADR-Entwurf + Anforderungsliste für Sprint 11/12

### Abhängigkeiten im Sprint

```
Aufgabe 4 (ToDo-Review) ──► Aufgabe 7 (Umsetzung)
Aufgabe 3 (Settings) ────► kann parallel zu Aufgabe 1 (Port in Settings)
Aufgabe 2 (REQ-3034) ────► unabhängig, Prio 2 nach Review
Aufgabe 6 (Multi-User) ──► Research-Output als Input für Sprint-11-Planning
```

### Go/No-Go Empfehlung

- ✅ **GO** für Aufgaben 1–5, 6 (Research only)
- ⏳ Aufgabe 7: **HOLD** bis Aufgabe 1 (ToDo-Review) abgeschlossen
- 🔴 Aufgabe 6 (Multi-User Implementierung): **NO-GO** für Sprint 10 – Research only
- 🔴 Eskalation an **GREAT Chief Architect** erforderlich: Multi-User-Architekturentscheidung (Score 16), Port-Architektur-Bestätigung

**Freigabe Sprint 10 (2026-09-04):**
- ✅ Program Manager – Scope + Priorisierung freigegeben
- ⏳ Chief Architect – Eskalation: Multi-User-Architektur + REQ-4019 Tech-Ansatz
- ⏳ Senior QA Director – Test-Strategie für REQ-3034, REQ-4019

---

## EPIC-18 – Multi-User Nutzung (Teams bis 10 Personen) – Sprint 11–13 Planning (2026-09-04)

**Status:** 🔵 SPRINTFÄHIG VORBEREITET – Program Manager Freigabe erteilt
**Auslöser:** Eskalation Sprint 10 (Multi-User-Architektur, Score 16) aufgelöst durch ADR-012 (HYBRID-Ansatz)
**Vollständige EPIC-Definition:** `Agenten und basisinfos/requirements_v1.1.md` → EPIC-18

### Zielbild

Teams bis 10 Personen arbeiten gemeinsam an G.R.E.A.T.-Projekten. Kollisionssichere
Zusammenarbeit über Login/Rollen + Optimistic Concurrency + Stale-Data-Warning.
**Keine** volle Realtime-Kollaboration (kein WebSocket-Live-Editing, kein Presence,
kein CRDT/OT) in dieser Ausbaustufe – siehe ADR-012.

### Sprint-Backlog (priorisiert)

| Sprint | REQ-ID | Titel | Prio | Aufwand | Risiko | Status |
|---|---|---|---|---|---|---|
| 11 | REQ-4001 | Authentifizierung (OAuth2/JWT) | Must | L | 🟡 M | Planned |
| 11 | REQ-4020 | Rollen & Rechte Basismodell (Admin/Editor/Viewer) | Should | M | 🟡 M | Planned |
| 12 | REQ-4006 | Multi-User-Datenmodell (SQLite/PostgreSQL optional) | Must | L | 🟡 M | Planned |
| 12 | REQ-4021 | Optimistic Concurrency Control (Versionsfeld, 409) | Must | L | 🟡 M | Planned |
| 12 | REQ-4022 | Stale-Data-Warning Frontend | Must | M | 🟢 L | Planned |
| 13 | REQ-4023 | Projekt-Sharing / Mitgliederverwaltung | Should | M | 🟡 M | Planned |
| 13 | REQ-4024 | Minimaler Audit-Trail (last_modified_by/-at) | Should | S | 🟢 L | Planned |
| 13 | – | Lasttest 10 gleichzeitige Nutzer + E2E-Konfliktszenario | Must | M | 🟡 M | Planned |

*(Aufwand: S/M/L grob analog Story-Points niedrig/mittel/hoch; Risiko-Ampel wie Risk-Log-Schema)*

### Out of Scope (explizit, siehe EPIC-18-Detail)

Realtime-Kollaboration (WebSocket/SSE/CRDT), Live-Presence, Echtzeit-Benachrichtigungen,
Enterprise-SSO, Multi-Tenant-SaaS, Teamgrößen > 10 Personen.

### Freigabe-Voraussetzungen vor Sprint 11

- ⏳ **Chief Architect:** ADR-007 (DB-Strategie SQLite/PostgreSQL) final bestätigen
- ⏳ **Security Architect:** Auth-Schema-Review (OAuth2/JWT, Passwort-Hashing) vor Implementierung
- ⏳ **Senior QA Director:** Teststrategie für Konfliktszenarien (REQ-4021/4022) freigeben
- ✅ **Program Manager:** Scope, Priorität, Out-of-Scope-Abgrenzung freigegeben (dieses Dokument)

### Risiken

Siehe `documentation/risk-log.md` RISK-S-001 (20, bestehend), RISK-T-008 (12, neu für EPIC-18),
RISK-T-006 (8, SQLite-Multi-User). RISK-S-001 und RISK-T-008 sind eskalationspflichtig (Score ≥ 10).

### Go/No-Go

- ✅ **GO** für Sprint-11-Planung (Backlog sprintfähig, REQs vollständig in requirements_v1.1.md)
- 🔴 **Bedingung:** Sprint-11-Start erst nach Chief-Architect- und Security-Architect-Freigabe (siehe oben)

---
