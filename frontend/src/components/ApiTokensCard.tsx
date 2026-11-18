// REQ-6012: API-Token-Verwaltung – Karten-Komponente

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listTokens, revokeToken, ApiToken } from '../api/apiTokensApi';
import ApiTokenCreateDialog from './ApiTokenCreateDialog';

export default function ApiTokensCard() {
  const { t } = useTranslation();
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTokens = useCallback(async () => {
    try {
      const data = await listTokens();
      setTokens(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTokens(); }, [loadTokens]);

  const handleRevoke = useCallback(async (id: number) => {
    if (!confirm(t('settings.apiTokens.revokeConfirm'))) return;
    try {
      await revokeToken(id);
      setTokens(prev => prev.filter(tok => tok.id !== id));
    } catch (e: any) {
      setError(e.response?.data?.detail || String(e));
    }
  }, [t]);

  if (loading) return <div className="p-4 text-gray-500">{t('common.loading')}</div>;

  return (
    <>
      <div className="border rounded-lg p-4 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold dark:text-white">{t('settings.apiTokens.title')}</h2>
          <button
            onClick={() => setDialogOpen(true)}
            className="px-3 py-1 rounded bg-blue-600 text-white text-sm"
          >
            {t('settings.apiTokens.createButton')}
          </button>
        </div>

        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        {tokens.length === 0 ? (
          <p className="text-gray-500 text-sm">{t('settings.apiTokens.empty')}</p>
        ) : (
          <div className="space-y-3">
            {tokens.map(token => (
              <div key={token.id} className="border rounded p-3 dark:border-gray-600">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium dark:text-white">{token.name}</span>
                    <span className="ml-2 text-xs font-mono text-gray-500">{token.prefix}...</span>
                  </div>
                  <button
                    onClick={() => handleRevoke(token.id)}
                    className="text-red-600 text-sm hover:underline"
                  >
                    {t('settings.apiTokens.revokeButton')}
                  </button>
                </div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {token.scopes.map(scope => (
                    <span key={scope} className="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">
                      {scope}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {t('settings.apiTokens.expires')} {new Date(token.expires_at).toLocaleDateString()}
                  {token.last_used_at && ` · ${t('settings.apiTokens.lastUsed')} ${new Date(token.last_used_at).toLocaleDateString()}`}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <ApiTokenCreateDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={loadTokens}
      />
    </>
  );
}