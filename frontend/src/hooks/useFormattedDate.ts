// REQ-6005 Slice 3: useFormattedDate Hook
// Formatiert Datumswerte basierend auf der aktuellen i18n-Sprache
// de: 18.11.2026 | en: 11/18/2026

import { useTranslation } from "react-i18next";

interface FormatOptions {
  /** 'date' | 'time' | 'datetime' */
  style?: "date" | "time" | "datetime";
  /** Custom Intl.DateTimeFormatOptions */
  custom?: Intl.DateTimeFormatOptions;
}

/**
 * Hook zum Formatieren von Datumswerten in der aktuellen UI-Sprache.
 *
 * @example
 * const { formatDate } = useFormattedDate();
 * formatDate(new Date()) // "18.11.2026" (DE) or "11/18/2026" (EN)
 *
 * @example
 * const { formatDate } = useFormattedDate({ style: "datetime" });
 * formatDate(new Date()) // "18.11.2026, 14:30" (DE) or "11/18/2026, 2:30 PM" (EN)
 */
export function useFormattedDate({ style = "date", custom }: FormatOptions = {}) {
  const { i18n } = useTranslation();

  const formatDate = (value: string | Date | null | undefined): string => {
    if (!value) return "";

    const date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) return "";

    const locale = i18n.language === "de" ? "de-DE" : "en-US";

    const defaults: Intl.DateTimeFormatOptions =
      style === "date"
        ? { year: "numeric", month: "2-digit", day: "2-digit" }
        : style === "time"
          ? { hour: "2-digit", minute: "2-digit" }
          : {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            };

    const formatter = new Intl.DateTimeFormat(locale, { ...defaults, ...custom });
    return formatter.format(date);
  };

  return { formatDate };
}