// REQ-6011: Export-Menü-Dropdown mit gruppierten Formaten
import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { generateApi } from "../api/client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExportFormat {
  /** API format identifier (e.g. "gherkin", "pytest", "xray-csv") */
  apiFormat: string;
  /** i18n key under export.menu.* */
  labelKey: string;
  /** File extension for download filename */
  extension: string;
  /** Optional: lang param for gherkin (en/de) */
  lang?: string;
}

interface ExportGroup {
  groupKey: string;
  formats: ExportFormat[];
}

interface ExportFormatDropdownProps {
  generationId: number;
  generationName: string;
  /** When provided, used for filename prefix; defaults to generationName */
  filenamePrefix?: string;
}

// ---------------------------------------------------------------------------
// Format definitions
// ---------------------------------------------------------------------------

const EXPORT_GROUPS: ExportGroup[] = [
  {
    groupKey: "groupAutomation",
    formats: [
      { apiFormat: "gherkin", labelKey: "gherkinEn", extension: ".feature", lang: "en" },
      { apiFormat: "gherkin", labelKey: "gherkinDe", extension: ".feature", lang: "de" },
      { apiFormat: "pytest", labelKey: "pytest", extension: ".py" },
      { apiFormat: "robot", labelKey: "robot", extension: ".robot" },
      { apiFormat: "json-data-driven", labelKey: "jsonDataDriven", extension: ".json" },
    ],
  },
  {
    groupKey: "groupTestManagement",
    formats: [
      { apiFormat: "xray-csv", labelKey: "xrayCsv", extension: ".csv" },
      { apiFormat: "testrail-csv", labelKey: "testrailCsv", extension: ".csv" },
      { apiFormat: "azuredevops-csv", labelKey: "azuredevopsCsv", extension: ".csv" },
    ],
  },
  {
    groupKey: "groupDocumentation",
    formats: [
      { apiFormat: "markdown", labelKey: "markdown", extension: ".md" },
      { apiFormat: "csv", labelKey: "csv", extension: ".csv" },
      { apiFormat: "xlsx", labelKey: "excel", extension: ".xlsx" },
      { apiFormat: "json", labelKey: "json", extension: ".json" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ExportFormatDropdown({
  generationId,
  generationName,
  filenamePrefix,
}: ExportFormatDropdownProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Flatten all formats for keyboard navigation
  const allFormats = EXPORT_GROUPS.flatMap((g) => g.formats);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setFocusedIndex(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setIsOpen(false);
        setFocusedIndex(null);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(e.key === "ArrowDown" ? 0 : allFormats.length - 1);
        }
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        if (!isOpen) {
          setFocusedIndex(0);
        }
      }
    },
    [isOpen, allFormats.length],
  );

  const handleMenuKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLUListElement>) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusedIndex((prev) =>
          prev === null ? 0 : Math.min(prev + 1, allFormats.length - 1),
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusedIndex((prev) =>
          prev === null ? allFormats.length - 1 : Math.max(prev - 1, 0),
        );
      } else if (e.key === "Enter" && focusedIndex !== null) {
        e.preventDefault();
        handleExport(allFormats[focusedIndex]);
      } else if (e.key === "Escape") {
        e.preventDefault();
        setIsOpen(false);
        setFocusedIndex(null);
        buttonRef.current?.focus();
      }
    },
    [focusedIndex, allFormats],
  );

  const handleExport = useCallback(
    async (format: ExportFormat) => {
      setIsOpen(false);
      setFocusedIndex(null);

      try {
        const blob = await generateApi.exportGeneration(
          generationId,
          format.apiFormat,
          format.lang,
        );
        const prefix = filenamePrefix || generationName;
        const safeName = prefix.replace(/[^a-zA-Z0-9äöüÄÖÜß _-]/g, "_");
        const filename = `${safeName}${format.extension}`;

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch {
        // Silently fail – the API interceptor shows the error toast
      }
    },
    [generationId, generationName, filenamePrefix],
  );

  return (
    <div ref={containerRef} className="relative inline-block">
      {/* Trigger button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => {
          setIsOpen((prev) => !prev);
          if (!isOpen) setFocusedIndex(0);
        }}
        onKeyDown={handleKeyDown}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={t("export.menu.buttonTitle")}
        className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-100 text-black inline-flex items-center gap-1"
      >
        <span>{t("export.menu.button")}</span>
        <span
          className={`transition-transform text-[10px] ${isOpen ? "rotate-180" : ""}`}
          aria-hidden="true"
        >
          ▼
        </span>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <ul
          role="menu"
          onKeyDown={handleMenuKeyDown}
          className="absolute right-0 top-full mt-1 w-56 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1 max-h-80 overflow-y-auto"
        >
          {EXPORT_GROUPS.map((group) => (
            <li key={group.groupKey}>
              {/* Group header */}
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                {t(`export.menu.${group.groupKey}`)}
              </div>
              {group.formats.map((fmt) => {
                const globalIdx = EXPORT_GROUPS
                  .flatMap((g) => g.formats)
                  .indexOf(fmt);
                const isFocused = focusedIndex === globalIdx;
                return (
                  <button
                    key={`${fmt.apiFormat}-${fmt.lang ?? "default"}`}
                    type="button"
                    role="menuitem"
                    tabIndex={isFocused ? 0 : -1}
                    onClick={() => handleExport(fmt)}
                    onMouseEnter={() => setFocusedIndex(globalIdx)}
                    className={`w-full text-left px-3 py-1.5 text-sm flex items-center justify-between gap-2 transition-colors ${
                      isFocused
                        ? "bg-sky-50 text-sky-700"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <span>{t(`export.menu.${fmt.labelKey}`)}</span>
                    <span className="text-xs text-slate-400 shrink-0">
                      {fmt.extension}
                    </span>
                  </button>
                );
              })}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}