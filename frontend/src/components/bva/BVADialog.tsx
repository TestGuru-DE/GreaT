// REQ-3041: BVADialog – Modal-Container fuer Grenzwertanalyse
import { useEffect, useState, useRef } from "react";
import { BVAInputPanel } from "./BVAInputPanel";
import { PreviewTable } from "./PreviewTable";
import { NumberlineVisualization } from "./NumberlineVisualization";
import { calculateBVAPoints, validateBVAConfig, type BVAConfig } from "../../lib/bva-calc";
import { bvaApi } from "../../api/bva";

interface BVADialogProps {
  isOpen: boolean;
  categoryId: number;
  categoryName: string;
  projectId: number;
  onClose: () => void;
  onApply: (values: string[]) => void;
}

export function BVADialog({
  isOpen,
  categoryId,
  categoryName,
  onClose,
  onApply,
}: BVADialogProps) {
  const [config, setConfig] = useState<BVAConfig>({
    min: "",
    max: "",
    pointsPerBoundary: 2,
    markAsErrorCase: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Focus-Trap + ESC
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
      if (e.key === "Enter" && !e.shiftKey) {
        const isValid = validateBVAConfig(config).length === 0;
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
      const minVal = parseFloat(config.min);
      const maxVal = parseFloat(config.max);

      const response = await bvaApi.generate(categoryId, {
        min_val: minVal,
        max_val: maxVal,
        points: config.pointsPerBoundary,
      });

      onApply(response.values);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const points = calculateBVAPoints(config);
  const isValid = validateBVAConfig(config).length === 0;

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
            Grenzwertanalyse (BVA)
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Kategorie: <span className="font-semibold">{categoryName}</span>
          </p>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          <BVAInputPanel config={config} onChange={setConfig} />

          {/* Visualisierung */}
          {points.length > 0 && (
            <div className="bg-slate-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">
                Zahlenstrahl
              </h3>
              <NumberlineVisualization points={points} />
            </div>
          )}

          {/* Vorschau */}
          {points.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-2">
                Vorschau ({points.length} Werte)
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
              <p className="text-sm text-red-700 font-semibold">Fehler</p>
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
            Abbrechen
          </button>
          <button
            onClick={handleApply}
            disabled={!isValid || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-sky-600 rounded-lg hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Wird angewendet..." : "Anwenden"}
          </button>
        </div>
      </div>
    </div>
  );
}
