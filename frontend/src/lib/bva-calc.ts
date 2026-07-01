// REQ-3041, REQ-3042: Grenzwertanalyse-Berechnungen mit Decimal.js
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
 * Berechnet BVA-Punkte fuer eine numerische Aequivalenzklasse.
 * 
 * REQ-3042: Nutzt Decimal.js fuer praezise Berechnungen (0.1 + 0.2 = 0.3).
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

  if (minDec.greaterThan(maxDec)) return [];

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
    points.push(
      { value: minDec.toString(), type: "boundary", label: "min" },
      { value: maxDec.toString(), type: "boundary", label: "max" }
    );
  } else if (pointsPerBoundary === 3) {
    const minPlusE = minDec.plus(epsilonDec);
    points.push(
      { value: minDec.toString(), type: "boundary", label: "min" },
      { value: minPlusE.toString(), type: "inside", label: "min+ε" },
      { value: maxDec.toString(), type: "boundary", label: "max" }
    );
  } else if (pointsPerBoundary === 4) {
    const minPlusE = minDec.plus(epsilonDec);
    const maxMinusE = maxDec.minus(epsilonDec);
    points.push(
      { value: minDec.toString(), type: "boundary", label: "min" },
      { value: minPlusE.toString(), type: "inside", label: "min+ε" },
      { value: maxMinusE.toString(), type: "inside", label: "max-ε" },
      { value: maxDec.toString(), type: "boundary", label: "max" }
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
 * Validiert BVA-Konfiguration.
 * @returns Array von Fehlermeldungen (leer = valide)
 */
export function validateBVAConfig(config: BVAConfig): string[] {
  const errors: string[] = [];

  if (!config.min) errors.push("Minimum erforderlich");
  if (!config.max) errors.push("Maximum erforderlich");

  try {
    const minDec = new Decimal(config.min);
    const maxDec = new Decimal(config.max);
    if (minDec.greaterThan(maxDec)) {
      errors.push("Minimum darf nicht größer als Maximum sein");
    }
  } catch {
    errors.push("Ungültiger numerischer Wert");
  }

  return errors;
}
