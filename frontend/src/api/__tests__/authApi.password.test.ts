// REQ-4027 AK-6 / REQ-4028 AK-3: Tests fuer neue Auth-API-Funktionen
import { describe, it, expect, vi, beforeEach } from "vitest";
import { getFirstStartHint, changePassword } from "../authApi";

vi.mock("../client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from "../client";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("authApi.getFirstStartHint - REQ-4027", () => {
  it("gibt { show_hint: true } bei 200 mit true zurueck", async () => {
    (api.get as any).mockResolvedValue({
      data: { show_hint: true },
    });

    const result = await getFirstStartHint();

    expect(api.get).toHaveBeenCalledWith("/auth/first-start-hint");
    expect(result).toEqual({ show_hint: true });
  });

  it("gibt { show_hint: false } bei 200 mit false zurueck", async () => {
    (api.get as any).mockResolvedValue({
      data: { show_hint: false },
    });

    const result = await getFirstStartHint();

    expect(result).toEqual({ show_hint: false });
  });

  it("wirft Error bei 429 Rate-Limit", async () => {
    (api.get as any).mockRejectedValue(new Error("too_many_requests"));

    await expect(getFirstStartHint()).rejects.toThrow("too_many_requests");
  });

  it("wirft Error bei Server-Fehler", async () => {
    (api.get as any).mockRejectedValue(new Error("internal_error"));

    await expect(getFirstStartHint()).rejects.toThrow("internal_error");
  });
});

describe("authApi.changePassword - REQ-4028", () => {
  it("sendet POST /auth/change-password mit korrektem Body", async () => {
    (api.post as any).mockResolvedValue({
      data: { message: "Passwort wurde geaendert" },
    });

    const result = await changePassword("oldpass123!", "newpass123!abc");

    expect(api.post).toHaveBeenCalledWith("/auth/change-password", {
      current_password: "oldpass123!",
      new_password: "newpass123!abc",
    });
    expect(result).toEqual({ message: "Passwort wurde geaendert" });
  });

  it("wirft Error mit detail 'current_password_invalid' bei falschem Passwort", async () => {
    (api.post as any).mockRejectedValue(new Error("current_password_invalid"));

    await expect(changePassword("wrong", "newpass123!abc")).rejects.toThrow(
      "current_password_invalid"
    );
  });

  it("wirft Error mit detail 'password_is_default' bei Standardpasswort", async () => {
    (api.post as any).mockRejectedValue(new Error("password_is_default"));

    await expect(changePassword("old", "changeme123!")).rejects.toThrow(
      "password_is_default"
    );
  });

  it("wirft Error mit detail 'password_too_short' bei zu kurzem Passwort", async () => {
    (api.post as any).mockRejectedValue(new Error("password_too_short"));

    await expect(changePassword("old", "short")).rejects.toThrow(
      "password_too_short"
    );
  });

  it("wirft Error mit detail 'password_too_long' bei zu langem Passwort", async () => {
    (api.post as any).mockRejectedValue(new Error("password_too_long"));

    await expect(changePassword("old", "a".repeat(129))).rejects.toThrow(
      "password_too_long"
    );
  });

  it("wirft Error mit detail 'too_many_attempts' bei 429", async () => {
    (api.post as any).mockRejectedValue(new Error("too_many_attempts"));

    await expect(changePassword("old", "new")).rejects.toThrow(
      "too_many_attempts"
    );
  });

  it("wirft Error bei 401 ohne Token", async () => {
    (api.post as any).mockRejectedValue(new Error("Not authenticated"));

    await expect(changePassword("old", "new")).rejects.toThrow(
      "Not authenticated"
    );
  });
});