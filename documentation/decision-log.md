# Decision Log – G.R.E.A.T.
Version: 1.0
Phase: 0 – Bestandsaufnahme
Erstellt: 2026-06-10
Erstellt von: Program Manager Agent

---

## Format

Jeder Eintrag enthält:
- **ID**: ADR-XXX (Architecture Decision Record)
- **Datum**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Kontext**: Warum war eine Entscheidung nötig?
- **Entscheidung**: Was wurde entschieden?
- **Begründung**: Warum diese Option?
- **Konsequenzen**: Was folgt daraus?
- **Entscheider**: Welcher Agent / welche Person

---

## ADR-001 – Technologiestack: Python/FastAPI beibehalten

**Datum:** 2026-06-10
**Status:** ✅ Accepted (Georg Hartel, 2026-06-10) – Chief Architect Bestätigung ausstehend

**Kontext:**
SYSTEM_v1.0.md schreibt als Zielarchitektur ASP.NET Core Backend vor.
Die bestehende Codebasis ist Python/FastAPI. Eine sofortige Migration würde alle bestehenden
Komponenten (Kombinatorik, CSV-Handler, Tests) verwerfen.
Zusätzliche Anforderung: Betrieb auf Raspberry Pi (ARM-Architektur) muss möglich sein.

**Entscheidung:** Python/FastAPI als Backend beibehalten + React/TypeScript Frontend (sofort)

- ASP.NET Core wird **nicht** eingesetzt
- Python/FastAPI bleibt das Backend (alle Phasen)
- React/TypeScript Frontend startet in Phase 2 (OQ-003 entschieden: sofort React)
- Kombinatorik-Kern (Python) wird weiterentwickelt

**Begründung:**
- Wiederverwendung des funktionierenden Kombinatorik-Kerns (Python)
- **Raspberry Pi Kompatibilität**: Python läuft nativ auf ARM/Raspberry Pi ohne .NET-Runtime-Probleme
- **Einfache Installation**: `pip install -r requirements.txt` + `Start.bat/Start.sh` für alle Plattformen
- Keine Parallelentwicklung in zwei Tech-Stacks
- REST-API ermöglicht React-Frontend ohne Backend-Änderungen
- Python ist für Tester/QA-Engineers zugänglicher als .NET

**Raspberry Pi Anforderungen (Chief Architect muss bestätigen):**
- uvicorn + FastAPI auf ARM64 läuft problemlos (getestet auf Pi 4/5)
- SQLite ohne externe Abhängigkeiten
- `Start.sh` für Linux/Raspberry Pi ergänzen
- Installationsanleitung für Raspberry Pi OS (Debian) erstellen

**Konsequenzen:**
- SYSTEM_v1.0.md §12 (ASP.NET Core) wird durch diesen ADR überschrieben
- requirements.txt muss versionsgepinnt werden
- Installationspaket: kein GREAT.exe, stattdessen `Start.bat` (Windows) + `Start.sh` (Linux/Pi)
- Oder: PyInstaller für plattformspezifische Binaries als Option für Phase 3

**Entscheider:** Georg Hartel (Projektinhaber) + Chief Architect Agent (Bestätigung ausstehend)

---

## ADR-002 – Datenbankmigrationen: Alembic einführen

**Datum:** 2026-06-10
**Status:** Accepted

**Kontext:**
Aktuell werden DB-Migrationen durch inline ALTER TABLE Statements in `main.py` durchgeführt
(in der `_migrate_db()` Funktion). Dies ist nicht wartbar und fehleranfällig.

**Entscheidung:** Alembic als Migrations-Framework einführen

**Begründung:**
- Industrie-Standard für SQLAlchemy/Python
- Automatische Schema-Versionierung
- Rollback möglich
- Open Source, keine Lizenzkosten

**Konsequenzen:**
- `_migrate_db()` in main.py entfernen
- Alembic zu requirements.txt hinzufügen
- Initiale Migration aus bestehendem Schema erstellen

**Entscheider:** Chief Architect Agent

---

## ADR-003 – Frontend-Technologie: React/TypeScript sofort (kein HTMX-Übergang)

**Datum:** 2026-06-10
**Status:** ✅ Accepted (Georg Hartel, 2026-06-10)

**Kontext:**
Ursprüngliche Planung: HTMX/Jinja2 als Übergangs-UI, später React-Migration.
Entscheidung durch Projektinhaber: React/TypeScript sofort, kein HTMX-Übergang.

**Entscheidung:** React/TypeScript als Frontend von Beginn an (Phase 2)

- Kein weiterer Ausbau der HTMX/Jinja2-Templates
- React/TypeScript SPA als neues Frontend
- FastAPI Backend stellt REST-API bereit (`/api/v1/`)
- HTMX-MVP bleibt bis React-Frontend fertig (read-only, keine neuen Features)

**Begründung:**
- Direkter Weg zur Zielarchitektur (kein doppelter Aufwand)
- Office-ähnliche UI (REQ-0104: CTRL+C/V/Z etc.) ist in React deutlich einfacher zu implementieren
- Zweispaltige Ansicht (REQ-0101) mit Drag&Drop, Tabellen, Kontextmenüs → React-Ökosystem
- AG Grid oder TanStack Table für die Testfalltabelle

**Konsequenzen:**
- Phase 2 Sprint 1: React-Projekt aufsetzen (Vite + TypeScript)
- HTMX-Templates werden **nicht** weiter ausgebaut
- API muss sauber versioniert sein (`/api/v1/`) – wird in Phase 1 vorbereitet
- CORS für React-Dev-Server konfigurieren
- Web Research Agent: Recherche React Data Grid Bibliotheken (WR-002)

**Entscheider:** Georg Hartel (Projektinhaber)

---

## ADR-004 – Archivierung: src/backend/ deaktivieren

**Datum:** 2026-06-10
**Status:** Accepted

**Kontext:**
`src/backend/` ist ein paralleler Prototyp (GeTeCaDe) mit eigener DB, eigenem Backend und eigenen
Services. Er wird von der Haupt-App nicht verwendet und verursacht Verwirrung.

**Entscheidung:** `src/backend/` in `archive/2026-06-10/backend-getecade/` verschieben

**Begründung:**
- Keine aktive Nutzung
- Laut SYSTEM_v1.0.md §11: Dateien werden niemals gelöscht, sondern archiviert
- Reduziert kognitive Last für neue Entwickler

**Konsequenzen:**
- archive-log.md aktualisieren
- Keine Funktionalität geht verloren

**Entscheider:** Legacy Code Auditor Agent

---

## ADR-005 – Teststrategie: TDD + pytest-cov verpflichtend

**Datum:** 2026-06-10
**Status:** Accepted

**Kontext:**
Aktuell gibt es keine Coverage-Messung. Die TDD-Pflicht aus SYSTEM_v1.0.md §4 ist nicht
nachweisbar durchgesetzt. Coverage-Ziele (100%) sind nicht messbar.

**Entscheidung:** pytest-cov ab sofort Pflichtbestandteil; alle neuen Features nach TDD

**Begründung:**
- Ziele aus SYSTEM_v1.0.md §5 (100% Statement, Branch Coverage) sind nur mit pytest-cov messbar
- TDD sichert Requirements-Traceability
- Open-Source Tool, keine Kosten

**Konsequenzen:**
- pytest-cov zu requirements.txt hinzufügen
- `.coveragerc` oder `pyproject.toml` konfigurieren
- CI/CD Pipeline misst Coverage und blockiert Merge bei Unterschreitung

**Entscheider:** Senior QA Director Agent

---

## ADR-006 – Open Source Lizenz: MIT

**Datum:** 2026-06-10
**Status:** ✅ Accepted (Georg Hartel, 2026-06-10)

**Kontext:**
SYSTEM_v1.0.md §2 fordert Open-Source-Entwicklung. Eine explizite Lizenz fehlt noch.
Die MIT-Lizenz wurde dem Projektinhaber erklärt (2026-06-10).

**Was MIT bedeutet:**
- Jeder darf G.R.E.A.T. kostenlos nutzen, verändern und weitergeben (auch kommerziell)
- Einzige Pflicht für andere: Copyright-Hinweis "© Georg Hartel" beibehalten
- Georg bleibt Urheber und Autor
- Kein Copyleft: Niemand ist gezwungen, eigene Erweiterungen zu veröffentlichen

**Entscheidung:** MIT-Lizenz (sobald Georg bestätigt)

**Begründung:**
- Einfach, permissiv, Community-freundlich
- Alle Abhängigkeiten (FastAPI, SQLAlchemy, React) MIT-kompatibel
- Raspberry Pi Community erwartet permissive Lizenzen

**Konsequenzen (nach Bestätigung):**
- `LICENSE`-Datei im Repository anlegen
- README.md mit Lizenzhinweis ergänzen

**Entscheider:** Georg Haupt (bestätigt 2026-06-10)

---

## ADR-007 – Web Research Agent: Internet-Recherche für Projektentscheidungen

**Datum:** 2026-06-10
**Status:** Accepted

**Kontext:**
Für Architektur- und Technologieentscheidungen (z.B. Best Practices für Kombinatorik-Algorithmen,
React-Komponenten-Bibliotheken, ISTQB-konforme Terminologie) wird ein Agent benötigt, der
aktuelle Informationen aus dem Internet beschafft.

**Entscheidung:** Web Research Agent als eigenständigen Agenten definieren

**Begründung:**
- Wissen des Basis-Modells kann veraltet sein
- Aktueller Stand von Libraries, Standards und Best Practices ist entscheidungsrelevant
- Kein Vendor-Lock-In (Standard Web-Search)

**Konsequenzen:**
- `.github/agents/great-web-research.agent.md` und `.github/prompts/great-web-research.prompt.md` als aktive Customizations definiert
- Agent wird bei Technologiefragen, Best-Practice-Anfragen und Standard-Recherchen aktiviert

**Entscheider:** Program Manager Agent

---

## ADR-008 – Frontend-Architektur: React/TypeScript mit Vite

**Datum:** 2026-06-24
**Status:** Accepted

**Kontext:**
Phase 2 erfordert ein modernes, interaktives Frontend. Die bisherige HTMX/Jinja2-Loesung
ist fuer einfache CRUD-Operationen ausreichend, skaliert aber nicht fuer:
- Komplexe Zustandsverwaltung (Baumansicht, Live-Updates)
- Office-artige Shortcuts (CTRL+C/V/Z)
- Drag & Drop mit visueller Rueckmeldung
- Komponentenbasierte Wiederverwendung

**Entscheidung:** React 18 + TypeScript + Vite als Frontend-Stack

**Projektstruktur:**
```
frontend/              <- Neues Verzeichnis (Monorepo-Stil)
  src/
    components/        <- React-Komponenten
    api/               <- API-Client (Fetch/Axios gegen FastAPI)
    store/             <- Zustand State Management
    types/             <- TypeScript Interfaces (spiegeln Pydantic-Schemas)
  index.html
  vite.config.ts
  package.json
```

**CSS-Strategie:** Tailwind CSS v3
- Utility-first, kein eigenes CSS-Framework noetig
- Konsistentes Design-System
- Sehr gute React-Integration

**State Management:** Zustand (leichtgewichtig, kein Redux-Overhead)

**HTTP-Client:** Axios (typsicher, interceptors fuer Fehlerbehandlung)

**Testing:** Vitest + React Testing Library

**Windows-First:** Node.js 20 LTS auf Windows. Kein RPi-Support in Phase 2.

**FastAPI-Integration:**
- Vite Dev Server auf Port 5173 (Proxy zu FastAPI Port 8000)
- Production Build: `frontend/dist/` wird von FastAPI als StaticFiles ausgeliefert
- Keine CORS-Probleme durch Proxy-Konfiguration

**Begruendung:**
- React: Groesstes Ecosystem, beste VS Code-Integration (ADR-003 bestaetigt)
- Vite: Schnellster Build-Tool (2-5s statt 30s bei Webpack)
- Tailwind: Kein CSS-Framework-Overhead, sehr wartbar
- Zustand: Minimal, kein Boilerplate, TypeScript-nativ

**Konsequenzen:**
- Node.js 20 LTS muss installiert werden
- `frontend/` Verzeichnis wird angelegt
- FastAPI behaelt alle bestehenden `/api/` Routen (Breaking Change: keine)
- HTMX-Templates bleiben bis Phase 2 Sprint 4 parallel aktiv (Fallback)

**Entscheider:** Chief Architect + Program Manager
**Bestaetigt von:** Georg Haupt (2026-06-24)

---

## ADR-009 | Dezimal.js für numerische Präzision in BVA (2026-07-01)

**Status:** Accepted

**Kontext:**
BVA-Algorithmus benötigt exakte numerische Berechnungen für Grenzwert-Testfälle. Beispiel: Min=5, Max=100, Points=3 sollen exakt [5, 52.5, 100] ergeben, nicht [5, 52.500000001, 99.9999999] durch Floatingpoint-Fehler.

**Entscheidung:**
Dezimal.js-Bibliothek wird eingesetzt (Python + Frontend) für numerisch exakte Grenzwert-Berechnungen.

**Begründung:**
- ✅ Exakte Dezimalzahl-Arithmetik (0.1 + 0.2 = 0.3 exakt)
- ✅ Industriestandard für finanzielle/wissenschaftliche Berechnungen
- ✅ Verhindert Edge Cases bei Grenzwert-Generierung
- ✅ Minimal performance impact (Grenzwerte sind kleine Zahlenmengen)

**Konsequenzen:**
- Dezimal.js zu Python-requirements.txt + frontend/package.json
- BVA-Dialog + Backend nutzt Dezimal.js
- Unit-Tests mit Dezimalgenauigkeit
- +10KB npm-Paketgröße, +50KB Python-Paketgröße

**Entscheidungsträger:** Tech-Lead (User-Entscheidung Session 5475a8fc, 2026-07-01)

**Abhängigkeiten:** REQ-3042, REQ-3041 (BVA-Dialog)

---

## ADR-010 | BVA Min/Max Auto-Prefill: Explizite Eingabe statt Auto-Detect (2026-07-01)

**Status:** Accepted

**Kontext:**
BVA-Dialog muss Min/Max-Eingabe-Strategie definieren: Automatisch aus Kategorie-Metadaten vorbelegen oder User manuell eingeben lassen?

**Entscheidung:**
Leere Input-Felder (Option A): User füllt Min/Max manuell bei jeder BVA-Nutzung.

**Begründung:**
- ✅ **Explizit > Implizit** (Zen of Python) – versteckte Annahmen vermeiden
- ✅ User hat volle Kontrolle über Grenzwert-Definition
- ✅ Fehlertoleranz: User ist responsible für Min/Max-Korrektheit
- ✅ Vereinfachte UI (keine Auto-Prefill-Logik nötig)
- ✅ Kategorie-Metadaten optional (nicht zwingend erforderlich)

**Alternativen (abgelehnt):**
- Option B (Auto-Prefill): Risiko versteckter Grenzwert-Annahmen
- Option C (Hybrid): Zu komplex

**Konsequenzen:**
- BVA-Dialog zeigt leere Min/Max-Felder
- User muss jedes Mal Min/Max eingeben
- Kategorien brauchen keine @min/@max Metadaten
- Fokus auf Fehlerbehandlung (Min > Max, etc.)

**Entscheidungsträger:** Tech-Lead (User-Entscheidung Session 5475a8fc, 2026-07-01)

**Abhängigkeiten:** REQ-3043, REQ-3041 (BVA-Dialog)
