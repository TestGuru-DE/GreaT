// REQ-6005: i18next Initialisierung fuer G.R.E.A.T. Frontend
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import translationDE from "./de.json";
import translationEN from "./en.json";

import { detectDefaultLanguage } from "../lib/language";

// BUG A-15: Spracherkennung und -wechsel liegen in lib/language (ohne React-Bindung)
export { applyLanguage, detectDefaultLanguage, languageFromBrowser } from "../lib/language";
export type { AppLanguage } from "../lib/language";

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

// HTML-Attribut lang fuer Screenreader und Silbentrennung mitfuehren
i18n.on("languageChanged", (lng) => {
  if (typeof document !== "undefined") document.documentElement.lang = lng;
});

export default i18n;
