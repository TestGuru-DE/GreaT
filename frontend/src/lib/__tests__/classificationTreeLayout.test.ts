// REQ-6006: Unit-Tests fuer classificationTreeLayout

import { describe, expect, it } from "vitest";
import { computeTreeLayout } from "../classificationTreeLayout";

describe("computeTreeLayout", () => {
  it("erzeugt Root + Kategorien + Werte", () => {
    const result = computeTreeLayout("TestProjekt", [
      { id: 1, name: "Browser", values: [{ name: "Chrome" }, { name: "Firefox" }] },
      { id: 2, name: "OS", values: [{ name: "Win" }, { name: "Linux" }] },
    ]);
    expect(result.nodes.length).toBe(7); // root + 2 cats + 4 values
    expect(result.nodes[0].type).toBe("root");
    expect(result.nodes[0].label).toBe("TestProjekt");
  });

  it("keine negative Position", () => {
    const result = computeTreeLayout("Projekt", [
      { id: 1, name: "A", values: [{ name: "a1" }] },
    ]);
    for (const n of result.nodes) {
      expect(n.x).toBeGreaterThanOrEqual(0);
      expect(n.y).toBeGreaterThanOrEqual(0);
    }
  });

  it("keine Ueberlappung horizontal", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "A", values: [{ name: "a1" }] },
      { id: 2, name: "B", values: [{ name: "b1" }] },
    ]);
    const cats = result.nodes.filter((n) => n.type === "category");
    expect(cats[1].x).toBeGreaterThan(cats[0].x + cats[0].width);
  });

  it("keine Ueberlappung vertikal", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "A", values: [{ name: "a1" }, { name: "a2" }] },
    ]);
    const vals = result.nodes.filter((n) => n.type === "value" && n.categoryId === 1);
    expect(vals[1].y).toBeGreaterThan(vals[0].y + vals[0].height);
  });

  it("30 Kategorien x 20 Werte < totalWidth", () => {
    const cats = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      name: `Cat${i}`,
      values: Array.from({ length: 20 }, (_, j) => ({ name: `v${j}` })),
    }));
    const result = computeTreeLayout("Big", cats);
    expect(result.totalWidth).toBeGreaterThan(0);
    expect(result.totalHeight).toBeGreaterThan(0);
    // No overlap check for a sample
    const catNodes = result.nodes.filter((n) => n.type === "category");
    for (let i = 1; i < catNodes.length; i++) {
      expect(catNodes[i].x).toBeGreaterThan(catNodes[i - 1].x + catNodes[i - 1].width);
    }
  });

  it("Root ist zentriert", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "A", values: [{ name: "a1" }] },
      { id: 2, name: "B", values: [{ name: "b1" }] },
    ]);
    const root = result.nodes[0];
    const center = root.x + root.width / 2;
    expect(center).toBeCloseTo(result.totalWidth / 2, 0);
  });

  it("leere Kategorien-Liste", () => {
    const result = computeTreeLayout("P", []);
    expect(result.nodes.length).toBe(1); // only root
    expect(result.totalWidth).toBe(0);
  });

  it("leere Werte-Liste", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "A", values: [] },
    ]);
    const vals = result.nodes.filter((n) => n.type === "value");
    expect(vals.length).toBe(0);
  });

  it("isError-Flag wird uebernommen", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "A", values: [{ name: "err", isError: true }] },
    ]);
    const val = result.nodes.find((n) => n.type === "value");
    expect(val?.isError).toBe(true);
  });

  it("isResult-Flag auf Kategorie", () => {
    const result = computeTreeLayout("P", [
      { id: 1, name: "Ergebnis", isResult: true, values: [{ name: "ok" }] },
    ]);
    const cat = result.nodes.find((n) => n.type === "category");
    expect(cat?.isResult).toBe(true);
  });
});