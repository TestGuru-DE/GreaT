# REQ-6006: Klassifikationsbaum-Ansicht — UX-Spezifikation

> **Status:** Entwurf · **Autor:** UX Lead · **Phase:** 5, Release v1.11.0
> **Abhaengigkeiten:** REQ-3016, REQ-3053, REQ-6005; optional REQ-6009, REQ-6016

---

## 1. UX-Spezifikation

### 1.1 Benutzerziel

Als Tester, der mit der Klassifikationsbaummethode arbeitet, moechte ich mein Testmodell als Baum
(Testobjekt → Klassifikationen → Klassen) mit der Testfallmatrix darunter sehen,
damit ich das Modell in der gewohnten Notation pruefen, im Team besprechen und in Dokumentationen verwenden kann.

### 1.2 Primärer Ablauf

```
Projekt oeffnen → Tab "Klassifikationsbaum" klicken
  → Baum rendert: Wurzel (Projektname) → Kategorien (Rechtecke) → Werte (Blatter)
  → Generierung per Dropdown waehlen
  → Matrix unter dem Baum erscheint: Zeilen = Testfaelle, Spalten = Klassen, ● = Zuordnung
  → Export SVG/PNG per Button
```

### 1.3 Sekundaer Ablauf: Bearbeiten

```
Kategorie/Klasse waehlen (Klick)
  → Hinzufuegen: "+"-Button oder Kontextmenü
  → Umbenennen: Doppelklick oder F2 → Inline-Input → Enter/Blur = speichern, Escape = abbrechen
  → Loeschen: Entf-Taste → Bestätigungs-Dialog → API-Call → Store-Update
  → Reihenfolge: Drag & Drop → API reorder → Store-Update
  → Alle Aenderungen: sofort im Baum + Undo/Redo (REQ-3053)
```

### 1.4 Sekundaer Ablauf: Manuelle Testfaelle

```
Matrix: "Neuer manueller Testfall"-Button → neue Zeile am Ende
  → Klick auf Zelle in Klassifikation-Spalte → Dropdown/Wahl der Klasse
  → Regelverstoess sofort als roter Rahmen + Tooltip markiert (REQ-6001)
  → "Speichern" → Generierung vom Typ "manual" (REQ-3016) oder Seed-Satz (REQ-6009)
```

### 1.5 Tastatur / Shortcuts

| Shortcut | Aktion | Scope |
|----------|--------|-------|
| `F2` | Umbenennen (gewaehlte Kategorie/Klasse) | Baum |
| `Enter` | Bestaetigen (Inline-Edit) | Baum |
| `Escape` | Abbrechen (Inline-Edit, Dialog) | Baum |
| `Delete` | Loeschen (mit Rueckfrage) | Baum |
| `Pfeil hoch/runter` | Navigation Kategorien | Baum |
| `Pfeil links/rechts` | Navigation Werte (in geoeffneter Kategorie) | Baum |
| `Tab` | Zwischen Baum und Matrix wechseln | Gesamt |
| `Strg+Mausrad` | Zoom ein/aus | Gesamt |
| `+` / `-` | Zoom ein/aus (Buttons) | Toolbar |
| `0` | Zoom einpassen (Button) | Toolbar |
| `Strg+E` | Export SVG | Toolbar |
| `Strc+P` | Export PNG | Toolbar |
| `Strg+Z` / `Strg+Y` | Undo / Redo (REQ-3053) | Gesamt |

### 1.6 Maus / Drag & Drop

- **Drag & Drop** zum Aendern der Reihenfolge von Kategorien und Werten
- **Doppelklick** zum Umbenennen
- **Rechtsklick** → Kontextmenü (Hinzufuegen, Umbenennen, Loeschen, Typ aendern, BVA)
- **Klick** auf Zelle in Matrix → Klasse waehlen (Dropdown)
- **Strg+Mausrad** → Zoom (nur wenn Fokus im Baum/Matrix-Bereich)

### 1.7 Fehlerfaelle

| Situation | Verhalten |
|-----------|-----------|
| Keine Kategorien | Hinweis: "Keine Klassifikationen vorhanden. Fuege in der Kategorien-Ansicht welche hinzu." |
| Keine Werte in Kategorie | Blatt zeigt "— keine Klassen —" als Platzhalter |
| API-Fehler beim Bearbeiten | Toast-Fehlermeldung + Rueckgängig machen (Undo) |
| Loeschen mit aktiver Referenz (Regeln/Testfaelle) | Bestätigungs-Dialog mit Warnung: "Diese Klasse wird in X Regeln und Y Testfaellen verwendet." |
| Zoom > 500% oder < 10% | Soft-Limit: Zoom-Buttons deaktivieren, Tooltip "Maximaler/Minimaler Zoom erreicht" |
| Matrix zu breit fuer Viewport | Waagerechtes Scrollen + Sticky-erste-Spalte (Testfall-Nr.) |

### 1.8 Accessibility

| Kriterium | Umsetzung |
|-----------|-----------|
| Kontrast >= 4.5:1 | Theme-Tokens (`--theme-text`, `--theme-surface`); keine reinen Farbcodes |
| Screenreader | `role="tree"`, `role="treeitem"`, `role="grid"`, `role="row"`, `role="gridcell"` |
| Tastaturbedienung | Alle Aktionen per Keyboard moeglich (siehe Shortcuts) |
| ARIA-Labels | `aria-label` auf allen interaktiven Elementen; `aria-expanded` auf Kategorien |
| Fokus-Indikator | Sichtbarer Ring (`ring-2 ring-theme-primary`) auf fokussiertem Element |
| Live-Region | `aria-live="polite"` fuer Toast-Meldungen nach Aenderungen |

### 1.9 Akzeptanzkriterien (Given/When/Then)

```
AK-1: Tab "Klassifikationsbaum"
  Given ich bin in der Projektansicht
  When ich den Tab "Klassifikationsbaum" klicke
  Then sehe ich den Baum mit Wurzel, Kategorien und Werten

AK-2: Baumstruktur
  Given das Projekt hat Kategorien und Werte
  When der Baum rendert
  Then zeigt er Wurzel (Projektname) → Kategorien (Rechtecke) → Werte (Blatter)

AK-3: Markierung Ergebnis-Kategorien
  Given eine Kategorie ist als Ergebnis markiert (is_result=true)
  When der Baum rendert
  Then zeigt er ein Symbol (z.B. "E") UND die Beschriftung "Ergebnis"

AK-4: Markierung Fehlerwerte
  Given ein Wert ist als Fehlerwert markiert (allowed=false)
  When der Baum rendert
  Then zeigt er ein Symbol (z.B. "✕") UND die Beschriftung "Fehlerwert"

AK-5: Markierung Default-Werte
  Given ein Wert ist als Default markiert (is_default=true)
  When der Baum rendert
  Then zeigt er ein Symbol (z.B. "★") UND die Beschriftung "Standard"

AK-6: Testfallmatrix
  Given eine Generierung ist ausgewaehlt
  When die Matrix rendert
  Then zeigt sie eine Zeile pro Testfall mit ● in der Spalte der gewaehlten Klasse

AK-7: Bearbeiten (Hinzufuegen)
  Given ich bin im Klassifikationsbaum
  When ich "+" klicke oder "Hinzufuegen" im Kontextmenü waehle
  Then erscheint ein neuer Eintrag, der sofort per API gespeichert wird

AK-8: Bearbeiten (Umbenennen)
  Given eine Kategorie/Klasse ist gewaehlt
  When ich F2 drücke oder doppelklicke
  Then erscheint ein Inline-Input; nach Enter wird der neue Name gespeichert

AK-9: Bearbeiten (Loeschen)
  Given eine Kategorie/Klasse ist gewaehlt
  When ich Entf drücke
  Then erscheint eine Rueckfrage; nach Bestaetigung wird der Eintrag geloescht

AK-10: Bearbeiten (Reihenfolge)
  Given zwei Kategorien/Werte sind im Baum
  When ich eine per Drag & Drop ueber die andere ziehe
  Then wird die Reihenfolge geaendert und per API gespeichert

AK-11: Manuelle Testfaelle
  Given ich klicke "Neuer manueller Testfall"
  Then erscheint eine neue Zeile in der Matrix; Klick auf Zelle waehlt Klasse

AK-12: Zoom
  Given ich drücke Strg+Mausrad oder +/-/Einpassen
  Then zoomt die Ansicht; bei 30x20 bleibt sie fluessig (<200ms)

AK-13: Export
  Given ich klicke "Export SVG" oder "Export PNG"
  Then wird der Baum (optional mit Matrix) als Datei heruntergeladen

AK-14: Themes
  Given ich wechsle das Theme (Light/Dark)
  Then bleibt der Baum lesbar mit Kontrast >= 4.5:1

AK-15: Performance
  Given 30 Klassifikationen x 20 Klassen
  When ich interagiere (Scrollen, Zoom, Bearbeiten)
  Then reagiert die Ansicht in < 200ms
```

---

## 2. Komponenten-Design

### 2.1 Dateistruktur

```
frontend/src/
  components/
    classification-tree/
      ClassificationTreeTab.tsx       # Hauptkomponente (Tab-Inhalt)
      ClassificationTreeView.tsx      # SVG-Baum-Rendering
      ClassificationTreeMatrix.tsx    # Testfallmatrix unter dem Baum
      ClassificationTreeNode.tsx      # Einzelner Baumknoten (Kategorie/Wert)
      ClassificationTreeToolbar.tsx   # Zoom + Export Buttons
      ClassificationTreeContextMenu.tsx # Kontextmenü (wiederverwendbar aus ContextMenu)
      ManualTestCaseEditor.tsx        # Editor fuer manuelle Testfaelle
  lib/
    classificationTreeLayout.ts       # Layout-Berechnung (Positionen, Breiten)
    classificationTreeSvg.ts          # SVG-Element-Hilfen
  __tests__/
    classificationTreeLayout.test.ts  # Layout-Tests (30x20, keine Ueberlappung)
    ClassificationTreeView.test.tsx   # Rendering-Tests
    ClassificationTreeMatrix.test.tsx # Matrix-Zuordnung-Tests
```

### 2.2 ClassificationTreeTab.tsx

**Rolle:** Hauptkomponente des neuen Tabs. Koordiniert Baum, Matrix, Toolbar und Daten.

```typescript
interface Props {
  projectId: number;
  projectName: string;
}

export default function ClassificationTreeTab({ projectId, projectName }: Props) {
  // State:
  // - categories + values (aus categoryStore oder direkter API)
  // - generations (Liste, fuer Dropdown)
  // - selectedGenerationId (aktive Generierung fuer Matrix)
  // - zoomLevel (1.0 default, 0.1 - 5.0)
  // - isEditing (inline-edit state)
  // - manualTestCases (Array fuer manuelle Testfaelle)

  return (
    <div className="flex flex-col h-full">
      <ClassificationTreeToolbar
        zoomLevel={zoomLevel}
        onZoomIn={...}
        onZoomOut={...}
        onFit={...}
        onExportSvg={...}
        onExportPng={...}
        generations={generations}
        selectedGenerationId={selectedGenerationId}
        onSelectGeneration={...}
        onAddManualTestCase={...}
      />
      <div className="flex-1 overflow-auto" style={{ minHeight: 0 }}>
        <ClassificationTreeView
          projectName={projectName}
          categories={categories}
          values={values}
          zoomLevel={zoomLevel}
          onNodeClick={...}
          onNodeEdit={...}
          onNodeDelete={...}
          onDragStart={...}
          onDrop={...}
          onContextMenu={...}
        />
        <ClassificationTreeMatrix
          categories={categories}
          values={values}
          testcases={testcases}
          zoomLevel={zoomLevel}
          manualTestCases={manualTestCases}
          onCellClick={...}
          onManualSave={...}
        />
      </div>
    </div>
  );
}
```

### 2.3 ClassificationTreeView.tsx

**Rolle:** SVG-basierter Baum. Reines Rendering + Interaktion (Klick, Drag, Edit).

```typescript
interface Props {
  projectName: string;
  categories: Category[];
  values: Record<number, Value[]>;
  zoomLevel: number;
  selectedNodeId: string | null;  // "cat-{id}" oder "val-{id}"
  onNodeClick: (nodeId: string) => void;
  onNodeEdit: (nodeId: string, newName: string) => Promise<void>;
  onNodeDelete: (nodeId: string) => Promise<void>;
  onDragStart: (nodeId: string) => void;
  onDrop: (fromId: string, toId: string) => Promise<void>;
  onContextMenu: (e: MouseEvent, nodeId: string) => void;
}
```

**Interne Struktur:**
- `useMemo` fuer Layout-Berechnung (`classificationTreeLayout.ts`)
- SVG-Rendering mit `<g transform="scale(zoom)">`
- Jeder Knoten: `<g class="tree-node" data-node-id="...">`
  - Kategorie: `<rect>` + `<text>` + Badges (E/U/W)
  - Wert: `<circle>` oder `<rect class="leaf">` + `<text>` + Badges (★/✕)
- Verbindungslinien: `<path>` oder `<line>` zwischen Eltern und Kindern
- Inline-Edit: `<foreignObject>` mit `<input>` oder Overlay-DIV

### 2.4 ClassificationTreeMatrix.tsx

**Rolle:** Testfallmatrix unter dem Baum. Spalten exakt unter den Klassen ausgerichtet.

```typescript
interface Props {
  categories: Category[];
  values: Record<number, Value[]>;
  testcases: TestCaseOut[];
  zoomLevel: number;
  manualTestCases: ManualTestCase[];
  onCellClick: (testCaseIndex: number, categoryId: number, valueId: number) => void;
  onManualSave: () => Promise<void>;
}
```

**Layout-Strategie:**
- Spalten-Breiten und -Positionen kommen vom gleichen Layout wie der Baum
- Jede Spalte entspricht einem Wert (Klasse) einer Kategorie
- Kategorie-Header ueber den Wert-Spalten (wie Baum-Struktur)
- Zeilen: Testfall-Nr. (sticky links) + ● in Spalten der zugewiesenen Klassen
- Manuelle Zeilen: Dropdown pro Zelle bei Klick

**Matrix-Zeile:**
```
| Nr. | Kat1:Val1 | Kat1:Val2 | Kat2:Val1 | ... |
|-----|-----------|-----------|-----------|-----|
| 1   |     ●     |           |     ●     |     |
| 2   |           |     ●     |           |     |
```

### 2.5 ClassificationTreeToolbar.tsx

**Rolle:** Zoom-Controls + Generierung-Dropdown + Export + manueller Testfall.

```
[ Generierung: v ]  [ + ] [ - ] [ Einpassen ]  [ SVG ] [ PNG ]  [ + Manuelles TF ]
```

---

## 3. Layout-Funktion: lib/classificationTreeLayout.ts

### 3.1 Ziel

Berechnen von Positionen und Breiten fuer alle Baumknoten, sodass:
- Keine Ueberlappung bei 30 Klassifikationen × 20 Klassen
- Spalten exakt unter den Klassen fuer die Matrix ausgerichtet sind
- Layout in < 50ms berechnet wird

### 3.2 API

```typescript
interface LayoutNode {
  id: string;           // "root" | "cat-{id}" | "val-{id}"
  x: number;            // Linke Kante
  y: number;            // Obere Kante
  width: number;        // Breite
  height: number;       // Hoehe
  children?: LayoutNode[];
  centerX: number;      // Mittelpunkt X (für Verbindungslinien)
}

interface LayoutResult {
  root: LayoutNode;
  categoryColumns: CategoryColumn[]; // fuer Matrix-Spalten
  totalWidth: number;
  totalHeight: number;
}

interface CategoryColumn {
  categoryId: number;
  categoryName: string;
  isResult: boolean;
  valueColumns: ValueColumn[];
}

interface ValueColumn {
  valueId: number;
  valueName: string;
  x: number;
  width: number;
  isDefault: boolean;
  isError: boolean;
}

export function computeClassificationTreeLayout(
  projectName: string,
  categories: Category[],
  values: Record<number, Value[]>,
  options?: LayoutOptions
): LayoutResult;

interface LayoutOptions {
  nodeWidth?: number;        // Standard-Breite pro Wert-Knoten (default: 100)
  nodeHeight?: number;       // Standard-Hoehe pro Knoten (default: 40)
  categoryHeight?: number;   // Hoehe Kategorie-Rechteck (default: 50)
  levelGap?: number;         // Vertikaler Abstand zwischen Ebenen (default: 60)
  siblingGap?: number;       // Horizontaler Abstand zwischen Geschwistern (default: 10)
  categoryGap?: number;      // Horizontaler Abstand zwischen Kategorien (default: 30)
  padding?: number;          // Rand um den Baum (default: 40)
  maxLabelWidth?: number;    // Max. Breite fuer Text (Text wird abgeschnitten)
}
```

### 3.3 Algorithmus

```
1. Fuer jede Kategorie:
   a. Werte der Kategorie zaehlen (n)
   b. Kategorie-Breite = max(n * (nodeWidth + siblingGap), minCategoryWidth)
   c. Kategorie-X = Summe vorheriger Kategorien + categoryGap

2. Fuer jede Kategorie:
   a. Werte horizontal unter der Kategorie verteilen
   b. Wert-X = Kategorie-X + i * (nodeWidth + siblingGap)
   c. Wert-Y = Kategorie-Y + categoryHeight + levelGap

3. Wurzel (Projektname):
   a. Zentriert ueber allen Kategorien
   b. Breite = Gesamtbreite aller Kategorien
   c. Y = 0

4. Verbindungslinien:
   a. Wurzel → Mitte jeder Kategorie
   b. Kategorie → Mitte jedes Werts

5. Matrix-Spalten:
   a. categoryColumns[].valueColumns[].x = Wert.X
   b. categoryColumns[].valueColumns[].width = nodeWidth
```

### 3.4 Performance-Garantie

- O(C * V) wo C = Kategorien, V = max Werte pro Kategorie
- Bei 30 × 20 = 600 Knoten: < 50ms (gemessen mit `performance.now()`)
- `useMemo` in React cached das Layout bis categories/values sich aendern

---

## 4. SVG-Rendering-Strategie

### 4.1 Warum SVG?

- **Vektorbasiert:** Perfekt fuer Export (keine Pixel-Aufloesung)
- **Zoom:** Native `transform="scale(...)"` — kein Re-Render
- **Performance:** 600 Knoten als SVG-Elemente sind leichtgewichtiger als HTML-DOM
- **Export:** `new XMLSerializer().serializeToString(svgElement)` → Blob → Download

### 4.2 SVG-Struktur

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {totalWidth} {totalHeight}"
     width="{totalWidth * zoom}"
     height="{totalHeight * zoom}"
     class="classification-tree-svg">

  <!-- Verbindungslinien (hinten) -->
  <g class="connections">
    <path d="M{rootCenterX},{rootBottom} L{catCenterX},{catTop}" />
    <path d="M{catCenterX},{catBottom} L{valCenterX},{valTop}" />
  </g>

  <!-- Wurzel -->
  <g class="tree-node root" transform="translate({x},{y})">
    <rect width="{w}" height="{h}" rx="8" />
    <text x="{w/2}" y="{h/2}" text-anchor="middle">{projectName}</text>
  </g>

  <!-- Kategorien -->
  <g class="tree-node category" transform="translate({x},{y})" data-node-id="cat-{id}">
    <rect width="{w}" height="{h}" rx="4" />
    <text x="8" y="{h/2}">{name}</text>
    <!-- Badges: E (Ergebnis), U (Ursache), W (Wirkung) -->
    <g class="badge" transform="translate({w-24},{h/2-8})">
      <rect width="20" height="16" rx="8" />
      <text x="10" y="12" text-anchor="middle" font-size="10">E</text>
    </g>
  </g>

  <!-- Werte (Blatter) -->
  <g class="tree-node value" transform="translate({x},{y})" data-node-id="val-{id}">
    <rect width="{w}" height="{h}" rx="20" />
    <text x="{w/2}" y="{h/2}" text-anchor="middle">{value}</text>
    <!-- Badges: ★ (Default), ✕ (Fehlerwert) -->
  </g>
</svg>
```

### 4.3 Theme-Unterstützung

Alle Farben ueber CSS Custom Properties:

```css
.classification-tree-svg {
  --tree-root-bg: var(--theme-primary, #0ea5e9);
  --tree-root-text: var(--theme-primary-foreground, #fff);
  --tree-category-bg: var(--theme-surface, #f8fafc);
  --tree-category-border: var(--theme-border, #e2e8f0);
  --tree-category-text: var(--theme-text, #1e293b);
  --tree-value-bg: var(--theme-bg, #ffffff);
  --tree-value-border: var(--theme-border, #e2e8f0);
  --tree-value-text: var(--theme-text, #1e293b);
  --tree-connection: var(--theme-border, #cbd5e1);
  --tree-badge-result-bg: #a855f7;
  --tree-badge-result-text: #fff;
  --tree-badge-error-bg: #ef4444;
  --tree-badge-error-text: #fff;
  --tree-badge-default-bg: #f59e0b;
  --tree-badge-default-text: #fff;
}
```

Dark Theme: CSS-Variabeln werden durch Theme-System ersetzt.

### 4.4 Inline-Edit via foreignObject

```xml
<foreignObject x="0" y="0" width="{w}" height="{h}">
  <input xmlns="http://www.w3.org/1999/xhtml"
         type="text" value="{currentName}"
         class="tree-edit-input" />
</foreignObject>
```

**Alternative (empfohlen):** Overlay-DIV positioniert via `getBoundingClientRect()` des SVG-Knotens.
Dies vermeidet `foreignObject`-Inkompatibilitaeten zwischen Browsern.

### 4.5 Export SVG/PNG

```typescript
// SVG Export
function exportSvg(svgElement: SVGSVGElement, filename: string): void {
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svgElement);
  const blob = new Blob([svgString], { type: "image/svg+xml" });
  downloadBlob(blob, filename);
}

// PNG Export (via Canvas)
function exportPng(svgElement: SVGSVGElement, filename: string, scale: number = 2): void {
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svgElement);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;
  const img = new Image();
  const blob = new Blob([svgString], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  img.onload = () => {
    canvas.width = img.width * scale;
    canvas.height = img.height * scale;
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((pngBlob) => {
      downloadBlob(pngBlob!, filename);
      URL.revokeObjectURL(url);
    }, "image/png");
  };
  img.src = url;
}

function downloadBlob(blob: Blob, filename: string): void {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
```

---

## 5. Interaktionsspezifikation

### 5.1 Knoten-Auswahl

```
Klick auf Knoten → selectedNodeId = nodeId
  → Visuelles Feedback: ring-2 ring-theme-primary
  → Toolbar zeigt Kontext-Info (Name, Typ)
  → Tastaturaktionen (F2, Delete) wirken auf selectedNodeId
```

### 5.2 Inline-Edit (Umbenennen)

```
Trigger: Doppelklick ODER F2 auf gewaehltен Knoten
  → editingNodeId = nodeId
  → editingName = currentName
  → SVG-Knoten zeigt Input-Overlay

Bestaetigen: Enter ODER Blur
  → Wenn editingName.trim() !== currentName:
    → API-Call (renameApi.category oder renameApi.value)
    → On Success: Store-Update, Toast "Umbenannt"
    → On Error: Toast Fehler, Wert rueckgaengig
  → editingNodeId = null

Abbrechen: Escape
  → editingNodeId = null (keine Aenderung)
```

### 5.3 Loeschen

```
Trigger: Delete-Taste auf gewaehltен Knoten ODER Kontextmenü "Loeschen"
  → Dialog: "Bist du sicher, dass du '{name}' loeschen moechtest?"
    + Warnung bei aktiven Referenzen: "Diese Klasse wird in X Regeln verwendet."
  → Bestaetigen:
    → API-Call (deleteCategory oder deleteValue)
    → On Success: Store-Update, Toast "Geloescht"
    → On Error: Toast Fehler, Zustand unveraendert
  → Abbrechen: Dialog schliessen, nichts aendern
```

### 5.4 Drag & Drop (Reihenfolge)

```
Drag Start: Mousedown auf Knoten + Bewegung
  → dragNodeId = nodeId
  → Visuell: Knoten wird halbtransparent (opacity-60)

Drag Over: Mousemove ueber anderen Knoten
  → dropTargetId = hoveredNodeId
  → Visuell: Ziel-Knoten zeigt Indikator (z.B. blauer Balken davor)

Drop: Mouseup
  → Wenn dragNodeId && dropTargetId && dragNodeId !== dropTargetId:
    → Neue Reihenfolge berechnen (Index-Tausch)
    → API-Call (reorderApi.categories oder values)
    → On Success: Store-Update, Toast "Reihenfolge gespeichert"
    → On Error: Toast Fehler, Zustand rueckgaengig
  → dragNodeId = null, dropTargetId = null

Drag Cancel: Escape ODER Mouseup auerhalb des Baums
  → dragNodeId = null, dropTargetId = null
```

### 5.5 Zoom

```
Strg+Mausrad:
  → e.preventDefault()
  → zoomLevel = clamp(zoomLevel * (e.deltaY > 0 ? 0.9 : 1.1), 0.1, 5.0)
  → SVG: transform="scale(zoomLevel)"

Buttons +/-:
  → zoomLevel = clamp(zoomLevel +/- 0.25, 0.1, 5.0)

Button "Einpassen":
  → zoomLevel = min(viewportWidth / totalWidth, viewportHeight / totalHeight) * 0.9
  → clamp auf [0.1, 5.0]
```

### 5.6 Matrix-Zelle (manuelle Testfaelle)

```
Klick auf Zelle (manuelle Zeile, Klassifikation-Spalte):
  → Zeigt Dropdown mit allen Werten der Kategorie
  → Auswaehl setzt assignment[categoryId] = valueId
  → Regelpruefung (REQ-6001): bei Verstoß → roter Rahmen + Tooltip

Klick auf Zelle (generierter Testfall):
  → Nur Anzeige (● oder leer), keine Bearbeitung

"Neuer manueller Testfall":
  → Neue Zeile am Ende der Matrix
  → assignment = {} (alle Spalten leer)
  → Fokus auf erste Spalte

"Speichern manueller Testfall":
  → Wenn assignment unvollstaendig: Warnung "Nicht alle Klassifikationen zugewiesen"
  → API-Call (manual generation per REQ-3016 oder Seed-Satz per REQ-6009)
  → On Success: Toast "Manueller Testfall gespeichert", Zeile wird zu generierter Zeile
```

### 5.7 Kontextmenü

```
Rechtsklick auf Knoten:
  → ClassificationTreeContextMenu an Mausposition

Items fuer Kategorie:
  - "Klasse hinzufuegen" → neuer Wert unter dieser Kategorie
  - "Umbenennen" → Inline-Edit
  - "Typ aendern: Standard / Ursache / Wirkung" → API categoryPropertiesApi
  - "Als Ergebnis markieren" → API (is_result toggle)
  - "BVA (Grenzwertanalyse)" → BVADialog (wie in CategoryTree)
  - "Datenklasse anwenden" → DataNodeApplyDialog
  - "— " (Trennlinie)
  - "Loeschen" (rot) → Loesch-Dialog

Items fuer Wert:
  - "Als Standard markieren" / "Standard entfernen" → API categoriesApi.setDefault/unsetDefault
  - "Umbenennen" → Inline-Edit
  - "— "
  - "Loeschen" (rot) → Loesch-Dialog
```

---

## 6. i18n Keys (REQ-6005)

Neue Keys fuer `de.json` und `en.json`:

```json
"classificationTree": {
  "tabLabel": "Klassifikationsbaum",
  "tabLabelEn": "Classification Tree",
  "rootLabel": "Testobjekt",
  "categoryLabel": "Klassifikation",
  "valueLabel": "Klasse",
  "badgeResult": "Ergebnis",
  "badgeResultEn": "Result",
  "badgeCause": "Ursache",
  "badgeCauseEn": "Cause",
  "badgeEffect": "Wirkung",
  "badgeEffectEn": "Effect",
  "badgeDefault": "Standard",
  "badgeDefaultEn": "Default",
  "badgeError": "Fehlerwert",
  "badgeErrorEn": "Error Value",
  "noCategories": "Keine Klassifikationen vorhanden.",
  "noCategoriesHint": "Fuege in der Kategorien-Ansicht Klassifikationen hinzu.",
  "noValues": "— keine Klassen —",
  "selectGeneration": "Generierung waehlen",
  "zoomIn": "Vergrößern",
  "zoomOut": "Verkleinern",
  "zoomFit": "Einpassen",
  "exportSvg": "Als SVG exportieren",
  "exportPng": "Als PNG exportieren",
  "addManualTestCase": "Neuer manueller Testfall",
  "saveManualTestCase": "Speichern",
  "manualIncomplete": "Nicht alle Klassifikationen sind zugewiesen.",
  "manualSaved": "Manueller Testfall gespeichert.",
  "contextMenu": {
    "addValue": "Klasse hinzufuegen",
    "rename": "Umbenennen",
    "delete": "Loeschen",
    "deleteConfirm": "Bist du sicher, dass du '{name}' loeschen moechtest?",
    "deleteWarning": "Diese Klasse wird in {ruleCount} Regeln und {testcaseCount} Testfaellen verwendet.",
    "typeNormal": "Typ: Standard",
    "typeCause": "Typ: Ursache",
    "typeEffect": "Typ: Wirkung",
    "setResult": "Als Ergebnis markieren",
    "unsetResult": "Ergebnis-Status entfernen",
    "setDefault": "Als Standard markieren",
    "unsetDefault": "Standard entfernen",
    "bva": "Grenzwertanalyse (BVA)",
    "applyDataClass": "Datenklasse anwenden"
  },
  "toast": {
    "renamed": "Umbenannt.",
    "deleted": "Geloescht.",
    "orderSaved": "Reihenfolge gespeichert.",
    "errorRename": "Fehler beim Umbenennen.",
    "errorDelete": "Fehler beim Loeschen.",
    "errorSort": "Fehler beim Speichern der Reihenfolge.",
    "manualSaved": "Manueller Testfall gespeichert.",
    "manualError": "Fehler beim Speichern des manuellen Testfalls."
  },
  "keyboardHelp": {
    "rename": "F2 = Umbenennen",
    "delete": "Entf = Loeschen",
    "zoomIn": "+ = Vergrößern",
    "zoomOut": "- = Verkleinern",
    "zoomFit": "0 = Einpassen",
    "exportSvg": "Strg+E = SVG exportieren",
    "exportPng": "Strg+P = PNG exportieren",
    "undo": "Strg+Z = Rueckgaengig",
    "redo": "Strg+Y = Wiederholen"
  }
}
```

---

## 7. Testplan (TDD-Reihenfolge)

### Phase 1: Layout (lib/classificationTreeLayout.ts)

```
TEST-1: computeClassificationTreeLayout mit 1 Kategorie, 3 Werten
  → Positionen korrekt, keine Ueberlappung

TEST-2: 30 Kategorien × 20 Werte
  → totalWidth > 0, totalHeight > 0
  → Keine Ueberlappung zwischen beliebigen Knoten
  → Berechnung in < 50ms

TEST-3: categoryColumns fuer Matrix
  → Anzahl Spalten = Summe aller Werte
  → Spalten-X entspricht Wert-X im Baum
```

### Phase 2: ClassificationTreeView (Rendering)

```
TEST-4: Render mit mock categories/values
  → SVG existiert, Knoten-Anzahl korrekt

TEST-5: Badge-Rendering (Ergebnis, Fehlerwert, Default)
  → Symbol UND Beschriftung sichtbar

TEST-6: Zoom-Transformation
  → viewBox und transform korrekt

TEST-7: Doppelklick → Inline-Edit
  → Input erscheint, Wert praefilled
```

### Phase 3: ClassificationTreeMatrix (Zuordnung)

```
TEST-8: Matrix-Zeilen = testcase-Anzahl
TEST-9: ● in korrekter Spalte pro assignment
TEST-10: Manuelle Zeile → Klick auf Zelle → Dropdown
```

### Phase 4: Integration (ClassificationTreeTab)

```
TEST-11: Tab erscheint in ProjectDetailPage
TEST-12: Generierung-Dropdown → Matrix aktualisiert
TEST-13: Export SVG/PNG → Blob Download
```

### Phase 5: E2E (Playwright)

```
TEST-14: Screenshot von Baum mit 5 Kategorien × 5 Werten
TEST-15: Zoom-In/Out → Screenshot-Vergleich
TEST-16: Bearbeiten (Umbenennen, Loeschen) → Zustand nach Aktion
```

---

## 8. Risiken & Rueckfragen

### 8.1 Risiken

| Risiko | Einflus | Minderung |
|--------|---------|-----------|
| SVG-Performance bei > 600 Knoten | Hoch | `useMemo` + virtueller Render (nur sichtbare Knoten) |
| foreignObject-Inkompatibilitaet | Mittel | Overlay-DIV statt foreignObject |
| PNG-Export bei groesseren Baeumen | Mittel | Canvas-Scale begrenzen, Progress-Indicator |
| Drag & Drop in SVG | Hoch | Eigene Pointer-Events-Implementierung (kein HTML-drag) |
| Theme-Kontrast bei Badges | Mittel | Kontrast-Tests in CI (axe-core) |

### 8.2 Rueckfragen an Orchestrator

1. **Verfeinerung (REQ-6016):** Soll der Klassifikationsbaum bereits die Struktur fuer mehrstufige Baeume vorbereiten, oder strikt zweistufig bleiben?
   - *Vorschlag:* Zweistufig implementieren, aber Layout-Funktion mit optionalem `children`-Feld vorbereiten.

2. **Manuelle Testfaelle:** Soll das Speichern eine neue Generierung (`manual`) erstellen oder einen Seed-Satz (REQ-6009)?
   - *Vorschlag:* Beides anbieten: "Als Generierung speichern" und "Als Seed-Satz speichern".

3. **Export mit Matrix:** Soll der Export standardmaessig Matrix enthalten, oder nur als Option?
   - *Vorschlag:* Zwei Buttons: "Baum exportieren" und "Baum + Matrix exportieren".

4. **Undo/Redo Integration:** Soll der Klassifikationsbaum den bestehenden `categoryStore` Undo/Redo verwenden, oder einen eigenen?
   - *Vorschlag:* Gleichen `categoryStore` verwenden; Aenderungen im Baum triggern die gleichen Snapshot-Mechanismen.

---

## 9. Implementierungs-Checkliste

- [ ] `lib/classificationTreeLayout.ts` — Layout-Algorithmus + Tests
- [ ] `lib/classificationTreeSvg.ts` — SVG-Hilfsfunktionen
- [ ] `components/classification-tree/ClassificationTreeNode.tsx` — Einzelknoten
- [ ] `components/classification-tree/ClassificationTreeView.tsx` — Baum-Rendering
- [ ] `components/classification-tree/ClassificationTreeMatrix.tsx` — Matrix
- [ ] `components/classification-tree/ClassificationTreeToolbar.tsx` — Zoom + Export
- [ ] `components/classification-tree/ClassificationTreeTab.tsx` — Hauptkomponente
- [ ] `components/classification-tree/ManualTestCaseEditor.tsx` — Manuelle Testfaelle
- [ ] `ProjectDetailPage.tsx` — Neuen Tab "classification" hinzufuegen
- [ ] `i18n/de.json`, `i18n/en.json` — Neue Keys
- [ ] `__tests__/classificationTreeLayout.test.ts` — Layout-Tests
- [ ] `__tests__/ClassificationTreeView.test.tsx` — Rendering-Tests
- [ ] `__tests__/ClassificationTreeMatrix.test.tsx` — Matrix-Tests
- [ ] Playwright-E2E-Test

---

*Ende der UX-Spezifikation fuer REQ-6006*