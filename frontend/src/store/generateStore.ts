// REQ-1208 + REQ-2001: Zustand Store fuer Testfall-Generierung mit History
import { create } from "zustand";
import { generateApi } from "../api/client";
import type { GenerationSummary } from "../api/client";
import type { TestCaseOut, Strategy } from "../types";

interface GenerateStore {
  testcases: TestCaseOut[];
  generationId: number | null;
  count: number;
  loading: boolean;
  error: string | null;
  strategy: Strategy;
  generations: GenerationSummary[];
  generationsLoading: boolean;
  setStrategy: (s: Strategy) => void;
  generate: (projectId: number, applyRules?: boolean, tStrength?: number) => Promise<void>;
  fetchGenerations: (projectId: number) => Promise<void>;
  loadGeneration: (generationId: number) => Promise<void>;
  renameGeneration: (generationId: number, name: string) => Promise<void>;
}

export const useGenerateStore = create<GenerateStore>((set, get) => ({
  testcases: [],
  generationId: null,
  count: 0,
  loading: false,
  error: null,
  strategy: "each",
  generations: [],
  generationsLoading: false,

  setStrategy: (strategy) => set({ strategy }),

  generate: async (projectId, applyRules = false, tStrength = 2) => {
    set({ loading: true, error: null, testcases: [] });
    try {
      const res = await generateApi.run(projectId, { 
        strategy: get().strategy, 
        apply_rules: applyRules,
        t_strength: tStrength, // BUG-3: T-Wise Stärke
      });
      const testcases = await generateApi.getTestcases(res.generation_id);
      set({
        testcases,
        generationId: res.generation_id,
        count: res.count,
        loading: false,
      });
      // History nach neuer Generierung aktualisieren
      get().fetchGenerations(projectId);
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  fetchGenerations: async (projectId) => {
    set({ generationsLoading: true });
    try {
      const generations = await generateApi.listGenerations(projectId);
      set({ generations, generationsLoading: false });
    } catch {
      set({ generationsLoading: false });
    }
  },

  loadGeneration: async (generationId) => {
    set({ loading: true, error: null, testcases: [] });
    try {
      const testcases = await generateApi.getTestcases(generationId);
      set({
        testcases,
        generationId,
        count: testcases.length,
        loading: false,
      });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  renameGeneration: async (generationId, name) => {
    const updated = await generateApi.renameGeneration(generationId, name);
    set((state) => ({
      generations: state.generations.map((g) => g.id === generationId ? updated : g),
    }));
  },
}));