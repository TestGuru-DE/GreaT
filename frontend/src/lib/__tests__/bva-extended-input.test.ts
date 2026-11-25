// BUG C-02: Eingabepruefung fuer Datum, Uhrzeit, Datum+Uhrzeit, Stringlaenge
import { describe, it, expect } from "vitest";
import { defaultExtendedOptions, EXTRAS_BY_TYPE, validateExtendedRanges } from "../bva-extended-input";

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
