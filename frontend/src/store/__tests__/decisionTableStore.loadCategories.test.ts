// REQ-5002/REQ-5003: Entscheidungstabelle laedt Ursachen und Wirkungen aus dem Projekt
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useDecisionTableStore } from "../decisionTableStore";

vi.mock("../../api/client", () => ({
  decisionTableApi: {
    loadCategories: vi.fn(),
  },
}));

import { decisionTableApi } from "../../api/client";

describe("decisionTableStore.loadCategories", () => {
  beforeEach(() => {
    useDecisionTableStore.setState({ causes: [], effects: [], loading: false, error: null });
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("setzt causes und effects aus GET /decision-table/categories/{pid}", async () => {
    (decisionTableApi.loadCategories as any).mockResolvedValue({
      causes: [{ id: 1, name: "Farbe" }],
      effects: [{ id: 2, name: "Ergebnis" }],
    });

    await useDecisionTableStore.getState().loadCategories(7);

    expect(decisionTableApi.loadCategories).toHaveBeenCalledWith(7);
    expect(useDecisionTableStore.getState().causes).toEqual([{ id: 1, name: "Farbe" }]);
    expect(useDecisionTableStore.getState().effects).toEqual([{ id: 2, name: "Ergebnis" }]);
  });

  it("setzt error bei fehlgeschlagenem Laden", async () => {
    (decisionTableApi.loadCategories as any).mockRejectedValue(new Error("x"));
    await useDecisionTableStore.getState().loadCategories(7);
    expect(useDecisionTableStore.getState().error).toBeTruthy();
  });
});