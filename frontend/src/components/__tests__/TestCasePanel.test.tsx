// REQ-3052: Tests für Office-ähnliche Tabellenansicht
// BUGFIX React #300 (REQ-1208, REQ-2001, REQ-3052, REQ-4018, REQ-5006): Rules-of-Hooks-Verletzung im Panel
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import TestCasePanel from "../TestCasePanel";
import { useGenerateStore } from "../../store/generateStore";
import { useDecisionTableStore } from "../../store/decisionTableStore";
import { rulesApi, generateApi } from "../../api/client";

// Mock Store + API
vi.mock("../../store/generateStore", () => ({
  useGenerateStore: vi.fn(),
}));

vi.mock("../../api/client", () => ({
  rulesApi: {
    list: vi.fn(),
  },
  generateApi: {
    run: vi.fn(),
    getTestcases: vi.fn(),
    listGenerations: vi.fn(),
    renameGeneration: vi.fn(),
    updateAssignment: vi.fn(),
  },
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

  beforeEach(() => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(useGenerateStore).mockReturnValue(mockStore);
  });

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
          has_error_value: true,
        },
        {
          id: 2,
          name: "TC_2",
          assignments: { Kategorie1: "Wert2" },
          risk_coverage: 3.0,
          has_error_value: false,
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


describe("TestCasePanel - REQ-3005 Mit-Regeln-Checkbox", () => {
  const baseStore = {
    testcases: [],
    count: 0,
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

  beforeEach(() => {
    vi.mocked(useGenerateStore).mockReturnValue({ ...baseStore, generate: vi.fn() });
  });

  it("aktiviert die Checkbox standardm??ig, wenn Regeln existieren", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([{ id: 1 }] as never);

    render(<TestCasePanel projectId={1} />);

    const checkbox = await screen.findByRole("checkbox", { name: /mit regeln generieren/i });
    await waitFor(() => expect(checkbox).toBeChecked());
  });

  it("l?sst die Checkbox deaktiviert, wenn keine Regeln existieren", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([] as never);

    render(<TestCasePanel projectId={1} />);

    const checkbox = await screen.findByRole("checkbox", { name: /mit regeln generieren/i });
    await waitFor(() => expect(checkbox).not.toBeChecked());
  });

  it("l?sst sich per Klick umschalten und steuert generate() mit dem Checkbox-Wert", async () => {
    const generate = vi.fn();
    vi.mocked(useGenerateStore).mockReturnValue({ ...baseStore, generate });
    vi.mocked(rulesApi.list).mockResolvedValue([] as never);

    render(<TestCasePanel projectId={7} />);

    const checkbox = await screen.findByRole("checkbox", { name: /mit regeln generieren/i });
    await waitFor(() => expect(checkbox).not.toBeChecked());
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: /neu generieren/i }));
    expect(generate).toHaveBeenCalledWith(7, true, undefined);
  });

  it("beh?lt den umgeschalteten Zustand bei einem Re-Render", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([] as never);

    const { rerender } = render(<TestCasePanel projectId={7} />);

    const checkbox = await screen.findByRole("checkbox", { name: /mit regeln generieren/i });
    await waitFor(() => expect(checkbox).not.toBeChecked());
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    rerender(<TestCasePanel projectId={7} />);
    expect(screen.getByRole("checkbox", { name: /mit regeln generieren/i })).toBeChecked();
  });
});

// BUGFIX React #300 ("Rendered fewer hooks than expected"): Die Komponente darf die Anzahl
// der Hook-Aufrufe zwischen Renders nicht aendern. Die Tests nutzen den ECHTEN Generate- und
// Decision-Table-Store (nur die API ist gemockt), damit der Hook-Fehler reproduzierbar ist.
describe("TestCasePanel - BUGFIX React #300 (Rules of Hooks)", () => {
  const ALL_STRATEGIES = ["each", "linear", "all", "pairwise", "risk_based", "t_wise", "mcdc"] as const;

  let realGenerateStore: typeof useGenerateStore;
  let initialGenerateState: ReturnType<typeof useGenerateStore.getState>;
  const initialDecisionTableState = useDecisionTableStore.getState();

  const testcasesResponse = {
    testcases: [
      { id: 1, name: "TC_1", assignments: { Kategorie1: "Wert1", Kategorie2: "WertA" }, risk_coverage: 1.0 },
      { id: 2, name: "TC_2", assignments: { Kategorie1: "Wert2", Kategorie2: "WertB" }, risk_coverage: 2.0 },
    ],
    risk_summary: null,
    result_categories: [],
  };

  beforeAll(async () => {
    // Echter Store (nicht gemockt) fuer Reproduktion des Hook-Fehlers
    const actual = await vi.importActual<typeof import("../../store/generateStore")>(
      "../../store/generateStore",
    );
    realGenerateStore = actual.useGenerateStore;
    initialGenerateState = realGenerateStore.getState();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(generateApi.listGenerations).mockResolvedValue([] as never);
    vi.mocked(generateApi.run).mockResolvedValue({ generation_id: 42, count: 2 } as never);
    vi.mocked(generateApi.getTestcases).mockResolvedValue(testcasesResponse as never);
    vi.mocked(useGenerateStore).mockImplementation(realGenerateStore);
    realGenerateStore.setState(initialGenerateState, true);
    useDecisionTableStore.setState(initialDecisionTableState, true);
  });

  it("a) Strategiewechsel t_wise <-> each per Rerender wirft keinen Hook-Fehler", () => {
    const { rerender } = render(<TestCasePanel projectId={1} />);

    act(() => realGenerateStore.setState({ strategy: "t_wise" }));
    rerender(<TestCasePanel projectId={1} />);
    expect(screen.getByText("T-Stärke")).toBeInTheDocument();

    act(() => realGenerateStore.setState({ strategy: "each" }));
    rerender(<TestCasePanel projectId={1} />);
    expect(screen.queryByText("T-Stärke")).not.toBeInTheDocument();
  });

  it("b) Loading-Wechsel true -> false wirft keinen Hook-Fehler", () => {
    const { rerender } = render(<TestCasePanel projectId={1} />);

    act(() => realGenerateStore.setState({ loading: true }));
    rerender(<TestCasePanel projectId={1} />);
    expect(screen.getByRole("button", { name: /generiere/i })).toBeDisabled();

    act(() => realGenerateStore.setState({ loading: false }));
    rerender(<TestCasePanel projectId={1} />);
    expect(screen.getByRole("button", { name: /neu generieren/i })).toBeEnabled();
  });

  // Hinweis: Die API-Antworten sind bewusst DEFERRED (nicht sofort aufgeloest). Ein sofort
  // aufgeloestes Promise wuerde den Zwischenzustand loading=true im selben Batch verschlucken,
  // sodass der Hook-Fehler nie gerendert wird. Im Browser liegen zwischen Klick und Antwort
  // Netzwerk-Tasks; genau das bildet das deferred Promise nach.
  const deferred = <T,>() => {
    let resolve!: (value: T) => void;
    const promise = new Promise<T>((r) => {
      resolve = r;
    });
    return { promise, resolve };
  };

  it.each(ALL_STRATEGIES)(
    "c) 'Neu generieren' mit Strategie %s zeigt Testfaelle-Tabelle ohne Fehler",
    async (strategy) => {
      realGenerateStore.setState({ strategy });
      const run = deferred<{ generation_id: number; count: number }>();
      vi.mocked(generateApi.run).mockReturnValue(run.promise as never);
      const { container } = render(<TestCasePanel projectId={1} />);

      // Synchroner Klick: Zwischen-Render mit loading=true wird sofort gerendert
      fireEvent.click(screen.getByRole("button", { name: /neu generieren/i }));
      expect(screen.getByRole("button", { name: /generiere/i })).toBeDisabled();

      await act(async () => {
        run.resolve({ generation_id: 42, count: 2 });
      });

      await waitFor(() => expect(container.querySelectorAll("tbody tr")).toHaveLength(2));
      expect(screen.getByText("Wert1")).toBeInTheDocument();
      expect(generateApi.run).toHaveBeenCalledWith(1, expect.objectContaining({ strategy }));
    },
  );

  it("d) 'Vorherige Generierung laden' zeigt Testfaelle-Tabelle ohne Fehler", async () => {
    vi.mocked(generateApi.listGenerations).mockResolvedValue([
      { id: 5, name: "Lauf A" },
    ] as never);
    const testcases = deferred<typeof testcasesResponse>();
    vi.mocked(generateApi.getTestcases).mockReturnValue(testcases.promise as never);
    const { container } = render(<TestCasePanel projectId={1} />);

    await screen.findByText("Lauf A");
    const historySelect = screen.getByText("-- Generierung wählen --").closest("select");
    expect(historySelect).not.toBeNull();

    // Synchroner Wechsel: Zwischen-Render mit loading=true wird sofort gerendert
    fireEvent.change(historySelect!, { target: { value: "5" } });
    expect(screen.getByText(/Lade Testfälle/)).toBeInTheDocument();

    await act(async () => {
      testcases.resolve(testcasesResponse);
    });

    await waitFor(() => expect(container.querySelectorAll("tbody tr")).toHaveLength(2));
    expect(generateApi.getTestcases).toHaveBeenCalledWith(5);
  });

  it("e) Entscheidungstabelle-Modus an/aus: Sperren + Hinweis, danach ohne Exception zurueck", () => {
    act(() => useDecisionTableStore.setState({ mode: true }));
    const { container } = render(<TestCasePanel projectId={1} />);

    expect(screen.getByText(/Entscheidungstabelle-Modus aktiv/)).toBeInTheDocument();
    expect(container.querySelector("select")).toBeDisabled();
    expect(screen.getByRole("button", { name: /neu generieren/i })).toBeDisabled();

    act(() => useDecisionTableStore.setState({ mode: false }));

    expect(screen.queryByText(/Entscheidungstabelle-Modus aktiv/)).not.toBeInTheDocument();
    expect(container.querySelector("select")).toBeEnabled();
    expect(screen.getByRole("button", { name: /neu generieren/i })).toBeEnabled();
  });
});
