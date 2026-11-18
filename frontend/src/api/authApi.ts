// REQ-4001: Auth-API-Calls (JWT-Tokens in httpOnly-Cookies)
// Cookies werden automatisch vom Browser mitgesendet (withCredentials: true)
import { authClient } from "./client";

export interface AuthResponse {
  user_id: number;
  username: string;
  role: string;
  message: string;
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  password_change_required?: boolean;
  language?: "de" | "en" | null;
}

export const authApi = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    const { data } = await authClient.post<AuthResponse>("/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },

  logout: async (): Promise<void> => {
    await authClient.post("/logout");
  },

  refresh: async (): Promise<void> => {
    await authClient.post("/refresh");
  },

  me: async (): Promise<UserInfo> => {
    const { data } = await authClient.get<UserInfo>("/me");
    return data;
  },

  // REQ-4027 AK-6: Statusabfrage fuer Erststart-Hinweis (ohne Authentifizierung)
  getFirstStartHint: async (): Promise<{ show_hint: boolean }> => {
    const { data } = await authClient.get<{ show_hint: boolean }>("/first-start-hint");
    return data;
  },

  // REQ-4028 AK-3: Selbst-Passwortwechsel fuer alle Rollen
  changePassword: async (
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> => {
    const { data } = await authClient.post<{ message: string }>("/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return data;
  },

  // REQ-6005: Sprachpraferenz speichern
  setLanguage: async (lang: "de" | "en"): Promise<{ language: string | null }> => {
    const { data } = await authClient.put<{ language: string | null }>("/me/preferences", {
      language: lang,
    });
    return data;
  },
};

// Legacy exports for backwards compatibility during migration
export const login = authApi.login;
export const logout = authApi.logout;
export const refreshToken = authApi.refresh;
export const me = authApi.me;
export const getFirstStartHint = authApi.getFirstStartHint;
export const changePassword = authApi.changePassword;