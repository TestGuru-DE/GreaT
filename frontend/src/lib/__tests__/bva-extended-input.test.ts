// BUG C-02: Eingabepruefung fuer Datum, Uhrzeit, Datum+Uhrzeit, Stringlaenge
import { describe, it, expect } from "vitest";
import { defaultExtendedOptions, EXTRAS_BY_TYPE, validateExtendedRanges, validateTimezone } from "../bva-extended-input";

const r = (minVal: string, maxVal: string) => [{ id: "r1", minVal, maxVal, allowed: true }];

describe("validateExtendedRanges", () => {
  it.each([
    ["date", "2024-01-01", "2024-12-31"],
    ["date", "2024-02-29", "2024-03-01"],
    ["time", "08:00", "17:30"],
    ["time", "22:00", "06:00"], // ueber Mitternacht erlaubt
    ["time", "00:00:00", "23:59:59"],
    ["datetime", "2024-01-01T08:00", "2024-12-31 17:30:15"],
    ["strlen", "0", "255"],
  ] as const)("%s %s..%s ist gueltig", (type, min, max) => {
    expect(validateExtendedRanges(type, r(min, max))).toEqual([]);
  });

  it.each([
    ["date", "2023-02-29", "2023-03-01"], // kein Schaltjahr
    ["date", "2024-04-31", "2024-05-01"],
    ["date", "01.01.2024", "2024-12-31"],
    ["time", "24:00", "23:00"],
    ["time", "8:00", "09:00"],
    ["time", "-00:01", "09:00"],
    ["datetime", "2024-01-01", "2024-12-31T10:00"],
    ["strlen", "-1", "5"],
    ["strlen", "1.5", "5"],
  ] as const)("%s %s..%s meldet Formatfehler", (type, min, max) => {
    expect(validateExtendedRanges(type, r(min, max))[0]).toMatch(/erwartet/);
  });

  it("fehlende Grenzen und min > max werden gemeldet (ausser Uhrzeit)", () => {
    expect(validateExtendedRanges("date", r("", "2024-01-01"))[0]).toMatch(/erforderlich/);
    expect(validateExtendedRanges("date", r("2024-12-31", "2024-01-01"))[0]).toMatch(/größer/);
    expect(validateExtendedRanges("strlen", r("10", "2"))[0]).toMatch(/größer/);
  });
});

describe("defaultExtendedOptions", () => {
  it("nutzt die snake_case-Schluessel des Backends", () => {
    expect(Object.keys(defaultExtendedOptions("date").extras!)).toEqual(EXTRAS_BY_TYPE.date);
    expect(EXTRAS_BY_TYPE.date).toContain("leap_year");
    for (const keys of Object.values(EXTRAS_BY_TYPE)) {
      for (const k of keys) expect(k).toMatch(/^[a-z0-9_]+$/);
    }
  });
});

// BUG C-05 / REQ-6007: ueberlappende Bereiche sofort melden
describe("validateExtendedRanges - Ueberschneidung", () => {
  const ranges = (...pairs: [string, string][]) =>
    pairs.map(([minVal, maxVal], i) => ({ id: `r${i}`, minVal, maxVal, allowed: i === 0 }));

  it("meldet ueberlappende Datumsbereiche", () => {
    const errors = validateExtendedRanges("date", ranges(["2024-01-01", "2024-01-31"], ["2024-01-15", "2024-02-15"]));
    expect(errors.some((e) => e.includes("überschneiden"))).toBe(true);
  });

  it("akzeptiert angrenzende Bereiche", () => {
    expect(validateExtendedRanges("strlen", ranges(["1", "10"], ["11", "20"]))).toEqual([]);
    expect(validateExtendedRanges("date", ranges(["2024-01-01", "2024-01-31"], ["2024-02-01", "2024-02-29"]))).toEqual([]);
  });

  it("prueft Uhrzeiten nicht auf Ueberschneidung (Mitternacht; das Backend prueft)", () => {
    expect(validateExtendedRanges("time", ranges(["22:00", "02:00"], ["08:00", "12:00"]))).toEqual([]);
  });
});

// BUG C-10: Zeitzone als Formatoption
describe("validateTimezone", () => {
  it.each(["", "+02:00", "-05:30", "Z", "z", "+14:00"])("akzeptiert %j", (tz) => {
    expect(validateTimezone(tz)).toBeNull();
  });
  it.each(["2", "+2", "+0200", "MEZ", "+15:00", "+02:60"])("lehnt %j ab", (tz) => {
    expect(validateTimezone(tz)).not.toBeNull();
  });
});
