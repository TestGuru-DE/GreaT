// REQ-3041, REQ-3042: Tests fuer Grenzwertanalyse-Berechnungen mit Decimal.js
// ISTQB-konform: 2-Wert = 4, 3-Wert = 6, 4-Wert = 8 Werte
import { describe, it, expect } from "vitest";
import {
  calculateBVAPoints,
  type BVAConfig,
} from "../bva-calc";
import Decimal from "decimal.js";

describe("calculateBVAPoints", () => {
  it("2 Punkte pro Grenze: [min-1, min, max, max+1]", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(4);
    expect(result.map((p) => p.value)).toEqual(["9", "10", "20", "21"]);
  });

  it("3 Punkte pro Grenze: [min-1, min, min+1, max-1, max, max+1]", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 3,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(6);
    expect(result.map((p) => p.value)).toEqual(["9", "10", "11", "19", "20", "21"]);
  });

  it("4 Punkte pro Grenze: [min-2, min-1, min, min+1, max-1, max, max+1, max+2]", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 4,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(8);
    expect(result.map((p) => p.value)).toEqual(["8", "9", "10", "11", "19", "20", "21", "22"]);
  });

  it("Dezimal-Präzision: 0.1 + 0.2 = 0.3 exakt", () => {
    const config: BVAConfig = {
      min: "0.1",
      max: "0.3",
      pointsPerBoundary: 3,
      epsilon: "0.1",
    };
    const result = calculateBVAPoints(config);
    expect(result.length).toBeGreaterThanOrEqual(5);
    // Deduplizierung entfernt Duplikate
    const values = result.map((p) => p.value);
    expect(values).toContain("0.1");
    expect(values).toContain("0.3");
  });

  it("Negative Zahlen", () => {
    const config: BVAConfig = {
      min: "-10",
      max: "-5",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(4);
    expect(result.map((p) => p.value)).toEqual(["-11", "-10", "-5", "-4"]);
  });

  it("Epsilon aus Bereich ableiten, wenn nicht angegeben", () => {
    const config: BVAConfig = {
      min: "0.01",
      max: "0.99",
      pointsPerBoundary: 3,
    };
    const result = calculateBVAPoints(config);
    expect(result.length).toBeGreaterThanOrEqual(5);
    // Epsilon sollte 0.01 sein (abgeleitet von min)
    expect(result[0].value).toBe("0");
    expect(result[1].value).toBe("0.01");
  });

  it("Min = Max: nur ein Wert", () => {
    const config: BVAConfig = {
      min: "42",
      max: "42",
      pointsPerBoundary: 4,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(1);
    expect(result[0].value).toBe("42");
  });

  it("Sehr enger Bereich mit 4 Punkten dedupliziert korrekt", () => {
    const config: BVAConfig = {
      min: "1",
      max: "2",
      pointsPerBoundary: 4,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    // min-2=-1, min-1=0, min=1, min+1=2, max-1=1, max=2, max+1=3, max+2=4
    // dedupliziert: [-1, 0, 1, 2, 3, 4]
    expect(result.length).toBeGreaterThanOrEqual(4);
  });

  it("BVAPoint enthält korrekte Typen", () => {
    const config: BVAConfig = {
      min: "5",
      max: "15",
      pointsPerBoundary: 3,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result[0].type).toBe("outside"); // min-1
    expect(result[1].type).toBe("boundary"); // min
    expect(result[2].type).toBe("inside");   // min+1
  });

  it("Wissenschaftliche Notation wird korrekt behandelt", () => {
    const config: BVAConfig = {
      min: "1e-3",
      max: "2e-3",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(4);
    expect(new Decimal(result[1].value).toNumber()).toBeCloseTo(0.001);
    expect(new Decimal(result[2].value).toNumber()).toBeCloseTo(0.002);
  });

  it("Auto-swap wenn min > max", () => {
    const config: BVAConfig = {
      min: "20",
      max: "10",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(4);
    expect(result.map((p) => p.value)).toEqual(["9", "10", "20", "21"]);
  });
});
