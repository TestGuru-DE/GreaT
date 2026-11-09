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

### ADR-011: Theme-System-Ansatz
- **Datum:** 2026-07-01
- **Status:** ENTSCHIEDEN
- **Entscheidung:** CSS-Variablen + Tailwind Dark Mode
- **Begründung:** Einfach, performant (~0KB Overhead), kein zusätzliches Tooling nötig. Tailwind-`dark:`-Klassen + CSS-Custom-Properties für Theme-Werte. Theme-Klasse auf `<html>`-Element, LocalStorage-Persistenz.
- **Alternativen verworfen:** Styled-Components (+50KB, Migration nötig), reine Tailwind-Config (schwer wartbar bei 5 Themes)

---

## ADR-012 – Multi-User-Konfliktstrategie: HYBRID (Optimistic Concurrency + Stale-Warning)

**Datum:** 2026-09-01
**Status:** ✅ Accepted

**Kontext:**
Sprint 10 hat "Multi-User-Analyse" als Research-Auftrag ergeben (RISK Score 16,
eskalationspflichtig, siehe project-assessment.md Sprint-10-Abschnitt). Offene Frage:
Volle Realtime-Kollaboration (WebSocket/SSE, Live-Cursor, CRDT/OT) vs. einfacherer
Zwischenschritt für Teams bis 10 Personen.

**Entscheidung:** HYBRID-Ansatz als Vorstufe zu echter Realtime-Kollaboration:
- **Optimistic Concurrency Control**: Versionsfeld pro Entität (Projekt/Kategorie/Wert/Testfall),
  Konflikt wird erst beim Speichern erkannt (409 Conflict), keine Sperren beim Lesen/Öffnen
- **Stale-Data-Warning**: Nutzer wird im Konfliktfall aktiv informiert und entscheidet
  (Neu laden vs. bewusst überschreiben) – kein stilles Überschreiben
- **Explizit KEINE** Realtime-Kollaboration in Sprint 11–13 (kein WebSocket-Live-Editing,
  kein Presence/Live-Cursor, kein CRDT/OT)

**Begründung:**
- Team-Größe bis 10 Personen macht seltene, statt permanente Kollisionen wahrscheinlich –
  voller Realtime-Aufwand steht in keinem Verhältnis zum Nutzen dieser Ausbaustufe
- Optimistic Concurrency ist mit bestehendem REST/FastAPI-Stack ohne neue Infrastruktur
  (kein WebSocket-Server, kein zusätzlicher State-Sync-Mechanismus) umsetzbar
- Reduziert Sicherheits- und Architekturrisiko: Auth (RISK-S-001, Score 20) muss ohnehin
  zuerst stehen; Realtime-Kollaboration hätte zusätzliche Angriffsfläche geschaffen
- Nutzer behält Kontrolle über Konfliktauflösung – vermeidet Datenverlust durch Auto-Merge-Fehler
- Realtime-Kollaboration bleibt als spätere Ausbaustufe im Themenspeicher/Backlog auswählbar,
  sobald Team-Größe/Anforderungen dies rechtfertigen

**Konsequenzen:**
- REQ-4021 (Optimistic Concurrency) und REQ-4022 (Stale-Data-Warning) werden in
  requirements_v1.1.md (EPIC-18) als neue Requirements geführt
- Kein WebSocket-/SSE-Server wird in Sprint 11–13 aufgebaut
- Klare Kommunikation an Stakeholder: "Multi-User" bedeutet in dieser Stufe kollisionssichere
  Zusammenarbeit, keine Echtzeit-Ansicht fremder Änderungen
- Chief-Architect-Eskalation aus Sprint 10 (Multi-User-Architekturentscheidung, Score 16) ist
  hiermit fachlich/Scope-seitig aufgelöst; technische Detailfreigabe (ADR-007 DB-Strategie,
  Auth-Schema-Review) bleibt gesondert erforderlich vor Sprint-11-Start

**Entscheider:** Program Manager Agent (Scope/Priorität), in Abstimmung mit GREAT Chief Architect
(technische Machbarkeit der Eskalation aus Sprint 10)
**Abhängigkeiten:** REQ-4001, REQ-4006, REQ-4021, REQ-4022, RISK-S-001, RISK-T-008 (neu)

---

## REQ-3051: API-Contract fuer Risikoabdeckungs-Gesamtprozentsatz nachgezogen

**Status:** Umgesetzt (Developer, TDD)

**Kontext:**
REQ-3051 (Prozentuale Risikoabdeckung pro Generierung) war laut requirements_v1.1.md und
project-assessment.md bereits als DONE/TESTED gefuehrt. Backend-Berechnung
(`calculate_generation_risk_summary` in `src/app/services.py`) und Frontend-Badge
(gruen/gelb/rot in `TestCasePanel.tsx`) waren funktional bereits vorhanden und die
reinen Unit-Tests der Berechnungsfunktion (`tests/test_risk_summary.py`) gruen.

**Gefundene Luecke (TDD RED):**
- Der Endpunkt `GET /api/generations/{gid}/testcases` lieferte `risk_summary` zwar
  korrekt im Response-Body, war aber ohne `response_model` deklariert. Das
  vorbereitete Schema `schemas.TestcasesResponse`/`schemas.RiskSummary` war im
  OpenAPI-Dokument nicht sichtbar (leeres Response-Schema) – Bruch mit dem sonst
  durchgaengigen API-Muster (alle anderen Endpunkte nutzen `response_model`).
- Keine Integrationstests auf API-Ebene fuer den Gesamtprozentsatz (nur Unit-Tests der
  reinen Berechnungsfunktion).
- Kein Test fuer die Farbwahl des Badges (gruen >=80 %, gelb 50-79 %, rot <50 %) und
  keine Store-Tests, die belegen, dass `riskSummary` nach `generate()`/
  `loadGeneration()` aus der API uebernommen wird.

**Massnahme:**
- `response_model=schemas.TestcasesResponse` am Endpunkt ergaenzt (1 Zeile,
  bestehendes Muster wiederverwendet, keine Verhaltensaenderung der Response-Struktur).
- Neue Tests: `tests/test_req3051_risk_summary_api.py` (API-Contract + Gesamtprozentsatz),
  Ergaenzungen in `frontend/src/store/__tests__/generateStore.test.ts` (riskSummary-Uebernahme)
  und `frontend/src/components/__tests__/TestCasePanel.test.tsx` (Badge-Farben/Grenzwerte).

**Ergebnis:** REQ-3051 bleibt DONE/TESTED, jetzt mit vollstaendiger Test- und API-Vertragsabdeckung.
**Entscheider:** GREAT Senior Developer Agent
**Abhaengigkeiten:** REQ-3050

---

## REQ-3003 / REQ-3004: Testabdeckung fuer Regeleditor in RulesPanel nachgezogen (Todo p3s2-frontend-rules-editor)

**Status:** Umgesetzt (Developer, TDD)

**Kontext:**
Todo `p3s2-frontend-rules-editor` verlangte den Regeleditor oberhalb der Regelanzeige im
`RulesPanel` (Formular mit Typ-/Kategorie-/Wert-Dropdowns, direktes Speichern, Konflikt-Warnung).
Bei Pruefung war die Implementierung in `frontend/src/components/RulesPanel.tsx` bereits
vollstaendig vorhanden (Kommentarkopf referenziert REQ-1216 + REQ-3003 + REQ-3004), jedoch
**ohne jegliche Tests** – es existierte keine `RulesPanel.test.tsx`.

**Gefundene Luecke (TDD):**
- Keine automatisierten Tests fuer das Regelformular (Typ-/Kategorie-/Wert-Dropdowns), das
  direkte Speichern neuer Regeln sowie die Konflikt-Warnung samt Hervorhebung der betroffenen
  Regel in der Regelanzeige.

**Massnahme:**
- Neue Testdatei `frontend/src/components/__tests__/RulesPanel.test.tsx` (4 Tests, TDD-Stil
  analog zu `CategoryTree.test.tsx`, `rulesApi`/`categoriesApi` gemockt):
  - REQ-3003: Formular zeigt Typ-, Kategorie- und Wert-Dropdowns oberhalb der Regelanzeige.
  - REQ-3003: Neue Regel wird direkt ueber `rulesApi.create` gespeichert und erscheint sofort
    in der Regelanzeige.
  - REQ-3004: Konflikt-Antwort (`conflict_with`) fuehrt zu Warnmeldung „Regelwiderspruch mit
    Regel #N" und visueller Hervorhebung (Amber) der betroffenen Regel in der Liste; Speichern
    bleibt trotzdem erfolgreich (kein Hard-Block).
  - REQ-3004: Widerspruchsfreie Regel zeigt Erfolgsmeldung ohne Hervorhebung (Abgrenzung/Regression).
- Keine Aenderung an Produktivcode noetig – Implementierung erfuellte bereits alle
  Akzeptanzkriterien; erste Testlaeufe scheiterten nur an mehrdeutigen Testabfragen
  (Options-Text vs. Anzeige-Text), nicht an fachlicher Logik. Nach Praezisierung der Queries
  (`within(list)`) sind alle 4 Tests gruen.

**Ergebnis:** Frontend-Suite 26/26 Testdateien, 166 Tests gruen (2 vorbestehend uebersprungen).
Backend-Regression `tests/test_phase3_sprint2.py` (14 Tests) weiterhin gruen. REQ-3003/REQ-3004
sind funktional und testseitig abgesichert; Status in `requirements_v1.1.md` sollte bei
naechster QA-Freigabe von „Planned" auf „DONE/TESTED" aktualisiert werden.
**Entscheider:** GREAT Senior Developer Agent
**Abhaengigkeiten:** REQ-3003, REQ-3004

---

## REQ-3045: "Normal"-Theme zu "Normal (HSV)" umbenannt (Sprint 11, Theme-Vorgabe Nutzer)

**Status:** Umgesetzt (Developer, TDD)

**Kontext:**
Sprint-11-Vorgabe: Bestehende Theme-Varianten im Settings-/Appearance-Bereich sollen nach
neuen Vorgaben angepasst werden, insbesondere das Standard-Theme "Normal" (REQ-3045) auf
"Normal (HSV)" mit den Vereinsfarben des Hamburger SV umgestellt werden. Kein Refactor des
Theme-Systems (`frontend/src/lib/theme.ts`), nur CSS-Token- und Label-Anpassung.

**TDD-Vorgehen (RED → GREEN):**
- Neuer Test `frontend/src/lib/__tests__/normal-hsv-theme.test.ts` liest `index.css` als
  Rohtext (Source of Truth der Theme-Tokens) und pruefte vor der Implementierung erwartungsgemaess
  rot: fehlender REQ-3045/HSV-Dokumentationskommentar, fehlende Tokens `--color-accent: #0f4c81`,
  `--color-accent-hover: #0b3860`, `--color-accent-text: #ffffff` im `:root`-Block sowie
  WCAG-AA-Kontrast (Weiss auf HSV-Blau).
- Ergaenzender Test in `frontend/src/components/__tests__/ThemeSwitcher.test.tsx` pruefte vor
  der Implementierung erwartungsgemaess rot auf das Label "Normal (HSV)".
- Minimal-Implementierung: `--color-accent`/`--color-accent-hover` im `:root`-Block von
  `frontend/src/index.css` auf HSV-Blau (#0f4c81 / hover #0b3860) gesetzt, `--color-accent-text`
  (Weiss, #ffffff) neu ergaenzt (Konsistenz mit den anderen Theme-Bloecken, die dieses Token
  bereits nutzen), Label in `frontend/src/components/ThemeSwitcher.tsx` von "☀️ Normal" auf
  "☀️ Normal (HSV)" geaendert. Kein Eingriff in `theme.ts` (Wert `'normal'` bleibt als
  ThemeName/localStorage-Key unveraendert, keine Migration noetig).

**Annahme/Risiko:**
- Der exakte offizielle Hex-Code der HSV-Vereinsfarbe war nicht vorgegeben; es wurde ein
  gaengiger, oeffentlich referenzierter Blauton (#0f4c81) verwendet. Empfehlung: fachliche
  Bestaetigung des exakten Marken-/Pantone-Werts durch Stakeholder vor Public-Release,
  Aenderung ist ansonsten ein Ein-Zeilen-Wert-Swap ohne Strukturaenderung.
- Bestehender Kontrast-Testfile `theme-contrast.test.ts` enthaelt fuer "Light"/Normal einen
  Text/Hintergrund-Eintrag mit `#1e293b` statt dem tatsaechlichen `--color-text-primary`
  (`#111827`) aus `index.css` – vorbestehende Abweichung, nicht Teil dieses Slices, nur
  dokumentiert.

**Ergebnis:** Frontend-Suite 27/27 Testdateien, 172 Tests gruen (2 vorbestehend uebersprungen),
`tsc --noEmit` ohne Fehler. REQ-3045 bleibt DONE/TESTED, jetzt mit HSV-Farbvorgabe umgesetzt
und testseitig gegen Regressionen abgesichert.

**Entscheider:** GREAT Senior Developer Agent
**Abhaengigkeiten:** REQ-3045, REQ-3046..REQ-3049 (unveraendert), REQ-3062 (unveraendert)

---

## ADR-014 – DB-Schema-Erweiterung fuer Entscheidungstabelle (EPIC-20)

**Datum:** 2026-10-05
**Status:** Proposed

**Kontext:**
EPIC-20 (Entscheidungstabelle / Decision Table Testing) wird in Phase 4, Sprint 14-17
implementiert. Die fachliche Grundlage ist ISTQB CTFL v4.0 FL-4.2.3 / CTAL-TA 3.2.4
(siehe `documentation/research-decision-table-istqb.md`).

Das bestehende DB-Schema (`src/app/models.py`) kennt Kategorien nur als generische
Parameter-Kontainer mit einem booleschen `is_result`-Flag (ADR-012 / Migration a7b8b126c88d).
Fuer Entscheidungstabellen sind drei neue Domänenkonzepte notwendig:

1. **Kategorie-Rollen**: Ursachen (Conditions) vs. Wirkungen (Effects) vs. Standard
2. **Entscheidungstabellen**: Projektgebundene Container fuer Cause-Effect-Modelle
3. **Entscheidungsrules**: Spalten in der Tabelle (jede Spalte = 1 Regel/Testfall)
4. **Constraints**: E, I, O, R, M – logische Beziehungen zwischen Ursachen/Wirkungen

Das bestehende `rules`-Tabelle (Dependency-Regeln) ist ein anderes Domänenkonzept
(Wenn-Dann-Regeln fuer klassische Kombinatorik) und darf nicht mit Decision-Rules
vermischt werden.

**Entscheidung:** Vier neue Tabellen + eine Spalten-Erweiterung, keine Aenderung bestehender
Tabellen-Strukturen (nur additive Erweiterung).

### 1. Erweiterung `categories` – category_type

```python
# src/app/models.py – Erweiterung Category-Modell
from sqlalchemy import Enum

CATEGORY_ROLE = Enum("standard", "cause", "effect", name="category_role_enum")

class Category(Base):
    # ... bestehende Felder ...
    category_type = Column(CATEGORY_ROLE, nullable=False, server_default="standard")
```

**Rueckwaertige Kompatibilität:**
- `server_default="standard"` – alle bestehenden Kategorien werden automatisch als
  `standard` behandelt
- `is_result` bleibt erhalten (nicht deprecated, nicht entfernt) – bestehende Code-Stellen
  in `services.py` und `api_projects.py` die `is_result` lesen/schreiben funktionieren
  unveraendert weiter
- Migration backfillt `category_type` aus `is_result`: `is_result=True` → `effect`,
  `is_result=False` → `standard`
- Langfristig: `is_result` kann als computed property implementiert werden
  (`@property: return self.category_type == "effect"`)

### 2. Neue Tabelle `decision_tables`

```sql
CREATE TABLE decision_tables (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name            VARCHAR(300) NOT NULL,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT 0,
    generated_rules INTEGER NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL
);
CREATE INDEX idx_dt_project ON decision_tables(project_id);
```

**Begründung:** Eine Entscheidungstabelle ist ein projektgebundener Container.
`is_active` erlaubt genau eine aktive Tabelle pro Projekt (der Rest bleibt als
Versionierung/Archiv). `generated_rules` speichert die aktuelle Spaltenanzahl
(2^n nach Constraint-Filterung) fuer UI-Feedback.

### 3. Neue Tabelle `decision_rules`

```sql
CREATE TABLE decision_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_table_id INTEGER NOT NULL REFERENCES decision_tables(id) ON DELETE CASCADE,
    rule_number     INTEGER NOT NULL,          -- R1, R2, R3, ...
    is_collapsed    BOOLEAN NOT NULL DEFAULT 0, -- REQ-5013: Collapsing-Marker
    created_at      DATETIME NOT NULL,
    UNIQUE(decision_table_id, rule_number)
);
CREATE INDEX idx_dr_table ON decision_rules(decision_table_id);
```

**Begründung:** Jede Spalte der Entscheidungstabelle ist eine Regel. `rule_number`
garantiert stabile Sortierung. `is_collapsed` markiert Regeln die durch Collapsing
(REQ-5013) entstanden sind (Don't Care-Werte enthalten).

### 4. Neue Tabelle `decision_rule_entries`

```sql
CREATE TABLE decision_rule_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_rule_id INTEGER NOT NULL REFERENCES decision_rules(id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    entry_value     VARCHAR(10) NOT NULL DEFAULT '',  -- 'Y', 'N', '-', 'X', ''
    created_at      DATETIME NOT NULL,
    UNIQUE(decision_rule_id, category_id)
);
CREATE INDEX idx_dre_rule ON decision_rule_entries(decision_rule_id);
CREATE INDEX idx_dre_category ON decision_rule_entries(category_id);
```

**Begründung:** Jede Zelle in der Tabelle ist ein Entry. `entry_value` als freier
String (nicht Enum) – erlaubt Y/N/- (Ursachen), X/- (Wirkungen binär),
oder Freitext (REQ-5016: Wirkungen als Text). Empty string `''` = nicht gefuellt
(initialer Zustand fuer Wirkungen laut Nutzerentscheidung).

**Wichtig:** Die Category-Rolle (`cause` vs `effect`) bestimmt den Entry-Typ:
- `category_type='cause'` → Entry-Werte: Y, N, - (Don't Care)
- `category_type='effect'` → Entry-Werte: X, -, oder Freitext

### 5. Neue Tabelle `decision_constraints`

```sql
CREATE TABLE decision_constraints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_table_id INTEGER NOT NULL REFERENCES decision_tables(id) ON DELETE CASCADE,
    constraint_type VARCHAR(1) NOT NULL,          -- 'E', 'I', 'O', 'R', 'M'
    description     VARCHAR(500),                  -- menschenlesbare Beschreibung
    created_at      DATETIME NOT NULL
);
CREATE INDEX idx_dc_table ON decision_constraints(decision_table_id);

CREATE TABLE decision_constraint_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    constraint_id   INTEGER NOT NULL REFERENCES decision_constraints(id) ON DELETE CASCADE,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,   -- fuer R/M: Richtung C1→C2
    UNIQUE(constraint_id, category_id)
);
CREATE INDEX idx_dcc_constraint ON decision_constraint_categories(constraint_id);
```

**Begründung:** Constraints sind projekt- und tabelle-spezifisch. Die 1:N-Beziehung
zwischen `decision_constraints` und `decision_constraint_categories` via Junction-Table
unterstuetzt alle 5 Constraint-Typen:

| Constraint | Kategorien-Anzahl | Bedeutung sort_order |
|---|---|---|
| E (Exclusive) | ≥2 Ursachen | Reihenfolge irrelevant |
| I (Inclusive) | ≥2 Ursachen | Reihenfolge irrelevant |
| O (One-and-Only-One) | ≥2 Ursachen | Reihenfolge irrelevant |
| R (Requires) | genau 2 Ursachen | 0=Quelle (C1), 1=Ziel (C2) |
| M (Mask) | genau 2 Wirkungen | 0=Quelle (E1), 1=Ziel (E2) |

### SQLAlchemy-Modelle (Pseudo-Code)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

CATEGORY_ROLE = Enum("standard", "cause", "effect", name="category_role_enum")
CONSTRAINT_TYPES = Enum("E", "I", "O", "R", "M", name="constraint_type_enum")
ENTRY_VALUES = {"Y", "N", "-", "X", ""}  # Validierung in Service-Schicht

class DecisionTable(Base):
    __tablename__ = "decision_tables"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    generated_rules = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    project = relationship("Project", back_populates="decision_tables")
    rules = relationship("DecisionRule", back_populates="decision_table",
                         cascade="all, delete-orphan", order_by="DecisionRule.rule_number")
    constraints = relationship("DecisionConstraint", back_populates="decision_table",
                               cascade="all, delete-orphan")

class DecisionRule(Base):
    __tablename__ = "decision_rules"
    id = Column(Integer, primary_key=True)
    decision_table_id = Column(Integer, ForeignKey("decision_tables.id", ondelete="CASCADE"),
                               nullable=False)
    rule_number = Column(Integer, nullable=False)
    is_collapsed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (UniqueConstraint("decision_table_id", "rule_number"),)
    decision_table = relationship("DecisionTable", back_populates="rules")
    entries = relationship("DecisionRuleEntry", back_populates="rule",
                           cascade="all, delete-orphan")

class DecisionRuleEntry(Base):
    __tablename__ = "decision_rule_entries"
    id = Column(Integer, primary_key=True)
    decision_rule_id = Column(Integer, ForeignKey("decision_rules.id", ondelete="CASCADE"),
                              nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    entry_value = Column(String(10), nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (UniqueConstraint("decision_rule_id", "category_id"),)
    rule = relationship("DecisionRule", back_populates="entries")
    category = relationship("Category")

class DecisionConstraint(Base):
    __tablename__ = "decision_constraints"
    id = Column(Integer, primary_key=True)
    decision_table_id = Column(Integer, ForeignKey("decision_tables.id", ondelete="CASCADE"),
                               nullable=False)
    constraint_type = Column(String(1), nullable=False)  # E, I, O, R, M
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    decision_table = relationship("DecisionTable", back_populates="constraints")
    categories = relationship("DecisionConstraintCategory", back_populates="constraint",
                              cascade="all, delete-orphan", order_by="DecisionConstraintCategory.sort_order")

class DecisionConstraintCategory(Base):
    __tablename__ = "decision_constraint_categories"
    id = Column(Integer, primary_key=True)
    constraint_id = Column(Integer, ForeignKey("decision_constraints.id", ondelete="CASCADE"),
                           nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("constraint_id", "category_id"),)
    constraint = relationship("DecisionConstraint", back_populates="categories")
    category = relationship("Category")
```

### Migration-Schritte (Alembic)

**Revision:** `xxx_epic20_decision_table_schema`
**Revises:** `a7b8b126c88d` (letzte Migration: add_is_result_to_category)

```python
def upgrade() -> None:
    # Step 1: category_type Spalte zu categories hinzufuegen
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('category_type',
                      sa.Enum('standard', 'cause', 'effect', name='category_role_enum'),
                      nullable=False, server_default='standard'))

    # Step 2: Bestehende Daten backfillen (is_result -> category_type)
    # is_result=True → effect, is_result=False → standard
    op.execute("""
        UPDATE categories SET category_type = 'effect'
        WHERE is_result = 1 AND category_type = 'standard'
    """)

    # Step 3: Neue Tabellen erstellen
    op.create_table('decision_tables',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer,
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('generated_rules', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Index('idx_dt_project', 'project_id')
    )

    op.create_table('decision_rules',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('decision_table_id', sa.Integer,
                  sa.ForeignKey('decision_tables.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_number', sa.Integer, nullable=False),
        sa.Column('is_collapsed', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('decision_table_id', 'rule_number')
    )
    op.create_index('idx_dr_table', 'decision_rules', ['decision_table_id'])

    op.create_table('decision_rule_entries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('decision_rule_id', sa.Integer,
                  sa.ForeignKey('decision_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer,
                  sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_value', sa.String(10), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('decision_rule_id', 'category_id')
    )
    op.create_index('idx_dre_rule', 'decision_rule_entries', ['decision_rule_id'])
    op.create_index('idx_dre_category', 'decision_rule_entries', ['category_id'])

    op.create_table('decision_constraints',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('decision_table_id', sa.Integer,
                  sa.ForeignKey('decision_tables.id', ondelete='CASCADE'), nullable=False),
        sa.Column('constraint_type', sa.String(1), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Index('idx_dc_table', 'decision_table_id')
    )

    op.create_table('decision_constraint_categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('constraint_id', sa.Integer,
                  sa.ForeignKey('decision_constraints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer,
                  sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.UniqueConstraint('constraint_id', 'category_id')
    )
    op.create_index('idx_dcc_constraint', 'decision_constraint_categories', ['constraint_id'])


def downgrade() -> None:
    # Reverse order
    op.drop_index('idx_dcc_constraint', table_name='decision_constraint_categories')
    op.drop_table('decision_constraint_categories')
    op.drop_index('idx_dc_table', table_name='decision_constraints')
    op.drop_table('decision_constraints')
    op.drop_index('idx_dre_category', table_name='decision_rule_entries')
    op.drop_index('idx_dre_rule', table_name='decision_rule_entries')
    op.drop_table('decision_rule_entries')
    op.drop_index('idx_dr_table', table_name='decision_rules')
    op.drop_table('decision_rules')
    op.drop_index('idx_dt_project', table_name='decision_tables')
    op.drop_table('decision_tables')

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_column('category_type')

    # Enum-Type bereinigen (SQLite benoetigt explizites DROP)
    op.execute("DROP TYPE IF EXISTS category_role_enum")
```

**Begründung der Migration-Strategie:**
- `batch_alter_table` fuer SQLite-Kompatibilität (SQLite unterstuetzt ALTER TABLE begrenzt)
- Backfill vor Tabellen-Erstellung: Kategorien muessen bereits den korrekten Typ haben,
  bevor Decision-Tables darauf referenzieren koennen
- `server_default` auf allen neuen Spalten: keine NOT NULL Verletzung bei leeren Tabellen

### Backward-Compatibility-Garantien

| Aspekt | Garantie |
|---|---|
| **Bestehende Projekte** | Keine Aenderung – `category_type='standard'` default, `is_result` unveraendert |
| **Bestehende API-Endpunkte** | Keine Breaking Changes – neue Tabellen sind neue Endpunkte (`/api/v1/decision-tables/`) |
| **Bestehende Kombinatorik** | Unveraendert – `rules`-Tabelle bleibt fuer Dependency-Regeln; Decision-Rules sind separat |
| **is_result-Feld** | Bleibt erhalten, wird nicht deprecated; Migration backfillt category_type daraus |
| **Datenbank-Rollback** | Vollstaendiger downgrade moeglich (alle neuen Tabellen + Spalte entfernbar) |
| **SQLite WAL-Mode** | Neue Tabellen profitieren vom bestehenden WAL-Mode (REQ-4006) |
| **Foreign Key Constraints** | CASCADE-Delete auf allen neuen FKs – Orphan-Vermeidung |

### Abgelehnte Alternativen

| Alternative | Grund der Ablehnung |
|---|---|
| **is_result durch category_type ersetzen** | Breaking Change – bestehender Code in `services.py`, `api_projects.py` liest `is_result`; Migration waere riskant |
| **Decision-Rules in bestehender `rules`-Tabelle** | Konzeptuelle Vermischung – Dependency-Regnen (Wenn-Dann) sind ein anderes Domänenkonzept als Decision-Rules (Ursache→Wirkung-Spalten) |
| **Constraints als JSON-Spalte in decision_tables** | Nicht querybar – Constraints muessen einzeln gelesen/validiert/geaendert werden; relationales Design ist wartbarer |
| **Entry-Werte als Integer-Enum** | Extended Entry (REQ-5015: S/M/L/XL) und Freitext-Wirkungen (REQ-5016) erfordern flexiblen String |
| **Separate Tabellen fuer Cause-Entries und Effect-Entries** | Ueberengineered – eine Tabelle mit category_type-Referenz ist einfacher und querybar |

**Begründung:**
- Additive Erweiterung (keine Aenderung bestehender Tabellen-Strukturen) ist der
  sicherste Migrationsweg und entspricht dem Vorgehen aus ADR-002 (Alembic)
- Die Trennung von `rules` (Dependency) und `decision_rules` (Decision Table) vermeidet
  Domänen-Vermischung und erleichtert die parallele Nutzung beider Features
- Die Junction-Table `decision_constraint_categories` unterstuetzt alle 5 Constraint-Typen
  ohne spezielle Spalten pro Typ – skalierbar fuer zukunftsige Constraint-Erweiterungen
- `entry_value` als String(10) statt Enum: unterstuetzt Boolean (Y/N/-), binär (X/-),
  Extended Entry (S/M/L/XL) und Freitext (REQ-5016) in einem Feld

**Konsequenzen:**
- **REQ-5002** (Kategorie-Typ): `category_type` Spalte in `categories` – implementierbar
- **REQ-5003** (Tabelle-Layout): `decision_tables` + `decision_rules` + `decision_rule_entries`
- **REQ-5005** (Auto-Generierung): Service-Schicht generiert Rules/Entries aus Causes×Effects
- **REQ-5007-5011** (Constraints): `decision_constraints` + `decision_constraint_categories`
- **REQ-5012** (Constraint-Dialog): CRUD-Endpunkte fuer Constraints
- **REQ-5013** (Collapsing): `is_collapsed` Flag + Don't Care in `entry_value`
- **REQ-5014** (Checksum): Berechnung in Service-Schicht (keine DB-Speicherung)
- **REQ-5015** (Extended Entry): `entry_value` als String unterstuetzt beliebige Werte
- **REQ-5016** (Wirkungen als Text): `entry_value` als String unterstuetzt Freitext
- **REQ-5017** (Don't Care): `-` in `entry_value`
- **REQ-5018** (Graph): Kann aus Constraints + Categories generiert werden (Frontend)
- **REQ-5019** (Widerspruchserkennung): Service-Schicht validiert Rules
- **REQ-5020** (Vollstaendigkeit): Service-Schicht prueft Coverage
- **REQ-5021** (Priorisierung): Optionaler `priority`-Index in `decision_rule_entries`
  (kann in nachfolgender Migration ergaenzt werden)

**Entscheider:** GREAT Chief Architect Agent
**Abhaengigkeiten:** EPIC-20 (REQ-5000-5021), ADR-001 (Python/FastAPI), ADR-002 (Alembic),
ADR-012 (is_result in categories), REQ-4006 (Multi-User/WAL-Mode),
REQ-4018 (Max-Testfaelle-Limit als Generierungs-Bremse)

---

## ADR-015 – DB-Schema-Erweiterung fuer EPIC-18 (Multi-User)

**Datum:** 2026-10-05
**Status:** Proposed

**Kontext:**
EPIC-18 (Multi-User-Nutzung, Teams bis 10 Personen) wird in Phase 4, Sprint 11–13
implementiert. Sieben Requirements (REQ-4001, 4006, 4020, 4021, 4022, 4023, 4024)
erfordern eine umfassende Erweiterung des bestehenden DB-Schemas.

Das aktuelle Schema (`src/app/models.py`) kennt keine Benutzer, keine Rollen,
keine Projekt-Mitgliedschaften, keine Versionsfelder und keine Audit-Felder.
Alle sieben Tabellen (projects, categories, values, generations, testcases,
testcase_values, rules sowie dataclasses, dataclass_values, data_nodes,
data_node_values) sind fuer Single-User-Betrieb ausgelegt.

ADR-012 (HYBRID-Ansatz) hat die Konfliktstrategie festgelegt:
Optimistic Concurrency + Stale-Data-Warning. Diese ADR definiert die
konkrete Datenbankschema-Implementierung fuer EPIC-18.

**Entscheidung:** Additive Schema-Erweiterung mit drei neuen Tabellen und
vier neuen Spalten-Typen auf bestehenden Tabellen. Keine bestehende Tabelle
wird geloescht oder strukturell veraendert (aufer durch additive Spalten).

### 1. Bestehendes Schema (Analyse)

| Tabelle | Felder (relevant) | FK-Beziehungen |
|---|---|---|
| `projects` | id, name, created_at, updated_at | – |
| `categories` | id, project_id, name, order_index, is_result, created_at, updated_at | → projects |
| `values` | id, category_id, value, risk_weight, allowed, vtype, order_index, is_default, created_at, updated_at | → categories |
| `generations` | id, project_id, strategy, name, created_at, updated_at, coverage_meta | → projects |
| `testcases` | id, generation_id, name | → generations |
| `testcase_values` | id, testcase_id, category_id, value | → testcases, categories |
| `rules` | id, project_id, type, if_category_id, if_value, then_category_id, then_value, then_values_json | → projects, categories |
| `dataclasses` | id, name, value_type, description, is_system, created_at | – |
| `dataclass_values` | id, dataclass_id, value, sort_order, created_at | → dataclasses |
| `data_nodes` | id, name, parent_id, is_system, source, sort_order, created_at | → data_nodes (self) |
| `data_node_values` | id, node_id, value, sort_order, created_at | → data_nodes |

**Luecken fuer EPIC-18:**
- Keine Benutzer-Tabelle → kein Login moeglich (REQ-4001)
- Keine Rollen-Tabelle → keine Rechtepruefung moeglich (REQ-4020)
- Keine Projekt-Mitgliedschaften → kein Projekt-Sharing moeglich (REQ-4023)
- Keine Versionsfelder → keine Optimistic Concurrency moeglich (REQ-4021)
- Keine Audit-Felder → kein "wer hat geaendert" moeglich (REQ-4024)

### 2. Neue Tabellen

#### 2.1 `users` – Benutzer (REQ-4001, REQ-4020)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt/argon2 Hash

    # REQ-4020: Globale Rolle (Admin/Editor/Viewer)
    role = Column(String(20), nullable=False, default="editor", server_default="editor")
    # Moegliche Werte: "admin", "editor", "viewer"

    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    is_first_admin = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # REQ-4023: Projekt-Mitgliedschaften (1:N)
    project_memberships = relationship("ProjectMembership",
                                        back_populates="user",
                                        cascade="all, delete-orphan")
```

**Entscheidungen:**
- `username` statt `email`: EPIC-18 ist fuer lokale Teams konzipiert, keine E-Mail-Verifizierung
- `password_hash` als String(255): bcrypt-Haeshes sind typisch 60 Zeichen, argon2 bis ~120; 255 bietet Puffer
- `role` als String-Enum (nicht separate Tabelle): Bei nur 3 Rollen (Admin/Editor/Viewer) ist
  eine separate Tabelle mit Junction-Table Overkill. String-Spalte ist einfacher, schneller,
  und fuer ≤10 Benutzer完全没有 Performance-Probleme.
- `is_first_admin`: Boolean-Flag fuer Bootstrapping. Der erste registrierte User wird automatisch Admin.

#### 2.2 `refresh_tokens` – Token-Invalidierung (REQ-4001)

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
```

**Entscheidungen:**
- Hash des Refresh-Tokens speichern (nicht der Token selbst): Logout kann den Token
  invalidate ohne den Token selbst in der DB zu speichern
- `revoked`-Flag: Ermoglicht explizite Invalidierung (Logout, Security-Events)
- `expires_at`-Index: Ermoglicht effiziente Bereinigung abgelaufener Tokens (cron-job oder lazy cleanup)
- Alternative (abgelehnt): In-Memory-Blacklist → geht bei Server-Neustart verloren;
  bei Teams mit langer Session-Dauer ist DB-gestuetzte Persistenz sicherer

#### 2.3 `project_memberships` – Projekt-Sharing (REQ-4023)

```python
PROJECT_ROLES = ["owner", "editor", "viewer"]

class ProjectMembership(Base):
    __tablename__ = "project_memberships"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="editor", server_default="editor")
    # "owner" = Ersteller des Projekts (kann nicht entfernt werden, kann Rolle delegieren)
    # "editor" = kann Kategorien/Werte/Testfaelle bearbeiten
    # "viewer" = nur lesen

    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    project = relationship("Project")
    user = relationship("User", back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
```

**Entscheidungen:**
- `role` pro Projekt (nicht global): Ein User kann in Projekt A Editor und in Projekt B Viewer sein
- `owner`-Rolle: Der Ersteller eines Projekts ist automatisch Owner. Owner kann andere Owner
  designieren, aber mindestens ein Owner muss immer existieren
- UniqueConstraint `(project_id, user_id)`: Ein User kann nur einmal pro Projekt Mitglied sein
- `invited_by`: Optional, fuer Audit-Zwecke (wer hat wen eingeladen)

**Abgelehnte Alternativen:**

| Alternative | Grund der Ablehnung |
|---|---|
| **Separate `roles`-Tabelle + Junction-Table** | 3 Rollen (Admin/Editor/Viewer) sind statisch; eine Enum-Spalte ist einfacher und performanter. Eine separate Tabelle waere Overengineering fuer ≤10 Benutzer. |
| **Globale Rolle ohne Projekt-Mitgliedschaft** | REQ-4023 verlangt projekt-spezifischen Zugriff. Ein Viewer soll nicht automatisch alle Projekte sehen. |
| **Invitation-Token (E-Mail)** | EPIC-18 ist fuer lokale Teams ohne E-Mail-Infrastruktur. Registrierung erfolgt durch Admin. |

### 3. Neue Spalten auf bestehenden Tabellen

#### 3.1 `version` – Optimistic Concurrency (REQ-4021)

| Tabelle | Spalte | Typ | Default | Index |
|---|---|---|---|---|
| `projects` | `version` | Integer | 0 | – |
| `categories` | `version` | Integer | 0 | – |
| `values` | `version` | Integer | 0 | – |
| `testcases` | `version` | Integer | 0 | – |

**Entscheidung:** `version` als Integer, startet bei 0, wird bei jedem UPDATE um 1 erhoht.
Der Client sendet die aktuelle Version im PUT/PATCH-Request; das Backend vergleicht
und liefert 409 Conflict bei Diskrepanz.

**Abgelehnt:**
- `updated_at` als Concurrency-Token: Nicht granular genug (zwei Updates innerhalb derselben Sekunde)
- UUID-basierte Versioning: Unnoetig komplex fuer Integer-Vergleich

**Nicht betroffen:** `generations`, `testcase_values`, `rules`, `dataclasses`,
`dataclass_values`, `data_nodes`, `data_node_values` – diese werden entweder nur
vom System geschrieben (generations, testcase_values) oder sind Referenzdaten
(dataclasses, data_nodes) ohne Multi-User-Bearbeitung.

#### 3.2 `last_modified_by` + `last_modified_at` – Audit-Trail (REQ-4024)

| Tabelle | `last_modified_by` | `last_modified_at` |
|---|---|---|
| `projects` | Integer (FK → users.id, nullable) | DateTime (nullable) |
| `categories` | Integer (FK → users.id, nullable) | DateTime (nullable) |
| `values` | Integer (FK → users.id, nullable) | DateTime (nullable) |
| `testcases` | Integer (FK → users.id, nullable) | DateTime (nullable) |

**Entscheidung:**
- `nullable=True`: Bestehende Datensatze haben keinen letzten Aenderer (Pre-Migration-Zustand)
- FK mit `ondelete="SET NULL"`: Wenn ein User geloescht wird, bleibt der Audit-Trail erhalten
- `last_modified_at` ist ein separates Feld, nicht identisch mit `updated_at`:
  `updated_at` wird vom ORM automatisch gesetzt (onupdate), `last_modified_at` wird
  explizit zusammen mit `last_modified_by` gesetzt

**Abgelehnt:**
- Vollstaendiges Audit-Log (alle Aenderungen historisieren): REQ-4024 verlangt explizit
  nur "letzten Aenderer", nicht Historie. Vollstaendiger Audit-Trail ist ein separates
  Requirement (REQ-4003, Phase 5+).
- `updated_at` wiederverwenden statt neues Feld: `updated_at` wird bereits vom ORM
  automatisch verwaltet; eine Kollision zwischen ORM-Auto-Update und explizitem
  Audit-Setzen waere fehleranfaellig.

### 4. SQLAlchemy-Modelle (Pseudo-Code)

```python
# src/app/models.py – Erweiterungen fuer EPIC-18

import bcrypt  # oder argon2-cffi
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# REQ-4001 / REQ-4020: User-Modell
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="editor", server_default="editor")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    is_first_admin = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project_memberships = relationship("ProjectMembership",
                                        back_populates="user",
                                        cascade="all, delete-orphan")

    def set_password(self, plain_password: str) -> None:
        self.password_hash = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, plain_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), self.password_hash.encode())


# ---------------------------------------------------------------------------
# REQ-4001: Refresh-Token-Speicherung
# ---------------------------------------------------------------------------

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")


# ---------------------------------------------------------------------------
# REQ-4023: Projekt-Mitgliedschaft
# ---------------------------------------------------------------------------

class ProjectMembership(Base):
    __tablename__ = "project_memberships"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="editor", server_default="editor")
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    project = relationship("Project")
    user = relationship("User", back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])


# ---------------------------------------------------------------------------
# REQ-4021 / REQ-4024: Erweiterungen bestehender Modelle
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"
    # ... bestehende Felder ...
    version = Column(Integer, nullable=False, default=0, server_default="0")
    last_modified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    # ... relationships ...
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    memberships = relationship("ProjectMembership", back_populates="project")


class Category(Base):
    __tablename__ = "categories"
    # ... bestehende Felder ...
    version = Column(Integer, nullable=False, default=0, server_default="0")
    last_modified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    last_modifier = relationship("User", foreign_keys=[last_modified_by])


class Value(Base):
    __tablename__ = "values"
    # ... bestehende Felder ...
    version = Column(Integer, nullable=False, default=0, server_default="0")
    last_modified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    last_modifier = relationship("User", foreign_keys=[last_modified_by])


class TestCase(Base):
    __tablename__ = "testcases"
    # ... bestehende Felder ...
    version = Column(Integer, nullable=False, default=0, server_default="0")
    last_modified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
```

### 5. Migration-Schritte (Alembic)

Zwei separate Migrationen fuer klares Rollback und Testing:

#### Migration 1: Neue Tabellen (`users`, `refresh_tokens`, `project_memberships`)

```python
"""EPIC-18: Create Multi-User tables

Revision ID: xxx_epic18_multi_user_tables
Revises: a7b8b126c88d
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx_epic18_multi_user_tables'
down_revision = 'a7b8b126c88d'


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='editor'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('is_first_admin', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # 2. refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime, nullable=False, index=True),
        sa.Column('revoked', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # 3. project_memberships
    op.create_table(
        'project_memberships',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer,
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer,
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='editor'),
        sa.Column('invited_by', sa.Integer,
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('joined_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )
    op.create_index('idx_pm_project', 'project_memberships', ['project_id'])
    op.create_index('idx_pm_user', 'project_memberships', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_pm_user', table_name='project_memberships')
    op.drop_index('idx_pm_project', table_name='project_memberships')
    op.drop_table('project_memberships')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
```

#### Migration 2: Neue Spalten (`version`, `last_modified_by`, `last_modified_at`)

```python
"""EPIC-18: Add version and audit columns to existing tables

Revision ID: xxx_epic18_version_audit_columns
Revises: xxx_epic18_multi_user_tables
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx_epic18_version_audit_columns'
down_revision = 'xxx_epic18_multi_user_tables'


def upgrade() -> None:
    for table in ['projects', 'categories', 'values', 'testcases']:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('version', sa.Integer, nullable=False, server_default='0'))
            batch_op.add_column(
                sa.Column('last_modified_by',
                          sa.Integer,
                          sa.ForeignKey('users.id', ondelete='SET NULL'),
                          nullable=True))
            batch_op.add_column(
                sa.Column('last_modified_at', sa.DateTime, nullable=True))


def downgrade() -> None:
    for table in ['testcases', 'values', 'categories', 'projects']:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('last_modified_at')
            batch_op.drop_column('last_modified_by')
            batch_op.drop_column('version')
```

**Backward-Compatibility-Garantien:**

| Aspekt | Garantie |
|---|---|
| **Bestehende Projekte** | Keine Aenderung – `version=0`, `last_modified_by=NULL` |
| **Bestehende API-Endpunkte** | Keine Breaking Changes – neue Felder sind nullable oder haben Defaults |
| **Single-User-Betrieb** | Bleibt voll funktionsfahig – Auth-Dependency kann optional sein (Admin-Mode) |
| **SQLite WAL-Mode** | Bestehende WAL-Konfiguration in `database.py` bleibt unveraendert |
| **Rollback** | Vollstaendiger downgrade moeglich (beide Migrationen reversibel) |
| **Foreign-Key-Constraints** | `SET NULL` auf `last_modified_by` – User-Loeschung loescht keine Audit-Info |

### 6. PostgreSQL vs. SQLite (REQ-4006)

#### 6.1 Konfiguration (bereits vorhanden)

Die Datei `src/app/database.py` unterstuetzt bereits DATABASE_URL-basierten Switch:

```python
if DATABASE_URL.startswith("sqlite"):
    # SQLite: WAL-Mode + Connection-Pool
else:
    # PostgreSQL: Connection-Pool
```

**Keine Aenderung erforderlich** – die bestehende Implementierung deckt REQ-4006 ab.

#### 6.2 PostgreSQL-spezifische Ueberlegungen

| Aspekt | SQLite | PostgreSQL | Massnahme |
|---|---|---|---|
| **Connection Pooling** | QueuePool (5+10) | QueuePool (10+20) | Bereits in `database.py` implementiert |
| **WAL-Mode** | PRAGMA auf Connect-Event | Nicht relevant (PG hat eigenen WAL) | Bereits implementiert |
| **Enum-Typen** | Stored as TEXT | Native ENUM | String-Spalten (nicht sa.Enum) fuer Kompatibilitaet |
| **AUTOINCREMENT** | `INTEGER PRIMARY KEY` | `SERIAL` | SQLAlchemy abstrahiert dies automatisch |
| **Boolean** | INTEGER (0/1) | BOOLEAN | SQLAlchemy abstrahiert dies automatisch |
| **Migrations** | `batch_alter_table` (SQLite-Besonderheit) | Direkte ALTER TABLE | `batch_alter_table` funktioniert auch unter PG (no-op wrapper) |

**Entscheidung:** Alle Enum-Werte (`role`, `project_membership.role`) als `String` implementieren,
nicht als `sa.Enum`. Grund: SQLite speichert Enums als TEXT, PostgreSQL als nativen ENUM-Typ.
Die Migration zwischen beiden ist bei sa.Enum problematisch (ENUM-Typ muss in PG erst erstellt
werden). String vermeidet diesen Cross-DB-Konflikt komplett.

#### 6.3 Lasttest-Anforderung (REQ-4006)

- 10 simulierten gleichzeitigen Nutzer (Lesen + Schreiben)
- Sowohl SQLite als auch PostgreSQL
- Messung: Antwortzeiten, 409-Raten, Deadlocks (SQLite), Connection-Pool-Exhaustion (PG)

### 7. API-Design

#### 7.1 Neue Endpunkte

| Methode | Pfad | Beschreibung | Rolle | REQ |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | Login, liefert Access+Refresh Token | Public | REQ-4001 |
| POST | `/api/v1/auth/refresh` | Refresh-Token → neue Token-Paar | Authenticated | REQ-4001 |
| POST | `/api/v1/auth/logout` | Refresh-Token invalidate | Authenticated | REQ-4001 |
| GET | `/api/v1/auth/me` | Eigene User-Info | Authenticated | REQ-4001 |
| POST | `/api/v1/users` | User anlegen (nur wenn noch kein User existiert = first-admin) | Public (1x) | REQ-4001 |
| GET | `/api/v1/users` | User-Liste | Admin | REQ-4020 |
| PATCH | `/api/v1/users/{uid}/role` | Globale Rolle aendern | Admin | REQ-4020 |
| PATCH | `/api/v1/users/{uid}/status` | Aktiv/Inaktiv schalten | Admin | REQ-4020 |
| GET | `/api/v1/projects/{pid}/members` | Mitglieder-Liste eines Projekts | Owner/Admin | REQ-4023 |
| POST | `/api/v1/projects/{pid}/members` | Mitglied hinzufuegen | Owner/Admin | REQ-4023 |
| DELETE | `/api/v1/projects/{pid}/members/{uid}` | Mitglied entfernen | Owner/Admin | REQ-4023 |
| PATCH | `/api/v1/projects/{pid}/members/{uid}` | Projekt-Rolle aendern | Owner/Admin | REQ-4023 |

#### 7.2 Aenderungen an bestehenden Endpunkten

Alle bestehenden Endpunkte erhalten drei neue Anforderungen:

1. **Auth-Dependency**: `Depends(get_current_user)` auf allen Endpunkten
2. **Rollen-Pruefung**: `Depends(require_role)` auf schreibenden Endpunkten
   - Viewer: Nur GET-Endpunkte
   - Editor: GET + POST + PUT/PATCH + DELETE (innerhalb zugreifbarer Projekte)
   - Admin: Alles + Nutzerverwaltung
3. **Version-Check**: PUT/PATCH-Endpunkte pruefen `version`-Feld
   - Request-Body enthaelt `version` (vom Client mitgesendet)
   - Backend vergleicht mit DB-Version
   - Diskrepanz → 409 Conflict mit aktuellem Serverstand im Body
   - Bei Erfolg: `version` wird um 1 erhoht, `last_modified_by` und `last_modified_at` werden gesetzt

```python
# Beispiel: PATCH /categories/{id} – erweitert
@router.patch("/categories/{cat_id}")
async def update_category(
    cat_id: int,
    body: CategoryUpdate,  # enthaelt jetzt 'version'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ = Depends(require_role("editor")),
):
    cat = db.get(Category, cat_id)
    if cat.version != body.version:
        raise HTTPException(
            status_code=409,
            detail={
                "reason": "stale_version",
                "current_version": cat.version,
                "sent_version": body.version,
                "last_modified_by": cat.last_modifier.username if cat.last_modifier else None,
                "last_modified_at": cat.last_modified_at.isoformat() if cat.last_modified_at else None,
                "current_data": cat.to_dict()  # aktueller Serverstand
            }
        )

    # ... Aktualisierung ...
    cat.version += 1
    cat.last_modified_by = current_user.id
    cat.last_modified_at = datetime.now(timezone.utc)
    db.commit()
```

#### 7.3 JWT-Token-Strategie

| Token | TTL | Speicher | Rotation |
|---|---|---|---|
| **Access Token** | 15 Minuten | httpOnly-Cookie (secure, sameSite=strict) | Bei jedem Refresh neu |
| **Refresh Token** | 7 Tage | httpOnly-Cookie (secure, sameSite=strict) | Rotation: alter Token wird invalidiert, neuer Token ausgegeben |

**Entscheidungen:**
- httpOnly-Cookies statt localStorage: Schutz gegen XSS (RISK-S-004)
- Kurze Access-Token-TTL: Begrenzt den Schaden bei Token-Diebstahl
- Refresh-Token-Rotation: Jeder Refresh invalidiert den alten Token;
  wenn ein abgehoerter alter Token noch verwendet wird, ist das ein
  Indiz fuer Session-Hijacking (kann in der Zukunft zu einem Alert fuehren)
- bcrypt fuer Passwort-Hashing: Industriestandard, gut getestet, SQLite/PostgreSQL-kompatibel

### 8. Rollen-Matrix

| Aktion | Viewer | Editor | Admin |
|---|---|---|---|
| Projekt lesen | ✅ (wenn Mitglied) | ✅ (wenn Mitglied) | ✅ (alle) |
| Projekt erstellen | ❌ | ✅ | ✅ |
| Projekt loeschen | ❌ | ❌ | ✅ |
| Kategorie bearbeiten | ❌ | ✅ (in zugreifbaren Projekten) | ✅ |
| Wert bearbeiten | ❌ | ✅ (in zugreifbaren Projekten) | ✅ |
| Testfall bearbeiten | ❌ | ✅ (in zugreifbaren Projekten) | ✅ |
| Regel bearbeiten | ❌ | ✅ (in zugreifbaren Projekten) | ✅ |
| Generierung starten | ❌ | ✅ (in zugreifbaren Projekten) | ✅ |
| User anlegen | ❌ | ❌ | ✅ (nur first-admin kann ersten User anlegen) |
| User-Rolle aendern | ❌ | ❌ | ✅ |
| Projekt-Mitglieder verwalten | ❌ | ❌ | ✅ + Owner |
| Projekt als Owner verwalten | ❌ | ❌ | ✅ (automatisch bei Erzeugung) |

### 9. Bootstrapping (First-Admin-Pattern)

```
1. App startet, keine User in DB
2. POST /auth/register (einmalig) – erstellt ersten User als Admin (is_first_admin=True)
3. Nach erfolgreichem ersten Register: /auth/register gibt 403 (nur Admin kann neue User anlegen)
4. Admin legt weitere User ueber POST /users an
5. Admin weist User Projekten zu ueber POST /projects/{pid}/members
```

### 10. Abgelehnte Alternativen

| Alternative | Grund der Ablehnung |
|---|---|
| **Rollen als separate Tabelle + Junction-Table** | Nur 3 statische Rollen; String-Enum ist einfacher und performanter |
| **E-Mail-Authentifizierung** | EPIC-18 ist fuer lokale Teams ohne E-Mail-Infrastructure |
| **OAuth2-Provider (Google, GitHub)** | Out of Scope – nur lokale Authentifizierung (REQ-4001: "lokale OAuth2/JWT-Nutzer") |
| **Vollstaendiges Audit-Log (alle Aenderungen)** | REQ-4024 verlangt explizit nur "letzten Aenderer"; voller Audit-Trail ist REQ-4003 (Phase 5+) |
| **Version auf allen Tabellen** | `generations`, `testcase_values`, `rules`, `dataclasses` werden nicht von Nutzern direkt bearbeitet; Overhead ohne Nutzen |
| **Pessimistic Locking (SELECT FOR UPDATE)** | ADR-012 hat Optimistic Concurrency entschieden; Pessimistic Locking waere ein Konflikt mit ADR-012 |
| **Row-Level Security (PostgreSQL RLS)** | SQLite hat keine RLS; Cross-DB-Kompatibilitaet erfordert App-Level-Filterung |

### 11. Konsequenzen

| Bereich | Auswirkung |
|---|---|
| **Dependencies** | `bcrypt` (oder `argon2-cffi`) + `PyJWT` zu requirements.txt |
| **Config** | `JWT_SECRET_KEY` und `JWT_REFRESH_SECRET_KEY` als neue Umgebungsvariablen in config.py |
| **Migrations** | Zwei neue Alembic-Migrationen (siehe oben) |
| **API-Breaking** | Alle bestehenden Endpunkte erhalten Auth-Dependency – bestehende Clients ohne Token erhalten 401 |
| **Migration-Pfad** | Bestehende Daten bleiben erhalten; erste Installation ohne User → Bootstrapping-Flow |
| **Testing** | Neue Test-Suite fuer Auth, Rollen, Concurrency (REQ-4021), Stale-Warnings (REQ-4022) |
| **Security** | Security Architect Review (RISK-S-001) vor Sprint-11-Start zwingend |
| **Frontend** | Login-Komponente, Token-Management, Stale-Data-Banner (REQ-4022) |
| **CORS** | Whitelist-Konfiguration vor Multi-User-Release (EPIC-18-Risiko) |

**Begründung:**
- Additive Erweiterung (keine Aenderung bestehender Tabellen-Strukturen) ist der
  sicherste Migrationsweg und entspricht dem Vorgehen aus ADR-002 (Alembic)
- String-basierte Enums statt sa.Enum: Cross-DB-Kompatibilitaet (SQLite + PostgreSQL)
- Separation der drei neuen Tabellen: Klares Rollback, klares Testing
- Version/Audit nur auf nutzer-bearbeitbaren Tabellen: Vermeidet Overhead auf System-Tabellen
- httpOnly-Cookies fuer Token: OWASP-Empfehlung, Schutz gegen XSS
- Refresh-Token-Rotation: Erkennung von Session-Hijacking

**Konsequenzen (Detail):**
- **REQ-4001** (Auth): `users` + `refresh_tokens` Tabellen, JWT-Endpunkte, bcrypt-Hashing
- **REQ-4006** (Multi-User-DB): DATABASE_URL-Switch bereits vorhanden, WAL-Mode aktiv, Pooling aktiv
- **REQ-4020** (Rollen): `role`-Spalte in `users`, Rollen-Pruefung auf allen Endpunkten
- **REQ-4021** (Optimistic Concurrency): `version`-Spalte auf 4 Tabellen, 409-Conflict-Logik
- **REQ-4022** (Stale-Data-Warning): 409-Response enthaelt genuegend Info fuer Frontend-Banner
- **REQ-4023** (Projekt-Sharing): `project_memberships` Tabelle, Mitglieder-Endpunkte
- **REQ-4024** (Audit-Trail): `last_modified_by` + `last_modified_at` auf 4 Tabellen

**Entscheider:** GREAT Chief Architect Agent
**Abhaengigkeiten:** EPIC-18 (REQ-4001, 4006, 4020-4024), ADR-001 (Python/FastAPI),
ADR-002 (Alembic), ADR-012 (HYBRID-Konfliktstrategie), RISK-S-001 (Auth-Security),
RISK-T-006 (SQLite-Multi-User), RISK-T-008 (Concurrency-Konflikte)

---

## ADR-016 - Persistente Constraint-Speicherung fuer Entscheidungstabelle (EPIC-20, Sprint 15)

**Datum:** 2026-10-06
**Status:** Accepted
**Kontext:**
REQ-5012 (Constraint-Dialog) benoetigt persistente Speicherung von Constraints pro Projekt.
Bisher wurden Constraints nur transient ueber den /generate-Endpoint uebergeben.
Fuer die UX des Constraint-Dialogs muss jeder Constraint persistent gespeichert, editiert und geloescht werden koennen.

**Entscheidung:**
- Neue Tabelle decision_table_constraints mit Spalten: id, project_id, constraint_type, targets (JSON), description
- CRUD-Endpoints: GET /constraints/{project_id}, POST /constraints, DELETE /constraints/{id}
- POST /generate laedt automatisch persistente Constraints, wenn kein Override uebergeben wird
- targets als JSON-Spalte: Liste fuer E/O/I, Dict {from, to} fuer R/M

**Begründung:**
- JSON-Spalte in SQLite ist nativ unterstuetzt und flexibel genug fuer verschiedene Constraint-Typen
- Einfache CRUD-Struktur ohne komplexe Normalisierung
- Override-Mechanismus in /generate erlaubt sowohl persistente als auch ad-hoc Constraints

**Konsequenzen:**
- Frontend-Dialog (UX-Lead) kann auf CRUD-API aufsetzen
- Constraints sind projektgebunden und werden mit Projekt gespeichert
- Migration in main.py _migrate_db() integriert (idempotent)

**Geaenderte Dateien:**
- src/app/models/decision_table_constraint.py (NEU)
- src/app/routers/api_decision_table.py (erweitert)
- src/app/main.py (Migration)
- tests/test_decision_table_constraints.py (NEU, 18 Tests)

**Entscheider:** GREAT Senior Developer Agent
**Abhaengigkeiten:** REQ-5012, ADR-014 (Entscheidungstabelle-Schema), ADR-001 (Python/FastAPI)

---

## ADR-013 – Rollen- und Rechtekonzept fuer G.R.E.A.T.

**Datum:** 2026-10-07
**Status:** Proposed

**Kontext:**
G.R.E.A.T. wird im Multi-User-Betrieb mit bis zu 10 Nutzern eingesetzt (EPIC-18, ADR-012, ADR-015).
REQ-4020 definiert drei serverseitige Rollen: Admin, Editor, Viewer.
REQ-4025 implementiert die Benutzerverwaltung im Frontend.
Der Projektinhaber fragt nach einem expliziten Konzept, welche Funktionen und Rechte
die einzelnen Rollen in der Anwendung haben duerfen.

**Entscheidung:** Drei-Rollen-Modell mit folgender Rechte-Matrix:

### Rechte-Matrix

| Funktion | Admin | Editor | Viewer |
|---|:---:|:---:|:---:|
| Login/Logout | ✅ | ✅ | ✅ |
| Passwort eigenen aendern | ✅ | ✅ | ✅ |
| Nutzer anlegen | ✅ | ❌ | ❌ |
| Nutzer loeschen | ✅ | ❌ | ❌ |
| Nutzer-Rolle aendern | ✅ | ❌ | ❌ |
| Projekt anlegen | ✅ | ✅ | ❌ |
| Projekt bearbeiten (Kategorien/Werte) | ✅ | ✅ | ❌ |
| Projekt loeschen | ✅ | ❌ | ❌ |
| Testfaelle generieren | ✅ | ✅ | ✅ |
| Testfaelle exportieren | ✅ | ✅ | ✅ |
| Einstellungen (Port, Max Testfaelle) | ✅ | ❌ | ❌ |
| Datensicherung (Backup) | ✅ | ✅ | ❌ |
| Datenbank zuruecksetzen | ✅ | ❌ | ❌ |
| BugMagnet-Import | ✅ | ❌ | ❌ |
| System-Datenklassen verwalten | ✅ | ❌ | ❌ |

### Rollendefinitionen

**Admin** – Vollzugriff inkl. Nutzerverwaltung und System-Einstellungen
- Kann alle Funktionen der Anwendung nutzen
- Verwaeltigt andere Nutzer (anlegen, loeschen, Rollen aendern)
- Hat Zugriff auf System-Einstellungen (Port, Max-Testfaelle, Datenbank-Reset)
- Kann BugMagnet-Importe durchfuehren und System-Datenklassen verwalten
- Kann Projekte loeschen

**Editor** – Kann Projekte erstellen, bearbeiten und Testfaelle generieren
- Kann eigene Projekte anlegen, bearbeiten und Testfaelle generieren/exportieren
- Kann Datensicherungen (Backups) erstellen
- **Keine** Nutzerverwaltung (keine User anlegen/loeschen/Rollen aendern)
- **Keine** System-Einstellungen (Port, Max-Testfaelle, Datenbank-Reset)
- **Kein** BugMagnet-Import, **keine** System-Datenklassen-Verwaltung
- **Kann** Projekte nicht loeschen (nur Admin)

**Viewer** – Nur lesen, generieren und exportieren
- Kann in zugreifbaren Projekten lesen und Testfaelle generieren/exportieren
- **Kein** Schreibzugriff auf Projekte (keine Kategorien/Werte bearbeiten)
- **Kein** Projekt anlegen oder loeschen
- **Keine** System-Einstellungen oder Nutzerverwaltung
- **Kein** Backup oder BugMagnet-Import

### Backend-Implementierung

Alle schreibenden Endpunkte muessen eine Rollenpruefung besitzen. Die Pruefung
erfolgt ueber FastAPI-Dependencies (`Depends(require_role(...))`), wie in ADR-015
beschrieben. Bei fehlender Berechtigung gibt der Endpunkt HTTP 403 (Forbidden)
zurueck mit folgendem Detail:

```json
{
  "detail": "Diese Aktion erfordert die Rolle 'Admin'",
  "required_role": "admin",
  "current_role": "editor"
}
```

### Frontend-Implementierung

Die UI muss Aktionen fuer nicht-berechtigte Rollen ausblenden oder deaktivieren:
- Menuepunkte und Buttons, die eine hohere Rolle erfordern, werden ausgeblendet oder
  als deaktiviert (disabled) dargestellt mit einem Tooltip, der die erforderliche Rolle
  anzeigt
- Bei einem 403-Fehler vom Backend zeigt das Frontend eine klare Fehlermeldung:
  "Diese Aktion erfordert die Rolle X"

### Projekt-Sharing (REQ-4023)

ADR-015 definiert projekt-spezifische Rollen (Owner/Editor/Viewer) in der
`project_memberships`-Tabelle. Das Zusammenspiel mit den globalen Rollen ist
folgendermassen zu verstehen:

- **Globale Rolle** (in `users.role`): Bestimmt, ob ein Nutzer systemuebergreifende
  Aktionen ausfuehren darf (Nutzerverwaltung, System-Einstellungen, BugMagnet-Import)
- **Projekt-Rolle** (in `project_memberships.role`): Bestimmt, ob ein Nutzer
  Zugriff auf ein bestimmtes Projekt hat und welche Aktionen er dort duerfen

Die effektive Berechtigung fuer eine Projektaktion ist die Schnittmenge aus
globaler Rolle und Projekt-Rolle. Beispiel: Ein globaler Editor, der in einem
Projekt als Viewer eingeladen wurde, kann in diesem Projekt nur lesen
(Projekt-Rolle Viewer limitiert den Zugriff).

### Abgelehnte Alternativen

| Alternative | Grund der Ablehnung |
|---|---|
| **Vier Rollen (Admin/Editor/Viewer/Guest)** | Kein Bedarf fuer Gast-Zugriff; EPIC-18 ist fuer authentifizierte Teams konzipiert |
| **Feingraenulare Berechtigungen pro Funktion** | Bei ≤10 Nutzern und 3 Rollen ist eine grobe Rollen-Matrix einfacher zu verstehen und zu warten |
| **Editor darf Projekte loeschen** | Projektersteller (Owner) und Admin behalten die Kontrolle; Editor kann ein Projekt nicht versehentlich loeschen |
| **Viewer darf Backup erstellen** | Backup ist eine schreibende Operation; Viewer soll rein lesend arbeiten |

### Offene Fragen

1. **Sollte Editor Projekte loeschen duerfen?**
   Aktuell: Nein, nur Admin. Begründung: Der Projektersteller (Owner) sollte
   die Kontrolle behalten. Ein Editor, der zu einem Projekt eingeladen wurde,
   sollte nicht in der Lage sein, das Projekt zu loeschen.
   
2. **Sollte Viewer Backup erstellen duerfen?**
   Aktuell: Nein, nur Admin/Editor. Begründung: Viewer hat keinen Schreibzugriff
   und sollte keine Operationen ausfuehren, die Systemressourcen verbrauchen.
   
3. **Projekt-Sharing: Kann Editor Projekte mit anderen teilen?**
   Noch zu entscheiden. ADR-015 sieht vor, dass nur Owner/Admin Mitglieder
   verwalten duerfen. Die Frage ist, ob ein Editor, der als Owner eines
   Projekts eingetragen ist, auch Mitglieder einladen kann. Empfehlung: Ja,
   Owner kann Mitglieder einladen, unabhaengig von der globalen Rolle.

**Begründung:**
- Das Drei-Rollen-Modell ist einfach zu verstehen und deckt die typischen
  Nutzungsszenarien kleiner Teams ab
- Admin hat Vollzugriff, da er fuur die System-Administration verantwortlich ist
- Editor ist die Hauptnutzerrolle: Kann arbeiten, aber keine System- oder
  Nutzer-Einstellungen veraendern
- Viewer ist fuur Read-Only-Zugriff (z.B. QA-Berichte, Management-Review)
- Die Trennung zwischen globalen und projekt-spezifischen Rollen (ADR-015)
  erlaubt flexible Zugriffskontrolle ohne Komplexitaets-Explosion

**Konsequenzen:**
- **Backend**: Alle schreibenden Endpunkte erhalten Rollenpruefung (bereits teilweise
  in ADR-015 dokumentiert). Die 403-Antwort muss die erforderliche Rolle enthalten.
- **Frontend**: UI muss Aktionen fuer nicht-berechtigte Rollen ausblenden/deaktivieren.
  REQ-4025 (Benutzerverwaltung im Frontend) muss die Rechte-Matrix implementieren.
- **Testing**: Neue Tests fuer jede Rolle × jede Funktion (Matrix-Tests), um sicherzustellen,
  dass Berechtigungen korrekt enforced werden.
- **Dokumentation**: Nutzerdokumentation muss die drei Rollen und ihre Rechte beschreiben.

**Entscheider:** GREAT Chief Architect Agent (in Abstimmung mit Projektinhaber)
**Abhaengigkeiten:** REQ-4020 (Rollen serverseitig), REQ-4025 (Benutzerverwaltung Frontend),
REQ-4023 (Projekt-Sharing), ADR-012 (HYBRID-Multi-User), ADR-015 (DB-Schema EPIC-18),
RISK-S-001 (Auth-Security)

---

## ADR-017 – Erststart-Hinweis mit Risikoakzeptanz (REQ-4027/4028)

**Datum:** 2026-11-03
**Status:** Accepted (Risikoakzeptanz durch Projektinhaber Georg Hartel)

**Kontext:**
G.R.E.A.T. bootstrapped einen Default-Admin-Account (`admin` / `changeme123!`) in
`src/app/bootstrap.py`. Das Passwort steht als Klartext im Quellcode. Ohne Authentifizierung
(RISK-S-001, Score 20) ist dies ein bekanntes Sicherheitsrisiko.

Der Security Architect hat den Vorschlag eines Klartext-Hinweises auf der Login-Seite
abgelehnt. Der Projektinhaber (Georg Hartel) hat das Risiko am 2026-11-03 bewusst
akzeptiert mit der Bedingung, dass das Risiko durch Gegenmassnahmen gemildert wird.

**Entscheidung:**
- **REQ-4027**: Die Login-Seite zeigt bei Erstanmeldung einen Hinweis mit dem Standardpasswort
  des Default-Admin-Accounts. Dies ist eine bewusste Risikoakzeptanz, keine Empfehlung.
- **REQ-4028**: Nach der Erstanmeldung mit dem Default-Passwort wird der Benutzer gezwungen,
  sein Passwort zu aendern. Selbst-Passwortwechsel ist fuer alle Rollen (Admin/Editor/Viewer)
  verfuegbar.
- **Zusaetzliche Gegenmassnahmen**: Ablehnung bekannter Default-Passwoerter bei der
  Passwortvalidierung, Rate-Limit von 10 Anmeldeversuchen pro Minute pro IP-Adresse.

**Begründung:**
- Der Default-Admin ist fuer lokale Einzelplatz-Nutzung konzipiert (kein Multi-User-Betrieb
  in der aktuellen Phase)
- Die Risikoakzeptanz ist zeitlich begrenzt: Mit EPIC-18 (Sprint 11-13) wird eine
  vollstaendige Authentifizierung (REQ-4001) implementiert, die den Default-Admin
  ersetzt
- Der Pflicht-Passwortwechsel (REQ-4028) stellt sicher, dass das Default-Passwort
  nach der ersten Nutzung nicht mehr existiert
- Rate-Limit und Ablehnung bekannter Defaults schuetzen vor automatisierten Angriffen

**Konsequenzen:**
- **RISK-S-016**: Score bleibt 20 (Risiko nicht beseitigt, nur gemildert). Status:
  "Risikoakzeptanz durch Projektinhaber (Georg Hartel, 2026-11-03)". Siehe `documentation/risk-log.md`.
- **Backend**: 63 neue Tests, 794/796 im Gesamtlauf (2 vorbestehend fehlgeschlagen)
- **Frontend**: In Arbeit (parallel zum Backend), Tests TBD
- **Keine Aenderung** der Roadmap oder Phase-Planung
- **Keine Aenderung** von `requirements_v1.1.md` (REQ-4027/4028 bereits als Planned vorhanden)

**Entscheider:** Georg Hartel (Projektinhaber, Risikoakzeptanz 2026-11-03)
**Abhaengigkeiten:** REQ-4027, REQ-4028, RISK-S-016, EPIC-18 (REQ-4001 als langfristige Loesung)
