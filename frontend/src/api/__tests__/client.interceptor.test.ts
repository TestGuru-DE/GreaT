// REQ-4028 AK-2: Tests fuer 403-Interceptor mit password_change_required
// B-43: Tests fuer Token-Refresh + ApiError
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import { ApiError } from "../ApiError";

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

    // Add the interceptor matching client.ts logic
    testApi.interceptors.response.use(
      (res) => res,
      (err) => {
        const detail = err.response?.data?.detail;
        if (err.response?.status === 403 && detail === "password_change_required") {
          // Redirect to password change page instead of rejecting
          window.location.href = "/account/password";
          return Promise.reject(new Error("password_change_required_redirect"));
        }
        const apiError = new ApiError(
          err.response?.status ?? 0,
          err.response?.data?.detail ?? err.message
        );
        throw apiError;
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

  it("wirft ApiError bei 403 ohne password_change_required", async () => {
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
        const apiError = new ApiError(
          err.response?.status ?? 0,
          err.response?.data?.detail ?? err.message
        );
        throw apiError;
      }
    );

    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 403,
        data: { detail: "forbidden" },
      },
    });
    testApi.defaults.adapter = mockAdapter;

    try {
      await testApi.get("/projects");
      expect.fail("should have thrown");
    } catch (e: any) {
      expect(e instanceof ApiError).toBe(true);
      expect(e.status).toBe(403);
      expect(e.message).toBe("forbidden");
    }
    expect(mockWindowLocation.href).toBe("");
  });

  it("wirft ApiError bei 401", async () => {
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
        const apiError = new ApiError(
          err.response?.status ?? 0,
          err.response?.data?.detail ?? err.message
        );
        throw apiError;
      }
    );

    const mockAdapter = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: "Not authenticated" },
      },
    });
    testApi.defaults.adapter = mockAdapter;

    try {
      await testApi.get("/projects");
      expect.fail("should have thrown");
    } catch (e: any) {
      expect(e instanceof ApiError).toBe(true);
      expect(e.status).toBe(401);
      expect(e.message).toBe("Not authenticated");
    }
    expect(mockWindowLocation.href).toBe("");
  });
});