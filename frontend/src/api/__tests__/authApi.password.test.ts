// REQ-4027 AK-6 / REQ-4028 AK-3: Tests fuer neue Auth-API-Funktionen
import { describe, it, expect, vi, beforeEach } from "vitest";
import { getFirstStartHint, changePassword } from "../authApi";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("authApi.getFirstStartHint - REQ-4027", () => {
  it("gibt { show_hint: true } bei 200 mit true zurueck", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ show_hint: true }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await getFirstStartHint();

    expect(mockedFetch).toHaveBeenCalledWith("/auth/first-start-hint", {
      credentials: "include",
    });
    expect(result).toEqual({ show_hint: true });
  });

  it("gibt { show_hint: false } bei 200 mit false zurueck", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ show_hint: false }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await getFirstStartHint();

    expect(result).toEqual({ show_hint: false });
  });

  it("wirft Error bei 429 Rate-Limit", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve({ detail: "too_many_requests" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(getFirstStartHint()).rejects.toThrow("too_many_requests");
  });

  it("wirft Error bei Server-Fehler", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "internal_error" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(getFirstStartHint()).rejects.toThrow("internal_error");
  });
});

describe("authApi.changePassword - REQ-4028", () => {
  it("sendet POST /auth/change-password mit korrektem Body", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: "Passwort wurde geaendert" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await changePassword("oldpass123!", "newpass123!abc");

    expect(mockedFetch).toHaveBeenCalledWith("/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_password: "oldpass123!",
        new_password: "newpass123!abc",
      }),
      credentials: "include",
    });
    expect(result).toEqual({ message: "Passwort wurde geaendert" });
  });

  it("wirft Error mit detail 'current_password_invalid' bei falschem Passwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "current_password_invalid" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("wrong", "newpass123!abc")).rejects.toThrow(
      "current_password_invalid"
    );
  });

  it("wirft Error mit detail 'password_is_default' bei Standardpasswort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "password_is_default" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("old", "changeme123!")).rejects.toThrow(
      "password_is_default"
    );
  });

  it("wirft Error mit detail 'password_too_short' bei zu kurzem Passwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "password_too_short" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("old", "short")).rejects.toThrow(
      "password_too_short"
    );
  });

  it("wirft Error mit detail 'password_too_long' bei zu langem Passwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "password_too_long" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("old", "a".repeat(129))).rejects.toThrow(
      "password_too_long"
    );
  });

  it("wirft Error mit detail 'too_many_attempts' bei 429", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve({ detail: "too_many_attempts" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("old", "new")).rejects.toThrow(
      "too_many_attempts"
    );
  });

  it("wirft Error bei 401 ohne Token", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Not authenticated" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(changePassword("old", "new")).rejects.toThrow(
      "Not authenticated"
    );
  });
});