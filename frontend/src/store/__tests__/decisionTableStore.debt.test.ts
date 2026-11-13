// EPIC-20 Schulden: Tests fuer neue decisionTableStore Features
import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDecisionTableStore } from "../decisionTableStore";

describe("decisionTableStore debt features", () => {
  beforeEach(() => {
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

  it("setEffectMode wechselt zwischen binary und text", () => {
    const { result } = renderHook(() => useDecisionTableStore());

    act(() => {
      result.current.setEffectMode("text");
    });
    expect(result.current.effectMode).toBe("text");

    act(() => {
      result.current.setEffectMode("binary");
    });
    expect(result.current.effectMode).toBe("binary");
  });

  it("setEnableOverride toggelt", () => {
    const { result } = renderHook(() => useDecisionTableStore());

    act(() => {
      result.current.setEnableOverride(true);
    });
    expect(result.current.enableOverride).toBe(true);

    act(() => {
      result.current.setEnableOverride(false);
    });
    expect(result.current.enableOverride).toBe(false);
  });

  it("setEffectPriority setzt und loescht", () => {
    const { result } = renderHook(() => useDecisionTableStore());

    act(() => {
      result.current.setEffectPriority(1, 1);
    });
    expect(result.current.effectPriorities[1]).toBe(1);

    act(() => {
      result.current.setEffectPriority(1, 999);
    });
    expect(result.current.effectPriorities[1]).toBeUndefined();
  });
});