// REQ-6012: API-Token-Erstellungs-Dialog

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { createToken, CreateTokenRequest } from '../api/apiTokensApi';
import { expiresAtToDays } from '../lib/tokenExpiry';
import { useAuthStore } from '../store/authStore';
import { usersApi, type AppUser } from '../api/usersApi';

const ALL_SCOPES = [
  'projects:read',
  'projects:write',
  'generate',
  'export',
  'models:read',
  'models:write',
];

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function ApiTokenCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [expiresAt, setExpiresAt] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 90);
    return d.toISOString().slice(0, 10);
  });
  const [scopes, setScopes] = useState<string[]>(['projects:read']);
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // BUG A-01: Admins koennen Tokens fuer technische Nutzer (api_user) anlegen
  const isAdmin = useAuthStore((s) => s.user?.role === 'admin');
  const [technicalUsers, setTechnicalUsers] = useState<AppUser[]>([]);
  const [ownerId, setOwnerId] = useState<number | ''>('');

  useEffect(() => {
    if (!open || !isAdmin) return;
    usersApi.list()
      .then((users) => setTechnicalUsers(users.filter((u) => u.role === 'api_user' && u.is_active)))
      .catch(() => setTechnicalUsers([]));
  }, [open, isAdmin]);

  const toggleScope = useCallback((s: string) => {
    setScopes(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
  }, []);

  const handleCreate = useCallback(async () => {
    if (!name.trim()) {
      setError(t('settings.apiTokens.nameRequired'));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const req: CreateTokenRequest = { name: name.trim(), expires_in_days: expiresAtToDays(expiresAt), scopes }; // BUG A-04
      if (ownerId !== '') req.user_id = ownerId; // BUG A-01
      const res = await createToken(req);
      setCreatedToken(res.token);
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e)); // ApiError liefert lesbare Meldung
    } finally {
      setLoading(false);
    }
  }, [name, expiresAt, scopes, ownerId, t]);

  const handleCopy = useCallback(() => {
    if (createdToken) navigator.clipboard.writeText(createdToken);
  }, [createdToken]);

  const handleClose = useCallback(() => {
    setName('');
    setCreatedToken(null);
    setError(null);
    onClose();
  }, [onClose]);

  const handleConfirm = useCallback(() => {
    setCreatedToken(null);
    onCreated();
    onClose();
  }, [onCreated, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-lg">
        <h2 className="text-xl font-bold mb-4 dark:text-white">
          {t('settings.apiTokens.createTitle')}
        </h2>

        {!createdToken ? (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1 dark:text-gray-300">
                {t('settings.apiTokens.name')} *
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                placeholder={t('settings.apiTokens.namePlaceholder')}
              />
            </div>

            {isAdmin && technicalUsers.length > 0 && (
              <div className="mb-4">
                <label htmlFor="token-owner" className="block text-sm font-medium mb-1 dark:text-gray-300">
                  {t('settings.apiTokens.owner')}
                </label>
                <select
                  id="token-owner"
                  value={ownerId}
                  onChange={(e) => setOwnerId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="">{t('settings.apiTokens.ownerSelf')}</option>
                  {technicalUsers.map((u) => (
                    <option key={u.id} value={u.id}>{u.username}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">{t('settings.apiTokens.ownerHint')}</p>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1 dark:text-gray-300">
                {t('settings.apiTokens.expiresAt')} *
              </label>
              <input
                type="date"
                value={expiresAt}
                onChange={e => setExpiresAt(e.target.value)}
                min={new Date().toISOString().slice(0, 10)}
                max={new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)}
                className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <p className="text-xs text-gray-500 mt-1">{t('settings.apiTokens.expiresAtHint')}</p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 dark:text-gray-300">
                {t('settings.apiTokens.scopes')}
              </label>
              <div className="space-y-2">
                {ALL_SCOPES.map(scope => (
                  <label key={scope} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={scopes.includes(scope)}
                      onChange={() => toggleScope(scope)}
                      className="rounded"
                    />
                    <span className="text-sm dark:text-gray-300">
                      <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">{scope}</code>
                      {' '}{t(`settings.apiTokens.scopeDescriptions.${scope}`)}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

            <div className="flex justify-end gap-2">
              <button onClick={handleClose} className="px-4 py-2 rounded border dark:border-gray-600 dark:text-white">
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCreate}
                disabled={loading}
                className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
              >
                {loading ? t('common.loading') : t('settings.apiTokens.createButton')}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded p-4 mb-4">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm mb-2">
                ⚠️ {t('settings.apiTokens.warning')}
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white dark:bg-gray-800 border dark:border-gray-600 rounded px-3 py-2 text-sm font-mono break-all">
                  {createdToken}
                </code>
                <button
                  onClick={handleCopy}
                  className="px-3 py-2 rounded border dark:border-gray-600 dark:text-white text-sm whitespace-nowrap"
                >
                  {t('settings.apiTokens.copyButton')}
                </button>
              </div>
            </div>
            <div className="flex justify-end">
              <button onClick={handleConfirm} className="px-4 py-2 rounded bg-blue-600 text-white">
                {t('settings.apiTokens.understood')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}