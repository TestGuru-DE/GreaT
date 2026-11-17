// REQ-1203: Typsicherer API-Client fuer alle FastAPI-Endpunkte
// REQ-1209, REQ-1213: Rename + Reorder Endpunkte
// B-43: Token-Refresh + ApiError-Interceptor
import axios from "axios";
import type {
  Project, ProjectCreate,
  Category, CategoryCreate,
  Value, ValueCreate,
  GenerateRequest, GenerateResponse, TestCaseOut, RiskSummary, ResultCategory,
} from "../types";
import { ApiError } from './ApiError';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

let refreshPromise: Promise<void> | null = null;

function isAuthRoute(url?: string): boolean {
  if (!url) return true;
  const u = url.toLowerCase();
  return u.includes('/auth/login') || u.includes('/auth/refresh') || u.includes('/auth/logout');
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // B-43: 401 -> Token-Refresh + Retry (nur bei nicht-Auth-Routes)
    if (error.response?.status === 401 && !isAuthRoute(originalRequest?.url)) {
      if (refreshPromise) {
        await refreshPromise;
        return api(originalRequest);
      }

      refreshPromise = (async () => {
        try {
          await useAuthStore.getState().refresh();
        } catch {
          useAuthStore.getState().logout();
          window.location.href = '/login?reason=session_expired';
        } finally {
          refreshPromise = null;
        }
      })();

      await refreshPromise;
      return api(originalRequest);
    }

    // B-42: 403 password_change_required -> Redirect (REQ-4028)
    const detail = error.response?.data?.detail;
    if (error.response?.status === 403 && detail === "password_change_required") {
      window.location.href = "/account/password";
      return Promise.reject(new Error("password_change_required_redirect"));
    }

    const apiError = new ApiError(
      error.response?.status ?? 0,
      error.response?.data?.detail ?? error.message
    );
    throw apiError;
  }
);

// --- Projekte ---
export const projectsApi = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  create: (data: ProjectCreate) =>
    api.post<Project>("/projects", data).then((r) => r.data),
  delete: (id: number) =>
    api.delete<{ok: boolean}>("/projects/" + id, {params: {force: true}}).then((r) => r.data),
  // REQ-4021: Umbenennen mit Versionspruefung (version weglassen = ohne Pruefung)
  update: (id: number, data: { name: string; version?: number }) =>
    api.put<Project>("/projects/" + id, data).then((r) => r.data),
  forceDelete: (id: number) =>
    api.delete<{ok: boolean}>("/projects/" + id + "/force").then((r) => r.data),
  
  bulkDeleteForce: (ids: number[]) =>
    api.post<{deleted: number; blocked: number[]}>("/projects/bulk-delete-force", { project_ids: ids }).then((r) => r.data),
};

// --- Kategorien ---
export const categoriesApi = {
  list: (projectId: number) =>
    api.get<Category[]>("/projects/" + projectId + "/categories").then((r) => r.data),
  create: (projectId: number, data: CategoryCreate) =>
    api.post<Category>("/projects/" + projectId + "/categories", data).then((r) => r.data),
  delete: (categoryId: number) =>
    api.delete<{ok: boolean}>("/categories/" + categoryId).then((r) => r.data),
  
  updateProperties: (valueId: number, props: { risk_weight?: number; vtype?: string; allowed?: boolean }) =>
    api.patch<Value>("/values/" + valueId + "/properties", props).then((r) => r.data),
  setDefault: (valueId: number) =>
    api.patch<Value>("/values/" + valueId + "/set-default").then((r) => r.data),
  unsetDefault: (valueId: number) =>
    api.patch<Value>("/values/" + valueId + "/unset-default").then((r) => r.data),
};

// --- Werte ---
export const valuesApi = {
  list: (categoryId: number) =>
    api.get<Value[]>("/categories/" + categoryId + "/values").then((r) => r.data),
  create: (categoryId: number, data: ValueCreate) =>
    api.post<Value>("/categories/" + categoryId + "/values", data).then((r) => r.data),
  delete: (valueId: number) =>
    api.delete<{ok: boolean}>("/values/" + valueId).then((r) => r.data),
};

// --- Generierung ---
export interface GenerationSummary {
  id: number;
  strategy: string;
  name: string;
  created_at: string;
  testcase_count: number;
}

// REQ-3051: Testcases Response mit risk_summary
export interface TestcasesResponse {
  testcases: TestCaseOut[];
  risk_summary: RiskSummary;
  result_categories: ResultCategory[];
}

export const generateApi = {
  run: (projectId: number, req: GenerateRequest) =>
    api.post<GenerateResponse>("/projects/" + projectId + "/generate", req).then((r) => r.data),
  getTestcases: (generationId: number) =>
    api.get<TestcasesResponse>("/generations/" + generationId + "/testcases").then((r) => r.data),
  listGenerations: (projectId: number) =>
    api.get<GenerationSummary[]>("/projects/" + projectId + "/generations").then((r) => r.data),
  renameGeneration: (generationId: number, name: string) =>
    api.patch<GenerationSummary>("/generations/" + generationId + "/rename", { name }).then((r) => r.data),
  deleteGeneration: (generationId: number) =>
    api.delete<{ok: boolean}>("/generations/" + generationId).then((r) => r.data),
  updateAssignment: (testcaseId: number, categoryName: string, value: string) =>
    api.patch<{ testcase_id: number; category_name: string; value: string }>(
      "/testcases/" + testcaseId + "/assignments",
      { category_name: categoryName, value },
    ).then((r) => r.data),
};

// --- Rename + Reorder (REQ-1209, REQ-1213) ---
export const renameApi = {
  category: (categoryId: number, name: string) =>
    api.patch<Category>("/categories/" + categoryId + "/rename", { name }).then((r) => r.data),
  value: (valueId: number, value: string) =>
    api.patch<Value>("/values/" + valueId + "/rename", { value }).then((r) => r.data),
};

// --- Category Properties (REQ-4016) ---

export const categoryPropertiesApi = {
  // REQ-5002: Kategorie-Typ standard | cause | effect
  updateCategoryType: (categoryId: number, category_type: "standard" | "cause" | "effect") =>
    api.patch<Category>("/categories/" + categoryId + "/properties", { category_type }).then((r) => r.data),
};

export const reorderApi = {
  categories: (projectId: number, order: number[]) =>
    api.patch("/projects/" + projectId + "/categories/reorder", { order }).then((r) => r.data),
};

export default api;



// export interface DataClass { ... }
// export interface DataClassValue { ... }
// export const dataclassApi = { ... }

export interface Rule {
  id: number;
  type: string;
  if_category_id: number;
  if_value: string;
  then_category_id: number;
  then_value: string;
  then_values_json: string | null;
}

export const rulesApi = {
  list: (projectId: number) =>
    api.get<Rule[]>("/projects/" + projectId + "/rules").then((r) => r.data),
  create: (projectId: number, data: {
    type: string;
    if_category_id: number;
    if_value: string;
    then_category_id: number;
    then_value?: string;
    then_values?: string[];
  }) => api.post<Rule & { conflict_with: number[] }>("/projects/" + projectId + "/rules", data).then((r) => r.data),
  delete: (projectId: number, ruleId: number) =>
    api.delete("/projects/" + projectId + "/rules/" + ruleId).then((r) => r.data),
};

// REQ-4018: Hierarchische Datenklassen (DataNodes)
export const datanodesApi = {
  getTree: () => api.get<import("../types").DataNode[]>("/datanodes/tree").then((r) => r.data),
  create: (data: Partial<import("../types").DataNode>) =>
    api.post<import("../types").DataNode>("/datanodes", data).then((r) => r.data),
  delete: (nodeId: number) => api.delete("/datanodes/" + nodeId).then((r) => r.data),
  addValue: (nodeId: number, value: string, sort_order?: number) =>
    api.post<import("../types").DataNodeValue>("/datanodes/" + nodeId + "/values", { value, sort_order: sort_order ?? 0 }).then((r) => r.data),
  deleteValue: (nodeId: number, valueId: number) =>
    api.delete("/datanodes/" + nodeId + "/values/" + valueId).then((r) => r.data),
  importBugMagnet: () =>
    api.post<{ status: string; nodes_created: number }>("/datanodes/bugmagnet-import").then((r) => r.data),
  getBugMagnetStatus: () =>
    api.get<{ imported: boolean }>("/datanodes/bugmagnet-status").then((r) => r.data),
  
  importUser: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<{ imported: number }>("/datanodes/import-user", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};

// --- Entscheidungstabelle (aus decisionTableStore.ts ausgelagert) ---
export interface DecisionTableCause {
  id: number;
  name: string;
  values?: string[];
}

export interface DecisionTableEffect {
  id: number;
  name: string;
  values?: string[];
}

export interface DecisionTableRow {
  id: number;
  causes: Record<string, string>;
  effects: Record<string, string | null>;
}

export interface DecisionTableChecksum {
  checksum: number;
  expected: number;
  status: string;
  message: string;
}

export interface DecisionTableContradiction {
  rule_a: number;
  rule_b: number;
  message: string;
}

export interface DecisionTableGap {
  combination: Record<string, string>;
  message: string;
}

export const decisionTableApi = {
  generate: (projectId: number, data: {
    effect_mode?: string;
    enable_override?: boolean;
    priorities?: Record<string, number>;
  }) =>
    api.post<{ causes: DecisionTableCause[]; effects: DecisionTableEffect[]; rules: DecisionTableRow[]; canGenerate: boolean }>(
      "/decision-table/generate",
      { project_id: projectId, ...data }
    ).then((r) => r.data),

  collapse: (projectId: number) =>
    api.post<{ rules: DecisionTableRow[]; collapsed_count: number }>(
      "/decision-table/collapse",
      { project_id: projectId }
    ).then((r) => r.data),

  loadCategories: (projectId: number) =>
    api.get<{ causes: DecisionTableCause[]; effects: DecisionTableEffect[] }>(
      `/decision-table/categories/${projectId}`
    ).then((r) => r.data),

  validate: (projectId: number) =>
    api.post<{
      checksum: DecisionTableChecksum | null;
      contradictions: DecisionTableContradiction[];
      gaps: DecisionTableGap[];
    }>(
      "/decision-table/validate",
      { project_id: projectId }
    ).then((r) => r.data),

  // REQ-5018: Cause-Effect-Graph
  getGraph: (projectId: number) =>
    api.get<{ causes: DecisionTableCause[]; effects: DecisionTableEffect[]; edges: { from: string; to: string; type: string; label: string }[] }>(
      `/decision-table/graph/${projectId}`
    ).then((r) => r.data),
};

// --- Constraints (aus ConstraintDialog.tsx ausgelagert) ---
export interface Constraint {
  id: number;
  type: string;
  targets: number[] | { from: number; to: number };
  description?: string;
}

export const constraintsApi = {
  list: (projectId: number) =>
    api.get<Constraint[]>(`/decision-table/constraints/${projectId}`).then((r) => r.data),

  create: (projectId: number, data: {
    constraint_type: string;
    targets: number[] | { from: number; to: number };
    description?: string;
  }) =>
    api.post<Constraint>("/decision-table/constraints", {
      project_id: projectId,
      ...data,
    }).then((r) => r.data),

  delete: (id: number) =>
    api.delete(`/decision-table/constraints/${id}`).then((r) => r.data),
};

// --- Backup / Reset (aus SettingsPage.tsx ausgelagert) ---
export const backupApi = {
  // Backup erstellen (optional mit Passwort)
  create: (password?: string) => {
    const config = { responseType: "blob" as const };
    if (password) {
      return api.post<Blob>("/backup", { password }, config).then((r) => r.data);
    }
    return api.get<Blob>("/backup", config).then((r) => r.data);
  },

  // Backup wiederherstellen
  restore: (file: File, password?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (password) fd.append("password", password);
    return api.post<{ projects_restored: number }>("/backup/restore", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  // Datenbank zuruecksetzen
  reset: () =>
    api.post<{ default_admin_created: boolean; default_admin_username?: string }>("/backup/reset").then((r) => r.data),
};