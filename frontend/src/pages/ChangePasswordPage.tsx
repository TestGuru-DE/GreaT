// REQ-4028 AK-3: Seite "Passwort aendern" fuer alle Rollen
// REQ-6005: i18n
import { useState, FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/ApiError";

// REQ-4028 AK-4: Mindestlaenge 12 Zeichen (serverseitig enforced, clientseitig vorab geprueft)
const MIN_PASSWORD_LENGTH = 12;
// B-23: mindestens 4 verschiedene Zeichen (serverseitig MIN_PASSWORD_VARIETY)
const MIN_PASSWORD_VARIETY = 4;

export default function ChangePasswordPage() {
  const { t } = useTranslation();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const changePassword = useAuthStore((s) => s.changePassword);
  const setPasswordChangeRequired = useAuthStore((s) => s.setPasswordChangeRequired);
  const navigate = useNavigate();

  // Clientseitige Validierung
  const [clientError, setClientError] = useState<string | null>(null);

  function validate(): string | null {
    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      return t('changePassword.errors.tooShort', { count: MIN_PASSWORD_LENGTH });
    }
    if (newPassword !== confirmPassword) {
      return t('changePassword.errors.mismatch');
    }
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError(null);
    setSuccess(false);

    // Clientseitige Validierung
    const validationError = validate();
    if (validationError) {
      setClientError(validationError);
      return;
    }
    setClientError(null);

    try {
      await changePassword(currentPassword, newPassword);
      setPasswordChangeRequired(false);
      setSuccess(true);
      // Nach kurzer Verzögerung zur /app weiterleiten
      setTimeout(() => {
        navigate("/app");
      }, 1500);
    } catch (e: unknown) {
      setServerError(serverErrorMessage(e));
    }
  }

  // N-01: Server-Codes (ApiError.message) in verstaendliche Meldungen uebersetzen.
  // Unbekannte Codes und rohe HTTP-Fehler fuehren zu einer allgemeinen Meldung.
  function serverErrorMessage(e: unknown): string {
    const message = e instanceof Error ? e.message : String(e);
    const errorKeyMap: Record<string, [string, number?]> = {
      current_password_invalid: ['changePassword.errors.currentInvalid'],
      password_is_default: ['changePassword.errors.isDefault'],
      password_too_short: ['changePassword.errors.tooShort', MIN_PASSWORD_LENGTH],
      password_too_long: ['changePassword.errors.tooLong'],
      password_too_common: ['changePassword.errors.tooCommon'],
      password_low_variety: ['changePassword.errors.lowVariety', MIN_PASSWORD_VARIETY],
      too_many_attempts: ['changePassword.errors.tooManyAttempts'],
    };
    const mapped = errorKeyMap[message];
    if (mapped) return t(mapped[0], { count: mapped[1] });
    // Netzwerkfehler: Meldung des Clients ist bereits verstaendlich
    if (e instanceof ApiError && e.status === 0) return message;
    return t('changePassword.errors.generic');
  }

  const displayError = clientError || serverError;

  return (
    <main className="page" style={{ maxWidth: "34rem" }}>
      <header className="page-header">
        <h1 className="page-title text-theme-text">{t('changePassword.title')}</h1>
      </header>

      {success ? (
        <div className="bg-theme-success-soft text-theme-success p-4 rounded-lg" role="alert">
          {t('changePassword.success')}
        </div>
      ) : (
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6">
          {displayError && (
            <div className="bg-theme-danger-soft text-theme-danger p-3 rounded mb-4" role="alert">
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="current-password"
                className="block text-sm font-medium text-theme-text"
              >
                {t('changePassword.currentPassword')}
              </label>
              <input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-theme-border shadow-sm focus:border-theme-accent focus:ring-theme-accent bg-theme-surface text-theme-text"
                required
                autoFocus
              />
            </div>

            <div>
              <label
                htmlFor="new-password"
                className="block text-sm font-medium text-theme-text"
              >
                {t('changePassword.newPassword')}
              </label>
              <input
                id="new-password"
                data-testid="new-password-input"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-theme-border shadow-sm focus:border-theme-accent focus:ring-theme-accent bg-theme-surface text-theme-text"
                required
                minLength={MIN_PASSWORD_LENGTH}
              />
              <p className="mt-1 text-xs text-theme-text-secondary">
                {t('changePassword.minLength', { count: MIN_PASSWORD_LENGTH })}
              </p>
            </div>

            <div>
              <label
                htmlFor="confirm-password"
                className="block text-sm font-medium text-theme-text"
              >
                {t('changePassword.confirmPassword')}
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-theme-border shadow-sm focus:border-theme-accent focus:ring-theme-accent bg-theme-surface text-theme-text"
                required
                minLength={MIN_PASSWORD_LENGTH}
              />
            </div>

            <button
              type="submit"
              className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50"
            >
              {t('changePassword.changeBtn')}
            </button>
          </form>
        </div>
      )}
    </main>
  );
}