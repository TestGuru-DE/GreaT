// REQ-1203: Unit-Tests fuer API-Client
import { describe, it, expect } from "vitest";
import { projectsApi, renameApi, reorderApi } from "../api/client";

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
});