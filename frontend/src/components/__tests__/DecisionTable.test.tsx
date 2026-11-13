// REQ-5003 + REQ-5004 + REQ-5005: Tests fuer DecisionTable-Komponente
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DecisionTable from "../DecisionTable";
import { useDecisionTableStore } from "../../store/decisionTableStore";

vi.mock("../../store/decisionTableStore", () => ({
  useDecisionTableStore: vi.fn(),
}));

// REQ-5012: Mock des ConstraintDialog
vi.mock("../ConstraintDialog", () => ({
  default: function MockConstraintDialog({ onClose }: { onClose: () => void }) {
    return (
      <div data-testid="constraint-dialog">
        <span>Constraint Dialog Mock</span>
        <button onClick={onClose}>Schliessen</button>
      </div>
    );
  },
}));

describe("DecisionTable - REQ-5003/5004/5005", () => {
  const mockUpdateCause = vi.fn();
  const mockUpdateEffect = vi.fn();

  const mockStore = {
    causes: [
      { id: 1, name: "Ursache 1", values: ["Y", "N"] },
      { id: 2, name: "Ursache 2", values: ["Y", "N"] },
    ],
    effects: [
      { id: 10, name: "Wirkung 1" },
      { id: 11, name: "Wirkung 2" },
    ],
    rules: [
      { id: 1, causes: { 1: "Y", 2: "Y" }, effects: { 10: null, 11: null } },
      { id: 2, causes: { 1: "Y", 2: "N" }, effects: { 10: null, 11: null } },
      { id: 3, causes: { 1: "N", 2: "Y" }, effects: { 10: null, 11: null } },
      { id: 4, causes: { 1: "N", 2: "N" }, effects: { 10: null, 11: null } },
    ],
    loading: false,
    error: null,
    updateCause: mockUpdateCause,
    updateEffect: mockUpdateEffect,
    // REQ-5013/5014/5019/5020: Optimierungsfelder
    checksum: null,
    contradictions: [],
    gaps: [],
    collapsedCount: 0,
    runCollapse: vi.fn(),
    runValidate: vi.fn(),
    // REQ-5021: Priorisierung
    effectPriorities: {},
    setEffectPriority: vi.fn(),
    // EPIC-20 Schulden
    effectMode: "binary" as "binary" | "text",
    setEffectMode: vi.fn(),
    enableOverride: false,
    setEnableOverride: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...mockStore };
      return typeof selector === "function" ? selector(state) : state;
    });
  });

  it("zeigt Ursachen-Zeilen (wenn vorhanden)", () => {
    render(<DecisionTable />);
    expect(screen.getByText("Ursache 1")).toBeInTheDocument();
    expect(screen.getByText("Ursache 2")).toBeInTheDocument();
  });

  it("zeigt Wirkungen-Zeilen (wenn vorhanden)", () => {
    render(<DecisionTable />);
    expect(screen.getByText("Wirkung 1")).toBeInTheDocument();
    expect(screen.getByText("Wirkung 2")).toBeInTheDocument();
  });

  it("zeigt jede Regel als Spalte (R1, R2, R3, R4)", () => {
    render(<DecisionTable />);
    expect(screen.getByText("R1")).toBeInTheDocument();
    expect(screen.getByText("R2")).toBeInTheDocument();
    expect(screen.getByText("R3")).toBeInTheDocument();
    expect(screen.getByText("R4")).toBeInTheDocument();
  });

  it("hat Ursachenzellen mit Y/N/- Dropdown", () => {
    render(<DecisionTable />);
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBeGreaterThan(0);
  });

  it("hat Wirkungszellen mit X/- Dropdown", () => {
    render(<DecisionTable />);
    // Die Wirkungszellen haben option "" (·), "X", "-"
    const options = screen.getAllByText("X");
    expect(options.length).toBeGreaterThan(0);
  });

  it("updateEffect aendert den Wert im Store", () => {
    render(<DecisionTable />);
    const selects = screen.getAllByRole("combobox");
    // 2 causes x 4 rules = 8 cause-selects, dann 2 priority-selects, dann 2 effects x 4 rules = 8 effect-selects
    // Der erste effect-select ist bei Index 10 (8 cause + 2 priority)
    const effectSelect = selects[10];
    fireEvent.change(effectSelect, { target: { value: "X" } });
    expect(mockUpdateEffect).toHaveBeenCalled();
  });

  it("updateCause aendert den Wert im Store", () => {
    render(<DecisionTable />);
    const selects = screen.getAllByRole("combobox");
    const causeSelect = selects[0]; // Erste Ursachezeile, erste Regel
    fireEvent.change(causeSelect, { target: { value: "N" } });
    expect(mockUpdateCause).toHaveBeenCalled();
  });

  it("zeigt Trennlinie zwischen Ursachen und Wirkungen", () => {
    render(<DecisionTable />);
    expect(screen.getByText(/Ursachen \/ Wirkungen/)).toBeInTheDocument();
  });

  it("zeigt Error-State mit Fehlermeldung", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...mockStore, error: "Keine Ursache-Kategorien gefunden", loading: false };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable />);
    expect(screen.getByText("Keine Ursache-Kategorien gefunden")).toBeInTheDocument();
  });

  it("zeigt Loading-State mit 'Lade...'", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...mockStore, loading: true };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable />);
    expect(screen.getByText(/Lade Entscheidungstabelle/)).toBeInTheDocument();
  });

  it("zeigt Empty-State wenn keine Ursachen oder Wirkungen", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...mockStore, rules: [], causes: [], effects: [] };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable />);
    expect(screen.getByText("Keine Ursachen oder Wirkungen gefunden")).toBeInTheDocument();
  });

  it("zeigt 'Regeln generieren' Button wenn Ursachen/Wirkungen da sind, aber keine Regeln", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...mockStore,
        rules: [],
        causes: [{ id: 1, name: "Ursache 1" }],
        effects: [{ id: 2, name: "Wirkung 1" }],
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByLabelText("Regeln generieren")).toBeInTheDocument();
  });

  it("zeigt nur Ursachen wenn keine Wirkungen", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...mockStore,
        effects: [],
        rules: [
          { id: 1, causes: { 1: "Y", 2: "Y" }, effects: {} },
          { id: 2, causes: { 1: "Y", 2: "N" }, effects: {} },
        ],
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable />);
    expect(screen.getByText("Ursache 1")).toBeInTheDocument();
    expect(screen.queryByText(/Ursachen \/ Wirkungen/)).not.toBeInTheDocument();
  });

  // REQ-5012: Constraint-Dialog Integration
  it("zeigt 'Constraint hinzufuegen' Button wenn projectId uebergeben", () => {
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText("Constraint hinzufuegen")).toBeInTheDocument();
  });

  it("zeigt keinen Constraint-Button ohne projectId", () => {
    render(<DecisionTable />);
    expect(screen.queryByText("Constraint hinzufuegen")).not.toBeInTheDocument();
  });

  it("oeffnet ConstraintDialog beim Button-Klick", () => {
    render(<DecisionTable projectId={1} />);
    const btn = screen.getByText("Constraint hinzufuegen");
    fireEvent.click(btn);
    expect(screen.getByTestId("constraint-dialog")).toBeInTheDocument();
  });

  it("schliesst ConstraintDialog mit onClose", () => {
    render(<DecisionTable projectId={1} />);
    const btn = screen.getByText("Constraint hinzufuegen");
    fireEvent.click(btn);
    expect(screen.getByTestId("constraint-dialog")).toBeInTheDocument();

    const closeBtn = screen.getByText("Schliessen");
    fireEvent.click(closeBtn);
    expect(screen.queryByTestId("constraint-dialog")).not.toBeInTheDocument();
  });
});