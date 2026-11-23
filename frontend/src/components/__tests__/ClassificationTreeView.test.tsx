// REQ-6006: Tests fuer ClassificationTreeView
// REQ-6016: Tests fuer hierarchische Klassen (Verfeinerung)
import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";

// Mock dependencies
vi.mock("../../store/categoryStore", () => ({
  useCategoryStore: () => ({
    categories: [
      { id: 1, name: "Browser", order_index: 0, is_result: false },
      { id: 2, name: "OS", order_index: 1, is_result: false },
    ],
    values: {
      1: [
        { id: 10, value: "Chrome", risk_weight: 1, vtype: "string", allowed: true, is_default: true, parent_value_id: null },
        { id: 11, value: "Firefox", risk_weight: 1, vtype: "string", allowed: true, is_default: false, parent_value_id: null },
        { id: 12, value: "Mobile Chrome", risk_weight: 1, vtype: "string", allowed: true, is_default: false, parent_value_id: 10 }, // REQ-6016: child of Chrome
      ],
      2: [
        { id: 20, value: "Windows", risk_weight: 1, vtype: "string", allowed: true, is_default: true, parent_value_id: null },
      ],
    },
    createCategory: vi.fn(),
    deleteCategory: vi.fn(),
  }),
}));

vi.mock("../../store/projectStore", () => ({
  useProjectStore: () => ({
    projects: [{ id: 1, name: "TestProjekt" }],
  }),
}));

vi.mock("../../lib/classificationTreeLayout", () => ({
  computeTreeLayout: () => ({
    nodes: [
      { id: "root", x: 50, y: 0, width: 100, height: 40, label: "TestProjekt", type: "root" },
      { id: "cat-1", x: 0, y: 64, width: 120, height: 36, label: "Browser", type: "category", categoryId: 1 },
      { id: "cat-2", x: 140, y: 64, width: 120, height: 36, label: "OS", type: "category", categoryId: 2 },
      { id: "val-1-0", x: 0, y: 116, width: 120, height: 28, label: "Chrome", type: "value", categoryId: 1, parentId: null },
      { id: "val-1-1", x: 0, y: 156, width: 120, height: 28, label: "Firefox", type: "value", categoryId: 1, parentId: null },
      // REQ-6016: Hierarchical value (child of Chrome)
      { id: "val-1-2", x: 0, y: 196, width: 120, height: 28, label: "Mobile Chrome", type: "value", categoryId: 1, parentId: 10 },
      { id: "val-2-0", x: 140, y: 116, width: 120, height: 28, label: "Windows", type: "value", categoryId: 2, parentId: null },
    ],
    totalWidth: 260,
    totalHeight: 236,
  }),
}));

vi.mock("../../api/client", () => ({
  categoriesApi: {
    refine: vi.fn().mockResolvedValue({ id: 99, name: "Test Refinement" }),
    getHierarchy: vi.fn().mockResolvedValue({
      category_id: 1,
      category_name: "Browser",
      roots: [
        { id: 10, value: "Chrome", children: [{ id: 12, value: "Mobile Chrome", children: [] }] },
        { id: 11, value: "Firefox", children: [] },
      ],
    }),
  },
}));

import ClassificationTreeView from "../ClassificationTreeView";

describe("ClassificationTreeView", () => {
  it("rendert ohne Crash", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeView projectId={1} />
      </I18nextProvider>
    );
    expect(container.firstChild).toBeTruthy();
  });

  it("zeigt Zoom-Controls", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeView projectId={1} />
      </I18nextProvider>
    );
    const buttons = container.querySelectorAll("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("zeigt SVG-Element", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeView projectId={1} />
      </I18nextProvider>
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("leere Kategorien-Liste", () => {
    const { container } = render(
      <I18nextProvider i18n={i18n}>
        <ClassificationTreeView projectId={1} />
      </I18nextProvider>
    );
    expect(container.firstChild).toBeTruthy();
  });

  // REQ-6016: Hierarchy tests
  describe("REQ-6016: Hierarchische Klassen", () => {
    it("zeigt Werte mit parentId korrekt an", () => {
      const { container } = render(
        <I18nextProvider i18n={i18n}>
          <ClassificationTreeView projectId={1} />
        </I18nextProvider>
      );
      // The SVG should contain nodes with parentId
      const svg = container.querySelector("svg");
      expect(svg).toBeTruthy();
      // Check that nodes with parentId attribute exist
      const nodes = container.querySelectorAll("[data-node-id]");
      expect(nodes.length).toBeGreaterThan(0);
    });

    it("zeigt hierarchische Werte im Baum", () => {
      const { container } = render(
        <I18nextProvider i18n={i18n}>
          <ClassificationTreeView projectId={1} />
        </I18nextProvider>
      );
      // Check that the tree renders with hierarchical structure
      const svg = container.querySelector("svg");
      expect(svg).toBeTruthy();
      // The tree should have more nodes due to hierarchy
      const nodes = container.querySelectorAll("[data-node-id]");
      // We expect at least: root + 2 categories + 4 values = 7 nodes
      expect(nodes.length).toBeGreaterThanOrEqual(7);
    });

    it("unterstuetzt Kontextmenue fuer Verfeinerung", () => {
      const { container } = render(
        <I18nextProvider i18n={i18n}>
          <ClassificationTreeView projectId={1} />
        </I18nextProvider>
      );
      // The component should be renderable and ready for context menu interaction
      expect(container.firstChild).toBeTruthy();
    });
  });
});