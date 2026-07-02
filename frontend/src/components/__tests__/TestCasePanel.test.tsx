// REQ-3052: Tests für Office-ähnliche Tabellenansicht
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
        name: "TC_1",
        assignments: { Kategorie1: "Wert1", Kategorie2: "WertA" },
        risk_coverage: 5.0,
      },
      {
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
    generationId: null,
    setStrategy: vi.fn(),
    generate: vi.fn(),
    fetchGenerations: vi.fn(),
    loadGeneration: vi.fn(),
    renameGeneration: vi.fn(),
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
          name: "TC_1",
          assignments: { Kategorie1: "Wert1" },
          risk_coverage: 5.0,
          _has_error_value: true,
        },
        {
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
});
