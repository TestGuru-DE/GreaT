// REQ-4001: Unit-Tests fuer AuthStore
import { renderHook, act } from "@testing-library/react";
import { useAuthStore } from "../authStore";
import * as authApi from "../../api/authApi";

vi.mock("../../api/authApi", () => ({
  login: vi.fn(),
  logout: vi.fn(),
  me: vi.fn(),
  refreshToken: vi.fn(),
  getFirstStartHint: vi.fn(),
  changePassword: vi.fn(),
}));

describe("authStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useAuthStore.setState({
      user: null,
      isLoading: false,
      error: null,
      passwordChangeRequired: false,
    });
  });

  describe("login", () => {
    it("setzt isLoading=true und dann user nach erfolgreichem Login", async () => {
      vi.mocked(authApi.login).mockResolvedValue({
        user_id: 1,
        username: "admin",
        role: "admin",
        message: "Login erfolgreich",
      });
      vi.mocked(authApi.me).mockResolvedValue({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login("admin", "password123");
      });

      expect(authApi.login).toHaveBeenCalledWith("admin", "password123");
      expect(authApi.me).toHaveBeenCalled();
      expect(result.current.user).toEqual({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
      });
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it("setzt error bei fehlgeschlagenem Login", async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error("Ungueltige Anmeldedaten"));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login("admin", "wrong");
        } catch {
          // expected
        }
      });

      expect(result.current.error).toBe("Ungueltige Anmeldedaten");
      expect(result.current.isLoading).toBe(false);
      expect(result.current.user).toBe(null);
    });

    it("wirft den Error weiter", async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error("Ungueltige Anmeldedaten"));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await expect(result.current.login("admin", "wrong")).rejects.toThrow(
          "Ungueltige Anmeldedaten"
        );
      });
    });
  });

  describe("logout", () => {
    it("setzt user=null nach Logout", async () => {
      vi.mocked(authApi.logout).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuthStore());

      // Setze zuerst einen User
      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            username: "admin",
            role: "admin",
            is_active: true,
          },
        });
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(authApi.logout).toHaveBeenCalled();
      expect(result.current.user).toBe(null);
      expect(result.current.error).toBe(null);
    });

    it("setzt user=null auch wenn Logout-API fehlschlaegt", async () => {
      vi.mocked(authApi.logout).mockRejectedValue(new Error("Server Error"));

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            username: "admin",
            role: "admin",
            is_active: true,
          },
        });
      });

      await act(async () => {
        try {
          await result.current.logout();
        } catch {
          // Error wird weitergeworfen, aber finally setzt user=null
        }
      });

      expect(result.current.user).toBe(null);
    });
  });

  describe("loadUser", () => {
    it("laedt User-Info bei gueltiger Session", async () => {
      vi.mocked(authApi.me).mockResolvedValue({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUser();
      });

      expect(result.current.user).toEqual({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
      });
    });

    it("setzt user=null bei ungueltiger Session", async () => {
      vi.mocked(authApi.me).mockRejectedValue(new Error("Nicht authentifiziert"));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUser();
      });

      expect(result.current.user).toBe(null);
    });
  });

  describe("clearError", () => {
    it("setzt error auf null", () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({ error: "Some error" });
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBe(null);
    });
  });

  describe("refresh", () => {
    it("ruft refreshToken auf und behaelt User bei Erfolg", async () => {
      vi.mocked(authApi.refreshToken).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            username: "admin",
            role: "admin",
            is_active: true,
          },
        });
      });

      await act(async () => {
        await result.current.refresh();
      });

      expect(authApi.refreshToken).toHaveBeenCalled();
      expect(result.current.user).not.toBe(null);
    });

    it("setzt user=null bei fehlgeschlagenem Refresh", async () => {
      vi.mocked(authApi.refreshToken).mockRejectedValue(new Error("Token expired"));

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            username: "admin",
            role: "admin",
            is_active: true,
          },
        });
      });

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.user).toBe(null);
    });
  });
});