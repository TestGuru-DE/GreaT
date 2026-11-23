// REQ-6007: Tests fuer bva-extended.ts

import { describe, expect, it } from "vitest";
import {
  isLeapYear,
  isTimeAcrossMidnight,
  countCodepoints,
  calculateDateBVAPoints,
  calculateTimeBVAPoints,
  calculateStrlenBVAPoints,
  validateBVAExtendedConfig,
} from "../bva-extended";

describe("isLeapYear", () => {
  it("2024 ist Schaltjahr", () => { expect(isLeapYear(2024)).toBe(true); });
  it("2023 ist kein Schaltjahr", () => { expect(isLeapYear(2023)).toBe(false); });
  it("2100 ist kein Schaltjahr", () => { expect(isLeapYear(2100)).toBe(false); });
  it("2000 ist Schaltjahr", () => { expect(isLeapYear(2000)).toBe(true); });
});

describe("isTimeAcrossMidnight", () => {
  it("22:00-02:00 ueber Mitternacht", () => {
    expect(isTimeAcrossMidnight("22:00", "02:00")).toBe(true);
  });
  it("08:00-17:00 nicht ueber Mitternacht", () => {
    expect(isTimeAcrossMidnight("08:00", "17:00")).toBe(false);
  });
});

describe("countCodepoints", () => {
  it("ASCII-Laenge", () => { expect(countCodepoints("abc")).toBe(3); });
  it("Emoji zaehlt als 1 Codepoint", () => { expect(countCodepoints("\u{1F600}")).toBe(1); });
});

describe("calculateDateBVAPoints", () => {
  it("2-Punkt-Methode", () => {
    const result = calculateDateBVAPoints({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2024-01-01", dateMax: "2024-12-31",
    });
    expect(result.length).toBeGreaterThan(0);
  });

  it("Schaltjahr-Extrawert", () => {
    const result = calculateDateBVAPoints({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2024-01-01", dateMax: "2024-12-31",
      dateExtras: { leapYear: true },
    });
    const feb29 = result.find((r) => r.value.includes("02-29"));
    expect(feb29).toBeTruthy();
    expect(feb29!.is_error).toBe(false);
  });

  it("Nicht-Schaltjahr-Extrawert (fehlerhaft)", () => {
    const result = calculateDateBVAPoints({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2023-01-01", dateMax: "2023-12-31",
      dateExtras: { nonLeapYear: true },
    });
    const feb29 = result.find((r) => r.value.includes("02-29"));
    expect(feb29).toBeTruthy();
    expect(feb29!.is_error).toBe(true);
  });

  it("DE-Format", () => {
    const result = calculateDateBVAPoints({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2024-01-01", dateMax: "2024-12-31",
      dateFormat: "de",
    });
    const first = result[0];
    expect(first.value).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });
});

describe("calculateTimeBVAPoints", () => {
  it("normaler Bereich", () => {
    const result = calculateTimeBVAPoints({
      type: "time", pointsPerBoundary: 2,
      timeMin: "08:00", timeMax: "17:00",
    });
    expect(result.length).toBeGreaterThan(0);
  });

  it("Mitternachtsuebergang", () => {
    const result = calculateTimeBVAPoints({
      type: "time", pointsPerBoundary: 2,
      timeMin: "22:00", timeMax: "02:00",
      timeExtras: { acrossMidnight: true },
    });
    expect(result.length).toBeGreaterThan(0);
  });

  it("24:00 als Fehlerwert", () => {
    const result = calculateTimeBVAPoints({
      type: "time", pointsPerBoundary: 2,
      timeMin: "00:00", timeMax: "23:59",
      timeExtras: { invalid24: true },
    });
    const invalid = result.find((r) => r.value.startsWith("24:"));
    expect(invalid).toBeTruthy();
    expect(invalid!.is_error).toBe(true);
  });
});

describe("calculateStrlenBVAPoints", () => {
  it("normaler Bereich", () => {
    const result = calculateStrlenBVAPoints({
      type: "strlen", pointsPerBoundary: 2,
      strlenMin: 5, strlenMax: 100,
      charset: "alpha",
    });
    expect(result.length).toBeGreaterThan(0);
  });

  it("Laenge > 500 symbolisch", () => {
    const result = calculateStrlenBVAPoints({
      type: "strlen", pointsPerBoundary: 2,
      strlenMin: 400, strlenMax: 600,
      charset: "alnum",
    });
    const symbolic = result.find((r) => r.value.startsWith("<STR"));
    expect(symbolic).toBeTruthy();
  });

  it("Laenge 0 (leer)", () => {
    const result = calculateStrlenBVAPoints({
      type: "strlen", pointsPerBoundary: 2,
      strlenMin: 1, strlenMax: 50,
      charset: "alpha",
      strlenExtras: { empty: true },
    });
    const empty = result.find((r) => r.label.includes("0"));
    expect(empty).toBeTruthy();
  });
});

describe("validateBVAExtendedConfig", () => {
  it("gueltiges Datum", () => {
    const errors = validateBVAExtendedConfig({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2024-01-01", dateMax: "2024-12-31",
    });
    expect(errors.length).toBe(0);
  });

  it("ungueltiges Datum (Min > Max)", () => {
    const errors = validateBVAExtendedConfig({
      type: "date", pointsPerBoundary: 2,
      dateMin: "2024-12-31", dateMax: "2024-01-01",
    });
    expect(errors.length).toBeGreaterThan(0);
  });

  it("ungueltige Stringlaenge (Min > Max)", () => {
    const errors = validateBVAExtendedConfig({
      type: "strlen", pointsPerBoundary: 2,
      strlenMin: 100, strlenMax: 10,
    });
    expect(errors.length).toBeGreaterThan(0);
  });
});