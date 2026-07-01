// REQ-1207: Zustand Store fuer Kategorien und Werte
import { create } from "zustand";
import { categoriesApi, valuesApi } from "../api/client";
import type { Category, Value } from "../types";

interface CategoryStore {
  categories: Category[];
  values: Record<number, Value[]>;
  loading: boolean;
  error: string | null;
  fetchCategories: (projectId: number) => Promise<void>;
  createCategory: (projectId: number, name: string) => Promise<void>;
  deleteCategory: (categoryId: number) => Promise<void>;
  fetchValues: (categoryId: number) => Promise<void>;
  createValue: (categoryId: number, value: string, riskWeight?: number) => Promise<void>;
  deleteValue: (categoryId: number, valueId: number) => Promise<void>;
}

export const useCategoryStore = create<CategoryStore>((set) => ({
  categories: [],
  values: {},
  loading: false,
  error: null,

  fetchCategories: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const categories = await categoriesApi.list(projectId);
      set({ categories, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  createCategory: async (projectId, name) => {
    const cat = await categoriesApi.create(projectId, { name });
    set((s) => ({ categories: [...s.categories, cat] }));
  },

  deleteCategory: async (categoryId) => {
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
  },

  createValue: async (categoryId, value, riskWeight = 1) => {
    const val = await valuesApi.create(categoryId, { value, risk_weight: riskWeight });
    set((s) => ({
      values: {
        ...s.values,
        [categoryId]: [...(s.values[categoryId] ?? []), val],
      },
    }));
  },

  deleteValue: async (categoryId, valueId) => {
    await valuesApi.delete(valueId);
    set((s) => ({
      values: {
        ...s.values,
        [categoryId]: (s.values[categoryId] ?? []).filter((v) => v.id !== valueId),
      },
    }));
  },
}));