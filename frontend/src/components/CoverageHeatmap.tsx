// REQ-6008: CoverageHeatmap — Heatmap-Matrix fuer zwei Kategorien
// Farbskala: Okabe-Ito (farbenblind-tauglich), Intensitaet nach count

import { useState, useEffect, useCallback } from "react";
import { Trans, useTranslation } from "react-i18next";
import { coverageApi, type HeatmapResponse, type HeatmapCellData } from "../api/client";

interface CoverageHeatmapProps {
  generationId: number;
  catA: string;
  catB: string;
  categories?: string[]; // Fuer Category-Selector
  onFilterChange?: (filter: Record<string, string>) => void;
}

// Okabe-Ito Palette (farbenblind-tauglich)
// https://jfly.uni-koeln.de/color/
// Used for colorblind-safe gradients

// Intensitaet: 0 = transparent, higher = more saturated
function getCellColor(count: number, maxCount: number): string {
  if (count === 0) return "transparent";
  const intensity = Math.min(1, count / Math.max(maxCount, 1));
  // Gradient von hellblau zu dunkelgruen (Okabe-Ito skyBlue -> blue)
  const r = Math.round(86 + (0 - 86) * intensity);
  const g = Math.round(180 + (154 - 180) * intensity);
  const b = Math.round(233 + (115 - 233) * intensity);
  const a = 0.3 + 0.7 * intensity;
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function getExcludedColor(): string {
  return "rgba(200, 200, 200, 0.3)";
}

function getUncoveredColor(): string {
  return "rgba(220, 80, 80, 0.15)";
}

export default function CoverageHeatmap({
  generationId,
  catA,
  catB,
  categories,
  onFilterChange,
}: CoverageHeatmapProps) {
  const { t } = useTranslation();
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCatA, setSelectedCatA] = useState(catA);
  const [selectedCatB, setSelectedCatB] = useState(catB);
  const [showGapHint, setShowGapHint] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setShowGapHint(false);
    try {
      const data = await coverageApi.getHeatmap(generationId, selectedCatA, selectedCatB, {});
      setHeatmap(data);
    } catch (e: any) {
      setError(e.message || t('coverageView.loadError'));
    } finally {
      setLoading(false);
    }
  }, [generationId, selectedCatA, selectedCatB]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Category selector options
  const availableCategories = categories || [];
  const catAOptions = availableCategories.filter((c) => c !== selectedCatB);
  const catBOptions = availableCategories.filter((c) => c !== selectedCatA);

  const maxCount = heatmap
    ? Math.max(0, ...Object.values(heatmap.cells).map((c) => c.count))
    : 0;

  const handleCellClick = (rowVal: string, colVal: string, cell: HeatmapCellData) => {
    if (cell.status === "uncovered") {
      setShowGapHint(true);
      return;
    }
    if (onFilterChange) {
      onFilterChange({ [selectedCatA]: rowVal, [selectedCatB]: colVal });
    }
  };

  if (loading) return <div className="coverage-heatmap-loading">{t("coverage.loadingHeatmap")}</div>;
  if (error) return <div className="coverage-heatmap-error">{error}</div>;
  if (!heatmap) return null;

  return (
    <div className="coverage-heatmap" role="region" aria-label={t("coverage.heatmapAria", { a: selectedCatA, b: selectedCatB })}>
      {/* Category Selectors */}
      {availableCategories.length >= 2 && (
        <div className="coverage-heatmap-selectors">
          <label>
            {t('coverageView.categoryA')}
            <select
              value={selectedCatA}
              onChange={(e) => {
                setSelectedCatA(e.target.value);
                setShowGapHint(false);
              }}
            >
              {catAOptions.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            {t('coverageView.categoryB')}
            <select
              value={selectedCatB}
              onChange={(e) => {
                setSelectedCatB(e.target.value);
                setShowGapHint(false);
              }}
            >
              {catBOptions.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
      )}

      {/* Title */}
      <h3 className="coverage-heatmap-title">
        {selectedCatA} &times; {selectedCatB}
      </h3>

      {/* Heatmap Grid */}
      <div className="coverage-heatmap-grid" style={{
        display: "grid",
        gridTemplateColumns: `120px repeat(${heatmap.cols.length}, 1fr)`,
        gap: "2px",
      }}>
        {/* Header row */}
        <div className="coverage-heatmap-corner" />
        {heatmap.cols.map((col) => (
          <div key={col} className="coverage-heatmap-header" title={col}>
            {col}
          </div>
        ))}

        {/* Data rows */}
        {heatmap.rows.map((row) => (
          <>
            <div key={`row-${row}`} className="coverage-heatmap-row-header" title={row}>
              {row}
            </div>
            {heatmap.cols.map((col) => {
              const cellKey = `${row}-${col}`;
              const cell = heatmap.cells[cellKey];
              if (!cell) return null;

              const bgColor =
                cell.status === "excluded"
                  ? getExcludedColor()
                  : cell.status === "uncovered"
                  ? getUncoveredColor()
                  : getCellColor(cell.count, maxCount);

              const symbol =
                cell.status === "covered"
                  ? (cell.count > 0 ? String(cell.count) : "\u2713")
                  : cell.status === "excluded"
                  ? "\u2298"
                  : "\u2715";

              return (
                <div
                  key={cellKey}
                  className="coverage-heatmap-cell"
                  data-cell-status={cell.status}
                  data-count={cell.count}
                  style={{ backgroundColor: bgColor }}
                  onClick={() => handleCellClick(row, col, cell)}
                  title={t("coverage.cellTitle", { row, col, count: cell.count, status: cell.status })}
                  role="gridcell"
                  tabIndex={0}
                >
                  <span className="coverage-heatmap-cell-value" data-testid={`cell-${row}-${col}`}>{symbol}</span>
                </div>
              );
            })}
          </>
        ))}
      </div>

      {/* Gap hint */}
      {showGapHint && (
        <div className="coverage-heatmap-gap-hint" role="alert">
          <p>{t("coverage.uncovered")}</p>
          <p><Trans i18nKey="coverage.gapHint" components={{ strong: <strong /> }} /></p>
        </div>
      )}

      {/* Legend */}
      <div className="coverage-heatmap-legend" role="definition">
        <div className="coverage-heatmap-legend-item">
          <span className="coverage-heatmap-legend-swatch" style={{ backgroundColor: getCellColor(maxCount, maxCount) }} />
          <span>{t("coverage.legendHigh")}</span>
        </div>
        <div className="coverage-heatmap-legend-item">
          <span className="coverage-heatmap-legend-swatch" style={{ backgroundColor: getCellColor(1, maxCount) }} />
          <span>{t("coverage.legendLow")}</span>
        </div>
        <div className="coverage-heatmap-legend-item">
          <span className="coverage-heatmap-legend-swatch" style={{ backgroundColor: getUncoveredColor() }} />
          <span>{t("coverage.uncovered")}</span>
        </div>
        <div className="coverage-heatmap-legend-item">
          <span className="coverage-heatmap-legend-swatch" style={{ backgroundColor: getExcludedColor() }} />
          <span>{t("coverage.legendExcluded")}</span>
        </div>
      </div>
    </div>
  );
}