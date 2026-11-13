// REQ-5000 + REQ-5003 + REQ-5004 + REQ-5005: Tests fuer decisionTableStore
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDecisionTableStore } from "../decisionTableStore";

describe("decisionTableStore - REQ-5000/5003/5004/5005", () => {
  beforeEach(() => {
    // Reset store state before each test
    useDecisionTableStore.setState({
      mode: false,
      causes: [],
      effects: [],
      rules: [],
      loading: false,
      error: null,
      canGenerate: false,
      // REQ-5013/5014/5019/5020: Optimierungsfelder resetten
      checksum: null,
      contradictions: [],
      gaps: [],
      collapsedCount: 0,
      // REQ-5021: Priorisierung resetten
      effectPriorities: {},
    });
  });

  describe("setMode - REQ-5000", () => {
    it("schaltet den Modus ein", () => {
      const { result } = renderHook(() => useDecisionTableStore());
      act(() => {
        result.current.setMode(true);
      });
      expect(result.current.mode).toBe(true);
    });

    it("schaltet den Modus aus und setzt Daten zurueck", () => {
      const { result } = renderHook(() => useDecisionTableStore());
      act(() => {
        result.current.setMode(true);
      });
      act(() => {
        result.current.setMode(false);
      });
      expect(result.current.mode).toBe(false);
      expect(result.current.causes).toEqual([]);
      expect(result.current.effects).toEqual([]);
      expect(result.current.rules).toEqual([]);
      expect(result.current.canGenerate).toBe(false);
    });
  });

  describe("generate - REQ-5005", () => {
    it("setzt causes, effects, rules bei erfolgreicher Generierung", async () => {
      const mockResponse = {
        causes: [
          { id: 1, name: "Ursache 1", values: ["Y", "N"] },
          { id: 2, name: "Ursache 2", values: ["Y", "N"] },
        ],
        effects: [
          { id: 10, name: "Wirkung 1" },
        ],
        rules: [
          { id: 1, causes: { 1: "Y", 2: "Y" }, effects: { 10: null } },
          { id: 2, causes: { 1: "Y", 2: "N" }, effects: { 10: null } },
          { id: 3, causes: { 1: "N", 2: "Y" }, effects: { 10: null } },
          { id: 4, causes: { 1: "N", 2: "N" }, effects: { 10: null } },
        ],
      };

      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockResponse),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.generate(1);
      });

      expect(result.current.causes).toEqual(mockResponse.causes);
      expect(result.current.effects).toEqual(mockResponse.effects);
      expect(result.current.rules).toEqual(mockResponse.rules);
      expect(result.current.canGenerate).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it("setzt error bei fehlgeschlagener Generierung", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "Keine Ursache-Kategorien gefunden" }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.generate(1);
      });

      expect(result.current.error).toBe("Keine Ursache-Kategorien gefunden");
      expect(result.current.loading).toBe(false);
    });

    it("setzt loading waehrend der Generierung", async () => {
      let resolvePromise: (value: unknown) => void;
      global.fetch = vi.fn(() =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      let generatePromise: Promise<void>;
      act(() => {
        generatePromise = result.current.generate(1);
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise!({
          ok: true,
          json: () => Promise.resolve({ causes: [], effects: [], rules: [] }),
        });
        await generatePromise;
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe("updateEffect - REQ-5003", () => {
    it("aendert den Effekt-Wert in einer Regel", () => {
      useDecisionTableStore.setState({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: null } },
          { id: 2, causes: { 1: "N" }, effects: { 10: null } },
        ],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.updateEffect(1, 10, "X");
      });

      expect(result.current.rules[0].effects[10]).toBe("X");
      expect(result.current.rules[1].effects[10]).toBeNull();
    });

    it("setzt den Effekt-Wert zurueck auf null", () => {
      useDecisionTableStore.setState({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: "X" } },
        ],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.updateEffect(1, 10, null);
      });

      expect(result.current.rules[0].effects[10]).toBeNull();
    });

    it("setzt den Effekt-Wert auf Don't Care (—)", () => {
      useDecisionTableStore.setState({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: null } },
        ],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.updateEffect(1, 10, "-");
      });

      expect(result.current.rules[0].effects[10]).toBe("-");
    });
  });

  describe("updateCause - REQ-5004", () => {
    it("aendert den Ursache-Wert in einer Regel", () => {
      useDecisionTableStore.setState({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: null } },
          { id: 2, causes: { 1: "Y" }, effects: { 10: null } },
        ],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.updateCause(1, 1, "N");
      });

      expect(result.current.rules[0].causes[1]).toBe("N");
      expect(result.current.rules[1].causes[1]).toBe("Y");
    });

    it("setzt den Ursache-Wert auf Don't Care (—)", () => {
      useDecisionTableStore.setState({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: null } },
        ],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.updateCause(1, 1, "-");
      });

      expect(result.current.rules[0].causes[1]).toBe("-");
    });
  });

  describe("reset", () => {
    it("setzt alle Daten zurueck", () => {
      useDecisionTableStore.setState({
        mode: true,
        causes: [{ id: 1, name: "C1", values: ["Y", "N"] }],
        effects: [{ id: 10, name: "E1" }],
        rules: [{ id: 1, causes: { 1: "Y" }, effects: { 10: "X" } }],
        canGenerate: true,
        error: "alter Fehler",
      });

      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.reset();
      });

      expect(result.current.causes).toEqual([]);
      expect(result.current.effects).toEqual([]);
      expect(result.current.rules).toEqual([]);
      expect(result.current.canGenerate).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });
});