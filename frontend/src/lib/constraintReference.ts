// REQ-6001 AK-10 / BUG K-02: Loeschen von Kategorien und Werten, auf die Constraints verweisen.
// Das Backend antwortet zuerst mit 409 (code "constraint_reference") und nennt die betroffenen
// Constraints. Nach Bestaetigung wird mit force=true geloescht; die Constraints werden dabei
// als ungueltig markiert, nicht geloescht.
import { ApiError } from "../api/ApiError";

export function constraintReferenceNames(error: unknown): string[] | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const detail = error.detail as { code?: unknown; constraints?: unknown } | null;
  if (!detail || typeof detail !== "object" || detail.code !== "constraint_reference") return null;
  return Array.isArray(detail.constraints) ? detail.constraints.map(String) : [];
}

/**
 * Fuehrt das Loeschen aus und fragt bei betroffenen Constraints nach.
 * @returns true wenn geloescht, false wenn der Nutzer abgebrochen hat
 */
export async function deleteWithConstraintCheck(
  run: (force: boolean) => Promise<unknown>,
  confirmAffected: (names: string[]) => boolean,
): Promise<boolean> {
  try {
    await run(false);
    return true;
  } catch (error) {
    const names = constraintReferenceNames(error);
    if (names === null) throw error;
    if (!confirmAffected(names)) return false;
    await run(true);
    return true;
  }
}
