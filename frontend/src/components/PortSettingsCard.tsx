import { useMemo, useState } from 'react';

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

export function PortSettingsCard() {
  const [portText, setPortText] = useState(() => String(readStoredPort()));
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewPort = useMemo(() => parsePort(portText), [portText]);

  function handleSave() {
    const normalized = parsePort(portText);
    if (normalized === null) {
      setError('Bitte einen Port zwischen 1 und 65535 eingeben.');
      setStatus(null);
      return;
    }

    localStorage.setItem(STORAGE_KEY, String(normalized));
    setError(null);
    setStatus(`Port ${normalized} gespeichert. Neustart erforderlich.`);
  }

  return (
    <section className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Port-Einstellung</h2>
      <div className="space-y-3 max-w-xl">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="preferred-port">
          Bevorzugter Port
        </label>
        <input
          id="preferred-port"
          type="number"
          min={1}
          max={65535}
          value={portText}
          onChange={(e) => setPortText(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
        />
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Standard ist <strong>8000</strong>. <strong>5173</strong> bleibt nur die Dev-Option. Nach einer Aenderung muss der Server neu gestartet werden.
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Aktuelle lokale URL: <span className="font-mono">http://localhost:{previewPort ?? DEFAULT_PORT}</span>
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

export default PortSettingsCard;

