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
- Berechnung basiert auf Summe der risk_weight aller erzeugten Testfaelle geteilt durch Summe aller moeglichen Werte

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
**Status:** Planned
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

### REQ-4001 | Authentifizierung (OAuth2/JWT)
**Phase:** 4, Sprint 1 | **Status:** Planned

### REQ-4004 | Business Rule Based Testing
**Phase:** 4, Sprint 2 | **Status:** Planned

### REQ-4005 | Ollama/LLM-Integration
**Phase:** 4, Sprint 3 | **Status:** Planned

### REQ-4006 | Multi-User (PostgreSQL optional)
**Phase:** 4, Sprint 4 | **Status:** Planned

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