# Recherche-Befund: Entscheidungstabellentest nach ISTQB

**Projekt:** G.R.E.A.T. (Georg Radikal Einfacher Automatisierter TestcaseDesigner)
**Thema:** Decision Table Testing / Cause-Effect Graphing nach ISTQB
**Datum:** 5. Oktober 2026
**Auftraggeber:** GREAT Orchestrator → GREAT Web Research Agent
**Zweck:** Grundlage fuer EPIC-19 – Entscheidungstabelle-Funktion

---

## 1. ISTQB-Grundlagen

### Definition
Eine **Entscheidungstabelle (Decision Table)** ist eine **Black-Box-Test-Design-Technik**, bei der das Systemverhalten von **Kombinationen mehrerer Bedingungen** abhaengt. Jede Kombination produziert eine spezifische Aktion.

**ISTQB-Referenz:** CTFL v4.0 Syllabus, Sektion **FL-4.2.3 (K3 Apply)**: "Use decision table testing to derive test cases"

### Cause-Effect Graphing vs. Decision Table Testing
| Aspekt | Cause-Effect Graphing | Decision Table Testing |
|---|---|---|
| **Art** | Analytisches Werkzeug (Graph) | Test-Artefakt (Tabelle) |
| **Zweck** | Logische Beziehungen modellieren | Alle gueltigen Kombinationen auflisten |
| **ISTQB** | Advanced TA-3.2.4 (K4 Analyse) | Foundation FL-4.2.3 (K3 Apply) |

**Zusammenfassung:** *"The graph is the thinking tool and the decision table is the deliverable."*

---

## 2. Tabellarischer Aufbau – 4 Quadranten

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTSCHEIDUNGSTABELLE                         │
├───────────────────┬─────────────────────────────────────────────┤
│  QUADRANT 1       │  QUADRANT 2                                 │
│  Condition Stubs   │  Condition Entries                          │
│  (Ursachenliste)   │  (Ursacheneintraege: Y/N/-)                  │
│  C1: Bedingung A  │  ┌────┬────┬────┬────┐                      │
│  C2: Bedingung B  │  │ Y  │ Y  │ N  │ N  │  <- Regel 1-4        │
│  C3: Bedingung C  │  │ Y  │ N  │ Y  │ N  │                      │
├───────────────────┼─────────────────────────────────────────────┤
│  QUADRANT 3       │  QUADRANT 4                                 │
│  Action Stubs      │  Action Entries                             │
│  (Wirkungsliste)   │  (Wirkungseintraege: X/-)                    │
│  A1: Aktion X     │  │ X  │ -  │ -  │ -  │                      │
│  A2: Aktion Y     │  │ -  │ X  │ -  │ -  │                      │
│  A3: Aktion Z     │  │ -  │ -  │ X  │ X  │                      │
└───────────────────┴─────────────────────────────────────────────┘
```

**Leserichtung:** Spaltenweise (vertikal). Jede Spalte = 1 Regel = 1 Testfall.

---

## 3. Entscheidungslogik

### Condition Entries (Ursachen-Werte)
| Symbol | Bedeutung |
|---|---|
| **Y** / **T** / **1** | Bedingung ist wahr (True/Yes/Ja) |
| **N** / **F** / **0** | Bedingung ist falsch (False/No/Nein) |
| **—** (Dash) | **Don't Care** – Bedingung ist fuer diese Regel irrelevant |

### Action Entries (Wirkungen-Werte)
| Symbol | Bedeutung |
|---|---|
| **X** | Aktion tritt ein (wird ausgefuehrt) |
| **—** / leer | Aktion tritt nicht ein |

### Logik pro Regel
Konjunktive (AND) Verknuepfung aller Bedingungen in der Spalte:
`Wenn C1=Y AND C2=N AND C3=Y → Dann A1=X, A2=—`

---

## 4. Optimierung – Collapsing (Regel-Zusammenfassung)

**3 strenge Bedingungen** (Seidl, 2026):
1. **Identische Aktionen:** Beide Regeln muessen exakt die gleichen Aktionen ausloesen.
2. **Einziger Unterschied:** Die Regeln duerfen sich in **genau einer** Bedingung unterscheiden.
3. **Vollstaendige Abdeckung:** Zusammen genommen muessen sie **alle Werte** dieser einen Bedingung abdecken.

Wenn alle 3 Bedingungen erfueellt → unterscheidende Bedingung wird zu **Don't Care (—)**.

### Sparse vs. Dense
| Typ | Beschreibung |
|---|---|
| **Dense (Vollstaendige)** | Alle 2^n Kombinationen explizit |
| **Sparse (Reduzierte)** | Redundante Regeln zusammengefasst, Don't Care-Werte |

**Wichtig:** ISTQB sagt: *"Decision table minimization algorithms are out of scope of this syllabus."*
Manuelles Zusammenfassen ist relevant, automatische Algorithmen (Quine-McCluskey) sind nicht im Pruefungsumfang.

### Checksum-Validierung
`Checksum = Σ(2^(Anzahl Don't-Care pro Regel))`
- `= 2^n` → Notwendige Bedingung erfueellt
- `> 2^n` → Uberschneidungen (Overlap)
- `< 2^n` → Luicken (Gap)

**Warnung:** Checksum allein beweist weder Vollstaendigkeit noch Widerspruchsfreiheit.

---

## 5. Cause-Effect Graphing – 5 Constraint-Typen

| Constraint | Abk. | Bedeutung | Beispiel |
|---|---|---|---|
| **Exclusive** | **E** | Maximal eine Ursache kann wahr sein (0 oder 1) | Zahlung: Kreditkarte ODER PayPal |
| **Inclusive** | **I** | Mindestens eine Ursache muss wahr sein | Mind. 1 Lieferadresse |
| **One-and-Only-One** | **O** | Genau eine Ursache muss wahr sein | Genau 1 Zahlungsmethode |
| **Requires** | **R** | Wenn C1 wahr, dann muss C2 auch wahr sein | Express → Lieferadresse |
| **Mask** | **M** | Wenn Wirkung E1, dann E2 erzwungen falsch | "Abgelehnt" → keine Bestaetigungsmail |

### Bool'sche Operatoren im Graph
Identity, NOT, OR, AND, NAND, NOR

### 5-Stufen-Prozess (Graph → Tabelle)
1. Spezifikation zerlegen
2. Ursachen und Wirkungen identifizieren (binär)
3. Graph konstruieren mit Constraints
4. In Entscheidungstabelle umwandeln
5. Testfaelle ableiten

---

## 6. Optimierungsmechanismen

### Mutual Exclusion (E-Constraint)
Kombinationen bei denen beide Ursachen gleichzeitig wahr sind → unmöglich, aus Tabelle entfernen.

### Inhibitors / Mask (M-Constraint)
Wirkung E1 unterdrueckt erzwungen Wirkung E2.

### Superposition / Override
Bestimmte Wirkungen haben Vorrang. Zeigt sich durch Don't Care-Werte in niedriger-priorisierten Bedingungen.

### Don't Care (—)
Entsteht durch Zusammenfassen oder Priorisierung. Hauptwerkzeug zur Tabellenreduktion.

### Priority / Precedence
Fruehe Validierungsfehler machen spaetere Bedingungen zu Don't Care → drastische Tabellenreduktion.

---

## 7. Praxis-Beispiel: Kreditgenehmigung

**Ursachen:** C1: Angestellter (Y/N), C2: Einkommen >= 5k (Y/N), C3: Keine Kredite (Y/N)
**Wirkungen:** E1: Genehmigen, E2: Ablehnen, E3: Manuelle Pruefung

### Vollstaendige Tabelle (8 Regeln → 4 nach Collapsing)
| | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| C1: Angestellter? | Y | Y | Y | N |
| C2: Einkommen >= 5k? | Y | Y | N | — |
| C3: Keine Kredite? | Y | N | — | — |
| E1: Genehmigen | X | — | — | — |
| E2: Ablehnen | — | — | X | X |
| E3: Manuelle Pruefung | — | X | — | — |

**Checksum:** 1 + 1 + 2 + 4 = 8 = 2^3 ✓ → 4 Testfaelle fuer 100% Coverage.

---

## 8. Implementierungs-Hinweise

### Algorithmische Generierung
1. Ursachen extrahieren (C1..Cn)
2. Wirkungen extrahieren (E1..Em)
3. Constraints identifizieren
4. Kartesisches Produkt: 2^n Kombinationen
5. Constraints anwenden → unmögliche Kombinationen entfernen
6. Wirkungen evaluieren (logische Operatoren)
7. Redundante Regeln zusammenfassen (Collapsing)
8. Testfaelle ableiten

### Maximale Anzahl Regeln
| Ursachen | Max. Regeln | Praxis nach Constraints |
|---|---|---|
| 2 | 4 | 2-4 |
| 5 | 32 | 8-32 |
| 8 | 256 | 16-256 |
| 10 | 1024 | 20-1024 |
| 15 | 32768 | Zerlegung empfohlen |

### Widerspruchserkennung
- Zwei Regeln mit identischen Bedingungen → unterschiedliche Aktionen
- Ueberlappende Bedingungen (nach Don't Care) → unterschiedliche Aktionen
- M-Constraint verletzt

### Vollstaendigkeitspruefung
- Nicht alle gueltigen Kombinationen abgedeckt
- Checksum < 2^n (nach Constraint-Filterung)
- Gueltige Kombination ohne zugeordnete Aktion

---

## 9. Quellen

1. **ISTQB CTFL v4.0 Syllabus** FL-4.2.3 (K3) – https://istqb.org/
2. **ISTQB CTAL-TA v4.0 Syllabus** TA-3.2.4 (K4) – https://astqb.org/
3. **Richard Seidl** – Decision Table Testing – https://www.richard-seidl.com/en/decision-table-testing/
4. **Yuri Kan** – Cause-Effect Graphing – https://yrkan.com/course/module-03-test-design/cause-effect-graphing/
5. **Virtuoso QA** – Cause-Effect Graphing – https://www.virtuosoqa.com/post/cause-effect-graphing
6. **Resync Bootcamp** – Cause-Effect Graphing – https://bootcamp.resync.nz/library/techniques/cause-effect-graphing/
7. **GeeksforGeeks** – Cause Effect Graphing + Decision Table – https://www.geeksforgeeks.org/
8. **ISTQB Guru** – Decision Tables – https://www.istqb.guru/
9. **TestGrid** – Decision Table Testing – https://testgrid.io/blog/decision-table-testing/
10. **ToolsQA** – Decision Table Testing – https://toolsqa.com/

---

## Entscheidung des Nutzers (Georg Hartel, 2026-10-05)

| Frage | Entscheidung |
|---|---|
| **Epic-Zuordnung** | Eigenstaendiges EPIC-20 (EPIC-19 existiert bereits) |
| **Kategorie-Zuordnung** | Explizite Wahl Ursache/Wirkung bei jeder neuen Kategorie |
| **Tabellenformat** | G.R.E.A.T.-adaptiert (nicht 1:1 ISTQB, aber fachlich korrekt) |
| **Optimierung** | Alle ISTQB-Optimierungen recherchieren |
| **Wertetyp** | Boolean (Ja/Nein) als Default, Extended Entry fuer multiple Werte |
| **Phasenmodell** | Phasenweise: P1=Button+Kategorien+Tabelle+Boolean, P2=Constraints, P3=Collapsing+Checksum+Extended, P4=Graph |
| **Constraint-UI** | Separater Dialog, mehrere Ursachen waehlbar, Constraint-Typ zuweisen |
| **Max. Ursachen** | Kein Hard-Limit, nur durch globales Max-Testfaelle-Limit (REQ-4018) begrenzt |
| **Wirkungen** | Beides: Binär (X/—) als Default, Text als Option |
| **Tabelle-Fuellung** | **Ursachen-Bereich:** Automatisch mit Y/N (oder Extended-Entry-Werten) gefuellt. **Wirkungen-Bereich:** Initial komplett leer. Der Tester tragt manuell ein, welche Wirkung auf welche Ursachen-Kombination zutrifft. Optional: Regeln koennen definiert werden fuer automatische Fuellung. |
| **Andere Kombinatorik-Funktionen** | Ausgegraut im Entscheidungstabelle-Modus |