// REQ-4022: API-Helper fuer 409-Conflict-Erkennung
// Teil von EPIC-18 (Multi-User) / Sprint 12

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

/**
 * Prueft ob eine Response einen 409 Conflict ist und extrahiert
 * die Konflikt-Informationen.
 * Gibt null zurueck wenn kein 409.
 */
export async function extractConflict(response: Response): Promise<ConflictInfo | null> {
  if (response.status !== 409) return null;

  const cloned = response.clone();
  try {
    const data: ConflictInfo = await cloned.json();
    return data;
  } catch {
    // Fallback wenn kein gueltiges JSON
    return {
      type: "version_conflict",
      message: "Version-Konflikt (Details nicht verfuegbar)",
      clientVersion: 0,
      serverVersion: 0,
    };
  }
}

/**
 * Hook-Helper: Fuegt 409-Handling zu einem API-Call hinzu.
 * Gibt true zurueck, wenn ein Konflikt erkannt wurde und onConflict aufgerufen wurde.
 */
export async function handleConflictResponse(
  response: Response,
  onConflict: (conflict: ConflictInfo) => void
): Promise<boolean> {
  if (response.status === 409) {
    const conflict = await extractConflict(response);
    if (conflict) {
      onConflict(conflict);
      return true;
    }
  }
  return false;
}