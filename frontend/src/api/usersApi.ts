// REQ-4025: API-Calls fuer Benutzerverwaltung
// Alle Endpunkte erfordern Admin-Rechte, außer Passwort-aendern (User fuer sich selbst)
import api from "./client";

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

export const usersApi = {
  list: async (): Promise<AppUser[]> => {
    const { data } = await api.get<AppUser[]>("/users");
    return data;
  },

  create: async (data: CreateUserRequest): Promise<AppUser> => {
    const { data: result } = await api.post<AppUser>("/users", data);
    return result;
  },

  update: async (id: number, data: UpdateUserRequest): Promise<void> => {
    await api.put(`/users/${id}`, data);
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
  },

  // Umbenannt von changePassword zu adminSetPassword
  adminSetPassword: async (id: number, newPassword: string): Promise<void> => {
    await api.put(`/users/${id}/password`, { password: newPassword });
  },
};

// Legacy export for backwards compatibility during migration
export const fetchUsers = usersApi.list;
export const createUser = usersApi.create;
export const updateUser = usersApi.update;
export const deleteUser = usersApi.delete;

export const changePassword = usersApi.adminSetPassword;