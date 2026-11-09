// REQ-4001: Login-Seite fuer JWT-basierte Authentifizierung
// REQ-4027: Erststart-Hinweis (Standardbenutzer/Standardpasswort)
import { useState, FormEvent, useEffect } from "react";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";
import { getFirstStartHint } from "../api/authApi";
import { DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD } from "../lib/defaultCredentials";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useAuthStore((s) => s.login);
  const error = useAuthStore((s) => s.error);
  const isLoading = useAuthStore((s) => s.isLoading);
  const navigate = useNavigate();

  // REQ-4027 AK-2/AK-6/AK-8: Erststart-Hinweis
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    // AK-8: Bei Fehler/429/Netzwerkfehler: KEIN Hinweis, Login bleibt voll nutzbar
    getFirstStartHint()
      .then((data) => {
        setShowHint(data.show_hint);
      })
      .catch(() => {
        // Fehler ignorieren - Login bleibt nutzbar (AK-8)
        setShowHint(false);
      });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await login(username, password);
      // REQ-4028 AK-1: Wenn password_change_required, auf Passwort-Seite navigieren
      const passwordChangeRequired = useAuthStore.getState().passwordChangeRequired;
      if (passwordChangeRequired) {
        navigate("/account/password");
      } else {
        navigate("/app");
      }
    } catch {
      // error ist im Store
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-theme-bg">
      <div className="max-w-md w-full space-y-8 bg-theme-surface p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold text-center text-theme-text">
          G.R.E.A.T. &ndash; Anmelden
        </h2>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-theme-text"
            >
              Benutzername
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
              required
              autoFocus
            />
            {/* REQ-4027 AK-2: Standardbenutzer-Hinweis unter dem Feld "Benutzername" */}
            {showHint && (
              <p className="mt-1 text-xs text-theme-text-secondary">
                Standardbenutzer: {DEFAULT_ADMIN_USERNAME}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-theme-text"
            >
              Passwort
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
              required
            />
            {/* REQ-4027 AK-2: Standardpasswort-Hinweis unter dem Feld "Passwort" */}
            {showHint && (
              <p className="mt-1 text-xs text-theme-text-secondary">
                Standardpasswort: {DEFAULT_ADMIN_PASSWORD} (bitte nach der ersten Anmeldung aendern)
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Anmelden..." : "Anmelden"}
          </button>
        </form>
      </div>
    </div>
  );
}