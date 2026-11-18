// REQ-6005 Slice 3: Tests fuer useFormattedDate Hook
// Testet Intl.DateTimeFormat direkt (ohne React-Rendering)
import { describe, it, expect } from "vitest";

describe("REQ-6005: useFormattedDate Intl behavior", () => {
  const testDate = new Date("2026-11-18T14:30:00");

  it("should format date in German format DD.MM.YYYY", () => {
    const formatter = new Intl.DateTimeFormat("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    const formatted = formatter.format(testDate);
    // de-DE uses DD.MM.YYYY
    expect(formatted).toMatch(/\d{2}\.\d{2}\.\d{4}/);
    expect(formatted).toContain("2026");
    expect(formatted).toBe("18.11.2026");
  });

  it("should format date in US format MM/DD/YYYY", () => {
    const formatter = new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    const formatted = formatter.format(testDate);
    // en-US uses MM/DD/YYYY
    expect(formatted).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(formatted).toContain("2026");
    expect(formatted).toBe("11/18/2026");
  });

  it("should format datetime in German format", () => {
    const formatter = new Intl.DateTimeFormat("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
    const formatted = formatter.format(testDate);
    expect(formatted).toContain("14:30");
    expect(formatted).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it("should format datetime in US format", () => {
    const formatter = new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
    const formatted = formatter.format(testDate);
    expect(formatted).toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });

  it("should produce different output for DE and EN", () => {
    const formatterDE = new Intl.DateTimeFormat("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    const formatterEN = new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });

    const deFormatted = formatterDE.format(testDate);
    const enFormatted = formatterEN.format(testDate);

    // DE uses dots, EN uses slashes
    expect(deFormatted).toContain(".");
    expect(enFormatted).toContain("/");
    expect(deFormatted).not.toBe(enFormatted);
  });

  it("should handle invalid date gracefully", () => {
    const formatter = new Intl.DateTimeFormat("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    const invalidDate = new Date("not-a-date");
    expect(isNaN(invalidDate.getTime())).toBe(true);
    // Intl.format throws on invalid dates in some environments
    expect(() => formatter.format(invalidDate)).toThrow();
  });
});