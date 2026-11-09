// REQ-4025: API-Calls fuer Benutzerverwaltung
// Alle Endpunkte erfordern Admin-Rechte, außer Passwort-aendern (User fuer sich selbst)

export interface AppUser {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
}

export interface CreateUserRequest {
  username: string;
  password: string;
  role: string;
}

export interface UpdateUserRequest {
  role?: string;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  password: string;
}

export async function fetchUsers(): Promise<AppUser[]> {
  const response = await fetch("/api/users", {
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Fehler beim Laden der Nutzer" }));
    throw new Error(error.detail || "Fehler beim Laden der Nutzer");
  }

  return response.json();
}

export async function createUser(data: CreateUserRequest): Promise<AppUser> {
  const response = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Fehler beim Erstellen des Nutzers" }));
    throw new Error(error.detail || "Fehler beim Erstellen des Nutzers");
  }

  return response.json();
}

export async function updateUser(id: number, data: UpdateUserRequest): Promise<void> {
  const response = await fetch(`/api/users/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Fehler beim Aendern des Nutzers" }));
    throw new Error(error.detail || "Fehler beim Aendern des Nutzers");
  }
}

export async function deleteUser(id: number): Promise<void> {
  const response = await fetch(`/api/users/${id}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Fehler beim Loeschen des Nutzers" }));
    throw new Error(error.detail || "Fehler beim Loeschen des Nutzers");
  }
}

export async function changePassword(id: number, newPassword: string): Promise<void> {
  const response = await fetch(`/api/users/${id}/password`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: newPassword }),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Fehler beim Aendern des Passworts" }));
    throw new Error(error.detail || "Fehler beim Aendern des Passworts");
  }
}