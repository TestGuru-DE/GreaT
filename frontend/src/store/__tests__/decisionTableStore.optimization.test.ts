// REQ-5013/5014/5019/5020: Tests fuer decisionTableStore Optimierung
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDecisionTableStore } from "../decisionTableStore";

describe("decisionTableStore Optimization - REQ-5013/5014/5019/5020", () => {
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
      checksum: null,
      contradictions: [],
      gaps: [],
      collapsedCount: 0,
      effectPriorities: {},
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("runCollapse - REQ-5013/5019", () => {
    it("setzt loading waehrend des Collapsing", async () => {
      let resolvePromise: (value: unknown) => void;
      global.fetch = vi.fn(() =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      let collapsePromise: Promise<void>;
      act(() => {
        collapsePromise = result.current.runCollapse(1);
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise!({
          ok: true,
          json: () =>
            Promise.resolve({
              rules: [{ id: 1, causes: {}, effects: {} }],
              collapsed_count: 3,
            }),
        });
        await collapsePromise;
      });

      expect(result.current.loading).toBe(false);
    });

    it("aktualisiert rules und collapsedCount bei Erfolg", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              rules: [
                { id: 1, causes: { 1: "Y" }, effects: { 10: "X" } },
                { id: 2, causes: { 1: "N" }, effects: { 10: "X" } },
              ],
              collapsed_count: 5,
            }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runCollapse(1);
      });

      expect(result.current.collapsedCount).toBe(5);
      expect(result.current.rules.length).toBe(2);
      expect(result.current.rules[0].id).toBe(1);
    });

    it("setzt loading auf false bei Fehler", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "Server error" }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runCollapse(1);
      });

      expect(result.current.loading).toBe(false);
    });

    it("nutzt korrekte API-URL", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              rules: [],
              collapsed_count: 0,
            }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runCollapse(42);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/decision-table/collapse",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: 42 }),
        })
      );
    });
  });

  describe("runValidate - REQ-5014/5020", () => {
    it("setzt checksum, contradictions, gaps bei Erfolg", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              checksum: {
                checksum: 8,
                expected: 8,
                status: "complete",
                message: "Vollstaendig",
              },
              contradictions: [
                {
                  rule_a: 1,
                  rule_b: 2,
                  message: "Regel R1 und R2 widersprechen sich",
                },
              ],
              gaps: [
                {
                  combination: { 1: "Y", 2: "N" },
                  message: "Luecke: Y,N nicht abgedeckt",
                },
              ],
            }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.checksum).toEqual({
        checksum: 8,
        expected: 8,
        status: "complete",
        message: "Vollstaendig",
      });
      expect(result.current.contradictions.length).toBe(1);
      expect(result.current.contradictions[0].message).toBe(
        "Regel R1 und R2 widersprechen sich"
      );
      expect(result.current.gaps.length).toBe(1);
      expect(result.current.gaps[0].message).toBe("Luecke: Y,N nicht abgedeckt");
    });

    it("setzt loading auf false nach Validation", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              checksum: null,
              contradictions: [],
              gaps: [],
            }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.loading).toBe(false);
    });

    it("haendelt leere Response korrekt", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.checksum).toBeNull();
      expect(result.current.contradictions).toEqual([]);
      expect(result.current.gaps).toEqual([]);
    });

    it("setzt loading auf false bei Fehler", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "Validation failed" }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.loading).toBe(false);
    });

    it("nutzt korrekte API-URL", async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              checksum: null,
              contradictions: [],
              gaps: [],
            }),
        })
      );

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(99);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/decision-table/validate",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: 99 }),
        })
      );
    });
  });
});