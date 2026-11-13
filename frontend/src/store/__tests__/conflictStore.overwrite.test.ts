// REQ-4022: Ueberschreiben wiederholt die gemerkte Aenderung (ohne Version)
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useConflictStore } from "../conflictStore";

const conflict = { type: "version_conflict" as const, message: "m", clientVersion: 1, serverVersion: 2 };

describe("conflictStore - Ueberschreiben (REQ-4022)", () => {
  beforeEach(() => {
    useConflictStore.setState({ conflict: null, visible: false, retry: null });
  });

  it("onOverwrite fuehrt die gemerkte Aenderung erneut aus und leert den Konflikt", async () => {
    const retry = vi.fn().mockResolvedValue(undefined);
    useConflictStore.getState().setConflict(conflict, retry);
    useConflictStore.getState().onOverwrite();
    expect(retry).toHaveBeenCalledTimes(1);
    expect(useConflictStore.getState().visible).toBe(false);
    expect(useConflictStore.getState().retry).toBe(null);
  });

  it("onReload verwirft die gemerkte Aenderung ohne sie auszufuehren", () => {
    const retry = vi.fn();
    useConflictStore.getState().setConflict(conflict, retry);
    useConflictStore.getState().onReload();
    expect(retry).not.toHaveBeenCalled();
    expect(useConflictStore.getState().conflict).toBe(null);
  });
});
