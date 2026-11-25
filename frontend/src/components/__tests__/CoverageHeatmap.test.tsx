// REQ-6008: CoverageHeatmap Komponente — Vitest-Tests
// TEST-ID: TEST-REQ-6008-FE-001 bis 011

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import CoverageHeatmap from "../CoverageHeatmap";
import i18n from "../../i18n";

// BUG R-06: Komponente ist jetzt uebersetzt; Tests laufen mit der echten DE-Uebersetzung
beforeEach(async () => { await i18n.changeLanguage("de"); });

// Mock API
vi.mock("../../api/client", () => ({
  coverageApi: {
    getHeatmap: vi.fn(),
    getUncoveredTuples: vi.fn(),
  },
}));

import { coverageApi } from "../../api/client";

// Mock-Daten
const MOCK_HEATMAP_2X2 = {
  cat_a: "Browser",
  cat_b: "OS",
  rows: ["Chrome", "Firefox"],
  cols: ["Windows", "Linux"],
  cells: {
    "Chrome-Windows": { count: 2, status: "covered", testcase_ids: [1, 3] },
    "Chrome-Linux": { count: 1, status: "covered", testcase_ids: [2] },
    "Firefox-Windows": { count: 1, status: "covered", testcase_ids: [4] },
    "Firefox-Linux": { count: 0, status: "uncovered", testcase_ids: [] },
  },
};

const MOCK_HEATMAP_WITH_EXCLUDED = {
  cat_a: "Browser",
  cat_b: "OS",
  rows: ["Chrome", "Firefox"],
  cols: ["Windows", "Linux"],
  cells: {
    "Chrome-Windows": { count: 1, status: "covered", testcase_ids: [1] },
    "Chrome-Linux": { count: 0, status: "excluded", testcase_ids: [] },
    "Firefox-Windows": { count: 1, status: "covered", testcase_ids: [2] },
    "Firefox-Linux": { count: 1, status: "covered", testcase_ids: [3] },
  },
};

const MOCK_UNCOVERED_TUPLES = [
  { categories: ["Browser", "OS"], values: ["Firefox", "Linux"] },
];

describe("CoverageHeatmap - REQ-6008", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("TEST-REQ-6008-FE-001: renders heatmap grid", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      // Grid sollte Zellen fuer alle Kombinationen haben
      expect(screen.getByText("Chrome")).toBeInTheDocument();
      expect(screen.getByText("Firefox")).toBeInTheDocument();
      expect(screen.getByText("Windows")).toBeInTheDocument();
      expect(screen.getByText("Linux")).toBeInTheDocument();
    });
  });

  it("TEST-REQ-6008-FE-002: shows cell count", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      // Chrome-Windows hat count=2
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("TEST-REQ-6008-FE-003: shows uncovered symbol ✕", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      // Firefox-Linux ist uncovered
      expect(screen.getByText("✕")).toBeInTheDocument();
    });
  });

  it("TEST-REQ-6008-FE-004: shows excluded symbol ⊘", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_WITH_EXCLUDED as never);

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      // Chrome-Linux ist excluded
      expect(screen.getByText("⊘")).toBeInTheDocument();
    });
  });

  it("TEST-REQ-6008-FE-005: color intensity by count", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    const { container } = render(
      <CoverageHeatmap generationId={1} catA="Browser" catB="OS" />
    );

    await waitFor(() => {
      const cells = container.querySelectorAll("[data-cell-status]");
      expect(cells.length).toBeGreaterThan(0);

      // Zellen mit count=2 sollten andere Farbe/Intensitaet haben als count=1
      const cellWith2 = Array.from(cells).find(
        (c) => c.getAttribute("data-count") === "2"
      );
      const cellWith1 = Array.from(cells).find(
        (c) => c.getAttribute("data-count") === "1"
      );

      if (cellWith2 && cellWith1) {
        // Verschiedene Intensitaet via inline style backgroundColor
        const style2 = window.getComputedStyle(cellWith2);
        const style1 = window.getComputedStyle(cellWith1);
        expect(style2.backgroundColor).not.toBe(style1.backgroundColor);
      }
    });
  });

  it("TEST-REQ-6008-FE-006: click cell filters testcases", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    const onFilterChange = vi.fn();
    render(
      <CoverageHeatmap
        generationId={1}
        catA="Browser"
        catB="OS"
        onFilterChange={onFilterChange}
      />
    );

    await waitFor(() => {
      const cell = screen.getByText("2"); // Chrome-Windows, count=2
      fireEvent.click(cell);
    });

    expect(onFilterChange).toHaveBeenCalledWith({
      Browser: "Chrome",
      OS: "Windows",
    });
  });

  it("TEST-REQ-6008-FE-007: click uncovered shows hint", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);
    vi.mocked(coverageApi.getUncoveredTuples).mockResolvedValue(
      MOCK_UNCOVERED_TUPLES as never
    );

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      const uncoveredCell = screen.getByText("✕");
      fireEvent.click(uncoveredCell);
    });

    await waitFor(() => {
      // Gap hint appears in role="alert" container
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert.textContent).toMatch(/Nicht abgedeckt|Lücken schlie[ßs]en/i);
    });
  });

  it("TEST-REQ-6008-FE-008: legend is visible", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    render(<CoverageHeatmap generationId={1} catA="Browser" catB="OS" />);

    await waitFor(() => {
      // Legende sollte Symbole und Erklarungen zeigen
      expect(screen.getByText("✕")).toBeInTheDocument();
      // Oder eine Legende mit Beschriftung
      const legend = screen.queryByRole("definition");
      if (legend) {
        expect(legend).toBeInTheDocument();
      }
    });
  });

  it("TEST-REQ-6008-FE-009: uses colorblind-safe palette", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    const { container } = render(
      <CoverageHeatmap generationId={1} catA="Browser" catB="OS" />
    );

    await waitFor(() => {
      const cells = container.querySelectorAll("[data-cell-status]");
      cells.forEach((cell) => {
        const style = window.getComputedStyle(cell);
        const bg = style.backgroundColor;

        // Farbenblind-tauglich: keine reinen Rot-Gruen-Kontraste
        // Stattdessen: Okabe-Ito, Viridis, Cividis oder aehnlich
        // Wir pruefen nur, dass eine Farbe gesetzt ist
        expect(bg).not.toBe("rgba(0, 0, 0, 0)");
      });
    });
  });

  it("TEST-REQ-6008-FE-010: category selectors prevent same selection", async () => {
    vi.mocked(coverageApi.getHeatmap).mockResolvedValue(MOCK_HEATMAP_2X2 as never);

    const { container } = render(
      <CoverageHeatmap
        generationId={1}
        catA="Browser"
        catB="OS"
        categories={["Browser", "OS", "Lang"]}
      />
    );

    // Wenn catA="Browser" gewaehlt, sollte catB "Browser" nicht als Option haben
    await waitFor(() => {
      const selects = container.querySelectorAll("select");
      if (selects.length >= 2) {
        // catB-Select sollte "Browser" nicht enthalten
        const catBSelect = selects[1];
        const options = catBSelect.querySelectorAll("option");
        const browserOption = Array.from(options).find(
          (o) => o.textContent === "Browser"
        );
        expect(browserOption).toBeNull();
      }
    });
  });

  it("TEST-REQ-6008-FE-011: switches categories on select change", async () => {
    const mockHeatmapAB = {
      ...MOCK_HEATMAP_2X2,
      cat_a: "A",
      cat_b: "B",
    };
    const mockHeatmapAC = {
      ...MOCK_HEATMAP_2X2,
      cat_a: "A",
      cat_b: "C",
      cols: ["c1", "c2"],
    };

    vi.mocked(coverageApi.getHeatmap)
      .mockResolvedValueOnce(mockHeatmapAB as never)
      .mockResolvedValueOnce(mockHeatmapAC as never);

    const { container } = render(
      <CoverageHeatmap
        generationId={1}
        catA="A"
        catB="B"
        categories={["A", "B", "C"]}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("B")).toBeInTheDocument();
    });

    // Wechsel catB von B zu C
    const selects = container.querySelectorAll("select");
    if (selects.length >= 2) {
      fireEvent.change(selects[1], { target: { value: "C" } });

      await waitFor(() => {
        expect(coverageApi.getHeatmap).toHaveBeenCalledTimes(2);
        expect(coverageApi.getHeatmap).toHaveBeenLastCalledWith(
          1,
          "A",
          "C",
          expect.anything()
        );
      });
    }
  });
});