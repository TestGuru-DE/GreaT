// REQ-4001: Unit-Tests fuer Auth-API-Client (axios-basiert)
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { authApi } from "./authApi";
import * as clientModule from "./client";

vi.mock("./client", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
  authClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockAuthClient = vi.mocked(clientModule.authClient);

describe("authApi.login", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sendet POST /auth/login mit x-www-form-urlencoded", async () => {
    const mockResponse = {
      user_id: 1,
      username: "admin",
      role: "admin",
      message: "Login erfolgreich",
    };

    mockAuthClient.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await authApi.login("admin", "password123");

    expect(mockAuthClient.post).toHaveBeenCalledWith("/login", expect.any(URLSearchParams), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    expect(result).toEqual(mockResponse);
  });

  it("wirft Error bei 401 Antwort", async () => {
    const error = new Error("Ungueltige Anmeldedaten");
    (error as any).response = { status: 401, data: { detail: "Ungueltige Anmeldedaten" } };
    mockAuthClient.post.mockRejectedValueOnce(error);

    await expect(authApi.login("admin", "wrong")).rejects.toThrow();
  });
});

describe("authApi.logout", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sendet POST /auth/logout", async () => {
    mockAuthClient.post.mockResolvedValueOnce({ data: undefined });

    await authApi.logout();

    expect(mockAuthClient.post).toHaveBeenCalledWith("/logout");
  });
});

describe("authApi.refresh", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sendet POST /auth/refresh", async () => {
    mockAuthClient.post.mockResolvedValueOnce({ data: undefined });

    await authApi.refresh();

    expect(mockAuthClient.post).toHaveBeenCalledWith("/refresh");
  });
});

describe("authApi.me", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sendet GET /auth/me und gibt UserInfo zurueck", async () => {
    const mockUser = {
      id: 1,
      username: "admin",
      role: "admin",
      is_active: true,
    };

    mockAuthClient.get.mockResolvedValueOnce({ data: mockUser });

    const result = await authApi.me();

    expect(mockAuthClient.get).toHaveBeenCalledWith("/me");
    expect(result).toEqual(mockUser);
  });
});
