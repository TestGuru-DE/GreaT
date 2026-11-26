// BUG C-02: Eingabepruefung und Optionen der Grenzwertanalyse fuer Datum,
// Uhrzeit, Datum+Uhrzeit und Stringlaenge (REQ-6007). Die Zahlen-Pruefung
// (validateMultiRangeBVAConfig) blockierte hier gueltige Eingaben.
import type { BVADataType, BVAExtendedOptions } from "../api/bva";
import type { BVARangeEntry } from "./bva-calc";

export type ExtendedType = Exclude<BVADataType, "number">;

/** Zusatzwert-Schluessel exakt wie im Backend (snake_case, boundary_value.py). */
export const EXTRAS_BY_TYPE: Record<ExtendedType, string[]> = {
  date: ["leap_year", "non_leap_year", "month_ends", "year_transition", "invalid_date"],
  time: ["midnight", "end_of_day", "invalid_2400", "midnight_crossing"],
  datetime: ["leap_year", "midnight"],
  strlen: ["empty", "whitespace_only", "leading_whitespace", "trailing_whitespace"],
};

export const DATE_FORMATS = ["iso", "de"] as const;
export const TIME_FORMATS = ["HH:MM", "HH:MM:SS"] as const;
export const STEPS = ["minute", "second"] as const;
export const CHARSETS = ["alpha", "alnum", "alpha_de", "special", "unicode"] as const;

export function defaultExtendedOptions(type: BVADataType): BVAExtendedOptions {
  if (type === "number") return {};
  const extras = Object.fromEntries(EXTRAS_BY_TYPE[type].map((k) => [k, false]));
  switch (type) {
    case "date":
      return { format: "iso", extras };
    case "time":
      return { format: "HH:MM", step: "minute", extras };
    case "datetime":
      return { step: "minute", extras };
    case "strlen":
      return { charset: "alnum", extras };
  }
}

export const PLACEHOLDERS: Record<ExtendedType, { min: string; max: string }> = {
  date: { min: "2024-01-01", max: "2024-12-31" },
  time: { min: "08:00", max: "17:30" },
  datetime: { min: "2024-01-01T08:00", max: "2024-12-31T17:30" },
  strlen: { min: "1", max: "50" },
};

const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const TIME_RE = /^(\d{2}):(\d{2})(?::(\d{2}))?$/;
const DATETIME_RE = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}(?::\d{2})?)$/;

/** Tage seit Epoche fuer ein gueltiges Kalenderdatum, sonst null. */
function parseDate(raw: string): number | null {
  const m = DATE_RE.exec(raw);
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (y < 1 || mo < 1 || mo > 12 || d < 1) return null;
  const dt = new Date(Date.UTC(2000, mo - 1, d));
  dt.setUTCFullYear(y);
  if (dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return Math.floor(dt.getTime() / 86_400_000);
}

/** Sekunden seit Mitternacht fuer HH:MM oder HH:MM:SS, sonst null. */
function parseTime(raw: string): number | null {
  const m = TIME_RE.exec(raw);
  if (!m) return null;
  const [h, mi, s] = [Number(m[1]), Number(m[2]), Number(m[3] ?? 0)];
  if (h > 23 || mi > 59 || s > 59) return null;
  return h * 3600 + mi * 60 + s;
}

function parseDateTime(raw: string): number | null {
  const m = DATETIME_RE.exec(raw);
  if (!m) return null;
  const d = parseDate(m[1]);
  const t = parseTime(m[2]);
  return d === null || t === null ? null : d * 86_400 + t;
}

function parseLength(raw: string): number | null {
  return /^\d+$/.test(raw) ? Number(raw) : null;
}

const PARSERS: Record<ExtendedType, (raw: string) => number | null> = {
  date: parseDate,
  time: parseTime,
  datetime: parseDateTime,
  strlen: parseLength,
};

const FORMAT_HINT: Record<ExtendedType, string> = {
  date: "Datum im Format JJJJ-MM-TT erwartet",
  time: "Uhrzeit im Format HH:MM oder HH:MM:SS erwartet",
  datetime: "Datum+Uhrzeit im Format JJJJ-MM-TTTHH:MM erwartet",
  strlen: "Ganze Zahl >= 0 erwartet",
};

/** BUG C-10: Zeitzone leer (keine) oder ISO-8601-Offset wie +02:00, -05:30, Z. */
const TIMEZONE_RE = /^(Z|[+-](0\d|1[0-4]):[0-5]\d)$/i;

export function validateTimezone(raw: string | undefined): string | null {
  const value = (raw ?? "").trim();
  return value === "" || TIMEZONE_RE.test(value) ? null : "Zeitzone im Format +HH:MM, -HH:MM oder Z erwartet";
}

/**
 * Prueft die Bereiche fuer einen erweiterten Datentyp.
 * Minimum und Maximum sind Pflicht (das Backend kennt keine offenen Grenzen).
 * Bei Uhrzeiten ist min > max erlaubt (Bereich ueber Mitternacht).
 * Ueberlappende Bereiche werden gemeldet (REQ-6007; bei Uhrzeiten prueft das Backend).
 */
export function validateExtendedRanges(type: ExtendedType, ranges: BVARangeEntry[]): string[] {
  const errors: string[] = [];
  if (!ranges.length) return ["Mindestens ein Bereich erforderlich"];
  const parse = PARSERS[type];
  const parsed: { idx: number; min: number; max: number }[] = [];
  ranges.forEach((range, idx) => {
    const prefix = `Bereich ${idx + 1}`;
    const minRaw = range.minVal.trim();
    const maxRaw = range.maxVal.trim();
    if (!minRaw || !maxRaw) {
      errors.push(`${prefix}: Minimum und Maximum erforderlich`);
      return;
    }
    const min = parse(minRaw);
    const max = parse(maxRaw);
    if (min === null || max === null) {
      errors.push(`${prefix}: ${FORMAT_HINT[type]}`);
      return;
    }
    if (type !== "time" && min > max) {
      errors.push(`${prefix}: Minimum ist größer als Maximum`);
      return;
    }
    parsed.push({ idx, min, max });
  });
  if (type !== "time") {
    const ordered = [...parsed].sort((a, b) => a.min - b.min);
    for (let i = 1; i < ordered.length; i++) {
      if (ordered[i].min <= ordered[i - 1].max) {
        errors.push(`Bereich ${ordered[i - 1].idx + 1} und Bereich ${ordered[i].idx + 1} überschneiden sich`);
      }
    }
  }
  return errors;
}
