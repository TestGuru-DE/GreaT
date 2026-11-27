// REQ-4001: Login-Seite fuer JWT-basierte Authentifizierung
// REQ-4027: Erststart-Hinweis (Standardbenutzer/Standardpasswort)
// REQ-6005: i18n + LanguageSwitcher
import { useState, FormEvent, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";
import { getFirstStartHint } from "../api/authApi";
import { DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD } from "../lib/defaultCredentials";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { LayoutGrid } from "lucide-react";

export default function LoginPage() {
  const { t } = useTranslation();
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
      <div className="card max-w-md w-full space-y-7 p-8 mx-4">
        <div className="flex items-center gap-3">
          <span className="icon-tile icon-tile-lg tile-blue" aria-hidden="true"><LayoutGrid className="w-6 h-6" /></span>
          <h1 className="text-2xl font-bold tracking-tight text-theme-text flex-1">
            {t("login.title")}
          </h1>
          {/* REQ-6005: LanguageSwitcher auf Login-Seite */}
          <LanguageSwitcher />
        </div>

        {error && (
          <div className="banner banner-danger text-sm" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="field-label"
            >
              {t("login.username")}
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
              required
              autoFocus
            />
            {/* REQ-4027 AK-2: Standardbenutzer-Hinweis unter dem Feld "Benutzername" */}
            {showHint && (
              <p className="mt-1 text-xs text-theme-text-secondary">
                {t("login.defaultUser", { username: DEFAULT_ADMIN_USERNAME })}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="field-label"
            >
              {t("login.password")}
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
            />
            {/* REQ-4027 AK-2: Standardpasswort-Hinweis unter dem Feld "Passwort" */}
            {showHint && (
              <p className="mt-1 text-xs text-theme-text-secondary">
                {t("login.defaultPassword", { password: DEFAULT_ADMIN_PASSWORD })}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full !py-2.5"
          >
            {isLoading ? t("login.submitLoading") : t("login.submit")}
          </button>
        </form>
      </div>
    </div>
  );
}