// REQ-3052: Tests für Office-ähnliche Tabellenansicht
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import TestCasePanel from "../TestCasePanel";
import { useGenerateStore } from "../../store/generateStore";

// Mock Store
vi.mock("../../store/generateStore", () => ({
  useGenerateStore: vi.fn(),
}));

describe("TestCasePanel - REQ-3052 Office-ähnliche Tabelle", () => {
  const mockStore = {
    testcases: [
      {
        id: 1,
        name: "TC_1",
        assignments: { Kategorie1: "Wert1", Kategorie2: "WertA" },
        risk_coverage: 5.0,
      },
      {
        id: 2,
        name: "TC_2",
        assignments: { Kategorie1: "Wert2", Kategorie2: "WertB" },
        risk_coverage: 3.0,
      },
    ],
    count: 2,
    loading: false,
    error: null,
    strategy: "each" as const,
    generations: [],
    generationsLoading: false,
    riskSummary: null,
    resultCategories: [],
    generationId: null,
    setStrategy: vi.fn(),
    generate: vi.fn(),
    fetchGenerations: vi.fn(),
    loadGeneration: vi.fn(),
    renameGeneration: vi.fn(),
    updateAssignment: vi.fn(),
  };

  it("zeigt Zeilennummern in erster Spalte", () => {
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
    render(<TestCasePanel projectId={1} />);
    
    // Prüfe Header-Spalte "#"
    expect(screen.getByText("#")).toBeInTheDocument();
    
    // Prüfe Zeilennummern
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("hat Sticky Header mit korrekten CSS-Klassen", () => {
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
    const { container } = render(<TestCasePanel projectId={1} />);
    
    const thead = container.querySelector("thead");
    expect(thead).toHaveClass("sticky", "top-0", "z-10");
  });

  it("sortiert Spalten bei Header-Klick", () => {
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
    const { container } = render(<TestCasePanel projectId={1} />);
    
    // Finde den Risiko-TH-Header (nicht die Option)
    const risikoHeader = container.querySelector('th[title*="Risikoabdeckung"]');
    expect(risikoHeader).toBeInTheDocument();
    
    // Erster Klick: aufsteigend sortieren
    fireEvent.click(risikoHeader!);
    
    // Prüfe Sortierung: 3.0 vor 5.0
    const cells = container.querySelectorAll('tbody td:nth-child(2)');
    expect(cells[0]).toHaveTextContent("3.0");
    expect(cells[1]).toHaveTextContent("5.0");
  });

  it("zeigt Sortier-Indikator im Header", () => {
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
    const { container } = render(<TestCasePanel projectId={1} />);
    
    // Unsortiert: ↕
    expect(container.textContent).toContain("↕");
    
    // Nach Klick: ↑
    const risikoHeader = container.querySelector('th[title*="Risikoabdeckung"]');
    fireEvent.click(risikoHeader!);
    expect(risikoHeader?.textContent).toContain("↑");
  });

  it("exportiert CSV mit korrektem Format", () => {
    // Mock URL.createObjectURL für jsdom
    window.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();
    
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
    render(<TestCasePanel projectId={1} />);
    
    // Client-seitiger CSV-Export-Button
    const csvTableButton = screen.getByText(/CSV \(Tabelle\)/);
    expect(csvTableButton).toBeInTheDocument();
    
    // Backend-CSV-Export-Button
    const csvApiButton = screen.getByText(/CSV \(API\)/);
    expect(csvApiButton).toBeInTheDocument();
    
    // Test client-seitiger Export
    const createElementSpy = vi.spyOn(document, "createElement");
    fireEvent.click(csvTableButton);
    
    // Prüfe dass ein Link-Element erstellt wurde
    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    
    createElementSpy.mockRestore();
  });

  it("zeigt leere Tabelle wenn keine Testfälle", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...mockStore,
      testcases: [],
      count: 0,
    });
    render(<TestCasePanel projectId={1} />);
    
    expect(screen.getByText("Noch keine Testfälle")).toBeInTheDocument();
  });

  it("markiert Fehlerwert-Zeilen rot", () => {
    const storeWithError = {
      ...mockStore,
      testcases: [
        {
          id: 1,
          name: "TC_1",
          assignments: { Kategorie1: "Wert1" },
          risk_coverage: 5.0,
          _has_error_value: true,
        },
        {
          id: 2,
          name: "TC_2",
          assignments: { Kategorie1: "Wert2" },
          risk_coverage: 3.0,
          _has_error_value: false,
        },
      ],
    };
    vi.mocked(useGenerateStore).mockReturnValue(storeWithError);
    const { container } = render(<TestCasePanel projectId={1} />);
    
    const errorRow = container.querySelector(".bg-red-50");
    expect(errorRow).toBeInTheDocument();
    expect(errorRow).toHaveClass("border-l-4", "border-l-red-500");
  });

  it("rendert Ergebnis-Spalten als editierbare Eingaben mit Auswahlwerten", async () => {
    const updateAssignment = vi.fn();
    vi.mocked(useGenerateStore).mockReturnValue({
      ...mockStore,
      updateAssignment,
      resultCategories: [
        {
          id: 10,
          name: "Ergebnis 1",
          editable: true,
          values: [
            { id: 100, value: "Pass" },
            { id: 101, value: "Fail" },
          ],
        },
      ],
      testcases: [
        {
          id: 1,
          name: "TC_1",
          assignments: { Kategorie1: "Wert1", "Ergebnis 1": "" },
          risk_coverage: 1.0,
        },
      ],
    });

    render(<TestCasePanel projectId={1} />);

    const input = screen.getByLabelText("TC_1 – Ergebnis 1");
    expect(input).toBeInTheDocument();
    expect(screen.getByText("Pass")).toBeInTheDocument();
    expect(screen.getByText("Fail")).toBeInTheDocument();

    await act(async () => {
      fireEvent.change(input, { target: { value: "Pass" } });
      fireEvent.blur(input);
    });

    await waitFor(() => {
      expect(updateAssignment).toHaveBeenCalledWith(1, "Ergebnis 1", "Pass");
    });
  });
});

describe("TestCasePanel - REQ-3051 Risikoabdeckungs-Badge (Gesamtprozentsatz)", () => {
  const baseStore = {
    testcases: [
      { id: 1, name: "TC_1", assignments: { Kategorie1: "Wert1" }, risk_coverage: 5.0 },
    ],
    count: 1,
    loading: false,
    error: null,
    strategy: "each" as const,
    generations: [],
    generationsLoading: false,
    resultCategories: [],
    generationId: 1,
    setStrategy: vi.fn(),
    generate: vi.fn(),
    fetchGenerations: vi.fn(),
    loadGeneration: vi.fn(),
    renameGeneration: vi.fn(),
    updateAssignment: vi.fn(),
  };

  it("zeigt kein Badge, wenn keine Generierung vorliegt (riskSummary = null)", () => {
    vi.mocked(useGenerateStore).mockReturnValue({ ...baseStore, riskSummary: null });
    render(<TestCasePanel projectId={1} />);

    expect(screen.queryByText(/Risikoabdeckung:/)).not.toBeInTheDocument();
  });

  it("zeigt gruenes Badge bei Risikoabdeckung >= 80%", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...baseStore,
      riskSummary: { total_risk: 8, max_possible_risk: 10, risk_coverage_percent: 80, testcase_count: 1 },
    });
    const { container } = render(<TestCasePanel projectId={1} />);

    expect(screen.getByText(/Risikoabdeckung: 80%/)).toBeInTheDocument();
    const badge = container.querySelector(".bg-green-100");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-green-800", "border-green-300");
  });

  it("zeigt gelbes Badge bei Risikoabdeckung zwischen 50% und 79%", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...baseStore,
      riskSummary: { total_risk: 6, max_possible_risk: 10, risk_coverage_percent: 60, testcase_count: 1 },
    });
    const { container } = render(<TestCasePanel projectId={1} />);

    expect(screen.getByText(/Risikoabdeckung: 60%/)).toBeInTheDocument();
    const badge = container.querySelector(".bg-yellow-100");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-yellow-800", "border-yellow-300");
  });

  it("zeigt rotes Badge bei Risikoabdeckung unter 50%", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...baseStore,
      riskSummary: { total_risk: 3, max_possible_risk: 10, risk_coverage_percent: 30, testcase_count: 1 },
    });
    const { container } = render(<TestCasePanel projectId={1} />);

    expect(screen.getByText(/Risikoabdeckung: 30%/)).toBeInTheDocument();
    const badge = container.querySelector(".bg-red-100");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-red-800", "border-red-300");
  });

  it("zeigt Grenzwert 50% als gelb (nicht rot)", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...baseStore,
      riskSummary: { total_risk: 5, max_possible_risk: 10, risk_coverage_percent: 50, testcase_count: 1 },
    });
    const { container } = render(<TestCasePanel projectId={1} />);

    expect(container.querySelector(".bg-yellow-100")).toBeInTheDocument();
    expect(container.querySelector(".bg-red-100")).not.toBeInTheDocument();
  });

  it("zeigt absolute Werte (total/max) neben dem Badge", () => {
    vi.mocked(useGenerateStore).mockReturnValue({
      ...baseStore,
      riskSummary: { total_risk: 8, max_possible_risk: 10, risk_coverage_percent: 80, testcase_count: 1 },
    });
    render(<TestCasePanel projectId={1} />);

    expect(screen.getByText("(8.0 / 10.0)")).toBeInTheDocument();
  });
});
