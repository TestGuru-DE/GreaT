// REQ-4022: Typ fuer 409-Conflict-Erkennung
// Aus handlers.ts ausgelagert (handlers.ts archiviert)

/**
 * Typ fuer Konflikt-Informationen aus einer 409-Response.
 * Das Backend (REQ-4021) sendet diese Struktur bei Versionskonflikten.
 */
export interface ConflictInfo {
  /** Art des Konflikts */
  type: "version_conflict";
  /** Menschlesbare Fehlermeldung */
  message: string;
  /** Version die der Client gesendet hat */
  clientVersion: number;
  /** Version die aktuell auf dem Server ist */
  serverVersion: number;
  /** Optional: Wer hat geaendert (aus Backend-Response) */
  modifiedBy?: string;
  /** Optional: Wann wurde geaendert (ISO-String oder formatiert) */
  modifiedAt?: string;
  /** Optional: Die aktuelle Entitaet vom Server (zum Reload) */
  entity?: unknown;
}