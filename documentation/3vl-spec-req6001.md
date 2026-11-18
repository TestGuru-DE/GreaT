# Dreiwertige Logik-Spezifikation fuer REQ-6001 Constraint-Evaluierung

**Datum:** 2026-11-18
**Autor:** great-combinatorics-expert
**Status:** Draft – zur Implementierung durch great-senior-developer
**Betroffene REQ:** REQ-6001 AK-6 (Pairwise/T-Wise + dreiwertige Logik)
**Referenzen:** ADR-020 (JSON-AST-Format), REQ-3040 (Constraint-aware Generierung)

---

## 1. Problemstellung

Bei der Generierung durch Pairwise (IPO) und T-Wise werden Testfaelle inkrementell aufgebaut:
zunachst werden Paare/Tupel generiert, dann schrittweise um weitere Kategorien erganzt.
Wahrend dieses Prozesses existieren **partielle Testfaelle** mit nicht allen Kategorien gesetzt.

Ein Constraint wie:

> `NICHT (Zahlart=Rechnung AND Land!=DE AND Versand=Express)`

kann nicht binar (wahr/falsch) evaluiert werden, wenn z.B. "Land" noch `None` ist.

**Ziel:** Ein partieller Testfall wird NUR verworfen, wenn er einen Constraint **sicher** verletzt.
Im Zweifel (unbekannt) wird er vorlaufig behalten – er kann spater bei Vollstandigkeit noch verworfen werden.

---

## 2. Wertedomain

| Symbol | Python | Bedeutung |
|---|---|---|
| `T` | `True` | Bedingung ist definitiv erfullt |
| `F` | `False` | Bedingung ist definitiv NICHT erfullt |
| `U` | `None` | Unbekannt (Kategorie nicht gesetzt im Teiltestfall) |

**Wichtig:** `None` als Evaluierungsergebnis ist zu unterscheiden von `None` als Kategorie-Wert
(wenn eine Kategorie nicht im assignment-Dict steht). Die Funktion `evaluate_3vl()` gibt
`Optional[bool]` zurueck: `True`, `False` oder `None`.

---

## 3. Wahrheitstabellen fuer atomare Operatoren

Atomare Operatoren arbeiten auf einem einzelnen Vergleich zwischen einer Kategorie und einem Wert.
Der Kategorie-Wert wird aus `assignment[category_id]` gelesen. Ist die Kategorie nicht im assignment
enthalten (oder explizit `None`), ist das Ergebnis `None` (unbekannt).

### 3.1 `eq(a, b)` – Gleichheit

| assignment[a] | b (Wert) | Ergebnis | Begrundung |
|---|---|---|---|
| `x` (== b) | `b` | **T** | Wert stimmt uberein |
| `x` (!= b) | `b` | **F** | Wert stimmt nicht uberein |
| `None` | `b` | **U** | Kategorie nicht gesetzt |

**Spezialfall:** `b` ist immer ein konkreter Wert (nicht None). Ein Vergleich "Kategorie == None"
ist kein gueltiger atomarer Operator im AST.

### 3.2 `ne(a, b)` – Ungleichheit

| assignment[a] | b (Wert) | Ergebnis | Begrundung |
|---|---|---|---|
| `x` (== b) | `b` | **F** | Wert ist gleich, also NICHT ungleich |
| `x` (!= b) | `b` | **T** | Wert ist ungleich |
| `None` | `b` | **U** | Kategorie nicht gesetzt |

### 3.3 `in(a, [b1, b2, ...])` – Wert in Menge

| assignment[a] | value_ids | Ergebnis | Begrundung |
|---|---|---|---|
| `x` (in list) | `[b1, b2, ...]` | **T** | Wert ist in der Menge |
| `x` (not in list) | `[b1, b2, ...]` | **F** | Wert ist nicht in der Menge |
| `None` | `[b1, b2, ...]` | **U** | Kategorie nicht gesetzt |

### 3.4 `not_in(a, [b1, b2, ...])` – Wert nicht in Menge

| assignment[a] | value_ids | Ergebnis | Begrundung |
|---|---|---|---|
| `x` (in list) | `[b1, b2, ...]` | **F** | Wert ist in der Menge, also NICHT "nicht in" |
| `x` (not in list) | `[b1, b2, ...]` | **T** | Wert ist nicht in der Menge |
| `None` | `[b1, b2, ...]` | **U** | Kategorie nicht gesetzt |

---

## 4. Wahrheitstabellen fuer logische Verknupfungen

### 4.1 `and(x, y)` – Logisches UND

Kommutativ. Kleene-Logik (strong 3VL).

| x | y | Ergebnis | Begrundung |
|---|---|---|---|
| T | T | **T** | Beide erfullt |
| T | F | **F** | Eins nicht erfullt |
| T | U | **F** | Unbekannt kann nur F oder T sein; AND mit T propagiert U → aber: U bedeutet "konnte F sein" → **F** |
| F | T | **F** | Eins nicht erfullt |
| F | F | **F** | Beide nicht erfullt |
| F | U | **F** | Eins nicht erfullt, U irrelevant |
| U | T | **F** | Symmetrisch zu T,U |
| U | F | **F** | Symmetrisch zu F,U |
| U | U | **U** | Beides unbekannt |

**Kurzfassung:** `and(x, y)` = F wenn mindestens eines F; T wenn beide T; sonst U.

**Multi-Arg-Extension (and(x1, x2, ..., xn)):**
- Wenn IRGENDEIN Argument F → **F** (Kurzschluss)
- Wenn ALLE Argumente T → **T**
- Sonst (mindestens eins U, keines F) → **U**

### 4.2 `or(x, y)` – Logisches ODER

Kommutativ. Kleene-Logik.

| x | y | Ergebnis | Begrundung |
|---|---|---|---|
| T | T | **T** | Mindestens eins erfullt |
| T | F | **T** | Mindestens eins erfullt |
| T | U | **T** | Mindestens eins erfullt, U irrelevant |
| F | T | **T** | Symmetrisch |
| F | F | **F** | Keins erfullt |
| F | U | **U** | Eins nicht erfullt, anderes unbekannt |
| U | T | **T** | Symmetrisch zu T,U |
| U | F | **U** | Symmetrisch zu F,U |
| U | U | **U** | Beides unbekannt |

**Kurzfassung:** `or(x, y)` = T wenn mindestens eines T; F wenn beide F; sonst U.

**Multi-Arg-Extension (or(x1, x2, ..., xn)):**
- Wenn IRGENDEIN Argument T → **T** (Kurzschluss)
- Wenn ALLE Argumente F → **F**
- Sonst (mindestens eins U, keines T) → **U**

### 4.3 `not(x)` – Logisches NICHT

| x | Ergebnis | Begrundung |
|---|---|---|
| T | **F** | Negation von wahr |
| F | **T** | Negation von falsch |
| U | **U** | Negation von unbekannt ist unbekannt |

---

## 5. Evaluierungsregeln fuer Constraint-Arten

### 5.1 `forbid` – Verbot

**Semantik:** `NICHT(condition)` – Kein Testfall darf die Bedingung erfullen.

| evaluate(condition) | Constraint verletzt? | Aktion | Begrundung |
|---|---|---|---|
| **T** | JA | **Testfall verwerfen** (return False) | Bedingung ist sicher erfullt → Verbot aktiv |
| **F** | NEIN | **Testfall behalten** (return True) | Bedingung ist sicher NICHT erfullt → Verbot inaktiv |
| **U** | UNBEKANNT | **Testfall behalten** (return True) | AK-6: "nur werfen, wenn sicher verletzt" → im Zweifel behalten |

**Begrundung fur U→behalten:** Ein partieller Testfall mit unbekannter Bedingung konnte
spater, wenn alle Kategorien gesetzt sind, entweder T oder F ergeben. Da wir nur sicher
verletzte Testfaelle verwerfen durfen, behalten wir ihn. Bei spaterer Vollstandigkeit wird
er erneut gepruft.

### 5.2 `implies` – Implikation

**Semantik:** `WENN(condition) DANN(consequence)` – Jeder Testfall, der die Bedingung erfullt,
muss auch die Folge erfullen.

Logisch aquivalent zu: `NOT(condition AND NOT(consequence))`

| evaluate(condition) | evaluate(consequence) | Constraint verletzt? | Aktion | Begrundung |
|---|---|---|---|---|
| **T** | **T** | NEIN | **Behalten** (True) | Bedingung erfullt, Folge erfullt → alles OK |
| **T** | **F** | JA | **Verwerfen** (False) | Bedingung erfullt, Folge NICHT erfullt → Verletzung |
| **T** | **U** | JA | **Verwerfen** (False) | Bedingung sicher erfullt, Folge unbekannt → Folge MUSS sicher erfullt sein, ist sie aber nicht → Verletzung |
| **F** | **T** | NEIN | **Behalten** (True) | Antezedens nicht erfullt → Regel irrelevant |
| **F** | **F** | NEIN | **Behalten** (True) | Antezedens nicht erfullt → Regel irrelevant |
| **F** | **U** | NEIN | **Behalten** (True) | Antezedens nicht erfullt → Regel irrelevant, Folge egal |
| **U** | **T** | NEIN | **Behalten** (True) | Bedingung unbekannt → nicht sicher verletzt → behalten (AK-6) |
| **U** | **F** | NEIN | **Behalten** (True) | Bedingung unbekannt → nicht sicher verletzt → behalten (AK-6) |
| **U** | **U** | NEIN | **Behalten** (True) | Beides unbekannt → nicht sicher verletzt → behalten (AK-6) |

**Kritische Entscheidung: condition=T, consequence=U → verwerfen**

Begrundung: Wenn die Bedingung sicher erfullt ist, muss die Folge ebenfalls sicher erfullt sein.
Wenn die Folge unbekannt ist (weil eine Kategorie fehlt), kann der Testfall spater eine
Verletzung ergeben. Da wir aber garantieren mussen, dass kein ausgelieferter Testfall
einen Constraint verletzt, und wir bei condition=T wissen, dass die Regel aktiv ist,
mussen wir den Testfall verwerfen – es gibt keine Moglichkeit, die Folge "nachzuholen",
wenn eine Kategorie fehlt.

**Alternative (konservativer):** condition=T, consequence=U → behalten.
Dies wurde angewendet, wenn die Generierung den Testfall spater vervollstandigt und erneut
pruft. Die Implementierung MUSS entscheiden, ob sie im inkrementalen Modus (verwerfen)
oder im batch-Modus (behalten + spater prufen) arbeitet.

**Entscheidung fur diese Spezifikation:** Wir verwenden den **konservativen Ansatz**:
condition=T, consequence=U → **behalten (True)**.

Begrundung: Pairwise/T-Wise generieren inkrementell. Ein partieller Testfall wird spater
erganzt und erneut gepruft. Wenn wir ihn zu fruh verwerfen, koennen wir gueltige Kombinationen
verlieren. Der AK-6-Grundsatz "nur werfen, wenn sicher verletzt" gilt auch hier:
wenn consequence=U, ist die Verletzung nicht sicher.

**Korrektur der Tabelle:**

| evaluate(condition) | evaluate(consequence) | Constraint verletzt? | Aktion | Begrundung |
|---|---|---|---|---|
| **T** | **T** | NEIN | **Behalten** (True) | Bedingung + Folge erfullt |
| **T** | **F** | JA | **Verwerfen** (False) | Bedingung erfullt, Folge nicht |
| **T** | **U** | NEIN | **Behalten** (True) | Folge unbekannt → nicht sicher verletzt (AK-6) |
| **F** | _ | NEIN | **Behalten** (True) | Antezedens nicht erfullt → irrelevant |
| **U** | _ | NEIN | **Behalten** (True) | Bedingung unbekannt → nicht sicher verletzt (AK-6) |

**Kurzfassung fur `implies`:**
- Verwerfen NUR wenn: `condition == T AND consequence == F`
- Sonst: behalten

---

## 6. Python-Pseudocode

```python
from __future__ import annotations
from typing import Optional, Dict, List, Any


def evaluate_3vl(
    ast: dict[str, Any],
    assignment: Dict[int, int],
) -> Optional[bool]:
    """
    Evaluiert einen JSON-AST (ADR-020) mit dreiwertiger Logik.

    Args:
        ast: JSON-AST-Node gemass ADR-020
        assignment: {category_id: value_id} – None wenn Kategorie nicht gesetzt
                     (Kategorie fehlt im Dict oder assignment[cat_id] is None)

    Returns:
        True  – Bedingung ist sicher erfullt
        False – Bedingung ist sicher NICHT erfullt
        None  – Unbekannt (mindestens eine Kategorie nicht gesetzt)
    """
    op = ast["op"]

    # --- Atomare Operatoren ---
    if op == "eq":
        cat_val = assignment.get(ast["category_id"])
        if cat_val is None:
            return None  # U: Kategorie nicht gesetzt
        return cat_val == ast["value_id"]

    if op == "ne":
        cat_val = assignment.get(ast["category_id"])
        if cat_val is None:
            return None
        return cat_val != ast["value_id"]

    if op == "in":
        cat_val = assignment.get(ast["category_id"])
        if cat_val is None:
            return None
        return cat_val in ast["value_ids"]

    if op == "not_in":
        cat_val = assignment.get(ast["category_id"])
        if cat_val is None:
            return None
        return cat_val not in ast["value_ids"]

    # --- Logische Verknuepfungen ---
    if op == "not":
        arg = ast["args"][0]
        result = evaluate_3vl(arg, assignment)
        if result is None:
            return None
        return not result

    if op == "and":
        # Kurzschluss: erstes F → F; sonst alle evaluieren
        results = []
        for arg in ast["args"]:
            r = evaluate_3vl(arg, assignment)
            if r is False:
                return False  # Kurzschluss
            results.append(r)
        # Kein F gefunden: alle sind T oder U
        if all(r is True for r in results):
            return True
        return None  # Mindestens ein U, kein F

    if op == "or":
        # Kurzschluss: erstes T → T; sonst alle evaluieren
        results = []
        for arg in ast["args"]:
            r = evaluate_3vl(arg, assignment)
            if r is True:
                return True  # Kurzschluss
            results.append(r)
        # Kein T gefunden: alle sind F oder U
        if all(r is False for r in results):
            return False
        return None  # Mindestens ein U, kein T

    raise ValueError(f"Unbekannter Operator: {op}")


def check_constraint(
    constraint: dict[str, Any],
    assignment: Dict[int, int],
) -> bool:
    """
    Prueft, ob ein partieller Testfall (assignment) einen Constraint verletzt.

    Args:
        constraint: {"kind": "forbid"|"implies", "condition": AST, "consequence": AST?}
        assignment: {category_id: value_id}

    Returns:
        True  – Testfall ist gueltig (Constraint nicht verletzt oder unbekannt)
        False – Testfall verletzt Constraint sicher und muss verworfen werden
    """
    cond_result = evaluate_3vl(constraint["condition"], assignment)

    if constraint["kind"] == "forbid":
        # Verbot: verwerfen NUR wenn condition sicher True
        if cond_result is True:
            return False  # Verletzt → verwerfen
        return True  # False oder None → behalten

    if constraint["kind"] == "implies":
        # Implikation: verwerfen NUR wenn condition=True UND consequence=False
        if cond_result is False:
            return True  # Antezedens nicht erfullt → irrelevant
        if cond_result is None:
            return True  # Bedingung unbekannt → nicht sicher verletzt (AK-6)
        # cond_result is True: Folge muss geprueft werden
        cons_result = evaluate_3vl(constraint["consequence"], assignment)
        if cons_result is False:
            return False  # Folge sicher nicht erfullt → verwerfen
        return True  # Folge True oder None → behalten (AK-6: nicht sicher verletzt)

    raise ValueError(f"Unbekannte Constraint-Art: {constraint['kind']}")


def check_all_constraints(
    constraints: List[dict[str, Any]],
    assignment: Dict[int, int],
) -> bool:
    """
    Prueft alle Constraints gegen einen partiellen Testfall.

    Returns:
        True  – Kein Constraint sicher verletzt
        False – Mindestens ein Constraint sicher verletzt
    """
    for c in constraints:
        if not check_constraint(c, assignment):
            return False
    return True
```

---

## 7. Invarianten

Die Implementierung muss folgende Invarianten gewahrleisten:

| # | Invariante | Begrundung |
|---|---|---|
| I1 | `evaluate_3vl` gibt niemals `None` zuruck, wenn alle im AST referenzierten Kategorien im assignment gesetzt sind | Vollstandige Testfaelle haben binare Ergebnisse |
| I2 | `check_constraint` gibt `False` (verwerfen) nur zuruck, wenn `evaluate_3vl` der condition `True` liefert (forbid) bzw. condition=True und consequence=False (implies) | AK-6: "nur werfen, wenn sicher verletzt" |
| I3 | `check_all_constraints` gibt `False` zuruck, wenn IRGENDEIN Constraint verletzt ist | Alle Constraints mussen gelten |
| I4 | Ein leerer assignment `{}` ergibt fur alle atomaren Operatoren `None` | Keine Kategorie ist gesetzt |
| I5 | `not(not(x))` ergibt denselben Wert wie `x` (inkl. None) | Doppelte Negation |
| I6 | `and(x)` mit einem Argument ist semantisch aquivalent zu `x` (wenn 1-Arg erlaub ware) | Identitat |
| I7 | `or(x)` mit einem Argument ist semantisch aquivalent zu `x` | Identitat |
| I8 | `and(T, x) == x` und `or(F, x) == x` fur alle x in {T, F, U} | Identitaetselemente |
| I9 | `and(F, x) == F` und `or(T, x) == T` fur alle x in {T, F, U} | Absorptionsgesetze |
| I10 | De Morgan: `not(and(x, y)) == or(not(x), not(y))` in 3VL | De Morgan-Gesetze gelten in Kleene-3VL |

---

## 8. Edge Cases

| # | Szenario | assignment | Erwartetes Verhalten |
|---|---|---|---|
| E1 | Leerer AST (soll nie vorkommen) | beliebig | Spezifikation: nicht definiert; Implementierung: ValueError |
| E2 | Alle Kategorien im AST sind None im assignment | `{}` | `evaluate_3vl` → `None` (unbekannt); `check_constraint` → `True` (behalten) |
| E3 | Gemischte Werte: einige Kategorien gesetzt, andere nicht | `{1: 10}` bei AST mit cat 1 und cat 2 | `None` propagation durch AND/OR |
| E4 | Constraint referenziert Kategorie, die im Modell nicht existiert | beliebig | `assignment.get(cat_id)` → `None` → `None` (unbekannt) → behalten |
| E5 | `forbid` mit immer-False-Bedingung (z.B. `eq(a,1) AND eq(a,2)`) | `{a: 1}` | `and(T, F)` → `F` → behalten (korrekt: Verbot nie aktiv) |
| E6 | `implies` mit immer-True-Bedingung | `{a: 1}` bei `eq(a,1)` | condition=T → consequence wird gepruft |
| E7 | Verschachtelungstiefe 5 (Maximum aus ADR-020) | beliebig | Rekursion funktioniert ohne StackOverflow (max 5*20=100 Nodes) |
| E8 | 20 atomare Vergleiche in einem `and` (Maximum aus ADR-020) | beliebig | Kurzschluss-Funktioniert korrekt |
| E9 | `in` mit leerer value_ids-Liste (soll nie vorkommen, ADR-020: min 2) | beliebig | Implementierung: `x in []` → `False`; Validierung verhindert |
| E10 | `not_in` mit leerer value_ids-Liste | beliebig | `x not in []` → `True`; Validierung verhindert |
| E11 | Constraint mit sich selbst widersprechender Bedingung (z.B. `eq(a,1) AND ne(a,1)`) | `{a: 1}` | `and(T, F)` → `F` → forbid: behalten (korrekt) |
| E12 | Mehrere Constraints, einer verletzt, einer nicht | beliebig | `check_all_constraints` → `False` (mindestens einer verletzt) |

---

## 9. Test-Fall-Spezifikation

Folgende 20 reprasentative Testfaelle mussen als Unit-Tests implementiert werden.
Jeder Testfall hat eine eindeutige ID, einen AST, ein assignment und einen Erwartungswert.

### 9.1 Atomare Operatoren (Tests T01–T06)

| ID | Beschreibung | AST | assignment | Erwartung `evaluate_3vl` |
|---|---|---|---|---|
| T01 | `eq` mit treffer | `{"op":"eq","category_id":1,"value_id":10}` | `{1: 10}` | `True` |
| T02 | `eq` ohne Treffer | `{"op":"eq","category_id":1,"value_id":10}` | `{1: 20}` | `False` |
| T03 | `eq` mit None-Kategorie | `{"op":"eq","category_id":1,"value_id":10}` | `{}` | `None` |
| T04 | `ne` mit Treffer | `{"op":"ne","category_id":1,"value_id":10}` | `{1: 20}` | `True` |
| T05 | `in` mit Treffer | `{"op":"in","category_id":1,"value_ids":[10,20]}` | `{1: 10}` | `True` |
| T06 | `not_in` mit None-Kategorie | `{"op":"not_in","category_id":1,"value_ids":[10,20]}` | `{}` | `None` |

### 9.2 Logische Verknupfungen (Tests T07–T14)

| ID | Beschreibung | AST | assignment | Erwartung `evaluate_3vl` |
|---|---|---|---|---|
| T07 | `and(T, T)` | `{"op":"and","args":[{"op":"eq","category_id":1,"value_id":10},{"op":"eq","category_id":2,"value_id":20}]}` | `{1:10, 2:20}` | `True` |
| T08 | `and(T, F)` | `{"op":"and","args":[{"op":"eq","category_id":1,"value_id":10},{"op":"eq","category_id":2,"value_id":20}]}` | `{1:10, 2:30}` | `False` |
| T09 | `and(T, U)` – Kurzschluss nicht moeglich | `{"op":"and","args":[{"op":"eq","category_id":1,"value_id":10},{"op":"eq","category_id":2,"value_id":20}]}` | `{1:10}` | `None` |
| T10 | `or(F, F)` | `{"op":"or","args":[{"op":"ne","category_id":1,"value_id":10},{"op":"ne","category_id":2,"value_id":20}]}` | `{1:10, 2:20}` | `False` |
| T11 | `or(F, U)` | `{"op":"or","args":[{"op":"ne","category_id":1,"value_id":10},{"op":"ne","category_id":2,"value_id":20}]}` | `{1:10}` | `None` |
| T12 | `not(T)` | `{"op":"not","args":[{"op":"eq","category_id":1,"value_id":10}]}` | `{1:10}` | `False` |
| T13 | `not(U)` | `{"op":"not","args":[{"op":"eq","category_id":1,"value_id":10}]}` | `{}` | `None` |
| T14 | `and` mit 3 Args, mittlere U | `{"op":"and","args":[{"op":"eq","cat":1,"val":10},{"op":"eq","cat":2,"val":20},{"op":"eq","cat":3,"val":30}]}` | `{1:10, 3:30}` | `None` |

### 9.3 Forbid-Constraints (Tests T15–T18)

| ID | Beschreibung | Constraint | assignment | Erwartung `check_constraint` |
|---|---|---|---|---|
| T15 | Forbid: condition=T → verwerfen | `{"kind":"forbid","condition":{"op":"eq","category_id":1,"value_id":10}}` | `{1: 10}` | `False` |
| T16 | Forbid: condition=F → behalten | `{"kind":"forbid","condition":{"op":"eq","category_id":1,"value_id":10}}` | `{1: 20}` | `True` |
| T17 | Forbid: condition=None → behalten (AK-6) | `{"kind":"forbid","condition":{"op":"eq","category_id":1,"value_id":10}}` | `{}` | `True` |
| T18 | Forbid: `and(T, U)` → None → behalten | `{"kind":"forbid","condition":{"op":"and","args":[{"op":"eq","category_id":1,"value_id":10},{"op":"eq","category_id":2,"value_id":20}]}}` | `{1: 10}` | `True` |

### 9.4 Implies-Constraints (Tests T19–T24)

| ID | Beschreibung | Constraint | assignment | Erwartung `check_constraint` |
|---|---|---|---|---|
| T19 | Implies: cond=T, cons=T → behalten | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{1:10, 2:20}` | `True` |
| T20 | Implies: cond=T, cons=F → verwerfen | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{1:10, 2:30}` | `False` |
| T21 | Implies: cond=T, cons=None → behalten (AK-6) | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{1:10}` | `True` |
| T22 | Implies: cond=F, _ → behalten | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{1:20}` | `True` |
| T23 | Implies: cond=None, _ → behalten | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{}` | `True` |
| T24 | Implies: cond=None, cons=F → behalten (AK-6) | `{"kind":"implies","condition":{"op":"eq","cat":1,"val":10},"consequence":{"op":"eq","cat":2,"val":20}}` | `{2:30}` | `True` |

### 9.5 Komplexes Beispiel (Tests T25–T27)

| ID | Beschreibung | Constraint | assignment | Erwartung `check_constraint` |
|---|---|---|---|---|
| T25 | Forbid: `and(eq(1,10), ne(2,20), in(3,[30,40]))` – alle T → verwerfen | Forbid mit 3-Arg-AND | `{1:10, 2:30, 3:30}` | `False` |
| T26 | Forbid: gleiches AST, cat 2 nicht gesetzt → `and(T, U, T)` → U → behalten | Gleiches AST | `{1:10, 3:30}` | `True` |
| T27 | Implies: `and(eq(1,10), eq(2,20)) → not_in(3,[30,40])` – cond=T, cons=F → verwerfen | Implies mit komplexem AST | `{1:10, 2:20, 3:30}` | `False` |

---

## 10. Property-Test-Spezifikation

Neben den obigen Unit-Tests sollen folgende Property-Tests implementiert werden:

### P1: Idempotenz bei vollstandigen Testfallen
Fur jeden vollstandigen Testfall (alle Kategorien gesetzt) gilt:
`evaluate_3vl(ast, assignment)` ist niemals `None`.

### P2: Monotonie bei Erganzung
Wenn `evaluate_3vl(ast, assignment1) == False` und `assignment1` eine Teilmenge von `assignment2` ist,
dann gilt `evaluate_3vl(ast, assignment2) != True` NUR wenn der AST monotone Eigenschaften hat.
**Hinweis:** Diese Eigenschaft gilt NICHT allgemein fur 3VL (z.B. `ne` kehrt sich um).
Sie gilt nur fur bestimmte AST-Strukturen. Daher: KEIN generischer Property-Test,
sondern spezifische Tests pro Operator.

### P3: Random-Model-Test
Zufallige Modelle mit 3-5 Kategorien, 2-5 Werten pro Kategorie, 1-3 zufallige Constraints.
Jede Strategie (pairwise, t_wise, each_choice) generiert Testfaelle.
Kein ausgelieferter Testfall verletzt einen Constraint.

### P4: De Morgan-Gesetze in 3VL
Fur alle x, y in {T, F, U}:
- `not(and(x, y)) == or(not(x), not(y))`
- `not(or(x, y)) == and(not(x), not(y))`

### P5: Kurzschluss-Korrektheit
`and(F, <beliebig>)` == F; `or(T, <beliebig>)` == T
unabhangig vom zweiten Argument (auch wenn es eine Exception werfen wurde).

---

## 11. Abgrenzung zu bestehender RuleEngine

Die bestehende `RuleEngine.is_combination_valid()` (REQ-3040) arbeitet mit
einfachen `ForbiddenRule`/`CombineRule`/`DependencyRule`-Objekten und verwendet
bereits eine implizite 3VL: wenn eine Kategorie nicht gesetzt ist, wird die
Prufung ubersprungen (return True = behalten).

Die neue `evaluate_3vl()` / `check_constraint()` arbeitet mit dem JSON-AST-Format
aus ADR-020 und unterstutzt verschachtelte logische Ausdrucke mit UND/ODER/NICHT.
Beide Systeme koennen parallel existieren:

- **Bestehende RuleEngine:** Einfache 2-Kategorie-Regeln, schnell, etabliert
- **Neue Constraint-Evaluation:** Komplexe Mehrbedingungs-Regeln, AST-basiert, 3VL

Die Strategien (pairwise, t_wise, etc.) mussen entscheiden, welche Prufung sie
anwenden. Idealerweise werden beide kombiniert:
```
if not rule_engine.is_combination_valid(partial):
    return False
if not check_all_constraints(constraints, partial):
    return False
return True
```

---

## 12. Kombinatorik-Befund

```markdown
# Kombinatorik-Befund

Strategie/REQ: REQ-6001 AK-6 (Pairwise/T-Wise + dreiwertige Logik)
Referenz: ADR-020 (JSON-AST-Format)

Invarianten:
- I1-I10 (siehe Abschnitt 7)
- AK-6: "nur werfen, wenn sicher verletzt" → None → immer behalten

Testfaelle:
- 27 Unit-Tests (T01-T27) fur evaluate_3vl und check_constraint
- 5 Property-Tests (P1-P5) fur generische Eigenschaften

Befund: SPEZIFIKATION VOLLSTAENDIG

Empfehlung:
1. Senior Developer implementiert evaluate_3vl() und check_constraint() gemass Pseudocode
2. TDD: Zuerst Tests T01-T27 als failing, dann Implementierung
3. Property-Tests P1-P5 als zusatzliche Sicherheit
4. Integration in pairwise/t_wise: is_combination_valid() erweitert um check_all_constraints()
5. ADR-020 Dreiwertige-Logik-Sektion aktualisieren mit Verweis auf diese Spezifikation
6. BACKWARD-COMPAT: Bestehende RuleEngine.is_combination_valid() bleibt unverandert
```

---

## 13. Offene Fragen

| # | Frage | Status |
|---|---|---|
| Q1 | Soll `evaluate_3vl` bei unbekanntem `category_id` (nicht im Modell) eine Exception werfen oder `None` zuruckgeben? | Empfehlung: `None` (konservativ, wie bei nicht-gesetzter Kategorie) |
| Q2 | Sollen Constraints mit `is_valid=False` (ungultige Referenzen, ADR-020) in `check_all_constraints` ubersprungen werden? | Empfehlung: Ja, mit Logging-Warnung |
| Q3 | Wie wird die Performance bei vielen Constraints (100+) und groBen Modellen (50 Kategorien) sichergestellt? | Empfehlung: Kurzschluss in `and`/`or` + fruhes Abbruch in `check_all_constraints`; Benchmark-Test P3 |