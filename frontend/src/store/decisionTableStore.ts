// REQ-5000 + REQ-5003 + REQ-5004 + REQ-5005: Zustand Store fuer Entscheidungstabelle
// REQ-5021: Priorisierung von Wirkungen (Override)
import { create } from "zustand";
import type {
  DecisionTableRow,
  DecisionTableCause,
  DecisionTableEffect,
  DecisionTableGenerateResponse,
} from "../types";

interface DecisionTableChecksum {
  checksum: number;
  expected: number;
  status: string;
  message: string;
}

interface DecisionTableContradiction {
  rule_a: number;
  rule_b: number;
  message: string;
}

interface DecisionTableGap {
  combination: Record<string, string>;
  message: string;
}

// REQ-5021: Priorisierung von Wirkungen
interface DecisionTableState {
  mode: boolean;
  causes: DecisionTableCause[];
  effects: DecisionTableEffect[];
  rules: DecisionTableRow[];
  loading: boolean;
  error: string | null;
  canGenerate: boolean;

  // REQ-5013/5014/5019/5020: Optimierungsfelder
  checksum: DecisionTableChecksum | null;
  contradictions: DecisionTableContradiction[];
  gaps: DecisionTableGap[];
  collapsedCount: number;

  // REQ-5021: Priorisierung von Wirkungen
  effectPriorities: Record<number, number>; // effect_id -> priority (1=highest, N=lowest, 999=none)

  // EPIC-20 Schulden: Text/Binar-Modus und Override
  effectMode: "binary" | "text";
  enableOverride: boolean;

  setMode: (mode: boolean) => void;
  generate: (projectId: number) => Promise<void>;
  updateEffect: (ruleId: number, effectId: number, value: string | null) => void;
  updateCause: (ruleId: number, causeId: number, value: string) => void;
  reset: () => void;

  // REQ-5013/5014/5019/5020: Optimierung-Actions
  runCollapse: (projectId: number) => Promise<void>;
  runValidate: (projectId: number) => Promise<void>;
  /** REQ-5002/REQ-5003: Ursachen und Wirkungen des Projekts laden */
  loadCategories: (projectId: number) => Promise<void>;

  // REQ-5021: Prioritaet-Actions
  setEffectPriority: (effectId: number, priority: number) => void;

  // EPIC-20 Schulden: Modus- und Override-Actions
  setEffectMode: (mode: "binary" | "text") => void;
  setEnableOverride: (val: boolean) => void;
}

export const useDecisionTableStore = create<DecisionTableState>((set, get) => ({
  mode: false,
  causes: [],
  effects: [],
  rules: [],
  loading: false,
  error: null,
  canGenerate: false,

  // REQ-5013/5014/5019/5020: Optimierungsfelder
  checksum: null,
  contradictions: [],
  gaps: [],
  collapsedCount: 0,

  // REQ-5021: Priorisierung von Wirkungen
  effectPriorities: {},

  // EPIC-20 Schulden
  effectMode: "binary",
  enableOverride: false,

  setMode: (mode) => {
    set({ mode });
    if (!mode) {
      // Beim Verlassen des Modus: Daten zuruecksetzen
      set({ causes: [], effects: [], rules: [], canGenerate: false, effectPriorities: {}, effectMode: "binary", enableOverride: false });
    }
  },

  generate: async (projectId) => {
    set({ loading: true, error: null });
    const state = get();
    try {
      const response = await fetch("/api/decision-table/generate", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          effect_mode: state.effectMode,
          enable_override: state.enableOverride,
          priorities: Object.keys(state.effectPriorities).length > 0
            ? state.effectPriorities
            : undefined,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Generierung fehlgeschlagen" }));
        // REQ-5000: Freundliche Fehlermeldung fuer den User
        let message = "Generierung fehlgeschlagen";

        if (response.status === 422) {
          // FastAPI Validation Error – detail kann ein Array oder Objekt sein
          if (Array.isArray(err.detail)) {
            // Extrahiere die ersten Fehlermeldung
            const firstErr = err.detail[0];
            if (firstErr && firstErr.msg) {
              message = firstErr.msg;
            } else {
              message = "Ungueltige Anfrage. Bitte pruefe, dass mindestens eine Ursache- und eine Wirkungskategorie existiert.";
            }
          } else if (typeof err.detail === "string") {
            message = err.detail;
          } else {
            message = "Ungueltige Anfrage. Ursachen und Wirkungen muessen korrekt konfiguriert sein.";
          }
        } else if (typeof err.detail === "string") {
          message = err.detail;
        } else if (err.detail && typeof err.detail === "object") {
          message = "Bitte pruefe deine Eingabe. Ursachen und Wirkungen muessen korrekt konfiguriert sein.";
        }

        throw new Error(message);
      }
      const data: DecisionTableGenerateResponse = await response.json();
      set({
        causes: data.causes,
        effects: data.effects,
        rules: data.rules,
        canGenerate: true,
      });
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e) });
    } finally {
      set({ loading: false });
    }
  },

  updateEffect: (ruleId, effectId, value) => {
    set((state) => ({
      ...state,
      rules: state.rules.map((r) =>
        r.id === ruleId
          ? { ...r, effects: { ...r.effects, [effectId]: value } }
          : r
      ),
    }));
  },

  updateCause: (ruleId, causeId, value) => {
    set((state) => ({
      ...state,
      rules: state.rules.map((r) =>
        r.id === ruleId
          ? { ...r, causes: { ...r.causes, [causeId]: value } }
          : r
      ),
    }));
  },

  reset: () => {
    set({ causes: [], effects: [], rules: [], canGenerate: false, error: null, effectPriorities: {}, effectMode: "binary", enableOverride: false });
  },

  // REQ-5013/5019: Collapsing – redundant Regeln zusammenfassen
  runCollapse: async (projectId) => {
    set({ loading: true });
    try {
      const response = await fetch("/api/decision-table/collapse", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId }),
      });
      if (response.ok) {
        const data = await response.json();
        set({
          rules: data.rules || [],
          collapsedCount: data.collapsed_count || 0,
        });
      }
    } finally {
      set({ loading: false });
    }
  },

  // REQ-5014/5020: Validation – Checksum, Widersprueche, Luecken
  loadCategories: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/decision-table/categories/${projectId}`, {
        credentials: "include",
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Laden fehlgeschlagen" }));
        set({ loading: false, error: typeof err.detail === "string" ? err.detail : "Kategorien konnten nicht geladen werden" });
        return;
      }
      const data = await response.json();
      set({ causes: data.causes ?? [], effects: data.effects ?? [], loading: false });
    } catch {
      set({ loading: false, error: "Kategorien konnten nicht geladen werden" });
    }
  },

  runValidate: async (projectId) => {
    set({ loading: true });
    try {
      const response = await fetch("/api/decision-table/validate", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId }),
      }
      );
      if (response.ok) {
        const data = await response.json();
        set({
          checksum: data.checksum || null,
          contradictions: data.contradictions || [],
          gaps: data.gaps || [],
        });
      }
    } finally {
      set({ loading: false });
    }
  },

  // REQ-5021: Prioritaet fuer Wirkung setzen
  setEffectPriority: (effectId, priority) => {
    set((state) => {
      const newPriorities = { ...state.effectPriorities };
      if (priority === 999) delete newPriorities[effectId];
      else newPriorities[effectId] = priority;
      return { effectPriorities: newPriorities };
    });
  },

  // EPIC-20 Schulden: Modus- und Override-Actions
  setEffectMode: (mode) => set({ effectMode: mode }),
  setEnableOverride: (val) => set({ enableOverride: val }),
}));