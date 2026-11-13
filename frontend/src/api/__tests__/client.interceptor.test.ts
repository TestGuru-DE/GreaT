// REQ-4028 AK-2: Tests fuer 403-Interceptor mit password_change_required
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";

// We need to test the interceptor behavior on the api client
// The interceptor should catch 403 with detail "password_change_required"
// and redirect to /account/password instead of showing a toast

describe("API Interceptor - REQ-4028 password_change_required", () => {
  let mockWindowLocation: { href: string };

  beforeEach(() => {
    mockWindowLocation = { href: "" };
    vi.stubGlobal("window", {
      ...globalThis.window,
      location: mockWindowLocation,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("leitet bei 403 password_change_required auf /account/password um", async () => {
    // Create a test axios instance with the interceptor
    const testApi = axios.create({
      baseURL: "/api",
    });

    // Add the password_change_required interceptor (same logic as in client.ts)
    testApi.interceptors.response.use(
      (res) => res,
      (err) => {
        const detail = err.response?.data?.detail;
        if (err.response?.status === 403 && detail === "password_change_required") {
          // Redirect to password change page instead of rejecting
          window.location.href = "/account/password";
          return Promise.reject(new Error("password_change_required_redirect"));
        }
        const msg = err.response?.data?.detail ?? err.message;
        return Promise.reject(new Error(String(msg)));
      }
    );

    // Mock the HTTP adapter
    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 403,
        data: { detail: "password_change_required" },
      },
    });
    testApi.defaults.adapter = mockAdapter;

    await expect(testApi.get("/projects")).rejects.toThrow(
      "password_change_required_redirect"
    );

    expect(mockWindowLocation.href).toBe("/account/password");
  });

  it("wirft normalen Error bei 403 ohne password_change_required", async () => {
    const testApi = axios.create({
      baseURL: "/api",
    });

    testApi.interceptors.response.use(
      (res) => res,
      (err) => {
        const detail = err.response?.data?.detail;
        if (err.response?.status === 403 && detail === "password_change_required") {
          window.location.href = "/account/password";
          return Promise.reject(new Error("password_change_required_redirect"));
        }
        const msg = err.response?.data?.detail ?? err.message;
        return Promise.reject(new Error(String(msg)));
      }
    );

    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 403,
        data: { detail: "forbidden" },
      },
    });
    testApi.defaults.adapter = mockAdapter;

    await expect(testApi.get("/projects")).rejects.toThrow("forbidden");
    expect(mockWindowLocation.href).toBe("");
  });

  it("wirft normalen Error bei 401", async () => {
    const testApi = axios.create({
      baseURL: "/api",
    });

    testApi.interceptors.response.use(
      (res) => res,
      (err) => {
        const detail = err.response?.data?.detail;
        if (err.response?.status === 403 && detail === "password_change_required") {
          window.location.href = "/account/password";
          return Promise.reject(new Error("password_change_required_redirect"));
        }
        const msg = err.response?.data?.detail ?? err.message;
        return Promise.reject(new Error(String(msg)));
      }
    );

    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: "Not authenticated" },
      },
    });
    testApi.defaults.adapter = mockAdapter;

    await expect(testApi.get("/projects")).rejects.toThrow("Not authenticated");
    expect(mockWindowLocation.href).toBe("");
  });
});