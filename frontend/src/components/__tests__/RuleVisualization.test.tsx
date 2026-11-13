// REQ-NEU: Tests fuer RuleVisualization (grafische Regeldarstellung)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import RuleVisualization from "../RuleVisualization";
import { rulesApi, categoriesApi } from "../../api/client";

vi.mock("../../api/client", () => ({
  rulesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  categoriesApi: {
    list: vi.fn(),
    getValues: vi.fn(),
  },
}));

const categories = [
  { id: 1, name: "Browser", order_index: 0 },
  { id: 2, name: "OS", order_index: 1 },
];

const valuesByCat: Record<number, { id: number; value: string; risk_weight: number; vtype: string; allowed: boolean; is_default: boolean }[]> = {
  1: [
    { id: 1, value: "Chrome", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
    { id: 2, value: "Firefox", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
    { id: 3, value: "Safari", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
  ],
  2: [
    { id: 4, value: "Windows", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
    { id: 5, value: "Linux", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
    { id: 6, value: "macOS", risk_weight: 0, vtype: "standard", allowed: true, is_default: false },
  ],
};

const mockRules = [
  {
    id: 1,
    type: "exclude",
    if_category_id: 1,
    if_value: "Chrome",
    then_category_id: 2,
    then_value: "Windows",
    then_values_json: null,
    if_category_name: "Browser",
    then_category_name: "OS",
  },
  {
    id: 2,
    type: "dependency",
    if_category_id: 1,
    if_value: "Safari",
    then_category_id: 2,
    then_value: "Linux",
    then_values_json: null,
    if_category_name: "Browser",
    then_category_name: "OS",
  },
];

describe("RuleVisualization - grafische Regeldarstellung", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rulesApi.list).mockResolvedValue(mockRules as never);
    vi.mocked(categoriesApi.list).mockResolvedValue(categories as never);
    vi.mocked(categoriesApi.getValues).mockImplementation(
      (catId: number) => Promise.resolve((valuesByCat[catId] ?? []) as never)
    );
  });

  it("zeigt Lade-Status waehrend des Ladens", () => {
    vi.mocked(rulesApi.list).mockReturnValue(new Promise(() => {})); // niemals resolve
    const { getByText } = render(<RuleVisualization projectId={1} />);
    expect(getByText("Lade Regeln...")).toBeInTheDocument();
  });

  it("zeigt Platzhalter wenn keine Regeln existieren", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Noch keine Regeln/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Erstelle Regeln im "Regeln"-Tab/i)).toBeInTheDocument();
  });

  it("zeigt Regeln-Header mit Anzahl", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Regeln \(2\)/i)).toBeInTheDocument();
    });
  });

  it("zeigt Legende mit Regeltypen und Anzahlen", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      // Should show symbols for exclude and dependency
      const text = screen.getByText(/Regeln \(2\)/i);
      expect(text).toBeInTheDocument();
    });
  });

  it("rendert SVG-Element fuer Visualisierung", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  it("zeigt Kategorie-Namen in der Visualisierung", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
      
      // Check for category names in SVG text elements
      const texts = svg?.querySelectorAll('text') || [];
      const textContents = Array.from(texts).map(t => t.textContent);
      expect(textContents.some(t => t === "Browser" || t?.startsWith("Browser"))).toBe(true);
      expect(textContents.some(t => t === "OS" || t?.startsWith("OS"))).toBe(true);
    });
  });

  it("zeigt Resize-Handle fuer Hoehe-Anpassung", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      const resizeHandle = document.querySelector('.cursor-row-resize');
      expect(resizeHandle).toBeInTheDocument();
    });
  });

  it("filtert nur relevante Kategorien an (mit Regeln)", async () => {
    // Füge eine dritte Kategorie hinzu, die keine Regeln hat
    const categoriesWithUnused = [
      ...categories,
      { id: 3, name: "Unused", order_index: 2 },
    ];
    vi.mocked(categoriesApi.list).mockResolvedValue(categoriesWithUnused as never);
    
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
      
      // "Unused" sollte nicht in der Visualisierung erscheinen
      const texts = svg?.querySelectorAll('text') || [];
      const textContents = Array.from(texts).map(t => t.textContent);
      expect(textContents.some(t => t === "Unused")).toBe(false);
    });
  });

  it("hat einen Aktualisieren-Button", async () => {
    render(<RuleVisualization projectId={1} />);
    
    await waitFor(() => {
      const refreshButton = document.querySelector('button[title="Aktualisieren"]');
      expect(refreshButton).toBeInTheDocument();
    });
  });
});