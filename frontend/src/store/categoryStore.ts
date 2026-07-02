// REQ-1207 + REQ-3053: Zustand Store fuer Kategorien und Werte mit Undo/Redo
import { create } from "zustand";
import { categoriesApi, valuesApi } from "../api/client";
import type { Category, Value } from "../types";

interface CategorySnapshot {
  categories: Category[];
  values: Record<number, Value[]>;
}

interface CategoryStore {
  categories: Category[];
  values: Record<number, Value[]>;
  loading: boolean;
  error: string | null;
  // REQ-3053: Undo/Redo
  past: CategorySnapshot[];
  future: CategorySnapshot[];
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  snapshot: () => void;
  resetHistory: () => void;
  // Original actions
  fetchCategories: (projectId: number) => Promise<void>;
  createCategory: (projectId: number, name: string) => Promise<void>;
  deleteCategory: (categoryId: number) => Promise<void>;
  fetchValues: (categoryId: number) => Promise<void>;
  createValue: (categoryId: number, value: string, riskWeight?: number) => Promise<void>;
  deleteValue: (categoryId: number, valueId: number) => Promise<void>;
}

export const useCategoryStore = create<CategoryStore>((set, get) => ({
  categories: [],
  values: {},
  loading: false,
  error: null,
  // REQ-3053: Undo/Redo State
  past: [],
  future: [],
  canUndo: false,
  canRedo: false,

  // REQ-3053: Snapshot für Undo
  snapshot: () => {
    const s = get();
    const snapshot = { categories: s.categories, values: s.values };
    set({
      past: [...s.past.slice(-49), snapshot], // max 50 Schritte
      future: [],
      canUndo: true,
      canRedo: false,
    });
  },

  // REQ-3053: Undo
  undo: () => {
    const s = get();
    if (s.past.length === 0) return;
    const previous = s.past[s.past.length - 1];
    const currentSnapshot = { categories: s.categories, values: s.values };
    set({
      categories: previous.categories,
      values: previous.values,
      past: s.past.slice(0, -1),
      future: [currentSnapshot, ...s.future],
      canUndo: s.past.length > 1,
      canRedo: true,
    });
  },

  // REQ-3053: Redo
  redo: () => {
    const s = get();
    if (s.future.length === 0) return;
    const next = s.future[0];
    const currentSnapshot = { categories: s.categories, values: s.values };
    set({
      categories: next.categories,
      values: next.values,
      past: [...s.past, currentSnapshot],
      future: s.future.slice(1),
      canUndo: true,
      canRedo: s.future.length > 1,
    });
  },

  // REQ-3053: History zurücksetzen (z.B. nach Fetch)
  resetHistory: () => {
    set({ past: [], future: [], canUndo: false, canRedo: false });
  },

  fetchCategories: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const categories = await categoriesApi.list(projectId);
      set({ categories, loading: false });
      get().resetHistory(); // Nach Fetch History löschen
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  createCategory: async (projectId, name) => {
    get().snapshot(); // Snapshot vor Änderung
    const cat = await categoriesApi.create(projectId, { name });
    set((s) => ({ categories: [...s.categories, cat] }));
  },

  deleteCategory: async (categoryId) => {
    get().snapshot(); // Snapshot vor Änderung
    await categoriesApi.delete(categoryId);
    set((s) => ({
      categories: s.categories.filter((c) => c.id !== categoryId),
      values: Object.fromEntries(
        Object.entries(s.values).filter(([k]) => Number(k) !== categoryId)
      ),
    }));
  },

  fetchValues: async (categoryId) => {
    const vals = await valuesApi.list(categoryId);
    set((s) => ({ values: { ...s.values, [categoryId]: vals } }));
    // Kein Snapshot für Fetch-Operationen
  },

  createValue: async (categoryId, value, riskWeight = 1) => {
    get().snapshot(); // Snapshot vor Änderung
    const val = await valuesApi.create(categoryId, { value, risk_weight: riskWeight });
    set((s) => ({
      values: {
        ...s.values,
        [categoryId]: [...(s.values[categoryId] ?? []), val],
      },
    }));
  },

  deleteValue: async (categoryId, valueId) => {
    get().snapshot(); // Snapshot vor Änderung
    await valuesApi.delete(valueId);
    set((s) => ({
      values: {
        ...s.values,
        [categoryId]: (s.values[categoryId] ?? []).filter((v) => v.id !== valueId),
      },
    }));
  },
}));