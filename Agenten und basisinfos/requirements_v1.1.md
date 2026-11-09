# requirements_v1.1.md – G.R.E.A.T. Konsolidierte Requirements
Version: 1.1
Status: Baseline Phase 0
Projekt: G.R.E.A.T. – Georg Radikal Einfacher Automatisierter TestcaseDesigner
Erstellt: 2026-06-10
Erstellt von: Requirements Engineer Agent

**Hinweis:** Diese Datei ist die einzige maßgebliche Requirements-Quelle ab Phase 1.
`requirements_v1.0.md` bleibt unverändert als Referenz erhalten.

---

## Quellen dieser Konsolidierung
- `Agenten und basisinfos/requirements_v1.0.md` (Initialbacklog)
- `Agenten und basisinfos/requirements.md` (Erweiterter Backlog)
- `Agenten und basisinfos/projektbeschreibung.md` (Fachliche Vision)
- `Agenten und basisinfos/SYSTEM_v1.0.md` (Governance)
- Codeanalyse (bestehende Implementierung)

---

## Prioritäten

- **Must** – zwingend für jede Version
- **Should** – wichtig, aber verzichtbar für MVP
- **Could** – wünschenswert

## Statuswerte

- Planned → Approved → In Progress → Implemented → Tested → Released

---

# EPIC-01 – Projektmanagement & Architektur

## REQ-0001
**Titel:** Bestandsanalyse bestehender Codebasis
**Priorität:** Must
**Status:** Implemented (Phase 0)
**Beschreibung:** Vor Beginn der Entwicklung muss die vorhandene Codebasis analysiert werden.
**Business Value:** Verhindert Doppelentwicklung, schützt Investitionen.
**Akzeptanzkriterien:**
- Given: Phase 0 startet
- When: Legacy Code Auditor analysiert src/
- Then: component-inventory.md ist erstellt mit Klassifizierung (Reuse/Refactor/Replace/Archive)
**Traceability:** DOC-001 (component-inventory.md)
**Abhängigkeiten:** –

## REQ-0002
**Titel:** Archivierungsstrategie
**Priorität:** Must
**Status:** Approved
**Beschreibung:** Nicht genutzte Artefakte werden archiviert, niemals gelöscht.
**Business Value:** Verlustfreie Weiterentwicklung, Rückverfolgbarkeit.
**Akzeptanzkriterien:**
- Given: Datei wird als obsolet klassifiziert
- When: Archive-Prozess ausgeführt wird
- Then: Datei liegt in archive/YYYY-MM-DD/, archive-log.md ist aktualisiert
**Traceability:** ADR-004
**Abhängigkeiten:** –

## REQ-0003
**Titel:** Open-Source-Fähigkeit
**Priorität:** Must
**Status:** Approved
**Beschreibung:** Nur Open-Source-Abhängigkeiten, MIT-Lizenz.
**Business Value:** Community-Adoption, keine Lizenzkosten.
**Akzeptanzkriterien:**
- Given: Neues Paket soll hinzugefügt werden
- When: Lizenzprüfung erfolgt
- Then: Nur MIT/Apache/BSD-kompatible Pakete erlaubt; LICENSE-Datei im Repo vorhanden
**Traceability:** ADR-006
**Abhängigkeiten:** –

---

# EPIC-02 – Benutzeroberfläche

## REQ-0100
**Titel:** Moderne Weboberfläche
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Browserbasierte Oberfläche, die mit allen gängigen Browsern (Chrome, Firefox, Edge, Safari) funktioniert.
**Business Value:** Plattformunabhängige Nutzung ohne Installation beim Endbenutzer.
**Akzeptanzkriterien:**
- Given: Anwendung läuft
- When: Benutzer öffnet Browser
- Then: Oberfläche ist vollständig funktionsfähig in Chrome, Firefox, Edge (aktuelle Versionen)
**Traceability:** TEST-UI-001
**Abhängigkeiten:** –

## REQ-0101
**Titel:** Zweispaltige Hauptansicht
**Priorität:** Must
**Status:** Partial (HTMX-MVP vorhanden, nicht zweispaltig)
**Beschreibung:** Links Baumansicht der Testbedingungen, rechts Tabelle der Testfälle.
**Business Value:** Kernworkflow: Testbedingungen definieren und Testfälle sofort sehen.
**Akzeptanzkriterien:**
- Given: Projekt geöffnet
- When: Hauptansicht geladen
- Then: Links Baumstruktur (Testbedingungen/Äquivalenzklassen), rechts scrollbare Testfalltabelle
**Traceability:** TEST-UI-002
**Abhängigkeiten:** REQ-0300, REQ-0900

## REQ-0102
**Titel:** Menüleiste (Datei, Bearbeiten, Einstellungen, Hilfe)
**Priorität:** Should
**Status:** Planned
**Beschreibung:** Standard Office-ähnliche Menüleiste mit Datei, Bearbeiten, Einstellungen, Hilfe.
**Business Value:** Vertraute Bedienung für Office-Nutzer.
**Akzeptanzkriterien:**
- Given: Anwendung geöffnet
- When: Benutzer klickt Menü
- Then: Untermenüs mit allen relevanten Aktionen erscheinen
**Traceability:** TEST-UI-003
**Abhängigkeiten:** REQ-0200, REQ-0300

## REQ-0103
**Titel:** Kontextmenüs (Rechte Maustaste)
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Kontextmenüs auf allen Objekten (Projekte, Kategorien, Werte, Testfälle).
**Business Value:** Effiziente Bedienung ohne Menüleiste.
**Akzeptanzkriterien:**
- Given: Benutzer rechtsklickt auf Objekt
- When: Kontextmenü erscheint
- Then: Kontextspezifische Aktionen (Umbenennen, Löschen, Hinzufügen, etc.) sind auswählbar
**Traceability:** TEST-UI-004
**Abhängigkeiten:** –

## REQ-0104
**Titel:** Tastaturkürzel (CTRL+C, CTRL+V, CTRL+X, CTRL+Z, CTRL+Y)
**Priorität:** Should
**Status:** Planned
**Beschreibung:** Standard Office-Tastaturkürzel für Kopieren, Einfügen, Ausschneiden, Rückgängig, Wiederholen.
**Business Value:** Produktivität für erfahrene Nutzer.
**Akzeptanzkriterien:**
- Given: Zelle oder Bereich in Testfalltabelle selektiert
- When: CTRL+C gedrückt
- Then: Inhalt liegt in Zwischenablage; CTRL+V fügt ein
**Traceability:** TEST-UI-005
**Abhängigkeiten:** REQ-0900

## REQ-0105
**Titel:** Toolbar mit Hauptfunktionen
**Priorität:** Should
**Status:** Planned
**Beschreibung:** Toolbar-Buttons für häufige Aktionen (Generieren, Exportieren, Neues Projekt, etc.)
**Business Value:** Schnellzugriff auf Kernfunktionen.
**Akzeptanzkriterien:**
- Given: Anwendung geöffnet
- When: Toolbar sichtbar
- Then: Buttons für Generieren, Export, Import, Neues Projekt vorhanden und funktionsfähig
**Traceability:** TEST-UI-006
**Abhängigkeiten:** –

---

# EPIC-03 – Projektverwaltung

## REQ-0200
**Titel:** Projekt anlegen
**Priorität:** Must
**Status:** Implemented
**Beschreibung:** Benutzer kann ein neues Projekt mit Namen anlegen.
**Business Value:** Projekte isolieren Testdesigns voneinander.
**Akzeptanzkriterien:**
- Given: Projektliste geöffnet
- When: Name eingegeben und bestätigt
- Then: Projekt in DB angelegt, erscheint in der Liste, ID zugewiesen
**Traceability:** TEST-PROJ-001 | ARCH-DB-001
**Abhängigkeiten:** –

## REQ-0201
**Titel:** Projekt öffnen/auswählen
**Priorität:** Must
**Status:** Implemented
**Beschreibung:** Benutzer kann ein bestehendes Projekt aus der Liste öffnen.
**Akzeptanzkriterien:**
- Given: Projektliste mit Einträgen
- When: Benutzer klickt Projekt
- Then: Projektkonfiguration wird angezeigt
**Traceability:** TEST-PROJ-002
**Abhängigkeiten:** REQ-0200

## REQ-0202
**Titel:** Projekt umbenennen
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Projekt existiert
- When: Neuer Name eingegeben
- Then: Name in DB aktualisiert, Änderung sofort sichtbar
**Traceability:** TEST-PROJ-003
**Abhängigkeiten:** REQ-0200

## REQ-0203
**Titel:** Projekt löschen
**Priorität:** Must
**Status:** Implemented (mit Guardrail: blockiert bei existierenden Generierungen)
**Akzeptanzkriterien:**
- Given: Projekt ohne Generierungen
- When: Löschen bestätigt
- Then: Projekt + alle Kategorien/Werte/Regeln CASCADE-gelöscht
**Traceability:** TEST-PROJ-004
**Abhängigkeiten:** REQ-0200

## REQ-0204
**Titel:** Projekt duplizieren
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Projekt existiert
- When: Duplizieren ausgelöst
- Then: Neues Projekt mit gleichem Schema (Kategorien/Werte) aber leerem Generierungsverlauf
**Traceability:** TEST-PROJ-005
**Abhängigkeiten:** REQ-0200

---

# EPIC-04 – Testbedingungen & Äquivalenzklassen

## REQ-0300
**Titel:** Testbedingung (Kategorie) anlegen
**Priorität:** Must
**Status:** Implemented
**Beschreibung:** Benutzer kann Testbedingungen (Kategorien) mit Name anlegen.
**Akzeptanzkriterien:**
- Given: Projekt geöffnet
- When: Kategorie-Name eingegeben
- Then: Kategorie in DB angelegt, in Baumansicht sichtbar
**Traceability:** TEST-CAT-001
**Abhängigkeiten:** REQ-0200

## REQ-0301
**Titel:** Testbedingung umbenennen/löschen
**Priorität:** Must
**Status:** Implemented (mit Guardrail)
**Akzeptanzkriterien:**
- Given: Kategorie ohne Generierungen
- When: Umbenennen/Löschen ausgelöst
- Then: Änderung persistiert, Generierungs-Guardrail aktiv
**Traceability:** TEST-CAT-002
**Abhängigkeiten:** REQ-0300

## REQ-0302
**Titel:** Äquivalenzklasse (Wert) anlegen/bearbeiten/löschen
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Kategorie existiert
- When: Wert eingegeben
- Then: Wert mit risk_weight, allowed-Flag, vtype gespeichert
**Traceability:** TEST-VAL-001
**Abhängigkeiten:** REQ-0300

## REQ-0303
**Titel:** Erlaubte/Nicht-erlaubte Klasse markieren
**Priorität:** Must
**Status:** Implemented (allowed-Flag vorhanden)
**Akzeptanzkriterien:**
- Given: Wert angelegt
- When: allowed=false gesetzt
- Then: Wert bei Generierung nicht als erlaubter Wert verwendet
**Traceability:** TEST-VAL-002
**Abhängigkeiten:** REQ-0302

## REQ-0304
**Titel:** Kategorien sortieren (Reihenfolge)
**Priorität:** Should
**Status:** Implemented (order_index + Drag&Drop)
**Akzeptanzkriterien:**
- Given: Mehrere Kategorien vorhanden
- When: Drag&Drop ausgeführt
- Then: order_index persistiert, Reihenfolge bleibt nach Reload
**Traceability:** TEST-VAL-003
**Abhängigkeiten:** REQ-0300

## REQ-0305
**Titel:** Werttypen (Integer, String, Boolean, Liste, Datum, Decimal, Enum)
**Priorität:** Should
**Status:** Partial (vtype-Feld vorhanden, aber nur String implementiert)
**Beschreibung:** Jede Äquivalenzklasse kann einem Typ zugeordnet werden.
**Akzeptanzkriterien:**
- Given: Wert wird angelegt
- When: Typ ausgewählt (Integer, String, Bool, etc.)
- Then: vtype in DB gespeichert; UI zeigt typspezifische Eingabefelder
**Traceability:** TEST-VAL-004
**Abhängigkeiten:** REQ-0302

## REQ-0306
**Titel:** Grenzwertanalyse
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Für numerische Typen: Grenzwerte (untere/obere Grenze) definieren, automatisch 2/3/4 Testwerte pro Grenze generieren.
**Business Value:** ISTQB-konforme Grenzwertanalyse ohne manuelle Berechnung.
**Akzeptanzkriterien:**
- Given: Kategorie mit Integer/Decimal-Typ
- When: Grenzen (Min, Max) eingegeben + Anzahl Testwerte gewählt
- Then: Grenzwerttestwerte automatisch berechnet und als Äquivalenzklassen eingefügt
**Traceability:** TEST-BVA-001
**Abhängigkeiten:** REQ-0305

---

# EPIC-05 – Geschäftsregeln

## REQ-0700
**Titel:** Regeltyp Verboten (Forbidden)
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Zwei Äquivalenzklassen können nicht gleichzeitig in einem Testfall erscheinen.
**Akzeptanzkriterien:**
- Given: Regel Verboten(A=x, B=y) definiert
- When: Testfälle generiert werden
- Then: Kein Testfall enthält A=x und B=y gleichzeitig
**Traceability:** TEST-RULE-001
**Abhängigkeiten:** REQ-0300, REQ-0800

## REQ-0701
**Titel:** Regeltyp Abhängig (Dependency)
**Priorität:** Must
**Status:** Partial (DB-Modell vorhanden, Generierung teilweise)
**Beschreibung:** Wenn A=x, dann muss B=y in demselben Testfall sein.
**Akzeptanzkriterien:**
- Given: Regel Abhängig(A=x → B=y) definiert
- When: Testfall mit A=x generiert
- Then: B=y im selben Testfall gesetzt
**Traceability:** TEST-RULE-002
**Abhängigkeiten:** REQ-0300, REQ-0800

## REQ-0702
**Titel:** Regeltyp Kombinierbar (Combine)
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Regel Kombinierbar(A=x, B=[y1,y2]) definiert
- When: Generierung läuft
- Then: A=x wird nur mit y1 oder y2 kombiniert
**Traceability:** TEST-RULE-003
**Abhängigkeiten:** REQ-0700

## REQ-0703
**Titel:** Grafische Darstellung von Regeln
**Priorität:** Could
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Regeln definiert
- When: Baumansicht angezeigt
- Then: Verbindungslinien in Farbe (rot=Verboten, grün=Abhängig, blau=Kombinierbar)
**Traceability:** TEST-RULE-004
**Abhängigkeiten:** REQ-0700, REQ-0701, REQ-0702

---

# EPIC-06 – Kombinationsverfahren

## REQ-0800
**Titel:** Pairwise (2-Wege-Abdeckung)
**Priorität:** Must
**Status:** Implemented (als Orthogonal/Pairwise)
**Akzeptanzkriterien:**
- Given: Kategorien mit Werten konfiguriert
- When: Strategie Pairwise gewählt
- Then: Jedes Wertepaar (alle Kategoriepaare) mindestens einmal abgedeckt; weniger Testfälle als All-Combinations
**Traceability:** TEST-COMB-001
**Abhängigkeiten:** REQ-0300

## REQ-0801
**Titel:** Each Choice
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Kategorien konfiguriert
- When: Each-Choice gewählt
- Then: Jeder Wert erscheint mindestens einmal
**Traceability:** TEST-COMB-002
**Abhängigkeiten:** REQ-0300

## REQ-0802
**Titel:** All Combinations
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Kategorien konfiguriert
- When: All-Combinations gewählt
- Then: Kartesisches Produkt aller Werte; |TC| = Produkt aller Wertemengen
**Traceability:** TEST-COMB-003
**Abhängigkeiten:** REQ-0300

## REQ-0803
**Titel:** Lineare Expansion
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Ein Basisfall + je ein Testfall pro Abweichung.
**Akzeptanzkriterien:**
- Given: Kategorien konfiguriert, Basiswert je Kategorie festgelegt
- When: Lineare Expansion gewählt
- Then: 1 Basisfall + N Testfälle (je Kategorie ein abweichender Wert)
**Traceability:** TEST-COMB-004
**Abhängigkeiten:** REQ-0300

## REQ-0804
**Titel:** MCDC (Modified Condition/Decision Coverage)
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Boolesche Bedingungen konfiguriert
- When: MCDC gewählt
- Then: Jede Bedingung hat unabhängigen Einfluss auf mindestens einen Testfall
**Traceability:** TEST-COMB-005
**Abhängigkeiten:** REQ-0305

## REQ-0805
**Titel:** Risikogewichtete Generierung
**Priorität:** Should
**Status:** Planned
**Beschreibung:** Werte mit höherem risk_weight erscheinen häufiger in Testfällen.
**Akzeptanzkriterien:**
- Given: Werte mit risk_weight > 1 konfiguriert
- When: Risikogewichtet gewählt
- Then: Hochrisiko-Werte erscheinen in mehr Testfällen als Niedrigrisiko-Werte
**Traceability:** TEST-COMB-006
**Abhängigkeiten:** REQ-0302

## REQ-0806
**Titel:** T-Wise / 3-Wise
**Priorität:** Could
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Kategorien konfiguriert
- When: 3-Wise gewählt
- Then: Alle 3er-Kombinationen mindestens einmal abgedeckt
**Traceability:** TEST-COMB-007
**Abhängigkeiten:** REQ-0800

## REQ-0807
**Titel:** Freie Benutzerkombination (Manuelle Testfälle)
**Priorität:** Must
**Status:** Planned
**Beschreibung:** Benutzer wählt manuell Werte pro Testfall.
**Akzeptanzkriterien:**
- Given: Testfalltabelle offen
- When: Benutzer Wert in Zelle klickt
- Then: Dropdown mit allen Äquivalenzklassen der Kategorie; Auswahl speichert Wert
**Traceability:** TEST-COMB-008
**Abhängigkeiten:** REQ-0900

---

# EPIC-07 – Testfalltabelle

## REQ-0900
**Titel:** Testfälle als scrollbare Tabelle anzeigen
**Priorität:** Must
**Status:** Partial (UI vorhanden, nicht zweispaltig)
**Akzeptanzkriterien:**
- Given: Testfälle generiert
- When: Ansicht geöffnet
- Then: Tabelle mit Kategorien als Zeilen, Testfällen als Spalten; scrollbar
**Traceability:** TEST-TABLE-001
**Abhängigkeiten:** REQ-0800

## REQ-0901
**Titel:** Testfallwerte manuell editieren
**Priorität:** Must
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Testfall-Zelle selektiert
- When: Neuer Wert eingegeben
- Then: Wert persistiert, Tabelle aktualisiert
**Traceability:** TEST-TABLE-002
**Abhängigkeiten:** REQ-0900

## REQ-0902
**Titel:** Mehrfachselektion + Copy/Paste
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Mehrere Zellen selektiert (Shift+Klick / CTRL+A)
- When: CTRL+C gedrückt, dann CTRL+V
- Then: Inhalte in neue Auswahl eingefügt
**Traceability:** TEST-TABLE-003
**Abhängigkeiten:** REQ-0900, REQ-0104

## REQ-0903
**Titel:** Undo/Redo (CTRL+Z / CTRL+Y)
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Änderung durchgeführt
- When: CTRL+Z gedrückt
- Then: Letzte Änderung rückgängig gemacht (mindestens 10 Schritte)
**Traceability:** TEST-TABLE-004
**Abhängigkeiten:** REQ-0901

---

# EPIC-08 – Export

## REQ-1000
**Titel:** CSV Export
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Testfälle generiert
- When: CSV Export ausgelöst
- Then: CSV-Datei mit Semikolon-Trennzeichen, Kategorie-Namen als Zeilen, TC-Namen als Spalten
**Traceability:** TEST-EXP-001
**Abhängigkeiten:** REQ-0900

## REQ-1001
**Titel:** JSON Export
**Priorität:** Must
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Testfälle vorhanden
- When: JSON Export gewählt
- Then: Strukturiertes JSON mit projects/categories/testcases Hierarchie
**Traceability:** TEST-EXP-002
**Abhängigkeiten:** REQ-0900

## REQ-1002
**Titel:** Excel Export (.xlsx)
**Priorität:** Should
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Testfälle vorhanden
- When: Excel Export gewählt
- Then: .xlsx Datei mit korrekter Tabellendarstellung (openpyxl vorhanden)
**Traceability:** TEST-EXP-003
**Abhängigkeiten:** REQ-0900

## REQ-1003
**Titel:** XML Export
**Priorität:** Could
**Status:** Planned
**Traceability:** TEST-EXP-004
**Abhängigkeiten:** REQ-0900

## REQ-1004
**Titel:** Frei definierbarer Separator
**Priorität:** Could
**Status:** Planned
**Akzeptanzkriterien:**
- Given: Export-Dialog
- When: Benutzer Separator eingibt (z.B. Tab, Komma)
- Then: Datei mit gewähltem Separator exportiert
**Traceability:** TEST-EXP-005
**Abhängigkeiten:** REQ-1000

---

# EPIC-09 – Import

## REQ-1100
**Titel:** CSV Import
**Priorität:** Must
**Status:** Implemented
**Akzeptanzkriterien:**
- Given: Gültige CSV-Datei vorhanden
- When: Import ausgelöst (Überschreiben oder Ergänzen)
- Then: Testfälle korrekt in DB gespeichert
**Traceability:** TEST-IMP-001
**Abhängigkeiten:** REQ-1000

## REQ-1101
**Titel:** JSON Import
**Priorität:** Must
**Status:** Planned
**Traceability:** TEST-IMP-002
**Abhängigkeiten:** REQ-1001

## REQ-1102
**Titel:** Excel Import
**Priorität:** Should
**Status:** Planned
**Traceability:** TEST-IMP-003
**Abhängigkeiten:** REQ-1002

---

# EPIC-10 – Datenhaltung & Qualität

## REQ-1200
**Titel:** SQLite Projektdatenbank mit Alembic-Migrationen
**Priorität:** Must
**Status:** Partial (SQLite vorhanden, Alembic fehlt)
**Akzeptanzkriterien:**
- Given: Neue Version installiert
- When: Anwendung startet
- Then: Datenbankschema automatisch auf aktuelle Version migriert, keine Datenverluste
**Traceability:** ADR-002
**Abhängigkeiten:** –

## REQ-1300
**Titel:** TDD Pflicht + 100% Coverage
**Priorität:** Must
**Status:** Partial (Tests vorhanden, Coverage nicht gemessen)
**Akzeptanzkriterien:**
- Given: Feature entwickelt wird
- When: Tests geschrieben und ausgeführt
- Then: pytest-cov zeigt 100% Statement Coverage für neuen Code
**Traceability:** ADR-005
**Abhängigkeiten:** –

---

# EPIC-11 – Dokumentation

## REQ-1400
**Titel:** Vollständige Projektdokumentation
**Priorität:** Must
**Status:** Partial
**Akzeptanzkriterien:**
- Given: Repository geklont
- When: README.md geöffnet
- Then: Vollständige Installationsanleitung, Startanleitung, Feature-Übersicht vorhanden
**Traceability:** SYSTEM_v1.0 §8
**Abhängigkeiten:** –

---

# EPIC-12 – Zukunftsfunktionen (KI-Roadmap)

## REQ-1500
**Titel:** Benutzerverwaltung vorbereiten (Authentifizierung)
**Priorität:** Should
**Status:** Planned
**Beschreibung:** Architektur muss OAuth2/JWT-Integration unterstützen.
**Traceability:** RISK-S-001 | SYSTEM_v1.0 §15
**Abhängigkeiten:** ADR-001

## REQ-1503
**Titel:** Ollama / LLM-Integration vorbereiten
**Priorität:** Could
**Status:** Planned
**Beschreibung:** Architektur muss lokale LLM-Aufrufe für KI-Vorschläge unterstützen.
**Traceability:** SYSTEM_v1.0 §15
**Abhängigkeiten:** REQ-1500

---

# Phase 4 – Enterprise & Stabilisierung

| REQ-ID | Typ | Titel | Status | Sprint |
|---|---|---|---|---|
| REQ-4007 | Must | GREAT_PORT Umgebungsvariable + .env Support | Tested | Sprint 6 |
| REQ-4008 | Should | Health-Check Endpoint /health | Tested | Sprint 6 |
| REQ-4009 | Should | Strukturiertes Logging (structlog JSON) | Tested | Sprint 7 |
| REQ-4010 | Should | E2E-Tests (Playwright 5 Workflows) | Tested | Sprint 7 |
| REQ-4006 | Must | Multi-User / PostgreSQL optional | Tested | Sprint 8 |
| REQ-4011 | Should | Datensicherung & Wiederherstellung | Tested | Sprint 8 |
| REQ-4012 | Must | BugMagnet-Import + Datenklassen-Überarbeitung | Tested | Sprint 9 |
| REQ-4013 | Should | Eigene Datenklassen Import/Export JSON | Tested | Sprint 9 |
| REQ-4014 | Should | Kategorien-Tabelle + Drag&Drop Reihenfolge | Tested | Sprint 9 |
| REQ-4015 | Should | BVA-Visualisierung überarbeitet + Fehlerwert-Fix | Tested | Sprint 9 |
| REQ-4016 | Must | Ergebnis-Typ für Kategorien (ISTQB Expected Result) | Tested | Sprint 9 |
| REQ-4018 | Should | Max. Testfälle pro Kombination (Setting, Default 1000) | DONE / TESTED | Sprint 10 |
| REQ-4001 | Must | Authentifizierung (OAuth2/JWT) | Implemented | Sprint 11 |
| REQ-4002 | Should | Team-Verwaltung (Projekte teilen) | Planned | Sprint 10+ |
| REQ-4003 | Could | Audit-Log (Wer hat was wann geändert) | Planned | Sprint 11+ |
| REQ-4004 | Should | MCDC + T-Wise Optimierung | Planned | Sprint 9+ |
| REQ-4005 | Could | Ollama / LLM-Integration (optional) | Planned | Sprint 12+ |

**Siehe auch:** `documentation/phase-4-planning.md` (detaillierte Sprint-Planung)

---

## Offene Fragen

| Nr. | Frage | Betreffend | Status |
|---|---|---|---|
| ~~OQ-001~~ | ~~Python/FastAPI oder ASP.NET Core?~~ | Zielarchitektur | ✅ **Python/FastAPI** (ADR-001) |
| ~~OQ-002~~ | ~~MIT-Lizenz?~~ | Lizenz | ✅ **MIT** © Georg Haupt (ADR-006) |
| ~~OQ-003~~ | ~~HTMX oder React?~~ | Frontend | ✅ **React/TypeScript sofort** (ADR-003) |
| ~~OQ-004~~ | ~~Kombinatorik-Priorisierung?~~ | Roadmap | ✅ **Each Choice → Lineare Expansion → All Combinations → Pairwise** |
| ~~OQ-005~~ | ~~Grenzwertanalyse Sprint 1 oder 2?~~ | Planung | ✅ **Sprint 2** |

**Alle offenen Fragen geklärt. Phase 0 vollständig abgeschlossen.**

### Kombinatorik-Roadmap (Priorisierung durch Georg Haupt, 2026-06-10)

| Prio | Strategie | REQ | Sprint Phase 1 | Status |
|---|---|---|---|---|
| 1 | Each Choice | REQ-0801 | Sprint 1 | Implemented (prüfen + testen) |
| 2 | Lineare Expansion | REQ-0803 | Sprint 1 | Planned → implementieren |
| 3 | All Combinations | REQ-0802 | Sprint 1 | Implemented (prüfen + testen) |
| 4 | Pairwise | REQ-0800 | Sprint 1 | Implemented ✅ |
| 5 | Risikogewichtet | REQ-0805 | Sprint 2 | Planned |
| 6 | MCDC | REQ-0804 | Sprint 2 | Planned |
| 7 | T-Wise / 3-Wise | REQ-0806 | Phase 2 | Planned |
| 8 | Business Rule Based | REQ-0808 | Phase 2 | Planned |

**Grenzwertanalyse (REQ-0306): Phase 1 Sprint 2**

### Neues Requirement aus OQ-001-Entscheidung

## REQ-0010
**Titel:** Raspberry Pi Kompatibilität
**Priorität:** Should
**Status:** ⏸ Pausiert (2026-06-29 – Reaktivierung nach Kernstabilisierung)
**Beschreibung:** G.R.E.A.T. muss auf einem Raspberry Pi 4/5 (ARM64, Raspberry Pi OS) lauffähig sein.
**Business Value:** Ermöglicht kostengünstigen Teambetrieb auf dedizierter Hardware ohne Windows-Server.
**Akzeptanzkriterien:**
- Given: Raspberry Pi 4/5 mit Raspberry Pi OS (64-bit)
- When: `pip install -r requirements.txt && bash Start.sh` ausgeführt
- Then: Server startet, UI im Browser erreichbar auf Port 8010
**Traceability:** ADR-001
**Abhängigkeiten:** REQ-0003 (Open Source Only – keine proprietären Pakete)



---
## Phase 2 – Frontend (React/TypeScript)

### REQ-1201 | Vite + React Projekt aufsetzen
Als Entwickler
moechte ich ein Vite + React + TypeScript Projekt im `frontend/` Verzeichnis
damit das Frontend modular, typsicher und schnell buildbar ist.

Akzeptanzkriterien:
- [ ] `npm create vite@latest` Projekt angelegt unter `frontend/`
- [ ] TypeScript konfiguriert (strict mode)
- [ ] Tailwind CSS v3 integriert
- [ ] Vite-Proxy auf FastAPI Port 8000 konfiguriert
- [ ] `npm run dev` startet auf Port 5173
- [ ] `npm run build` erzeugt `frontend/dist/`

Status: offen
Phase: 2, Sprint 1
Prioritaet: hoch

---

### REQ-1202 | FastAPI liefert React-Frontend aus
Als Nutzer
moechte ich das Frontend ueber denselben Port wie die API erreichen (Port 8000)
damit keine separate URL benoetigt wird.

Akzeptanzkriterien:
- [ ] FastAPI liefert `frontend/dist/` als StaticFiles aus
- [ ] Route `/` zeigt React-App (Production Build)
- [ ] API-Routen `/api/` bleiben unveraendert
- [ ] Vite Dev Server (Port 5173) proxied `/api/` zu Port 8000

Status: offen
Phase: 2, Sprint 1
Prioritaet: hoch

---

### REQ-1203 | API-Client in TypeScript
Als Entwickler
moechte ich einen typsicheren API-Client der alle FastAPI-Endpunkte abdeckt
damit keine manuellen fetch-Aufrufe im Frontend-Code noetig sind.

Akzeptanzkriterien:
- [ ] TypeScript-Interfaces fuer alle Pydantic-Schemas (Project, Category, Value, Generation)
- [ ] Axios-Client mit Fehlerbehandlung
- [ ] Alle bestehenden REST-Endpunkte abgedeckt
- [ ] Unit-Tests fuer API-Client (Vitest + Mock)

Status: offen
Phase: 2, Sprint 1
Prioritaet: hoch

---

### REQ-1204 | Projektliste als React-Komponente
Als Nutzer
moechte ich Projekte anlegen, umbenennen und loeschen ohne Seitenreload
damit die Bedienung fluessig und reaktiv ist.

Akzeptanzkriterien:
- [ ] Projektliste wird per API geladen
- [ ] Neues Projekt anlegen (Modal oder Inline-Form)
- [ ] Projekt loeschen mit Bestaetigungsdialog
- [ ] Zustand wird automatisch aktualisiert (kein manueller Reload)

Status: offen
Phase: 2, Sprint 1
Prioritaet: hoch

---

### REQ-1205 | Windows-First Entwicklungsumgebung
Als Entwickler
moechte ich das Frontend auf Windows entwickeln und starten koennen
damit keine Linux/RPi-Abhaengigkeiten in Phase 2 benoetigt werden.

Akzeptanzkriterien:
- [ ] `Start.bat` fuer Windows erstellt (Backend + Frontend)
- [ ] README.md mit Windows-Installationsanleitung aktualisiert
- [ ] Node.js 20 LTS als Voraussetzung dokumentiert
- [ ] Kein Shell-Script (.sh) Pflege in Phase 2

Status: offen
Phase: 2, Sprint 1
Prioritaet: mittel


---
## Phase 2 Sprint 3 – Office-Bedienung + UX

### REQ-1209 | Drag & Drop Sortierung fuer Kategorien
Als Nutzer
moechte ich Kategorien per Drag & Drop neu anordnen koennen
damit ich die wichtigsten Kategorien an erster Stelle sehen kann.

Akzeptanzkriterien:
- [ ] Kategorien sind per Drag & Drop sortierbar
- [ ] Reihenfolge wird per API gespeichert (PATCH /categories/reorder)
- [ ] Visuelle Rueckmeldung waehrend des Ziehens

Status: offen
Phase: 2, Sprint 3
Prioritaet: hoch

---

### REQ-1210 | Keyboard-Shortcuts
Als Nutzer
moechte ich haeufige Aktionen per Tastatur ausfuehren koennen
damit ich schneller arbeiten kann ohne die Maus zu benutzen.

Akzeptanzkriterien:
- [ ] CTRL+N: Fokus auf Neue-Kategorie-Eingabefeld
- [ ] DEL: Selektiertes Element loeschen (mit Bestaetigung)
- [ ] F2: Selektiertes Element umbenennen
- [ ] ESC: Aktuelle Eingabe abbrechen / Dialog schliessen

Status: offen
Phase: 2, Sprint 3
Prioritaet: hoch

---

### REQ-1211 | Kontextmenue (Rechtsklick)
Als Nutzer
moechte ich per Rechtsklick auf Kategorien und Werte ein Kontextmenue oeffnen koennen
damit ich Aktionen schnell ohne Navigation ausfuehren kann.

Akzeptanzkriterien:
- [ ] Rechtsklick auf Kategorie: Umbenennen / Wert hinzufuegen / Loeschen
- [ ] Rechtsklick auf Wert: Umbenennen / Loeschen
- [ ] Kontextmenue schliesst bei Klick ausserhalb

Status: offen
Phase: 2, Sprint 3
Prioritaet: hoch

---

### REQ-1212 | Toast-Benachrichtigungen
Als Nutzer
moechte ich nach jeder Aktion eine kurze Rueckmeldung sehen
damit ich weiss ob die Aktion erfolgreich war.

Akzeptanzkriterien:
- [ ] Erfolg: Gruene Toast-Nachricht (3 Sekunden sichtbar)
- [ ] Fehler: Rote Toast-Nachricht (5 Sekunden sichtbar)
- [ ] Mehrere Toasts stacken sich

Status: offen
Phase: 2, Sprint 3
Prioritaet: mittel

---

### REQ-1213 | Inline-Umbenennen + Werte-Zaehler
Als Nutzer
moechte ich Kategorien und Werte durch Doppelklick umbenennen
und die Anzahl der Werte pro Kategorie auf einen Blick sehen.

Akzeptanzkriterien:
- [ ] Doppelklick auf Kategoriename -> Inline-Textfeld
- [ ] ENTER bestaetigt, ESC bricht ab
- [ ] Badge mit Werte-Anzahl neben Kategoriename
- [ ] PATCH /categories/{cid}/rename Endpunkt

Status: offen
Phase: 2, Sprint 3
Prioritaet: mittel

---

### REQ-1214 | Testfalltabelle sortierbar
Als Nutzer
moechte ich die Testfalltabelle durch Klick auf Spaltenheader sortieren koennen
damit ich bestimmte Wertekombinationen schnell finden kann.

Status: offen
Phase: 2, Sprint 3
Prioritaet: niedrig


---

### REQ-2001 | Generierungshistorie
Als Nutzer
moechte ich bereits generierte Kombinationen wieder aufrufen koennen
damit ich nicht jedes Mal neu generieren muss.

Akzeptanzkriterien:
- [ ] GET /api/projects/{pid}/generations liefert Liste aller Generierungen
- [ ] Jeder Eintrag: id, strategy, created_at, testcase_count
- [ ] Klassische Ansicht: Dropdown in /ui/generate mit HTMX-History
- [ ] React-Ansicht: Dropdown im TestCasePanel
- [ ] Klick auf Eintrag laedt die Testfaelle dieser Generierung

Status: implementiert
Phase: 2, Sprint 5
Prioritaet: hoch
REQ-ID: REQ-2001

---

### REQ-2002 | Bulk-Delete Projekte
Als Nutzer
moechte ich mehrere Projekte gleichzeitig auswählen und loeschen koennen
damit ich effizienter aufräumen kann.

Akzeptanzkriterien:
- [ ] Checkboxen in der Projektliste (beide Views)
- [ ] "Alle auswählen" Checkbox im Header
- [ ] POST /api/projects/bulk-delete: loescht ohne Generierungen, blockiert wenn vorhanden
- [ ] POST /api/projects/bulk-delete-force: loescht inkl. aller abhaengigen Daten
- [ ] Response enthaelt deleted-Count und blocked-Liste
- [ ] Klassische Ansicht: HTMX Bulk-Formular
- [ ] React-Ansicht: Bulk-Aktionen Toolbar

Status: implementiert
Phase: 2, Sprint 5
Prioritaet: mittel
REQ-ID: REQ-2002

---

### REQ-0011 | View-Synchronitätspflicht
Als Entwickler
muss ich sicherstellen dass klassische (HTMX) und neue (React) Ansicht
funktional immer synchron sind.

Akzeptanzkriterien:
- [ ] Jedes Feature ist in beiden Views implementiert
- [ ] Jeder Bugfix wird in beiden Views geprueft
- [ ] Tests decken beide Views ab
- [ ] Abweichung > 1 Sprint: STOP, Architect-Entscheidung

Status: aktiv (Projektregel)
Phase: alle
Prioritaet: kritisch
REQ-ID: REQ-0011

---

### REQ-2003 | Datenklassen – Wiederverwendbare Aequivalenzklassen-Bibliothek
Als Nutzer
moechte ich typische Aequivalenzklassen (z.B. Statuswerte, Gewichtsklassen) einmalig definieren
und in beliebigen Projekten und Kategorien wiederverwenden koennen.

Akzeptanzkriterien:
- [ ] Datenklassen haben Name, Typ (text/number/date/time/boolean/email/freetext), Beschreibung
- [ ] Werte werden beim Eingeben gegen den Typ validiert (z.B. Datum-Format, numerisch)
- [ ] GET/POST/DELETE /api/dataclasses CRUD
- [ ] GET/POST /api/dataclasses/{id}/values + DELETE /api/dataclasses/values/{vid}
- [ ] POST /api/categories/{cid}/apply-dataclass – uebernimmt alle Werte in Kategorie (ohne Duplikate)
- [ ] Klassische Ansicht: /ui/dataclasses mit HTMX
- [ ] React-Ansicht: /app/dataclasses + DataClassDialog im Kategorienbaum (Rechtsklick)
- [ ] Navigation in beiden Views

Status: implementiert
Phase: 2, Sprint 5
Prioritaet: hoch
REQ-ID: REQ-2003
---

# PHASE 3 – React-First & HTMX-Ablösung
**Entscheidung (2026-06-29):** Die klassische HTMX-Ansicht wird vollständig durch React ersetzt.
Alle neuen Features werden ausschließlich in React implementiert. REQ-0011 (View-Synchronitätspflicht) ist damit aufgehoben.

---

## EPIC-03 – Navigationsstruktur & Shell

### REQ-3001 | Einheitliche Navigationsleiste (Top-Nav)
**Titel:** Konsistente Navigationsleiste in jeder Ansicht
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 1
**User Story:**
Als Nutzer
möchte ich in jedem Fenster dieselbe Navigationsleiste oben sehen
damit ich ohne Umwege zwischen Projekten, Datenklassen, Generierungen, API-Docs und Einstellungen wechseln kann.
**Akzeptanzkriterien:**
- Nav-Bar enthält: Projekte | Datenklassen | Generierungen | API-Docs | Einstellungen
- Aktiver Tab ist visuell hervorgehoben
- Nav-Bar erscheint auf allen React-Seiten
- Einstellungen-Seite ist vorerst eine Leerseite mit Platzhalter
**Abhängigkeiten:** –

---

### REQ-3002 | Einstellungen-Seite (Leerseite)
**Titel:** Einstellungen-Platzhalter
**Priorität:** Could
**Status:** Planned
**Phase:** 3, Sprint 1
**User Story:**
Als Nutzer
möchte ich eine Einstellungen-Seite aufrufen können
damit zukünftige Konfigurationsoptionen einen festen Platz haben.
**Akzeptanzkriterien:**
- Route /app/settings existiert
- Seite zeigt "Einstellungen – coming soon"
**Abhängigkeiten:** REQ-3001

---

## EPIC-04 – Regellogik in React

### REQ-3003 | Regeln anlegen in React (Verboten / Abhängig / Kombinieren)
**Titel:** Regeleditor in der React-Projektansicht
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 2
**User Story:**
Als Tester
möchte ich direkt in der React-Ansicht Regeln vom Typ „Verboten (Paar nicht gemeinsam)", „Abhängig (Wenn/Dann)" und „Kombinieren (Fan-out)" anlegen können
damit ich die Geschäftslogik vollständig in der neuen Oberfläche nutzen kann ohne die klassische Ansicht zu benötigen.
**Akzeptanzkriterien:**
- Neuer Block oberhalb der Regelanzeige: Regel anlegen
- Typ-Auswahl per Dropdown: Verboten | Abhängig | Kombinieren
- Kategorie-Auswahl per Dropdown (aus aktuellem Projekt)
- Werte-Auswahl per Dropdown (zu gewählter Kategorie)
- Bestehende Regellogik aus dem Backend wird wiederverwendet (kein neues Backend nötig)
- Gespeicherte Regeln erscheinen direkt in der Regelanzeige darunter
**Abhängigkeiten:** –

---

### REQ-3004 | Regelwiderspruch-Erkennung
**Titel:** Sofortige Anzeige bei widersprechenden Regeln
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 2
**User Story:**
Als Tester
möchte ich sofort beim Speichern einer Regel gewarnt werden, wenn diese einer bestehenden Regel widerspricht
damit ich inkonsistente Regelsätze vermeiden kann.
**Akzeptanzkriterien:**
- Beim Speichern einer Regel wird der Regelsatz auf Widersprüche geprüft
- Widerspruch wird direkt im Regeleditor angezeigt: „Regelwiderspruch mit Regel [Regelnummer]"
- Die widersprüchliche Regel ist in der Regelanzeige hervorgehoben
- Speichern ist trotzdem möglich (Warnung, kein Hard-Block)
**Abhängigkeiten:** REQ-3003

---

### REQ-3005 | Generierung mit Regeln (opt-in)
**Titel:** Checkbox „Mit Regeln generieren"
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 2
**User Story:**
Als Tester
möchte ich beim Starten der Generierung wählen können ob die definierten Regeln berücksichtigt werden
damit ich sowohl regelfreie als auch regelkonforme Kombinationen erzeugen kann.
**Akzeptanzkriterien:**
- Checkbox „Mit Regeln generieren" im Generierungs-Panel (Default: aktiviert wenn Regeln vorhanden)
- Wenn aktiviert: Regeln werden beim Generieren angewendet
- Wenn deaktiviert: Generierung ignoriert alle Regeln (bisheriges Verhalten)
**Abhängigkeiten:** REQ-3003

---

### REQ-3006 | Nachträgliche Regelprüfung generierter Kombinationen
**Titel:** Regelprüfung auf generierte Testfälle
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 3
**User Story:**
Als Tester
möchte ich nach der Generierung prüfen lassen ob alle Regeln eingehalten wurden
damit ich Lücken (fehlende Pflicht-Kombinationen) und Verstöße (verbotene Paare) erkennen kann.
**Akzeptanzkriterien:**
- „Regelprüfung"-Button in der Generierungsansicht
- Prüfung erkennt fehlende Abhängigkeits-Kombinationen und fügt diese hinzu
- Prüfung erkennt Verboten-Verletzungen und markiert diese rot
- Ergebnis: Zusammenfassung „X Kombinationen hinzugefügt, Y Verletzungen gefunden"
**Abhängigkeiten:** REQ-3005

---

## EPIC-05 – Wert-Eigenschaften & Default-Markierung

### REQ-3007 | Wert-Eigenschaften: Risiko, Datentyp, Fehlerwert
**Titel:** Erweiterte Wert-Eigenschaften in der Kategorie-Ansicht
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 2
**User Story:**
Als Tester
möchte ich für jeden Wert in einer Kategorie die Eigenschaften Risiko (numerisch), Datentyp (Dropdown) und Fehlerwert (boolean) direkt in der Ansicht sehen und bearbeiten können
damit ich die Testfall-Gewichtung und Klassifikation präzise steuern kann.
**Akzeptanzkriterien:**
- Jeder Wert zeigt inline: Risiko (Zahl 1-10), Datentyp (Dropdown: text/number/date/...), Fehlerwert (Checkbox)
- Werte können direkt in der Tabellenzeile bearbeitet werden (kein extra Dialog)
- Änderungen werden sofort gespeichert (PATCH API)
**Abhängigkeiten:** –

---

### REQ-3008 | Default-Wert Markierung
**Titel:** Wert als „Default" markieren für Lineare Expansion
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 2
**User Story:**
Als Tester
möchte ich einen Wert pro Kategorie als „Default" markieren können (per Rechtsklick oder Tastenkombination)
damit die Lineare Expansion diesen Wert als Basislinie verwendet.
**Akzeptanzkriterien:**
- Rechtsklick auf Wert → Kontextmenü-Eintrag „Als Default markieren"
- Default-Wert ist visuell markiert (z.B. ★-Symbol)
- Wenn kein Default gesetzt: erster Eintrag in der Liste gilt automatisch als Default
- Backend: PATCH /api/values/{id} mit default-Flag
**Abhängigkeiten:** REQ-3007

---

## EPIC-06 – Generierungsverwaltung

### REQ-3009 | Karteireiter „Generierte Testfälle"
**Titel:** Eigener Reiter für alle Generierungen eines Projekts
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 1
**User Story:**
Als Tester
möchte ich alle Generierungen meines Projekts in einem eigenen Karteireiter sehen können
damit ich Generierungen verwalten (umbenennen, löschen, exportieren) kann ohne die aktuelle Generierungsansicht zu verlassen.
**Akzeptanzkriterien:**
- Neuer Tab „Generierte Testfälle" in der Projektdetail-Ansicht
- Liste aller Generierungen: Name, Strategie, Datum, Testfall-Anzahl
- Aktionen je Generierung: Umbenennen (Inline), Löschen (mit Bestätigung), Exportieren (JSON/Excel/CSV)
- Die Funktion „Vorherige Generierung laden" im Tab „Testfall-Generierung" bleibt unverändert
**Abhängigkeiten:** REQ-2001

---

## EPIC-07 – Datenklassen überarbeiten

### REQ-3010 | Datenklassen-Ansicht: System + User-Klassen
**Titel:** Datenklassen-Ansicht überarbeiten (System & User getrennt, nicht Projekt-gebunden)
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 1
**User Story:**
Als Nutzer
möchte ich in der Datenklassen-Ansicht System-Datenklassen und eigene User-Datenklassen separat sehen und verwalten können
damit ich die vorgefertigten Klassen von meinen eigenen unterscheiden kann, ohne dass Projekt-Kategorien dort auftauchen.
**Akzeptanzkriterien:**
- Datenklassen-Ansicht zeigt zwei Bereiche: „System-Datenklassen" (read-only, nicht löschbar) und „Meine Datenklassen" (CRUD)
- Projekt-Kategorien erscheinen NICHT in dieser Ansicht
- User-Datenklassen (aus dieser Ansicht) sind in der Kategorie-Ansicht als „Datenklasse einfügen" verfügbar
- System-Datenklassen ebenfalls als „Datenklasse einfügen" verfügbar
- Bestehende Datenklassen-API wird wiederverwendet
**Abhängigkeiten:** REQ-2003

---

## EPIC-08 – HTMX-Ablösung & Bereinigung

### REQ-3011 | Klassische HTMX-Ansicht archivieren
**Titel:** HTMX-Ansicht vollständig entfernen
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 4 (nach Abschluss aller anderen Sprint-3-Features)
**User Story:**
Als Entwickler
möchte ich die klassische HTMX-Ansicht archivieren
nachdem alle Funktionalitäten in React übernommen wurden
damit der Codebase schlanker wird und kein Doppel-Maintenance nötig ist.
**Akzeptanzkriterien:**
- Alle HTMX-Templates nach archive/YYYY-MM-DD/ verschoben
- HTMX-Router-Registrierungen aus main.py entfernt
- ui_projects.py, ui_generate.py, ui_rules.py, ui_dataclasses.py archiviert
- Alle zugehörigen Tests aktualisiert
- React-Ansicht ist vollständiger Ersatz (alle Features vorhanden)
- REQ-0011 als „aufgehoben" markiert
**Abhängigkeiten:** REQ-3003, REQ-3007, REQ-3009, REQ-3010

---

### REQ-3012 | Alt+N Shortcut entfernen
**Titel:** Alt+N Tastenkombination aus Kategorie-Ansicht entfernen
**Priorität:** Could
**Status:** Planned
**Phase:** 3, Sprint 1
**User Story:**
Als Entwickler
möchte ich den Alt+N-Shortcut entfernen
damit keine unnötige Tastenbelegung existiert.
**Akzeptanzkriterien:**
- useKeyboardShortcuts: „alt+n" entfernt
- Placeholder-Text ohne Shortcut-Hinweis
- Hilfe-Text aktualisiert
**Abhängigkeiten:** –

---

## EPIC-09 – Regel-Qualität & Transparenz

### REQ-3013 | Regeln benennen
**Titel:** Editierbare Regelbezeichnungen pro Projekt
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
möchte ich jeder Regel in einem Projekt einen eigenen Namen geben können (z. B. „Chrome nur Windows", „Keine Linux-Tests")
damit Widerspruchs- und Duplikatmeldungen verständlich auf konkrete Regeln verweisen statt auf abstrakte IDs.
**Akzeptanzkriterien:**
- Default-Name beim Anlegen: „{N}. Regel" (N = laufende Nummer im Projekt)
- Regelname inline editierbar (Doppelklick oder Stift-Icon)
- PATCH /api/projects/{pid}/rules/{rid}/rename Endpunkt
- Widerspruchs-Meldung REQ-3004 verwendet Regelname statt ID: „Regelwiderspruch mit ‚{Name}'"
- Duplikat-Meldung REQ-3014 verwendet Regelname
**Abhängigkeiten:** REQ-3003

---

### REQ-3014 | Duplikat-Erkennung bei Regeln
**Titel:** Prüfung auf identische Wertekombinationen in Regeln
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
möchte ich beim Anlegen einer Regel sofort gewarnt werden, wenn dieselbe Wertekombination bereits in einer anderen Regel definiert ist
damit redundante Regeln vermieden werden und der Regelsatz übersichtlich bleibt.
**Akzeptanzkriterien:**
- Backend-Prüfung in _detect_conflicts(): gleiche (type, if_cat, if_val, then_cat, then_val/vals) → Duplikat
- Meldung: „Wertekombination bereits in Regel ‚{Name}' enthalten"
- Wird als Warnung angezeigt (kein Hard-Block)
- RuleRead-Response enthält conflict_with (wie REQ-3004)
**Abhängigkeiten:** REQ-3013

---

### REQ-3015 | Toter-Wert-Warnung
**Titel:** Hinweis wenn ein Wert durch Regeln nicht mehr erreichbar ist
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
möchte ich einen Hinweis erhalten wenn eine Kombination aus exclude-Regeln bewirkt, dass ein Wert in keinem einzigen Testfall mehr vorkommen kann
damit ich unrealisierbare Regelsets frühzeitig erkenne.
**Akzeptanzkriterien:**
- Prüfung nach jeder Regeländerung: Gibt es Werte, die durch alle aktiven exclude-Regeln ausgeschlossen sind?
- Meldung: „Wert ‚{Wertname}' in Kategorie ‚{Kategoriename}' ist durch aktive Regeln nicht mehr für Testfälle verfügbar."
- Hinweis nur für exclude-Regeln (dependency/combine lösen keinen toten Wert aus)
- Vereinfachte Prüflogik: Ein Wert gilt als tot, wenn für jede seiner möglichen Kombinationen mindestens eine exclude-Regel greift
- Wert bleibt in der Liste, ist aber visuell als „blockiert" markiert
**Abhängigkeiten:** REQ-3013

---

## EPIC-10 – Manuelle Kombinatorik

### REQ-3016 | Manuelle Testfall-Zusammenstellung
**Titel:** Neue Kombinatorik-Strategie: Manuell
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
möchte ich Testfallkombinationen selbst Zeile für Zeile zusammenstellen können
damit ich gezielt spezifische Szenarien abdecken kann, die kein Algorithmus automatisch erzeugen würde.
**Akzeptanzkriterien:**
- Neue Strategie „manual" in der Generierungsansicht (eigener Tab oder Strategie-Option)
- Schaltfläche „Testfall hinzufügen": neue leere Zeile wird eingefügt
- Pro Kategorie: Dropdown zur Wertauswahl
- Schaltfläche „Testfall löschen" pro Zeile
- Speichern erzeugt eine Generation mit strategy=„manual" in der DB
- Manuelle Testfälle erscheinen in Generierungen-Übersicht und können exportiert werden
**Abhängigkeiten:** –

---

## EPIC-11 – UX-Feinschliff

### REQ-3017 | Spaltenüberschriften in der Kategorie-Werteliste
**Titel:** Sichtbare Header für Wert-Eigenschaften
**Priorität:** Should
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester (Erstnutzer)
möchte ich beim Blick auf eine Kategorie sofort verstehen, was die Felder neben jedem Wert bedeuten
damit ich Risiko, Typ und Fehlerwert-Checkbox intuitiv nutzen kann.
**Akzeptanzkriterien:**
- Über der Werteliste erscheinen Spalten-Header: „Wert | Risiko | Typ | Fehlerwert"
- Header nur sichtbar wenn die Kategorie aufgeklappt ist und mindestens ein Wert vorhanden
- Header sind nicht interaktiv (rein beschriftend)
**Abhängigkeiten:** REQ-3007

---

## EPIC-12 – Fehlerwert-Generierungslogik

### REQ-3018 | Fehlerwert-Werte immer am Ende, max. 1 pro Testfall
**Titel:** Fehlerfall-konforme Testfall-Sortierung bei Generierung
**Priorität:** Must
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester (ISTQB-konform)
möchte ich dass Testfälle mit Fehlerwert-Werten (allowed=False) immer am Ende der generierten Liste stehen und niemals mehr als einen Fehlerwert pro Testfall enthalten
damit ich positiv-Testfälle zuerst und gezielt negative Testfälle am Ende durchführen kann.
**Akzeptanzkriterien:**
- Nach Generierung: Testfälle ohne Fehlerwerte kommen zuerst
- Testfälle mit genau einem Fehlerwert kommen danach (sortiert nach Fehlerwert-Kategorie)
- Testfälle mit mehr als einem Fehlerwert: Falls ein Fehlerwert durch eine aktive Regel erzwungen ist, übersteuert die Regel. Ansonsten: Testfall wird aufgeteilt in N Testfälle mit je 1 Fehlerwert.
- Gilt für alle Strategien außer „manual"
- Backend-Postprocessing-Funktion: `apply_error_value_constraints(cases, categories_with_values)`
**Abhängigkeiten:** REQ-3007 (Fehlerwert-Flag)


---

## EPIC-13 - Sprint-5-Backlog

### REQ-3019 | Projekt-Vorlagen
**Titel:** Projekt als Vorlage speichern und daraus neue Projekte erzeugen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich ein bestehendes Projekt als Vorlage markieren und daraus neue Projekte erzeugen koennen
damit ich wiederkehrende Testdesign-Strukturen nicht jedes Mal neu anlegen muss.
**Akzeptanzkriterien:**
- Ein Projekt kann als Vorlage gespeichert werden
- Beim Erzeugen aus Vorlage werden Kategorien, Werte und Regeln uebernommen
- Generierungshistorie und projektspezifische Ergebnisse werden NICHT uebernommen
- Vorlagen sind in der Projektanlage separat auswaehlbar
**Abhaengigkeiten:** REQ-0200, REQ-0204, REQ-3003

---

### REQ-3020 | Regelsets exportieren/importieren
**Titel:** Regelkonfiguration projektuebergreifend als JSON austauschen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester
moechte ich Regelsets eines Projekts exportieren und in ein anderes Projekt importieren koennen
damit ich fachliche Regelwerke wiederverwenden kann ohne komplette Projekte zu duplizieren.
**Akzeptanzkriterien:**
- Export erzeugt JSON nur fuer Regeln des gewaehlten Projekts
- Import prueft, ob referenzierte Kategorien/Werte im Zielprojekt vorhanden sind
- Nicht aufloesbare Referenzen werden als verstaendliche Warnung angezeigt
- Erfolgreich importierte Regeln erscheinen direkt in der Regeluebersicht
**Abhaengigkeiten:** REQ-3003, REQ-3013

---

### REQ-3021 | Projekt-Dashboard
**Titel:** Uebersichtsseite mit Projektkennzahlen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich pro Projekt eine kompakte Uebersichtsseite mit zentralen Kennzahlen sehen
damit ich den Projektzustand schnell erfassen kann.
**Akzeptanzkriterien:**
- Dashboard zeigt mindestens: Anzahl Kategorien, Werte, Regeln, Generierungen
- Dashboard zeigt offene Warnungen getrennt an
- Dashboard ist aus der Projektansicht direkt erreichbar
- Kennzahlen aktualisieren sich nach Aenderungen ohne manuellen Reload
**Abhaengigkeiten:** REQ-0200, REQ-2001, REQ-3003

---

### REQ-3022 | Fortschritts-Indikator
**Titel:** Ampel-Status pro Projekt
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich pro Projekt einen einfachen Ampel-Status sehen
damit ich problematische Projekte sofort erkenne.
**Akzeptanzkriterien:**
- Status Gruen: keine offenen Warnungen
- Status Gelb: mindestens eine Warnung, aber keine harte Inkonsistenz
- Status Rot: Regelwidersprueche oder blockierende Konfigurationsprobleme vorhanden
- Der Status wird im Dashboard und in der Projektliste angezeigt
**Abhaengigkeiten:** REQ-3021, REQ-3004, REQ-3015

---

### REQ-3023 | Test-Coverage-Analyse
**Titel:** Prozentuale Abdeckungsanzeige nach Generierung
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester
moechte ich nach einer Generierung sehen, wie viel des theoretisch moeglichen Kombinationsraums abgedeckt ist
damit ich die Aussagekraft der erzeugten Testfaelle besser einschaetzen kann.
**Akzeptanzkriterien:**
- Nach jeder Generierung wird eine Coverage-Kennzahl in Prozent angezeigt
- Die Berechnung bezieht nur aktive und erlaubte Werte ein
- Die Anzeige nennt erzeugte Testfaelle und theoretisch moegliche Kombinationen
- Bei sehr grossen Kombinationsraeumen darf die Berechnung als Naeherung gekennzeichnet werden
**Abhaengigkeiten:** REQ-0800, REQ-0801, REQ-0802, REQ-3009

---

### REQ-3024 | Testfall-Kommentar
**Titel:** Freitext-Kommentar pro Testfall
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester
moechte ich jedem Testfall einen Kommentar hinzufuegen koennen
damit ich Hinweise wie Priorisierung, bekannte Bugs oder Testnotizen direkt am Testfall speichern kann.
**Akzeptanzkriterien:**
- Jeder Testfall besitzt ein optionales Freitext-Kommentarfeld
- Kommentare sind in der Testfallansicht sichtbar und editierbar
- Kommentare werden mit der Generation persistiert
- Kommentare sind in Exporten optional mit ausgebbar
**Abhaengigkeiten:** REQ-0900, REQ-3009

---

### REQ-3025 | Generierungs-Vergleich
**Titel:** Zwei Generierungen desselben Projekts vergleichen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester
moechte ich zwei Generierungen desselben Projekts nebeneinander vergleichen koennen
damit ich erkenne, welche Testfaelle neu hinzugekommen, entfallen oder unveraendert sind.
**Akzeptanzkriterien:**
- Nutzer kann zwei Generierungen desselben Projekts auswaehlen
- Vergleich zeigt mindestens: nur links, nur rechts, in beiden vorhanden
- Unterschiede sind visuell hervorgehoben
- Vergleich funktioniert auch fuer verschiedene Strategien desselben Projekts
**Abhaengigkeiten:** REQ-2001, REQ-3009

---

### REQ-3026 | Fehlerwert-Report
**Titel:** Separater Export nur fuer Fehlerwert-Testfaelle
**Prioritaet:** Could
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester
moechte ich Fehlerwert-Testfaelle separat exportieren koennen
damit ich Negativtests unabhaengig von Positivtests weitergeben oder ausfuehren kann.
**Akzeptanzkriterien:**
- Exportfilter "Nur Fehlerwert-Testfaelle" ist auswaehlbar
- Export enthaelt nur Testfaelle mit mindestens einem Fehlerwert
- Report kann zusaetzlich zur Gesamtausgabe erzeugt werden
- Anzahl exportierter Fehlerwert-Testfaelle wird angezeigt
**Abhaengigkeiten:** REQ-3018, REQ-1000, REQ-1002

---

### REQ-3027 | Massenimport von Kategorien
**Titel:** CSV-Import fuer Kategorien und Werte
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich viele Kategorien und Werte per CSV importieren koennen
damit ich grosse Testmodelle schneller anlegen kann.
**Akzeptanzkriterien:**
- CSV-Import legt Kategorien und zugehoerige Werte in einem Projekt an
- Import unterstuetzt Vorschau vor dem Speichern
- Bereits vorhandene Kategorien/Werte werden als Konflikt oder Merge-Fall behandelt
- Importer meldet Zeilenfehler verstaendlich mit Zeilennummer zurueck
**Abhaengigkeiten:** REQ-0300, REQ-0302

---

### REQ-3028 | Wert-Sortierung per Drag & Drop
**Titel:** Reihenfolge von Werten innerhalb einer Kategorie per Drag & Drop aendern
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich Werte innerhalb einer Kategorie per Drag & Drop sortieren koennen
damit fachlich wichtige oder haeufig genutzte Werte oben stehen.
**Akzeptanzkriterien:**
- Werte innerhalb einer geoeffneten Kategorie sind per Drag & Drop umsortierbar
- Neue Reihenfolge bleibt nach Reload erhalten
- Visuelle Rueckmeldung waehrend des Ziehens ist vorhanden
- Sortierung wirkt sich auf Darstellung und Default-Auswahlreihenfolge aus
**Abhaengigkeiten:** REQ-0302, REQ-3007

---

### REQ-3029 | Keyboard-Navigation in Generierungstabelle
**Titel:** Tabellenbedienung per Pfeiltasten, Tab und Enter
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Power-User
moechte ich mich in der Generierungstabelle mit der Tastatur bewegen und Werte aendern koennen
damit ich ohne Maus schneller arbeiten kann.
**Akzeptanzkriterien:**
- Pfeiltasten bewegen den Fokus zwischen editierbaren Zellen
- Tab und Shift+Tab springen horizontal weiter bzw. zurueck
- Enter oeffnet Bearbeitung oder bestaetigt Auswahl
- Fokuszustand ist jederzeit sichtbar
**Abhaengigkeiten:** REQ-0900, REQ-0901

---

### REQ-3030 | Wert-Suche in Kategorien
**Titel:** Suchfeld fuer grosse Wertelisten
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer
moechte ich Werte innerhalb einer Kategorie ueber ein Suchfeld filtern koennen
damit ich auch bei grossen Kategorien schnell den gewuenschten Wert finde.
**Akzeptanzkriterien:**
- Jede Kategorie kann ein lokales Suchfeld fuer ihre Werte anzeigen
- Filterung erfolgt ohne Seitenreload
- Trefferzahl oder Leerzustand wird angezeigt
- Der Filter veraendert nicht die gespeicherte Wertemenge
**Abhaengigkeiten:** REQ-0302, REQ-3007

---

### REQ-3045 | Theme: Normal
**Titel:** Standard Hell-Theme
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer moechte ich ein helles Standard-Theme nutzen damit die App benutzerfreundlich und fokussiert ist.
**Akzeptanzkriterien:**
- Theme ist vorgespeichert und Nutzer kann es waehlen
- Kontrastverhaeltnisse nach WCAG 2.1 AA Standard
- Alle UI-Komponenten mit Theme korrekt gestylt

---

### REQ-3046 | Theme: Dark
**Titel:** Dunkles Theme mit System-Sync
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5

---

### REQ-3047 | Theme: Steampunk
**Titel:** Visuell interessantes Steampunk-Theme
**Prioritaet:** Could
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5

---

### REQ-3048 | Theme: Rainbow
**Titel:** Buntes Rainbow-Theme
**Prioritaet:** Could
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5

---

### REQ-3049 | Theme: Heavy Metal
**Titel:** Extremes Schwarz/Rot Heavy-Metal-Theme
**Prioritaet:** Could
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5

---

### REQ-3050 | Risikoabdeckung pro Testfall
**Titel:** Risikogewicht-Summe in Testfalltabelle anzeigen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich sehen, wie viel Risiko jeder Testfall abdeckt damit ich Prioritaeten einschaetzen kann.
**Akzeptanzkriterien:**
- Jeder Testfall zeigt seine kumulative Risikoabdeckung (Summe der risk_weight aller enthaltenen Werte)
- Wert ist in Testfalltabelle als separate Spalte sichtbar
- Sortierung nach Risiko ist moeglich

---

### REQ-3051 | Risikoabdeckung-Prozentsatz
**Titel:** Prozentuale Risikoabdeckung pro Generierung
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich nach einer Generierung sehen, wie viel Prozent des Gesamt-Risikos abgedeckt sind damit ich die Qualitaet schnell einschaetzen kann.
**Akzeptanzkriterien:**
- Nach Generierung wird ein Risikoabdeckungs-Prozentsatz angezeigt
- Farbiges Badge: Gruen >= 80%, Gelb 50–79%, Rot < 50%
- Absolute Risikoabdeckung = Summe der risk_weight aller generierten Testfälle / theoretisches All-Combinations-Maximum
- Berechnung basiert auf Summe der risk_weight aller erzeugten Testfälle geteilt durch das theoretische All-Combinations-Maximum aller möglichen Wertkombinationen (dies ergänzt die bisherige generische Formulierung)

---

### REQ-3052 | Tabellenansicht mit Sortierung und CSV-Export
**Titel:** Testfallansicht mit sortierbare Spalten, Sticky Header, CSV-Export
**Prioritaet:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich Testfaelle in einer sortierbaren Tabelle mit Export sehen damit ich schnell die Daten nutzen kann.
**Akzeptanzkriterien:**
- Tabelle hat Sticky Header (bleibt sichtbar beim Scrollen)
- Spalten sind nach Klick auf Header sortierbar (aufsteigend/absteigend)
- CSV-Export Button exportiert alle sichtbaren Testfaelle

---

### REQ-3053 | Undo/Redo
**Titel:** STRG+Z / STRG+Y Funktionalität für Testfall-Änderungen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Power-User moechte ich mit STRG+Z/STRG+Y Testfall-Aenderungen rueckgaengig machen/wiederherstellen damit ich schneller arbeiten kann.
**Akzeptanzkriterien:**
- STRG+Z macht letzte Aenderung rueckgaengig (mindestens 50 Schritte)
- STRG+Y stellt rueckgaengig gemachte Aenderung wieder her
- Undo/Redo-Stack wird pro Projekt beibehalten
- Visuelle Anzeige des Undo/Redo-Status

---

### REQ-3054 | Tastaturnavigation
**Titel:** Vollständige Tastaturnavigation in Testfalltabelle
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich Testfaelle nur mit Tastatur bearbeiten koennen damit ich effizienter ohne Maus arbeite.
**Akzeptanzkriterien:**
- Pfeiltasten bewegen Fokus zwischen Zellen
- Enter oeffnet Bearbeitung einer Zelle
- Delete loescht Testfall (mit Bestaetigung)
- F2 startet Inline-Bearbeitung
- Escape bricht Bearbeitung ab
- ARIA-Attribute sind korrekt gesetzt
- Fokusreihenfolge ist logisch und nachvollziehbar

---

### REQ-3062 | Dark-Mode System-Sync
**Titel:** System-Einstellung für Hell/Dunkel-Theme nutzen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Nutzer moechte ich dass die App automatisch mein OS-Theme (Hell/Dunkel) nutzt damit ich nicht manuell umschalten muss.
**Akzeptanzkriterien:**
- App erkennt OS `prefers-color-scheme` Einstellung
- Theme wird automatisch angepasst, wenn OS-Einstellung sich aendert
- Nutzer kann manuell überschreiben (Einstellungen > Theme > Manuell auswählen)
- Einstellung wird lokal persistent gespeichert

---

### REQ-3063 | Fehlerwert-Testfälle visuell markieren
**Titel:** Rote Hervorhebung von Testfällen mit Fehlerwerten
**Prioritaet:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich Testfaelle mit Fehlerwerten (Negativ-Tests) sofort visuell erkennen damit ich diese gezielt priorisieren kann.
**Akzeptanzkriterien:**
- Testfaelle mit mindestens einem Fehlerwert haben roten Hintergrund in der Tabelle
- Farbe ist anpassbar ueber Theme-System
- Export behaelt die Markierung bei

---

### REQ-3064 | Multi-Range BVA
**Titel:** Grenzwertanalyse mit mehreren Äquivalenzklassen und erlaubt/nicht-erlaubt Markierung
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 5
**User Story:**
Als Tester moechte ich mehrere Grenzwertbereiche in einer Kategorie definieren koennen damit ich komplexe numerische Domänen abdecke.
**Akzeptanzkriterien:**
- BVA-Dialog erlaubt Definition mehrerer Grenzwertbereiche (z.B. [1-10], [11-100])
- Pro Bereich kann "erlaubt" oder "nicht erlaubt" markiert werden
- Erzeugte Werte werden mit dem Flag markiert
- Generierung respektiert die "nicht erlaubt"-Markierung

---

## EPIC-14 - Sprint-6-Backlog

### REQ-3031 | Kombinatorische Abdeckungsanzeige
**Titel:** N-Wise-Coverage-Metrik nach Generierung
**Prioritaet:** Should
**Status:** Planned
**Phase:** 3, Sprint 6
**User Story:**
Als Tester
moechte ich sehen, welche 1-wise-, 2-wise- oder 3-wise-Abdeckung eine Generierung tatsaechlich erreicht
damit ich die kombinatorische Qualitaet objektiv bewerten kann.
**Akzeptanzkriterien:**
- Fuer eine Generierung werden mindestens 1-wise und 2-wise Coverage angezeigt
- Falls 3-wise relevant oder aktiv ist, wird auch diese Kennzahl angezeigt
- Nicht abgedeckte Tupel koennen in einer Detailansicht gelistet werden
- Regeln und nicht erlaubte Werte werden bei der Berechnung beruecksichtigt
**Abhaengigkeiten:** REQ-0800, REQ-0801, REQ-0806, REQ-3023

---

### REQ-3032 | Orthogonale Arrays als Strategie
**Titel:** OA oder Taguchi als zusaetzliche Generierungsstrategie
**Prioritaet:** Could
**Status:** Planned
**Phase:** 3, Sprint 6
**User Story:**
Als erfahrener Testdesigner
moechte ich orthogonale Arrays als eigene Strategie auswaehlen koennen
damit ich bei passenden Modellen eine normierte und kompakte Abdeckung nutzen kann.
**Akzeptanzkriterien:**
- Neue Strategie "oa" ist auswaehlbar
- System prueft, ob das aktuelle Modell fuer eine OA-Generierung geeignet ist
- Bei fehlender Eignung wird verstaendlich auf eine alternative Strategie verwiesen
- Erzeugte Generation wird mit strategy="oa" gespeichert
**Abhaengigkeiten:** REQ-0800, REQ-3009

---

## EPIC-17 - Sprint 9 Backlog

### REQ-4012 | Datenklassen-Überarbeitung + BugMagnet-Import
**Titel:** System-Datenklassen umbenannt, Live-Import von BugMagnet GitHub
**Prioritaet:** Must
**Status:** TESTED
**Phase:** 3, Sprint 9
**User Story:**
Als Nutzer
moechte ich System-Datenklassen als "Beispiele" nutzen und BugMagnet-Datenklassen live importieren koennen
damit ich schnell professionelle Testdaten fuer meine Projekte verfuegbar habe.
**Akzeptanzkriterien:**
- System-Datenklassen sind in der UI als "Beispiele" benannt
- Settings-Seite zeigt "Datenklassen"-Bereich mit Import-Button
- Live-Import von BugMagnet GitHub https://github.com/gojko/bugmagnet funktioniert
- Nach erfolgreichen Import wechselt Bezeichnung zu "Bug Magnet Import"
- Endpoints vorhanden: POST /api/dataclasses/bugmagnet-import, GET /api/dataclasses/bugmagnet-status
**Traceability:** CHANGELOG v1.5.0, Sprint 9 Release

---

### REQ-4013 | Eigene Datenklassen Import/Export JSON
**Titel:** JSON-basierter Import/Export fuer benutzerdefinierte Datenklassen
**Prioritaet:** Must
**Status:** TESTED
**Phase:** 3, Sprint 9
**User Story:**
Als Nutzer
moechte ich meine Datenklassen als JSON exportieren und importieren koennen
damit ich diese zwischen Projekten portieren und mit anderen teilen kann.
**Akzeptanzkriterien:**
- Export-Funktion: eigene Datenklassen als JSON herunterladen
- Import-Funktion: JSON-Datei hochladen mit Merge-Strategie
- Legacy-Format wird korrekt unterstuetzt
- UI-Kasten sitzt oben in "Meine Datenklassen"
- Endpoints vorhanden: GET /api/dataclasses/export-user, POST /api/dataclasses/import-user
**Traceability:** CHANGELOG v1.5.0, Sprint 9 Release

---

### REQ-4014 | Kategorien & Werte – Tabellarische Ansicht + Drag & Drop
**Titel:** Spalten-Header, Drag-Drop-Umsortierung und verbesserte BVA/Default-Markierung
**Prioritaet:** Must
**Status:** TESTED
**Phase:** 3, Sprint 9
**User Story:**
Als Tester
moechte ich Kategoriewerte tabellarisch mit Spalten-Header anzeigen und per Drag-Drop umsortieren koennen
damit ich die Reihenfolge intuitiv und schnell anpasse.
**Akzeptanzkriterien:**
- Werte-Tabelle hat Spalten-Header (Reihenfolge, Wert, Aktionen)
- Werte sind per Drag-Drop umsortierbar, Reihenfolge wird gespeichert
- BVA-Symbol ist groesser mit "BVA"-Label gekennzeichnet
- Default-Markierung zeigt ★ statt ?
- Endpoint PUT /api/dataclasses/{id}/values/reorder ist implementiert
**Traceability:** CHANGELOG v1.5.0, Sprint 9 Release

---

### REQ-4015 | BVA-Visualisierung überarbeitet + Fehlerwert-Bug-Fix
**Titel:** Symbolischer Zahlenstrahl mit Farbkodierung und is_error-Korrektur
**Prioritaet:** Must
**Status:** TESTED
**Phase:** 3, Sprint 9
**User Story:**
Als Tester
moechte ich BVA-Bereiche mit besserer Visualisierung und farblicher Unterscheidung sehen
damit ich komplexe Multi-Range-Modelle schnell erfasse.
**Akzeptanzkriterien:**
- Symbolischer Zahlenstrahl mit gleichmaessigen Abststaenden (Lesbarkeit > Masseinheiten)
- Multi-Range: jede Aequivalenzklasse farbig unterschieden, Luecken ausgegraut
- BVARange.is_valid: erlaubte/unerlaubte Aequivalenzklassen explizit markierbar
- Fehlerwert-Bug behoben: is_error korrekt in Kategorien & Werte angezeigt
**Traceability:** CHANGELOG v1.5.0, Sprint 9 Release

---

### REQ-4016 | Neuer Typ "Ergebnis" für Kategorien (ISTQB Expected Result)
**Titel:** Ergebnis-Kategorien nicht automatisch in Kombinatorik einbezogen
**Prioritaet:** Must
**Status:** TESTED
**Phase:** 3, Sprint 9
**User Story:**
Als Tester
moechte ich Kategorien als "Ergebnis-Kategorien" markieren koennen, die nicht automatisch in die Kombinatorik einbezogen werden
damit ich ISTQB-konform nur erwartete Ergebnisse manuell oder regelbasiert befuelle.
**Akzeptanzkriterien:**
- Kategorien sind als "Ergebnis-Kategorie" markierbar (is_result Flag)
- Ergebnis-Kategorien werden NICHT automatisch in Kombinatorik einbezogen
- Nur durch Regeln oder manuelle Eingabe befuellbar (ISTQB-konform)
- Testfall-Tabelle zeigt Ergebnis-Spalte immer sichtbar mit farblich markierten leeren Feldern
- ResultCellEditor: Dropdown + Freitext nach Generierung editierbar
**Traceability:** CHANGELOG v1.5.0, Sprint 9 Release

---

### REQ-4018 | Max. Testfaelle pro Kombination (Setting)
**Titel:** Konfigurierbare Obergrenze fuer generierte Testfaelle
**Prioritaet:** Should
**Status:** DONE / TESTED (Sprint 10 Nacharbeit, 2026-09-01)
**Phase:** 4, Sprint 10
**User Story:**
Als Tester
moechte ich eine maximale Anzahl generierter Testfaelle pro Kombination einstellen koennen (Default 1000)
damit eine Generierung mit sehr vielen Kombinationen (z. B. Strategie "all") nicht unbegrenzt viele Testfaelle erzeugt und das System nicht ueberlastet.
**Akzeptanzkriterien:**
- Backend liest die Obergrenze konfigurierbar (Umgebungsvariable `GREAT_MAX_TESTCASES`), Default ist 1000
- Ungueltige Werte (nicht-numerisch oder <= 0) fallen robust auf den Default zurueck
- `POST /projects/{pid}/generate` respektiert die Obergrenze, wenn kein expliziter `limit` mitgeschickt wird
- Ein expliziter, kleinerer `limit`-Wert im Request bleibt weiterhin massgeblich (bestehendes Verhalten unveraendert)
- Die bestehende Validierung (`limit` muss positiv sein) bleibt unveraendert erhalten
- Settings-Seite (Frontend) zeigt eine Karte "Maximale Anzahl Testfaelle" mit Eingabefeld, Default-Anzeige (1000) und Validierung (Bereich 1–100000)
- Der Frontend-Wert wird lokal gespeichert (localStorage) und ohne Server-Neustart bei der naechsten Generierung als `limit` mitgeschickt
**Abhaengigkeiten:** REQ-4007 (Analogie zum Port-Setting-Muster)
**Traceability:** Sprint-10 Aufgabe 3 – Implementierung + Tests gruen (Backend: `tests/test_max_testcases_setting.py`; Frontend: `frontend/src/lib/__tests__/maxTestCasesSetting.test.ts`, `frontend/src/components/__tests__/MaxTestCasesSettingsCard.test.tsx`, `frontend/src/store/__tests__/generateStore.test.ts`), Nachtrag 2026-09-01

---

### REQ-3033 | Transparente Analysegrenzen bei Regelkomplexitaet
**Titel:** Heuristische Kennzeichnung komplexer Regelanalysen
**Prioritaet:** Should
**Status:** Planned
**Phase:** 3, Sprint 6
**User Story:**
Als Tester
moechte ich erkennen, ob eine Analyse zu toten Werten vollstaendig oder nur heuristisch erfolgt ist
damit ich Warnungen bei komplexen Regelsaetzen richtig einordnen kann.
**Akzeptanzkriterien:**
- Die Analyse kennzeichnet Ergebnisse als "vollstaendig geprueft" oder "heuristisch geprueft"
- Bei hoher Regelkomplexitaet wird keine Vollstaendigkeit suggeriert
- Die UI erklaert den Heuristik-Hinweis verstaendlich
- REQ-3015-Warnungen bleiben sichtbar, werden aber um den Pruefmodus ergaenzt
**Abhaengigkeiten:** REQ-3015, REQ-3004

---

### REQ-3034 | Risikobasierte Testfall-Sortierung
**Titel:** Generierte Testfaelle nach kumuliertem Risiko priorisieren
**Prioritaet:** Should
**Status:** DONE / TESTED (Sprint 10 Nacharbeit, 2026-09-01)
**Phase:** 3, Sprint 6
**User Story:**
Als Tester
moechte ich generierte Testfaelle nach dem kumulierten Risiko ihrer enthaltenen Werte sortiert sehen
damit ich zuerst die fachlich kritischsten Testfaelle ausfuehren kann.
**Akzeptanzkriterien:**
- Pro Testfall wird ein kumulierter Risiko-Score berechnet
- Nutzer kann nach Risiko absteigend sortieren
- Die Sortierung bleibt von der eigentlichen Generierungslogik getrennt
- Fehlerwert-Sortierregeln aus REQ-3018 haben Vorrang vor reiner Risiko-Sortierung
**Abhaengigkeiten:** REQ-3007, REQ-3018, REQ-0805
**Traceability:** Sprint-10 Aufgabe 2 – Risk-Sortierung implementiert, zugehörige Tests gruen (Nachtrag 2026-09-01)

---

## EPIC-15 - Grenzwertanalyse-Frontend und weitere Kombinatoriken

### REQ-3035 | Grenzwertanalyse-Frontend fuer vorhandenen BVA-Endpunkt
**Titel:** React-Oberflaeche fuer POST /categories/{cid}/bva
**Prioritaet:** Must
**Status:** Planned
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
moechte ich die bestehende Grenzwertanalyse direkt in der React-Kategorieansicht ausloesen und konfigurieren koennen
damit ich numerische Grenzwerte ohne manuelle API-Nutzung in Werte umwandeln kann.
**Akzeptanzkriterien:**
- In numerischen Kategorien gibt es eine UI-Aktion "Grenzwertanalyse"
- Die Maske erfasst mindestens Min, Max und Modus fuer 2, 3 oder 4 Testwerte pro Grenze
- Beim Bestaetigen wird explizit der vorhandene Endpunkt POST /categories/{cid}/bva aufgerufen
- Die vom Endpunkt erzeugten Werte erscheinen danach sofort in der Kategorieansicht
- Fuer nicht numerische Kategorien ist die Aktion verborgen oder deaktiviert
**Abhaengigkeiten:** REQ-0306, REQ-0305, REQ-3007

---

### REQ-3036 | Mixed-Strength-Kombinatorik
**Titel:** Hoehere Abdeckungsstaerke nur fuer ausgewaehlte Kategorien
**Prioritaet:** Should
**Status:** Planned
**Phase:** 3, Sprint 6+
**User Story:**
Als Tester
moechte ich fuer ausgewaehlte fachlich kritische Kategorien eine hoehere Kombinationsstaerke als fuer den Rest definieren
damit ich gezielt mehr Abdeckung erhalte ohne den gesamten Testumfang unverhaeltnismaessig zu erhoehen.
**Akzeptanzkriterien:**
- Nutzer kann eine Basistrategie und davon abweichende staerkere Abdeckung fuer ausgewaehlte Kategorien festlegen
- Konfiguration wird mit der Generation gespeichert
- Coverage-Anzeige unterscheidet globale und verstaerkte Teilabdeckung
- Nicht erfuellbare Konfigurationen werden verstaendlich validiert
**Abhaengigkeiten:** REQ-0800, REQ-0806, REQ-3031

---

### REQ-3037 | Seed-basierte Kombinatorik
**Titel:** Vorgegebene Testfaelle beibehalten und algorithmisch ergaenzen
**Prioritaet:** Could
**Status:** Planned
**Phase:** 3, Sprint 6+
**User Story:**
Als Tester
moechte ich vorhandene oder manuell definierte Testfaelle als feste Seeds verwenden und nur die fehlende Abdeckung automatisch ergaenzen lassen
damit manuelle Fachfaelle und algorithmische Ergaenzung kombiniert werden koennen.
**Akzeptanzkriterien:**
- Bestehende Testfaelle koennen als Seeds markiert werden
- Generierung behaelt Seeds unveraendert bei
- System ergaenzt nur zusaetzliche Faelle zur gewaehlten Zielabdeckung
- Ergebnis zeigt getrennt an: Seed-Faelle und ergaenzte Faelle
**Abhaengigkeiten:** REQ-3016, REQ-0800, REQ-3009

---

### REQ-3038 | Coverage-Gap-Closure
**Titel:** Fehlende Tupel nach einer Generierung gezielt nacherzeugen
**Prioritaet:** Could
**Status:** Planned
**Phase:** 3, Sprint 6+
**User Story:**
Als Tester
moechte ich nach einer Generierung gezielt nur noch fehlende kombinatorische Luecken schliessen lassen
damit ich eine bestehende Generation inkrementell verbessern kann statt komplett neu zu starten.
**Akzeptanzkriterien:**
- System identifiziert nicht abgedeckte Tupel der gewaehlten Staerke
- Nutzer kann eine "Luecken schliessen"-Aktion ausloesen
- Neu erzeugte Zusatzfaelle respektieren aktive Regeln
- Ergebnisbericht nennt geschlossene und weiterhin unmoegliche Luecken
**Abhaengigkeiten:** REQ-3031, REQ-3005, REQ-3036

---

### REQ-3039 | T-Wise-Algorithmus
**Titel:** T-Wise Kombinatorik (t=1..4) als Kernstrategie
**Prioritaet:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 4
**User Story:**
Als Testdesigner
moechte ich T-Wise Kombinationen (1-wise bis 4-wise) als primäre Generierungsstrategie einsetzen koennen
damit ich skalierbar hohe Abdeckungsziele mit kontrollierbarem Testumfang erreiche.
**Akzeptanzkriterien:**
- Neue Strategie "t-wise" wahlbar, Laengeparameter t=1..4 konfigurierbar
- Default: 2-wise (pairwise) fuer MVP, 3-wise und 4-wise wahlbar fuer erweiterte Szenarien
- Generator respektiert aktive Regeln und Fehlerprohibitionen
- Coverage-Metriken (REQ-3031) berechnen t-wise Coverage korrekt
- Generierung dokumentiert verwendetes t in Generation-Metadaten
- Performance: t=2 < 1s, t=3 < 5s, t=4 < 30s fuer typische Modelle (< 20 Kategorien, < 10 Werte)
**Akzeptanzkriterien Detail:**
- T-Wise nutzt Constraint-aware Generierung (REQ-3040) statt Post-Processing-Filterung
- Systematische Tupel-Reduktion nicht vorhanden (= bereits optimal kombiniert)
- Ungueltige Kombinationen werden pruefbar ausgeschlossen (nicht als "Dead Test Case" markiert)
**Abhaengigkeiten:** REQ-3040, REQ-3005, REQ-3031, REQ-0800, REQ-0806
**Blockiert:** REQ-3036, REQ-3037, REQ-3038

---

### REQ-3040 | RuleEngine-Refactor fuer Constraint-aware Generierung
**Titel:** Architektur-Refactor: Regel-Integration in Generierungs-Algorithmen
**Prioritaet:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 3–4
**User Story:**
Als Entwickler
moechte ich dass alle Kombinatorik-Generatoren (T-Wise, OA, Coverage-Gap) Constraints bereits während der Generierung beruecksichtigen
damit vermieden wird, dass ungueltige Kombinationen erzeugt und danach gefiltert werden.
**Akzeptanzkriterien:**
- RuleEngine (existing src/core/rule_engine.py) wird in alle Generatoren integriert
- Keine Generierung erzeugt bewusst ungueltige Kombinationen (= Post-Processing-Reduktion gegen Null)
- Performance-Vergleich "vor/nach": Refactor darf nicht > 10% langsamer sein
- Bestandstests bleiben bestanden (Backward-Compatibility)
- Neue Unit-Tests fuer Constraint-aware Generierung in allen Kombinatorik-Strategien
**Detailanforderungen:**
- Prohibiertes Wert-Set (from REQ-3004/3005) wird vor Tupel-Konstruktion geprueft
- Regeln (REQ-0806) werden als Boolean-Constraints in Generierungs-Baum propagiert
- Tote Werte (REQ-3015) werden nicht in Tupel-Generation beruecksichtigt
**Abhaengigkeiten:** REQ-3005, REQ-3004, REQ-0806, REQ-3015
**Blockiert:** REQ-3039, REQ-3032, REQ-3036, REQ-3037, REQ-3038

---

### REQ-3041 | BVA-Dialog UX-Implementation
**Titel:** React-Komponente fuer Grenzwertanalyse-Konfiguration
**Prioritaet:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 4
**User Story:**
Als Tester
moechte ich eine intuitiv bedienbare Maske zur Konfiguration von Grenzwertanalysen nutzen
damit ich auch ohne API-Kenntnisse numerische Grenzen in Testwerte umwandeln kann.
**Akzeptanzkriterien:**
- Dialog ist über Action "Grenzwertanalyse" in numerischen Kategorien erreichbar
- Eingabefelder: Min (required), Max (required), Modus (2/3/4-wertig)
- Live-Vorschau: Beim Ändern werden generierte Werte angezeigt
- "Anwenden"-Button ruft POST /categories/{cid}/bva auf und speichert Ergebnis
- Neue Werte erscheinen sofort in Kategoriewertliste (REQ-0302)
- Validierung: Min < Max, numerische Eingaben, aussagekräftige Fehlermeldungen
- Für nicht-numerische Kategorien: Aktion ist verborgen
**UI-Struktur (basierend auf Wireframe REQ-3035):**
- Modal oder Inline-Panel mit 3–4 Input-Feldern
- Presets fuer Standard-Modi (2/3/4 Testwerte)
- Undo/Reset-Option
- Hilfetexte fuer Min/Max/Modus
**Akzeptanzkriterien Detail (UX-Design-Ready):**
- Dezimalzahl-Handling (Dezimal.js vs. Float) – entschieden in REQ-3042
- Min/Max Auto-Prefill: Optional (Entscheidung durch Tech-Lead, s. REQ-3043)
- Numerische Sondertypen (Integer, Float, Decimal) unterschieden
**Abhaengigkeiten:** REQ-3035, REQ-0306, REQ-0305, REQ-3007, REQ-3042 (tech), REQ-3043 (tech)
**Open Questions dokumentiert:** 
- O1: Dezimal.js Dependency? (Entscheidung: Tech-Lead)
- O2: Min/Max Auto-Prefill aus Kategorie-Metadaten?
- O3: Modus-Labels: "Obergrenze", "Untergrenze", "Bereich"?
- O4: Batch-BVA auf mehreren Kategorien gleichzeitig?
- O5: Historisierung: Generierte Werte nachverfolgbar speichern?
- O6: Export BVA-Konfiguration in Projekt mitnehmen?
- O7: BVA-Qualitaetsbewertung: Äquivalenzklassen-Gütemetrik?
- O8: Integriert mit Orchesterung? (z.B. automatische BVA vor T-Wise?)

---

### REQ-3042 | Tech-Decision: Dezimal.js für numerische Präzision
**Titel:** Dezimal.js-Bibliothek für exakte numerische Berechnungen
**Priorität:** Must
**Status:** DONE / TESTED
**Phase:** 3, Sprint 4
**Decision:** Dezimal.js wird eingesetzt (User Decision 2026-07-01)
**User Story:**
Als Backend-/Frontend-Developer möchte ich Dezimal.js nutzen damit BVA-Grenzwert-Berechnungen numerisch exakt sind und keine Floatingpoint-Fehler auftreten (z.B. 0.1 + 0.2 ≠ 0.3).
**Akzeptanzkriterien:**
- Dezimal.js in Python-requirements.txt (oder numpy.decimal)
- decimal.js in frontend/package.json
- BVA-Dialog (REQ-3041) nutzt Dezimal.js für Berechnungen
- Unit-Tests für Dezimalgenauigkeit vorhanden
- Dokumentiert in decision-log.md als ADR-009
**Abhängigkeiten:** –

---

### REQ-3043 | BVA Min/Max-Input-Strategie: Explizite Eingabe
**Titel:** BVA-Dialog startet mit leeren Min/Max-Feldern
**Priorität:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 4
**Decision:** Option A – Leere Felder, User füllt manuell (User Decision 2026-07-01)
**User Story:**
Als Tester möchte ich beim BVA-Dialog Min/Max manuell eingeben damit ich explizite Kontrolle über die Grenzwert-Analyse habe und keine versteckten Annahmen aus der Kategorie entstehen.
**Akzeptanzkriterien:**
- BVA-Dialog zeigt beim Öffnen leere Min/Max-Input-Felder
- Keine Auto-Prefill aus Kategorie-Metadaten
- User muss Min/Max bei jeder BVA-Nutzung eingeben
- Validierung: Min < Max erforderlich
- Dokumentiert in decision-log.md als ADR-010
**Abhängigkeiten:** REQ-3042

---

## EPIC-16 - Phase 3 Sprint 4+ Kombinatorik-Algorithmen (MCDC)

### REQ-3044 | MCDC-Algorithmus (Modified Condition/Decision Coverage)
**Titel:** MCDC Testfall-Generierung fuer komplexe Bedingungen
**Prioritaet:** Should
**Status:** DONE / TESTED
**Phase:** 3, Sprint 4–5
**User Story:**
Als Software-Tester fuer kritische Systeme
moechte ich Testfaelle nach MCDC-Kriterium (Modified Condition/Decision Coverage) erzeugen koennen
damit Boolean-Ausdruecke und Entscheidungslogik vollstaendig getestet werden.
**Akzeptanzkriterien:**
- Neue Strategie "mcdc" wahlbar
- System identifiziert verändernde Bedingungen für jede Entscheidung
- MCDC-Testfälle werden gemäß Standard erzeugt
- Coverage-Anzeige unterscheidet MCDC-vollständig vs. teilweise
- Regeln und tote Werte beeinflussen MCDC-Generierung
**Abhaengigkeiten:** REQ-3040, REQ-0806, REQ-3005, REQ-3031

---

# PHASE 4 – Enterprise & KI
*(ehemals Phase 3 Backlog – verschoben durch Entscheidung 2026-06-29)*

### REQ-4004 | Business Rule Based Testing
**Phase:** 4, Sprint 2 | **Status:** Planned

### REQ-4005 | Ollama/LLM-Integration
**Phase:** 4, Sprint 3 | **Status:** Planned

---

## EPIC-18 – Multi-User Nutzung (Teams bis 10 Personen)

**Eingeplant:** Phase 4, Sprint 11–13
**Freigegeben durch:** Program Manager Agent (2026-09-01)
**Voraussetzung/Architektur-Leitplanke:** ADR-012 (HYBRID-Ansatz – Optimistic Concurrency + Stale-Warning, siehe decision-log.md)

### Zielbild

G.R.E.A.T. wird für Teams bis **10 gleichzeitig angemeldete Personen** nutzbar. Mehrere
Tester:innen können am selben Projekt arbeiten (verschiedene Kategorien/Generierungen),
ohne dass Änderungen sich unbemerkt gegenseitig überschreiben. Es handelt sich **nicht**
um echte Realtime-Kollaboration (kein Live-Cursor, kein CRDT/OT) – das ist bewusst auf
eine spätere Ausbaustufe verschoben (siehe Out of Scope). Diese Ausbaustufe ist die
**Vorstufe**: Login/Rollen + optimistisches Sperren + Hinweis bei veralteten Daten.

### In Scope (Sprint 11–13)

- REQ-4001 – Authentifizierung (OAuth2/JWT) als Basisvoraussetzung
- REQ-4006 – Multi-User-Datenmodell (SQLite weiterhin Default, PostgreSQL optional)
- REQ-4020 – Rollen & Rechte Basismodell (Admin/Editor/Viewer)
- REQ-4021 – Optimistic Concurrency Control (Versionsfeld + 409-Conflict-Antwort)
- REQ-4022 – Stale-Data-Warning im Frontend (Banner + gezieltes Neuladen)
- REQ-4023 – Projekt-Sharing / Mitgliederverwaltung pro Projekt
- REQ-4024 – Minimaler Audit-Trail (wer hat zuletzt geändert)
- REQ-4025 – Benutzerverwaltung im Frontend (CRUD-Nutzer, Rollen, Passwörter)
- REQ-4026 – Datenbank-Reset behält Admin-Konto (Bugfix)
- REQ-4027 – Erststart-Hinweis auf der Login-Seite (solange Default-Admin das Standardpasswort hat; Risikoakzeptanz durch Projektinhaber, RISK-S-016)
- REQ-4028 – Pflicht-Passwortwechsel nach Erstanmeldung mit Standardpasswort (serverseitige Sperre, Folge-REQ zu REQ-4027, Massnahme RISK-S-016)

### Out of Scope (bewusst NICHT Sprint 11–13)

- Echtzeit-Kollaboration (WebSocket/SSE Live-Editing, CRDT/Operational Transform)
- Live-Presence-Anzeige ("wer schaut gerade zu") und Live-Cursor
- Echtzeit-Benachrichtigungsfunktion (Push/E-Mail) – nur als Klärungsauftrag aus Sprint 10 vermerkt, keine Umsetzung
- Enterprise-SSO (SAML/LDAP/Azure AD) – nur lokale OAuth2/JWT-Nutzer
- Mandantenfähigkeit/Multi-Tenant-SaaS-Hosting
- Team-Größe > 10 Personen (keine horizontale Skalierung/Cluster-Betrieb Ziel dieser Stufe)

### Abhängigkeiten

- REQ-4007 (GREAT_PORT/.env) – DONE, Voraussetzung für Konfigurationsmuster
- REQ-4008 (Health-Check) – DONE, Voraussetzung für Monitoring im Multi-User-Betrieb
- ADR-007 (DB-Strategie SQLite/PostgreSQL) – Bestätigung Chief Architect ausstehend
- ADR-012 (HYBRID-Konfliktstrategie) – Accepted (Grundlage für REQ-4021/4022)
- Security Architect Review für Auth-Schema (RISK-S-001) vor Sprint-11-Start zwingend
- CORS-Konfiguration muss vor Multi-User-Release auf Whitelist umgestellt werden (Schulden-Item #8, phase-4-sprint-stabi-needs.md)

### Risiken (EPIC-Ebene)

| Risiko | W | I | Score | Ampel | Maßnahme |
|---|---|---|---|---|---|
| Fehlende Authentifizierung bei Multi-User-Rollout (RISK-S-001) | 5 | 4 | 20 | 🔴 | REQ-4001 vor jedem Multi-User-Feature zwingend abschließen |
| Konflikte bei gleichzeitiger Bearbeitung ungeklärt (neu: RISK-T-008) | 3 | 4 | 12 | 🔴 | Optimistic Concurrency (REQ-4021) + Stale-Warning (REQ-4022) |
| SQLite-Schreibkonflikte bei >5 gleichzeitigen Nutzern (RISK-T-006) | 2 | 4 | 8 | 🟡 | PostgreSQL optional (REQ-4006), Lasttest in Sprint 13 |
| Default-Admin mit bekanntem Standardpasswort `changeme123!` (RISK-S-016) | 4 | 5 | 20 | 🔴 | Massnahme REQ-4028 (Pflicht-Passwortwechsel, serverseitig). Hinweis auf der Login-Seite (REQ-4027) nur unter **Risikoakzeptanz durch Projektinhaber, RISK-S-016** (Georg Hartel, 2026-11-03); Security Architect hat den Klartext-Hinweis abgelehnt |
| CORS/Origin-Policy zu offen vor Rollout | 3 | 3 | 9 | 🟡 | Whitelist vor Sprint-11-Release umsetzen |
| Scope-Erwartung "Echtzeit" vs. tatsächlich Hybrid-Vorstufe (Stakeholder-Missverständnis) | 3 | 3 | 9 | 🟡 | Klare Kommunikation Out-of-Scope, Abnahme durch Program Manager |

**Eskalationspflichtig (Score ≥ 10):** RISK-S-001 (20), RISK-S-016 (20, Risikoakzeptanz Projektinhaber für REQ-4027, Massnahme REQ-4028), RISK-T-008 (12, neu).

---

### REQ-4001 | Authentifizierung (OAuth2/JWT)
**Titel:** Login/Token-basierte Authentifizierung als Voraussetzung für Multi-User
**Prioritaet:** Must
**Status:** Implemented (Backend)
**Phase:** 4, Sprint 11
**User Story:**
Als Administrator
moechte ich, dass sich Nutzer:innen mit Benutzername/Passwort anmelden und ein Token erhalten
damit nur autorisierte Personen auf Projekte zugreifen koennen.
**Akzeptanzkriterien:**
- POST /auth/login akzeptiert Benutzername/Passwort und liefert JWT Access-Token + Refresh-Token
- Passwoerter werden gehasht gespeichert (bcrypt/argon2), niemals im Klartext
- Alle bestehenden API-Endpunkte pruefen ein gueltiges Token (Depends(get_current_user))
- Abgelaufene/ungueltige Token liefern 401 mit klarer Fehlermeldung
- Frontend zeigt Login-Maske, speichert Token sicher (httpOnly-Cookie oder memory, kein localStorage fuer Access-Token)
- Logout invalidiert Refresh-Token serverseitig
**TDD-Hinweis:** Test-first fuer Token-Erzeugung/-Validierung (pytest), danach Router-Absicherung; Frontend Login-Flow mit Vitest/RTL vor Implementierung der Komponente.
**Abhaengigkeiten:** –
**Blockiert:** REQ-4006, REQ-4020, REQ-4021, REQ-4022, REQ-4023, REQ-4024

---

### REQ-4006 | Multi-User (PostgreSQL optional)
**Titel:** Mehrbenutzerfaehiger Datenzugriff fuer Teams bis 10 Personen
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 12
**User Story:**
Als Team-Mitglied
moechte ich zeitgleich mit bis zu 9 weiteren Kolleg:innen an G.R.E.A.T.-Projekten arbeiten
damit unser Team gemeinsam Testfaelle entwickeln kann, ohne sich gegenseitig zu blockieren.
**Akzeptanzkriterien:**
- SQLAlchemy Engine ist ueber DATABASE_URL konfigurierbar (Default: SQLite, optional PostgreSQL)
- Alembic-Migrationen laufen gegen SQLite UND PostgreSQL
- Connection Pooling (QueuePool) fuer PostgreSQL aktiv
- Lasttest bestaetigt stabilen Betrieb mit 10 simulierten gleichzeitigen Nutzern (Lesen + Schreiben)
- Bestehender Single-User-Betrieb (SQLite) bleibt ohne Regression funktionsfaehig
**TDD-Hinweis:** tests/test_multi_user_db.py mit Parametrisierung SQLite/PostgreSQL (skip-if-unavailable), zuerst Test fuer Engine-Switch schreiben.
**Abhaengigkeiten:** REQ-4001, ADR-007
**Blockiert:** REQ-4021, REQ-4023

---

### REQ-4020 | Rollen & Rechte Basismodell
**Titel:** Admin/Editor/Viewer-Rollen fuer Projekte und Team-Verwaltung
**Prioritaet:** Should
**Status:** Implemented (Backend, Frontend fehlt)
**Phase:** 4, Sprint 11
**User Story:**
Als Team-Lead
moechte ich Mitgliedern Rollen (Admin, Editor, Viewer) zuweisen
damit nicht jede Person versehentlich Projekte loeschen oder Nutzer verwalten kann.
**Akzeptanzkriterien:**
- Drei Rollen sind definiert: Admin (Vollzugriff inkl. Nutzerverwaltung), Editor (Projekte bearbeiten), Viewer (nur lesen)
- Rollenpruefung erfolgt serverseitig auf allen schreibenden Endpunkten
- Erste registrierte Person wird automatisch Admin
- UI blendet nicht erlaubte Aktionen fuer Viewer aus/deaktiviert sie
- Fehlversuch (Viewer versucht Schreibaktion) liefert 403 mit verstaendlicher Meldung
**TDD-Hinweis:** Backend-Rollenpruefung zuerst als Unit-Test pro Rolle x Endpunkt-Matrix, danach Implementierung der Dependency.
**Abhaengigkeiten:** REQ-4001
**Blockiert:** REQ-4023, REQ-4025

---

### REQ-4021 | Optimistic Concurrency Control
**Titel:** Versionsfeld + Konflikterkennung statt Pessimistic Locking (HYBRID-Ansatz, ADR-012)
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 12
**User Story:**
Als Tester
moechte ich gewarnt werden, wenn eine Kategorie/ein Testfall zwischenzeitlich von jemand anderem geaendert wurde
damit ich meine Aenderung nicht versehentlich eine fremde Aenderung ueberschreibt.
**Akzeptanzkriterien:**
- Projekt, Kategorie, Wert und Testfall erhalten ein `version`-Feld (int, inkrementiert bei jedem Update)
- PUT/PATCH-Requests senden die zuletzt gelesene `version` mit
- Stimmt die Version nicht mit der aktuellen DB-Version ueberein: 409 Conflict mit aktuellem Serverstand im Body
- Keine echte Sperre (kein Lock) – parallele Lesevorgaenge bleiben uneingeschraenkt moeglich
- Konfliktfall ist durch Backend-Tests abgedeckt (zwei simulierte gleichzeitige Updates)
**TDD-Hinweis:** Test zuerst fuer "zwei Updates mit gleicher Ausgangsversion -> zweites liefert 409" schreiben, danach Versionsfeld + Vergleichslogik implementieren.
**Abhaengigkeiten:** REQ-4006
**Blockiert:** REQ-4022

---

### REQ-4022 | Stale-Data-Warning im Frontend
**Titel:** Hinweisbanner bei veralteten Daten nach 409-Conflict
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 12
**User Story:**
Als Tester
moechte ich sofort erkennen, wenn meine Ansicht veraltet ist
damit ich bewusst entscheiden kann, neu zu laden oder meine Aenderung dennoch (mit Ueberschreibungs-Bestaetigung) zu speichern.
**Akzeptanzkriterien:**
- Bei 409-Response zeigt das Frontend ein deutliches Banner: "Diese Ansicht ist veraltet – von {Nutzer} geaendert"
- Aktionen im Banner: "Neu laden" (verwirft lokale Aenderung) oder "Trotzdem ueberschreiben" (mit Bestaetigungsdialog)
- Kein automatisches, stilles Ueberschreiben ohne Nutzerinteraktion
- Banner verschwindet nach gewaehlter Aktion
- Kein Live-Update/Polling der Fremdaenderung (das ist bewusst Out of Scope, siehe EPIC-18)
**TDD-Hinweis:** Vitest/RTL-Test fuer Banner-Zustand bei simuliertem 409-Response zuerst schreiben, danach Komponente implementieren.
**Abhaengigkeiten:** REQ-4021
**Blockiert:** –

---

### REQ-4023 | Projekt-Sharing / Mitgliederverwaltung
**Titel:** Projekte gezielt mit Team-Mitgliedern teilen
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 13
**User Story:**
Als Projekt-Owner
moechte ich festlegen koennen, welche Team-Mitglieder Zugriff auf mein Projekt haben
damit nicht automatisch alle 10 Team-Mitglieder alle Projekte sehen.
**Akzeptanzkriterien:**
- Projekt hat eine Mitgliederliste (Nutzer + Rolle je Projekt: Editor/Viewer)
- Owner (oder Admin) kann Mitglieder hinzufuegen/entfernen
- Nutzer ohne Zugriff sehen das Projekt nicht in der Projektliste
- Endpoint-Absicherung: 403 bei Zugriff ohne Mitgliedschaft
**TDD-Hinweis:** Test zuerst fuer "Nutzer ohne Mitgliedschaft sieht Projekt X nicht in GET /projects", danach Filterlogik implementieren.
**Abhaengigkeiten:** REQ-4006, REQ-4020
**Blockiert:** –

---

### REQ-4024 | Minimaler Audit-Trail
**Titel:** Nachvollziehbarkeit "wer hat zuletzt geaendert"
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 13
**User Story:**
Als Team-Lead
moechte ich sehen, wer eine Kategorie oder einen Testfall zuletzt geaendert hat
damit ich bei Rueckfragen die richtige Person ansprechen kann.
**Akzeptanzkriterien:**
- Projekt, Kategorie, Wert und Testfall speichern `last_modified_by` (User-ID) und `last_modified_at` (Timestamp)
- Werte werden in der UI dezent angezeigt (z.B. Tooltip "Zuletzt geaendert von X am Y")
- Kein vollstaendiges Audit-Log mit Historie (das ist REQ-4003 "Audit-Log", separat und spaeter) – nur letzter Stand
**TDD-Hinweis:** Unit-Test fuer automatisches Setzen von last_modified_* bei jedem Update-Call, vor Implementierung schreiben.
**Abhaengigkeiten:** REQ-4001, REQ-4006
**Blockiert:** –

---

### REQ-4025 | Benutzerverwaltung im Frontend (EPIC-18)
**Titel:** Benutzerverwaltung in Einstellungen (Erstellen, Loeschen, Rolle aendern, Passwort aendern)
**Prioritaet:** Must
**Status:** Done / TESTED
**Phase:** 4, Sprint 11+
**User Story:**
Als Admin
moechte ich in den Einstellungen Nutzer verwalten (anlegen, loeschen, Rolle aendern, Passwort aendern)
damit ich mein Team ohne technische Kenntnisse konfigurieren kann.
**Akzeptanzkriterien:**
- Admin sieht in Einstellungen alle Nutzer mit Benutzername, Rolle, Status (aktiv/inaktiv)
- Admin kann neuen Nutzer anlegen (Benutzername, Passwort, Rolle)
- Admin kann Rolle eines Nutzers aendern (Admin, Editor, Viewer)
- Admin kann Nutzer loeschen (nicht sich selbst)
- Admin kann Passwort eines Nutzers aendern (auch sein eigenes)
- Editor/Viewer koennen keine Nutzer verwalten (403)
- Bei Loeschen eines Nutzers: dessen Projektmitgliedschaften werden entfernt
**TDD-Hinweis:** Backend-Tests fuer CRUD-Endpunkte zuerst, dann Frontend-Tests
**Abhaengigkeiten:** REQ-4001, REQ-4020
**Blockiert:** –

---

### REQ-4026 | Datenbank-Reset behaelt Admin-Konto (Bugfix)
**Titel:** Datenbank-zuruecksetzen behaelt aktuelles Admin-Konto oder erstellt Standard-Admin
**Prioritaet:** Must (Bugfix)
**Status:** Done (Backend) – Change Request CR-4026-01 offen (Umsetzung in `services.py` ausstehend)
**Phase:** 4, Sprint 11+
**User Story:**
Als Admin
moechte ich die Datenbank zuruecksetzen koennen ohne danach ausgesperrt zu werden.
**Akzeptanzkriterien:**
- Datenbank-Reset loescht alle Projekte/Kategorien/Werte/Testfaelle
- User-Tabelle bleibt erhalten (aktive Nutzer werden nicht geloescht)
- Nach Reset ist der Admin weiterhin eingeloggt
- Falls kein Admin existiert: Standard-Admin (admin / changeme123!) wird erstellt
  - *Change Request CR-4026-01 (2026-11-03):* Vorher lautete dieser Punkt `Standard-Admin (admin/admin123)`. Geaendert, damit Start-Bootstrap (`DEFAULT_ADMIN_PASSWORD`, `bootstrap.py`) und Reset-Pfad (`services.py`) dasselbe Standardpasswort verwenden. Entscheidung Projektinhaber (Georg Hartel). Der alte Wert `admin123` entfaellt.
**Change Request CR-4026-01 (2026-11-03):**
- Aenderung: Standardpasswort im Reset-Pfad von `admin123` auf `changeme123!` (= `DEFAULT_ADMIN_PASSWORD`, einzige Definition).
- Umsetzung offen: `src/app/services.py` (Zeile ~85, Reset-Pfad) und Test in `tests/test_user_management.py` anpassen. Bis dahin gilt der Code-Stand `admin123` als Abweichung von diesem REQ.
- Erneute Pruefung nach Umsetzung: Test "Reset ohne Admin erzeugt Admin mit `DEFAULT_ADMIN_PASSWORD`" (Gleichheit mit Bootstrap-Konstante, vgl. REQ-4027 AK-1).
**TDD-Hinweis:** Test fuer "Reset behaelt User-Tabelle" zuerst (bestehend); fuer CR-4026-01 Test auf neuen Standardwert zuerst rot, dann anpassen.
**Abhaengigkeiten:** REQ-4001, REQ-4027 (Konsistenz des Standardpassworts)
**Blockiert:** –

---

### REQ-4027 | Erststart-Hinweis auf der Login-Seite (Default-Admin)
**Titel:** Standard-Zugangsdaten auf der Anmeldemaske anzeigen, solange der Default-Admin das Standardpasswort hat
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 11+
**Risiko:** RISK-S-016 (Score 20)
**Risikoakzeptanz:** Risikoakzeptanz durch Projektinhaber, RISK-S-016 (Georg Hartel, 2026-11-03). Der Security Architect hat die Anzeige des Standardpassworts im Klartext als Risiko abgelehnt. Der Projektinhaber akzeptiert das Risiko bewusst. Die Auflagen AK-10 bis AK-14 gelten trotzdem. Die Massnahme zur Risikoreduktion ist REQ-4028 (Pflicht-Passwortwechsel).
**User Story:**
Als neue Nutzerin beim ersten Start
moechte ich auf der Anmeldemaske die Standard-Zugangsdaten des Admin-Kontos sehen
damit ich mich sofort anmelden kann und weiss, dass ich das Passwort danach aendern muss.
**Akzeptanzkriterien:**
- AK-1 (Konsistenz): Das Standardpasswort ist genau einmal als Backend-Konstante `DEFAULT_ADMIN_PASSWORD` definiert (Wert `changeme123!`). Start-Bootstrap (`ensure_first_admin`), Reset (`reset_database_state`, siehe REQ-4026 CR-4026-01) und Hinweistext verwenden diese Konstante. Test: alle Pfade erzeugen bzw. erwarten denselben Wert.
- AK-2 (Anzeige): Given der Benutzer `admin` existiert mit `is_first_admin=True`, `is_active=True` und `check_password(DEFAULT_ADMIN_PASSWORD)` ist wahr, When die Login-Seite geladen wird, Then steht unter dem Feld "Benutzername" der Text `Standardbenutzer: admin` und unter dem Feld "Passwort" der Text `Standardpasswort: changeme123! (bitte nach der ersten Anmeldung aendern)`.
- AK-3 (Ausblenden nach Passwortwechsel): Given der Default-Admin hat ein anderes Passwort als `DEFAULT_ADMIN_PASSWORD` (z.B. nach Passwortwechsel gemaess REQ-4025 oder REQ-4028), When die Login-Seite geladen wird, Then wird kein Erststart-Hinweis angezeigt.
- AK-4 (Ausblenden ohne Default-Admin): Given kein Benutzer `admin` mit `is_first_admin=True` und `is_active=True` existiert, Then wird kein Erststart-Hinweis angezeigt.
- AK-5 (Login mit Standardpasswort): Given der Default-Admin meldet sich erfolgreich mit `DEFAULT_ADMIN_PASSWORD` an und hat sein Passwort nicht geaendert, When er danach die Login-Seite erneut oeffnet, Then bleibt der Hinweis sichtbar. Hat er es geaendert, gilt AK-3.
- AK-6 (Endpunkt-Vertrag): Die Statusabfrage (z.B. `GET /auth/first-start-hint`, ohne Authentifizierung) liefert ausschliesslich `{"show_hint": true|false}`. Keine Passwoerter, Benutzernamen, Rollen, IDs oder weiteren Nutzerdaten. Test: Schluesselmenge der Antwort ist in allen Zustaenden exakt `{"show_hint"}`.
- AK-7 (Frontend-Konstante): Der angezeigte Passworttext stammt aus einer einzigen Frontend-Konstante, deren Wert mit `DEFAULT_ADMIN_PASSWORD` uebereinstimmt. Pruefung per Test oder Review-Checkliste (Drift-Risiko durch Zweitdefinition).
- AK-8 (Fehlerfall): Given die Statusabfrage schlaegt fehl, Then wird kein Hinweis angezeigt, aber die Anmeldung bleibt voll nutzbar (kein Blockieren des Logins).
- AK-9 (Freigabe-Gate, aktualisiert 2026-11-03): Die Umsetzung ist durch die Risikoakzeptanz des Projektinhabers fuer RISK-S-016 freigegeben. Der Security Architect hat den Klartext-Hinweis als Risiko abgelehnt. Der Hinweis ist nur bis zur Umsetzung von REQ-4028 (Pflicht-Passwortwechsel) vertretbar. Das Risiko bleibt als akzeptiert dokumentiert, nicht als geloest.
- AK-10 (Flag-Lebenszyklus, Security-Auflage): Der Zustand "Standardpasswort aktiv" wird persistiert (z.B. Flag `default_password_active`). Das Flag wird gesetzt, wenn der Default-Admin angelegt wird (Start oder Reset). Es wird geloescht, sobald ein erfolgreicher Passwortwechsel auf einen Nicht-Default-Wert erfolgt (REQ-4028 AK-6). AK-2 bis AK-5 lesen diesen Zustand. Offen: Flag oder Laufzeit-Pruefung `check_password` (siehe offene Frage 3).
- AK-11 (Rate-Limit, Security-Auflage): Der Statusendpunkt (AK-6) ist rate-limitiert, damit er nicht als Orakel fuer Brute-Force-Versuche genutzt werden kann. Schwelle: `OFFEN – Vorschlag 10 Anfragen pro Minute und Client-IP` (Entscheidung siehe offene Frage 4). Bei Ueberschreitung: HTTP 429, Antwort ohne Zustandsdaten.
- AK-12 (Keine Geheimnisse in Antworten, Security-Auflage): Passwort, Passwort-Hash und Passwortlaenge werden in keiner API-Antwort, keinem Log und keiner Fehlermeldung ausgegeben. Das gilt auch fuer REQ-4028 (Selbst-Passwortwechsel).
- AK-13 (Endpunkt nur Bool): Der Statusendpunkt liefert nur `show_hint` als Bool (AK-6). Keine weiteren Felder, auch nicht im Fehlerfall.
- AK-14 (Default-Passwort-Ablehnung beim Wechsel, Security-Auflage): Ein Passwortwechsel auf ein bekanntes Standardpasswort wird abgelehnt. Das gilt fuer `changeme123!` und `admin123` sowie fuer alle Werte aus REQ-4028 AK-5. Die Pruefung ist in REQ-4028 AK-5 definiert.
**TDD-Hinweis:** Backend zuerst (pytest): Flag fuer Zustaende "Standard aktiv -> true", "geaendert -> false", "kein/inaktiver Admin -> false", Schluesselmenge der Antwort. Danach Router. Frontend zuerst (Vitest/RTL): exakter Text unter beiden Feldern, Ausblenden bei `show_hint=false`, Fehlerfall ohne Blockade.
**Abhaengigkeiten:** REQ-4001 (Login-Seite und Auth-Router), REQ-4020 (Admin-Rolle, erster Nutzer ist Admin), REQ-4025 (Passwortwechsel durch Admin, Status Done/TESTED), REQ-4026 (Standard-Admin-Anlage bei Reset; Passwortwert vereinheitlicht auf `changeme123!`, Umsetzung CR-4026-01 offen)
**Blockiert:** –
**Traceability:** RISK-S-016 | project-assessment.md Punkt 6 | src/app/bootstrap.py (ensure_first_admin) | src/app/services.py (reset_database_state) | REQ-4028 (Massnahme)
**Entschieden (2026-11-03, Projektinhaber):**
- Standardpasswort einheitlich `changeme123!` (Start war bereits `changeme123!`; Reset `admin123` entfaellt per CR-4026-01).
- Risikoakzeptanz fuer den Hinweis (RISK-S-016), Folge-REQ REQ-4028 als Pflicht-Massnahme.
- Wortlaut der Hinweise: `Standardbenutzer: admin` und `Standardpasswort: changeme123! (bitte nach der ersten Anmeldung aendern)`.

**Offene Fragen (RUECKFRAGE an Nutzer / Security Architect):**
1. Release-Kopplung: Werden REQ-4027 und REQ-4028 im selben Release ausgeliefert? Empfehlung: ja. Ohne REQ-4028 bleibt der Hinweis ein offenes, akzeptiertes Risiko ohne Gegenmassnahme.
2. Security Architect: Bestaetigung, dass die Auflagen AK-10 bis AK-14 als ausreichend fuer die Risikoakzeptanz gelten (Review, kein Freigabe-Gate mehr).
3. Flag-Persistenz vs. Laufzeitpruefung: Empfehlung Flag (AK-10), damit der Statusendpunkt nicht bei jedem Aufruf Passwort-Hashes vergleicht.
4. Rate-Limit-Schwelle (AK-11) festlegen.

### REQ-4028 | Pflicht-Passwortwechsel nach Erstanmeldung
**Titel:** Erzwungener Passwortwechsel, solange der Default-Admin das Standardpasswort hat (serverseitige Sperre)
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 11+
**Risiko:** RISK-S-016 (Score 20) – Massnahme zur Risikoreduktion. Folge-REQ zu REQ-4027, dessen Hinweis unter Risikoakzeptanz durch den Projektinhaber steht.
**User Story:**
Als Administrator, der sich mit dem Standardpasswort anmeldet,
moechte ich direkt zur Passwortaenderung gefuehrt werden und erst danach G.R.E.A.T. nutzen,
damit das oeffentlich dokumentierte Standardpasswort nicht dauerhaft gueltig bleibt.
**Akzeptanzkriterien:**
- AK-1 (UI-Redirect): Given die Anmeldung mit `DEFAULT_ADMIN_PASSWORD` war erfolgreich und das Flag `default_password_active` (REQ-4027 AK-10) ist gesetzt, When das Frontend den Login abschliesst, Then wird der Nutzer auf die Seite "Passwort aendern" geleitet. Andere Seiten sind bis dahin nicht erreichbar (Route-Guard).
- AK-2 (Serverseitige Sperre): Solange das Flag gesetzt ist, liefern alle Routen ausser Login, Token-Refresh, Logout, Statusendpunkt (REQ-4027 AK-6) und dem eigenen Passwortwechsel (AK-3) HTTP 403 mit maschinenlesbarem Code `password_change_required`. Test: Endpunkt-Matrix (alle Routen x Flag gesetzt/nicht gesetzt).
- AK-3 (Eigener Passwortwechsel – Luecke): Jeder angemeldete Nutzer kann sein eigenes Passwort aendern. Eingabe: aktuelles Passwort, neues Passwort, Bestaetigung. Falsches aktuelles Passwort liefert eine klare Fehlermeldung ohne Hinweis auf den Hash. *Luecke:* Heute kann nur ein Admin Passwoerter in der Benutzerverwaltung setzen (REQ-4025, auch das eigene). Ein Selbst-Wechsel-Endpunkt und eine Seite "Passwort aendern" fuer alle Rollen fehlen. REQ-4028 schliesst diese Luecke.
- AK-4 (Mindestlaenge): Neues Passwort hat mindestens `OFFEN – Vorschlag 12 Zeichen` (siehe offene Frage 1). Die Pruefung ist serverseitig. Das Frontend zeigt die Regel vorab an.
- AK-5 (Default-Ablehnung): Ein neues Passwort wird abgelehnt, wenn es nach Trim und ohne Beruecksichtigung der Gross-/Kleinschreibung einem bekannten Standardpasswort entspricht. Startliste (Backend-Konstante): `changeme123!`, `admin123`, `admin`, `password`. Die Fehlermeldung gibt das abgelehnte Passwort nicht zurueck.
- AK-6 (Flag-Loeschen): Bei erfolgreichem Wechsel auf einen Nicht-Default-Wert wird das Flag `default_password_active` geloescht. Danach ist die Sperre (AK-2) aufgehoben und der Hinweis (REQ-4027 AK-3) verschwindet. Test: Zustandsuebergang "Standard aktiv -> geaendert".
- AK-7 (Kein Umgehen): Die Sperre gilt serverseitig. Der Frontend-Redirect allein genuegt nicht. Test: Direkter API-Aufruf mit gueltigem Token auf eine gesperrte Route liefert 403.
- AK-8 (Fehlversuche begrenzt): Fehlgeschlagene Selbst-Wechsel-Versuche (falsches aktuelles Passwort) sind rate-limitiert. Schwelle: `OFFEN` (siehe offene Frage 5).
- AK-9 (Keine Geheimnisse): Passwort, Passwort-Hash und Passwortlaenge erscheinen in keiner API-Antwort, keinem Log und keiner Fehlermeldung (wie REQ-4027 AK-12).
- AK-10 (Geltungsbereich, Stand 2026-11-03): Heute betrifft das Flag nur den Default-Admin. Die Ausweitung auf von Admins angelegte Nutzer mit Initialpasswort ist offen (siehe offene Frage 2).
**TDD-Hinweis:** Backend zuerst (pytest): Endpunkt-Matrix Flag x Route (403 ausser Ausnahmen, AK-2), Passwort-Policy-Unit-Tests (AK-4, AK-5), Zustandsuebergang (AK-6), Selbst-Wechsel verlangt aktuelles Passwort (AK-3). Danach Router. Frontend zuerst (Vitest/RTL): Redirect nach Login bei gesetztem Flag, Fehlermeldung bei abgelehntem Standardpasswort.
**Abhaengigkeiten:** REQ-4001 (Auth-Router, Token), REQ-4020 (Rollen, Sperre rollenunabhaengig), REQ-4025 (Admin-Passwortsetzung, Luecke Selbst-Wechsel), REQ-4026 (Standard-Admin-Anlage; CR-4026-01 offen), REQ-4027 (Flag, Statusendpunkt)
**Blockiert:** –
**Traceability:** RISK-S-016 | REQ-4027 (Risikoakzeptanz, AK-10 Flag, AK-6 Endpunkt) | REQ-4025 (Luecke) | REQ-4026 (CR-4026-01) | src/app/bootstrap.py | src/app/services.py
**Offene Fragen (RUECKFRAGE an Georg Hartel):**
1. Mindestlaenge: Bestaetigung von 12 Zeichen (Vorschlag Security Architect). Soll die Regel auch fuer Passwoerter gelten, die Admins in REQ-4025 setzen? Empfehlung: ja.
2. Geltungsbereich: Nur Default-Admin (heute) oder auch Nutzer mit Initialpasswort, das ein Admin vergeben hat? Empfehlung: auch diese, sonst umgeht ein Initialpasswort die Sperre.
3. UX-Ziel fuer Nicht-Admins: Sollen Editor und Viewer die Seite "Passwort aendern" in der Navigation sehen (ohne Zugang zur Benutzerverwaltung)? Empfehlung: ja. Heute gibt es fuer sie keinen Weg, das eigene Passwort zu aendern.
4. Ablehnungsliste AK-5: Startliste (`changeme123!`, `admin123`, `admin`, `password`) bestaetigen oder erweitern (Security Architect).
5. Rate-Limit-Schwellen fuer AK-8 (Fehlversuche) und REQ-4027 AK-11 (Statusendpunkt, Vorschlag 10/Minute/IP) festlegen.

---

## Aufgehobene Regeln & Umklassifizierungen

### REQ-0011 | View-Synchronitätspflicht – AUFGEHOBEN
**Aufgehoben:** 2026-06-29
**Grund:** Phase-3-Entscheidung: HTMX-Ansicht wird vollständig durch React ersetzt.
Neue Features werden ausschließlich in React entwickelt. HTMX-Ablösung ist REQ-3011.

---

### REQ-4003 | T-Wise-Algorithmus – UMKLASSIFIZIERT ZU REQ-3039
**Umklassifizierung:** 2026-07-01
**Von:** Phase 4, Sprint 2
**Zu:** Phase 3, Sprint 4 → REQ-3039 (Must statt Should)
**Grund:** Combinatorics Expert Empfehlung: T-Wise hochgestuft zu MVP-Kernfunktion.
Wird durch Classification Tree Method ersetzt (überflüssig durch T-Wise).
REQ-4003-Placeholder in Phase 4 obsolet.

---

### REQ-4002 | MCDC-Algorithmus – UMKLASSIFIZIERT ZU REQ-3044
**Umklassifizierung:** 2026-07-01
**Von:** Phase 4, Sprint 2
**Zu:** Phase 3, Sprint 4–5 → REQ-3044 (Should statt Planned-Only)
**Grund:** Combinatorics Expert Empfehlung: MCDC sollte zeitiger in Phase 3 implementiert werden.
RuleEngine-Refactor (REQ-3040) ermöglicht frühzeitige MCDC-Integration.
REQ-4002-Placeholder bleibt als Referenz, REQ-3044 ist maßgeblich.

---

# EPIC-19 – Installation & Distribution

### REQ-5001 | Windows-Installationspaket (GREAT.exe)
**Titel:** Portable Windows-EXE fuer nicht-technische Nutzer
**Prioritaet:** Must
**Status:** In Progress
**Phase:** 4, Sprint 11+
**Risiko:** RISK-B-002 (Score 16)
**Implementierung:** 2026-10-05 (DevOps Engineer Agent)
- `GREAT.spec` – PyInstaller-Spec-Datei (onefile, no-console)
- `build-exe.bat` – automatischer Build mit Smoke-Test
- `src/app/main.py` – sys.frozen-Erkennung + Auto-Browser-Start
- `src/app/config.py` – DB-Pfad-Anpassung fuer portable Modus
- `INSTALLATION.md` / `QUICKSTART.md` – Endnutzer-Dokumentation
**User Story:**
Als nicht-technisch versierter Tester
moechte ich G.R.E.A.T. durch eine einzige Datei installieren koennen
damit ich keine Entwickler-Tools (Python, Node.js, Git) benoetige und sofort starten kann.
**Akzeptanzkriterien:**
- Eine einzige Datei `GREAT.exe` (oder ein kleines Installationsarchiv < 200 MB)
- Doppelklick auf `GREAT.exe` startet den Server
- Browser wird automatisch auf `http://localhost:8000` geoeffnet
- Keine Python- oder Node.js-Installation erforderlich
- Datenbank wird beim ersten Start automatisch angelegt
- Funktioniert ohne Internetverbindung (alle Dependencies eingebettet)
- Funktioniert auf Windows 10/11 (64-bit)
- Deinstallation: einfach Datei loeschen (portable)
**Abhaengigkeiten:** REQ-1202 (Frontend-Build), REQ-4007 (GREAT_PORT)
**Technik:** PyInstaller (einzelne EXE) oder Inno Setup (Installer) – Entscheidung durch DevOps Engineer
**TDD-Hinweis:** Build-Skript testbar durch automatischen Smoke-Test (Server startet, /health antwortet, Browser oeffnet)
**Blockiert:** –

---

# EPIC-20 – Entscheidungstabelle (Decision Table Testing)

**Eingeplant:** Phase 4, Sprint 14+
**Freigegeben durch:** Georg Hartel (2026-10-05)
**Fachliche Grundlage:** `documentation/research-decision-table-istqb.md`
**Standard-Referenz:** ISTQB CTFL v4.0 Syllabus FL-4.2.3 (K3 Apply) / CTAL-TA 3.2.4 (K4 Analyse)

### Zielbild

G.R.E.A.T. unterstuetzt **Entscheidungstabellentest nach ISTQB** als eigenstaendige
Kombinatorik-Strategie. Der Tester definiert **Ursachen** (Conditions) und **Wirkungen**
(Effects), setzt optional **Constraints** (E, I, O, R, M), und das System generiert
automatisch eine Entscheidungstabelle, bei der **jede Spalte = 1 Testfall** ist.

Die Entscheidungstabelle folgt dem klassischen ISTQB-Aufbau (4 Quadranten), adaptiert
fuer G.R.E.A.T.: Ursachen als Zeilen oben, Wirkungen als Zeilen unten, jede Spalte
als Testfall mit Y/N/— (Ursachen) und X/— (Wirkungen).

**Phasen-Plan:**
- **Phase 1 (MVP):** Button, Ursache/Wirkung-Kategorien, Tabelle, Boolean-Generierung, Auto-Generierung, andere Funktionen ausgrauen
- **Phase 2:** Constraints (E, I, O, R, M) mit Dialog
- **Phase 3:** Collapsing (Regel-Zusammenfassung), Checksum-Validierung, Extended Entry, Don't Care, Widerspruchserkennung, Vollstaendigkeitspruefung
- **Phase 4:** Cause-Effect-Graph-Visualisierung, Priorisierung von Wirkungen (Override)

**Nutzerentscheidungen (Georg Hartel, 2026-10-05):**
- Eigenstaendiges EPIC (nicht Teil von EPIC-06)
- Explizite Wahl Ursache/Wirkung bei jeder neuen Kategorie
- G.R.E.A.T.-adaptiertes Tabellenformat (nicht 1:1 ISTQB-Quadranten, aber fachlich korrekt)
- Boolean (Ja/Nein) als Default, Extended Entry fuer multiple Werte
- Constraints ueber separaten Dialog, mehrere Ursachen waehlbar
- Kein Hard-Limit fuer Ursachen, nur durch globales Max-Testfaelle-Limit (REQ-4018) begrenzt
- Wirkungen: Binär (X/—) als Default, Text als Option
- **Tabelle-Fuellung:** Ursachen-Bereich wird automatisch mit allen Kombinationen gefuellt. Wirkungen-Bereich bleibt initial komplett leer. Tester tragt manuell ein, welche Wirkung auf welche Ursachen-Kombination zutrifft.
- Andere Kombinatorik-Funktionen ausgegraut im Entscheidungstabelle-Modus

---

### REQ-5000 | Entscheidungstabelle-Button in Kategorien & Werte
**Titel:** Button „Entscheidungstabelle" in der Kategorien & Werte-Ansicht
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich einen Button „Entscheidungstabelle" in der Kategorien & Werte-Ansicht sehen
damit ich den Entscheidungstabelle-Modus starten kann.
**Akzeptanzkriterien:**
- Neuer Button „Entscheidungstabelle" ist in der Kategorien & Werte-Ansicht sichtbar
- Klick auf den Button schaltet in den Entscheidungstabelle-Modus
- Im Modus sind nur Kategorien vom Typ „Ursache" oder „Wirkung" relevant
- Kategorien vom Typ „Standard" (nicht Ursache/Wirkung) werden ignoriert
- Der Button ist deaktiviert, wenn keine Ursache- und keine Wirkungskategorie existiert
**Abhaengigkeiten:** REQ-5002 (Kategorie-Typ Ursache/Wirkung)
**Traceability:** documentation/research-decision-table-istqb.md §2 (Tabellarischer Aufbau)

---

### REQ-5002 | Kategorie-Typ: Ursache/Wirkung (explizite Wahl)
**Titel:** Explizite Wahl „Ursache" oder „Wirkung" bei jeder neuen Kategorie
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich bei jeder neuen Kategorie explizit waehlen koennen, ob sie eine Ursache (Condition) oder eine Wirkung (Effect) ist
damit das System weiss, welche Kategorien in den oberen und welche in den unteren Teil der Entscheidungstabelle gehoeren.
**Akzeptanzkriterien:**
- Beim Anlegen einer neuen Kategorie erscheint ein Auswahlmenue: „Standard" | „Ursache" | „Wirkung"
- Default ist „Standard" (bisheriges Verhalten)
- Ursache-Kategorien erscheinen im oberen Teil (Condition Stubs) der Entscheidungstabelle
- Wirkung-Kategorien erscheinen im unteren Teil (Action Stubs) der Entscheidungstabelle
- Standard-Kategorien werden im Entscheidungstabelle-Modus ignoriert
- Die Typzuordnung ist nachtraeglich aenderbar (Umbenennen-Dropdown)
**Abhaengigkeiten:** REQ-0300 (Kategorie anlegen)
**Traceability:** documentation/research-decision-table-istqb.md §2 (Tabellarischer Aufbau), Nutzerentscheidung 2026-10-05

---

### REQ-5003 | Entscheidungstabelle-Layout (Ursachen oben, Wirkungen unten)
**Titel:** G.R.E.A.T.-adaptiertes Entscheidungstabelle-Layout
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich die Entscheidungstabelle mit Ursachen oben und Wirkungen unten sehen
damit ich die logische Struktur (Wenn Ursachen → Dann Wirkungen) intuitiv erfassen kann.
**Akzeptanzkriterien:**
- Obere Sektion: Zeilen fuer jede Ursache-Kategorie (Condition Stubs)
- Untere Sektion: Zeilen fuer jede Wirkung-Kategorie (Action Stubs)
- Spalten repraesentieren Regeln/Testfaelle (R1, R2, R3, ...)
- Ursachenzellen werden **automatisch** mit Y (Ja), N (Nein) oder Extended-Entry-Werten gefuellt (alle Kombinationen)
- Wirkungszellen sind **initial komplett leer** (kein Vorbelegen, kein —)
- Der Tester tragt **manuell** ein, welche Wirkung auf welche Ursachen-Kombination zutrifft
- Trennlinie zwischen Ursachen- und Wirkungsbereich ist sichtbar
- Tabelle ist horizontal scrollbar bei vielen Regeln
**Abhaengigkeiten:** REQ-5000, REQ-5002, REQ-5004
**Traceability:** documentation/research-decision-table-istqb.md §2 (4 Quadranten), §3 (Entscheidungslogik)

---

### REQ-5004 | Boolean-Werte als Default (Ja/Nein)
**Titel:** Boolean-Werte (Ja/Nein) als Default fuer Ursache-Kategorien
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich dass Ursache-Kategorien standardmaessig Boolean-Werte (Ja/Nein) verwenden
damit ich Entscheidungstabellen schnell aufsetzen kann ohne jede Ursache manuell zu konfigurieren.
**Akzeptanzkriterien:**
- Jede Ursache-Kategorie hat automatisch zwei Werte: „Ja" (Y) und „Nein" (N)
- Diese Werte sind im Entscheidungstabelle-Modus als Y/N in den Zellen sichtbar
- Der Tester kann die Bezeichnungen anpassen (z.B. „Wahr"/„Falsch")
- Die interne Repraesentation bleibt Y/N
- Don't Care (—) ist als dritter Zustand verfuegbar (manuell, REQ-5016)
**Abhaengigkeiten:** REQ-5002, REQ-0302 (Wert anlegen)
**Traceability:** documentation/research-decision-table-istqb.md §3 (Condition Entries: Y/N/—)

---

### REQ-5005 | Automatische Regelgenerierung (alle gueltigen Kombinationen)
**Titel:** Automatische Generierung aller gueltigen Ursachenkombinationen
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich dass das System automatisch alle gueltigen Kombinationen der Ursachen generiert
damit ich keine manuelle Kombinatorik durchfuehren muss und jede Spalte der Tabelle einem Testfall entspricht.
**Akzeptanzkriterien:**
- Bei N Ursachen werden 2^N Kombinationen generiert (vollstaendige Entscheidungstabelle)
- Jede Kombination wird als eigene Spalte (Regel R1, R2, ...) dargestellt
- **Ursachen-Bereich:** Pro Spalte sind die Ursachenzellen **automatisch** mit Y oder N gefuellt (oder Extended-Entry-Werten)
- **Wirkungen-Bereich:** Die Wirkungszellen sind **initial komplett leer** (kein Vorbelegen)
- Der Tester tragt **manuell** in jede Wirkungszelle ein, welche Wirkung auf die Ursachen-Kombination in dieser Spalte zutrifft
- Optional: Regeln koennen definiert werden (z.B. "Wenn C1=Y UND C2=N → E1"), die dann Wirkungszellen automatisch fuellen
- Die Anzahl der generierten Spalten respektiert das globale Max-Testfaelle-Limit (REQ-4018)
- Bei Uberschreitung des Limits: Warnung und Abbruch der Generierung
**Abhaengigkeiten:** REQ-5000, REQ-5002, REQ-5003, REQ-5004, REQ-4018
**Traceability:** documentation/research-decision-table-istqb.md §8 (Algorithmische Generierung), §8 (Maximale Anzahl Regeln)

---

### REQ-5006 | Andere Kombinatorik-Funktionen ausgrauen
**Titel:** Andere Kombinatorik-Strategien im Entscheidungstabelle-Modus ausgrauen
**Prioritaet:** Must
**Status:** Planned
**Phase:** 4, Sprint 14 (P1 – MVP)
**User Story:**
Als Tester
moechte ich dass andere Kombinatorik-Strategien (Pairwise, All Combinations, etc.) im Entscheidungstabelle-Modus ausgegraut sind
damit ich nicht versehentlich eine falsche Strategie auswaehle und die Entscheidungstabelle ueberschreibe.
**Akzeptanzkriterien:**
- Im Entscheidungstabelle-Modus sind alle anderen Kombinatorik-Buttons ausgegraut (disabled)
- Versucht der Nutzer eine andere Strategie auszuwaelen, erscheint ein Hinweis: „Entscheidungstabelle-Modus aktiv – andere Strategien sind nicht verfuegbar"
- Der Nutzer kann den Entscheidungstabelle-Modus verlassen, um zurueck zur normalen Kombinatorik zu wechseln
- Die Entscheidungstabelle-Daten bleiben gespeichert und sind nach Ruecksprung wiederherstellbar
**Abhaengigkeiten:** REQ-5000, REQ-0800-0807 (bestehende Kombinatorik-Strategien)
**Traceability:** Nutzerentscheidung 2026-10-05

---

### REQ-5007 | Constraint E (Exclusive)
**Titel:** Exclusive-Constraint (maximal eine Ursache kann wahr sein)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich fuer eine Gruppe von Ursachen ein Exclusive-Constraint setzen
damit Kombinationen, bei denen mehr als eine Ursache gleichzeitig wahr ist, als ungueltig markiert und aus der Tabelle entfernt werden.
**Akzeptanzkriterien:**
- Der Constraint E (Exclusive) kann fuer 2 oder mehr Ursachen zugewiesen werden
- Nach Anwendung: Alle Regeln, bei denen 2+ der betroffenen Ursachen Y sind, werden entfernt
- Regeln, bei denen keine oder genau eine der Ursachen Y ist, bleiben erhalten
- Die entfernten Regeln erscheinen nicht in der generierten Tabelle
- Der Constraint ist in der UI sichtbar (Symbol + Beschreibung)
**Abhaengigkeiten:** REQ-5012 (Constraint-Dialog), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen: Exclusive/E)

---

### REQ-5008 | Constraint O (One-and-Only-One)
**Titel:** One-and-Only-One-Constraint (genau eine Ursache muss wahr sein)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich fuer eine Gruppe von Ursachen ein One-and-Only-One-Constraint setzen
damit nur Kombinationen, bei denen genau eine Ursache wahr ist, als gueltig gelten.
**Akzeptanzkriterien:**
- Der Constraint O (One-and-Only-One) kann fuer 2 oder mehr Ursachen zugewiesen werden
- Nach Anwendung: Alle Regeln, bei denen 0 oder 2+ der betroffenen Ursachen Y sind, werden entfernt
- Regeln, bei denen genau eine der Ursachen Y ist, bleiben erhalten
- Die entfernten Regeln erscheinen nicht in der generierten Tabelle
- Der Constraint ist in der UI sichtbar (Symbol + Beschreibung)
**Abhaengigkeiten:** REQ-5012 (Constraint-Dialog), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen: One-and-Only-One/O)

---

### REQ-5009 | Constraint I (Inclusive)
**Titel:** Inclusive-Constraint (mindestens eine Ursache muss wahr sein)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich fuer eine Gruppe von Ursachen ein Inclusive-Constraint setzen
damit Kombinationen, bei denen keine der Ursachen wahr ist, als ungueltig markiert und entfernt werden.
**Akzeptanzkriterien:**
- Der Constraint I (Inclusive) kann fuer 2 oder mehr Ursachen zugewiesen werden
- Nach Anwendung: Alle Regeln, bei denen alle betroffenen Ursachen N sind, werden entfernt
- Regeln, bei denen mindestens eine der Ursachen Y ist, bleiben erhalten
- Die entfernten Regeln erscheinen nicht in der generierten Tabelle
- Der Constraint ist in der UI sichtbar (Symbol + Beschreibung)
**Abhaengigkeiten:** REQ-5012 (Constraint-Dialog), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen: Inclusive/I)

---

### REQ-5010 | Constraint R (Requires)
**Titel:** Requires-Constraint (Wenn C1 wahr, dann muss C2 auch wahr sein)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich einen Requires-Constraint zwischen zwei Ursachen setzen
damit Kombinationen, bei denen die erste Ursache wahr aber die zweite falsch ist, als ungueltig entfernt werden.
**Akzeptanzkriterien:**
- Der Constraint R (Requires) wird zwischen zwei Ursachen C1 → C2 zugewiesen
- Nach Anwendung: Alle Regeln, bei denen C1=Y und C2=N, werden entfernt
- Regeln, bei denen C1=N (C2 beliebig) oder C1=Y und C2=Y, bleiben erhalten
- Die Richtung des Constraints ist in der UI sichtbar (Pfeil C1 → C2)
- Der Constraint ist in der UI sichtbar (Symbol + Beschreibung)
**Abhaengigkeiten:** REQ-5012 (Constraint-Dialog), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen: Requires/R)

---

### REQ-5011 | Constraint M (Mask)
**Titel:** Mask-Constraint (Wenn Wirkung E1, dann E2 erzwungen falsch)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich einen Mask-Constraint zwischen zwei Wirkungen setzen
damit in allen Regeln, wo E1=X, automatisch E2=— gesetzt wird.
**Akzeptanzkriterien:**
- Der Constraint M (Mask) wird zwischen zwei Wirkungen E1 → E2 zugewiesen
- Nach Anwendung: In allen Regeln, wo E1=X, wird E2 auf — gesetzt
- Die Richtung des Constraints ist in der UI sichtbar (Pfeil E1 → E2)
- Der Constraint ist in der UI sichtbar (Symbol + Beschreibung)
- Der Constraint wirkt nur auf Wirkungszellen, nicht auf Ursachenzellen
**Abhaengigkeiten:** REQ-5012 (Constraint-Dialog), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen: Mask/M), §6 (Inhibitors/Mask)

---

### REQ-5012 | Constraint-Dialog (mehrere Ursachen waehlbar)
**Titel:** Separater Dialog zur Definition von Constraints
**Prioritaet:** Must
**Status:** In Progress (Backend: CRUD-API + persist. Speicherung + /generate-Integration abgeschlossen; Frontend-Dialog: offen, UX-Lead)
**Phase:** 4, Sprint 15 (P2 – Constraints)
**User Story:**
Als Tester
moechte ich in einem separaten Dialog mehrere Ursachen oder Wirkungen auswaehlen und einen Constraint-Typ zuweisen
damit ich logische Beziehungen zwischen Bedingungen und Aktionen einfach definieren kann.
**Akzeptanzkriterien:**
- Dialog oeffnet sich per Button „Constraint hinzufuegen" in der Entscheidungstabelle-Ansicht
- Links: Auswahlliste aller Ursache- und Wirkungskategorien (Checkboxen, Mehrfachauswahl)
- Rechts: Dropdown fuer Constraint-Typ (E, I, O, R, M)
- Bei R (Requires) und M (Mask): genau 2 Eintraege erforderlich (Richtung C1→C2 bzw. E1→E2)
- Bei E, I, O: mindestens 2 Eintraege erforderlich (Gruppe)
- Validierung: Ungueltige Kombinationen (z.B. R mit 3 Ursachen) werden abgelehnt mit Hinweis
- Nach Bestaetigung: Constraints werden angewendet, Tabelle aktualisiert
- Liste aller aktiven Constraints ist sichtbar und editierbar
**Abhaengigkeiten:** REQ-5007-5011 (Constraint-Typen), REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §5 (Constraint-Typen), Nutzerentscheidung 2026-10-05

---

### REQ-5013 | Automatische Reduktion (Collapsing)
**Titel:** Automatisches Zusammenfassen redundanter Regeln (Collapsing)
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich dass das System automatisch redundante Regeln zusammenfasst
damit die Entscheidungstabelle kompakter wird und weniger Testfaelle notwendig sind.
**Akzeptanzkriterien:**
- Zwei Regeln koennen zusammengefasst werden wenn:
  1. Identische Aktionen (Wirkungen) in beiden Regeln
  2. Genau eine Ursache unterscheidet sich zwischen den Regeln
  3. Zusammen genommen decken sie alle Werte dieser einen Ursache ab (Y und N)
- Die unterscheidende Ursache wird in der zusammengefassten Regel zu Don't Care (—)
- Der Vorgang ist wiederholbar (kaskadierendes Collapsing)
- Der Nutzer kann Collapsing als Option aktivieren/deaktivieren
- Nach Collapsing: Anzahl der reduzierten Regeln wird angezeigt
**Abhaengigkeiten:** REQ-5005, REQ-5017 (Don't Care)
**Traceability:** documentation/research-decision-table-istqb.md §4 (Collapsing: 3 strenge Bedingungen)

---

### REQ-5014 | Checksum-Validierung
**Titel:** Checksum-Validierung der Entscheidungstabelle
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich eine Checksum-Validierung meiner Entscheidungstabelle sehen
damit ich erkenne, ob die Tabelle vollstaendig, lueckenhaft oder ueberschneidend ist.
**Akzeptanzkriterien:**
- Checksum = Summe(2^(Anzahl Don't-Care pro Regel)) fuer alle Regeln
- Vergleich mit 2^n (n = Anzahl Ursachen):
  - = 2^n → Gruenes Symbol „Vollstaendig" (Notwendige Bedingung erfueellt)
  - > 2^n → Gelbes Symbol „Uberschneidungen" (Overlap)
  - < 2^n → Rotes Symbol „Luecken" (Gap)
- Die Checksum wird nach jeder Aenderung (Constraints, Collapsing) neu berechnet
- Hinweis: „Checksum allein beweist weder Vollstaendigkeit noch Widerspruchsfreiheit"
**Abhaengigkeiten:** REQ-5005, REQ-5013 (Collapsing), REQ-5017 (Don't Care)
**Traceability:** documentation/research-decision-table-istqb.md §4 (Checksum-Validierung)

---

### REQ-5015 | Extended Entry (multiple Werte pro Ursache)
**Titel:** Extended Entry – Multiple Werte pro Ursache (z.B. T-Shirt-Größen)
**Prioritaet:** Could
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich Ursachen mit mehr als zwei Werten definieren koennen (z.B. S/M/L/XL)
damit ich auch nicht-boolesche Bedingungen in Entscheidungstabellen abbilden kann.
**Akzeptanzkriterien:**
- Ursache-Kategorien koennen optional mehr als 2 Werte haben (Extended Entry)
- Die Werte erscheinen in der Ursachenzeile als Dropdown pro Zelle
- Bei der Generierung wird das kartesische Produkt aller Ursache-Werte berechnet
- Die Anzahl der Regeln ist das Produkt der Wertemengen aller Ursachen
- Boolean (Ja/Nein) bleibt der Default; Extended Entry ist eine Option
- Die Werte sind in der Tabelle als Text sichtbar (nicht Y/N)
**Abhaengigkeiten:** REQ-5002, REQ-5004, REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §3 (Condition Entries), Nutzerentscheidung 2026-10-05

---

### REQ-5016 | Wirkungen als Text (nicht nur binär)
**Titel:** Wirkungen als Freitext statt nur binär (X/—)
**Prioritaet:** Could
**Status:** Implemented

---

### REQ-5017 | Don't Care manuell setzen
**Titel:** Manuelles Setzen von Don't Care (—) in Ursachenzellen
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich in Ursachenzellen manuell „Don't Care" (—) setzen koennen
damit ich ausdruecken kann, dass eine Bedingung fuer eine bestimmte Regel irrelevant ist.
**Akzeptanzkriterien:**
- Jede Ursachenzelle kann drei Werte annehmen: Y (Ja), N (Nein), — (Don't Care)
- Don't Care wird durch Klick auf die Zelle oder per Dropdown gesetzt
- Visuell: — ist grau hinterlegt oder mit einem Dash-Symbol dargestellt
- Don't Care bedeutet: Diese Bedingung ist fuer die Regel irrelevant (beide Y und N moeglich)
- Bei der Testfall-Generierung: Don't Care-Werte werden als „beliebig" behandelt
- Manuelles Setzen ist auch nach automatischer Generierung moeglich
**Abhaengigkeiten:** REQ-5003, REQ-5004, REQ-5005
**Traceability:** documentation/research-decision-table-istqb.md §3 (Condition Entries: — Don't Care)

---

### REQ-5018 | Cause-Effect-Graph-Visualisierung
**Titel:** Graphische Visualisierung der Cause-Effect-Beziehungen
**Prioritaet:** Could
**Status:** In Progress (Backend-Daten implementiert, Frontend-Visualisierung offen)
**Phase:** 4, Sprint 17 (P4 – Graph)
**User Story:**
Als Tester
moechte ich eine grafische Visualisierung der Cause-Effect-Beziehungen sehen
damit ich die logischen Zusammenhaenge zwischen Ursachen, Constraints und Wirkungen intuitiv erfassen kann.
**Akzeptanzkriterien:**
- Graphische Darstellung: Ursachen als Knoten links, Wirkungen als Knoten rechts
- Constraints werden als Kanten zwischen Knoten dargestellt (farbig nach Typ: E=rot, I=gruen, O=blau, R=orange, M=lila)
- Boolesche Operatoren (AND, OR, NOT) werden als Zwischenknoten dargestellt
- Der Graph ist interaktiv (Zoom, Drag, Hover-Info)
- Der Graph kann aus der Entscheidungstabelle generiert und zurueck exportiert werden
- Der Graph dient als Denkwerkzeug („The graph is the thinking tool")
**Abhaengigkeiten:** REQ-5002, REQ-5007-5011 (Constraints), REQ-5003
**Traceability:** documentation/research-decision-table-istqb.md §1 (Cause-Effect Graphing vs. Decision Table Testing), §5 (5-Stufen-Prozess)

---

### REQ-5019 | Widerspruchserkennung
**Titel:** Erkennung von widerspruechlichen Regeln in der Entscheidungstabelle
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich sofort gewarnt werden, wenn zwei Regeln mit identischen oder ueberlappenden Bedingungen unterschiedliche Wirkungen haben
damit ich inkonsistente Entscheidungstabellen erkenne und korrigieren kann.
**Akzeptanzkriterien:**
- Zwei Regeln mit identischen Ursacheneintraegen (Y/N/—) aber unterschiedlichen Wirkungseintraegen → Widerspruch
- Ueberlappende Regeln (durch Don't Care) mit unterschiedlichen Wirkungen → Widerspruch
- M-Constraint-Verletzung (E1=X und E2=X, obwohl M(E1→E2) gilt) → Widerspruch
- Widersprueche werden rot markiert mit Hinweis: „Regel R_X und R_Y widersprechen sich"
- Der Widerspruch wird bei jeder Aenderung neu geprueft
- Speichern ist trotzdem moeglich (Warnung, kein Hard-Block)
**Abhaengigkeiten:** REQ-5003, REQ-5005, REQ-5011 (Mask), REQ-5017 (Don't Care)
**Traceability:** documentation/research-decision-table-istqb.md §8 (Widerspruchserkennung)

---

### REQ-5020 | Vollstaendigkeitspruefung (Luecken-Erkennung)
**Titel:** Pruefung auf ungedeckte gueltige Kombinationen
**Prioritaet:** Should
**Status:** Planned
**Phase:** 4, Sprint 16 (P3 – Optimierung)
**User Story:**
Als Tester
moechte ich erkennen, wenn gueltige Ursachenkombinationen in der Entscheidungstabelle nicht abgedeckt sind
damit ich Luecken in meiner Testabdeckung erkenne und schließe.
**Akzeptanzkriterien:**
- Das System prueft, ob alle gueltigen Kombinationen (nach Constraint-Filterung) in der Tabelle vertreten sind
- Fehlt eine Kombination: Roter Hinweis „Luecke: Kombination [Ursachenwerte] ist nicht abgedeckt"
- Checksum < 2^n (nach Constraint-Filterung) → Hinweis auf moegliche Luecken
- Gueltige Kombination ohne zugeordnete Aktion → Hinweis „Keine Wirkung definiert"
- Der Tester kann fehlende Regeln automatisch hinzufuegen lassen (Button „Luecken schliessen")
- Die Pruefung laeuft nach jeder Aenderung automatisch
**Abhaengigkeiten:** REQ-5005, REQ-5007-5011 (Constraints), REQ-5014 (Checksum)
**Traceability:** documentation/research-decision-table-istqb.md §8 (Vollstaendigkeitspruefung)

---

### REQ-5021 | Priorisierung von Wirkungen (Override)
**Titel:** Priorisierung von Wirkungen bei mehreren gleichzeitig aktiven Wirkungen
**Prioritaet:** Could
**Status:** In Progress (Backend-Logik implementiert, UI-Prioritaetsanzeige offen)
**Phase:** 4, Sprint 17 (P4 – Graph)
**User Story:**
Als Tester
moechte ich Wirkungen priorisieren koennen, sodass bei mehreren gleichzeitig aktiven Wirkungen eine bestimmte Wirkung Vorrang hat
damit ich Superposition/Override-Szenarien korrekt abbilden kann.
**Akzeptanzkriterien:**
- Jede Wirkung kann eine Prioritaet (1=hoechst, N=niedrigst) zugewiesen bekommen
- Wenn in einer Regel mehrere Wirkungen X sind, gewinnt die hoechst-priorisierte
- Niedriger-priorisierte Wirkungen werden zu — (Don't Care)
- Die Priorisierung wird in der UI sichtbar (Prioritaetsnummer neben Wirkung)
- Fruehe Validierungsfehler (hohe Prioritaet) machen spaetere Bedingungen zu Don't Care → Tabellenreduktion
- Die Priorisierung wirkt nur im Override-Modus (opt-in)
**Abhaengigkeiten:** REQ-5002, REQ-5003, REQ-5011 (Mask)
**Traceability:** documentation/research-decision-table-istqb.md §6 (Superposition/Override, Priority/Precedence)

---

### Hinweis zur EPIC-Nummerierung

Der Nutzer hat EPIC-19 gewuenscht. EPIC-19 existiert bereits (Installation & Distribution, REQ-5001).
Dieses neue EPIC wurde als **EPIC-20** angelegt, um die Nummerierungskollision zu vermeiden.
**REQ-5001** bleibt dem bestehenden EPIC-19 (Installation) zugeordnet.
Die neuen REQs beginnen mit **REQ-5000** und enden bei **REQ-5021**.