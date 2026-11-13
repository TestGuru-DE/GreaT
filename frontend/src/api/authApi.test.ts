// REQ-4001: Unit-Tests fuer Auth-API-Client
import { describe, it, expect, vi, beforeEach } from "vitest";
import { login, logout, refreshToken, me } from "../api/authApi";

// Mock fetch globally
beforeEach(() => {
  vi.restoreAllMocks();
});

describe("authApi.login", () => {
  it("sendet POST /auth/login mit x-www-form-urlencoded", async () => {
    const mockResponse = {
      user_id: 1,
      username: "admin",
      role: "admin",
      message: "Login erfolgreich",
    };

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await login("admin", "password123");

    expect(mockedFetch).toHaveBeenCalledWith("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: expect.any(URLSearchParams),
      credentials: "include",
    });
    expect(result).toEqual(mockResponse);
  });

  it("wirft Error bei 401 Antwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: "Ungueltige Anmeldedaten" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(login("admin", "wrong")).rejects.toThrow("Ungueltige Anmeldedaten");
  });

  it("wirft generischen Error bei nicht-JSON-Antwort", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.reject(new Error("no json")),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(login("admin", "wrong")).rejects.toThrow("Login fehlgeschlagen");
  });
});

describe("authApi.logout", () => {
  it("sendet POST /auth/logout mit credentials", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await logout();

    expect(mockedFetch).toHaveBeenCalledWith("/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  });

  it("wirft Error bei fehlgeschlagenem Logout", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(logout()).rejects.toThrow("Logout fehlgeschlagen");
  });
});

describe("authApi.refreshToken", () => {
  it("sendet POST /auth/refresh mit credentials", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await refreshToken();

    expect(mockedFetch).toHaveBeenCalledWith("/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
  });

  it("wirft Error bei fehlgeschlagenem Refresh", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(refreshToken()).rejects.toThrow("Token-Refresh fehlgeschlagen");
  });
});

describe("authApi.me", () => {
  it("sendet GET /auth/me und gibt UserInfo zurueck", async () => {
    const mockUser = {
      id: 1,
      username: "admin",
      role: "admin",
      is_active: true,
    };

    const mockedFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser),
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await me();

    expect(mockedFetch).toHaveBeenCalledWith("/auth/me", {
      credentials: "include",
    });
    expect(result).toEqual(mockUser);
  });

  it("wirft Error bei 401", async () => {
    const mockedFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: "Nicht authentifiziert" }),
    });
    vi.stubGlobal("fetch", mockedFetch);

    await expect(me()).rejects.toThrow("Nicht authentifiziert");
  });
});