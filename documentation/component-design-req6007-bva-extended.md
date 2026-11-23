# Komponenten-Design: REQ-6007 BVA Extended

## Typsystem-Erweiterung (lib/bva-calc.ts)

### Discriminated Union für BVAConfig

```typescript
// Bestehender Typ bleibt erhalten (Zahl)
export interface BVAConfig {
  dataType: "number";
  min: string;
  max: string;
  pointsPerBoundary: 2 | 3 | 4;
  epsilon?: string;
  markAsErrorCase?: boolean;
  ranges?: BVARangeEntry[];
}

// Neue Typen (discriminated union via dataType)
export interface DateBVAConfig {
  dataType: "date";
  pointsPerBoundary: 2 | 3 | 4;
  dateFormat: "iso" | "german";
  ranges: DateBVARange[];
}

export interface TimeBVAConfig {
  dataType: "time";
  pointsPerBoundary: 2 | 3 | 4;
  timeFormat: "hhmm" | "hhmmss";
  stepUnit: "minute" | "second";
  ranges: TimeBVARange[];
}

export interface DateTimeBVAConfig {
  dataType: "datetime";
  pointsPerBoundary: 2 | 3 | 4;
  format: "iso8601" | "isoOffset" | "german";
  stepUnit: "hour" | "minute" | "second";
  ranges: DateTimeBVARange[];
}

export interface StringLengthBVAConfig {
  dataType: "stringLength";
  pointsPerBoundary: 2 | 3 | 4;
  charset: "alpha" | "alnum" | "alnumUmlaut" | "special" | "unicode";
  ranges: StringLengthBVARange[];
}

// Union-Typ für BVADialog-State
export type ExtendedBVAConfig =
  | BVAConfig
  | DateBVAConfig
  | TimeBVAConfig
  | DateTimeBVAConfig
  | StringLengthBVAConfig;

// Helper-Typ für Datentyp-Label
export type BVADataType = ExtendedBVAConfig["dataType"];
```

### Bereichs-Typen

```typescript
// Datum
export interface DateBVARange {
  id: string;
  minVal: string;  // "2024-01-01"
  maxVal: string;  // "2024-12-31"
  allowed: boolean;
  extras: DateExtras;
}

export interface DateExtras {
  leapYear: boolean;
  nonLeapYear: boolean;
  monthEnds: boolean;
  yearTransition: boolean;
  invalidDate: boolean;
}

// Uhrzeit
export interface TimeBVARange {
  id: string;
  minVal: string;  // "08:00" oder "08:00:00"
  maxVal: string;  // "18:00" oder "18:00:00"
  allowed: boolean;
  extras: TimeExtras;
}

export interface TimeExtras {
  midnight: boolean;
  endOfDay: boolean;
  invalid24: boolean;
  midnightTransition: boolean;
}

// Datum+Uhrzeit
export interface DateTimeBVARange {
  id: string;
  minDate: string;  // "2024-01-01"
  minTime: string;  // "08:00"
  maxDate: string;  // "2024-12-31"
  maxTime: string;  // "18:00"
  allowed: boolean;
  extras: DateTimeExtras;
}

export interface DateTimeExtras {
  leapYear: boolean;
  monthEnds: boolean;
  midnightBoundary: boolean;
  endOfDayBoundary: boolean;
}

// Stringlänge
export interface StringLengthBVARange {
  id: string;
  minLen: string;   // "1"
  maxLen: string;   // "50"
  allowed: boolean;
  extras: StringLengthExtras;
}

export interface StringLengthExtras {
  zeroLength: boolean;
  onlySpaces: boolean;
  leadingSpaces: boolean;
  trailingSpaces: boolean;
}
```

---

## BVADialog.tsx Änderungen

### State-Erweiterung

```typescript
// Vorher:
const [config, setConfig] = useState<BVAConfig>({
  min: "",
  max: "",
  pointsPerBoundary: 2,
  markAsErrorCase: false,
  ranges: [{ id: "range-1", minVal: "", maxVal: "", allowed: true }],
});

// Nachher:
const [dataType, setDataType] = useState<BVADataType>("number");
const [config, setConfig] = useState<ExtendedBVAConfig>({
  dataType: "number",
  min: "",
  max: "",
  pointsPerBoundary: 2,
  markAsErrorCase: false,
  ranges: [{ id: "range-1", minVal: "", maxVal: "", allowed: true }],
});
```

### Datentyp-Dropdown (neu im Dialog-Body)

```tsx
{/* Datentyp-Auswahl */}
<div className="flex items-center gap-3">
  <label
    htmlFor="bva-data-type"
    className="text-sm font-medium text-slate-700"
  >
    {t('bvaDialog.dataType.label')}
  </label>
  <select
    id="bva-data-type"
    value={dataType}
    onChange={(e) => handleDataTypeChange(e.target.value as BVADataType)}
    className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500"
    aria-label={t('bvaDialog.dataType.label')}
  >
    <option value="number">{t('bvaDialog.dataType.number')}</option>
    <option value="date">{t('bvaDialog.dataType.date')}</option>
    <option value="time">{t('bvaDialog.dataType.time')}</option>
    <option value="datetime">{t('bvaDialog.dataType.datetime')}</option>
    <option value="stringLength">{t('bvaDialog.dataType.stringLength')}</option>
  </select>
</div>
```

### handleDataTypeChange

```typescript
const handleDataTypeChange = (newType: BVADataType) => {
  setDataType(newType);
  
  // Config zurücksetzen auf Default für neuen Typ
  const newConfig = createDefaultConfig(newType);
  setConfig(newConfig);
};

function createDefaultConfig(type: BVADataType): ExtendedBVAConfig {
  const baseRanges = [{ id: `range-${Date.now()}`, allowed: true }];
  
  switch (type) {
    case "number":
      return {
        dataType: "number",
        min: "",
        max: "",
        pointsPerBoundary: 2,
        markAsErrorCase: false,
        ranges: [{ ...baseRanges[0], minVal: "", maxVal: "" }],
      };
    case "date":
      return {
        dataType: "date",
        pointsPerBoundary: 2,
        dateFormat: "iso",
        ranges: [{ ...baseRanges[0], minVal: "", maxVal: "", extras: defaultDateExtras() }],
      };
    case "time":
      return {
        dataType: "time",
        pointsPerBoundary: 2,
        timeFormat: "hhmm",
        stepUnit: "minute",
        ranges: [{ ...baseRanges[0], minVal: "", maxVal: "", extras: defaultTimeExtras() }],
      };
    case "datetime":
      return {
        dataType: "datetime",
        pointsPerBoundary: 2,
        format: "iso8601",
        stepUnit: "hour",
        ranges: [{ ...baseRanges[0], minDate: "", minTime: "", maxDate: "", maxTime: "", extras: defaultDateTimeExtras() }],
      };
    case "stringLength":
      return {
        dataType: "stringLength",
        pointsPerBoundary: 2,
        charset: "alnum",
        ranges: [{ ...baseRanges[0], minLen: "", maxLen: "", extras: defaultStringLengthExtras() }],
      };
  }
}
```

### InputPanel-Router

```tsx
{/* Typspezifisches InputPanel */}
{config.dataType === "number" && (
  <BVAInputPanel config={config} onChange={setConfig} />
)}
{config.dataType === "date" && (
  <DateInputPanel config={config} onChange={setConfig} t={t} />
)}
{config.dataType === "time" && (
  <TimeInputPanel config={config} onChange={setConfig} t={t} />
)}
{config.dataType === "datetime" && (
  <DateTimeInputPanel config={config} onChange={setConfig} t={t} />
)}
{config.dataType === "stringLength" && (
  <StringLengthInputPanel config={config} onChange={setConfig} t={t} />
)}
```

### handleApply-Erweiterung

```typescript
const handleApply = async () => {
  // ... existing validation ...
  
  const payload = {
    type: config.dataType,
    points: config.pointsPerBoundary,
    // Typspezifische Felder
    ...(config.dataType === "date" && {
      dateFormat: config.dateFormat,
      ranges: config.ranges.map(r => ({
        min_val: r.minVal,
        max_val: r.maxVal,
        allowed: r.allowed,
        extras: r.extras,
      })),
    }),
    // ... andere Typen analog ...
  };
  
  const response = await bvaApi.generateMultiRange(categoryId, payload);
  onApply(response.values);
  onClose();
};
```

---

## DateInputPanel.tsx (NEU)

```tsx
// REQ-6007: DateInputPanel – Datums-Eingabe mit Zusatzwerten
import { useTranslation } from "react-i18next";
import type { DateBVAConfig } from "../../lib/bva-calc";
import { validateDateConfig } from "../../lib/bva-calc";

interface DateInputPanelProps {
  config: DateBVAConfig;
  onChange: (config: DateBVAConfig) => void;
}

export function DateInputPanel({ config, onChange }: DateInputPanelProps) {
  const { t } = useTranslation();
  const errors = validateDateConfig(config.ranges);

  const updateRange = (index: number, patch: Partial<DateBVARange>) => {
    const ranges = [...config.ranges];
    ranges[index] = { ...ranges[index], ...patch };
    onChange({ ...config, ranges });
  };

  const updateExtras = (index: number, patch: Partial<DateExtras>) => {
    const ranges = [...config.ranges];
    ranges[index] = {
      ...ranges[index],
      extras: { ...ranges[index].extras, ...patch },
    };
    onChange({ ...config, ranges });
  };

  const addRange = () => {
    const ranges = [...config.ranges];
    ranges.push({
      id: `range-${Date.now()}`,
      minVal: "",
      maxVal: "",
      allowed: true,
      extras: defaultDateExtras(),
    });
    onChange({ ...config, ranges });
  };

  const removeRange = (index: number) => {
    const ranges = config.ranges.filter((_, i) => i !== index);
    onChange({ ...config, ranges });
  };

  return (
    <div className="space-y-4">
      {/* Ausgabeformat */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-slate-700">
          {t('bvaDialog.date.dateFormat')}
        </label>
        <select
          value={config.dateFormat}
          onChange={(e) => onChange({ ...config, dateFormat: e.target.value as "iso" | "german" })}
          className="px-3 py-2 border border-slate-300 rounded-lg"
        >
          <option value="iso">{t('bvaDialog.date.dateFormatIso')}</option>
          <option value="german">{t('bvaDialog.date.dateFormatGerman')}</option>
        </select>
      </div>

      {/* Bereichs-Liste */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">
          {t('bvaDialog.date.ranges')}
        </label>
        <button
          type="button"
          onClick={addRange}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100"
        >
          {t('bvaDialog.addRange')}
        </button>
      </div>

      {config.ranges.map((range, idx) => (
        <div key={range.id} className="rounded-lg border border-slate-200 p-3 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Bereich {idx + 1}: {range.minVal || "−∞"} … {range.maxVal || "∞"}
            </span>
            {config.ranges.length > 1 && (
              <button
                type="button"
                onClick={() => removeRange(idx)}
                className="text-xs text-red-600 hover:text-red-700"
              >
                {t('common.delete')}
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor={`bva-date-min-${range.id}`} className="block text-xs font-medium text-slate-600 mb-1">
                {t('bvaDialog.date.minLabel')}
              </label>
              <input
                id={`bva-date-min-${range.id}`}
                type="date"
                value={range.minVal}
                onChange={(e) => updateRange(idx, { minVal: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label htmlFor={`bva-date-max-${range.id}`} className="block text-xs font-medium text-slate-600 mb-1">
                {t('bvaDialog.date.maxLabel')}
              </label>
              <input
                id={`bva-date-max-${range.id}`}
                type="date"
                value={range.maxVal}
                onChange={(e) => updateRange(idx, { maxVal: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Zusatzwerte */}
          <fieldset className="border border-slate-200 rounded-lg p-3">
            <legend className="text-xs font-medium text-slate-600 px-2">
              {t('bvaDialog.date.extras')}
            </legend>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={range.extras.leapYear}
                  onChange={(e) => updateExtras(idx, { leapYear: e.target.checked })}
                  className="w-4 h-4 text-sky-600"
                />
                {t('bvaDialog.date.extrasLeapYear')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={range.extras.nonLeapYear}
                  onChange={(e) => updateExtras(idx, { nonLeapYear: e.target.checked })}
                  className="w-4 h-4 text-sky-600"
                />
                {t('bvaDialog.date.extrasNonLeapYear')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={range.extras.monthEnds}
                  onChange={(e) => updateExtras(idx, { monthEnds: e.target.checked })}
                  className="w-4 h-4 text-sky-600"
                />
                {t('bvaDialog.date.extrasMonthEnds')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={range.extras.yearTransition}
                  onChange={(e) => updateExtras(idx, { yearTransition: e.target.checked })}
                  className="w-4 h-4 text-sky-600"
                />
                {t('bvaDialog.date.extrasYearTransition')}
              </label>
              <label className="flex items-center gap-2 text-sm col-span-2">
                <input
                  type="checkbox"
                  checked={range.extras.invalidDate}
                  onChange={(e) => updateExtras(idx, { invalidDate: e.target.checked })}
                  className="w-4 h-4 text-sky-600"
                />
                {t('bvaDialog.date.extrasInvalidDate')}
              </label>
            </div>
          </fieldset>

          {/* Erlaubt/Fehler */}
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={range.allowed}
              onChange={(e) => updateRange(idx, { allowed: e.target.checked })}
              className="w-4 h-4 text-sky-600"
            />
            {t('bvaDialog.rangeAllowed')}
          </label>
        </div>
      ))}

      {/* Punkte-Auswahl (global, wie bisher) */}
      <PointsSelector
        value={config.pointsPerBoundary}
        onChange={(pts) => onChange({ ...config, pointsPerBoundary: pts })}
      />

      {/* Fehler */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3" role="alert">
          {errors.map((err, idx) => (
            <p key={idx} className="text-sm text-red-700">{err}</p>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## TimeInputPanel.tsx (NEU)

Analog zu DateInputPanel, mit:
- `<input type="time">` für Min/Max
- Bei `HH:MM:SS`: `<input type="time" step="1">`
- Schrittweite-Selektor (Minute/Sekunde)
- Mitternachtsübergang-Erkennung (Min > Max → Hinweis, kein Fehler)
- Zusatzwerte: 00:00, 23:59, 24:00, Mitternachtsübergang

---

## DateTimeInputPanel.tsx (NEU)

Kombination aus DateInputPanel + TimeInputPanel:
- Zwei Inputs pro Grenze: Datum + Uhrzeit
- Format-Selektor: ISO 8601, ISO+Offset, deutsch
- Schrittweite: Stunde/Minute/Sekunde
- Zusatzwerte: Union aus Datum + Uhrzeit

---

## StringLengthInputPanel.tsx (NEU)

```tsx
// REQ-6007: StringLengthInputPanel – Stringlängen-Eingabe
interface StringLengthInputPanelProps {
  config: StringLengthBVAConfig;
  onChange: (config: StringLengthBVAConfig) => void;
}

export function StringLengthInputPanel({ config, onChange }: StringLengthInputPanelProps) {
  const { t } = useTranslation();
  const errors = validateStringLengthConfig(config.ranges);

  return (
    <div className="space-y-4">
      {/* Zeichenvorrat */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-slate-700">
          {t('bvaDialog.stringLength.charset')}
        </label>
        <select
          value={config.charset}
          onChange={(e) => onChange({ ...config, charset: e.target.value as any })}
          className="px-3 py-2 border border-slate-300 rounded-lg"
        >
          <option value="alpha">{t('bvaDialog.stringLength.charsetAlpha')}</option>
          <option value="alnum">{t('bvaDialog.stringLength.charsetAlnum')}</option>
          <option value="alnumUmlaut">{t('bvaDialog.stringLength.charsetUmlaut')}</option>
          <option value="special">{t('bvaDialog.stringLength.charsetSpecial')}</option>
          <option value="unicode">{t('bvaDialog.stringLength.charsetUnicode')}</option>
        </select>
      </div>

      {/* Bereiche */}
      {config.ranges.map((range, idx) => (
        <div key={range.id} className="rounded-lg border border-slate-200 p-3 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                {t('bvaDialog.stringLength.minLabel')}
              </label>
              <input
                type="number"
                min="0"
                value={range.minLen}
                onChange={(e) => updateRange(idx, { minLen: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                {t('bvaDialog.stringLength.maxLabel')}
              </label>
              <input
                type="number"
                min="0"
                value={range.maxLen}
                onChange={(e) => updateRange(idx, { maxLen: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          {/* Zusatzwerte */}
          <fieldset className="border border-slate-200 rounded-lg p-3">
            <legend className="text-xs font-medium text-slate-600 px-2">
              {t('bvaDialog.stringLength.extras')}
            </legend>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={range.extras.zeroLength}
                  onChange={(e) => updateExtras(idx, { zeroLength: e.target.checked })}
                  className="w-4 h-4 text-sky-600" />
                {t('bvaDialog.stringLength.extrasZero')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={range.extras.onlySpaces}
                  onChange={(e) => updateExtras(idx, { onlySpaces: e.target.checked })}
                  className="w-4 h-4 text-sky-600" />
                {t('bvaDialog.stringLength.extrasSpaces')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={range.extras.leadingSpaces}
                  onChange={(e) => updateExtras(idx, { leadingSpaces: e.target.checked })}
                  className="w-4 h-4 text-sky-600" />
                {t('bvaDialog.stringLength.extrasLeading')}
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={range.extras.trailingSpaces}
                  onChange={(e) => updateExtras(idx, { trailingSpaces: e.target.checked })}
                  className="w-4 h-4 text-sky-600" />
                {t('bvaDialog.stringLength.extrasTrailing')}
              </label>
            </div>
          </fieldset>

          {/* Erlaubt */}
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={range.allowed}
              onChange={(e) => updateRange(idx, { allowed: e.target.checked })}
              className="w-4 h-4 text-sky-600" />
            {t('bvaDialog.rangeAllowed')}
          </label>
        </div>
      ))}

      {/* Punkte + Fehler */}
      <PointsSelector value={config.pointsPerBoundary}
        onChange={(pts) => onChange({ ...config, pointsPerBoundary: pts })} />
      {errors.length > 0 && (/* ... */)}
    </div>
  );
}
```

---

## NumberlineVisualization.tsx Erweiterungen

### Typspezifische Achsen

```typescript
// Erweiterung: dataType-aware X-Position
const getX = (idx: number, value: string, dataType: BVADataType): number => {
  switch (dataType) {
    case "number":
      // Bestehende Logik (Decimal-basiert)
      return getNumberX(idx, value, points);
    
    case "date":
      // Tage seit Epoch, normalisiert
      return getDateX(idx, value, points);
    
    case "time":
      // Minuten seit Mitternacht (0-1440)
      return getTimeX(idx, value, points);
    
    case "datetime":
      // Millisekunden seit Epoch
      return getDateTimeX(idx, value, points);
    
    case "stringLength":
      // Numerische Länge (wie Zahl)
      return getNumberX(idx, value, points);
    
    default:
      return getSymbolicX(idx, points.length);
  }
};

function getDateX(idx: number, value: string, points: BVAPoint[]): number {
  const dates = points.map(p => new Date(p.value).getTime());
  const min = Math.min(...dates);
  const max = Math.max(...dates);
  const range = max - min || 1;
  const val = new Date(value).getTime();
  return lineX1 + ((val - min) / range) * (lineX2 - lineX1);
}

function getTimeX(idx: number, value: string, points: BVAPoint[]): number {
  const toMinutes = (t: string) => {
    const [h, m, s] = t.split(":").map(Number);
    return h * 60 + m + (s || 0) / 60;
  };
  const times = points.map(p => toMinutes(p.value));
  const min = Math.min(...times);
  const max = Math.max(...times);
  const range = (max - min) || 1;
  const val = toMinutes(value);
  return lineX1 + ((val - min) / range) * (lineX2 - lineX1);
}
```

### Legende-Erweiterung

```tsx
{/* Typspezifische Legende */}
{dataType === "date" && (
  <g transform={`translate(${lineX1}, ${height - 30})`}>
    <text x={0} y={0} fontSize="10" fill="#64748b">Tage</text>
    {/* ... bestehende Legende ... */}
  </g>
)}
```

---

## PreviewTable.tsx Erweiterungen

### Symbolische String-Werte

```tsx
{points.map((pt, idx) => {
  const displayValue = formatStringValue(pt.value, config.charset);
  const isError = (pt as any).isError;
  
  return (
    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
      <td className="px-3 py-2 font-mono text-slate-800">
        {isError && <span className="mr-1">✗</span>}
        {displayValue}
      </td>
      {/* ... */}
    </tr>
  );
})}

function formatStringValue(value: string, charset?: string): string {
  // Symbolische Darstellung für lange Strings
  if (value.startsWith("<STR ")) return value; // Already symbolic
  if (value.length > 500) {
    return `<STR len=${value.length} charset=${charset || "unknown"}>`;
  }
  return value;
}
```

---

## api/bva.ts Erweiterungen

```typescript
// Bestehende Interfaces erweitern
export interface BVARangeRequest {
  id: string;
  minVal: string;
  maxVal: string;
  allowed: boolean;
  extras?: Record<string, boolean>;  // Typspezifische Extras
}

export interface BVAMultiRangeRequest {
  type?: "number" | "date" | "time" | "datetime" | "stringLength";
  ranges: BVARangeRequest[];
  points: 2 | 3 | 4;
  // Typspezifische Optionen
  dateFormat?: "iso" | "german";
  timeFormat?: "hhmm" | "hhmmss";
  stepUnit?: "minute" | "second" | "hour";
  charset?: "alpha" | "alnum" | "alnumUmlaut" | "special" | "unicode";
}

export const bvaApi = {
  generateMultiRange: async (
    categoryId: number,
    params: BVAMultiRangeRequest
  ): Promise<BVAResponse> => {
    const payload = {
      type: params.type || "number",
      points: params.points,
      ranges: params.ranges.map((range) => ({
        min_val: range.minVal,
        max_val: range.maxVal,
        allowed: range.allowed,
        extras: range.extras,
      })),
      // Typspezifische Felder
      ...(params.dateFormat && { dateFormat: params.dateFormat }),
      ...(params.timeFormat && { timeFormat: params.timeFormat }),
      ...(params.stepUnit && { stepUnit: params.stepUnit }),
      ...(params.charset && { charset: params.charset }),
    };
    // ...
  },
};
```

---

## Test-Design (für QA Director)

### DateInputPanel.test.tsx

```typescript
describe("DateInputPanel", () => {
  it("rendert Datumsauswähler für Min/Max", () => {
    // ...
  });

  it("rendert Ausgabeformat-Dropdown", () => {
    // ...
  });

  it("rendert alle 5 Zusatzwerte-Checkboxes", () => {
    // ...
  });

  it("zeigt Fehler bei Min > Max", () => {
    // Min=2024-12-31, Max=2024-01-01 → Fehler
  });

  it("zeigt Fehler bei ungültigem Datum", () => {
    // Min=2024-02-29 (Nicht-Schaltjahr) → Fehler
  });

  it("triggert onChange bei Datumsänderung", async () => {
    // ...
  });

  it("triggert onChange bei Zusatzwert-Änderung", async () => {
    // ...
  });

  it("erlaubt mehrere Bereiche", () => {
    // addRange → 2 Bereiche sichtbar
  });
});
```

### calculateDateBVAPoints.test.ts

```typescript
describe("calculateDateBVAPoints", () => {
  it("2-Punkt: min-1, min, max, max+1 (Tage)", () => {
    const result = calculateDateBVAPoints({
      dataType: "date",
      pointsPerBoundary: 2,
      dateFormat: "iso",
      ranges: [{
        id: "r1",
        minVal: "2024-01-15",
        maxVal: "2024-01-20",
        allowed: true,
        extras: defaultDateExtras(),
      }],
    });
    expect(result).toContainEqual(expect.objectContaining({ value: "2024-01-14" }));
    expect(result).toContainEqual(expect.objectContaining({ value: "2024-01-15" }));
    expect(result).toContainEqual(expect.objectContaining({ value: "2024-01-20" }));
    expect(result).toContainEqual(expect.objectContaining({ value: "2024-01-21" }));
  });

  it("Schaltjahr 2024: 29.02. als Grenzwert", () => {
    // Bereich enthält 29.02.2024, leapYear=true
  });

  it("Nicht-Schaltjahr 2100: 29.02. als Fehlerwert", () => {
    // 2100 ist kein Schaltjahr (Jahrhundert, nicht durch 400 teilbar)
  });

  it("Monatsenden: 30./31. im Bereich", () => {
    // Bereich 01.03.–31.03. → 31.03. als Grenzwert
  });

  it("Jahreswechsel: 31.12./01.01.", () => {
    // Bereich 28.12.–03.01. → 31.12. und 01.01. als Grenzwerte
  });

  it("Ungültiges Datum: 31.04.", () => {
    // April hat 30 Tage → 31.04. als Fehlerwert
  });
});
```

---

## Migration-Pfad

### Schritt 1: Typsystem (nicht-brechen)
- Neue Interfaces als `export` hinzufügen
- `BVAConfig` bleibt unverändert (discriminated union via `dataType: "number"`)

### Schritt 2: BVADialog (nicht-brechen)
- Datentyp-Dropdown mit Default `number`
- Router-Logik: `number` → bestehendes `BVAInputPanel`
- Neue Panels werden lazy geladen

### Schritt 3: API (nicht-brechen)
- `type`-Feld ist optional, Default `number`
- Backend ignoriert unbekannte Felder (idempotent)

### Schritt 4: i18n (nicht-brechen)
- Neue Keys werden hinzugefügt
- Bestehende Keys bleiben unverändert