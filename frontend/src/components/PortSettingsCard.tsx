import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

const STORAGE_KEY = 'great-preferred-port';
const DEFAULT_PORT = 8000;

function readStoredPort(): number {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return DEFAULT_PORT;
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) return DEFAULT_PORT;
  return parsed;
}

function parsePort(value: string): number | null {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) return null;
  return parsed;
}

// REQ-6005: i18n
export function PortSettingsCard() {
  const { t } = useTranslation();
  const [portText, setPortText] = useState(() => String(readStoredPort()));
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewPort = useMemo(() => parsePort(portText), [portText]);

  function handleSave() {
    const normalized = parsePort(portText);
    if (normalized === null) {
      setError(t('portSettings.error'));
      setStatus(null);
      return;
    }

    localStorage.setItem(STORAGE_KEY, String(normalized));
    setError(null);
    setStatus(t('portSettings.success', { port: normalized }));
  }

  return (
    <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold text-theme-text mb-4">{t('portSettings.title')}</h2>
      <div className="space-y-3 max-w-xl">
        <label className="block text-sm font-medium text-theme-text-secondary" htmlFor="preferred-port">
          {t('portSettings.label')}
        </label>
        <input
          id="preferred-port"
          type="number"
          min={1}
          max={65535}
          value={portText}
          onChange={(e) => setPortText(e.target.value)}
          className="w-full px-4 py-2 border border-theme-border rounded-lg bg-theme-bg text-theme-text"
        />
        <p className="text-sm text-theme-text-secondary" dangerouslySetInnerHTML={{ __html: t('portSettings.description') }} />
        <p className="text-xs text-theme-text-muted">
          {t('portSettings.currentUrl')} <span className="font-mono">http://localhost:{previewPort ?? DEFAULT_PORT}</span>
        </p>
        <button
          type="button"
          onClick={handleSave}
          className="px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover text-theme-accent-text rounded transition"
        >
          {t('portSettings.save')}
        </button>
        {error && <p className="text-sm text-theme-danger">{error}</p>}
        {status && <p className="text-sm text-theme-success">{status}</p>}
      </div>
    </section>
  );
}