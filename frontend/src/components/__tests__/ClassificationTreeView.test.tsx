// REQ-6006: Klassifikationsbaum – Tests zu C-15 bis C-23 (echtes Layout, gemockter Store/API)
// REQ-6016: Verfeinerung per Kontextmenue
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";

const store = vi.hoisted(() => ({
  categories: [
    { id: 1, name: "Browser", order_index: 0, is_result: false },
    { id: 2, name: "Ergebnis", order_index: 1, is_result: true },
  ],
  values: {
    1: [
      { id: 10, value: "Chrome", risk_weight: 1, vtype: "string", allowed: true, is_default: true, parent_value_id: null },
      { id: 11, value: "Firefox", risk_weight: 1, vtype: "string", allowed: true, is_default: false, parent_value_id: null },
      { id: 12, value: "IE6", risk_weight: 1, vtype: "string", allowed: false, is_default: false, parent_value_id: null },
    ],
    2: [
      { id: 20, value: "ok", risk_weight: 1, vtype: "string", allowed: true, is_default: true, parent_value_id: null },
      { id: 21, value: "Fehler", risk_weight: 1, vtype: "string", allowed: true, is_default: false, parent_value_id: null },
    ],
  } as Record<number, unknown[]>,
  error: null,
  canUndo: true,
  canRedo: true,
  busy: false,
  fetchAllValues: vi.fn().mockResolvedValue(undefined),
  fetchCategories: vi.fn().mockResolvedValue(undefined),
  createCategory: vi.fn().mockResolvedValue({ id: 3, name: "Neue Klassifikation" }),
  deleteCategory: vi.fn().mockResolvedValue(undefined),
  renameCategory: vi.fn().mockResolvedValue(undefined),
  reorderCategories: vi.fn().mockResolvedValue(undefined),
  createValue: vi.fn().mockResolvedValue({ id: 13, value: "Neue Klasse" }),
  deleteValue: vi.fn().mockResolvedValue(undefined),
  renameValue: vi.fn().mockResolvedValue(undefined),
  reorderValues: vi.fn().mockResolvedValue(undefined),
  undo: vi.fn().mockResolvedValue(undefined),
  redo: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../store/categoryStore", () => ({ useCategoryStore: () => store }));
vi.mock("../../store/projectStore", () => ({
  useProjectStore: (sel: (s: unknown) => unknown) => sel({ projects: [{ id: 7, name: "Shop" }] }),
}));

const api = vi.hoisted(() => ({
  listGenerations: vi.fn(),
  getTestcases: vi.fn(),
  check: vi.fn(),
  createSeeds: vi.fn(),
  refine: vi.fn(),
}));
vi.mock("../../api/client", () => ({
  generateApi: { listGenerations: api.listGenerations, getTestcases: api.getTestcases },
  testcaseCheckApi: { check: api.check },
  seedApi: { create: api.createSeeds },
  categoriesApi: { refine: api.refine },
}));

import ClassificationTreeView, { TREE_COLORS } from "../ClassificationTreeView";

function renderTree() {
  return render(
    <I18nextProvider i18n={i18n}>
      <ClassificationTreeView projectId={7} />
    </I18nextProvider>,
  );
}

const nodeRect = (container: HTMLElement, nodeId: string) =>
  container.querySelector(`g[data-node-id="${nodeId}"] rect`) as SVGRectElement;
const canvas = () => screen.getByLabelText(/Klassifikationsbaum und Testfallmatrix/);

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage("de");
  api.listGenerations.mockResolvedValue([{ id: 5, name: "Gen 5" }]);
  api.getTestcases.mockResolvedValue({
    testcases: [{ id: 50, name: "TC_1", assignments: { Browser: "Firefox", Ergebnis: "ok" }, has_error_value: false }],
  });
  api.check.mockResolvedValue({ valid: true, completable: true, violations: [] });
  api.createSeeds.mockResolvedValue({ id: 1, name: "Handarbeit", seed_count: 1, warnings: [] });
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

describe("C-15: alle Klassen laden", () => {
  it("laedt die Werte aller Kategorien beim Oeffnen", () => {
    renderTree();
    expect(store.fetchAllValues).toHaveBeenCalled();
  });
});

describe("C-16: Matrix mit Punkt je Klasse, unter den Klassen ausgerichtet", () => {
  it("setzt den Punkt genau in die Spalte der gewaehlten Klasse", async () => {
    const { container } = renderTree();
    const dot = await waitFor(() => {
      const d = container.querySelector('circle[data-dot="tc-50:Browser=Firefox"]');
      expect(d).not.toBeNull();
      return d as SVGCircleElement;
    });
    const rect = nodeRect(container, "val-1-11");
    const center = Number(rect.getAttribute("x")) + Number(rect.getAttribute("width")) / 2;
    expect(Number(dot.getAttribute("cx"))).toBe(center);
    // Klassen nebeneinander (gleiche Zeile), nicht untereinander
    expect(nodeRect(container, "val-1-10").getAttribute("y")).toBe(rect.getAttribute("y"));
  });
});

describe("C-17: Bearbeiten im Baum", () => {
  it("benennt eine Klasse per Doppelklick um", async () => {
    const { container } = renderTree();
    fireEvent.doubleClick(container.querySelector('g[data-node-id="val-1-11"]')!);
    const input = screen.getByRole("textbox", { name: /Umbenennen/ });
    fireEvent.change(input, { target: { value: "Edge" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(store.renameValue).toHaveBeenCalledWith(1, 11, "Edge"));
  });

  it("benennt eine ausgewaehlte Klassifikation mit F2 um", async () => {
    const { container } = renderTree();
    fireEvent.click(container.querySelector('g[data-node-id="cat-1"]')!);
    fireEvent.keyDown(canvas(), { key: "F2" });
    const input = screen.getByRole("textbox", { name: /Umbenennen/ });
    fireEvent.change(input, { target: { value: "Webbrowser" } });
    fireEvent.blur(input);
    await waitFor(() => expect(store.renameCategory).toHaveBeenCalledWith(1, "Webbrowser"));
  });

  it("loescht die ausgewaehlte Klasse mit Entf nach Rueckfrage", async () => {
    const { container } = renderTree();
    fireEvent.click(container.querySelector('g[data-node-id="val-1-10"]')!);
    fireEvent.keyDown(canvas(), { key: "Delete" });
    await waitFor(() => expect(store.deleteValue).toHaveBeenCalledWith(1, 10, false));
    expect(window.confirm).toHaveBeenCalled();
  });

  it("legt eine Klasse in der ausgewaehlten Klassifikation an", async () => {
    const { container } = renderTree();
    fireEvent.click(container.querySelector('g[data-node-id="cat-1"]')!);
    fireEvent.click(screen.getByRole("button", { name: "+ Klasse" }));
    await waitFor(() => expect(store.createValue).toHaveBeenCalledWith(1, "Neue Klasse"));
  });

  it("verschiebt Klassen mit Alt+Pfeil und Klassifikationen per Ziehen", async () => {
    const { container } = renderTree();
    fireEvent.click(container.querySelector('g[data-node-id="val-1-10"]')!);
    fireEvent.keyDown(canvas(), { key: "ArrowRight", altKey: true });
    await waitFor(() => expect(store.reorderValues).toHaveBeenCalledWith(1, [11, 10, 12]));

    fireEvent.pointerDown(container.querySelector('g[data-node-id="cat-2"]')!);
    fireEvent.pointerUp(container.querySelector('g[data-node-id="cat-1"]')!);
    await waitFor(() => expect(store.reorderCategories).toHaveBeenCalledWith(7, [2, 1]));
  });
});

describe("C-18: Undo/Redo per Tastatur", () => {
  it("ruft Undo und Redo des Stores auf", () => {
    renderTree();
    fireEvent.keyDown(canvas(), { key: "z", ctrlKey: true });
    fireEvent.keyDown(canvas(), { key: "y", ctrlKey: true });
    expect(store.undo).toHaveBeenCalledTimes(1);
    expect(store.redo).toHaveBeenCalledTimes(1);
  });
});

describe("C-19: manuelle Testfaelle", () => {
  it("markiert Regelverstoesse sofort und speichert als Seed-Satz", async () => {
    api.check.mockResolvedValue({ valid: false, completable: false, violations: ["Constraint: Kein IE6"] });
    const { container } = renderTree();
    fireEvent.click(screen.getByRole("button", { name: "+ Testfall" }));
    fireEvent.click(container.querySelector('rect[data-cell="m-1:Browser=IE6"]')!);
    await waitFor(() => expect(container.querySelector('g[data-row="m-1"]')?.getAttribute("data-row-state")).toBe("invalid"));
    expect(api.check).toHaveBeenCalledWith(7, { Browser: "IE6" });
    expect(container.querySelector('circle[data-dot="m-1:Browser=IE6"]')).not.toBeNull();

    fireEvent.change(screen.getByRole("textbox", { name: "Name des Seed-Satzes" }), { target: { value: "Handarbeit" } });
    fireEvent.click(screen.getByRole("button", { name: "Als Seed-Satz speichern" }));
    await waitFor(() => expect(api.createSeeds).toHaveBeenCalledWith(7, {
      name: "Handarbeit", seeds: [{ Browser: "IE6", Ergebnis: null }],
    }));
  });
});

describe("C-21/C-22: Lesbarkeit und Beschriftung", () => {
  const luminance = (hex: string) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
      .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const contrast = (a: string, b: string) => {
    const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };

  it.each([
    ["rootText", "rootFill"], ["categoryText", "categoryFill"], ["categoryText", "resultFill"],
    ["classText", "classFill"], ["errorText", "errorFill"], ["rowText", "invalidRow"],
    ["rowText", "incompleteRow"], ["rowText", "manualRow"], ["rowText", "background"],
  ] as const)("Kontrast %s auf %s >= 4,5:1", (fg, bg) => {
    expect(contrast(TREE_COLORS[fg], TREE_COLORS[bg])).toBeGreaterThanOrEqual(4.5);
  });

  it("beschriftet Fehlerwert, Standardwert und Ergebnis und zeigt eine Legende", () => {
    const { container } = renderTree();
    expect(container.querySelector('g[data-node-id="val-1-12"]')?.textContent).toContain("Fehlerwert");
    expect(container.querySelector('g[data-node-id="val-1-10"]')?.textContent).toContain("Standard");
    expect(container.querySelector('g[data-node-id="cat-2"]')?.textContent).toContain("Ergebnis");
    expect(screen.getByTestId("tree-legend").textContent).toContain("Fehlerwert");
  });
});

describe("C-23: Zoom", () => {
  it("Strg+Mausrad zoomt den Baum, ohne die Seite zu scrollen", () => {
    renderTree();
    const event = new WheelEvent("wheel", { deltaY: -100, ctrlKey: true, bubbles: true, cancelable: true });
    act(() => { canvas().dispatchEvent(event); });
    expect(event.defaultPrevented).toBe(true);
    expect(screen.getByTestId("zoom-level").textContent).toBe("110 %");
  });

  it("Einpassen richtet den Zoom an der verfuegbaren Breite aus", () => {
    renderTree();
    Object.defineProperty(canvas(), "clientWidth", { configurable: true, value: 240 });
    Object.defineProperty(canvas(), "clientHeight", { configurable: true, value: 2000 });
    fireEvent.click(screen.getByRole("button", { name: "Einpassen" }));
    expect(screen.getByTestId("zoom-level").textContent).not.toBe("100 %");
  });
});

describe("REQ-6016: Verfeinerung", () => {
  it("bietet im Kontextmenue einer Klasse die Verfeinerung an", () => {
    const { container } = renderTree();
    fireEvent.contextMenu(container.querySelector('g[data-node-id="val-1-10"]')!);
    expect(screen.getByRole("menuitem", { name: "Verfeinern …" })).toBeInTheDocument();
  });
});
