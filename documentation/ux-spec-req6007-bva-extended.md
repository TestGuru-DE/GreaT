# UX-Befund: REQ-6007 BVA-Dialog erweitern für Datum, Uhrzeit, Stringlänge

---

## Benutzerziel

Als Tester möchte ich im bestehenden BVA-Dialog neben Zahlen auch **Datum**, **Uhrzeit**, **Datum+Uhrzeit** und **Stringlänge** als Datentyp auswählen können. Für jeden Typ sollen typspezifische Grenzwerte und charakteristische Zusatzwerte (Schaltjahr, Mitternacht, Länge 0, ...) automatisch erzeugt werden — alles im vertrauten Multi-Range-Dialog mit Live-Vorschau und Zahlenstrahl.

---

## Primärer Ablauf

```
1. Nutzer öffnet BVA-Dialog (Rechtsklick → "Grenzwertanalyse...")
2. Dialog zeigt neuen Dropdown "Datentyp" (Standard: Zahl)
3. Unten wechselt das Eingabepanel je nach Typ:
   - Zahl      → bestehende BVAInputPanel (unchanged)
   - Datum     → DateInputPanel (Datumsauswahl + Zusatzwerte)
   - Uhrzeit   → TimeInputPanel (HH:MM/HH:MM:SS + Zusatzwerte)
   - Datum+Uhrzeit → DateTimeInputPanel (Kombination beider)
   - Stringlänge → StringLengthInputPanel (Min/Max-Länge + Zeichenvorrat + Zusatzwerte)
4. Nutzer definiert Bereiche (erlaubt/nicht-erlaubt) wie bisher
5. Live-Vorschau und Zahlenstrahl aktualisieren sich sofort
6. "Anwenden" sendet an Backend (bestehender Endpunkt mit neuem `type`-Feld)
```

---

## Datentyp-Auswahl (Dropdown)

### Position
Direkt unter dem Dialogtitel, oberhalb des Input-Panels.

### Design
```
┌─────────────────────────────────────────────────┐
│ Grenzwertanalyse: <categoryName>                │
│ Kategorie: <categoryName>                       │
├─────────────────────────────────────────────────┤
│ Datentyp: [ Zahl ▼ ]                           │
│              [ Zahl | Datum | Uhrzeit           │
│                | Datum+Uhrzeit | Stringlänge ]   │
├─────────────────────────────────────────────────┤
│ [ Typspezifisches InputPanel ]                  │
│ [ Zahlenstrahl / Visualisierung ]               │
│ [ Vorschau-Tabelle ]                            │
├─────────────────────────────────────────────────┤
│                     [Abbrechen]  [Anwenden]     │
└─────────────────────────────────────────────────┘
```

### Verhalten
- **Standardwert:** `number` (Zahl) — abwärtskompatibel
- **onChange:** Setzt `config.dataType` und wechselt das InputPanel
- **Bereiche bleiben erhalten** beim Wechsel — aber Validierung ist typspezifisch
- **Punkte pro Grenze (2/3/4)** bleiben global und gelten für alle Typen

### i18n Keys
```
bvaDialog.dataType.label: "Datentyp"
bvaDialog.dataType.number: "Zahl"
bvaDialog.dataType.date: "Datum"
bvaDialog.dataType.time: "Uhrzeit"
bvaDialog.dataType.datetime: "Datum+Uhrzeit"
bvaDialog.dataType.stringLength: "Stringlänge"
```

---

## 1. Datum (DateInputPanel)

### Eingabefelder pro Bereich

```
┌─ Bereich 1: 01.01.2024 – 31.12.2024 ──────────────┐
│ Minimum:  [📅 01.01.2024]  Maximum: [📅 31.12.2024]│
│ Ausgabeformat: [ ISO JJJJ-MM-TT ▼ ]                │
│                 [ ISO JJJJ-MM-TT | TT.MM.JJJJ ]    │
│                                                    │
│ Zusatzwerte:                                       │
│ ☑ 29.02. Schaltjahr (z.B. 29.02.2024)             │
│ ☑ 29.02. Nicht-Schaltjahr (z.B. 29.02.2023)       │
│ ☑ Monatsenden (30./31.)                            │
│ ☑ Jahreswechsel (31.12./01.01.)                    │
│ ☑ Ungültiges Datum (z.B. 31.04.)                   │
│                                                    │
│ [✓ Erlaubt]                                        │
└────────────────────────────────────────────────────┘
```

### Komponenten-Design

```tsx
interface DateBVAConfig {
  dataType: "date";
  ranges: DateBVARange[];
  pointsPerBoundary: 2 | 3 | 4;
  dateFormat: "iso" | "german";  // JJJJ-MM-TT | TT.MM.JJJJ
}

interface DateBVARange {
  id: string;
  minVal: string;  // "2024-01-01"
  maxVal: string;  // "2024-12-31"
  allowed: boolean;
  extras: {
    leapYear: boolean;       // 29.02. Schaltjahr
    nonLeapYear: boolean;    // 29.02. Nicht-Schaltjahr
    monthEnds: boolean;      // 30./31.
    yearTransition: boolean; // 31.12./01.01.
    invalidDate: boolean;    // 31.04.
  };
}
```

### Eingabe
- **HTML `<input type="date">`** für Min/Max (Browser-native Datumsauswahl)
- **Fallback:** Freitexteingabe `JJJJ-MM-TT` mit Validierung
- **Schrittweite:** Immer **1 Tag** (ISTQB-konform, nicht konfigurierbar)

### Zusatzwerte-Logik
| Checkbox | Wert | Typ | Bedingung |
|----------|------|-----|-----------|
| 29.02. Schaltjahr | `2024-02-29` | boundary | Falls 29.02. im oder direkt am Bereich |
| 29.02. Nicht-Schaltjahr | `2023-02-29` | outside (Fehler) | Immer, falls angekreuzt |
| Monatsenden | `*-30`, `*-31` | boundary | Monatsenden die im Bereich liegen |
| Jahreswechsel | `*-12-31`, `*-01-01` | boundary | Falls Bereich Jahresgrenze berührt |
| Ungültiges Datum | `2024-04-31` | outside (Fehler) | Erster ungültiger Tag im Bereich |

### Validierung
- [ ] Min-Datum muss vor/amgleichen Max-Datum liegen
- [ ] Datum muss gültig sein (kein 31.04., kein 29.02. in Nicht-Schaltjahren)
- [ ] Bereiche dürfen sich nicht überschneiden
- [ ] Ausgabeformat-Wechsel formatiert alle Werte sofort um

### i18n Keys
```
bvaDialog.date.minLabel: "Minimum"
bvaDialog.date.maxLabel: "Maximum"
bvaDialog.date.dateFormat: "Ausgabeformat"
bvaDialog.date.dateFormatIso: "ISO JJJJ-MM-TT"
bvaDialog.date.dateFormatGerman: "TT.MM.JJJJ"
bvaDialog.date.extras: "Zusatzwerte"
bvaDialog.date.extrasLeapYear: "29.02. Schaltjahr"
bvaDialog.date.extrasNonLeapYear: "29.02. Nicht-Schaltjahr"
bvaDialog.date.extrasMonthEnds: "Monatsenden (30./31.)"
bvaDialog.date.extrasYearTransition: "Jahreswechsel (31.12./01.01.)"
bvaDialog.date.extrasInvalidDate: "Ungültiges Datum (z.B. 31.04.)"
bvaDialog.date.errors.minAfterMax: "Minimum darf nicht nach Maximum liegen"
bvaDialog.date.errors.invalidDate: "Ungültiges Datum: {{value}}"
bvaDialog.date.errors.invalidFeb: "29.02. nur in Schaltjahren gültig"
```

---

## 2. Uhrzeit (TimeInputPanel)

### Eingabefelder pro Bereich

```
┌─ Bereich 1: 08:00 – 18:00 ────────────────────────┐
│ Minimum:  [🕐 08:00]  Maximum: [🕐 18:00]         │
│ Format:     [ HH:MM ▼ ]                           │
│               [ HH:MM | HH:MM:SS ]                 │
│ Schrittweite: [ Minute ▼ ]                        │
│               [ Minute | Sekunde ]                  │
│                                                    │
│ Zusatzwerte:                                       │
│ ☑ 00:00 (Mitternacht)                              │
│ ☑ 23:59(:59) (Tagende)                             │
│ ☑ 24:00 (ungültig)                                 │
│ ☑ Mitternachtsübergang                             │
│                                                    │
│ [✓ Erlaubt]                                        │
└────────────────────────────────────────────────────┘
```

### Komponenten-Design

```tsx
interface TimeBVAConfig {
  dataType: "time";
  ranges: TimeBVARange[];
  pointsPerBoundary: 2 | 3 | 4;
  timeFormat: "hhmm" | "hhmmss";
  stepUnit: "minute" | "second";
}

interface TimeBVARange {
  id: string;
  minVal: string;  // "08:00" oder "08:00:00"
  maxVal: string;  // "18:00" oder "18:00:00"
  allowed: boolean;
  extras: {
    midnight: boolean;         // 00:00
    endOfDay: boolean;         // 23:59 oder 23:59:59
    invalid24: boolean;        // 24:00 (ungültig)
    midnightTransition: boolean; // Bereich über Mitternacht
  };
}
```

### Eingabe
- **HTML `<input type="time">`** für Min/Max (Browser-native)
- Bei `HH:MM:SS`-Format: zusätzlicher `:SS`-Input oder `<input type="time" step="1">`
- **Schrittweite:** Minute (Standard) oder Sekunde

### Mitternachtsübergang
- Falls Min > Max (z.B. 22:00–02:00): Bereich wird als **über Mitternacht** interpretiert
- Visueller Hinweis: "Bereich überspringt Mitternacht (22:00 → 02:00)"
- Grenzwerte werden korrekt berechnet: 21:59, 22:00, 02:00, 02:01

### Zusatzwerte-Logik
| Checkbox | Wert (HH:MM) | Wert (HH:MM:SS) | Typ |
|----------|-------------|-----------------|-----|
| 00:00 | `00:00` | `00:00:00` | boundary |
| 23:59 | `23:59` | `23:59:59` | boundary |
| 24:00 | `24:00` | `24:00:00` | outside (Fehler) |
| Mitternachtsübergang | — | — | boundary (nur wenn Min > Max) |

### Validierung
- [ ] Uhrzeit muss gültig sein (00:00–23:59)
- [ ] 24:00 nur als Fehlerwert
- [ ] Bei Mitternachtsübergang: Hinweis, kein Fehler
- [ ] Schrittweite muss zur Formatwahl passen

### i18n Keys
```
bvaDialog.time.minLabel: "Minimum"
bvaDialog.time.maxLabel: "Maximum"
bvaDialog.time.format: "Format"
bvaDialog.time.formatHhmm: "HH:MM"
bvaDialog.time.formatHhmmss: "HH:MM:SS"
bvaDialog.time.stepUnit: "Schrittweite"
bvaDialog.time.stepMinute: "Minute"
bvaDialog.time.stepSecond: "Sekunde"
bvaDialog.time.extras: "Zusatzwerte"
bvaDialog.time.extrasMidnight: "00:00 (Mitternacht)"
bvaDialog.time.extrasEndOfDay: "23:59(:59) (Tagende)"
bvaDialog.time.extrasInvalid24: "24:00 (ungültig)"
bvaDialog.time.extrasMidnightTransition: "Mitternachtsübergang"
bvaDialog.time.midnightCrossing: "Bereich überspringt Mitternacht"
bvaDialog.time.errors.invalidTime: "Ungültige Uhrzeit: {{value}}"
bvaDialog.time.errors.invalid24: "24:00 ist kein gültiger Zeitwert"
```

---

## 3. Datum+Uhrzeit (DateTimeInputPanel)

### Eingabefelder pro Bereich

```
┌─ Bereich 1: 01.01.2024 08:00 – 31.12.2024 18:00 ─┐
│ Minimum:  [📅 01.01.2024] [🕐 08:00]              │
│ Maximum:  [📅 31.12.2024] [🕐 18:00]              │
│ Format:     [ ISO 8601 ▼ ]                        │
│               [ ISO 8601 | ISO+Offset | TT.MM.JJJJ HH:MM ] │
│ Schrittweite: [ Stunde ▼ ]                        │
│               [ Stunde | Minute | Sekunde ]        │
│                                                    │
│ Zusatzwerte (wie Datum + Uhrzeit kombiniert):      │
│ ☑ 29.02. Schaltjahr                                │
│ ☑ Monatsenden                                       │
│ ☑ 00:00 / 23:59 an Bereichsgrenzen                 │
│                                                    │
│ [✓ Erlaubt]                                        │
└────────────────────────────────────────────────────┘
```

### Komponenten-Design

```tsx
interface DateTimeBVAConfig {
  dataType: "datetime";
  ranges: DateTimeBVARange[];
  pointsPerBoundary: 2 | 3 | 4;
  format: "iso8601" | "isoOffset" | "german";
  stepUnit: "hour" | "minute" | "second";
}

interface DateTimeBVARange {
  id: string;
  minDate: string;  // "2024-01-01"
  minTime: string;  // "08:00"
  maxDate: string;  // "2024-12-31"
  maxTime: string;  // "18:00"
  allowed: boolean;
  extras: {
    leapYear: boolean;
    monthEnds: boolean;
    midnightBoundary: boolean;
    endOfDayBoundary: boolean;
  };
}
```

### Verhalten
- **Kombination** von DateInputPanel + TimeInputPanel
- **Schrittweite:** Stunde (Standard), Minute oder Sekunde
- **Format:** ISO 8601 (`2024-01-01T08:00:00`), ISO+Offset (`2024-01-01T08:00:00+01:00`), deutsch (`01.01.2024 08:00`)
- **Zusatzwerte:** Union aus Datum- und Uhrzeit-Zusatzwerten, angewendet auf die Bereichsgrenzen

### i18n Keys
```
bvaDialog.datetime.minDate: "Minimum Datum"
bvaDialog.datetime.minTime: "Minimum Uhrzeit"
bvaDialog.datetime.maxDate: "Maximum Datum"
bvaDialog.datetime.maxTime: "Maximum Uhrzeit"
bvaDialog.datetime.format: "Format"
bvaDialog.datetime.formatIso8601: "ISO 8601 (JJJJ-MM-TTThh:mm:ss)"
bvaDialog.datetime.formatIsoOffset: "ISO 8601 + Offset"
bvaDialog.datetime.formatGerman: "TT.MM.JJJJ hh:mm"
bvaDialog.datetime.stepUnit: "Schrittweite"
bvaDialog.datetime.stepHour: "Stunde"
bvaDialog.datetime.stepMinute: "Minute"
bvaDialog.datetime.stepSecond: "Sekunde"
```

---

## 4. Stringlänge (StringLengthInputPanel)

### Eingabefelder pro Bereich

```
┌─ Bereich 1: Länge 1 – 50 ─────────────────────────┐
│ Minimum:  [ 1 ]  Maximum: [ 50 ]                   │
│                                                    │
│ Zeichenvorrat: [ Buchstaben+Ziffern ▼ ]            │
│               [ Buchstaben                         │
│                 | Buchstaben+Ziffern                │
│                 | + Umlaute/ß                       │
│                 | + Sonderzeichen                   │
│                 | Unicode (Emoji, etc.) ]           │
│                                                    │
│ Zusatzwerte:                                       │
│ ☑ Länge 0 (leer)                                   │
│ ☑ Nur Leerzeichen                                  │
│ ☑ Führende Leerzeichen                             │
│ ☑ Abschließende Leerzeichen                         │
│                                                    │
│ [✓ Erlaubt]                                        │
└────────────────────────────────────────────────────┘
```

### Komponenten-Design

```tsx
interface StringLengthBVAConfig {
  dataType: "stringLength";
  ranges: StringLengthBVARange[];
  pointsPerBoundary: 2 | 3 | 4;
  charset: "alpha" | "alnum" | "alnumUmlaut" | "special" | "unicode";
}

interface StringLengthBVARange {
  id: string;
  minLen: string;   // "1"
  maxLen: string;   // "50"
  allowed: boolean;
  extras: {
    zeroLength: boolean;       // Länge 0
    onlySpaces: boolean;       // Nur Leerzeichen
    leadingSpaces: boolean;    // Führende Leerzeichen
    trailingSpaces: boolean;   // Abschließende Leerzeichen
  };
}
```

### Symbolische Darstellung (REQ-6007)
- Werte > 500 Zeichen: `<STR len=1001 charset=alnum>`
- Werte <= 500 Zeichen: tatsächlicher Text
- Die echte Zeichenkette entsteht beim Export (REQ-6010)

### Zeichenvorrat
| Option | Beispiel | vtype |
|--------|----------|-------|
| Buchstaben | `abcDEF` | alpha |
| Buchstaben+Ziffern | `abc123` | alnum |
| + Umlaute/ß | `äöüÄÖÜß` | alnumUmlaut |
| + Sonderzeichen | `!@#$%` | special |
| Unicode | `😀🎉中文` | unicode |

### Validierung
- [ ] Min-Länge >= 0
- [ ] Min-Länge <= Max-Länge
- [ ] Max-Länge > 0 (falls nicht nur Länge 0)
- [ ] Länge > 500 → symbolischer Wert (Hinweis, kein Fehler)

### i18n Keys
```
bvaDialog.stringLength.minLabel: "Minimum Länge"
bvaDialog.stringLength.maxLabel: "Maximum Länge"
bvaDialog.stringLength.charset: "Zeichenvorrat"
bvaDialog.stringLength.charsetAlpha: "Buchstaben"
bvaDialog.stringLength.charsetAlnum: "Buchstaben+Ziffern"
bvaDialog.stringLength.charsetUmlaut: "+ Umlaute/ß"
bvaDialog.stringLength.charsetSpecial: "+ Sonderzeichen"
bvaDialog.stringLength.charsetUnicode: "Unicode (Emoji, etc.)"
bvaDialog.stringLength.extras: "Zusatzwerte"
bvaDialog.stringLength.extrasZero: "Länge 0 (leer)"
bvaDialog.stringLength.extrasSpaces: "Nur Leerzeichen"
bvaDialog.stringLength.extrasLeading: "Führende Leerzeichen"
bvaDialog.stringLength.extrasTrailing: "Abschließende Leerzeichen"
bvaDialog.stringLength.symbolic: "Symbolisch (>500 Zeichen): <STR len={{len}} charset={{charset}}>"
bvaDialog.stringLength.errors.minNegative: "Länge darf nicht negativ sein"
bvaDialog.stringLength.errors.minGreaterThanMax: "Minimum darf nicht größer als Maximum sein"
```

---

## 5. Validierung (gemeinsam)

### Sofortvalidierung pro Bereich
Jede Änderung an Min/Max/Extras löst sofort Validierung aus:

```
┌─ Bereich 1 ────────────────────────────────────────┐
│ Minimum:  [ abc ]  Maximum: [ 10 ]                 │
│ ⚠️ Ungültiger Wert: "abc" ist keine Zahl           │
└────────────────────────────────────────────────────┘
```

### Validierungsregeln pro Typ

| Regel | Zahl | Datum | Uhrzeit | DateTime | StringLänge |
|-------|------|-------|---------|----------|-------------|
| Min > Max | Auto-Swap | ❌ Fehler | ⚠️ Mitternacht | ❌ Fehler | ❌ Fehler |
| Ungültiger Wert | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler |
| Überlappende Bereiche | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler |
| Leerer Bereich | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler | ❌ Fehler |

### Fehleranzeige
- **Pro-Bereich:** Roter Text unter dem betroffenen Feld
- **Global:** Rote Box oberhalb der Vorschau (wie bisher)
- **Anwenden-Button:** Disabled solange Validierungsfehler existieren

### i18n Keys
```
bvaDialog.errors.minGreaterThanMax: "Minimum darf nicht größer als Maximum sein"
bvaDialog.errors.overlappingRanges: "Bereiche dürfen sich nicht überschneiden oder berühren"
bvaDialog.errors.emptyRange: "Minimum oder Maximum erforderlich"
bvaDialog.errors.invalidValue: "Ungültiger Wert: {{value}}"
bvaDialog.errors.noRanges: "Mindestens ein Bereich erforderlich"
```

---

## Tastatur / Shortcut

| Shortcut | Aktion |
|----------|--------|
| `Escape` | Dialog schließen (bestehend) |
| `Enter` | Anwenden (wenn valide) (bestehend) |
| `Tab` | Durch Felder navigieren (bestehend) |
| `Alt+T` | Datentyp-Dropdown fokussieren (neu) |
| `Alt+E` | Zusatzwerte-Gruppe fokussieren (neu) |

---

## Accessibility

- **Datentyp-Dropdown:** `<select>` mit `aria-label="Datentyp"`
- **Alle Inputs:** `<label>` mit `for`-Attribut, `aria-required="true"` wo nötig
- **Zusatzwerte-Checkboxes:** `<label>` direkt nach `<input>`
- **Fehlermeldungen:** `role="alert"`, `aria-live="polite"`
- **Zahlenstrahl:** `role="img"`, `aria-label="Zahlenstrahl mit {{count}} Punkten"`
- **Farben:** Fehler rot (#ef4444), Grenzwert blau (#0ea5e9), Innen gelb (#f59e0b) — bestehen, barrierearm durch Symbole ergänzt
- **Kontrast:** Alle Texte WCAG AA (4.5:1)

---

## Akzeptanzkriterien (Given/When/Then)

### AC-1: Datentyp-Auswahl
```
GIVEN  BVA-Dialog ist geöffnet
WHEN   Nutzer wählt "Datum" im Datentyp-Dropdown
THEN   InputPanel wechselt zu DateInputPanel
AND    Datumsauswähler (input[type=date]) erscheint für Min/Max
AND    Zusatzwerte-Checkboxes für Datum erscheinen
AND    Punkte-Auswahl (2/3/4) bleibt sichtbar
```

### AC-2: Datum – Min/Max-Eingabe
```
GIVEN  Datentyp "Datum" ist ausgewählt
WHEN   Nutzer wählt Min=01.01.2024, Max=31.12.2024
THEN   Vorschau zeigt BVA-Punkte (z.B. 31.12.2023, 01.01.2024, 31.12.2024, 01.01.2025)
AND    Zahlenstrahl zeigt Datums-Achse
AND    Ausgabeformat wird angewendet (ISO oder TT.MM.JJJJ)
```

### AC-3: Datum – Zusatzwerte
```
GIVEN  Bereich 01.01.2024–31.12.2024, "29.02. Schaltjahr" angekreuzt
WHEN   Vorschau wird berechnet
THEN   29.02.2024 erscheint als Grenzwert in der Vorschau
AND    29.02.2024 ist als "boundary" markiert
```

### AC-4: Datum – Ungültige Eingabe
```
GIVEN  Datentyp "Datum" ist ausgewählt
WHEN   Nutzer gibt Min=31.04.2024 ein
THEN   Fehlermeldung "Ungültiges Datum: 31.04.2024" erscheint
AND    Anwenden-Button ist disabled
```

### AC-5: Datum – Min > Max
```
GIVEN  Datentyp "Datum" ist ausgewählt
WHEN   Nutzer gibt Min=31.12.2024, Max=01.01.2024
THEN   Fehlermeldung "Minimum darf nicht nach Maximum liegen" erscheint
AND    Anwenden-Button ist disabled
```

### AC-6: Uhrzeit – Mitternachtsübergang
```
GIVEN  Datentyp "Uhrzeit" ist ausgewählt
WHEN   Nutzer gibt Min=22:00, Max=02:00 (Min > Max)
THEN   Hinweis "Bereich überspringt Mitternacht" erscheint
AND    Vorschau berechnet korrekte Grenzwerte (21:59, 22:00, 02:00, 03:01)
AND    Kein Validierungsfehler
```

### AC-7: Uhrzeit – Zusatzwerte
```
GIVEN  Bereich 08:00–18:00, "00:00" und "23:59" angekreuzt
WHEN   Vorschau wird berechnet
THEN   00:00 und 23:59 erscheinen als zusätzliche Werte
AND    24:00 (falls angekreuzt) erscheint als Fehlerwert
```

### AC-8: Stringlänge – Symbolische Werte
```
GIVEN  Bereich Länge 1–1000, Zeichenvorrat "Buchstaben+Ziffern"
WHEN   Vorschau wird berechnet
THEN   Werte <= 500 Zeichen erscheinen als tatsächlicher Text
AND    Werte > 500 Zeichen erscheinen als "<STR len=... charset=...>"
AND    Vorschau-Tabelle zeigt symbolische Darstellung
```

### AC-9: Stringlänge – Zeichenvorrat
```
GIVEN  Zeichenvorrat "Unicode" gewählt
WHEN   Vorschau wird berechnet
THEN   Generierte Werte enthalten Unicode-Zeichen (Emoji, etc.)
AND    Längenzählung basiert auf Codepoints, nicht Bytes
```

### AC-10: Überlappende Bereiche
```
GIVEN  Zwei Bereiche: 01.01.2024–06.06.2024 und 01.06.2024–31.12.2024
WHEN   Vorschau wird berechnet
THEN   Fehlermeldung "Bereiche dürfen sich nicht überschneiden" erscheint
AND    Anwenden-Button ist disabled
```

### AC-11: API-Abwärtskompatibilität
```
GIVEN  Datentyp "Zahl" (Standard)
WHEN   Nutzer klickt "Anwenden"
THEN   API-Request enthält type="number" (oder kein type-Feld)
AND    Verhalten ist identisch zum bisherigen BVA-Dialog
```

### AC-12: i18n
```
GIVEN  Sprache ist Deutsch/Englisch
WHEN   BVA-Dialog mit neuem Datentyp geöffnet
THEN   Alle Labels, Fehlermeldungen, Zusatzwerte sind übersetzt
AND   Kein harter Text in Komponenten
```

---

## Risiken / Barrieren

### R1: Backend-Abhängigkeit
**Risiko:** REQ-6007 spezifiziert API-Erweiterung (`type`-Feld, typspezifische Optionen). Diese Aufgabe ist **nur Frontend** — das Backend muss parallel/ zuvor implementiert sein.
**Minderung:** Frontend sendet `type`-Feld im Request; falls Backend es nicht unterstützt, wird ein klarer Fehler gemeldet. Frontend-Validierung läuft lokal.

### R2: Datumsvalidierung im Browser
**Risiko:** `<input type="date">` unterstützt kein TT.MM.JJJJ-Format nativ.
**Minderung:** Input ist immer ISO `JJJJ-MM-TT` intern; Ausgabeformat betrifft nur die Darstellung in Vorschau/Export. Nutzer gibt immer ISO ein, sieht aber formatierte Werte.

### R3: Mitternachtsübergang-Validierung
**Risiko:** Min > Max bei Uhrzeit ist valide (Mitternacht) vs. bei Datum/DateTime invalide.
**Minderung:** Typspezifische Validierungsfunktionen; Uhrzeit behandelt Min > Max als Mitternachtsübergang, Datum/DateTime als Fehler.

### R4: Symbolische String-Werte
**Risiko:** Lange Strings (>500) müssen symbolisch dargestellt werden; Vorschau-Tabelle muss `<STR len=...>` rendern.
**Minderung:** Neue Helper-Funktion `formatStringValue(value, charset)` in `bva-calc.ts`; PreviewTable rendert symbolische Werte mit eigenem Style.

### R5: Zahlenstrahl-Visualisierung
**Risiko:** Datum/Uhrzeit/Stringlänge auf einem Zahlenstrahl darstellen erfordert neue Visualisierungslogik.
**Minderung:** `NumberlineVisualization` wird erweitert:
- Datum: X-Achse als Zeitachse (Tage seit Epoch)
- Uhrzeit: X-Achse als Minuten seit Mitternacht
- Stringlänge: X-Achse als numerische Länge (wie bisher)
- Zahl: wie bisher

### R6: Testabdeckung
**Risiko:** 5 Datentypen × 2/3/4 Punkte × Extras = viele Kombinationen.
**Minderung:** Jeder Datentyp bekommt eigene Testdatei; Grenzfälle explizit (Schaltjahr 2024/2100/2000, Mitternacht, Länge 0, Länge > 500).

---

## Komponenten-Übersicht

```
components/bva/
├── BVADialog.tsx           ← ERWEITERN: Datentyp-Dropdown, type-aware state
├── BVAInputPanel.tsx       ← ERWEITERN: Router zu typspezifischen Panels
├── DateInputPanel.tsx      ← NEU: Datumseingabe + Extras
├── TimeInputPanel.tsx      ← NEU: Zeiteingabe + Extras
├── DateTimeInputPanel.tsx  ← NEU: Kombination Datum+Uhrzeit
├── StringLengthInputPanel.tsx ← NEU: Längeneingabe + Zeichenvorrat + Extras
├── NumberlineVisualization.tsx ← ERWEITERN: Datum/Uhrzeit/Länge-Achsen
├── PreviewTable.tsx        ← ERWEITERN: symbolische String-Werte, Datums-Format
├── __tests__/
│   ├── BVADialog.test.tsx       ← ERWEITERN: Datentyp-Wechsel
│   ├── BVAInputPanel.test.tsx   ← ERWEITERN: Router-Tests
│   ├── DateInputPanel.test.tsx  ← NEU
│   ├── TimeInputPanel.test.tsx  ← NEU
│   ├── DateTimeInputPanel.test.tsx ← NEU
│   ├── StringLengthInputPanel.test.tsx ← NEU
│   ├── NumberlineVisualization.test.tsx ← ERWEITERN
│   └── PreviewTable.test.tsx    ← ERWEITERN
└── (bva-calc.ts bleibt in lib/, wird um typspezifische Funktionen erweitert)
```

## lib/bva-calc.ts Erweiterungen

```
lib/bva-calc.ts
├── BVAConfig → union type mit dataType
├── calculateDateBVAPoints(config: DateBVAConfig) → BVAPoint[]
├── calculateTimeBVAPoints(config: TimeBVAConfig) → BVAPoint[]
├── calculateDateTimeBVAPoints(config: DateTimeBVAConfig) → BVAPoint[]
├── calculateStringLengthBVAPoints(config: StringLengthBVAConfig) → BVAPoint[]
├── validateDateConfig(ranges: DateBVARange[]) → string[]
├── validateTimeConfig(ranges: TimeBVARange[]) → string[]
├── validateDateTimeConfig(ranges: DateTimeBVARange[]) → string[]
├── validateStringLengthConfig(ranges: StringLengthBVARange[]) → string[]
├── formatStringValue(value: string, charset: string, maxLength: number) → string
├── isLeapYear(year: number) → boolean
├── isDateInRange(date: string, min: string, max: string) → boolean
└── isTimeAcrossMidnight(min: string, max: string) → boolean
```

## api/bva.ts Erweiterungen

```
api/bva.ts
├── BVARequest → type?: "number" | "date" | "time" | "datetime" | "stringLength"
├── BVARangeRequest → extras?: {...} (typspezifisch)
├── BVAMultiRangeRequest → type?: string, dateFormat?: string, ...
└── generateMultiRange → fügt type + typspezifische Felder hinzu
```

---

## Implementierungsreihenfolge (für Senior Developer)

1. **Types & Interfaces** in `bva-calc.ts` — alle neuen Typen definieren
2. **Helper-Funktionen** — `isLeapYear`, `isTimeAcrossMidnight`, `formatStringValue`
3. **Validierung** — `validateDateConfig`, `validateTimeConfig`, etc.
4. **Berechnung** — `calculateDateBVAPoints`, etc. (mit Tests!)
5. **InputPanels** — `DateInputPanel`, `TimeInputPanel`, etc.
6. **BVADialog** — Datentyp-Dropdown + Router zu Panels
7. **BVAInputPanel** — Router-Logik (bestehende Zahl-Logik bleibt Default)
8. **NumberlineVisualization** — typspezifische Achsen
9. **PreviewTable** — symbolische Strings, Datums-Format
10. **API** — `type`-Feld + Extras in Request
11. **i18n** — alle neuen Keys in `de.json` + `en.json`
12. **Tests** — je Typ eine Testdatei, Grenzfälle explizit

---

## i18n-Keys (vollständige Liste)

Siehe oben pro Sektion. Zusammenfassung aller neuen Keys:

**Allgemein:**
- `bvaDialog.dataType.label`, `.number`, `.date`, `.time`, `.datetime`, `.stringLength`

**Datum:**
- `bvaDialog.date.*` (15 Keys)

**Uhrzeit:**
- `bvaDialog.time.*` (14 Keys)

**Datum+Uhrzeit:**
- `bvaDialog.datetime.*` (10 Keys)

**Stringlänge:**
- `bvaDialog.stringLength.*` (15 Keys)

**Validierung:**
- `bvaDialog.errors.*` (5 Keys)

**Gesamt: ~60 neue i18n-Keys** (DE + EN = ~120 Textzeilen)