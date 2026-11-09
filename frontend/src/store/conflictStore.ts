// REQ-4022: Zustand Store fuer Konflikt-Management
// Teil von EPIC-18 (Multi-User) / Sprint 12
import { create } from "zustand";
import type { ConflictInfo } from "../api/handlers";

interface ConflictState {
  /** Der aktuelle Konflikt (null wenn kein Konflikt) */
  conflict: ConflictInfo | null;
  /** Banner sichtbar? */
  visible: boolean;
  /** Gemerkte Aenderung, die bei "Trotzdem ueberschreiben" ohne Version erneut gesendet wird */
  retry: (() => Promise<void> | void) | null;

  /** Setzt einen Konflikt, merkt die Aenderung und macht Banner sichtbar */
  setConflict: (conflict: ConflictInfo, retry?: () => Promise<void> | void) => void;
  /** Loescht Konflikt und macht Banner unsichtbar */
  clearConflict: () => void;
  /** "Neu laden": loescht Konflikt und gemerkte Aenderung, Parent laedt frische Daten */
  onReload: () => void;
  /** "Trotzdem ueberschreiben": fuehrt die gemerkte Aenderung ohne Version erneut aus */
  onOverwrite: () => void;
  /** Schliesst nur das Banner (Konflikt bleibt im Store) */
  onClose: () => void;
}

export const useConflictStore = create<ConflictState>((set, get) => ({
  conflict: null,
  visible: false,
  retry: null,

  setConflict: (conflict: ConflictInfo, retry) =>
    set({ conflict, visible: true, retry: retry ?? null }),

  clearConflict: () => set({ conflict: null, visible: false, retry: null }),

  onReload: () => {
    set({ conflict: null, visible: false, retry: null });
  },

  onOverwrite: () => {
    const retry = get().retry;
    set({ conflict: null, visible: false, retry: null });
    if (retry) void retry();
  },

  onClose: () => set({ visible: false }),
}));
