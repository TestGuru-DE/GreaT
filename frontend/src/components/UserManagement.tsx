// REQ-4025: Benutzerverwaltung (Admin-only)
import { useState, useEffect } from "react";
import { useAuthStore } from "../store/authStore";
import {
  fetchUsers,
  createUser,
  updateUser,
  deleteUser,
  changePassword,
  type AppUser,
} from "../api/usersApi";

const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number];

export default function UserManagement() {
  const user = useAuthStore((s) => s.user);

  // Nur fuer Admins sichtbar
  if (!user || user.role !== "admin") {
    return null;
  }

  const [users, setUsers] = useState<AppUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog-Zustaende
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState<AppUser | null>(null);
  const [showPasswordDialog, setShowPasswordDialog] = useState<AppUser | null>(null);

  // Formular-Daten
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<Role>("viewer");
  const [changePasswordValue, setChangePasswordValue] = useState("");

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  async function handleCreateUser() {
    if (!newUsername || !newPassword) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await createUser({
        username: newUsername,
        password: newPassword,
        role: newRole,
      });
      setNewUsername("");
      setNewPassword("");
      setNewRole("viewer");
      setShowCreateDialog(false);
      setSuccess("Nutzer erfolgreich erstellt");
      await loadUsers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRoleChange(userId: number, newRole: Role) {
    setError(null);
    setSuccess(null);
    try {
      await updateUser(userId, { role: newRole });
      setSuccess("Rolle erfolgreich geaendert");
      await loadUsers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  async function handleToggleActive(user: AppUser) {
    setError(null);
    setSuccess(null);
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      setSuccess(`Nutzer ist jetzt ${!user.is_active ? "aktiv" : "inaktiv"}`);
      await loadUsers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  async function handleDeleteUser() {
    if (!showDeleteDialog) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteUser(showDeleteDialog.id);
      setSuccess(`Nutzer "${showDeleteDialog.username}" erfolgreich geloescht`);
      setShowDeleteDialog(null);
      await loadUsers();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
      setShowDeleteDialog(null);
    }
  }

  async function handleChangePassword() {
    if (!showPasswordDialog || !changePasswordValue) return;
    setError(null);
    setSuccess(null);
    try {
      await changePassword(showPasswordDialog.id, changePasswordValue);
      setSuccess("Passwort erfolgreich geaendert");
      setChangePasswordValue("");
      setShowPasswordDialog(null);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }

  function roleLabel(role: string): string {
    const labels: Record<string, string> = {
      admin: "Admin",
      editor: "Editor",
      viewer: "Viewer",
    };
    return labels[role] || role;
  }

  return (
    <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-theme-text">Benutzerverwaltung</h2>
        <button
          onClick={() => {
            setShowCreateDialog(true);
            setError(null);
            setSuccess(null);
          }}
          className="px-4 py-2 text-sm font-medium bg-theme-accent hover:bg-theme-accent-hover text-theme-accent-text rounded transition"
        >
          Neuen Nutzer anlegen
        </button>
      </div>

      {error && (
        <p className="mb-3 text-sm text-theme-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {success && (
        <p className="mb-3 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
          {success}
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-theme-border">
              <th className="text-left py-2 px-3 text-theme-text-secondary font-medium">Benutzername</th>
              <th className="text-left py-2 px-3 text-theme-text-secondary font-medium">Rolle</th>
              <th className="text-left py-2 px-3 text-theme-text-secondary font-medium">Status</th>
              <th className="text-right py-2 px-3 text-theme-text-secondary font-medium">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-theme-border hover:bg-theme-surface-hover">
                <td className="py-2 px-3 font-medium text-theme-text">{u.username}</td>
                <td className="py-2 px-3">
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value as Role)}
                    className="px-2 py-1 rounded border border-theme-border bg-theme-bg text-theme-text text-sm"
                    aria-label={`Rolle fuer ${u.username}`}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>{roleLabel(r)}</option>
                    ))}
                  </select>
                </td>
                <td className="py-2 px-3">
                  <button
                    onClick={() => handleToggleActive(u)}
                    className={`px-2 py-1 rounded text-xs font-medium transition ${
                      u.is_active
                        ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                        : "bg-gray-100 text-gray-500 border border-gray-200"
                    }`}
                    aria-label={`${u.username} ${u.is_active ? "deaktivieren" : "aktivieren"}`}
                  >
                    {u.is_active ? "aktiv" : "inaktiv"}
                  </button>
                </td>
                <td className="py-2 px-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => {
                        setShowPasswordDialog(u);
                        setChangePasswordValue("");
                        setError(null);
                      }}
                      className="text-xs text-theme-accent hover:underline"
                    >
                      Passwort aendern
                    </button>
                    {u.id !== user.id && (
                      <button
                        onClick={() => {
                          setShowDeleteDialog(u);
                          setError(null);
                        }}
                        className="text-xs text-theme-danger hover:underline"
                      >
                        Loeschen
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Dialog: Neuen Nutzer anlegen */}
      {showCreateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label="Neuen Nutzer anlegen">
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text mb-4">Neuen Nutzer anlegen</h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-theme-text-secondary mb-1">Benutzername</label>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="Benutzername"
                  className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
                />
              </div>

              <div>
                <label className="block text-sm text-theme-text-secondary mb-1">Passwort</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Passwort"
                  className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
                />
              </div>

              <div>
                <label className="block text-sm text-theme-text-secondary mb-1">Rolle</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as Role)}
                  className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{roleLabel(r)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-2 mt-5">
              <button
                onClick={handleCreateUser}
                disabled={loading || !newUsername || !newPassword}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded-lg font-medium text-sm transition"
              >
                {loading ? "..." : "Erstellen"}
              </button>

              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setError(null);
                }}
                className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog: Nutzer loeschen */}
      {showDeleteDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label={`Nutzer ${showDeleteDialog.username} loeschen`}>
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text mb-3">Nutzer loeschen</h3>
            <p className="text-sm text-theme-text-secondary mb-2">
              Moechtest du den Nutzer <strong>{showDeleteDialog.username}</strong> wirklich loeschen?
            </p>
            <p className="text-sm text-theme-warning bg-theme-bg border-2 border-theme-warning rounded-lg px-3 py-2 mb-5">
              Diese Aktion kann nicht rueckgaengig gemacht werden.
            </p>

            <div className="flex flex-col gap-2">
              <button
                onClick={handleDeleteUser}
                className="w-full px-4 py-2 bg-theme-danger text-theme-accent-text rounded-lg hover:opacity-90 font-medium text-sm"
              >
                Ja - loeschen
              </button>

              <button
                onClick={() => setShowDeleteDialog(null)}
                className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog: Passwort aendern */}
      {showPasswordDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label={`Passwort fuer ${showPasswordDialog.username} aendern`}>
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text mb-3">
              Passwort aendern fuer {showPasswordDialog.username}
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-theme-text-secondary mb-1">Neues Passwort</label>
                <input
                  type="password"
                  value={changePasswordValue}
                  onChange={(e) => setChangePasswordValue(e.target.value)}
                  placeholder="Neues Passwort"
                  className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2 mt-5">
              <button
                onClick={handleChangePassword}
                disabled={!changePasswordValue}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded-lg font-medium text-sm transition"
              >
                Aendern
              </button>

              <button
                onClick={() => {
                  setShowPasswordDialog(null);
                  setChangePasswordValue("");
                }}
                className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}