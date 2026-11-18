// REQ-6005: i18next Initialisierung fuer G.R.E.A.T. Frontend
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import translationDE from "./de.json";
import translationEN from "./en.json";

// detectDefaultLanguage: localStorage > navigator.language > "de"
function detectDefaultLanguage(): string {
  // 1. Gespeicherte Nutzerwahl aus localStorage (fuer Login-Seite vor Anmeldung)
  const stored = localStorage.getItem("great_language");
  if (stored === "de" || stored === "en") {
    return stored;
  }

  // 2. Browsersprache
  const browserLang = navigator.language || (navigator as any).userLanguage;
  if (browserLang && browserLang.startsWith("de")) {
    return "de";
  }

  // 3. Default Deutsch
  return "de";
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: translationDE },
      en: { translation: translationEN },
    },
    lng: detectDefaultLanguage(),
    fallbackLng: "de",
    interpolation: {
      escapeValue: false, // React protects from XSS
    },
  });

export default i18n;