// BUG A-15 (REQ-6005): Sprache anwenden und fuer die Login-Seite merken.
// Bewusst ohne React-Bindung (nur i18next), damit Stores und Tests mit gemocktem
// react-i18next dieses Modul laden koennen.
import i18next from "i18next";

export type AppLanguage = "de" | "en";
export const LANGUAGE_STORAGE_KEY = "great_language";

/** Erste unterstuetzte Browsersprache (de*, en*), sonst Deutsch. */
export function languageFromBrowser(languages: readonly string[] | undefined): AppLanguage {
  for (const lang of languages ?? []) {
    const tag = (lang || "").toLowerCase();
    if (tag.startsWith("de")) return "de";
    if (tag.startsWith("en")) return "en";
  }
  return "de";
}

/** localStorage > Browsersprachen > Deutsch */
export function detectDefaultLanguage(): AppLanguage {
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored === "de" || stored === "en") return stored;
  } catch {
    // localStorage gesperrt: weiter mit Browsersprache
  }
  const nav = typeof navigator !== "undefined" ? navigator : undefined;
  const languages = nav?.languages?.length ? nav.languages : [nav?.language ?? ""];
  return languageFromBrowser(languages);
}

export function applyLanguage(lang: string | null | undefined): void {
  if (lang !== "de" && lang !== "en") return;
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // ohne localStorage gilt die Wahl nur fuer diese Sitzung
  }
  if (i18next.isInitialized && i18next.language !== lang) void i18next.changeLanguage(lang);
}
