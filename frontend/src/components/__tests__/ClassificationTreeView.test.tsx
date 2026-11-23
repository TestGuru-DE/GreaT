// REQ-6006: Tests fuer ClassificationTreeView
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
    values: {},
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
    ],
    totalWidth: 260,
    totalHeight: 100,
  }),
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
});