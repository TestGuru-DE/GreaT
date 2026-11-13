// REQ-5013/5014/5019/5020: DecisionTable Optimization Tests
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

describe("DecisionTable Optimization - REQ-5013/5014/5019/5020", () => {
  const mockRunCollapse = vi.fn();
  const mockRunValidate = vi.fn();

  const baseMockStore = {
    causes: [
      { id: 1, name: "Ursache 1", values: ["Y", "N"] },
    ],
    effects: [
      { id: 10, name: "Wirkung 1" },
    ],
    rules: [
      { id: 1, causes: { 1: "Y" }, effects: { 10: null } },
    ],
    loading: false,
    error: null,
    updateCause: vi.fn(),
    updateEffect: vi.fn(),
    checksum: null,
    contradictions: [],
    gaps: [],
    collapsedCount: 0,
    runCollapse: mockRunCollapse,
    runValidate: mockRunValidate,
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
      const state = { ...baseMockStore };
      return typeof selector === "function" ? selector(state) : state;
    });
  });

  it("zeigt 'Zusammenfassen' Button wenn projectId uebergeben", () => {
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/Zusammenfassen/)).toBeInTheDocument();
  });

  it("zeigt 'Pruefen' Button wenn projectId uebergeben", () => {
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/Pruefen/)).toBeInTheDocument();
  });

  it("zeigt keinen Optimierungsbereich ohne projectId", () => {
    render(<DecisionTable />);
    expect(screen.queryByText(/Zusammenfassen/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Pruefen/)).not.toBeInTheDocument();
  });

  it("zeigt collapsedCount im Button-Text", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = { ...baseMockStore, collapsedCount: 5 };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/5 reduziert/)).toBeInTheDocument();
  });

  it("zeigt Checksum bei 'complete' Status gruen", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...baseMockStore,
        checksum: {
          checksum: 8,
          expected: 8,
          status: "complete",
          message: "Vollstaendig",
        },
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/Vollstaendig/)).toBeInTheDocument();
    expect(screen.getByText(/Checksum:/)).toBeInTheDocument();
  });

  it("zeigt Checksum bei 'overlap' Status gelb", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...baseMockStore,
        checksum: {
          checksum: 10,
          expected: 8,
          status: "overlap",
          message: "Ueberlappung",
        },
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/Ueberlappung/)).toBeInTheDocument();
  });

  it("zeigt Widersprueche in roter Box", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...baseMockStore,
        contradictions: [
          {
            rule_a: 1,
            rule_b: 2,
            message: "Regel R1 und R2 widersprechen sich",
          },
        ],
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/widersprechen/)).toBeInTheDocument();
  });

  it("zeigt Luecken in amber Box", () => {
    vi.mocked(useDecisionTableStore).mockImplementation((selector) => {
      const state = {
        ...baseMockStore,
        gaps: [
          {
            combination: { 1: "Y" },
            message: "Luecke: Y,N nicht abgedeckt",
          },
        ],
      };
      return typeof selector === "function" ? selector(state) : state;
    });
    render(<DecisionTable projectId={1} />);
    // Spezifischer: "Luecke: Y,N nicht abgedeckt" (nicht der Header)
    expect(screen.getByText("Luecke: Y,N nicht abgedeckt")).toBeInTheDocument();
    expect(screen.getByText(/Luecke\(n\) in der Abdeckung/)).toBeInTheDocument();
  });

  it("ruft runCollapse beim Button-Klick auf", () => {
    render(<DecisionTable projectId={1} />);
    const btn = screen.getByText(/Zusammenfassen/);
    fireEvent.click(btn);
    expect(mockRunCollapse).toHaveBeenCalledWith(1);
  });

  it("ruft runValidate beim Button-Klick auf", () => {
    render(<DecisionTable projectId={1} />);
    const btn = screen.getByText(/Pruefen/);
    fireEvent.click(btn);
    expect(mockRunValidate).toHaveBeenCalledWith(1);
  });
});