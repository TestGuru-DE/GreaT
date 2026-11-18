// REQ-6005 Slice 3: useFormattedNumber Hook
// Formatiert Zahlenwerte basierend auf der aktuellen i18n-Sprache
// de: 1.234,5 | en: 1,234.5

import { useTranslation } from "react-i18next";

interface FormatOptions {
  /** Minimum number of decimal places */
  minimumFractionDigits?: number;
  /** Maximum number of decimal places */
  maximumFractionDigits?: number;
  /** Custom Intl.NumberFormatOptions */
  custom?: Intl.NumberFormatOptions;
}

/**
 * Hook zum Formatieren von Zahlenwerten in der aktuellen UI-Sprache.
 *
 * @example
 * const { formatNumber } = useFormattedNumber();
 * formatNumber(1234.5) // "1.234,5" (DE) or "1,234.5" (EN)
 *
 * @example
 * const { formatNumber } = useFormattedNumber({ minimumFractionDigits: 1 });
 * formatNumber(42) // "42,0" (DE) or "42.0" (EN)
 */
export function useFormattedNumber({
  minimumFractionDigits,
  maximumFractionDigits,
  custom,
}: FormatOptions = {}) {
  const { i18n } = useTranslation();

  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined || isNaN(value)) return "";

    const locale = i18n.language === "de" ? "de-DE" : "en-US";

    const options: Intl.NumberFormatOptions = {
      minimumFractionDigits,
      maximumFractionDigits,
      ...custom,
    };

    const formatter = new Intl.NumberFormat(locale, options);
    return formatter.format(value);
  };

  return { formatNumber };
}