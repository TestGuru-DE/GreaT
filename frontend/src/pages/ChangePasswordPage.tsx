// REQ-4028 AK-3: Seite "Passwort aendern" fuer alle Rollen
// REQ-6005: i18n
import { useState, FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";

// REQ-4028 AK-4: Mindestlaenge 12 Zeichen (serverseitig enforced, clientseitig vorab geprueft)
const MIN_PASSWORD_LENGTH = 12;

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
      const message = e instanceof Error ? e.message : String(e);
      // Map server error codes to i18n keys
      const errorKeyMap: Record<string, string> = {
        current_password_invalid: 'changePassword.errors.currentInvalid',
        password_is_default: 'changePassword.errors.isDefault',
        password_too_short: 'changePassword.errors.tooShort',
        password_too_long: 'changePassword.errors.tooLong',
        too_many_attempts: 'changePassword.errors.tooManyAttempts',
      };
      setServerError(errorKeyMap[message] ? t(errorKeyMap[message], { count: MIN_PASSWORD_LENGTH }) : message);
    }
  }

  const displayError = clientError || serverError;

  return (
    <main className="max-w-md mx-auto px-6 py-12 bg-theme-bg">
      <h1 className="text-2xl font-bold text-theme-text mb-6">{t('changePassword.title')}</h1>

      {success ? (
        <div className="bg-green-100 text-green-700 p-4 rounded-lg" role="alert">
          {t('changePassword.success')}
        </div>
      ) : (
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6">
          {displayError && (
            <div className="bg-red-100 text-red-700 p-3 rounded mb-4" role="alert">
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
                className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
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
                className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
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
                className="mt-1 block w-full rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900"
                required
                minLength={MIN_PASSWORD_LENGTH}
              />
            </div>

            <button
              type="submit"
              className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              {t('changePassword.changeBtn')}
            </button>
          </form>
        </div>
      )}
    </main>
  );
}