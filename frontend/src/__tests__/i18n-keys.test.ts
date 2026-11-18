// REQ-6005: Test fuer Vollstaendigkeit der Uebersetzungsschluessel
import { describe, it, expect } from "vitest";
import translationDE from "../i18n/de.json";
import translationEN from "../i18n/en.json";

function getFlatKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  const keys: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      keys.push(...getFlatKeys(value as Record<string, unknown>, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

describe("REQ-6005: Translation Key Completeness", () => {
  it("de.json and en.json should have identical keys", () => {
    const deKeys = new Set(getFlatKeys(translationDE));
    const enKeys = new Set(getFlatKeys(translationEN));

    const missingInEN = [...deKeys].filter((k) => !enKeys.has(k));
    const missingInDE = [...enKeys].filter((k) => !deKeys.has(k));

    if (missingInEN.length > 0) {
      console.error("Missing in en.json:", missingInEN);
    }
    if (missingInDE.length > 0) {
      console.error("Missing in de.json:", missingInDE);
    }

    expect(missingInEN).toHaveLength(0);
    expect(missingInDE).toHaveLength(0);
  });

  it("should have all required nav keys", () => {
    const deKeys = getFlatKeys(translationDE);
    const requiredNavKeys = [
      "nav.home",
      "nav.projects",
      "nav.dataclasses",
      "nav.generations",
      "nav.settings",
      "nav.changePassword",
      "nav.help",
      "nav.apiDocs",
      "nav.logout",
      "nav.logoutTitle",
    ];

    for (const key of requiredNavKeys) {
      expect(deKeys).toContain(key);
    }
  });

  it("should have all required login keys", () => {
    const deKeys = getFlatKeys(translationDE);
    const requiredLoginKeys = [
      "login.title",
      "login.username",
      "login.password",
      "login.defaultUser",
      "login.defaultPassword",
      "login.submitLoading",
      "login.submit",
    ];

    for (const key of requiredLoginKeys) {
      expect(deKeys).toContain(key);
    }
  });

  it("should have language switcher keys", () => {
    const deKeys = getFlatKeys(translationDE);
    expect(deKeys).toContain("language.switcher.de");
    expect(deKeys).toContain("language.switcher.en");
    expect(deKeys).toContain("language.switcher.label");
  });

  // REQ-6013: Model Export/Import i18n keys
  it("should have all required modelExport keys", () => {
    const deKeys = getFlatKeys(translationDE);
    const requiredExportKeys = [
      "modelExport.button",
      "modelExport.yaml",
      "modelExport.json",
      "modelExport.loading",
      "modelExport.error",
      "modelExport.success",
    ];

    for (const key of requiredExportKeys) {
      expect(deKeys).toContain(key);
    }
  });

  it("should have all required modelImport keys", () => {
    const deKeys = getFlatKeys(translationDE);
    const requiredImportKeys = [
      "modelImport.title",
      "modelImport.button",
      "modelImport.fileSelect",
      "modelImport.dragDrop",
      "modelImport.acceptedFormats",
      "modelImport.mode",
      "modelImport.modeNew",
      "modelImport.modeUpdate",
      "modelImport.projectSelect",
      "modelImport.previewTitle",
      "modelImport.previewLoading",
      "modelImport.noChanges",
      "modelImport.added",
      "modelImport.modified",
      "modelImport.removed",
      "modelImport.categories",
      "modelImport.values",
      "modelImport.rules",
      "modelImport.warning",
      "modelImport.confirm",
      "modelImport.confirmLoading",
      "modelImport.cancel",
      "modelImport.errorFileTooLarge",
      "modelImport.errorInvalidFormat",
      "modelImport.errorImport",
      "modelImport.errorValidation",
      "modelImport.errorPreview",
      "modelImport.successNew",
      "modelImport.successUpdate",
    ];

    for (const key of requiredImportKeys) {
      expect(deKeys).toContain(key);
    }
  });
});