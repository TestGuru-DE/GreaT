// REQ-3041, REQ-3042: Tests fuer Grenzwertanalyse-Berechnungen mit Decimal.js
import { describe, it, expect } from "vitest";
import {
  calculateBVAPoints,
  type BVAConfig,
} from "../bva-calc";
import Decimal from "decimal.js";

describe("calculateBVAPoints", () => {
  it("2 Punkte pro Grenze: min, max", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(2);
    expect(result.map((p) => p.value)).toEqual(["10", "20"]);
  });

  it("3 Punkte pro Grenze: min, min+ε, max", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 3,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(3);
    expect(result.map((p) => p.value)).toEqual(["10", "11", "20"]);
  });

  it("4 Punkte pro Grenze: min, min+ε, max-ε, max", () => {
    const config: BVAConfig = {
      min: "10",
      max: "20",
      pointsPerBoundary: 4,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(4);
    expect(result.map((p) => p.value)).toEqual(["10", "11", "19", "20"]);
  });

  it("Dezimal-Präzision: 0.1 + 0.2 = 0.3 exakt", () => {
    const config: BVAConfig = {
      min: "0.1",
      max: "0.3",
      pointsPerBoundary: 3,
      epsilon: "0.1",
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(3);
    expect(result.map((p) => p.value)).toEqual(["0.1", "0.2", "0.3"]);
    // Kein 0.30000000000000004!
    expect(result[2].value).toBe("0.3");
  });

  it("Negative Zahlen", () => {
    const config: BVAConfig = {
      min: "-10",
      max: "-5",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(2);
    expect(result.map((p) => p.value)).toEqual(["-10", "-5"]);
  });

  it("Epsilon aus Bereich ableiten, wenn nicht angegeben", () => {
    const config: BVAConfig = {
      min: "0.01",
      max: "0.99",
      pointsPerBoundary: 3,
    };
    const result = calculateBVAPoints(config);
    expect(result.length).toBeGreaterThanOrEqual(3);
    // Epsilon sollte 0.01 sein (abgeleitet von min)
    expect(result[1].value).toBe("0.02");
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
    // min=1, min+1=2, max-1=1, max=2 -> dedupliziert zu [1,2]
    expect(result).toHaveLength(2);
    expect(result.map((p) => p.value)).toEqual(["1", "2"]);
  });

  it("BVAPoint enthält korrekte Typen", () => {
    const config: BVAConfig = {
      min: "5",
      max: "15",
      pointsPerBoundary: 3,
      epsilon: "1",
    };
    const result = calculateBVAPoints(config);
    expect(result[0].type).toBe("boundary"); // min
    expect(result[1].type).toBe("inside");   // min+ε
    expect(result[2].type).toBe("boundary"); // max
  });

  it("Wissenschaftliche Notation wird korrekt behandelt", () => {
    const config: BVAConfig = {
      min: "1e-3",
      max: "2e-3",
      pointsPerBoundary: 2,
    };
    const result = calculateBVAPoints(config);
    expect(result).toHaveLength(2);
    expect(new Decimal(result[0].value).toNumber()).toBeCloseTo(0.001);
    expect(new Decimal(result[1].value).toNumber()).toBeCloseTo(0.002);
  });
});
