// REQ-1203: Unit-Tests fuer API-Client
import { describe, it, expect } from "vitest";
import { projectsApi, renameApi, reorderApi, logicalConstraintsApi } from "../api/client";

describe("API-Client Exports", () => {
  it("projectsApi hat die erwarteten Methoden", () => {
    expect(typeof projectsApi.list).toBe("function");
    expect(typeof projectsApi.create).toBe("function");
    expect(typeof projectsApi.delete).toBe("function");
  });
  it("renameApi hat die erwarteten Methoden", () => {
    expect(typeof renameApi.category).toBe("function");
    expect(typeof renameApi.value).toBe("function");
  });
  it("reorderApi hat die erwarteten Methoden", () => {
    expect(typeof reorderApi.categories).toBe("function");
  });

  // REQ-6001: logicalConstraintsApi muss /v1/projects/... verwenden
  describe("logicalConstraintsApi (REQ-6001)", () => {
    it("hat alle CRUD-Methoden", () => {
      expect(typeof logicalConstraintsApi.list).toBe("function");
      expect(typeof logicalConstraintsApi.get).toBe("function");
      expect(typeof logicalConstraintsApi.create).toBe("function");
      expect(typeof logicalConstraintsApi.update).toBe("function");
      expect(typeof logicalConstraintsApi.delete).toBe("function");
      expect(typeof logicalConstraintsApi.validate).toBe("function");
    });

    it("verwendet /v1/projects/... URLs (nicht /projects/...)", () => {
      // Pruefe dass die Sourcen /v1/projects enthalten
      const source = logicalConstraintsApi.list.toString();
      expect(source).toContain("/v1/projects/");
    });
  });
});