// REQ-5002/REQ-5003: Entscheidungstabelle laedt Ursachen und Wirkungen aus dem Projekt
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useDecisionTableStore } from "../decisionTableStore";

describe("decisionTableStore.loadCategories", () => {
  const original = globalThis.fetch;
  beforeEach(() => {
    useDecisionTableStore.setState({ causes: [], effects: [], loading: false, error: null });
  });
  afterEach(() => {
    globalThis.fetch = original;
  });

  it("setzt causes und effects aus GET /api/decision-table/categories/{pid}", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        causes: [{ id: 1, name: "Farbe" }],
        effects: [{ id: 2, name: "Ergebnis" }],
      }),
    }) as unknown as typeof fetch;

    await useDecisionTableStore.getState().loadCategories(7);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/decision-table/categories/7",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(useDecisionTableStore.getState().causes).toEqual([{ id: 1, name: "Farbe" }]);
    expect(useDecisionTableStore.getState().effects).toEqual([{ id: 2, name: "Ergebnis" }]);
  });

  it("setzt error bei fehlgeschlagenem Laden", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: "x" }) }) as unknown as typeof fetch;
    await useDecisionTableStore.getState().loadCategories(7);
    expect(useDecisionTableStore.getState().error).toBeTruthy();
  });
});
