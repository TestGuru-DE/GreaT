// REQ-3041, REQ-6007: BVADialog – Modal-Container fuer Grenzwertanalyse
import { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { BVAInputPanel } from "./BVAInputPanel";
import { PreviewTable } from "./PreviewTable";
import { NumberlineVisualization } from "./NumberlineVisualization";
import {
  calculateMultiRangeBVAPoints,
  validateMultiRangeBVAConfig,
  type BVAConfig,
  type BVARangeEntry,
} from "../../lib/bva-calc";
import { bvaApi, type BVADataType, type BVAExtendedOptions } from "../../api/bva";

interface BVADialogProps {
  isOpen: boolean;
  categoryId: number;
  categoryName: string;
  projectId: number;
  onClose: () => void;
  onApply: (values: string[]) => void;
}

// REQ-6007: Datentyp-Optionen
const DATA_TYPE_OPTIONS: { value: BVADataType; labelKey: string }[] = [
  { value: "number", labelKey: "bvaDialog.dataType.number" },
  { value: "date", labelKey: "bvaDialog.dataType.date" },
  { value: "time", labelKey: "bvaDialog.dataType.time" },
  { value: "datetime", labelKey: "bvaDialog.dataType.datetime" },
  { value: "strlen", labelKey: "bvaDialog.dataType.stringLength" },
];

// REQ-6007: Standard-Extras pro Datentyp
function getDefaultExtras(type: BVADataType): Record<string, boolean> {
  switch (type) {
    case "date":
      return { leapYear: false, nonLeapYear: false, monthEnds: false, yearTransition: false, invalidDate: false };
    case "time":
      return { midnight: false, endOfDay: false, invalid_2400: false, midnight_crossing: false };
    case "datetime":
      return { leapYear: false, midnight: false };
    case "strlen":
      return { empty: false, whitespace_only: false, leading_whitespace: false, trailing_whitespace: false };
    default:
      return {};
  }
}

function createDefaultRanges(_type: BVADataType): BVARangeEntry[] {
  return [{ id: `range-${Date.now()}`, minVal: "", maxVal: "", allowed: true }];
}

export function BVADialog({
  isOpen,
  categoryId,
  categoryName,
  onClose,
  onApply,
}: BVADialogProps) {
  const { t } = useTranslation();
  const [dataType, setDataType] = useState<BVADataType>("number");
  const [config, setConfig] = useState<BVAConfig>({
    min: "",
    max: "",
    pointsPerBoundary: 2,
    markAsErrorCase: false,
    ranges: createDefaultRanges("number"),
  });
  const [extendedOptions, setExtendedOptions] = useState<BVAExtendedOptions>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  // REQ-6007: Datentyp wechseln
  const handleDataTypeChange = (newType: BVADataType) => {
    setDataType(newType);
    setConfig({
      min: "",
      max: "",
      pointsPerBoundary: config.pointsPerBoundary,
      markAsErrorCase: false,
      ranges: createDefaultRanges(newType),
    });
    setExtendedOptions({
      extras: getDefaultExtras(newType),
      ...(newType === "date" ? { format: "iso" } : {}),
      ...(newType === "time" ? { format: "HH:MM", step: "minute" } : {}),
      ...(newType === "datetime" ? { step: "minute" } : {}),
      ...(newType === "strlen" ? { charset: "alnum" } : {}),
    });
  };

  // Focus-Trap + ESC
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
      if (e.key === "Enter" && !e.shiftKey) {
        const isValid = validateMultiRangeBVAConfig(config.ranges ?? []).length === 0;
        if (isValid) {
          e.preventDefault();
          handleApply();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, config, onClose]);

  // Fokus auf ersten Input
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      const firstInput = dialogRef.current.querySelector("input");
      firstInput?.focus();
    }
  }, [isOpen]);

  const handleApply = async () => {
    setError(null);
    setLoading(true);

    try {
      if (dataType === "number") {
        // Bestehende Logik fuer Zahlen
        const response = await bvaApi.generateMultiRange(categoryId, {
          ranges: config.ranges ?? [],
          points: config.pointsPerBoundary,
        });
        onApply(response.values);
      } else {
        // REQ-6007: Erweiterte BVA mit Datentyp
        const response = await bvaApi.generateExtended(categoryId, {
          type: dataType,
          ranges: (config.ranges ?? []).map(r => ({
            min_val: r.minVal,
            max_val: r.maxVal,
            allowed: r.allowed,
          })),
          points: config.pointsPerBoundary,
          options: extendedOptions,
        });
        onApply(response.results.map(r => r.value));
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('errors.unknown'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const points = calculateMultiRangeBVAPoints(config.ranges ?? [], config.pointsPerBoundary);
  const isValid = validateMultiRangeBVAConfig(config.ranges ?? []).length === 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="bva-dialog-title"
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] overflow-auto"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-50 to-blue-50 px-6 py-4 border-b border-slate-200">
          <h2
            id="bva-dialog-title"
            className="text-lg font-bold text-slate-800"
          >
            {t('bvaDialog.title', { categoryName })}
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            {t('bvaDialog.category')}: <span className="font-semibold">{categoryName}</span>
          </p>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* REQ-6007: Datentyp-Dropdown */}
          <div className="flex items-center gap-3">
            <label
              htmlFor="bva-data-type"
              className="text-sm font-medium text-slate-700"
            >
              {t('bvaDialog.dataType.label')}
            </label>
            <select
              id="bva-data-type"
              value={dataType}
              onChange={(e) => handleDataTypeChange(e.target.value as BVADataType)}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500"
              aria-label={t('bvaDialog.dataType.label')}
            >
              {DATA_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {t(opt.labelKey)}
                </option>
              ))}
            </select>
          </div>

          <BVAInputPanel config={config} onChange={setConfig} />

          {/* Visualisierung */}
          {points.length > 0 && (
            <div className="bg-slate-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">
                {t('bvaDialog.numberline')}
              </h3>
              <NumberlineVisualization points={points} />
            </div>
          )}

          {/* Vorschau */}
          {points.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-2">
                {t('bvaDialog.preview', { count: points.length })}
              </h3>
              <PreviewTable
                points={points}
                markAsErrorCase={config.markAsErrorCase || false}
              />
            </div>
          )}

          {/* Backend-Fehler */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700 font-semibold">{t('common.error')}</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            {t('bvaDialog.cancel')}
          </button>
          <button
            onClick={handleApply}
            disabled={!isValid || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-sky-600 rounded-lg hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('bvaDialog.applying') : t('bvaDialog.apply')}
          </button>
        </div>
      </div>
    </div>
  );
}