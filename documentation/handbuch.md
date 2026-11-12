# G.R.E.A.T. — Benutzerhandbuch

**Georg Radikal Einfacher Automatisierter TestcaseDesigner**

*Version 1.8.0 | Stand November 2026*

---

## Inhaltsverzeichnis

1. [Erste Schritte](#1-erste-schritte)
   - 1.1 Anmeldung
   - 1.2 Erststart & Standardpasswort
   - 1.3 Passwort wechseln
   - 1.4 Projektuebersicht
2. [Projekte verwalten](#2-projekte-verwalten)
   - 2.1 Projekt anlegen
   - 2.2 Projekt loeschen
   - 2.3 Datenbank zuruecksetzen
3. [Kategorien & Werte](#3-kategorien--werte)
   - 3.1 Kategorien anlegen
   - 3.2 Kategorien umbenennen & loeschen
   - 3.3 Kategorie-Typen (Normal, Ursache, Wirkung, Ergebnis)
   - 3.4 Werte verwalten
   - 3.5 Fehlerwerte markieren
   - 3.6 Default-Wert (Lineare Expansion)
   - 3.7 Risiko-Gewichtung
   - 3.8 Drag & Drop Sortierung
4. [Regeln](#4-regeln)
   - 4.1 Regeltypen ueberblick
   - 4.2 Verbotene Kombinationen (Forbidden)
   - 4.3 Abhaengigkeiten (Dependency)
   - 4.4 Kombinieren (Combine)
   - 4.5 Regelvisualisierung
   - 4.6 Regelwidersprueche erkennen
5. [Testfall-Generierung](#5-testfall-generierung)
   - 5.1 Generierungsstrategien ueberblick
   - 5.2 All Combinations
   - 5.3 Pairwise / Orthogonal
   - 5.4 Each Choice
   - 5.5 Lineare Expansion
   - 5.6 T-Wise
   - 5.7 MC/DC
   - 5.8 Risk-Based
   - 5.9 BVA (Boundary Value Analysis)
   - 5.10 Regeln bei Generierung anwenden
6. [Risikoabdeckung](#6-risikoabdeckung)
   - 6.1 Risikoabdeckung pro Testfall
   - 6.2 Risikoabdeckungs-Prozentsatz
   - 6.3 Risiko-Zusammenfassung
7. [Export](#7-export)
   - 7.1 CSV-Export
   - 7.2 JSON-Export
   - 7.3 Excel-Export
   - 7.4 Fehlerwert-Kennzeichnung im Export
8. [Datenklassen](#8-datenklassen)
   - 8.1 System-Datenklassen
   - 8.2 Eigene Datenklassen
   - 8.3 Datenklassen in Projekten verwenden
9. [Einstellungen](#9-einstellungen)
   - 9.1 Erscheinungsbild (Themes)
   - 9.2 Maximale Anzahl Testfaelle
   - 9.3 Datensicherung
10. [Benutzer & Rollen](#10-benutzer--rollen)
   - 10.1 Rollen: Admin, Editor, Viewer
   - 10.2 Projekt-Freigabe
   - 10.3 Benutzer verwalten
11. [Tastaturnavigation & Shortcuts](#11-tastaturnavigation--shortcuts)
12. [Glossar](#12-glossar)
13. [Haeufige Fragen (FAQ)](#13-haeufige-fragen-faq)

---

## 1. Erste Schritte

### 1.1 Anmeldung

![Login-Seite](./screenshots/01-login.png)

G.R.E.A.T. startet mit einer Login-Seite. Geben Sie Ihren Benutzernamen und Ihr Passwort ein.

| Feld | Beschreibung |
|------|-------------|
| **Benutzername** | Ihr vom Admin zugewiesener Benutzername |
| **Passwort** | Ihr persoenliches Passwort |

Bei falscher Eingabe erscheint eine Fehlermeldung. Nach drei fehlgeschlagenen Versuchen wird das Konto kurz gesperrt.

### 1.2 Erststart & Standardpasswort

Beim allerersten Start des Systems zeigt die Login-Seite das **Standardpasswort** des Admin-Accounts an. Dies ist ein bewusster Kompromiss aus Einfachheit und Sicherheit:

- Der Standard-Admin-Benutzer heisst `admin`
- Das Standardpasswort wird einmalig bei der Login-Seite angezeigt
- Nach der ersten Anmeldung sind Sie **verpflichtet**, das Passwort zu aendern (siehe 1.3)

> **Hinweis:** Kopieren Sie das Standardpasswort sofort in einen Passwort-Manager. Nach dem Verlassen der Login-Seite ist es nicht mehr einsehbar.

### 1.3 Passwort wechseln

![Passwortwechsel](./screenshots/02-passwortwechsel.png)

Nach der Erstanmeldung werden Sie automatisch zur Passwortwechsel-Seite weitergeleitet. Auch spaeter koennen Sie Ihr Passwort ueber die Top-Navigation unter **"Passwort aendern"** wechseln.

**Anforderungen an das neue Passwort:**

| Kriterium | Minimum |
|-----------|---------|
| Laenge | 12 Zeichen |
| Grossbuchstaben | mindestens 1 |
| Kleinbuchstaben | mindestens 1 |
| Ziffern | mindestens 1 |
| Sonderzeichen | mindestens 1 |

> **Warnung:** Das alte Standardpasswort kann nicht wieder als neues Passwort verwendet werden (`password_is_default`).

### 1.4 Projektuebersicht

Nach erfolgreicher Anmeldung gelangen Sie zur **Projektuebersicht**. Hier sehen Sie alle Projekte, auf die Sie Zugriff haben:

![Projektuebersicht](./screenshots/03-projektuebersicht.png)

| Aktion | Beschreibung |
|--------|-------------|
| **Neues Projekt** | Legt ein neues, leeres Projekt an |
| **Projekt loeschen** | Entfernt ein Projekt unwiderruflich (mit Bestatigung) |
| **Bulk-Delete** | Loescht mehrere Projekte auf einmal |
| **Datenbank zuruecksetzen** | Stellt die Startkonfiguration wieder her (alle Daten gehen verloren) |

---

## 2. Projekte verwalten

### 2.1 Projekt anlegen

Klicken Sie auf **"Neues Projekt"** und geben Sie einen Namen ein. Das Projekt wird mit einer Beispielpopulierung gestartet (kann sofort bearbeitet werden).

### 2.2 Projekt loeschen

Rechtsklick auf ein Projekt im Projektbaum oeffnet das Kontextmenue mit der Option **"Loeschen"**. Eine Bestatigungsforderung verhindert versehentliche Loeschungen.

> **Achtung:** Alle Kategorien, Werte, Regeln und generierten Testfaelle des Projekts gehen unwiderruflich verloren.

### 2.3 Datenbank zuruecksetzen

In den **Einstellungen** finden Sie den Button **"Datenbank zuruecksetzen"**. Dies loescht alle Projekte, Benutzer (außer dem Admin) und stellt die Startkonfiguration wieder her.

> **Warnung:** Diese Aktion ist unwiderruflich. Sichern Sie wichtige Daten vorher (siehe 9.3).

---

## 3. Kategorien & Werte

Kategorien sind die Grundbausteine eines Testprojekts. Jede Kategorie entspricht einem Testparameter (z. B. "Betriebssystem", "Browser", "Datenbank").

### 3.1 Kategorien anlegen

![Kategorie anlegen](./screenshots/03-01-kategorie-anlegen.png)

1. Oeffnen Sie ein Projekt
2. Im linken Bereich (Kategoriebaum) erscheint ein Eingabefeld **"Neue Kategorie"**
3. Geben Sie den Namen ein und drücken Sie Enter
4. Die Kategorie erscheint im Baum

**Kategorie-Typen bei der Anlage:**

| Typ | Bedeutung | Symbol |
|-----|-----------|--------|
| **Normal** | Standard-Kategorie | — |
| **Ursache** | Ursache in Ursache-Wirkung-Diagrammen | U |
| **Wirkung** | Wirkung in Ursache-Wirkung-Diagrammen | W |
| **Ergebnis** | Nicht an Generierung beteiligt, manuelle Eingabe | E |

### 3.2 Kategorien umbenennen & loeschen

| Aktion | Wie |
|--------|-----|
| **Umbenennen** | Rechtsklick → "Umbenennen" oder **F2** auf ausgewaehlter Kategorie |
| **Loeschen** | Rechtsklick → "Loeschen" (mit Bestatigung) |
| **Typ aendern** | Rechtsklick → "Typ: Normal/Ursache/Wirkung" |

### 3.3 Kategorie-Typen im Detail

**Ergebnis-Kategorien (`is_result=True`):**
- Werden **nicht** bei der automatischen Testfall-Generierung beruecksichtigt
- Konnen nach der Generierung manuell in der Testfalltabelle befuellt werden
- Erkennbar am **E**-Badge im Kategoriebaum

### 3.4 Werte verwalten

Jede Kategorie kann beliebig viele Werte enthalten. Werte代表 die moeglichen Eingabewerte fuer einen Testparameter.

![Werte verwalten](./screenshots/03-04-werte-verwalten.png)

| Aktion | Wie |
|--------|-----|
| **Wert hinzufuegen** | Klick auf "+" neben der Kategorie |
| **Wert umbenennen** | Rechtsklick → "Umbenennen" oder **F2** |
| **Wert loeschen** | Rechtsklick → "Loeschen" |
| **Werte sortieren** | Drag & Drop im Wertelistenbereich |

**Werte-Zaehler:** Rechts neben jeder Kategorie zeigt ein Badge die Anzahl der Werte an. Ist die Kategorie noch nicht geoeffnet, erscheint "…" — ein Klick laedt die Werte.

### 3.5 Fehlerwerte markieren

Fehlerwerte (auch "Ungueltige Werte" genannt) sind Eingaben, die **nicht erlaubt** sind und die das System ablehnen soll. Sie sind wichtig fuer negative Tests.

![Fehlerwert markieren](./screenshots/03-05-fehlerwert.png)

**Markierung als Fehlerwert:**
1. Rechtsklick auf den Wert
2. **"Als Fehlerwert markieren"** anklicken
3. Der Wert wird mit einem **✕**-Symbol (rot) gekennzeichnet

**Verhalten bei Generierung:**
- Fehlerwerte werden in die Testfallgenerierung einbezogen
- Testfaelle mit Fehlerwerten werden **ans Ende der Liste** sortiert
- Im Export erscheint eine Spalte "Fehlerwert" (JA/NEIN)

### 3.6 Default-Wert (Lineare Expansion)

Die Strategie **"Lineare Expansion"** benoetigt pro Kategorie einen **Default-Wert**. Dieser Wert wird in allen Testfaellen verwendet, ausser in dem Testfall, der den aktuellen Wert testet.

![Default-Wert](./screenshots/03-06-default-wert.png)

**Default-Wert setzen:**
1. Rechtsklick auf den Wert
2. **"★ Als Default markieren"** anklicken
3. Der Wert wird mit einem **★**-Symbol (gold) gekennzeichnet

**Default-Wert entfernen:**
1. Rechtsklick auf den Default-Wert
2. **"✕ Default entfernen"** anklicken

> **Wichtig:** Pro Kategorie kann nur **ein** Default-Wert existieren. Setzen Sie einen neuen Default, wird der alte automatisch entfernt.

**Symbolueberblick:**

| Symbol | Bedeutung | Farbe |
|--------|-----------|-------|
| ★ | Default-Wert (Lineare Expansion) | Gold/Amber |
| ✕ | Fehlerwert (nicht erlaubt) | Rot |
| R1–R10 | Risiko-Gewichtung | Orange |

### 3.7 Risiko-Gewichtung

Jeder Wert kann ein **Risiko-Gewicht** (1–10) erhalten. Hoehere Gewichte bedeuten hoeheres Risiko und werden bei risikobasierten Strategien priorisiert.

![Risiko-Gewichtung](./screenshots/03-07-risiko.png)

**Einstellung:**
- Im Wertelistenbereich erscheint ein kleines Eingabefeld (Default: 1)
- Rechtsklick auf den Wert → Risiko aendern
- Werte mit Risiko > 2 werden mit **R{n}**-Badge markiert

### 3.8 Drag & Drop Sortierung

Kategorien und Werte koennen per **Drag & Drop** sortiert werden:

- **Kategorien:** Ziehen Sie eine Kategorie im Baum nach oben/unten
- **Werte:** Ziehen Sie einen Wert in der Werteliste um

Die Sortierung bestimmt die Reihenfolge in generierten Testfaellen und Exporten.

---

## 4. Regeln

Regeln definieren Zusammenhaenge zwischen Werten verschiedener Kategorien. Sie reduzieren den Testraum auf relevante Kombinationen.

### 4.1 Regeltypen ueberblick

| Typ | Symbol | Bedeutung | Farbe |
|-----|--------|-----------|-------|
| **Verboten** (Forbidden) | ✕ | Wenn A=X, dann B!=Y | Rot |
| **Abhaengig** (Dependency) | → | Wenn A=X, dann B=Y | Violett |
| **Kombinieren** (Combine) | ⊂ | Wenn A=X, dann B in [Y,Z,...] | Gruen |

### 4.2 Verbotene Kombinationen (Forbidden)

Eine verbotene Kombination sagt: "Wenn Kategorie A den Wert X hat, darf Kategorie B **nicht** den Wert Y haben."

![Forbidden-Regel](./screenshots/04-02-forbidden.png)

**Beispiel:**
- Wenn **Browser = Internet Explorer**, dann **CSS-Feature != Grid Layout**
- Diese Kombination wird bei der Generierung automatisch ausgeschlossen

**Anlegen:**
1. Im Regelbereich auf **"Verbotene Regel"** klicken
2. Wenn-Kategorie und Wenn-Wert auswahlen
3. Dann-Kategorie und Dann-Wert auswahlen
4. Regel wird sofort gespeichert

### 4.3 Abhaengigkeiten (Dependency)

Eine Abhaengigkeit sagt: "Wenn Kategorie A den Wert X hat, **muss** Kategorie B den Wert Y haben."

![Dependency-Regel](./screenshots/04-03-dependency.png)

**Beispiel:**
- Wenn **Datenbank = Oracle**, dann **Treiber = JDBC**
- Diese Kombination wird erzwungen

### 4.4 Kombinieren (Combine)

Eine Combine-Regel sagt: "Wenn Kategorie A den Wert X hat, darf Kategorie B **nur** einen der Werte aus der Liste [Y, Z, ...] haben."

![Combine-Regel](./screenshots/04-04-combine.png)

**Beispiel:**
- Wenn **Betriebssystem = Linux**, dann **Webserver in [Apache, Nginx]**
- Andere Webserver (IIS, Tomcat) werden fuer Linux ausgeschlossen

### 4.5 Regelvisualisierung

![Regelvisualisierung](./screenshots/04-05-visualisierung.png)

G.R.E.A.T. zeigt Regeln als **SVG-basierte Verbindungslinien** zwischen den Werten verschiedener Kategorien:

| Regeltyp | Linienstil | Farbe |
|----------|-----------|-------|
| Verboten | Gestrichelt + ✕ | Rot |
| Abhaengig | Durchgehend + → | Violett |
| Kombinieren | Punktiert + ⊂ | Gruen |

**Interaktion:**
- **Hover:** Mauszeiger ueber Linie zeigt Tooltip mit Regeldetails
- **Refresh:** ↻-Button aktualisiert die Visualisierung
- **Hoehe anpassen:** Resize-Handle zum Vergrößern/Verkleinern

### 4.6 Regelwidersprueche erkennen

G.R.E.A.T. prueft automatisch auf Widersprueche zwischen Regeln:

- **Duplikate:** Gleiche Regel existiert bereits
- **Widersprueche:** Zwei Regeln erzwingen gegensatzliche Werte
- **Tote Werte:** Ein Wert kann durch Regeln nie in einem Testfall erscheinen

Warnungen erscheinen als Toast-Nachrichten bei Regelanlage.

---

## 5. Testfall-Generierung

### 5.1 Generierungsstrategien ueberblick

| Strategie | Abkuerzung | Beschreibung | Wann verwenden |
|-----------|-----------|-------------|----------------|
| **All Combinations** | All | Vollstaendige kartesische Produkt | Kleine Projekte, Referenz |
| **Pairwise** | Pair | Jede Wertepaar-Kombination mindestens einmal | Standard, guter Coverage/Aufwand |
| **Orthogonal** | Orth | Orthogonale Arrays | Gleichverteilte Kategorien |
| **Each Choice** | Each | Jeder Wert mindestens einmal | Minimaler Testsatz |
| **Lineare Expansion** | Linear | Pro Kategorie ein Test, Rest auf Default | Geringer Aufwand |
| **T-Wise** | T-Wise | T-weise Kombinationen (t=2–5) | Konfigurierbare Tiefe |
| **MC/DC** | MC/DC | Modified Condition/Decision Coverage | Sicherheitskritisch (DO-178C) |
| **Risk-Based** | Risk | Risikogewichtete Auswahl | Risikofokus |
| **BVA** | BVA | Boundary Value Analysis | Numerische Bereiche |

### 5.2 All Combinations

Generiert **alle moeglichen Kombinationen** aller Werte aller Kategorien.

**Formel:** `Anzahl Testfaelle = W1 × W2 × ... × Wn` (W = Werte pro Kategorie)

**Beispiel:** 3 Kategorien mit je 3 Werten → 3 × 3 × 3 = **27 Testfaelle**

> **Achtung:** Bei vielen Kategorien/Werten explodiert die Anzahl schnell. Standardlimit: 1000 Testfaelle pro Generierung.

**Eigenschaften:**
- 100%ige kombinatorische Abdeckung
- Theoretisches Maximum fuer Risikoabdeckung
- Gut als Referenz fuer andere Strategien

### 5.3 Pairwise / Orthogonal

**Pairwise (All Pairs):** Testet jede **Paar-Kombination** von Werten mindestens einmal. Bei 3 Kategorien mit je 3 Werten: statt 27 nur ca. 9 Testfaelle.

**Orthogonal:** Basiert auf **orthogonalen Arrays** (Sroka/Meyer-Algorithmus). Liefert minimale Testsaetze mit garantierter Paar-Abdeckung.

**Wann verwenden:**
- Paarweise Fehler sind am haeufigsten (Studien: 95%+ der Fehler entstehen durch Interaktionen von 1–2 Parametern)
- Gutes Verhaeltnis von Abdeckung zu Aufwand

### 5.4 Each Choice

Stellt sicher, dass **jeder Wert** in mindestens einem Testfall vorkommt. Liefert den **minimal moeglichen** Testsatz.

**Beispiel:** 3 Kategorien mit 3, 4, 2 Werten → mindestens 4 Testfaelle (determiniert durch die groesste Kategorie)

**Wann verwenden:**
- Schneller Ueberblick
- Sehr grosse Testraeme
- Kombination mit anderen Strategien

### 5.5 Lineare Expansion

Pro Kategorie wird **ein Testfall** erzeugt, in dem der Wert der aktuellen Kategorie variiert und alle anderen Kategorien ihren **Default-Wert** haben.

**Voraussetzung:** Jede Kategorie braucht genau einen **Default-Wert** (markiert mit ★).

**Beispiel:** 3 Kategorien → 3 Testfaelle

**Wann verwenden:**
- Minimaler Testaufwand
- Smoke Tests
- Schnelle Regression

### 5.6 T-Wise

Verallgemeinerung von Pairwise: Testet alle **T-fachen Kombinationen**. Standard: t=2 (identisch mit Pairwise). Konfigurierbar bis t=5.

**Formel:** Hoeheres t → bessere Abdeckung, aber exponentiell mehr Testfaelle

**Einstellung:** In der Generierungs-UI waehlen Sie die T-Staerke (2–5).

### 5.7 MC/DC

**Modified Condition/Decision Coverage** ist ein Testkriterium aus der Luft- und Raumfahrt (DO-178C). Es stellt sicher, dass jede Bedingung in einer booleschen Formel unabhaengig von den anderen Bedingungen den Ausgang beeinflusst.

**Wann verwenden:**
- Sicherheitskritische Software (Avionics, Medizintechnik, Automotive)
- Zertifizierungsanforderungen (DO-178C, ISO 26262)

### 5.8 Risk-Based

Generiert Testfaelle basierend auf den **Risiko-Gewichten** der Werte. Hoeher gewichtete Werte erscheinen haeufiger.

**Voraussetzung:** Werte sollten Risiko-Gewichte (1–10) haben. Default-Gewicht: 1.

**Wann verwenden:**
- Fokus auf hochriskante Bereiche
- Begrenter Testzeitrahmen

### 5.9 BVA (Boundary Value Analysis)

**Boundary Value Analysis** testet die Grenzen von Wertebereichen. Fuer einen Bereich [1; 100] werden typischerweise getestet:
- Unterhalb der Grenze: 0
- Untere Grenze: 1
- Oberhalb der unteren Grenze: 2
- Unterhalb der oberen Grenze: 99
- Obere Grenze: 100
- Oberhalb der oberen Grenze: 101

**Multi-Range BVA:** G.R.E.A.T. unterstuetzt mehrere erlaubte/verbotene Bereiche pro Kategorie.

### 5.10 Regeln bei Generierung anwenden

In der Generierungs-UI finden Sie die Option **"Regeln anwenden"** (Checkbox). Wenn aktiviert:

1. Die Regel-Engine wird vor der Generierung geladen
2. Generate Testfaelle werden nach Regeln gefiltert
3. Verbotene Kombinationen werden entfernt
4. Abhaengigkeiten werden erzwungen
5. Combine-Regeln beschraenken erlaubte Werte

> **Hinweis:** Regeln koennen die Anzahl der generierten Testfaelle deutlich reduzieren.

---

## 6. Risikoabdeckung

### 6.1 Risikoabdeckung pro Testfall

Jeder Testfall erhaelt einen **risk_coverage**-Wert: die **Summe der Risiko-Gewichte** aller zugewiesenen Werte.

**Beispiel:**
| Testfall | Browser (R3) | OS (R5) | DB (R2) | risk_coverage |
|----------|-------------|---------|---------|--------------|
| TC_1 | Chrome | Linux | MySQL | 3 + 5 + 2 = **10** |
| TC_2 | Firefox | Windows | Oracle | 3 + 1 + 5 = **9** |

Testfaelle werden **absteigend nach risk_coverage** sortiert (hohe Risiken zuerst). Testfaelle mit Fehlerwerten kommen trotzdem ans Ende.

### 6.2 Risikoabdeckungs-Prozentsatz

Der **risk_coverage_percent** gibt an, wie gross der Anteil der erfassten Risiken am theoretischen Maximum (All Combinations) ist:

```
Prozent = (Summe aller risk_coverage / Maximum bei All Combinations) × 100
```

| Strategie | Typischer Wert |
|-----------|---------------|
| All Combinations | 100% |
| Pairwise | 40–70% |
| Each Choice | 10–30% |
| Lineare Expansion | 5–15% |

> **Hinweis:** Ein niedriger Prozentsatz bedeutet nicht schlechte Qualität — er zeigt nur, dass weniger Kombinationen getestet werden. Pairwise deckt z. B. 95%+ der paarenweise Fehler ab bei nur 30–50% Risikoabdeckung.

### 6.3 Risiko-Zusammenfassung

Nach der Generierung zeigt G.R.E.A.T. eine **Risiko-Zusammenfassung**:

| Kennzahl | Bedeutung |
|----------|-----------|
| **total_risk** | Summe aller risk_coverage-Werte |
| **max_possible_risk** | Theoretisches Maximum (All Combinations) |
| **risk_coverage_percent** | Erreichter Anteil in % |
| **testcase_count** | Anzahl generierter Testfaelle |

---

## 7. Export

### 7.1 CSV-Export

Exportiert Testfaelle als CSV-Datei (semikolon-getrennt, UTF-8 mit BOM fuer Excel-Kompatibilitaet).

**Spalten:**
- Eine Spalte pro Kategorie
- `__TestCaseID`, `__GenerationID`, `__Strategy`
- `Status` (optional, mit `?status=1`)
- `Fehlerwert` (JA/NEIN)

**URL-Parameter:**
| Parameter | Standard | Beschreibung |
|-----------|---------|-------------|
| `encoding` | `utf-8-sig` | utf-8-sig, utf-8, cp1252, iso-8859-1, utf-16le, utf-16be |
| `excel` | `true` | Fügt `sep=;` als erste Zeile hinzu |
| `bom` | auto | BOM ein/aus |
| `status` | `false` | Regel-Status-Spalte hinzufuegen |

### 7.2 JSON-Export

Exportiert Testfaelle als strukturiertes JSON mit Projekt-, Kategorie- und Testfall-Hierarchie.

**Struktur:**
```json
{
  "generation_id": 1,
  "project_id": 1,
  "strategy": "all",
  "testcase_count": 27,
  "testcases": [
    {
      "name": "TC_1",
      "assignments": {"Browser": "Chrome", "OS": "Linux"},
      "has_error_value": false
    }
  ]
}
```

### 7.3 Excel-Export

Exportiert Testfaelle als `.xlsx`-Datei (openpyxl). Gleiche Spalten wie CSV, aber als native Excel-Tabelle mit fettgedruckten Ueberschriften.

### 7.4 Fehlerwert-Kennzeichnung im Export

Alle Export-Formate enthalten eine Spalte/Field `Fehlerwert` (bzw. `has_error_value`), die **JA/NEIN** (bzw. `true/false`) angibt, ob der Testfall mindestens einen Fehlerwert enthaelt.

---

## 8. Datenklassen

### 8.1 System-Datenklassen

G.R.E.A.T. liefert vordefinierte Datenklassen (Aequivalenzklassen) fuer haeufige Testparameter:

| Datenklasse | Werte |
|-------------|-------|
| **Browser** | Chrome, Firefox, Safari, Edge, IE |
| **Betriebssystem** | Windows, Linux, macOS, iOS, Android |
| **Datenbank** | MySQL, PostgreSQL, Oracle, SQL Server, SQLite |
| **Webserver** | Apache, Nginx, IIS, Tomcat |
| **Aufloesung** | 800×600, 1024×768, 1920×1080, 2560×1440 |
| **Sprache** | Deutsch, Englisch, Franzoesisch, Spanisch |

### 8.2 Eigene Datenklassen

Erstellen Sie eigene Datenklassen in der **Datenklassen-Ansicht** (`/dataclasses`). Eine Datenklasse ist eine benannte Menge von Werten, die in mehreren Projekten wiederverwendbar ist.

### 8.3 Datenklassen in Projekten verwenden

Beim Anlegen einer Kategorie koennen Sie eine bestehende Datenklasse als Vorlage verwenden. Alle Werte der Datenklasse werden automatisch als Werte der Kategorie angelegt.

---

## 9. Einstellungen

### 9.1 Erscheinungsbild (Themes)

![Theme-Auswahl](./screenshots/09-01-themes.png)

G.R.E.A.T. unterstuetzt mehrere Themes:

| Theme | Beschreibung |
|-------|-------------|
| **☀️ Normal** | HSV-Farben: dunkelblauer Hintergrund, weiße Schrift, roter Akzent |
| **🌙 Dark** | Dunkles Theme mit lila Akzenten |
| **⚙️ Steampunk** | Braun/Gold in Steampunk-Aesthetik |
| **🌈 Rainbow** | Helles Theme mit pinken/lila Akzenten |
| **🤘 Heavy Metal** | Schwarz/Rot, hochkontrastierend |
| **🖥️ System (OS)** | Folgt der Betriebssystem-Einstellung: hell bei Light-Mode, dunkel bei Dark-Mode |

Die Auswahl wird automatisch im Browser gespeichert (localStorage).

**System (OS):** Nutzt `prefers-color-scheme` des Browsers/Betriebssystems. Aendert sich die Systemeinstellung, passt sich G.R.E.A.T. automatisch an.

### 9.2 Maximale Anzahl Testfaelle

Standardmaessig werden maximal **1000 Testfaelle** pro Generierung erzeugt. Dies verhindert unbeabsichtigte Ressourcen-Explosion bei grossen Testraemen.

**Konfiguration:**
- In den Einstellungen als Karte einsehbar und aenderbar
- Backend: Umgebungsvariable `GREAT_MAX_TESTCASES`
- Ein expliziter `limit`-Parameter in der Generierungsanfrage ueberschreibt diesen Wert

### 9.3 Datensicherung

In den Einstellungen finden Sie die Option zur **Datenbank-Sicherung**. Dies erstellt einen JSON-Export aller Projekte, Kategorien, Werte, Regeln und Testfaelle.

> **Tipp:** Vor dem Zuruecksetzen der Datenbank (s. 2.3) immer eine Sicherung erstellen.

---

## 10. Benutzer & Rollen

### 10.1 Rollen

| Rolle | Berechtigungen |
|-------|---------------|
| **Admin** | Alles: Benutzer verwalten, Projekte anlegen/loeschen, Datenbank resetten |
| **Editor** | Projekte bearbeiten, Kategorien/Werte/Regeln anlegen, generieren, exportieren |
| **Viewer** | Nur lesen: Projekte ansehen, Testfaelle exportieren |

### 10.2 Projekt-Freigabe

Admins und Projektbesitzer koennen Projekte an andere Benutzer freigeben. Der freigegebene Benutzer erhaelt Zugriff entsprechend seiner Rolle.

### 10.3 Benutzer verwalten

Admins koennen ueber die Einstellungen neue Benutzer anlegen, Rollen zuweisen und bestehende Benutzer bearbeiten oder deaktivieren.

---

## 11. Tastaturnavigation & Shortcuts

| Tastenkombination | Aktion |
|------------------|--------|
| **F1** | Hilfe oeffnen/schliessen |
| **F2** | Ausgewaehltes Element umbenennen |
| **Enter** | Bestatigen / Kategorie expandieren |
| **Escape** | Schliessen / Abbrechen |
| **Rechtsklick** | Kontextmenue oeffnen |
| **Tab** | Zwischen Elementen navigieren |
| **Pfeiltasten** | In Tabellen und Baumen navigieren |

---

## 12. Glossar

| Begriff | Definition |
|---------|-----------|
| **Aequivalenzklasse** | Menge von Eingabewerten, die vom System gleich behandelt werden (ISTQB) |
| **All Combinations** | Vollstaendige kartesische Produkt aller Werte |
| **Boundary Value Analysis (BVA)** | Testtechnik, die die Grenzen von Wertebereichen untersucht |
| **Default-Wert** | Standardwert fuer Lineare Expansion; pro Kategorie genau einer |
| **Fehlerwert** | Wert mit `allowed=False`; repraesentiert ungueltige Eingabe |
| **Kategorie** | Testparameter; enthaelt eine Menge moeglicher Werte |
| **Kombinatorisches Testing** | Testtechnik, die systematisch Kombinationen von Eingabeparametern untersucht |
| **Lineare Expansion** | Generierungsstrategie: pro Kategorie ein Testfall, andere auf Default |
| **MC/DC** | Modified Condition/Decision Coverage; Testkriterium fuer Sicherheitskritische Software |
| **Orthogonales Array** | Mathematische Struktur fuer minimale Testsaetze mit Paar-Abdeckung |
| **Pairwise Testing** | Testung aller moeglichen Paare von Werten (T=2) |
| **Risiko-Gewicht** | Wert 1–10 pro Wert; hoeher = risikoreicher |
| **Risk-Based Testing** | Teststrategie, die den Fokus auf hochriskante Bereiche legt |
| **Testfall** | Eine konkrete Kombination von Werten aller Kategorien |
| **T-Wise** | Verallgemeinerung von Pairwise auf T-fache Kombinationen |
| **Wert** | Moegliche Eingabe fuer eine Kategorie |

---

## 13. Haeufige Fragen (FAQ)

**Warum erscheinen bei All Combinations mehr als 1000 Testfaelle nicht?**
Standardmaessig greift ein Limit von 1000 Testfaellen pro Generierung. Aendern Sie dies in den Einstellungen oder uebergeben Sie einen expliziten `limit`-Parameter.

**Warum ist meine Risikoabdeckung nur 30% bei Pairwise?**
Das ist normal. Pairwise testet nur ~30–50% aller moeglichen Kombinationen, deckt aber >95% der paarenweise Fehler ab. Der Prozentsatz bezieht sich auf das All-Combinations-Maximum.

**Wie entferne ich einen Default-Wert?**
Rechtsklick auf den Wert mit ★-Symbol → "✕ Default entfernen".

**Kann ich nach der Generierung noch Werte aendern?**
Nein. Die generierten Testfaelle sind fest. Aendern Sie die Werte vor der Generierung oder legen Sie eine neue Generierung an.

**Was bedeutet das ✕-Symbol bei einem Wert?**
Der Wert ist als Fehlerwert markiert (`allowed=False`). Testfaelle mit diesem Wert werden ans Ende sortiert und im Export als "Fehlerwert: JA" gekennzeichnet.

**Warum erscheinen Ergebnis-Kategorien nicht in generierten Testfaellen?**
Ergebnis-Kategorien (`is_result=True`) sind nicht an der automatischen Generierung beteiligt. Sie dienen der manuellen Eingabe von Erwartungswerten nach der Generierung.

**Wie wechsle ich vom Standardpasswort?**
Nach der Erstanmeldung werden Sie automatisch zur Passwortwechsel-Seite weitergeleitet. Spaeter: Top-Navigation → "Passwort aendern".

---

*Ende des Benutzerhandbuchs*