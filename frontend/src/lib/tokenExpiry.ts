// BUG A-04: Reine Hilfsfunktion ohne Abhaengigkeiten (testbar ohne API-Client)

/** Rechnet ein Ablaufdatum (YYYY-MM-DD) in Tage ab heute um, begrenzt auf 1..365. */
export function expiresAtToDays(expiresAt: string, today: Date = new Date()): number {
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const [y, m, d] = expiresAt.split('-').map(Number);
  const end = new Date(y, (m || 1) - 1, d || 1);
  const days = Math.round((end.getTime() - start.getTime()) / 86_400_000);
  return Math.min(365, Math.max(1, days));
}
