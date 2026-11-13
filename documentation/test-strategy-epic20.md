# Teststrategie EPIC-20 – Entscheidungstabelle (Decision Table Testing)

**Projekt:** G.R.E.A.T. (Georg Radikal Einfacher Automatisierter TestcaseDesigner)
**EPIC:** EPIC-20 – Entscheidungstabelle (REQ-5000 bis REQ-5021)
**Autor:** GREAT QA Director
**Datum:** 2026-10-05
**Status:** Draft – zur Freigabe durch Orchestrator
**Sprint-Zuordnung:** Sprint 14-17 (Phase 4)

---

## 1. Einleitung und Ziel

Diese Teststrategie definiert den vollständigen Testansatz für EPIC-20 (Entscheidungstabelle),
eine neue Kombinatorik-Strategie nach ISTQB CTFL v4.0 FL-4.2.3 / CTAL-TA 3.2.4.

### 1.1 Ziel

- **Fachliche Korrektheit:** Alle Algorithmen (Generierung, Constraints, Collapsing, Checksum,
  Widerspruchserkennung, Vollstaendigkeit) sind mathematisch nach ISTQB korrekt implementiert.
- **Testbarkeit:** Jeder REQ hat mindestens einen zugeordneten Test (Unit, Integration, oder E2E).
- **Nachvollziehbarkeit:** Jeder Test tragt eine TEST-ID und referenziert den zugehoerigen REQ.
- **Regression:** Bestehende Kombinatorik-Strategien (Pairwise, All Combinations, etc.) werden
  durch EPIC-20 nicht beeintraechtigt.

### 1.2 Scope

| Bereich | Im Scope | Nicht im Scope |
|---|---|---|
| Backend (Python) | Entscheidungstabelle-Logik, Constraints, Collapsing, Checksum, Extended Entry, Widerspruchserkennung, Vollstaendigkeit | |
| Frontend (React) | Button, Tabelle-Layout, Constraint-Dialog, Graph-Visualisierung, Don't Care UI, Extended Entry UI | |
| E2E (Playwright) | Komplette Workflows pro Phase | |
| API-Tests | REST-Endpunkte fuer Entscheidungstabelle | |
| Mutation Testing | Nach P1 als Optional | In P1-P4 nicht erforderlich |

### 1.3 Test-Pyramide EPIC-20

```
        /    \
       /  E2E \        ~10-15 Tests (kritische Pfade pro Phase)
      /________\
     /          \
    / Integration \     ~20-30 Tests (API-Endpunkte, Store-Integration)
   /______________\
  /                \
 /     Unit Tests    \  ~120-150 Tests (Backend + Frontend)
/____________________\
```

---

## 2. Test-Level Matrix (alle 21 REQs)

Jeder REQ wird auf den relevanten Test-Leveln abgedeckt. Die Spalten geben an,
welche Test-Arten fuer den jeweiligen REQ erforderlich sind.

### Legende

| Symbol | Bedeutung |
|---|---|
| **U-B** | Unit-Test Backend (pytest) |
| **U-F** | Unit-Test Frontend (Vitest + RTL) |
| **I** | Integration-Test (API / Store-Integration) |
| **E2E** | End-to-End-Test (Playwright) |
| **PBT** | Property-Based-Testing (hypothesis) |
| - | Nicht erforderlich |

### 2.1 Phase 1 (MVP) – Sprint 14

| REQ | Titel | U-B | U-F | I | E2E | PBT | Schatz Tests |
|---|---|---|---|---|---|---|---|
| **REQ-5000** | Entscheidungstabelle-Button | - | Button sichtbar/klickbar/disabled | - | Button-Workflow (Moduswechsel) | - | 4 |
| **REQ-5002** | Kategorie-Typ: Ursache/Wirkung | CRUD: Typ anlegen/lesen/aendern/loeschen | Typ-Auswahlmenue (Standard/Ursache/Wirkung), Umbenennen-Dropdown | API: Kategorie mit Typ erstellen/lesen/aendern | Kategorie anlegen → Typ sichtbar in Tabelle | - | 10 |
| **REQ-5003** | Entscheidungstabelle-Layout | Tabelle-Generierung (Ursachen auto, Wirkungen leer), Spalten-Anzahl | Tabelle-Rendering (Ursachen oben, Wirkungen unten, Trennlinie, Scroll) | API: Tabelle generieren und zurueckgeben | Kompletter Workflow: Button → Tabelle erscheint → Ursachen gefuellt → Wirkungen leer | - | 12 |
| **REQ-5004** | Boolean-Werte als Default | Y/N Default-Werte pro Ursache, interne Repraesentation | Y/N Anzeige in Zellen, Bezeichnung anpassen | API: Default-Werte liefern | - | - | 8 |
| **REQ-5005** | Automatische Regelgenerierung (2^n) | 2^n Generierung, Max-Testfaelle-Limit (REQ-4018), Warnung bei Uberschreitung | Generierte Spalten korrekt dargestellt | API: Generierung mit/ohne Limit | Generierung ausfuehren → Spalten-Anzahl korrekt | Ja (groessere n) | 15 |
| **REQ-5006** | Andere Kombinatorik ausgrauen | - | Andere Buttons disabled, Hinweis bei Klick, Modus verlassen | API: Modus-Status | Moduswechsel → andere Strategien ausgegraut | - | 6 |

**P1 Gesamt: ~55 Tests**

### 2.2 Phase 2 (Constraints) – Sprint 15

| REQ | Titel | U-B | U-F | I | E2E | PBT | Schatz Tests |
|---|---|---|---|---|---|---|---|
| **REQ-5007** | Constraint E (Exclusive) | E-Filter: 0 oder 1 Y erlaubt, 2+ Y entfernt, Edge-Cases | Constraint E in UI sichtbar (Symbol + Beschreibung) | API: E-Constraint anwenden | Constraint E definieren → Tabelle aktualisiert | Ja (Kombinationen) | 12 |
| **REQ-5008** | Constraint O (One-and-Only-One) | O-Filter: genau 1 Y, 0 oder 2+ entfernt | Constraint O in UI sichtbar | API: O-Constraint anwenden | Constraint O definieren → Tabelle aktualisiert | Ja | 12 |
| **REQ-5009** | Constraint I (Inclusive) | I-Filter: mind. 1 Y, alle-N entfernt | Constraint I in UI sichtbar | API: I-Constraint anwenden | Constraint I definieren → Tabelle aktualisiert | Ja | 12 |
| **REQ-5010** | Constraint R (Requires) | R-Filter: C1=Y → C2=Y, C1=Y/C2=N entfernt, Richtung C1→C2 | Constraint R mit Pfeil C1→C2 sichtbar | API: R-Constraint anwenden | Constraint R definieren → Tabelle aktualisiert | Ja | 12 |
| **REQ-5011** | Constraint M (Mask) | M-Filter: E1=X → E2=—, nur Wirkungen, Richtung E1→E2 | Constraint M mit Pfeil E1→E2 sichtbar | API: M-Constraint anwenden | Constraint M definieren → Wirkungen aktualisiert | Ja | 12 |
| **REQ-5012** | Constraint-Dialog | Validierung: R/M=2 Eintraege, E/I/O>=2, ungültige Kombinationen ablehnen | Dialog oeffnen/schliessen, Mehrfachauswahl, Dropdown, Validierungsfehler | API: Constraints erstellen/listen/loeschen/aendern | Dialog oeffnen → Constraint definieren → Bestaetigen → Tabelle aktualisiert | - | 15 |

**P2 Gesamt: ~75 Tests**

### 2.3 Phase 3 (Optimierung) – Sprint 16

| REQ | Titel | U-B | U-F | I | E2E | PBT | Schatz Tests |
|---|---|---|---|---|---|---|---|
| **REQ-5013** | Collapsing (Reduktion) | 3 Bedingungen (identische Aktionen, 1 Unterschied, volle Abdeckung), kaskadierend, Don't Care-Ergebnis | Collapsing-Option aktivieren/deaktivieren, reduzierte Anzahl anzeigen | API: Collapsing anwenden | Collapsing aktivieren → Tabelle reduziert → Checksum gueltig | Ja (kaskadierend) | 15 |
| **REQ-5014** | Checksum-Validierung | Checksum-Berechnung (Summe(2^DC)), Vergleich mit 2^n, 3 Ergebnisse (vollstaendig/overlap/gap), Neuberechnung nach Aenderung | Checksum-Symbol (gruen/gelb/rot) + Hinweis | API: Checksum berechnen | - | Ja (verschiedene DC-Konfigurationen) | 12 |
| **REQ-5015** | Extended Entry | Kartesisches Produkt mit >2 Werten, Wert-Anzahl als Produkt, Boolean als Default | Dropdown pro Zelle, Werte als Text sichtbar | API: Extended Entry generieren | Extended Entry konfigurieren → Tabelle mit multiplen Werten | Ja | 12 |
| **REQ-5016** | Wirkungen als Text | Freitext-Werte statt X/—, Default bleibt binär, Export mit Text | Eingabefeld/Dropdown in Wirkungszelle | API: Text-Werte speichern/lesen | - | - | 8 |
| **REQ-5017** | Don't Care manuell setzen | Y/N/— pro Zelle, — bedeutet "beliebig", manuell nach Generierung | Klick/Dropdown fuer —, grau hinterlegt | API: Don't Care setzen/lesen | Don't Care manuell setzen → Checksum aktualisiert | - | 10 |
| **REQ-5019** | Widerspruchserkennung | Identische Bedingungen + verschiedene Wirkungen, ueberlappende (DC) + verschiedene Wirkungen, M-Constraint-Verletzung, Neuberechnung | Rot markiert + Hinweis "Regel R_X und R_Y widersprechen sich", Speichern mit Warnung | API: Widerspruch pruefen | Widerspruch erzeugen → Warnung erscheint | Ja (DC-Überlappungen) | 15 |
| **REQ-5020** | Vollstaendigkeitspruefung | Gueltige Kombinationen nach Constraint-Filterung pruefen, Luecken melden, "Luecken schliessen" Button, automatische Pruefung | Roter Hinweis "Luecke: Kombination [...] nicht abgedeckt", "Keine Wirkung definiert" | API: Vollstaendigkeit pruefen | Luecke erzeugen → Hinweis erscheint → "Luecken schliessen" | Ja | 12 |

**P3 Gesamt: ~84 Tests**

### 2.4 Phase 4 (Graph) – Sprint 17

| REQ | Titel | U-B | U-F | I | E2E | PBT | Schatz Tests |
|---|---|---|---|---|---|---|---|
| **REQ-5018** | Cause-Effect-Graph | Graph-Generierung aus Tabelle/Knoten/Kanten, farbliche Constraint-Darstellung, Boolesche Operatoren als Zwischenknoten | Graph-Rendering, Zoom, Drag, Hover-Info, Interaktivitaet | API: Graph-Daten generieren | Graph aus Tabelle generieren → Graph zurueck in Tabelle | - | 12 |
| **REQ-5021** | Priorisierung von Wirkungen | Prioritaet 1..N, Override-Logik, niedrigere zu —, Priorisierung nur im Override-Modus | Prioritaetsnummer neben Wirkung, Override-Modus Toggle | API: Prioritaet setzen/anwenden | Prioritaet setzen → Override wirksam | Ja | 10 |

**P4 Gesamt: ~22 Tests**

### 2.5 Gesamtuebersicht

| Phase | Sprint | REQs | U-B | U-F | I | E2E | PBT | Gesamt |
|---|---|---|---|---|---|---|---|---|
| P1 (MVP) | 14 | 6 | ~35 | ~30 | ~10 | ~8 | ~0 | ~83 |
| P2 (Constraints) | 15 | 6 | ~60 | ~20 | ~30 | ~10 | ~0 | ~120 |
| P3 (Optimierung) | 16 | 7 | ~64 | ~25 | ~20 | ~8 | ~0 | ~117 |
| P4 (Graph) | 17 | 2 | ~10 | ~15 | ~10 | ~8 | ~0 | ~43 |
| **GESAMT** | | **21** | **~169** | **~90** | **~70** | **~34** | **~0** | **~363** |

---

## 3. Test-Daten-Strategie

### 3.1 Ursachen/Wirkungen – Basis-Testdaten

Die folgenden Kategorien dienen als konsistente Testdaten fuer alle EPIC-20-Tests.
Sie spiegeln das ISTQB-Beispiel "Kreditgenehmigung" wider und sind leicht erweiterbar.

#### 3.1.1 Minimal-Set (2 Ursachen, 2 Wirkungen)

```python
CAUSES_MINIMAL = {
    "C1_Angestellter": ["Y", "N"],     # 2 Werte
    "C2_Einkommen5k":  ["Y", "N"],     # 2 Werte
}
# 2^2 = 4 Regeln

EFFECTS_MINIMAL = {
    "E1_Genehmigen":   ["X", "-"],
    "E2_Ablehnen":     ["X", "-"],
}
```

**Verwendung:** P1-Tests (REQ-5003, 5004, 5005), P2-Tests (REQ-5007-5011)

#### 3.1.2 Standard-Set (3 Ursachen, 3 Wirkungen) – ISTQB-Beispiel

```python
CAUSES_STANDARD = {
    "C1_Angestellter":  ["Y", "N"],
    "C2_Einkommen5k":   ["Y", "N"],
    "C3_KeineKredite":  ["Y", "N"],
}
# 2^3 = 8 Regeln

EFFECTS_STANDARD = {
    "E1_Genehmigen":      ["X", "-"],
    "E2_Ablehnen":        ["X", "-"],
    "E3_ManuellePruefung": ["X", "-"],
}
```

**Verwendung:** P1-P3 Tests, Collapsing-Tests (8 → 4 Regeln nach ISTQB-Beispiel)

#### 3.1.3 Extended-Set (4 Ursachen, 2 Wirkungen)

```python
CAUSES_EXTENDED = {
    "C1_Angestellter":  ["Y", "N"],
    "C2_Einkommen5k":   ["Y", "N"],
    "C3_KeineKredite":  ["Y", "N"],
    "C4_Unterbuergung": ["Y", "N"],
}
# 2^4 = 16 Regeln
```

**Verwendung:** P2-Tests (Constraints mit mehreren Ursachen), P3-Tests (kaskadierendes Collapsing)

#### 3.1.4 Large-Set (5 Ursachen, 2 Wirkungen)

```python
CAUSES_LARGE = {
    "C1": ["Y", "N"],
    "C2": ["Y", "N"],
    "C3": ["Y", "N"],
    "C4": ["Y", "N"],
    "C5": ["Y", "N"],
}
# 2^5 = 32 Regeln
```

**Verwendung:** P1-Tests (REQ-5005 Limit-Tests), P3-Tests (Collapsing-Performance)

### 3.2 Edge-Cases – Ursachen-Anzahl

| Szenario | Ursachen | Regeln (2^n) | Test-Zweck |
|---|---|---|---|
| **0 Ursachen** | 0 | 1 (leere Tabelle) | REQ-5005: Grenzwert, REQ-5003: leere Tabelle |
| **1 Ursache** | 1 | 2 | REQ-5005: Minimalfall, REQ-5004: Boolean-Default |
| **2 Ursachen** | 2 | 4 | REQ-5005: Basisfall, REQ-5007-5010: Constraints |
| **3 Ursachen** | 3 | 8 | REQ-5005: Standard, REQ-5013: Collapsing |
| **5 Ursachen** | 5 | 32 | REQ-5005: Performance, REQ-5013: kaskadierend |
| **8 Ursachen** | 8 | 256 | REQ-5005: Limit-Test (REQ-4018) |
| **10 Ursachen** | 10 | 1024 | REQ-5005: Limit-Test (Uberschreitung Default 1000) |
| **15 Ursachen** | 15 | 32768 | REQ-5005: Limit-Test (Warnung + Abbruch) |

### 3.3 Constraint-Kombinationen – Testmatrix

Jeder Constraint-Typ wird mit verschiedenen Eingaben getestet:

#### 3.3.1 Constraint E (Exclusive) – REQ-5007

| Test | Ursachen | Eingabe | Erwartetes Ergebnis |
|---|---|---|---|
| E-01 | C1, C2 | C1=Y, C2=Y | Regel entfernt |
| E-02 | C1, C2 | C1=Y, C2=N | Regel bleibt |
| E-03 | C1, C2 | C1=N, C2=Y | Regel bleibt |
| E-04 | C1, C2 | C1=N, C2=N | Regel bleibt |
| E-05 | C1, C2, C3 | C1=Y, C2=Y, C3=Y | Regel entfernt |
| E-06 | C1, C2, C3 | C1=Y, C2=N, C3=Y | Regel entfernt |
| E-07 | C1, C2, C3 | C1=Y, C2=N, C3=N | Regel bleibt |
| E-08 | C1, C2, C3 | C1=N, C2=N, C3=N | Regel bleibt |

#### 3.3.2 Constraint O (One-and-Only-One) – REQ-5008

| Test | Ursachen | Eingabe | Erwartetes Ergebnis |
|---|---|---|---|
| O-01 | C1, C2 | C1=Y, C2=Y | Regel entfernt (2 Y) |
| O-02 | C1, C2 | C1=Y, C2=N | Regel bleibt (1 Y) |
| O-03 | C1, C2 | C1=N, C2=Y | Regel bleibt (1 Y) |
| O-04 | C1, C2 | C1=N, C2=N | Regel entfernt (0 Y) |
| O-05 | C1, C2, C3 | C1=Y, C2=N, C3=N | Regel bleibt (1 Y) |
| O-06 | C1, C2, C3 | C1=N, C2=N, C3=N | Regel entfernt (0 Y) |

#### 3.3.3 Constraint I (Inclusive) – REQ-5009

| Test | Ursachen | Eingabe | Erwartetes Ergebnis |
|---|---|---|---|
| I-01 | C1, C2 | C1=Y, C2=Y | Regel bleibt |
| I-02 | C1, C2 | C1=Y, C2=N | Regel bleibt |
| I-03 | C1, C2 | C1=N, C2=Y | Regel bleibt |
| I-04 | C1, C2 | C1=N, C2=N | Regel entfernt |

#### 3.3.4 Constraint R (Requires) – REQ-5010

| Test | C1 → C2 | C1 | C2 | Erwartetes Ergebnis |
|---|---|---|---|---|
| R-01 | C1 → C2 | Y | Y | Regel bleibt |
| R-02 | C1 → C2 | Y | N | Regel entfernt |
| R-03 | C1 → C2 | N | Y | Regel bleibt |
| R-04 | C1 → C2 | N | N | Regel bleibt |

#### 3.3.5 Constraint M (Mask) – REQ-5011

| Test | E1 → E2 | E1 | E2 (vorher) | E2 (nach M) |
|---|---|---|---|---|
| M-01 | E1 → E2 | X | X | — |
| M-02 | E1 → E2 | X | — | — (bleibt) |
| M-03 | E1 → E2 | — | X | X (bleibt) |
| M-04 | E1 → E2 | — | — | — (bleibt) |

#### 3.3.6 Constraint-Dialog Validierung – REQ-5012

| Test | Constraint-Typ | Anzahl Eintraege | Erwartung |
|---|---|---|---|
| D-01 | E | 1 | Ablehnung: "Mindestens 2 Ursachen erforderlich" |
| D-02 | E | 2 | Akzeptanz |
| D-03 | E | 5 | Akzeptanz |
| D-04 | O | 1 | Ablehnung |
| D-05 | I | 1 | Ablehnung |
| D-06 | R | 1 | Ablehnung: "Genau 2 Ursachen erforderlich" |
| D-07 | R | 2 | Akzeptanz |
| D-08 | R | 3 | Ablehnung: "Genau 2 Ursachen erforderlich" |
| D-09 | M | 1 | Ablehnung: "Genau 2 Wirkungen erforderlich" |
| D-10 | M | 2 | Akzeptanz |
| D-11 | M | 3 | Ablehnung |
| D-12 | R | 1 Ursache + 1 Wirkung | Ablehnung: "Requires gilt nur fuer Ursachen" |
| D-13 | M | 2 Ursachen | Ablehnung: "Mask gilt nur fuer Wirkungen" |

### 3.4 Collapsing-Testfaelle – REQ-5013

#### 3.4.1 Basis-Collapsing (2 Regeln → 1)

```
Vorher:
  R1: C1=Y, C2=Y, C3=Y → E1=X
  R2: C1=N, C2=Y, C3=Y → E1=X

Nachher:
  R1: C1=—, C2=Y, C3=Y → E1=X
  (C1 unterscheidet sich, Y+N=volle Abdeckung → Don't Care)
```

#### 3.4.2 Kein Collapsing moeglich

```
R1: C1=Y, C2=Y, C3=Y → E1=X
R2: C1=N, C2=Y, C3=Y → E2=X
→ NICHT zusammenfuehrbar (unterschiedliche Aktionen)
```

```
R1: C1=Y, C2=Y, C3=Y → E1=X
R2: C1=N, C2=N, C3=Y → E1=X
→ NICHT zusammenfuehrbar (2 Unterschiede: C1 und C2)
```

```
R1: C1=Y, C2=Y, C3=Y → E1=X
R2: C1=N, C2=Y, C3=Y → E1=X
R3: C1=Y, C2=N, C3=Y → E1=X
→ R1+R2 zusammenfuehrbar (C1→—), aber R3 bleibt separat
```

#### 3.4.3 Kaskadierendes Collapsing

```
Start: 8 Regeln (3 Ursachen)
Schritt 1: R1+R2 → R1' (C1=—), R3+R4 → R3' (C1=—)
Schritt 2: R1'+R3' → R1'' (C2=—)
Ergebnis: 4 Regeln → 2 Regeln
```

#### 3.4.4 Collapsing mit Extended Entry

```
R1: C1=S, C2=Y → E1=X
R2: C1=M, C2=Y → E1=X
R3: C1=L, C2=Y → E1=X
→ C1 hat 3 Werte (S, M, L). Zusammenfassung nur wenn ALLE Werte abgedeckt.
→ R1+R2+R3 → C1=—, C2=Y → E1=X (wenn alle 3 Werte zusammengefasst)
```

### 3.5 Checksum-Testfaelle – REQ-5014

| Test | Regeln (DC=Don't Care) | Checksum | 2^n | Ergebnis |
|---|---|---|---|---|
| CS-01 | R1(0 DC), R2(0 DC), R3(0 DC), R4(0 DC) | 1+1+1+1=4 | 4 (2^2) | = 2^n → Vollstaendig |
| CS-02 | R1(1 DC), R2(1 DC) | 2+2=4 | 4 (2^2) | = 2^n → Vollstaendig |
| CS-03 | R1(0 DC), R2(0 DC) | 1+1=2 | 4 (2^2) | < 2^n → Luecken |
| CS-04 | R1(2 DC), R2(0 DC), R3(0 DC) | 4+1+1=6 | 4 (2^2) | > 2^n → Uberschneidungen |
| CS-05 | R1(1 DC), R2(1 DC), R3(1 DC) | 2+2+2=6 | 4 (2^2) | > 2^n → Uberschneidungen |
| CS-06 | R1(0 DC), R2(0 DC), R3(0 DC) | 1+1+1=3 | 4 (2^2) | < 2^n → Luecken |
| CS-07 | R1(3 DC) | 8 | 8 (2^3) | = 2^n → Vollstaendig (1 Regel mit 3 DC) |

### 3.6 Widerspruchserkennung – REQ-5019

| Test | Regel 1 | Regel 2 | Typ | Erwartung |
|---|---|---|---|---|
| W-01 | C1=Y, C2=Y → E1=X | C1=Y, C2=Y → E2=X | Identische Bedingungen | Widerspruch |
| W-02 | C1=Y, C2=Y → E1=X | C1=Y, C2=Y → E1=X | Identisch | Kein Widerspruch |
| W-03 | C1=—, C2=Y → E1=X | C1=Y, C2=Y → E2=X | Ueberlappend (DC) | Widerspruch |
| W-04 | C1=Y, C2=Y → E1=X | C1=N, C2=Y → E2=X | Keine Ueberlappung | Kein Widerspruch |
| W-05 | C1=Y, C2=Y → E1=X, E2=X | M(E1→E2) | M-Constraint verletzt | Widerspruch |
| W-06 | C1=Y, C2=Y → E1=X, E2=— | M(E1→E2) | M-Constraint eingehalten | Kein Widerspruch |

### 3.7 Vollstaendigkeitspruefung – REQ-5020

| Test | Gueltige Kombinationen | Abgedeckt | Erwartung |
|---|---|---|---|
| V-01 | 4 (2^2) | 4 | Vollstaendig |
| V-02 | 4 (2^2) | 3 | Luecke: 1 Kombination |
| V-03 | 4 (2^2) | 2 | Luecke: 2 Kombinationen |
| V-04 | 3 (nach E-Constraint) | 3 | Vollstaendig (nach Filterung) |
| V-05 | 3 (nach E-Constraint) | 2 | Luecke: 1 Kombination |
| V-06 | 4 (2^2) | 4, aber E2=— in allen | "Keine Wirkung definiert" |

---

## 4. Coverage-Ziele

### 4.1 Backend (Python/pytest)

| Metrik | Ziel | Messung |
|---|---|---|
| **Statement Coverage** | >= 90% | `pytest-cov --cov=src/combinatorics/decision_table` |
| **Branch Coverage** | >= 85% | `pytest-cov --cov-branch` |
| **Function Coverage** | >= 95% | `pytest-cov --cov-report=term-missing` |

**Betroffene Module** (neu in `src/combinatorics/`):
- `decision_table.py` – Hauptlogik (Generierung, Layout)
- `decision_constraints.py` – Constraint-Filter (E, I, O, R, M)
- `decision_collapsing.py` – Collapsing-Algorithmus
- `decision_checksum.py` – Checksum-Validierung
- `decision_extended_entry.py` – Extended Entry
- `decision_contradiction.py` – Widerspruchserkennung
- `decision_completeness.py` – Vollstaendigkeitspruefung
- `decision_graph.py` – Graph-Generierung
- `decision_priority.py` – Priorisierung/Override

### 4.2 Frontend (React/Vitest)

| Metrik | Ziel | Messung |
|---|---|---|
| **Component Coverage** | >= 80% | `vitest --coverage` (c8/v8) |
| **Branch Coverage** | >= 75% | `vitest --coverage --coverage.provider=v8` |

**Betroffene Komponenten** (neu in `frontend/src/components/decision-table/`):
- `DecisionTableButton.tsx` – Button (REQ-5000)
- `DecisionTableLayout.tsx` – Tabelle (REQ-5003)
- `CategoryTypeSelector.tsx` – Typ-Auswahl (REQ-5002)
- `ConstraintDialog.tsx` – Constraint-Dialog (REQ-5012)
- `CauseEffectGraph.tsx` – Graph-Visualisierung (REQ-5018)
- `DonutCareCell.tsx` – Don't Care Zelle (REQ-5017)
- `ExtendedEntryCell.tsx` – Extended Entry Zelle (REQ-5015)
- `ContradictionIndicator.tsx` – Widerspruchsmarkierung (REQ-5019)
- `CompletenessIndicator.tsx` – Vollstaendigkeitshinweis (REQ-5020)
- `PrioritySelector.tsx` – Prioritaetsauswahl (REQ-5021)

### 4.3 E2E (Playwright)

| Metrik | Ziel | Messung |
|---|---|---|
| **Kritische Pfade** | 100% | `npx playwright test` (alle E2E-Tests gruen) |
| **Screenshots bei Failure** | Standard | `playwright config` (screenshot: 'only-on-failure') |

---

## 5. Quality Gate Kriterien pro Phase

### 5.1 Phase 1 (MVP) – Quality Gate

| Kriterium | Ziel | Messung | Blocker? |
|---|---|---|---|
| Alle Unit-Tests (Backend) gruen | 100% | `pytest tests/test_req500*.py -v` | Ja |
| Alle Unit-Tests (Frontend) gruen | 100% | `npm run test -- decision-table` | Ja |
| Backend Coverage >= 90% | Statement | `pytest --cov=src/combinatorics/decision_table --cov-report=term` | Ja |
| Frontend Coverage >= 80% | Component | `npm run test -- --coverage` | Ja |
| E2E-Tests gruen | 100% | `npx playwright test e2e/decision-table` | Ja |
| Keine kritischen Bugs | 0 | Manual Review | Ja |
| Combinatorics-Review | Bestanden | GREAT Combinatorics Expert Agent | Ja |
| Regression: bestehende Strategien | Unverändert | `pytest tests/test_all_combinations.py tests/test_pairwise.py` | Ja |

### 5.2 Phase 2 (Constraints) – Quality Gate

| Kriterium | Ziel | Messung | Blocker? |
|---|---|---|---|
| Alle Unit-Tests (Backend) gruen | 100% | `pytest tests/test_req5007*.py tests/test_req5012*.py -v` | Ja |
| Alle Unit-Tests (Frontend) gruen | 100% | `npm run test -- constraint` | Ja |
| Backend Coverage >= 90% | Statement | `pytest --cov=src/combinatorics/decision_constraints --cov-report=term` | Ja |
| Frontend Coverage >= 80% | Component | `npm run test -- --coverage` | Ja |
| E2E-Tests gruen | 100% | `npx playwright test e2e/decision-table-constraints` | Ja |
| Constraint-Validierung korrekt | Alle 5 Typen | `pytest tests/test_req5007*.py -v` | Ja |
| Combinatorics-Review | Bestanden | GREAT Combinatorics Expert Agent | Ja |
| Regression: P1-Tests | Unverändert | `pytest tests/test_req500*.py -v` | Ja |

### 5.3 Phase 3 (Optimierung) – Quality Gate

| Kriterium | Ziel | Messung | Blocker? |
|---|---|---|---|
| Alle Unit-Tests (Backend) gruen | 100% | `pytest tests/test_req5013*.py -v` | Ja |
| Alle Unit-Tests (Frontend) gruen | 100% | `npm run test -- decision-table` | Ja |
| Backend Coverage >= 90% | Statement | `pytest --cov=src/combinatorics/decision_* --cov-report=term` | Ja |
| Frontend Coverage >= 80% | Component | `npm run test -- --coverage` | Ja |
| E2E-Tests gruen | 100% | `npx playwright test e2e/decision-table-optimization` | Ja |
| Collapsing korrekt (ISTQB-Beispiel) | 8→4 Regeln | `pytest tests/test_req5013_collapsing.py -v` | Ja |
| Checksum korrekt | 3 Ergebnisse | `pytest tests/test_req5014_checksum.py -v` | Ja |
| Widerspruchserkennung korrekt | 6 Testfaelle | `pytest tests/test_req5019_contradiction.py -v` | Ja |
| Combinatorics-Review | Bestanden | GREAT Combinatorics Expert Agent | Ja |
| Regression: P1+P2-Tests | Unverändert | `pytest tests/test_req500*.py tests/test_req5007*.py -v` | Ja |

### 5.4 Phase 4 (Graph) – Quality Gate

| Kriterium | Ziel | Messung | Blocker? |
|---|---|---|---|
| Alle Unit-Tests (Backend) gruen | 100% | `pytest tests/test_req5018*.py tests/test_req5021*.py -v` | Ja |
| Alle Unit-Tests (Frontend) gruen | 100% | `npm run test -- decision-table-graph` | Ja |
| Backend Coverage >= 90% | Statement | `pytest --cov=src/combinatorics/decision_graph --cov-report=term` | Ja |
| Frontend Coverage >= 80% | Component | `npm run test -- --coverage` | Ja |
| E2E-Tests gruen | 100% | `npx playwright test e2e/decision-table-graph` | Ja |
| Graph-Visualisierung korrekt | Knoten + Kanten | `npm run test -- CauseEffectGraph` | Ja |
| Priorisierung korrekt | Override-Logik | `pytest tests/test_req5021_priority.py -v` | Ja |
| Regression: P1+P2+P3-Tests | Unverändert | `pytest tests/test_req500*.py -v` | Ja |

---

## 6. Risiken und Gegenmassnahmen

| ID | Risiko | Wahrscheinlichkeit | Impact | Score | Gegenmassnahme |
|---|---|---|---|---|---|
| **RISK-DT-001** | Collapsing-Algorithmus inkorrekt (falsche Zusammenfassung) | 3 (mittel) | 5 (kritisch) | 15 🔴 | Combinatorics-Expert-Review + Property-Based-Testing (hypothesis) + ISTQB-Beispiel als Referenz |
| **RISK-DT-002** | Constraint-Logik erzeugt ungültige Zustände (z.B. alle Regeln entfernt) | 3 (mittel) | 4 (hoch) | 12 🔴 | Extensive Edge-Case-Tests + Validierung nach jedem Constraint + Warnung bei 0 Regeln |
| **RISK-DT-003** | Checksum-Validierung liefert falsches Ergebnis (falsch-positive/negative) | 2 (niedrig) | 4 (hoch) | 8 🟡 | Mathematische Verifikation + 7 spezifische Testfaelle + Hinweis "Checksum allein beweist weder Vollstaendigkeit noch Widerspruchsfreiheit" |
| **RISK-DT-004** | E2E-Tests instabil (Timing-Probleme bei Tabelle-Generierung) | 4 (hoch) | 3 (mittel) | 12 🔴 | Retry-Logik in Playwright, explizite Waits (`expect.toHaveCount()`), Screenshots bei Failure, Mock-Backend fuer deterministische Tests |
| **RISK-DT-005** | 2^15 = 32768 Regeln ueberlasten Frontend/Backend | 3 (mittel) | 4 (hoch) | 12 🔴 | REQ-4018 (Max-Testfaelle-Limit) als Hard-Stop + Warnung bei >1000 Regeln + Server-Side-Generierung mit Pagination |
| **RISK-DT-006** | Widerspruchserkennung falsch-positiv (Don't Care-Überlappungen) | 3 (mittel) | 4 (hoch) | 12 🔴 | Don't Care-Überlappung als separater Testfall + "Speichern trotzdem moeglich (Warnung, kein Hard-Block)" |
| **RISK-DT-007** | Graph-Visualisierung (REQ-5018) erfordert neue Library (z.B. react-flow) | 4 (hoch) | 3 (mittel) | 12 🔴 | Library-Auswahl in ADR dokumentieren + Fallback: SVG-basierte Visualisierung ohne externe Library |
| **RISK-DT-008** | Extended Entry (REQ-5015) bricht Collapsing-Algorithmus | 2 (niedrig) | 4 (hoch) | 8 🟡 | Extended Entry und Collapsing als separate Code-Pfade + Integrationstest fuer beide zusammen |
| **RISK-DT-009** | Constraint-Dialog UX zu komplex (Mehrfachauswahl + 5 Constraint-Typen) | 3 (mittel) | 3 (mittel) | 9 🟡 | Usability-Test mit Georg Hartel nach P2 + Progressive Disclosure (nur relevante Typen anzeigen) |
| **RISK-DT-010** | Regression in bestehenden Kombinatorik-Strategien durch gemeinsame Codebasis | 2 (niedrig) | 5 (kritisch) | 10 🔴 | Isolation: Entscheidungstabelle als eigenstaendiges Modul in `src/combinatorics/` + Regressionstests aller bestehenden Strategien nach jeder Phase |

### 6.1 Risikomatrix

```
Impact
  5  │    DT-001    DT-010
  4  │  DT-002  DT-003  DT-005  DT-006  DT-008
  3  │          DT-004        DT-007  DT-009
  2  │
  1  │
     └────────────────────────────────────
        1      2      3      4      5
              Wahrscheinlichkeit
```

---

## 7. Test-Dateien-Struktur (geplant)

### 7.1 Backend-Tests (`tests/`)

```
tests/
├── # Phase 1 (MVP)
│   ├── test_req5000_decision_table_button.py      # REQ-5000
│   ├── test_req5002_category_type.py               # REQ-5002
│   ├── test_req5003_decision_table_layout.py       # REQ-5003
│   ├── test_req5004_boolean_defaults.py            # REQ-5004
│   ├── test_req5005_auto_generation.py             # REQ-5005
│   └── test_req5006_other_strategies_greyed.py     # REQ-5006
│
├── # Phase 2 (Constraints)
│   ├── test_req5007_constraint_exclusive.py         # REQ-5007
│   ├── test_req5008_constraint_one_only_one.py      # REQ-5008
│   ├── test_req5009_constraint_inclusive.py         # REQ-5009
│   ├── test_req5010_constraint_requires.py          # REQ-5010
│   ├── test_req5011_constraint_mask.py              # REQ-5011
│   └── test_req5012_constraint_dialog.py            # REQ-5012
│
├── # Phase 3 (Optimierung)
│   ├── test_req5013_collapsing.py                   # REQ-5013
│   ├── test_req5014_checksum.py                     # REQ-5014
│   ├── test_req5015_extended_entry.py               # REQ-5015
│   ├── test_req5016_effects_as_text.py              # REQ-5016
│   ├── test_req5017_dont_care_manual.py             # REQ-5017
│   ├── test_req5019_contradiction_detection.py      # REQ-5019
│   └── test_req5020_completeness_check.py           # REQ-5020
│
├── # Phase 4 (Graph)
│   ├── test_req5018_cause_effect_graph.py           # REQ-5018
│   └── test_req5021_effect_priority.py              # REQ-5021
│
└── # Property-Based-Testing (optional, P2+P3)
    └── test_decision_table_pbt.py                   # hypothesis-basiert
```

### 7.2 Frontend-Tests (`frontend/src/components/decision-table/__tests__/`)

```
frontend/src/components/decision-table/__tests__/
├── # Phase 1
│   ├── DecisionTableButton.test.tsx                  # REQ-5000
│   ├── CategoryTypeSelector.test.tsx                 # REQ-5002
│   ├── DecisionTableLayout.test.tsx                  # REQ-5003
│   ├── BooleanCell.test.tsx                          # REQ-5004
│   └── StrategiesGreyed.test.tsx                     # REQ-5006
│
├── # Phase 2
│   ├── ConstraintDialog.test.tsx                     # REQ-5012
│   ├── ConstraintExclusiveIndicator.test.tsx         # REQ-5007
│   ├── ConstraintOneOnlyOneIndicator.test.tsx        # REQ-5008
│   ├── ConstraintInclusiveIndicator.test.tsx         # REQ-5009
│   ├── ConstraintRequiresIndicator.test.tsx          # REQ-5010
│   └── ConstraintMaskIndicator.test.tsx              # REQ-5011
│
├── # Phase 3
│   ├── CollapsingToggle.test.tsx                     # REQ-5013
│   ├── ChecksumIndicator.test.tsx                    # REQ-5014
│   ├── ExtendedEntryCell.test.tsx                    # REQ-5015
│   ├── TextEffectCell.test.tsx                       # REQ-5016
│   ├── DontCareCell.test.tsx                         # REQ-5017
│   ├── ContradictionIndicator.test.tsx               # REQ-5019
│   └── CompletenessIndicator.test.tsx                # REQ-5020
│
└── # Phase 4
    ├── CauseEffectGraph.test.tsx                     # REQ-5018
    └── PrioritySelector.test.tsx                     # REQ-5021
```

### 7.3 E2E-Tests (`tests/e2e/`)

```
tests/e2e/
├── # Phase 1
│   └── decision-table-mvp.spec.ts                    # REQ-5000, 5003, 5005, 5006
│
├── # Phase 2
│   └── decision-table-constraints.spec.ts            # REQ-5007-5012
│
├── # Phase 3
│   └── decision-table-optimization.spec.ts           # REQ-5013-5017, 5019-5020
│
└── # Phase 4
    └── decision-table-graph.spec.ts                  # REQ-5018, 5021
```

---

## 8. Test-Ausfuehrungs-Strategie

### 8.1 TDD-Zyklus pro REQ

Jeder REQ folgt dem RED-GREEN-REFACTOR-Zyklus:

1. **RED:** Test schreiben, der das erwartete Verhalten beschreibt (failt)
2. **GREEN:** Minimalen Code schreiben, um den Test zu bestanden
3. **REFACTOR:** Code und Test refactoren, ohne Verhalten zu aendern

### 8.2 Test-Ausfuehrung nach jeder Phase

```bash
# Phase 1
pytest tests/test_req500*.py -v --cov=src/combinatorics/decision_table --cov-report=term
npm run test -- decision-table
npx playwright test e2e/decision-table-mvp.spec.ts

# Phase 2
pytest tests/test_req5007*.py tests/test_req5012*.py -v --cov=src/combinatorics/decision_constraints --cov-report=term
npm run test -- constraint
npx playwright test e2e/decision-table-constraints.spec.ts

# Phase 3
pytest tests/test_req5013*.py -v --cov=src/combinatorics/decision_* --cov-report=term
npm run test -- decision-table
npx playwright test e2e/decision-table-optimization.spec.ts

# Phase 4
pytest tests/test_req5018*.py tests/test_req5021*.py -v --cov=src/combinatorics/decision_graph --cov-report=term
npm run test -- decision-table-graph
npx playwright test e2e/decision-table-graph.spec.ts

# Regression (nach jeder Phase)
pytest tests/test_all_combinations.py tests/test_pairwise.py tests/test_each_choice.py -v
```

### 8.3 Property-Based-Testing (optional)

Fuer komplexe Algorithmen (Collapsing, Checksum, Constraints) wird
`hypothesis` fuer Property-Based-Testing empfohlen:

```python
# Beispiel: Collapsing-Invarianz
from hypothesis import given, strategies as st

@given(
    st.lists(st.tuples(st.just("Y") | st.just("N"), st.just("X") | st.just("-")),
             min_size=2, max_size=8)
)
def test_collapsing_preserves_coverage(rules):
    """Nach Collapsing muss jede urspruengliche Kombination noch abgedeckt sein."""
    collapsed = collapse_rules(rules)
    # Jede urspruengliche Regel muss durch mindestens eine collapsed-Regel abgedeckt werden
    for rule in rules:
        assert any(covers(c, rule) for c in collapsed), f"Rule {rule} nicht mehr abgedeckt"
```

---

## 9. Combinatorics-Review-Pflicht

Fuer EPIC-20 gilt eine **zusaetzliche Review-Pflicht** durch den
**GREAT Combinatorics Expert Agent** nach Phase 1 und Phase 3:

### 9.1 P1-Review (nach MVP)

- [ ] 2^n Generierung korrekt fuer alle n=0..15?
- [ ] Boolean-Default (Y/N) korrekt fuer jede Ursache?
- [ ] Wirkungen initial leer (kein Vorbelegen)?
- [ ] Max-Testfaelle-Limit (REQ-4018) respektiert?

### 9.2 P3-Review (nach Optimierung)

- [ ] Collapsing: 3 Bedingungen strikt eingehalten?
- [ ] Checksum: Summe(2^DC) korrekt implementiert?
- [ ] Widerspruchserkennung: Don't Care-Überlappungen korrekt?
- [ ] Vollstaendigkeitspruefung: Nach Constraint-Filterung korrekt?
- [ ] Extended Entry: Kartesisches Produkt korrekt?

---

## 10. Abwaertige Kompatibilitaet

### 10.1 Bestehende Kombinatorik-Strategien

Alle bestehenden Strategien muessen nach jeder EPIC-20-Phase unveraendert funktionieren:

| Strategie | Test-Datei | Erwartung |
|---|---|---|
| All Combinations | `test_all_combinations.py` | Unverändert |
| Pairwise (Orthogonal) | `test_pairwise.py` | Unverändert |
| Each Choice | `test_each_choice.py` | Unverändert |
| Linear Expansion | `test_linear_expansion.py` | Unverändert |
| BVA | `test_bva_istqb.py`, `test_boundary_value.py` | Unverändert |
| Risk-Based | `test_risk_based.py` | Unverändert |
| MCDC | `test_req3044_mcdc.py` | Unverändert |
| Constraint-Aware | `test_req3040_constraint_aware.py` | Unverändert |

### 10.2 Kategorie-Modell

Das bestehende Kategorie-Modell wird durch REQ-5002 erweitert (Typ: Standard/Ursache/Wirkung).
Bestehende Kategorien vom Typ "Standard" bleiben unveraendert und werden im
Entscheidungstabelle-Modus ignoriert.

---

## 11. Anhang

### 11.1 Referenzen

| ID | Quelle |
|---|---|
| REQ-EPIC-20 | `Agenten und basisinfos/requirements_v1.1.md` (REQ-5000-5021) |
| ISTQB-CTFL | CTFL v4.0 Syllabus FL-4.2.3 (K3 Apply) |
| ISTQB-CTAL | CTAL-TA v4.0 Syllabus TA-3.2.4 (K4 Analyse) |
| Recherche | `documentation/research-decision-table-istqb.md` |
| ADR-005 | `documentation/decision-log.md` (TDD + pytest-cov verpflichtend) |
| SYSTEM | `Agenten und basisinfos/SYSTEM_v1.0.md` (Governance) |
| QA-Regeln | `.github/instructions/great-qa-director.instructions.md` |
| AGENTS | `AGENTS.md` (Projektanweisungen) |

### 11.2 Glossar

| Begriff | Bedeutung |
|---|---|
| **Ursache (Condition)** | Eingabe-Bedingung der Entscheidungstabelle |
| **Wirkung (Effect/Action)** | Ausgabe-Aktion der Entscheidungstabelle |
| **Y (Yes/True/Ja)** | Bedingung ist wahr |
| **N (No/False/Nein)** | Bedingung ist falsch |
| **— (Don't Care/Dash)** | Bedingung ist fuer diese Regel irrelevant |
| **X** | Aktion tritt ein |
| **Constraint E** | Exclusive: Maximal eine Ursache kann wahr sein |
| **Constraint I** | Inclusive: Mindestens eine Ursache muss wahr sein |
| **Constraint O** | One-and-Only-One: Genau eine Ursache muss wahr sein |
| **Constraint R** | Requires: Wenn C1 wahr, dann muss C2 auch wahr sein |
| **Constraint M** | Mask: Wenn Wirkung E1, dann E2 erzwungen falsch |
| **Collapsing** | Zusammenfassen redundanter Regeln zu Don't Care |
| **Extended Entry** | Mehr als 2 Werte pro Ursache |
| **Checksum** | Summe(2^Anzahl Don't-Care pro Regel) |
| **Sparse Table** | Reduzierte Entscheidungstabelle (nach Collapsing) |
| **Dense Table** | Vollstaendige Entscheidungstabelle (alle 2^n Kombinationen) |

---

## 12. Freigabe

| Rolle | Name | Status | Datum |
|---|---|---|---|
| QA Director | GREAT QA Director | Erstellt | 2026-10-05 |
| Combinatorics Expert | GREAT Combinatorics Expert | Ausstehend | |
| Orchestrator | GREAT Orchestrator | Ausstehend | |
| Projektinhaber | Georg Hartel | Ausstehend | |

---

*Diese Teststrategie ist ein lebendes Dokument und wird pro Phase aktualisiert.*