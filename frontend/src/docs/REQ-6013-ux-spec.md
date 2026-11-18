# UX-Befund: REQ-6013 Frontend-Integration (Export-Menü + Import-Dialog)

## Nutzerziel
Als Tester moechte ich das Testmodell eines Projekts als YAML- oder JSON-Datei exportieren, damit ich es im Git speichern, per PR pruefen oder zwischen G.R.E.A.T.-Instanzen uebertragen kann. Umgekehrt moechte ich ein Modell aus einer Datei importieren — entweder als neues Projekt oder als Aktualisierung eines bestehenden Projekts mit Aenderungsvorschau.

## Interaktionsvorschlag

### 1. Export-Menü im Projekt-Header
**Position:** Rechts neben dem "Umbenennen"-Button im Header der Projektdetailseite (`ProjectDetailPage.tsx`).

**Interaktion:**
- Button "Modell exportieren" (Icon: Download) mit Dropdown-Pfeil
- Klick oeffnet Dropdown mit zwei Optionen:
  - "Als YAML exportieren" (Standard, markiert)
  - "Als JSON exportieren"
- Klick auf eine Option loest sofort den Download aus
- Dateiname: `<projektname>.great.yaml` oder `<projektname>.great.json`
- Ladezustand waehrend des Downloads (Spinner am Button)

**Tastatur:**
- Kein globaler Shortcut (Export ist keine haeufige Aktion)
- Dropdown per Tab/Enter/Escape bedienbar

### 2. Import-Dialog
**Oeffnen:** Button "Modell importieren" im Projekt-Header (neben Export) ODER auf der Projekte-Liste als globaler Import-Button.

**Dialog-Struktur:**
```
┌─────────────────────────────────────────────────┐
│  Modell importieren                          [X] │
├─────────────────────────────────────────────────┤
│                                                 │
│  Datei auswaehlen:                              │
│  ┌───────────────────────────────────────────┐  │
│  │  [ Drag & DropBereich / Dateiauswahl ]    │  │
│  │  .yaml oder .json (max. 5 MB)             │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  Import-Modus:                                  │
│  ○ Neues Projekt erstellen                      │
│  ● Bestehendes Projekt aktualisieren            │
│                                                 │
│  Projekt (bei Aktualisierung):                  │
│  [ Dropdown: Projekt auswaehlen        ▼ ]      │
│                                                 │
│  ── Aenderungsvorschau (bei Aktualisierung) ──  │
│  + 3 Kategorien hinzugefuegt                    │
│  ~ 2 Kategorien geaendert                       │
│  - 1 Kategorie entfernt                         │
│  + 5 Werte hinzugefuegt                         │
│  ~ 1 Wert geaendert                             │
│  - 2 Werte entfernt                             │
│  + 1 Regel hinzugefuegt                         │
│  ~ 0 Regeln geaendert                           │
│  - 1 Regel entfernt                             │
│                                                 │
│  ⚠️ Bei Aktualisierung werden bestehende        │
│     Daten teilweise ersetzt. Generierungen       │
│     bleiben unveraendert.                        │
│                                                 │
│  [ Import abbrechen ]  [ Modell importieren ]   │
└─────────────────────────────────────────────────┘
```

**Ablauf:**
1. Datei wird ausgewaehlt (Drag & Drop oder Dateidialog)
2. Dateiname wird angezeigt, Format (YAML/JSON) erkannt
3. Import-Modus wird ausgewaehlt (Radio-Buttons)
4. Bei "Bestehendes Projekt aktualisieren":
   - Projekt-Dropdown wird aktiv
   - Nach Aenderung der Datei oder des Projekts wird automatisch die Aenderungsvorschau geladen
   - Aenderungsvorschau zeigt +/-~ pro Kategorie/Wert/Regel
5. Button "Modell importieren" ist deaktiviert, bis Datei + Modus gueltig
6. Nach Klick: Ladeanimation, dann Erfolgsmeldung oder Fehler

**Fehlerfaelle:**
- Ungueltiges Format: Fehlermeldung unter Dateibereich
- Datei zu gross (>5 MB): Fehlermeldung
- Schema-Fehler: Liste der Fehler mit Pfad (z.B. `categories[2].values[5].risk_weight`)
- Import fehlgeschlagen: Fehlermeldung mit Retry-Option

**Accessibility:**
- Alle Labels aria-beschriftet
- Drag & Drop hat alternativen Dateidialog-Button
- Aenderungsvorschau als Liste mit Semantik
- Fokusmanagement im Dialog (Escape schliesst, Tab bleibt im Dialog)

## Akzeptanzkriterien

### Export
- **AK-1:** Export-Button ist im Projekt-Header sichtbar (Editor/Admin)
- **AK-2:** Dropdown zeigt "YAML" und "JSON" als Optionen
- **AK-3:** Klick auf YAML loest Download der Datei `<name>.great.yaml` aus
- **AK-4:** Klick auf JSON loest Download der Datei `<name>.great.json` aus
- **AK-5:** Waehrend des Downloads zeigt Button Ladezustand
- **AK-6:** Fehler beim Export (404, 500) wird als Toast angezeigt

### Import
- **AK-7:** Import-Dialog oeffnet sich mit Dateiauswahl
- **AK-8:** Drag & Drop und Dateidialog funktionieren
- **AK-9:** Nur .yaml und .json Dateien werden akzeptiert
- **AK-10:** Dateigroesse wird auf 5 MB begrenzt
- **AK-11:** Zwei Import-Modi sind waehlbar (Radio-Buttons)
- **AK-12:** Bei "Neues Projekt": Button ist direkt aktiv nach Dateiauswahl
- **AK-13:** Bei "Aktualisierung": Projekt-Dropdown erscheint
- **AK-14:** Aenderungsvorschau wird nach Datei+Projekt geladen
- **AK-15:** Aenderungsvorschau zeigt hinzugefuegt/geaendert/entfernt farbig
- **AK-16:** Warnhinweis bei Aktualisierung ist sichtbar
- **AK-17:** Nach erfolgreichem Import: Toast + Navigation zum Projekt
- **AK-18:** Fehlermeldungen sind spezifisch und auf Deutsch/Englisch

### i18n
- **AK-19:** Alle Texte in de.json und en.json vorhanden
- **AK-20:** i18n-keys.test.ts erkennt neue Keys

## Risiken/Barrieren
- **Dateiparsing im Browser:** YAML-Parsing benoetigt eine Bibliothek (js-yaml). Diese muss als Dependency hinzugefuegt werden.
- **Groesse:** 5 MB Limit muss clientseitig und serverseitig enforced werden.
- **Konflikte:** Bei "Neues Projekt" mit bestehendem Namen muss Suffix-Logik im Backend laufen (bereits implementiert).
- **State-Management:** Der Import-Dialog muss viel lokalen State verwalten (Datei, Modus, Projekt, Diff, Loading, Fehler).

## Komponenten-Struktur
```
components/
  ModelExportDropdown.tsx       # Export-Dropdown im Header
  ModelImportDialog.tsx         # Import-Dialog (Modal)
  ModelDiffPreview.tsx          # Aenderungsvorschau-Komponente
api/
  modelApi.ts                   # API-Client fuer REQ-6013
```

## i18n-Schlüssel
```
modelExport:
  button: "Modell exportieren" / "Export model"
  yaml: "Als YAML exportieren" / "Export as YAML"
  json: "Als JSON exportieren" / "Export as JSON"
  loading: "Exportiert..." / "Exporting..."
  error: "Export fehlgeschlagen: {{error}}" / "Export failed: {{error}}"
  success: "Modell exportiert" / "Model exported"

modelImport:
  title: "Modell importieren" / "Import model"
  button: "Modell importieren" / "Import model"
  fileSelect: "Datei auswaehlen" / "Select file"
  dragDrop: "Datei hierher ziehen oder klicken" / "Drag file here or click to select"
  acceptedFormats: ".yaml oder .json (max. 5 MB)" / ".yaml or .json (max. 5 MB)"
  modeNew: "Neues Projekt erstellen" / "Create new project"
  modeUpdate: "Bestehendes Projekt aktualisieren" / "Update existing project"
  projectSelect: "Projekt auswaehlen" / "Select project"
  previewTitle: "Aenderungsvorschau" / "Change preview"
  previewLoading: "Aenderungsvorschau wird geladen..." / "Loading change preview..."
  added: "hinzugefuegt" / "added"
  modified: "geaendert" / "modified"
  removed: "entfernt" / "removed"
  categories: "Kategorien" / "categories"
  values: "Werte" / "values"
  rules: "Regeln" / "rules"
  warning: "Bei Aktualisierung werden bestehende Daten teilweise ersetzt. Generierungen bleiben unveraendert." / "Updating will partially replace existing data. Generations remain unchanged."
  confirm: "Modell importieren" / "Import model"
  confirmLoading: "Importiert..." / "Importing..."
  cancel: "Abbrechen" / "Cancel"
  errorFileTooLarge: "Datei zu gross. Maximum: 5 MB." / "File too large. Maximum: 5 MB."
  errorInvalidFormat: "Ungültiges Dateiformat. Nur .yaml oder .json." / "Invalid file format. Only .yaml or .json."
  errorImport: "Import fehlgeschlagen: {{error}}" / "Import failed: {{error}}"
  errorValidation: "Validierungsfehler: {{errors}}" / "Validation errors: {{errors}}"
  errorPreview: "Aenderungsvorschau fehlgeschlagen: {{error}}" / "Preview failed: {{error}}"
  successNew: "Projekt \"{{name}}\" erstellt." / "Project \"{{name}}\" created."
  successUpdate: "Projekt \"{{name}}\" aktualisiert." / "Project \"{{name}}\" updated."
```