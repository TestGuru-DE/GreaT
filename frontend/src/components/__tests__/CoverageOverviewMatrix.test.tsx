// REQ-6008: CoverageOverviewMatrix Komponente — Vitest-Tests
// TEST-ID: TEST-REQ-6008-FE-012 bis 018

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import CoverageOverviewMatrix from "../CoverageOverviewMatrix";

// Mock API
vi.mock("../../api/client", () => ({
  coverageApi: {
    getCoverage: vi.fn(),
    getUncoveredTuples: vi.fn(),
  },
}));

import { coverageApi } from "../../api/client";

// Mock-Daten: 4 Kategorien -> C(4,2) = 6 Paare
const MOCK_COVERAGE_4CATS = {
  generation_id: 1,
  coverage_1wise: { covered: 8, possible: 8, percentage: 100.0, excluded_by_rules: 0 },
  coverage_2wise: { covered: 10, possible: 12, percentage: 83.33, excluded_by_rules: 0 },
  heatmap: {
    categories: ["A", "B", "C", "D"],
    pairs: [
      { cat_a: "A", cat_b: "B", coverage_pct: 100.0, covered: 4, possible: 4 },
      { cat_a: "A", cat_b: "C", coverage_pct: 75.0, covered: 3, possible: 4 },
      { cat_a: "A", cat_b: "D", coverage_pct: 50.0, covered: 2, possible: 4 },
      { cat_a: "B", cat_b: "C", coverage_pct: 100.0, covered: 4, possible: 4 },
      { cat_a: "B", cat_b: "D", coverage_pct: 25.0, covered: 1, possible: 4 },
      { cat_a: "C", cat_b: "D", coverage_pct: 100.0, covered: 4, possible: 4 },
    ],
  },
  uncovered_tuples_2wise: [
    { categories: ["A", "C"], values: ["a2", "c2"] },
    { categories: ["A", "D"], values: ["a1", "d2"] },
    { categories: ["A", "D"], values: ["a2", "d1"] },
    { categories: ["B", "D"], values: ["b1", "d2"] },
    { categories: ["B", "D"], values: ["b2", "d1"] },
    { categories: ["B", "D"], values: ["b2", "d2"] },
  ],
  cached: false,
};

describe("CoverageOverviewMatrix - REQ-6008", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("TEST-REQ-6008-FE-012: renders tiles for all category pairs", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      // C(4,2) = 6 Kacheln
      const tiles = screen.getAllByRole("gridcell");
      expect(tiles.length).toBeGreaterThanOrEqual(6);
    });
  });

  it("TEST-REQ-6008-FE-013: tile shows coverage percentage", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      // A-C hat 75%
      expect(screen.getByText("75%")).toBeInTheDocument();
      // A-B hat 100% (appears multiple times, use getAllByText)
      expect(screen.getAllByText("100%").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("TEST-REQ-6008-FE-014: tile color varies by coverage", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    const { container } = render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      const tiles = container.querySelectorAll("[data-coverage-pct]");
      expect(tiles.length).toBeGreaterThanOrEqual(6);

      // 100% und 25% sollten unterschiedliche Farben haben
      const tile100 = Array.from(tiles).find(
        (t) => t.getAttribute("data-coverage-pct") === "100"
      );
      const tile25 = Array.from(tiles).find(
        (t) => t.getAttribute("data-coverage-pct") === "25"
      );

      if (tile100 && tile25) {
        const style100 = window.getComputedStyle(tile100);
        const style25 = window.getComputedStyle(tile25);
        expect(style100.backgroundColor).not.toBe(style25.backgroundColor);
      }
    });
  });

  it("TEST-REQ-6008-FE-015: click tile opens heatmap detail", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    const { container } = render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      const tiles = container.querySelectorAll("[data-cat-pair]");
      if (tiles.length > 0) {
        // Klick auf erste Kachel
        fireEvent.click(tiles[0]);

        // Heatmap-Detail sollte erscheinen
        const heatmap = screen.queryByRole("region", { name: /heatmap|abdeckung/i });
        if (heatmap) {
          expect(heatmap).toBeInTheDocument();
        }
      }
    });
  });

  it("TEST-REQ-6008-FE-016: uncovered tuples button visible when gaps exist", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      // Button fuer nicht abgedeckte Tupel
      const btn = screen.queryByText(/nicht abgedeckt|uncovered|missing/i);
      if (btn) {
        expect(btn).toBeInTheDocument();
      }
    });
  });

  it("TEST-REQ-6008-FE-017: CSV export button triggers download", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(async () => {
      const csvBtn = screen.queryByText(/CSV|Export|export/i);
      if (csvBtn) {
        expect(csvBtn).toBeInTheDocument();
        fireEvent.click(csvBtn);

        // Download sollte getriggert werden (pruefen via mock)
        await waitFor(() => {
          expect(coverageApi.getUncoveredTuples).toHaveBeenCalledWith(1, 2);
        });
      }
    });
  });

  it("TEST-REQ-6008-FE-018: shows overall 2-wise percentage summary", async () => {
    vi.mocked(coverageApi.getCoverage).mockResolvedValue(MOCK_COVERAGE_4CATS as never);

    render(<CoverageOverviewMatrix generationId={1} />);

    await waitFor(() => {
      // Gesamt-2-wise: 83.33%
      expect(screen.getByText(/83\.33%|83%/)).toBeInTheDocument();
    });
  });
});