// REQ-4027 AK-7: Tests fuer defaultCredentials
import { describe, it, expect } from "vitest";
import { DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD } from "../defaultCredentials";

describe("defaultCredentials - REQ-4027", () => {
  it("DEFAULT_ADMIN_USERNAME ist 'admin'", () => {
    expect(DEFAULT_ADMIN_USERNAME).toBe("admin");
  });

  it("DEFAULT_ADMIN_PASSWORD ist 'changeme123!'", () => {
    // AK-7: Wert muss mit Backend-Konstante DEFAULT_ADMIN_PASSWORD uebereinstimmen
    expect(DEFAULT_ADMIN_PASSWORD).toBe("changeme123!");
  });

  it("DEFAULT_ADMIN_PASSWORD hat mindestens 12 Zeichen (REQ-4028 AK-4)", () => {
    expect(DEFAULT_ADMIN_PASSWORD.length).toBeGreaterThanOrEqual(12);
  });
});