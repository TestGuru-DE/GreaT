import { useMemo, useState } from 'react';
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
 */
export function MaxTestCasesSettingsCard() {
  const [valueText, setValueText] = useState(() => String(readMaxTestCases()));
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewValue = useMemo(() => parseMaxTestCases(valueText), [valueText]);

  function handleSave() {
    try {
      const normalized = storeMaxTestCases(valueText);
      setError(null);
      setStatus(`Obergrenze auf ${normalized} Testfälle gesetzt. Wird ab der nächsten Generierung angewendet.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ungültiger Wert.');
      setStatus(null);
    }
  }

  return (
    <section className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Maximale Anzahl Testfälle</h2>
      <div className="space-y-3 max-w-xl">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="max-testcases">
          Obergrenze pro Generierung
        </label>
        <input
          id="max-testcases"
          type="number"
          min={MIN_MAX_TESTCASES}
          max={MAX_MAX_TESTCASES}
          value={valueText}
          onChange={(e) => setValueText(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
        />
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Standard ist <strong>{DEFAULT_MAX_TESTCASES}</strong>. Verhindert, dass eine Generierung unbegrenzt viele Testfälle erzeugt.
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Aktuell gewählte Obergrenze: <span className="font-mono">{previewValue ?? DEFAULT_MAX_TESTCASES}</span>
        </p>
        <button
          type="button"
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
        >
          Speichern
        </button>
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        {status && <p className="text-sm text-emerald-700 dark:text-emerald-400">{status}</p>}
      </div>
    </section>
  );
}

export default MaxTestCasesSettingsCard;
