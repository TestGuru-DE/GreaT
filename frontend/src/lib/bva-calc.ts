// REQ-3041, REQ-3042: Grenzwertanalyse-Berechnungen mit Decimal.js
// ISTQB-konform: 2-Wert = 4 Werte, 3-Wert = 6 Werte, 4-Wert = 8 Werte
import Decimal from "decimal.js";

function normalizeDecimalInput(value: string): string {
  return value.replace(/,/g, ".").trim();
}

export type BVAPointType = "boundary" | "inside" | "outside";

export interface BVAPoint {
  value: string;
  type: BVAPointType;
  label: string;
}

export interface BVAConfig {
  min: string;
  max: string;
  pointsPerBoundary: 2 | 3 | 4;
  epsilon?: string;
  markAsErrorCase?: boolean;
  ranges?: BVARangeEntry[];
}

/**
 * Leitet Epsilon aus der Praezision von min/max ab.
 * Nutzt die groessere Dezimalstellen-Anzahl.
 */
function deriveEpsilon(minDec: Decimal, maxDec: Decimal): Decimal {
  const minPlaces = Math.abs(minDec.decimalPlaces());
  const maxPlaces = Math.abs(maxDec.decimalPlaces());
  const places = Math.max(minPlaces, maxPlaces);
  
  if (places === 0) return new Decimal(1); // Ganzzahlen
  
  return new Decimal(1).div(new Decimal(10).pow(places));
}

/**
 * Berechnet BVA-Punkte fuer eine numerische Aequivalenzklasse.
 * 
 * REQ-3042: Nutzt Decimal.js fuer praezise Berechnungen (0.1 + 0.2 = 0.3).
 * ISTQB-konform:
 *   2-Wert: [min-1, min, max, max+1] = 4 Werte
 *   3-Wert: [min-1, min, min+1, max-1, max, max+1] = 6 Werte
 *   4-Wert: [min-2, min-1, min, min+1, max-1, max, max+1, max+2] = 8 Werte
 * 
 * @param config - Konfiguration mit min, max, Punkte-Anzahl, epsilon
 * @returns Liste von BVA-Punkten mit Wert, Typ und Label
 */
export function calculateBVAPoints(config: BVAConfig): BVAPoint[] {
  const { min, max, pointsPerBoundary, epsilon } = config;

  if (!min || !max) return [];

  let minDec: Decimal;
  let maxDec: Decimal;
  try {
    minDec = new Decimal(normalizeDecimalInput(min));
    maxDec = new Decimal(normalizeDecimalInput(max));
  } catch {
    return []; // Ungueltige Zahlen
  }

  if (minDec.greaterThan(maxDec)) {
    // Auto-swap wie Backend
    [minDec, maxDec] = [maxDec, minDec];
  }

  // Spezialfall: min == max
  if (minDec.equals(maxDec)) {
    return [{ value: minDec.toString(), type: "boundary", label: "min/max" }];
  }

  // Epsilon aus Bereich ableiten, falls nicht angegeben
  const epsilonDec = epsilon
    ? new Decimal(normalizeDecimalInput(epsilon))
    : deriveEpsilon(minDec, maxDec);

  const points: BVAPoint[] = [];

  if (pointsPerBoundary === 2) {
    // [min-1, min, max, max+1]
    points.push(
      { value: minDec.minus(epsilonDec).toString(), type: "outside",  label: "min−1 (außerhalb)" },
      { value: minDec.toString(),                    type: "boundary", label: "min (Grenze)" },
      { value: maxDec.toString(),                    type: "boundary", label: "max (Grenze)" },
      { value: maxDec.plus(epsilonDec).toString(),  type: "outside",  label: "max+1 (außerhalb)" }
    );
  } else if (pointsPerBoundary === 3) {
    // [min-1, min, min+1, max-1, max, max+1]
    points.push(
      { value: minDec.minus(epsilonDec).toString(), type: "outside",  label: "min−1 (außerhalb)" },
      { value: minDec.toString(),                    type: "boundary", label: "min (Grenze)" },
      { value: minDec.plus(epsilonDec).toString(),  type: "inside",   label: "min+1 (innerhalb)" },
      { value: maxDec.minus(epsilonDec).toString(), type: "inside",   label: "max−1 (innerhalb)" },
      { value: maxDec.toString(),                    type: "boundary", label: "max (Grenze)" },
      { value: maxDec.plus(epsilonDec).toString(),  type: "outside",  label: "max+1 (außerhalb)" }
    );
  } else if (pointsPerBoundary === 4) {
    // [min-2, min-1, min, min+1, max-1, max, max+1, max+2]
    points.push(
      { value: minDec.minus(epsilonDec.times(2)).toString(), type: "outside",  label: "min−2 (außerhalb)" },
      { value: minDec.minus(epsilonDec).toString(),          type: "outside",  label: "min−1 (außerhalb)" },
      { value: minDec.toString(),                            type: "boundary", label: "min (Grenze)" },
      { value: minDec.plus(epsilonDec).toString(),           type: "inside",   label: "min+1 (innerhalb)" },
      { value: maxDec.minus(epsilonDec).toString(),          type: "inside",   label: "max−1 (innerhalb)" },
      { value: maxDec.toString(),                            type: "boundary", label: "max (Grenze)" },
      { value: maxDec.plus(epsilonDec).toString(),           type: "outside",  label: "max+1 (außerhalb)" },
      { value: maxDec.plus(epsilonDec.times(2)).toString(),  type: "outside",  label: "max+2 (außerhalb)" }
    );
  }

  // Deduplizieren basierend auf Wert
  const seen = new Set<string>();
  return points.filter((p) => {
    if (seen.has(p.value)) return false;
    seen.add(p.value);
    return true;
  });
}

function parseOptionalDecimal(value: string): Decimal | null {
  const text = normalizeDecimalInput(value);
  if (!text) return null;
  return new Decimal(text);
}

function normalizeRange(range: BVARangeEntry): { min: Decimal | null; max: Decimal | null } {
  let min: Decimal | null;
  let max: Decimal | null;
  try {
    min = parseOptionalDecimal(range.minVal);
    max = parseOptionalDecimal(range.maxVal);
  } catch {
    return { min: null, max: null };
  }
  if (min && max && min.greaterThan(max)) {
    [min, max] = [max, min];
  }
  return { min, max };
}

function boundValue(bound: Decimal | null, isMin: boolean): string {
  if (!bound) {
    return isMin ? "-∞" : "∞";
  }
  return bound.toString();
}

function generateRangeCandidates(
  min: Decimal | null,
  max: Decimal | null,
  pointsPerBoundary: 2 | 3 | 4
): Array<{ value: Decimal; type: BVAPointType }> {
  if (!min && !max) return [];

  if (!min && max) {
   const epsilon = deriveEpsilon(max, max);
   if (pointsPerBoundary === 2) return [
     { value: max.minus(epsilon), type: "inside" },
     { value: max, type: "boundary" },
   ];
   if (pointsPerBoundary === 3) return [
     { value: max.minus(epsilon.times(2)), type: "outside" },
     { value: max.minus(epsilon), type: "inside" },
     { value: max, type: "boundary" },
   ];
   return [
     { value: max.minus(epsilon.times(3)), type: "outside" },
     { value: max.minus(epsilon.times(2)), type: "outside" },
     { value: max.minus(epsilon), type: "inside" },
     { value: max, type: "boundary" },
   ];
  }

  if (min && !max) {
   const epsilon = deriveEpsilon(min, min);
   if (pointsPerBoundary === 2) return [
     { value: min, type: "boundary" },
     { value: min.plus(epsilon), type: "inside" },
   ];
   if (pointsPerBoundary === 3) return [
     { value: min, type: "boundary" },
     { value: min.plus(epsilon), type: "inside" },
     { value: min.plus(epsilon.times(2)), type: "outside" },
   ];
   return [
     { value: min, type: "boundary" },
     { value: min.plus(epsilon), type: "inside" },
     { value: min.plus(epsilon.times(2)), type: "outside" },
     { value: min.plus(epsilon.times(3)), type: "outside" },
   ];
  }

  const epsilon = deriveEpsilon(min!, max!);
  if (pointsPerBoundary === 2) {
   return [
     { value: min!.minus(epsilon), type: "outside" },
     { value: min!, type: "boundary" },
     { value: max!, type: "boundary" },
     { value: max!.plus(epsilon), type: "outside" },
   ];
  }
  if (pointsPerBoundary === 3) {
   return [
     { value: min!.minus(epsilon), type: "outside" },
     { value: min!, type: "boundary" },
     { value: min!.plus(epsilon), type: "inside" },
     { value: max!.minus(epsilon), type: "inside" },
     { value: max!, type: "boundary" },
     { value: max!.plus(epsilon), type: "outside" },
   ];
  }
  return [
   { value: min!.minus(epsilon.times(2)), type: "outside" },
   { value: min!.minus(epsilon), type: "outside" },
   { value: min!, type: "boundary" },
   { value: min!.plus(epsilon), type: "inside" },
   { value: max!.minus(epsilon), type: "inside" },
   { value: max!, type: "boundary" },
   { value: max!.plus(epsilon), type: "outside" },
   { value: max!.plus(epsilon.times(2)), type: "outside" },
  ];
}

function rangeOverlaps(
  left: { min: Decimal | null; max: Decimal | null },
  right: { min: Decimal | null; max: Decimal | null }
): boolean {
  const leftMax = left.max ?? new Decimal("Infinity");
  const rightMin = right.min ?? new Decimal("-Infinity");
  return leftMax.greaterThanOrEqualTo(rightMin);
}

export function validateMultiRangeBVAConfig(ranges: BVARangeEntry[]): string[] {
  const errors: string[] = [];

  if (!ranges.length) {
    errors.push("Mindestens ein Bereich erforderlich");
    return errors;
  }

  const normalized = ranges.map((range, idx) => {
    let min: Decimal | null = null;
    let max: Decimal | null = null;
    let parseError = false;

    try {
      min = parseOptionalDecimal(range.minVal);
      max = parseOptionalDecimal(range.maxVal);
    } catch {
      parseError = true;
    }

    if (parseError) {
      errors.push(`Bereich ${idx + 1}: Ungültiger numerischer Wert`);
    }

    if (!min && !max) {
      errors.push(`Bereich ${idx + 1}: Minimum oder Maximum erforderlich`);
    }

    if (min && max && min.greaterThan(max)) {
      [min, max] = [max, min];
    }

    return { min, max, label: `${boundValue(min, true)}-${boundValue(max, false)}` };
  });

  const ordered = normalized
    .map((range, idx) => ({ idx, range }))
    .sort((a, b) => {
      const aMin = a.range.min ?? new Decimal("-Infinity");
      const bMin = b.range.min ?? new Decimal("-Infinity");
      if (aMin.lessThan(bMin)) return -1;
      if (aMin.greaterThan(bMin)) return 1;
      const aMax = a.range.max ?? new Decimal("Infinity");
      const bMax = b.range.max ?? new Decimal("Infinity");
      return aMax.comparedTo(bMax);
    });

  for (let i = 1; i < ordered.length; i++) {
    const prev = ordered[i - 1].range;
    const current = ordered[i].range;
    if (rangeOverlaps(prev, current)) {
      errors.push("Bereiche dürfen sich nicht überschneiden oder berühren.");
      break;
    }
  }

  return errors;
}

/**
 * Validiert BVA-Konfiguration.
 * @returns Array von Fehlermeldungen (leer = valide)
 */
export function validateBVAConfig(config: BVAConfig): string[] {
  const errors: string[] = [];

  if (!config.min) errors.push("Minimum erforderlich");
  if (!config.max) errors.push("Maximum erforderlich");

  try {
    new Decimal(normalizeDecimalInput(config.min));
    new Decimal(normalizeDecimalInput(config.max));
    // Auto-swap erlaubt, keine weitere Validierung
  } catch {
    errors.push("Ungültiger numerischer Wert");
  }

  return errors;
}


// REQ-3064: Multi-Range BVA Types
export interface BVARangeEntry {
  id: string;
  minVal: string;
  maxVal: string;
  allowed: boolean;
}

export interface MultiRangeBVAPoint extends BVAPoint {
  sourceRange?: string;
  isError?: boolean;
}

/**
 * Berechnet Multi-Range BVA-Punkte für mehrere Äquivalenzklassen.
 * REQ-3064: Mehrere angrenzende Bereiche mit erlaubt/nicht-erlaubt.
 */
export function calculateMultiRangeBVAPoints(
  ranges: BVARangeEntry[],
  pointsPerBoundary: 2 | 3 | 4
): MultiRangeBVAPoint[] {
  if (validateMultiRangeBVAConfig(ranges).length > 0) return [];

  const normalized = ranges.map((range) => ({
    ...range,
    ...normalizeRange(range),
  }));

  const ordered = [...normalized].sort((a, b) => {
    const aMin = a.min ?? new Decimal("-Infinity");
    const bMin = b.min ?? new Decimal("-Infinity");
    if (aMin.lessThan(bMin)) return -1;
    if (aMin.greaterThan(bMin)) return 1;
    const aMax = a.max ?? new Decimal("Infinity");
    const bMax = b.max ?? new Decimal("Infinity");
    return aMax.comparedTo(bMax);
  });

  const allCandidates = new Map<string, MultiRangeBVAPoint>();

  ordered.forEach((range) => {
    const rangePoints = generateRangeCandidates(range.min, range.max, pointsPerBoundary);
    rangePoints.forEach((point) => {
      const value = point.value.toString();
      if (allCandidates.has(value)) return;
      const sourceRange = `${boundValue(range.min, true)}-${boundValue(range.max, false)} (${
        range.allowed ? "erlaubt" : "nicht erlaubt"
      })`;
      allCandidates.set(value, {
        value,
        type: point.type,
        label: value,
        sourceRange,
        isError: classifyMultiRangeValue(value, normalized),
      });
    });
  });

  return Array.from(allCandidates.values()).sort((a, b) => {
    try {
      return new Decimal(a.value).comparedTo(new Decimal(b.value));
    } catch {
      return 0;
    }
  });
}

/**
 * Klassifiziert einen Wert als Fehler oder gültig.
 * Fehler wenn:
 * - In nicht-erlaubtem Bereich
 * - Außerhalb aller Bereiche
 */
function classifyMultiRangeValue(
  value: string,
  ranges: BVARangeEntry[]
): boolean {
  try {
    const val = new Decimal(value);

    for (const range of ranges) {
      const { min, max } = normalizeRange(range);
      if (min === null && max === null) continue;
      const lowerOk = min === null || val.greaterThanOrEqualTo(min);
      const upperOk = max === null || val.lessThanOrEqualTo(max);
      if (lowerOk && upperOk) {
        return !range.allowed; // In nicht-erlaubtem Bereich = Fehler
      }
    }

    return true; // Außerhalb aller Bereiche = Fehler
  } catch {
    return true; // Parse-Fehler = Fehler
  }
}

export function extractPersistableBVAValues(points: BVAPoint[]): string[] {
  const seen = new Set<string>();
  return points
    .map((pt) => pt.value)
    .filter((value) => value !== "∞" && value !== "-∞" && value.trim() !== "")
    .filter((value) => {
      if (seen.has(value)) return false;
      seen.add(value);
      return true;
    });
}
