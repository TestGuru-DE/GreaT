// REQ-6008: CoverageOverviewMatrix — Uebersicht aller Kategorienpaare als Kacheln

import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { coverageApi, type CoverageResponse, type UncoveredTuple } from "../api/client";
import CoverageHeatmap from "./CoverageHeatmap";

interface CoverageOverviewMatrixProps {
  generationId: number;
}

// Colorblind-safe palette for coverage percentage (Okabe-Ito based)
function getCoverageColor(pct: number): string {
  // 0% = red-ish, 100% = green-ish (using Okabe-Ito vermillion -> blue)
  const t = pct / 100;
  const r = Math.round(213 - (213 - 0) * t);
  const g = Math.round(94 + (154 - 94) * t);
  const b = Math.round(0 + (115 - 0) * t);
  return `rgb(${r}, ${g}, ${b})`;
}

export default function CoverageOverviewMatrix({ generationId }: CoverageOverviewMatrixProps) {
  const { t } = useTranslation();
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPair, setSelectedPair] = useState<{ catA: string; catB: string } | null>(null);
  const [showUncovered, setShowUncovered] = useState(false);
  const [uncoveredTuples, setUncoveredTuples] = useState<UncoveredTuple[]>([]);

  const fetchCoverage = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await coverageApi.getCoverage(generationId, 2);
      setCoverage(data);
    } catch (e: any) {
      setError(e.message || t("coverage.loadError"));
    } finally {
      setLoading(false);
    }
  }, [generationId]);

  useEffect(() => {
    fetchCoverage();
  }, [fetchCoverage]);

  const handleTileClick = (catA: string, catB: string) => {
    setSelectedPair({ catA, catB });
    setShowUncovered(false);
  };

  const handleExportCSV = async () => {
    try {
      const blob = await coverageApi.getUncoveredTuples(generationId, 2, "csv");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `uncovered_tuples_${generationId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Silently fail
    }
  };

  const handleShowUncovered = async () => {
    if (showUncovered) {
      setShowUncovered(false);
      return;
    }
    try {
      const data = await coverageApi.getUncoveredTuples(generationId, 2, "json") as any;
      setUncoveredTuples(data.tuples || []);
      setShowUncovered(true);
    } catch {
      // Silently fail
    }
  };

  if (loading) return <div className="coverage-overview-loading">{t("coverage.loadingOverview")}</div>;
  if (error) return <div className="coverage-overview-error">{error}</div>;
  if (!coverage) return null;

  const { coverage_1wise, coverage_2wise, heatmap, uncovered_tuples_2wise } = coverage;
  const hasGaps = coverage_2wise.percentage < 100 && coverage_2wise.possible > 0;

  return (
    <div className="coverage-overview" role="region" aria-label={t("coverage.overviewAria")}>
      {/* Summary */}
      <div className="coverage-overview-summary">
        <div className="coverage-overview-stat">
          <span className="coverage-overview-stat-label">{t("coverage.oneWise")}</span>
          <span className="coverage-overview-stat-value">{coverage_1wise.percentage}%</span>
          <span className="coverage-overview-stat-detail">
            ({coverage_1wise.covered}/{coverage_1wise.possible})
          </span>
        </div>
        <div className="coverage-overview-stat">
          <span className="coverage-overview-stat-label">{t("coverage.twoWise")}</span>
          <span className="coverage-overview-stat-value">{coverage_2wise.percentage}%</span>
          <span className="coverage-overview-stat-detail">
            ({coverage_2wise.covered}/{coverage_2wise.possible})
          </span>
        </div>
        {coverage_2wise.excluded_by_rules > 0 && (
          <div className="coverage-overview-stat">
            <span className="coverage-overview-stat-label">{t("coverage.excluded")}</span>
            <span className="coverage-overview-stat-value">{coverage_2wise.excluded_by_rules}</span>
          </div>
        )}
      </div>

      {/* Heatmap Detail (shown when tile is clicked) */}
      {selectedPair && (
        <div className="coverage-overview-heatmap-detail">
          <button className="coverage-overview-back" onClick={() => setSelectedPair(null)}>
            ← Zurueck zur Uebersicht
          </button>
          <CoverageHeatmap
            generationId={generationId}
            catA={selectedPair.catA}
            catB={selectedPair.catB}
            categories={heatmap.categories}
          />
        </div>
      )}

      {/* Tiles Grid */}
      {!selectedPair && (
        <>
          <div className="coverage-overview-tiles" role="grid">
            {heatmap.pairs.map((pair) => {
              const color = getCoverageColor(pair.coverage_pct);
              return (
                <div
                  key={`${pair.cat_a}-${pair.cat_b}`}
                  className="coverage-overview-tile"
                  data-coverage-pct={Math.round(pair.coverage_pct)}
                  data-cat-pair={`${pair.cat_a}-${pair.cat_b}`}
                  style={{ backgroundColor: color }}
                  onClick={() => handleTileClick(pair.cat_a, pair.cat_b)}
                  role="gridcell"
                  tabIndex={0}
                  title={`${pair.cat_a} x ${pair.cat_b}: ${pair.coverage_pct}% (${pair.covered}/${pair.possible})`}
                >
                  <div className="coverage-overview-tile-label">
                    {pair.cat_a} × {pair.cat_b}
                  </div>
                  <div className="coverage-overview-tile-pct">
                    {pair.coverage_pct}%
                  </div>
                  <div className="coverage-overview-tile-detail">
                    {pair.covered}/{pair.possible}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="coverage-overview-actions">
            {hasGaps && (
              <button
                className="coverage-overview-btn uncovered"
                onClick={handleShowUncovered}
              >
                {showUncovered ? "Verbergen" : `${uncovered_tuples_2wise.length} nicht abgedeckt`}
              </button>
            )}
            {hasGaps && (
              <button className="coverage-overview-btn export" onClick={handleExportCSV}>
                CSV Export
              </button>
            )}
          </div>

          {/* Uncovered Tuples List */}
          {showUncovered && uncoveredTuples.length > 0 && (
            <div className="coverage-overview-uncovered" role="list">
              <h4>{t("coverage.uncoveredTuples", { count: uncoveredTuples.length })}</h4>
              <div className="coverage-overview-uncovered-list" role="list">
                {uncoveredTuples.slice(0, 50).map((tuple, idx) => (
                  <div key={idx} className="coverage-overview-uncovered-item" role="listitem">
                    {tuple.categories.map((cat, i) => (
                      <span key={i} className="coverage-overview-uncovered-pair">
                        <strong>{cat}</strong>: {tuple.values[i]}
                      </span>
                    ))}
                  </div>
                ))}
                {uncoveredTuples.length > 50 && (
                  <div className="coverage-overview-uncovered-more">
                    ... und {uncoveredTuples.length - 50} weitere (siehe CSV-Export)
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}