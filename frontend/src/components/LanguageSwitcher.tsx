// REQ-6005: Sprachumschalter DE | EN
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import { applyLanguage } from "../lib/language";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const currentLang = i18n.language;

  const switchLanguage = async (lang: "de" | "en") => {
    applyLanguage(lang);

    // Sync with backend if logged in
    if (user) {
      try {
        await useAuthStore.getState().setLanguage(lang);
      } catch {
        // Silent fail – Sprache funktioniert lokal trotzdem
      }
    }
  };

  return (
    <div
      className="flex items-center gap-1 ml-2"
      role="group"
      aria-label={t("language.switcher.label")}
    >
      <button
        onClick={() => switchLanguage("de")}
        className={`px-2 py-1 text-xs rounded-lg border transition-colors ${
          currentLang === "de"
            ? "border-2 border-theme-accent text-theme-text font-bold underline bg-theme-surface-hover"
            : "border-theme-border text-theme-text-secondary hover:text-theme-text hover:border-theme-border"
        }`}
        aria-pressed={currentLang === "de"}
        title={t("language.switcher.de")}
      >
        DE
      </button>
      <span className="text-theme-text-secondary text-xs">|</span>
      <button
        onClick={() => switchLanguage("en")}
        className={`px-2 py-1 text-xs rounded-lg border transition-colors ${
          currentLang === "en"
            ? "border-2 border-theme-accent text-theme-text font-bold underline bg-theme-surface-hover"
            : "border-theme-border text-theme-text-secondary hover:text-theme-text hover:border-theme-border"
        }`}
        aria-pressed={currentLang === "en"}
        title={t("language.switcher.en")}
      >
        EN
      </button>
    </div>
  );
}