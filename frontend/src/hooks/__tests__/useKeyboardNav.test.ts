// REQ-3054: Tests für useKeyboardNav Hook
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useKeyboardNav, type NavigableItem } from "../useKeyboardNav";

describe("useKeyboardNav", () => {
  const mockItems: NavigableItem[] = [
    { id: 1, onSelect: vi.fn(), onDelete: vi.fn(), onRename: vi.fn() },
    { id: 2, onSelect: vi.fn(), onDelete: vi.fn(), onRename: vi.fn() },
    { id: 3, onSelect: vi.fn(), onDelete: vi.fn(), onRename: vi.fn() },
  ];

  it("initializes with focusedIndex -1", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    expect(result.current.focusedIndex).toBe(-1);
  });

  it("handles ArrowDown to focus next item", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(0);
    });
    expect(result.current.focusedIndex).toBe(0);

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    });
    expect(result.current.focusedIndex).toBe(1);
  });

  it("handles ArrowUp to focus previous item", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(2);
    });
    expect(result.current.focusedIndex).toBe(2);

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
    });
    expect(result.current.focusedIndex).toBe(1);
  });

  it("does not go below 0 with ArrowUp", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(0);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
    });
    expect(result.current.focusedIndex).toBe(0);
  });

  it("does not go beyond items.length with ArrowDown", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(2);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    });
    expect(result.current.focusedIndex).toBe(2);
  });

  it("calls onSelect when Enter is pressed", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(1);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
    });

    expect(mockItems[1].onSelect).toHaveBeenCalled();
  });

  it("calls onDelete when Delete is pressed", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(1);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Delete" }));
    });

    expect(mockItems[1].onDelete).toHaveBeenCalled();
  });

  it("calls onRename when F2 is pressed", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(1);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "F2" }));
    });

    expect(mockItems[1].onRename).toHaveBeenCalled();
  });

  it("resets focusedIndex to -1 when Escape is pressed", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems));
    
    act(() => {
      result.current.setFocusedIndex(1);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    });

    expect(result.current.focusedIndex).toBe(-1);
  });

  it("does not handle keys when enabled=false", () => {
    const { result } = renderHook(() => useKeyboardNav(mockItems, false));
    
    act(() => {
      result.current.setFocusedIndex(0);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    });

    // focusedIndex should stay 0 because hook is disabled
    expect(result.current.focusedIndex).toBe(0);
  });
});
