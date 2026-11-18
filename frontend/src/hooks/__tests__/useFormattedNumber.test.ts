// REQ-6005 Slice 3: Tests fuer useFormattedNumber Hook
// Testet Intl.NumberFormat direkt (ohne React-Rendering)
import { describe, it, expect } from "vitest";

describe("REQ-6005: useFormattedNumber Intl behavior", () => {
  it("should format number with German decimal separator (comma)", () => {
    const formatter = new Intl.NumberFormat("de-DE");
    const formatted = formatter.format(1234.5);
    // de-DE uses 1.234,5
    expect(formatted).toContain(",");
    expect(formatted).toBe("1.234,5");
  });

  it("should format number with minimumFractionDigits in German", () => {
    const formatter = new Intl.NumberFormat("de-DE", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    const formatted = formatter.format(42);
    expect(formatted).toBe("42,0");
  });

  it("should format large number with German thousands separator", () => {
    const formatter = new Intl.NumberFormat("de-DE");
    const formatted = formatter.format(1234567.89);
    // de-DE: 1.234.567,89
    expect(formatted).toContain(".");
    expect(formatted).toContain(",");
    expect(formatted).toBe("1.234.567,89");
  });

  it("should format number with US decimal separator (dot)", () => {
    const formatter = new Intl.NumberFormat("en-US");
    const formatted = formatter.format(1234.5);
    // en-US: 1,234.5
    expect(formatted).toContain(".");
    expect(formatted).toBe("1,234.5");
  });

  it("should format number with minimumFractionDigits in US", () => {
    const formatter = new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    const formatted = formatter.format(42);
    expect(formatted).toBe("42.0");
  });

  it("should format large number with US thousands separator", () => {
    const formatter = new Intl.NumberFormat("en-US");
    const formatted = formatter.format(1234567.89);
    // en-US: 1,234,567.89
    expect(formatted).toContain(",");
    expect(formatted).toContain(".");
    expect(formatted).toBe("1,234,567.89");
  });

  it("should produce different output for DE and EN", () => {
    const testValue = 1234.5;
    const formatterDE = new Intl.NumberFormat("de-DE");
    const formatterEN = new Intl.NumberFormat("en-US");

    const deFormatted = formatterDE.format(testValue);
    const enFormatted = formatterEN.format(testValue);

    // DE uses comma as decimal separator, EN uses dot
    expect(deFormatted).toContain(",");
    expect(enFormatted).toContain(".");
    expect(deFormatted).not.toBe(enFormatted);
  });

  it("should handle NaN gracefully", () => {
    const formatter = new Intl.NumberFormat("de-DE");
    // NaN is formatted as "NaN" by Intl
    const result = formatter.format(NaN);
    expect(result).toBe("NaN");
  });
});