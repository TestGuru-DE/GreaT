// REQ-3041, REQ-3042: Grenzwertanalyse-Berechnungen mit Decimal.js
// ISTQB-konform: 2-Wert = 4 Werte, 3-Wert = 6 Werte, 4-Wert = 8 Werte
import Decimal from "decimal.js";

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
    minDec = new Decimal(min);
    maxDec = new Decimal(max);
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
    ? new Decimal(epsilon)
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

/**
 * Validiert BVA-Konfiguration.
 * @returns Array von Fehlermeldungen (leer = valide)
 */
export function validateBVAConfig(config: BVAConfig): string[] {
  const errors: string[] = [];

  if (!config.min) errors.push("Minimum erforderlich");
  if (!config.max) errors.push("Maximum erforderlich");

  try {
    new Decimal(config.min);
    new Decimal(config.max);
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
  if (!ranges.length) return [];

  const allCandidates = new Map<string, MultiRangeBVAPoint>();

  ranges.forEach((range) => {
    const rangePoints = calculateBVAPoints({
      min: range.minVal,
      max: range.maxVal,
      pointsPerBoundary,
    });

    rangePoints.forEach((point) => {
      if (allCandidates.has(point.value)) return; // Skip duplicates

      const isError = classifyMultiRangeValue(point.value, ranges);
      const sourceRange = `${range.minVal}-${range.maxVal} (${
        range.allowed ? "erlaubt" : "nicht erlaubt"
      })`;

      allCandidates.set(point.value, {
        ...point,
        isError,
        sourceRange,
      });
    });
  });

  // Sort by numeric value
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
      const min = new Decimal(range.minVal);
      const max = new Decimal(range.maxVal);

      if (val.greaterThanOrEqualTo(min) && val.lessThanOrEqualTo(max)) {
        return !range.allowed; // In nicht-erlaubtem Bereich = Fehler
      }
    }

    return true; // Außerhalb aller Bereiche = Fehler
  } catch {
    return true; // Parse-Fehler = Fehler
  }
}
