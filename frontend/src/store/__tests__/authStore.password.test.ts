// REQ-4028 AK-1: Tests fuer passwordChangeRequired in authStore
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

describe("authStore - REQ-4028 passwordChangeRequired", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      user: null,
      isLoading: false,
      error: null,
      passwordChangeRequired: false,
    });
  });

  describe("passwordChangeRequired state", () => {
    it("ist initial false", () => {
      const { result } = renderHook(() => useAuthStore());
      expect(result.current.passwordChangeRequired).toBe(false);
    });

    it("wird durch setPasswordChangeRequired(true) auf true gesetzt", () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.getState().setPasswordChangeRequired(true);
      });

      expect(result.current.passwordChangeRequired).toBe(true);
    });

    it("wird durch setPasswordChangeRequired(false) auf false gesetzt", () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.getState().setPasswordChangeRequired(true);
      });

      act(() => {
        useAuthStore.getState().setPasswordChangeRequired(false);
      });

      expect(result.current.passwordChangeRequired).toBe(false);
    });
  });

  describe("login mit password_change_required", () => {
    it("setzt passwordChangeRequired=true wenn API es meldet", async () => {
      vi.mocked(authApi.login).mockResolvedValue({
        user_id: 1,
        username: "admin",
        role: "admin",
        message: "Login erfolgreich",
        password_change_required: true,
      });
      vi.mocked(authApi.me).mockResolvedValue({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
        password_change_required: true,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login("admin", "changeme123!");
      });

      expect(result.current.passwordChangeRequired).toBe(true);
    });

    it("setzt passwordChangeRequired=false wenn API es nicht meldet", async () => {
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

      expect(result.current.passwordChangeRequired).toBe(false);
    });
  });

  describe("loadUser mit password_change_required", () => {
    it("setzt passwordChangeRequired=true wenn /auth/me es meldet", async () => {
      vi.mocked(authApi.me).mockResolvedValue({
        id: 1,
        username: "admin",
        role: "admin",
        is_active: true,
        password_change_required: true,
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUser();
      });

      expect(result.current.passwordChangeRequired).toBe(true);
    });

    it("setzt passwordChangeRequired=false wenn /auth/me es nicht meldet", async () => {
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

      expect(result.current.passwordChangeRequired).toBe(false);
    });
  });

  describe("changePassword", () => {
    it("setzt passwordChangeRequired=false nach erfolgreichem Wechsel", async () => {
      vi.mocked(authApi.changePassword).mockResolvedValue({
        message: "Passwort wurde geaendert",
      });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.getState().setPasswordChangeRequired(true);
      });

      await act(async () => {
        await result.current.changePassword("oldpass123!", "newpass123!abc");
      });

      expect(result.current.passwordChangeRequired).toBe(false);
    });

    it("wirft Error bei fehlgeschlagenem Wechsel und laesst Flag unveraendert", async () => {
      vi.mocked(authApi.changePassword).mockRejectedValue(
        new Error("current_password_invalid")
      );

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.getState().setPasswordChangeRequired(true);
      });

      await act(async () => {
        try {
          await result.current.changePassword("wrong", "newpass123!abc");
        } catch {
          // expected
        }
      });

      expect(result.current.passwordChangeRequired).toBe(true);
      expect(result.current.error).toBe("current_password_invalid");
    });
  });
});