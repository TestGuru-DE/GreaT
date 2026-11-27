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
import {
  CHARSETS,
  DATE_FORMATS,
  EXTRAS_BY_TYPE,
  STEPS,
  TIME_FORMATS,
  defaultExtendedOptions,
  validateExtendedRanges,
  validateTimezone,
} from "../../lib/bva-extended-input";

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

// BUG C-02: Pruefung passend zum Datentyp (Zahlen-Pruefung blockierte Datum/Uhrzeit)
function validateRanges(type: BVADataType, ranges: BVARangeEntry[], options: BVAExtendedOptions = {}): string[] {
  if (type === "number") return validateMultiRangeBVAConfig(ranges);
  const errors = validateExtendedRanges(type, ranges);
  const tzError = type === "datetime" ? validateTimezone(options.timezone) : null;  // BUG C-10
  return tzError ? [...errors, tzError] : errors;
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
    setExtendedOptions(defaultExtendedOptions(newType));
  };

  const setOption = (patch: Partial<BVAExtendedOptions>) =>
    setExtendedOptions((prev) => ({ ...prev, ...patch }));

  const setExtra = (key: string, on: boolean) =>
    setExtendedOptions((prev) => ({ ...prev, extras: { ...(prev.extras ?? {}), [key]: on } }));

  // Focus-Trap + ESC
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
      if (e.key === "Enter" && !e.shiftKey) {
        const isValid = validateRanges(dataType, config.ranges ?? [], extendedOptions).length === 0;
        if (isValid && !loading) {
          e.preventDefault();
          handleApply();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, config, dataType, extendedOptions, loading, onClose]);

  // Fokus auf ersten Input
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      const firstInput = dialogRef.current.querySelector("input");
      firstInput?.focus();
    }
  }, [isOpen]);

  const handleApply = async () => {
    if (loading) return; // kein Doppelklick -> keine doppelten Werte
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
        onApply(response.values.map(r => r.value)); // BUG C-03
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('errors.unknown'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const isValid = validateRanges(dataType, config.ranges ?? [], extendedOptions).length === 0;
  // Zahlenstrahl und Vorschau gibt es nur fuer Zahlen; fuer die anderen Typen
  // berechnet das Backend die Werte.
  const points = dataType === "number" && isValid
    ? calculateMultiRangeBVAPoints(config.ranges ?? [], config.pointsPerBoundary)
    : [];
  const optionLabel = (key: string) => t(`bvaDialog.options.${key}`);

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
        className="bg-theme-surface rounded-2xl shadow-2xl border border-theme-border w-full max-w-3xl max-h-[90vh] overflow-auto"
      >
        {/* Header */}
        <div className="bg-theme-surface-2 px-6 py-4 border-b border-theme-border">
          <h2
            id="bva-dialog-title"
            className="text-lg font-bold text-theme-text"
          >
            {t('bvaDialog.title', { categoryName })}
          </h2>
          <p className="text-sm text-theme-text-secondary mt-1">
            {t('bvaDialog.category')}: <span className="font-semibold">{categoryName}</span>
          </p>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* REQ-6007: Datentyp-Dropdown */}
          <div className="flex items-center gap-3">
            <label
              htmlFor="bva-data-type"
              className="text-sm font-medium text-theme-text"
            >
              {t('bvaDialog.dataType.label')}
            </label>
            <select
              id="bva-data-type"
              value={dataType}
              onChange={(e) => handleDataTypeChange(e.target.value as BVADataType)}
              className="px-3 py-2 border border-theme-border rounded-lg focus:ring-2 focus:ring-theme-accent"
              aria-label={t('bvaDialog.dataType.label')}
            >
              {DATA_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {t(opt.labelKey)}
                </option>
              ))}
            </select>
          </div>

          <BVAInputPanel config={config} onChange={setConfig} dataType={dataType} />

          {/* BUG C-02: Typspezifische Optionen (REQ-6007) */}
          {dataType !== "number" && (
            <fieldset className="rounded-lg border border-theme-border p-3 space-y-3" data-testid="bva-options">
              <legend className="px-1 text-sm font-medium text-theme-text">{optionLabel("title")}</legend>
              <div className="flex flex-wrap gap-4">
                {(dataType === "date" || dataType === "time") && (
                  <label className="flex items-center gap-2 text-sm text-theme-text">
                    {optionLabel("format")}
                    <select
                      aria-label={optionLabel("format")}
                      value={extendedOptions.format ?? ""}
                      onChange={(e) => setOption({ format: e.target.value })}
                      className="px-2 py-1 border border-theme-border rounded-lg"
                    >
                      {(dataType === "date" ? DATE_FORMATS : TIME_FORMATS).map((f) => (
                        <option key={f} value={f}>{optionLabel(`formats.${f}`)}</option>
                      ))}
                    </select>
                  </label>
                )}
                {(dataType === "time" || dataType === "datetime") && (
                  <label className="flex items-center gap-2 text-sm text-theme-text">
                    {optionLabel("step")}
                    <select
                      aria-label={optionLabel("step")}
                      value={extendedOptions.step ?? "minute"}
                      onChange={(e) => setOption({ step: e.target.value })}
                      className="px-2 py-1 border border-theme-border rounded-lg"
                    >
                      {STEPS.map((st) => (
                        <option key={st} value={st}>{optionLabel(`steps.${st}`)}</option>
                      ))}
                    </select>
                  </label>
                )}
                {/* BUG C-10: optionale Zeitzone (ISO-8601-Offset) fuer Datum+Uhrzeit */}
                {dataType === "datetime" && (
                  <label className="flex items-center gap-2 text-sm text-theme-text">
                    {optionLabel("timezone")}
                    <input
                      type="text"
                      aria-label={optionLabel("timezone")}
                      value={extendedOptions.timezone ?? ""}
                      onChange={(e) => setOption({ timezone: e.target.value })}
                      placeholder="+02:00"
                      title={optionLabel("timezoneHint")}
                      aria-invalid={validateTimezone(extendedOptions.timezone) !== null}
                      className="w-24 px-2 py-1 border border-theme-border rounded-lg"
                    />
                    {validateTimezone(extendedOptions.timezone) && (
                      <span role="alert" className="text-xs text-theme-danger">{optionLabel("timezoneHint")}</span>
                    )}
                  </label>
                )}
                {dataType === "strlen" && (
                  <label className="flex items-center gap-2 text-sm text-theme-text">
                    {optionLabel("charset")}
                    <select
                      aria-label={optionLabel("charset")}
                      value={extendedOptions.charset ?? "alnum"}
                      onChange={(e) => setOption({ charset: e.target.value })}
                      className="px-2 py-1 border border-theme-border rounded-lg"
                    >
                      {CHARSETS.map((c) => (
                        <option key={c} value={c}>{optionLabel(`charsets.${c}`)}</option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
              <div>
                <p className="text-xs font-medium text-theme-text-secondary mb-1">{optionLabel("extras")}</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  {EXTRAS_BY_TYPE[dataType].map((key) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-theme-text">
                      <input
                        type="checkbox"
                        checked={Boolean(extendedOptions.extras?.[key])}
                        onChange={(e) => setExtra(key, e.target.checked)}
                        className="w-4 h-4 text-theme-link"
                      />
                      {optionLabel(`extraLabels.${key}`)}
                    </label>
                  ))}
                </div>
              </div>
            </fieldset>
          )}

          {/* Visualisierung */}
          {points.length > 0 && (
            <div className="bg-theme-surface-2 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-theme-text mb-3">
                {t('bvaDialog.numberline')}
              </h3>
              <NumberlineVisualization points={points} />
            </div>
          )}

          {/* Vorschau */}
          {points.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-theme-text mb-2">
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
            <div className="bg-theme-danger-soft border border-theme-danger-border rounded-lg p-4">
              <p className="text-sm text-theme-danger font-semibold">{t('common.error')}</p>
              <p className="text-sm text-theme-danger mt-1">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-theme-surface-2 px-6 py-4 border-t border-theme-border flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-theme-text bg-theme-surface border border-theme-border rounded-lg hover:bg-theme-surface-hover disabled:opacity-50"
          >
            {t('bvaDialog.cancel')}
          </button>
          <button
            onClick={handleApply}
            disabled={!isValid || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-theme-accent rounded-lg hover:bg-theme-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('bvaDialog.applying') : t('bvaDialog.apply')}
          </button>
        </div>
      </div>
    </div>
  );
}