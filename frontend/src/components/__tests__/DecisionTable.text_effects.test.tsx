/**
 * REQ-5016/5021: DecisionTable Text-Effects & Override Tests
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DecisionTable from "../DecisionTable";
import { useDecisionTableStore } from "../../store/decisionTableStore";

vi.mock("../../store/decisionTableStore", () => ({
  useDecisionTableStore: vi.fn(),
}));

// Helper: Mock-Store mit Standard-Daten (damit die Tabelle rendert)
function mockStoreWithTable(overrides: Record<string, any> = {}) {
  const defaults = {
    effectMode: "binary",
    setEffectMode: () => {},
    enableOverride: false,
    setEnableOverride: () => {},
    effectPriorities: {},
    setEffectPriority: () => {},
    causes: [{ id: 1, name: "C1", values: ["Y", "N"] }],
    effects: [{ id: 1, name: "E1", values: ["Genehmigen", "Ablehnen"] }],
    rules: [{ id: 1, causes: { "1": "Y" }, effects: { "1": null } }],
    loading: false,
    error: null,
    checksum: null,
    contradictions: [],
    gaps: [],
    collapsedCount: 0,
    runCollapse: () => {},
    runValidate: () => {},
    updateEffect: () => {},
    updateCause: () => {},
    projectId: 1,
  };
  return { ...defaults, ...overrides };
}

describe("DecisionTable Text Effects & Override", () => {
  it("zeigt Text/Binar Toggle Button", () => {
    const mocks = mockStoreWithTable();
    (useDecisionTableStore as any).mockImplementation((selector: any) => {
      const str = selector.toString();
      for (const [key, val] of Object.entries(mocks)) {
        if (str.includes(key)) return val;
      }
      return mocks[Object.keys(mocks).find(k => str.includes(k)) ?? ""];
    });
    render(<DecisionTable projectId={1} />);
    // Suche nach Button mit Text "Binar-Modus" oder "Text-Modus"
    const buttons = screen.getAllByRole("button");
    const found = buttons.find(b =>
      b.textContent?.includes("Binar-Modus") || b.textContent?.includes("Text-Modus")
    );
    expect(found).toBeTruthy();
  });

  it("zeigt Override-Modus Button", () => {
    const mocks = mockStoreWithTable();
    (useDecisionTableStore as any).mockImplementation((selector: any) => {
      const str = selector.toString();
      for (const [key, val] of Object.entries(mocks)) {
        if (str.includes(key)) return val;
      }
      return {};
    });
    render(<DecisionTable projectId={1} />);
    const buttons = screen.getAllByRole("button");
    const found = buttons.find(b => b.textContent?.includes("Override"));
    expect(found).toBeTruthy();
  });

  it("zeigt Override-Warnung wenn aktiv", () => {
    const mocks = mockStoreWithTable({ enableOverride: true });
    (useDecisionTableStore as any).mockImplementation((selector: any) => {
      const str = selector.toString();
      for (const [key, val] of Object.entries(mocks)) {
        if (str.includes(key)) return val;
      }
      return {};
    });
    render(<DecisionTable projectId={1} />);
    expect(screen.getByText(/Override-Modus.*Don't Care/i)).toBeTruthy();
  });

  it("zeigt Text-Input im Text-Modus", () => {
    const mocks = mockStoreWithTable({ effectMode: "text" });
    (useDecisionTableStore as any).mockImplementation((selector: any) => {
      const str = selector.toString();
      for (const [key, val] of Object.entries(mocks)) {
        if (str.includes(key)) return val;
      }
      return {};
    });
    render(<DecisionTable projectId={1} />);
    // Im Text-Modus: input mit placeholder="Wirkung" existiert
    const inputs = screen.queryAllByPlaceholderText("Wirkung");
    expect(inputs.length).toBeGreaterThan(0);
  });
});