// REQ-4018: Maximale Anzahl Testfaelle als konfigurierbares Setting (Default 1000).
// Analog zum Port-Setting (PortSettingsCard) wird der Wert lokal im Browser
// gespeichert. Anders als beim Port wirkt diese Einstellung sofort (kein
// Server-Neustart noetig), da sie bei jeder Generierung als 'limit' an das
// Backend mitgeschickt wird (siehe generateStore.generate()).
export const MAX_TESTCASES_STORAGE_KEY = 'great-max-testcases';
export const DEFAULT_MAX_TESTCASES = 1000;
export const MIN_MAX_TESTCASES = 1;
export const MAX_MAX_TESTCASES = 100000;

/**
 * Prueft und normalisiert eine Benutzereingabe fuer die Obergrenze.
 * Gueltig sind ganze Zahlen im Bereich [MIN_MAX_TESTCASES, MAX_MAX_TESTCASES].
 * Gibt bei ungueltiger Eingabe `null` zurueck (keine stillen Fehler: der
 * Aufrufer muss den Fehlerfall explizit behandeln).
 */
export function parseMaxTestCases(value: string): number | null {
  const trimmed = value.trim();
  if (!/^\d+$/.test(trimmed)) {
    return null;
  }
  const parsed = Number.parseInt(trimmed, 10);
  if (!Number.isInteger(parsed) || parsed < MIN_MAX_TESTCASES || parsed > MAX_MAX_TESTCASES) {
    return null;
  }
  return parsed;
}

/**
 * Liest die aktuell gespeicherte Obergrenze aus localStorage.
 * Fehlt der Wert oder ist er ungueltig, wird robust auf den Default (1000)
 * zurueckgefallen (kein Crash, keine stille Fehlkonfiguration).
 */
export function readMaxTestCases(): number {
  const raw = localStorage.getItem(MAX_TESTCASES_STORAGE_KEY);
  if (!raw) return DEFAULT_MAX_TESTCASES;
  const parsed = parseMaxTestCases(raw);
  return parsed ?? DEFAULT_MAX_TESTCASES;
}

/**
 * Speichert eine geprüfte Obergrenze. Wirft, wenn der Wert ungueltig ist,
 * damit Aufrufer (z. B. das Settings-Formular) den Fehler sichtbar behandeln.
 */
export function storeMaxTestCases(value: string): number {
  const normalized = parseMaxTestCases(value);
  if (normalized === null) {
    throw new Error(
      `Bitte eine ganze Zahl zwischen ${MIN_MAX_TESTCASES} und ${MAX_MAX_TESTCASES} eingeben.`
    );
  }
  localStorage.setItem(MAX_TESTCASES_STORAGE_KEY, String(normalized));
  return normalized;
}
