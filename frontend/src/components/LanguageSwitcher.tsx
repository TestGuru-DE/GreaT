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
      className="segmented"
      role="group"
      aria-label={t("language.switcher.label")}
    >
      <button
        onClick={() => switchLanguage("de")}
        className={`!px-2.5 !py-1 !text-xs font-semibold ${currentLang === "de" ? "is-active" : ""}`}
        aria-pressed={currentLang === "de"}
        title={t("language.switcher.de")}
      >
        DE
      </button>
      <button
        onClick={() => switchLanguage("en")}
        className={`!px-2.5 !py-1 !text-xs font-semibold ${currentLang === "en" ? "is-active" : ""}`}
        aria-pressed={currentLang === "en"}
        title={t("language.switcher.en")}
      >
        EN
      </button>
    </div>
  );
}