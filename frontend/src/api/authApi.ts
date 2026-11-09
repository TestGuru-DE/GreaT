// REQ-4001: Auth-API-Calls (JWT-Tokens in httpOnly-Cookies)
// Cookies werden automatisch vom Browser mitgesendet (credentials: "include")

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
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
    credentials: "include", // wichtig fuer httpOnly-Cookies
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login fehlgeschlagen" }));
    throw new Error(error.detail || "Login fehlgeschlagen");
  }

  return response.json();
}

export async function logout(): Promise<void> {
  const response = await fetch("/auth/logout", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Logout fehlgeschlagen");
  }
}

export async function refreshToken(): Promise<void> {
  const response = await fetch("/auth/refresh", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Token-Refresh fehlgeschlagen");
  }
}

export async function me(): Promise<UserInfo> {
  const response = await fetch("/auth/me", {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Nicht authentifiziert");
  }

  return response.json();
}

// REQ-4027 AK-6: Statusabfrage fuer Erststart-Hinweis (ohne Authentifizierung)
// Liefert ausschliesslich { show_hint: boolean }. Keine Passwoerter oder Nutzerdaten.
export interface FirstStartHintResponse {
  show_hint: boolean;
}

export async function getFirstStartHint(): Promise<FirstStartHintResponse> {
  const response = await fetch("/auth/first-start-hint", {
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Hinweis konnte nicht abgerufen werden" }));
    throw new Error(error.detail || "Hinweis konnte nicht abgerufen werden");
  }

  return response.json();
}

// REQ-4028 AK-3: Selbst-Passwortwechsel fuer alle Rollen
export interface ChangePasswordResponse {
  message: string;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<ChangePasswordResponse> {
  const response = await fetch("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Passwortwechsel fehlgeschlagen" }));
    throw new Error(error.detail || "Passwortwechsel fehlgeschlagen");
  }

  return response.json();
}