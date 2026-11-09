// REQ-4001: Zustand Store fuer Authentifizierungszustand
// REQ-4028: passwordChangeRequired State und changePassword Action
import { create } from "zustand";
import { login as apiLogin, logout as apiLogout, me as apiMe, refreshToken, changePassword as apiChangePassword } from "../api/authApi";
import type { UserInfo } from "../api/authApi";

interface AuthState {
  user: UserInfo | null;
  isLoading: boolean;
  error: string | null;
  passwordChangeRequired: boolean;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  clearError: () => void;
  refresh: () => Promise<void>;
  setPasswordChangeRequired: (value: boolean) => void;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  error: null,
  passwordChangeRequired: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiLogin(username, password);
      // Nach erfolgreichem Login: User-Info laden
      const user = await apiMe();
      // REQ-4028 AK-1: password_change_required aus /auth/me auslesen
      const requiresChange = !!user.password_change_required;
      set({ user, isLoading: false, passwordChangeRequired: requiresChange });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      set({ error: message, isLoading: false });
      throw e;
    }
  },

  logout: async () => {
    try {
      await apiLogout();
    } finally {
      set({ user: null, error: null, passwordChangeRequired: false });
    }
  },

  loadUser: async () => {
    try {
      const user = await apiMe();
      // REQ-4028 AK-1: password_change_required aus /auth/me auslesen
      const requiresChange = !!user.password_change_required;
      set({ user, passwordChangeRequired: requiresChange });
    } catch {
      set({ user: null, passwordChangeRequired: false });
    }
  },

  clearError: () => set({ error: null }),

  refresh: async () => {
    try {
      await refreshToken();
    } catch {
      // Refresh fehlgeschlagen - User wird ausgeloggt
      set({ user: null, passwordChangeRequired: false });
    }
  },

  setPasswordChangeRequired: (value: boolean) => set({ passwordChangeRequired: value }),

  // REQ-4028 AK-3: Selbst-Passwortwechsel
  changePassword: async (currentPassword: string, newPassword: string) => {
    set({ isLoading: true, error: null });
    try {
      await apiChangePassword(currentPassword, newPassword);
      // REQ-4028 AK-6: Bei erfolgreichem Wechsel Flag loeschen
      set({ isLoading: false, passwordChangeRequired: false });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      set({ error: message, isLoading: false });
      throw e;
    }
  },
}));