// REQ-6007: BVA fuer Datum, Uhrzeit, Stringlaenge (Frontend)
// Typspezifische Berechnungen und Validierung

export type BVAType = "number" | "date" | "time" | "datetime" | "strlen";

export interface BVAExtendedConfig {
  type: BVAType;
  pointsPerBoundary: 2 | 3 | 4;
  // Datum
  dateMin?: string;  // ISO date
  dateMax?: string;
  dateFormat?: "iso" | "de";
  dateExtras?: {
    leapYear?: boolean;
    nonLeapYear?: boolean;
    monthEnds?: boolean;
    yearTransition?: boolean;
    invalidDate?: boolean;
  };
  // Uhrzeit
  timeMin?: string;  // HH:MM or HH:MM:SS
  timeMax?: string;
  timeFormat?: "HH:MM" | "HH:MM:SS";
  timeStep?: "second" | "minute";
  timeExtras?: {
    midnight?: boolean;
    endOfDay?: boolean;
    invalid24?: boolean;
    acrossMidnight?: boolean;
  };
  // Stringlaenge
  strlenMin?: number;
  strlenMax?: number;
  charset?: "alpha" | "alnum" | "alpha_de" | "special" | "unicode";
  strlenExtras?: {
    empty?: boolean;
    spacesOnly?: boolean;
    leadingSpaces?: boolean;
    trailingSpaces?: boolean;
  };
}

// -- Helper functions --

export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
}

export function isTimeAcrossMidnight(minTime: string, maxTime: string): boolean {
  // If min > max, it wraps around midnight (e.g., 22:00 - 02:00)
  return minTime > maxTime;
}

export function countCodepoints(s: string): number {
  // JavaScript strings are UTF-16, spread operator gives codepoints
  return [...s].length;
}

export function formatDateString(date: Date, format: "iso" | "de"): string {
  if (format === "iso") {
    return date.toISOString().slice(0, 10);
  }
  const d = String(date.getDate()).padStart(2, "0");
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const y = date.getFullYear();
  return `${d}.${m}.${y}`;
}

export function formatTimeString(hours: number, mins: number, secs?: number, format?: "HH:MM" | "HH:MM:SS"): string {
  const h = String(hours).padStart(2, "0");
  const m = String(mins).padStart(2, "0");
  if (format === "HH:MM:SS" || secs !== undefined) {
    const s = String(secs ?? 0).padStart(2, "0");
    return `${h}:${m}:${s}`;
  }
  return `${h}:${m}`;
}

// -- BVA Point calculation --

export interface BVAValue {
  value: string;
  is_error: boolean;
  label: string;
}

export function calculateDateBVAPoints(config: BVAExtendedConfig): BVAValue[] {
  if (!config.dateMin || !config.dateMax) return [];
  
  const lo = new Date(config.dateMin);
  const hi = new Date(config.dateMax);
  const fmt = config.dateFormat ?? "iso";
  const results: BVAValue[] = [];
  const n = config.pointsPerBoundary;

  // Lower boundary
  addDatePoint(results, lo, -1, n, fmt, true);
  addDatePoint(results, lo, 0, n, fmt, false);
  addDatePoint(results, lo, 1, n, fmt, false);
  if (n >= 3) addDatePoint(results, lo, 2, n, fmt, false);
  if (n >= 4) addDatePoint(results, lo, -2, n, fmt, true);

  // Upper boundary
  addDatePoint(results, hi, 1, n, fmt, true);
  addDatePoint(results, hi, 0, n, fmt, false);
  addDatePoint(results, hi, -1, n, fmt, false);
  if (n >= 3) addDatePoint(results, hi, -2, n, fmt, false);
  if (n >= 4) addDatePoint(results, hi, 2, n, fmt, true);

  // Extras
  if (config.dateExtras?.leapYear) {
    for (let y = lo.getFullYear(); y <= hi.getFullYear(); y++) {
      if (isLeapYear(y)) {
        results.push({ value: fmt === "iso" ? `${y}-02-29` : `29.02.${y}`, is_error: false, label: `29.02.${y} (Schaltjahr)` });
        break;
      }
    }
  }
  if (config.dateExtras?.nonLeapYear) {
    for (let y = lo.getFullYear(); y <= hi.getFullYear(); y++) {
      if (!isLeapYear(y)) {
        results.push({ value: fmt === "iso" ? `${y}-02-29` : `29.02.${y}`, is_error: true, label: `29.02.${y} (Nicht-Schaltjahr)` });
        break;
      }
    }
  }

  // Deduplicate
  return deduplicate(results);
}

function addDatePoint(results: BVAValue[], base: Date, days: number, _n: number, fmt: "iso" | "de", isError: boolean) {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  const val = formatDateString(d, fmt);
  results.push({ value: val, is_error: isError, label: `${val} (${isError ? "ung\u00fcltig" : "g\u00fcltig"})` });
}

export function calculateTimeBVAPoints(config: BVAExtendedConfig): BVAValue[] {
  if (!config.timeMin || !config.timeMax) return [];
  
  const results: BVAValue[] = [];
  const fmt = config.timeFormat ?? "HH:MM";
  const hasSecs = fmt === "HH:MM:SS";
  config.timeStep; // step wird fuer Feinaufloesung verwendet

  // Parse min/max
  parseTime(config.timeMin); // min/max werden als Strings verwendet
  parseTime(config.timeMax);

  // Add boundary points (simplified)
  results.push({ value: config.timeMin, is_error: false, label: config.timeMin });
  results.push({ value: config.timeMax, is_error: false, label: config.timeMax });

  // Extras
  if (config.timeExtras?.midnight) {
    results.push({ value: hasSecs ? "00:00:00" : "00:00", is_error: false, label: "00:00 (Mitternacht)" });
  }
  if (config.timeExtras?.endOfDay) {
    results.push({ value: hasSecs ? "23:59:59" : "23:59", is_error: false, label: hasSecs ? "23:59:59" : "23:59" });
  }
  if (config.timeExtras?.invalid24) {
    results.push({ value: hasSecs ? "24:00:00" : "24:00", is_error: true, label: "24:00 (ung\u00fcltig)" });
  }

  return deduplicate(results);
}

function parseTime(t: string): [number, number, number] {
  const parts = t.split(":").map(Number);
  return [parts[0] ?? 0, parts[1] ?? 0, parts[2] ?? 0];
}

export function calculateStrlenBVAPoints(config: BVAExtendedConfig): BVAValue[] {
  const min = config.strlenMin ?? 0;
  const max = config.strlenMax ?? 10;
  const cs = config.charset ?? "alpha";
  const results: BVAValue[] = [];

  const n = config.pointsPerBoundary;

  // Lower boundary
  addStrlenPoint(results, min - 1, cs, true);
  addStrlenPoint(results, min, cs, false);
  addStrlenPoint(results, min + 1, cs, false);
  if (n >= 3) addStrlenPoint(results, min + 2, cs, false);
  if (n >= 4) addStrlenPoint(results, min - 2, cs, true);

  // Upper boundary
  addStrlenPoint(results, max + 1, cs, true);
  addStrlenPoint(results, max, cs, false);
  addStrlenPoint(results, max - 1, cs, false);
  if (n >= 3) addStrlenPoint(results, max - 2, cs, false);
  if (n >= 4) addStrlenPoint(results, max + 2, cs, true);

  // Extras
  if (config.strlenExtras?.empty) {
    addStrlenPoint(results, 0, cs, false);
  }
  if (config.strlenExtras?.spacesOnly) {
    results.push({ value: `<STR len=10 charset=spaces>`, is_error: false, label: "10 Leerzeichen" });
  }

  return deduplicate(results);
}

function addStrlenPoint(results: BVAValue[], len: number, charset: string, isError: boolean) {
  if (len < 0) return;
  if (len > 500) {
    results.push({ value: `<STR len=${len} charset=${charset}>`, is_error: isError, label: `Laenge ${len} (symbolisch)` });
  } else {
    const sample = generateSampleString(len, charset);
    results.push({ value: sample, is_error: isError, label: `Laenge ${len}` });
  }
}

function generateSampleString(len: number, charset: string): string {
  const chars = charset === "alpha" ? "abcdefghijklmnopqrstuvwxyz" :
                charset === "alpha_de" ? "abcdefghijklmnopqrstuvwxyz\u00e4\u00f6\u00fc\u00df" :
                charset === "alnum" ? "abcdefghijklmnopqrstuvwxyz0123456789" :
                charset === "special" ? "!\"$%&'()*+,-./:;?@[\\]^_`{|}~" :
                "a\u00e4\u00f6\u00fc0123\u2603";
  let s = "";
  for (let i = 0; i < len; i++) {
    s += chars[i % chars.length];
  }
  return s;
}

function deduplicate(results: BVAValue[]): BVAValue[] {
  const seen = new Set<string>();
  return results.filter((r) => {
    if (seen.has(r.value)) return false;
    seen.add(r.value);
    return true;
  });
}

// -- Validation --

export function validateBVAExtendedConfig(config: BVAExtendedConfig): string[] {
  const errors: string[] = [];

  if (config.type === "date") {
    if (config.dateMin && config.dateMax && config.dateMin > config.dateMax) {
      errors.push("Startdatum muss vor Enddatum liegen");
    }
    if (config.dateMin && isNaN(Date.parse(config.dateMin))) {
      errors.push("Ung\u00fcltiges Startdatum");
    }
    if (config.dateMax && isNaN(Date.parse(config.dateMax))) {
      errors.push("Ung\u00fcltiges Enddatum");
    }
  }

  if (config.type === "strlen") {
    if ((config.strlenMin ?? 0) > (config.strlenMax ?? 0)) {
      errors.push("Min-L\u00e4nge darf nicht gr\u00f6\u00dfer als Max sein");
    }
  }

  return errors;
}