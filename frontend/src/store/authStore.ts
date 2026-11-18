// REQ-4001: Zustand Store fuer Authentifizierungszustand
// REQ-4028: passwordChangeRequired State und changePassword Action
// REQ-6005: Sprachpraferenz
import { create } from "zustand";
import { authApi } from "../api/authApi";
import type { UserInfo } from "../api/authApi";

interface AuthState {
  user: UserInfo | null;
  isLoading: boolean;
  error: string | null;
  passwordChangeRequired: boolean;
  language: "de" | "en" | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;

  refresh: () => Promise<void>;
  setPasswordChangeRequired: (value: boolean) => void;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  setLanguage: (lang: "de" | "en") => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  error: null,
  passwordChangeRequired: false,
  language: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.login(username, password);
      // Nach erfolgreichem Login: User-Info laden
      const user = await authApi.me();
      // REQ-4028 AK-1: password_change_required aus /auth/me auslesen
      const requiresChange = !!user.password_change_required;
      // REQ-6005: Sprache vom Server laden
      const lang = user.language as "de" | "en" | null;
      set({ user, isLoading: false, passwordChangeRequired: requiresChange, language: lang });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      set({ error: message, isLoading: false });
      throw e;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null, error: null, passwordChangeRequired: false });
    }
  },

  loadUser: async () => {
    try {
      const user = await authApi.me();
      // REQ-4028 AK-1: password_change_required aus /auth/me auslesen
      const requiresChange = !!user.password_change_required;
      // REQ-6005: Sprache vom Server laden
      const lang = user.language as "de" | "en" | null;
      set({ user, passwordChangeRequired: requiresChange, language: lang });
    } catch {
      set({ user: null, passwordChangeRequired: false, language: null });
    }
  },

  
  // clearError: () => set({ error: null }),

  refresh: async () => {
    try {
      await authApi.refresh();
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
      await authApi.changePassword(currentPassword, newPassword);
      // REQ-4028 AK-6: Bei erfolgreichem Wechsel Flag loeschen
      set({ isLoading: false, passwordChangeRequired: false });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      set({ error: message, isLoading: false });
      throw e;
    }
  },

  // REQ-6005: Sprachpraferenz speichern
  setLanguage: async (lang: "de" | "en") => {
    try {
      await authApi.setLanguage(lang);
      set({ language: lang });
    } catch {
      // Silent fail – Sprache funktioniert lokal trotzdem
      throw new Error("Failed to save language preference");
    }
  },
}));