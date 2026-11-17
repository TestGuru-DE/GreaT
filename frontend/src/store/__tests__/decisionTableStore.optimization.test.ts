// REQ-5013/5014/5019/5020: Tests fuer decisionTableStore Optimierung
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDecisionTableStore } from "../decisionTableStore";

vi.mock("../../api/client", () => ({
  decisionTableApi: {
    collapse: vi.fn(),
    validate: vi.fn(),
  },
}));

import { decisionTableApi } from "../../api/client";

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
      (decisionTableApi.collapse as any).mockImplementation(() =>
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
          rules: [{ id: 1, causes: {}, effects: {} }],
          collapsed_count: 3,
        });
        await collapsePromise;
      });

      expect(result.current.loading).toBe(false);
    });

    it("aktualisiert rules und collapsedCount bei Erfolg", async () => {
      (decisionTableApi.collapse as any).mockResolvedValue({
        rules: [
          { id: 1, causes: { 1: "Y" }, effects: { 10: "X" } },
          { id: 2, causes: { 1: "N" }, effects: { 10: "X" } },
        ],
        collapsed_count: 5,
      });

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runCollapse(1);
      });

      expect(result.current.collapsedCount).toBe(5);
      expect(result.current.rules.length).toBe(2);
      expect(result.current.rules[0].id).toBe(1);
    });

    it("setzt loading auf false bei Fehler", async () => {
      (decisionTableApi.collapse as any).mockRejectedValue(new Error("Server error"));

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        try {
          await result.current.runCollapse(1);
        } catch {
          // expected - error propagates from store
        }
      });

      expect(result.current.loading).toBe(false);
    });

    it("nutzt korrekte API-URL", async () => {
      (decisionTableApi.collapse as any).mockResolvedValue({
        rules: [],
        collapsed_count: 0,
      });

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runCollapse(42);
      });

      expect(decisionTableApi.collapse).toHaveBeenCalledWith(42);
    });
  });

  describe("runValidate - REQ-5014/5020", () => {
    it("setzt checksum, contradictions, gaps bei Erfolg", async () => {
      (decisionTableApi.validate as any).mockResolvedValue({
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
      });

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
      (decisionTableApi.validate as any).mockResolvedValue({
        checksum: null,
        contradictions: [],
        gaps: [],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.loading).toBe(false);
    });

    it("haendelt leere Response korrekt", async () => {
      (decisionTableApi.validate as any).mockResolvedValue({});

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(1);
      });

      expect(result.current.checksum).toBeNull();
      expect(result.current.contradictions).toEqual([]);
      expect(result.current.gaps).toEqual([]);
    });

    it("setzt loading auf false bei Fehler", async () => {
      (decisionTableApi.validate as any).mockRejectedValue(new Error("Validation failed"));

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        try {
          await result.current.runValidate(1);
        } catch {
          // expected - error propagates from store
        }
      });

      expect(result.current.loading).toBe(false);
    });

    it("nutzt korrekte API-URL", async () => {
      (decisionTableApi.validate as any).mockResolvedValue({
        checksum: null,
        contradictions: [],
        gaps: [],
      });

      const { result } = renderHook(() => useDecisionTableStore());

      await act(async () => {
        await result.current.runValidate(99);
      });

      expect(decisionTableApi.validate).toHaveBeenCalledWith(99);
    });
  });
});