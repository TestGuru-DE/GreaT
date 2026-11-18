import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  DEFAULT_MAX_TESTCASES,
  MIN_MAX_TESTCASES,
  MAX_MAX_TESTCASES,
  parseMaxTestCases,
  readMaxTestCases,
  storeMaxTestCases,
} from '../lib/maxTestCasesSetting';

/**
 * REQ-4018: Einstellungs-Karte fuer die maximale Anzahl generierter Testfaelle.
 * Reuse des Port-Settings-Musters (PortSettingsCard): localStorage-Persistenz,
 * Validierung mit Fehlermeldung, Speichern-Button mit Statusmeldung.
 * REQ-6005: i18n
 */
export function MaxTestCasesSettingsCard() {
  const { t } = useTranslation();
  const [valueText, setValueText] = useState(() => String(readMaxTestCases()));
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewValue = useMemo(() => parseMaxTestCases(valueText), [valueText]);

  function handleSave() {
    try {
      const normalized = storeMaxTestCases(valueText);
      setError(null);
      setStatus(t('maxTestCases.success', { count: normalized }));
    } catch (e) {
      setError(e instanceof Error ? e.message : t('maxTestCases.error'));
      setStatus(null);
    }
  }

  return (
    <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold text-theme-text mb-4">{t('maxTestCases.title')}</h2>
      <div className="space-y-3 max-w-xl">
        <label className="block text-sm font-medium text-theme-text-secondary" htmlFor="max-testcases">
          {t('maxTestCases.label')}
        </label>
        <input
          id="max-testcases"
          type="number"
          min={MIN_MAX_TESTCASES}
          max={MAX_MAX_TESTCASES}
          value={valueText}
          onChange={(e) => setValueText(e.target.value)}
          className="w-full px-4 py-2 border border-theme-border rounded-lg bg-theme-bg text-theme-text"
        />
        <p className="text-sm text-theme-text-secondary" dangerouslySetInnerHTML={{ __html: t('maxTestCases.description', { default: DEFAULT_MAX_TESTCASES }) }} />
        <p className="text-xs text-theme-text-muted">
          {t('maxTestCases.currentLimit')} <span className="font-mono">{previewValue ?? DEFAULT_MAX_TESTCASES}</span>
        </p>
        <button
          type="button"
          onClick={handleSave}
          className="px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover text-theme-accent-text rounded transition"
        >
          {t('maxTestCases.save')}
        </button>
        {error && <p className="text-sm text-theme-danger">{error}</p>}
        {status && <p className="text-sm text-theme-success">{status}</p>}
      </div>
    </section>
  );
}