// REQ-6009: Zustand Store fuer Seed-Saetze und Lueckenschluss
import { create } from "zustand";
import { seedApi } from "../api/client";
import type {
  SeedSet,
  SeedSetList,
  SeedSetCreate,
  SeedSetUpdate,
  SeedCSVImportResponse,
  GapFillResponse,
} from "../types";

interface SeedStore {
  // State
  seedSets: SeedSetList[];
  currentSet: SeedSet | null;
  loading: boolean;
  error: string | null;
  msg: { text: string; type: "ok" | "warn" | "error" } | null;

  // CRUD Actions
  fetchSeedSets: (projectId: number) => Promise<void>;
  createSeedSet: (projectId: number, data: SeedSetCreate) => Promise<SeedSetList | null>;
  loadSeedSet: (projectId: number, seedSetId: number) => Promise<void>;
  updateSeedSet: (projectId: number, seedSetId: number, data: SeedSetUpdate) => Promise<void>;
  deleteSeedSet: (projectId: number, seedSetId: number) => Promise<void>;

  // CSV Import
  importCsv: (projectId: number, name: string, file: File) => Promise<SeedCSVImportResponse | null>;

  // Gap Fill
  gapFill: (generationId: number, strategy?: string, tStrength?: number) => Promise<GapFillResponse | null>;

  // Internal helpers
  setSelectedSet: (seedSet: SeedSet | null) => void;
  addSeed: (assignment: Record<string, string | null>) => void;
  removeSeed: (index: number) => void;
  updateSeed: (index: number, assignment: Record<string, string | null>) => void;
  clearMsg: () => void;
}

export const useSeedStore = create<SeedStore>((set, get) => ({
  seedSets: [],
  currentSet: null,
  loading: false,
  error: null,
  msg: null,

  fetchSeedSets: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const sets = await seedApi.list(projectId);
      set({ seedSets: sets, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  createSeedSet: async (projectId, data) => {
    set({ loading: true, error: null, msg: null });
    try {
      const res = await seedApi.create(projectId, data);
      if (res.warnings.length > 0) {
        set({ msg: { text: res.warnings.join("; "), type: "warn" } });
      } else {
        set({ msg: { text: "Seed-Satz erstellt", type: "ok" } });
      }
      // Liste aktualisieren
      await get().fetchSeedSets(projectId);
      set({ loading: false });
      return { id: res.id, name: res.name, seed_count: res.seed_count, created_at: "" };
    } catch (e) {
      set({ error: String(e), loading: false });
      return null;
    }
  },

  loadSeedSet: async (projectId, seedSetId) => {
    set({ loading: true, error: null });
    try {
      const seedSet = await seedApi.get(projectId, seedSetId);
      set({ currentSet: seedSet, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  updateSeedSet: async (projectId, seedSetId, data) => {
    set({ loading: true, error: null, msg: null });
    try {
      const res = await seedApi.update(projectId, seedSetId, data);
      if (res.warnings.length > 0) {
        set({ msg: { text: res.warnings.join("; "), type: "warn" } });
      } else {
        set({ msg: { text: "Seed-Satz aktualisiert", type: "ok" } });
      }
      // Detail und Liste aktualisieren
      await get().loadSeedSet(projectId, seedSetId);
      await get().fetchSeedSets(projectId);
      set({ loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  deleteSeedSet: async (projectId, seedSetId) => {
    set({ loading: true, error: null });
    try {
      await seedApi.delete(projectId, seedSetId);
      set({
        seedSets: get().seedSets.filter((s) => s.id !== seedSetId),
        currentSet: get().currentSet?.id === seedSetId ? null : get().currentSet,
        loading: false,
        msg: { text: "Seed-Satz geloescht", type: "ok" },
      });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  importCsv: async (projectId, name, file) => {
    set({ loading: true, error: null, msg: null });
    try {
      const res = await seedApi.importCsv(projectId, name, file);
      if (res.warnings.length > 0) {
        set({ msg: { text: res.warnings.join("; "), type: "warn" } });
      } else {
        set({ msg: { text: `${res.seed_count} Seeds importiert`, type: "ok" } });
      }
      await get().fetchSeedSets(projectId);
      set({ loading: false });
      return res;
    } catch (e) {
      set({ error: String(e), loading: false });
      return null;
    }
  },

  gapFill: async (generationId, strategy = "pairwise", tStrength = 2) => {
    set({ loading: true, error: null, msg: null });
    try {
      const res = await seedApi.gapFill(generationId, strategy, tStrength);
      if (res.warnings.length > 0) {
        set({ msg: { text: res.warnings.join("; "), type: "warn" } });
      } else {
        set({ msg: { text: `Lueckenschluss: ${res.supplemented_count} ergaenzt`, type: "ok" } });
      }
      set({ loading: false });
      return res;
    } catch (e) {
      set({ error: String(e), loading: false });
      return null;
    }
  },

  setSelectedSet: (seedSet) => set({ currentSet: seedSet }),

  // In-memory seed editing (before save)
  addSeed: (assignment) => {
    set((state) => {
      if (!state.currentSet) return state;
      const newCases = [...state.currentSet.seed_cases, {
        id: -Date.now(), // temporary negative ID
        assignment,
        order_index: state.currentSet.seed_cases.length,
      }];
      return {
        currentSet: {
          ...state.currentSet,
          seed_cases: newCases,
          seed_count: newCases.length,
        },
      };
    });
  },

  removeSeed: (index) => {
    set((state) => {
      if (!state.currentSet) return state;
      const newCases = state.currentSet.seed_cases.filter((_, i) => i !== index);
      return {
        currentSet: {
          ...state.currentSet,
          seed_cases: newCases,
          seed_count: newCases.length,
        },
      };
    });
  },

  updateSeed: (index, assignment) => {
    set((state) => {
      if (!state.currentSet) return state;
      const newCases = state.currentSet.seed_cases.map((sc, i) =>
        i === index ? { ...sc, assignment } : sc
      );
      return {
        currentSet: {
          ...state.currentSet,
          seed_cases: newCases,
        },
      };
    });
  },

  clearMsg: () => set({ msg: null }),
}));