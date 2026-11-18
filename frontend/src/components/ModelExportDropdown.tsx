// REQ-6013: Export-Menü im Projekt-Header
import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Download, ChevronDown } from "lucide-react";
import { exportModel } from "../api/modelApi";
import { useToastStore } from "./Toast";

interface Props {
  projectId: number;
  projectName: string;
}

export default function ModelExportDropdown({ projectId, projectName }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Klick außerhalb schließt Dropdown
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Escape schließt Dropdown
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  const handleExport = async (format: "yaml" | "json") => {
    setOpen(false);
    setLoading(true);
    try {
      await exportModel(projectId, format, projectName);
      useToastStore.getState().add(
        t("modelExport.success"),
        "success",
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      useToastStore.getState().add(
        t("modelExport.error", { error: msg }),
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={dropdownRef} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="flex items-center gap-1 text-sm text-theme-text-secondary hover:text-theme-text border border-theme-border rounded-lg px-3 py-1 transition-colors disabled:opacity-50"
        aria-expanded={open}
        aria-haspopup="true"
        aria-label={t("modelExport.button")}
      >
        {loading ? (
          <span className="inline-block w-3 h-3 border-2 border-theme-text-secondary border-t-transparent rounded-full animate-spin" />
        ) : (
          <Download className="w-3.5 h-3.5" />
        )}
        <span>{t("modelExport.button")}</span>
        <ChevronDown className="w-3 h-3" />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1 z-50 bg-theme-surface border border-theme-border rounded-lg shadow-lg min-w-[200px] py-1"
          role="menu"
          aria-orientation="vertical"
        >
          <button
            type="button"
            onClick={() => handleExport("yaml")}
            disabled={loading}
            className="w-full text-left px-4 py-2 text-sm text-theme-text hover:bg-theme-surface-hover disabled:opacity-50 transition-colors flex items-center gap-2"
            role="menuitem"
          >
            <span className="text-theme-text-muted text-xs font-mono">.yaml</span>
            {t("modelExport.yaml")}
          </button>
          <button
            type="button"
            onClick={() => handleExport("json")}
            disabled={loading}
            className="w-full text-left px-4 py-2 text-sm text-theme-text hover:bg-theme-surface-hover disabled:opacity-50 transition-colors flex items-center gap-2"
            role="menuitem"
          >
            <span className="text-theme-text-muted text-xs font-mono">.json</span>
            {t("modelExport.json")}
          </button>
        </div>
      )}
    </div>
  );
}