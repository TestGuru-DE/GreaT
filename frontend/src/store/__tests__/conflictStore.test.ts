// REQ-4022: Tests fuer conflictStore
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useConflictStore } from "../conflictStore";

describe("conflictStore - REQ-4022", () => {
  beforeEach(() => {
    // Reset store state vor jedem Test
    useConflictStore.setState({
      conflict: null,
      visible: false,
    });
  });

  it("Initial state hat visible=false und conflict=null", () => {
    const { result } = renderHook(() => useConflictStore());
    expect(result.current.visible).toBe(false);
    expect(result.current.conflict).toBe(null);
  });

  it("setConflict setzt conflict und visible=true", () => {
    const { result } = renderHook(() => useConflictStore());

    const mockConflict = {
      type: "version_conflict" as const,
      message: "Version mismatch",
      clientVersion: 1,
      serverVersion: 2,
      entity: { id: 1, name: "test" },
    };

    act(() => {
      result.current.setConflict(mockConflict);
    });

    expect(result.current.visible).toBe(true);
    expect(result.current.conflict).toEqual(mockConflict);
  });

  it("clearConflict setzt visible=false und conflict=null", () => {
    const { result } = renderHook(() => useConflictStore());

    // Setze zuerst einen Konflikt
    act(() => {
      result.current.setConflict({
        type: "version_conflict",
        message: "test",
        clientVersion: 1,
        serverVersion: 2,
      });
    });
    expect(result.current.visible).toBe(true);

    // Clear
    act(() => {
      result.current.clearConflict();
    });

    expect(result.current.visible).toBe(false);
    expect(result.current.conflict).toBe(null);
  });

  it("onReload setzt visible=false", () => {
    const { result } = renderHook(() => useConflictStore());

    act(() => {
      result.current.setConflict({
        type: "version_conflict",
        message: "test",
        clientVersion: 1,
        serverVersion: 2,
      });
    });

    act(() => {
      result.current.onReload();
    });

    expect(result.current.visible).toBe(false);
  });

  it("onOverwrite setzt visible=false", () => {
    const { result } = renderHook(() => useConflictStore());

    act(() => {
      result.current.setConflict({
        type: "version_conflict",
        message: "test",
        clientVersion: 1,
        serverVersion: 2,
      });
    });

    act(() => {
      result.current.onOverwrite();
    });

    expect(result.current.visible).toBe(false);
  });

  it("onClose setzt visible=false", () => {
    const { result } = renderHook(() => useConflictStore());

    act(() => {
      result.current.setConflict({
        type: "version_conflict",
        message: "test",
        clientVersion: 1,
        serverVersion: 2,
      });
    });

    act(() => {
      result.current.onClose();
    });

    expect(result.current.visible).toBe(false);
  });
});