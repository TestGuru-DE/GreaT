// REQ-1207 + REQ-3053: Zustand Store fuer Kategorien und Werte mit Undo/Redo
// REQ-5002: Kategorie-Typ (Standard/Ursache/Wirkung)
// BUG C-18 (REQ-6006/REQ-3053): Undo/Redo wirken auf dem Server. Jede Aenderung legt einen
// Befehl mit Gegenoperation an; Undo/Redo rufen die API auf und laden den Stand neu.
// Wiederhergestellte Kategorien/Werte bekommen neue IDs; Befehle verweisen deshalb ueber
// "Refs" auf Elemente, deren ID beim Wiederherstellen nachgefuehrt wird.
import { create } from "zustand";
import { categoriesApi, valuesApi, renameApi, reorderApi } from "../api/client";
import type { Category, Value, CategoryType } from "../types";

/** Stabiler Verweis auf ein Element, dessen Server-ID sich durch Undo/Redo aendern kann. */
interface Ref { id: number }

interface Command {
  label: string;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
}

interface CategoryStore {
  categories: Category[];
  values: Record<number, Value[]>;
  loading: boolean;
  error: string | null;
  // REQ-3053: Undo/Redo (serverseitig)
  past: Command[];
  future: Command[];
  canUndo: boolean;
  canRedo: boolean;
  busy: boolean;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
  resetHistory: () => void;
  // Laden
  fetchCategories: (projectId: number) => Promise<void>;
  fetchValues: (categoryId: number) => Promise<void>;
  fetchAllValues: () => Promise<void>;  // BUG C-15
  // Aenderungen (jeweils mit Undo)
  createCategory: (projectId: number, name: string, categoryType?: CategoryType, isResult?: boolean) => Promise<Category>;
  deleteCategory: (categoryId: number, force?: boolean) => Promise<void>;
  renameCategory: (categoryId: number, name: string) => Promise<void>;
  reorderCategories: (projectId: number, order: number[]) => Promise<void>;
  createValue: (categoryId: number, value: string, riskWeight?: number) => Promise<Value>;
  deleteValue: (categoryId: number, valueId: number, force?: boolean) => Promise<void>;
  renameValue: (categoryId: number, valueId: number, name: string) => Promise<void>;
  reorderValues: (categoryId: number, order: number[]) => Promise<void>;
}

const MAX_HISTORY = 50;

// Refs je Server-ID; beim Wiederherstellen wird die ID im Ref ersetzt
const catRefs = new Map<number, Ref>();
const valRefs = new Map<number, Ref>();
let currentProjectId: number | null = null;

function refFor(map: Map<number, Ref>, id: number): Ref {
  let ref = map.get(id);
  if (!ref) {
    ref = { id };
    map.set(id, ref);
  }
  return ref;
}

function moveRef(map: Map<number, Ref>, ref: Ref, newId: number) {
  map.delete(ref.id);
  ref.id = newId;
  map.set(newId, ref);
}

export const useCategoryStore = create<CategoryStore>((set, get) => {
  /** Kategorien und alle bereits geladenen Werte neu vom Server holen (ohne History-Reset). */
  const reload = async () => {
    if (currentProjectId === null) return;
    const categories = await categoriesApi.list(currentProjectId);
    const loaded = Object.keys(get().values).map(Number);
    const ids = new Set(categories.map((c) => c.id));
    const entries = await Promise.all(
      categories
        .filter((c) => loaded.includes(c.id))
        .map(async (c) => [c.id, await valuesApi.list(c.id)] as const),
    );
    set((s) => ({
      categories,
      values: Object.fromEntries([
        ...Object.entries(s.values).filter(([k]) => ids.has(Number(k)) && !loaded.includes(Number(k))),
        ...entries,
      ]),
    }));
  };

  const push = (cmd: Command) =>
    set((s) => ({
      past: [...s.past.slice(-(MAX_HISTORY - 1)), cmd],
      future: [],
      canUndo: true,
      canRedo: false,
    }));

  /** Werte einer Kategorie inkl. Eigenschaften wiederherstellen; aktualisiert die Refs. */
  const restoreValues = async (categoryId: number, saved: { ref: Ref; value: Value }[]) => {
    for (const { ref, value } of saved) {
      const created = await valuesApi.create(categoryId, { value: value.value, risk_weight: value.risk_weight });
      moveRef(valRefs, ref, created.id);
      if (value.allowed === false || (value.vtype && value.vtype !== created.vtype)) {
        await categoriesApi.updateProperties(created.id, { allowed: value.allowed, vtype: value.vtype });
      }
      if (value.is_default && !created.is_default) await categoriesApi.setDefault(created.id);
      if (!value.is_default && created.is_default) await categoriesApi.unsetDefault(created.id);
    }
  };

  const runHistory = async (direction: "undo" | "redo") => {
    const s = get();
    const stack = direction === "undo" ? s.past : s.future;
    if (stack.length === 0 || s.busy) return;
    const cmd = direction === "undo" ? stack[stack.length - 1] : stack[0];
    set({ busy: true, error: null });
    try {
      await (direction === "undo" ? cmd.undo() : cmd.redo());
      set((st) => {
        const past = direction === "undo" ? st.past.slice(0, -1) : [...st.past, cmd];
        const future = direction === "undo" ? [cmd, ...st.future] : st.future.slice(1);
        return { past, future, canUndo: past.length > 0, canRedo: future.length > 0 };
      });
    } catch (e) {
      // Server-Stand passt nicht mehr zur Historie: Historie verwerfen statt Inkonsistenzen
      set({ error: e instanceof Error ? e.message : String(e), past: [], future: [], canUndo: false, canRedo: false });
    } finally {
      try { await reload(); } finally { set({ busy: false }); }
    }
  };

  return {
    categories: [],
    values: {},
    loading: false,
    error: null,
    past: [],
    future: [],
    canUndo: false,
    canRedo: false,
    busy: false,

    undo: () => runHistory("undo"),
    redo: () => runHistory("redo"),

    resetHistory: () => set({ past: [], future: [], canUndo: false, canRedo: false }),

    fetchCategories: async (projectId) => {
      if (currentProjectId !== projectId) {
        set({ values: {} });
        catRefs.clear();
        valRefs.clear();
      }
      currentProjectId = projectId;
      set({ loading: true, error: null });
      try {
        const categories = await categoriesApi.list(projectId);
        set({ categories, loading: false });
        get().resetHistory();
      } catch (e) {
        set({ error: String(e), loading: false });
      }
    },

    fetchValues: async (categoryId) => {
      const vals = await valuesApi.list(categoryId);
      set((s) => ({ values: { ...s.values, [categoryId]: vals } }));
    },

    // BUG C-15: alle Klassen laden (der Baum zeigt alle Kategorien gleichzeitig)
    fetchAllValues: async () => {
      const missing = get().categories.filter((c) => !(c.id in get().values));
      const entries = await Promise.all(missing.map(async (c) => [c.id, await valuesApi.list(c.id)] as const));
      set((s) => ({ values: { ...s.values, ...Object.fromEntries(entries) } }));
    },

    createCategory: async (projectId, name, categoryType = "standard", isResult = false) => {
      const cat = await categoriesApi.create(projectId, { name, category_type: categoryType, is_result: isResult });
      set((s) => ({ categories: [...s.categories, cat], values: { ...s.values, [cat.id]: [] } }));
      const ref = refFor(catRefs, cat.id);
      push({
        label: "createCategory",
        undo: async () => { await categoriesApi.delete(ref.id, true); },
        redo: async () => {
          const again = await categoriesApi.create(projectId, { name, category_type: categoryType, is_result: isResult });
          moveRef(catRefs, ref, again.id);
        },
      });
      return cat;
    },

    deleteCategory: async (categoryId, force = false) => {
      const cat = get().categories.find((c) => c.id === categoryId);
      const vals = get().values[categoryId] ?? (await valuesApi.list(categoryId));
      const order = get().categories.map((c) => refFor(catRefs, c.id));
      await (force ? categoriesApi.delete(categoryId, true) : categoriesApi.delete(categoryId));
      set((s) => ({
        categories: s.categories.filter((c) => c.id !== categoryId),
        values: Object.fromEntries(Object.entries(s.values).filter(([k]) => Number(k) !== categoryId)),
      }));
      if (!cat || currentProjectId === null) return;
      const projectId = currentProjectId;
      const ref = refFor(catRefs, categoryId);
      const saved = vals.map((v) => ({ ref: refFor(valRefs, v.id), value: v }));
      push({
        label: "deleteCategory",
        undo: async () => {
          const again = await categoriesApi.create(projectId, {
            name: cat.name,
            category_type: cat.category_type as CategoryType | undefined,
            is_result: cat.is_result,
          });
          moveRef(catRefs, ref, again.id);
          await restoreValues(again.id, saved);
          await reorderApi.categories(projectId, order.map((r) => r.id));
        },
        redo: async () => { await categoriesApi.delete(ref.id, true); },
      });
    },

    renameCategory: async (categoryId, name) => {
      const old = get().categories.find((c) => c.id === categoryId)?.name;
      const updated = await renameApi.category(categoryId, name);
      set((s) => ({ categories: s.categories.map((c) => (c.id === categoryId ? { ...c, ...updated } : c)) }));
      if (old === undefined || old === name) return;
      const ref = refFor(catRefs, categoryId);
      push({
        label: "renameCategory",
        undo: async () => { await renameApi.category(ref.id, old); },
        redo: async () => { await renameApi.category(ref.id, name); },
      });
    },

    reorderCategories: async (projectId, order) => {
      const before = get().categories.map((c) => refFor(catRefs, c.id));
      const after = order.map((id) => refFor(catRefs, id));
      await reorderApi.categories(projectId, order);
      const byId = new Map(get().categories.map((c) => [c.id, c]));
      set({ categories: order.map((id) => byId.get(id)).filter((c): c is Category => !!c) });
      push({
        label: "reorderCategories",
        undo: async () => { await reorderApi.categories(projectId, before.map((r) => r.id)); },
        redo: async () => { await reorderApi.categories(projectId, after.map((r) => r.id)); },
      });
    },

    createValue: async (categoryId, value, riskWeight = 1) => {
      const val = await valuesApi.create(categoryId, { value, risk_weight: riskWeight });
      set((s) => ({ values: { ...s.values, [categoryId]: [...(s.values[categoryId] ?? []), val] } }));
      const catRef = refFor(catRefs, categoryId);
      const ref = refFor(valRefs, val.id);
      push({
        label: "createValue",
        undo: async () => { await valuesApi.delete(ref.id, true); },
        redo: async () => {
          const again = await valuesApi.create(catRef.id, { value, risk_weight: riskWeight });
          moveRef(valRefs, ref, again.id);
        },
      });
      return val;
    },

    deleteValue: async (categoryId, valueId, force = false) => {
      const list = get().values[categoryId] ?? [];
      const val = list.find((v) => v.id === valueId);
      const order = list.map((v) => refFor(valRefs, v.id));
      await (force ? valuesApi.delete(valueId, true) : valuesApi.delete(valueId));
      set((s) => ({
        values: { ...s.values, [categoryId]: (s.values[categoryId] ?? []).filter((v) => v.id !== valueId) },
      }));
      if (!val) return;
      const catRef = refFor(catRefs, categoryId);
      const ref = refFor(valRefs, valueId);
      push({
        label: "deleteValue",
        undo: async () => {
          await restoreValues(catRef.id, [{ ref, value: val }]);
          await valuesApi.reorder(catRef.id, order.map((r) => r.id));
        },
        redo: async () => { await valuesApi.delete(ref.id, true); },
      });
    },

    renameValue: async (categoryId, valueId, name) => {
      const old = (get().values[categoryId] ?? []).find((v) => v.id === valueId)?.value;
      const updated = await renameApi.value(valueId, name);
      set((s) => ({
        values: {
          ...s.values,
          [categoryId]: (s.values[categoryId] ?? []).map((v) => (v.id === valueId ? { ...v, ...updated } : v)),
        },
      }));
      if (old === undefined || old === name) return;
      const ref = refFor(valRefs, valueId);
      push({
        label: "renameValue",
        undo: async () => { await renameApi.value(ref.id, old); },
        redo: async () => { await renameApi.value(ref.id, name); },
      });
    },

    reorderValues: async (categoryId, order) => {
      const before = (get().values[categoryId] ?? []).map((v) => refFor(valRefs, v.id));
      const after = order.map((id) => refFor(valRefs, id));
      const catRef = refFor(catRefs, categoryId);
      await valuesApi.reorder(categoryId, order);
      const byId = new Map((get().values[categoryId] ?? []).map((v) => [v.id, v]));
      set((s) => ({
        values: { ...s.values, [categoryId]: order.map((id) => byId.get(id)).filter((v): v is Value => !!v) },
      }));
      push({
        label: "reorderValues",
        undo: async () => { await valuesApi.reorder(catRef.id, before.map((r) => r.id)); },
        redo: async () => { await valuesApi.reorder(catRef.id, after.map((r) => r.id)); },
      });
    },
  };
});
