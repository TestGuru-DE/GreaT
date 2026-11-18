// REQ-6005: Tests fuer i18n-Infrastruktur (Slice 1)
import { describe, it, expect } from "vitest";
import i18n from "../i18n";

describe("REQ-6005: i18n Infrastructure", () => {
  it("should have German as default language", () => {
    expect(i18n.language).toBe("de");
  });

  it("should have both de and en resources loaded", () => {
    expect(i18n.hasResourceBundle("de", "translation")).toBe(true);
    expect(i18n.hasResourceBundle("en", "translation")).toBe(true);
  });

  it("should have matching top-level keys in de.json and en.json", () => {
    const deBundle = i18n.getResourceBundle("de", "translation");
    const enBundle = i18n.getResourceBundle("en", "translation");

    const deKeys = Object.keys(deBundle || {});
    const enKeys = Object.keys(enBundle || {});

    expect(deKeys.sort()).toEqual(enKeys.sort());
  });

  it("should have required nav namespace", () => {
    const deBundle = i18n.getResourceBundle("de", "translation");
    expect(deBundle).toHaveProperty("nav");
    expect(deBundle?.nav).toHaveProperty("home");
    expect(deBundle?.nav).toHaveProperty("projects");
    expect(deBundle?.nav).toHaveProperty("logout");
  });

  it("should have required login namespace", () => {
    const deBundle = i18n.getResourceBundle("de", "translation");
    expect(deBundle).toHaveProperty("login");
    expect(deBundle?.login).toHaveProperty("title");
    expect(deBundle?.login).toHaveProperty("username");
    expect(deBundle?.login).toHaveProperty("password");
    expect(deBundle?.login).toHaveProperty("submit");
  });

  it("should have language switcher keys", () => {
    const deBundle = i18n.getResourceBundle("de", "translation");
    expect(deBundle?.language?.switcher).toHaveProperty("de");
    expect(deBundle?.language?.switcher).toHaveProperty("en");
    expect(deBundle?.language?.switcher).toHaveProperty("label");
  });

  it("should translate nav.home correctly in German", () => {
    expect(i18n.t("nav.home", { lng: "de" })).toBe("Home");
  });

  it("should translate nav.projects correctly in English", () => {
    expect(i18n.t("nav.projects", { lng: "en" })).toBe("Projects");
  });

  it("should translate login.title correctly in German", () => {
    expect(i18n.t("login.title", { lng: "de" })).toContain("Anmelden");
  });

  it("should translate login.title correctly in English", () => {
    expect(i18n.t("login.title", { lng: "en" })).toContain("Login");
  });
});