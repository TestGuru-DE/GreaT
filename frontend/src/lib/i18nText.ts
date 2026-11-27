// A-14: Uebersetzte Texte fuer Nicht-React-Code (Validierungen in lib/*).
// Nutzt die globale i18next-Instanz (dieselbe, die src/i18n initialisiert), ohne die
// React-Bindung zu importieren. Ist i18next nicht initialisiert (z. B. isolierte Tests),
// wird der deutsche Ersatztext mit Platzhaltern verwendet.
import i18next from "i18next";

export function tr(key: string, fallback: string, vars: Record<string, unknown> = {}): string {
  if (i18next.isInitialized && i18next.exists(key)) {
    return i18next.t(key, vars) as string;
  }
  return fallback.replace(/\{\{(\w+)\}\}/g, (_, name: string) => String(vars[name] ?? ""));
}
