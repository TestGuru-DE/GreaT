// REQ-5021: Tests fuer setEffectPriority im decisionTableStore
import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDecisionTableStore } from "../decisionTableStore";

describe("decisionTableStore Priority - REQ-5021", () => {
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
      effectMode: "binary",
      enableOverride: false,
    });
  });

  describe("setEffectPriority", () => {
    it("setzt Prioritaet 1 fuer eine Wirkung", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(10, 1);
      });

      expect(result.current.effectPriorities[10]).toBe(1);
    });

    it("setzt Prioritaet 2 fuer eine zweite Wirkung", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(11, 2);
      });

      expect(result.current.effectPriorities[11]).toBe(2);
    });

    it("ueberschreibt bestehende Prioritaet", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(10, 1);
      });

      expect(result.current.effectPriorities[10]).toBe(1);

      act(() => {
        result.current.setEffectPriority(10, 3);
      });

      expect(result.current.effectPriorities[10]).toBe(3);
    });

    it("loescht Prioritaet bei 999 (keine)", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(10, 1);
      });

      expect(result.current.effectPriorities[10]).toBe(1);

      act(() => {
        result.current.setEffectPriority(10, 999);
      });

      expect(result.current.effectPriorities[10]).toBeUndefined();
    });

    it("bewahrt andere Prioritaeten beim Aendern einer Wirkung", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(10, 1);
        result.current.setEffectPriority(11, 2);
      });

      expect(result.current.effectPriorities[10]).toBe(1);
      expect(result.current.effectPriorities[11]).toBe(2);

      act(() => {
        result.current.setEffectPriority(10, 3);
      });

      expect(result.current.effectPriorities[10]).toBe(3);
      expect(result.current.effectPriorities[11]).toBe(2);
    });

    it("hat leeres effectPriorities nach reset", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setEffectPriority(10, 1);
      });

      expect(result.current.effectPriorities[10]).toBe(1);

      act(() => {
        result.current.reset();
      });

      expect(result.current.effectPriorities).toEqual({});
    });

    it("hat leeres effectPriorities nach setMode(false)", () => {
      const { result } = renderHook(() => useDecisionTableStore());

      act(() => {
        result.current.setMode(true);
        result.current.setEffectPriority(10, 1);
      });

      expect(result.current.effectPriorities[10]).toBe(1);

      act(() => {
        result.current.setMode(false);
      });

      expect(result.current.effectPriorities).toEqual({});
    });
  });
});