// B-43: Sitzung wird auch bei /auth/*-Aufrufen (z. B. /auth/me beim Neuladen) per Refresh erneuert.
// N-01: Fehler der Auth-Endpunkte kommen als ApiError mit dem Server-Code als Nachricht an.
// Getestet wird der echte Client (keine nachgebauten Interceptoren); nur der HTTP-Adapter ist ersetzt.
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { AxiosAdapter, InternalAxiosRequestConfig } from "axios";
import api, { authClient } from "../client";
import { authApi } from "../authApi";
import { ApiError } from "../ApiError";

type Reply = { status: number; data?: unknown };
type Route = (config: InternalAxiosRequestConfig) => Reply;

function adapterFor(route: Route): AxiosAdapter & ReturnType<typeof vi.fn> {
  return vi.fn(async (config: InternalAxiosRequestConfig) => {
    const { status, data } = route(config);
    const response = { status, data, statusText: String(status), headers: {}, config };
    if (status >= 400) {
      const error = Object.assign(new Error(`Request failed with status code ${status}`), {
        isAxiosError: true, config, response,
      });
      throw error;
    }
    return response;
  }) as unknown as AxiosAdapter & ReturnType<typeof vi.fn>;
}

function urlOf(config: InternalAxiosRequestConfig): string {
  return `${config.baseURL ?? ""}${config.url ?? ""}`;
}

describe("Sitzungs-Erneuerung und Fehler der Auth-Endpunkte", () => {
  const originalApiAdapter = api.defaults.adapter;
  const originalAuthAdapter = authClient.defaults.adapter;
  let location: { href: string };

  beforeEach(() => {
    location = { href: "" };
    vi.stubGlobal("location", location);
  });

  afterEach(() => {
    api.defaults.adapter = originalApiAdapter;
    authClient.defaults.adapter = originalAuthAdapter;
    vi.unstubAllGlobals();
  });

  function install(route: Route) {
    const adapter = adapterFor(route);
    api.defaults.adapter = adapter;
    authClient.defaults.adapter = adapter;
    return adapter;
  }

  it("B-43: /auth/me mit abgelaufenem Access-Token wird nach Refresh wiederholt", async () => {
    let refreshed = false;
    const adapter = install((config) => {
      const url = urlOf(config);
      if (url === "/auth/refresh") { refreshed = true; return { status: 200, data: {} }; }
      if (url === "/auth/me") {
        return refreshed
          ? { status: 200, data: { id: 1, username: "anna", role: "editor", is_active: true } }
          : { status: 401, data: { detail: "Token abgelaufen" } };
      }
      return { status: 404 };
    });

    await expect(authApi.me()).resolves.toMatchObject({ username: "anna" });
    const calls = adapter.mock.calls.map(([c]) => urlOf(c as InternalAxiosRequestConfig));
    expect(calls).toEqual(["/auth/me", "/auth/refresh", "/auth/me"]);
  });

  it("B-43: scheitert der Refresh, wird nicht endlos wiederholt", async () => {
    const adapter = install((config) => {
      const url = urlOf(config);
      if (url === "/auth/refresh") return { status: 401, data: { detail: "Ungültiger Refresh-Token" } };
      return { status: 401, data: { detail: "Token abgelaufen" } };
    });

    await expect(api.get("/projects")).rejects.toBeInstanceOf(ApiError);
    const calls = adapter.mock.calls.map(([c]) => urlOf(c as InternalAxiosRequestConfig));
    expect(calls.filter((u) => u === "/auth/refresh")).toHaveLength(1);
    expect(calls.filter((u) => u === "/api/projects")).toHaveLength(1);
    expect(location.href).toBe("/login?reason=session_expired");
  });

  it("B-43: parallele 401-Antworten teilen sich einen Refresh", async () => {
    let refreshed = false;
    const adapter = install((config) => {
      const url = urlOf(config);
      if (url === "/auth/refresh") { refreshed = true; return { status: 200, data: {} }; }
      return refreshed ? { status: 200, data: [] } : { status: 401, data: { detail: "Token abgelaufen" } };
    });

    await Promise.all([api.get("/projects"), api.get("/dataclasses"), authApi.me()]);
    const calls = adapter.mock.calls.map(([c]) => urlOf(c as InternalAxiosRequestConfig));
    expect(calls.filter((u) => u === "/auth/refresh")).toHaveLength(1);
  });

  it("B-43: Login-Fehler loesen keinen Refresh aus", async () => {
    const adapter = install(() => ({ status: 401, data: { detail: "Ungültige Anmeldedaten" } }));
    await expect(authApi.login("anna", "falsch")).rejects.toThrow("Ungültige Anmeldedaten");
    expect(adapter).toHaveBeenCalledTimes(1);
  });

  it("N-01: Passwortwechsel liefert den Server-Code als Fehlermeldung", async () => {
    install(() => ({ status: 400, data: { detail: "password_too_common" } }));
    const error = await authApi.changePassword("alt-passwort-1", "password1234").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(400);
    expect(error.message).toBe("password_too_common");
  });
});
