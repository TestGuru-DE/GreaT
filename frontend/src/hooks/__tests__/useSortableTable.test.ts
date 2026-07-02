// REQ-3052: Tests für Tabellensortierung
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSortableTable } from "../useSortableTable";

describe("useSortableTable - REQ-3052", () => {
  const testData = [
    { name: "Alpha", value: "10", risk: 5 },
    { name: "Gamma", value: "20", risk: 3 },
    { name: "Beta", value: "5", risk: 8 },
  ];

  it("sortiert numerisch aufsteigend", () => {
    const { result } = renderHook(() => useSortableTable(testData));
    
    act(() => {
      result.current.toggleSort("risk");
    });
    
    expect(result.current.sortCol).toBe("risk");
    expect(result.current.sortDir).toBe("asc");
    expect(result.current.sorted[0].risk).toBe(3);
    expect(result.current.sorted[2].risk).toBe(8);
  });

  it("sortiert alphabetisch aufsteigend", () => {
    const { result } = renderHook(() => useSortableTable(testData));
    
    act(() => {
      result.current.toggleSort("name");
    });
    
    expect(result.current.sorted[0].name).toBe("Alpha");
    expect(result.current.sorted[2].name).toBe("Gamma");
  });

  it("wechselt zwischen asc/desc/unsortiert", () => {
    const { result } = renderHook(() => useSortableTable(testData));
    
    // Erster Klick: aufsteigend
    act(() => {
      result.current.toggleSort("name");
    });
    expect(result.current.sortDir).toBe("asc");
    expect(result.current.sorted[0].name).toBe("Alpha");
    
    // Zweiter Klick: absteigend
    act(() => {
      result.current.toggleSort("name");
    });
    expect(result.current.sortDir).toBe("desc");
    expect(result.current.sorted[0].name).toBe("Gamma");
    
    // Dritter Klick: unsortiert (zurück zu Original)
    act(() => {
      result.current.toggleSort("name");
    });
    expect(result.current.sortCol).toBe(null);
    expect(result.current.sortDir).toBe(null);
    expect(result.current.sorted).toEqual(testData);
  });

  it("wechselt Spalte beim Sortieren", () => {
    const { result } = renderHook(() => useSortableTable(testData));
    
    // Sortiere nach "name"
    act(() => {
      result.current.toggleSort("name");
    });
    expect(result.current.sortCol).toBe("name");
    
    // Wechsle zu "risk" - sollte aufsteigend starten
    act(() => {
      result.current.toggleSort("risk");
    });
    expect(result.current.sortCol).toBe("risk");
    expect(result.current.sortDir).toBe("asc");
  });

  it("gibt unsortierte Daten zurück wenn keine Sortierung aktiv", () => {
    const { result } = renderHook(() => useSortableTable(testData));
    
    expect(result.current.sorted).toEqual(testData);
    expect(result.current.sortCol).toBe(null);
    expect(result.current.sortDir).toBe(null);
  });
});
