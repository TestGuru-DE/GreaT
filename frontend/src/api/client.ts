// REQ-1203: Typsicherer API-Client fuer alle FastAPI-Endpunkte
// REQ-1209, REQ-1213: Rename + Reorder Endpunkte
// B-43: Token-Refresh + ApiError-Interceptor
// REQ-6005: Accept-Language Header basierend auf i18n-Sprache
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

// Auth-Endpunkte liegen unter /auth/* (nicht /api/auth/*)
const authClient = axios.create({
  baseURL: "/auth",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// REQ-6005: Accept-Language Header basierend auf aktueller i18n-Sprache
import i18n from "../i18n";

function getAcceptLanguage(): string {
  return i18n?.language ?? "de";
}

api.interceptors.request.use((config) => {
  config.headers["Accept-Language"] = getAcceptLanguage();
  return config;
});

authClient.interceptors.request.use((config) => {
  config.headers["Accept-Language"] = getAcceptLanguage();
  return config;
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
  // REQ-6011: Export generation in various formats via Blob download
  exportGeneration: (generationId: number, format: string, lang?: string) => {
    const params: Record<string, string> = {};
    if (lang) params.lang = lang;
    return api.get(`/generations/${generationId}/export/${format}`, {
      params,
      responseType: "blob",
    }).then((r) => r.data);
  },
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
// Export authClient for auth endpoints (baseURL: /auth, not /api)
export { authClient };

// --- REQ-6001: Logische Constraints (ADR-020 AST-Format) ---
// NEU: logicalConstraintsApi – bestehendes constraintsApi (REQ-5012) bleibt unveraendert

export type ConstraintKind = "forbid" | "implies";
export type ConstraintOp = "eq" | "ne" | "in" | "not_in" | "and" | "or" | "not";

export interface ConstraintAtom {
  op: "eq" | "ne" | "in" | "not_in";
  category_id: number;
  value_id: number;
  value_ids?: number[]; // for in / not_in
}

export interface ConstraintGroup {
  op: "and" | "or";
  args: (ConstraintAtom | ConstraintGroup | ConstraintNot)[];
}

export interface ConstraintNot {
  op: "not";
  arg: ConstraintNode;
}

export type ConstraintNode = ConstraintAtom | ConstraintGroup | ConstraintNot;

export interface LogicalConstraint {
  id: number;
  project_id: number;
  name: string;
  kind: ConstraintKind;
  expression: ConstraintNode;
  consequence?: ConstraintNode; // only for "implies"
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConstraintCreatePayload {
  name: string;
  kind: ConstraintKind;
  expression: ConstraintNode;
  consequence?: ConstraintNode;
}

export interface ConstraintUpdatePayload {
  name?: string;
  kind?: ConstraintKind;
  expression?: ConstraintNode;
  consequence?: ConstraintNode | null;
}

export interface ConstraintValidateResponse {
  is_valid: boolean;
  errors: string[];
}

export const logicalConstraintsApi = {
  list: (projectId: number) =>
    api.get<LogicalConstraint[]>(`/v1/projects/${projectId}/constraints`).then((r) => r.data),

  get: (projectId: number, cid: number) =>
    api.get<LogicalConstraint>(`/v1/projects/${projectId}/constraints/${cid}`).then((r) => r.data),

  create: (projectId: number, data: ConstraintCreatePayload) =>
    api.post<LogicalConstraint>(`/v1/projects/${projectId}/constraints`, data).then((r) => r.data),

  update: (projectId: number, cid: number, data: ConstraintUpdatePayload) =>
    api.put<LogicalConstraint>(`/v1/projects/${projectId}/constraints/${cid}`, data).then((r) => r.data),

  delete: (projectId: number, cid: number) =>
    api.delete(`/v1/projects/${projectId}/constraints/${cid}`).then((r) => r.data),

  validate: (projectId: number, data: ConstraintCreatePayload) =>
    api.post<ConstraintValidateResponse>(`/v1/projects/${projectId}/constraints/validate`, data).then((r) => r.data),
};

// ============================================================================
// REQ-6008: Coverage API
// ============================================================================

export interface CoverageStat {
  t: number;
  covered: number;
  possible: number;
  percentage: number;
  excluded_by_rules: number;
}

export interface HeatmapPair {
  cat_a: string;
  cat_b: string;
  coverage_pct: number;
  covered: number;
  possible: number;
}

export interface HeatmapOverview {
  categories: string[];
  pairs: HeatmapPair[];
}

export interface UncoveredTuple {
  categories: string[];
  values: string[];
}

export interface CoverageResponse {
  generation_id: number;
  coverage_1wise: CoverageStat;
  coverage_2wise: CoverageStat;
  coverage_3wise?: CoverageStat | null;
  heatmap: HeatmapOverview;
  uncovered_tuples_2wise: UncoveredTuple[];
  cached: boolean;
}

export interface HeatmapCellData {
  count: number;
  status: "covered" | "uncovered" | "excluded";
  testcase_ids: number[];
}

export interface HeatmapResponse {
  cat_a: string;
  cat_b: string;
  rows: string[];
  cols: string[];
  cells: Record<string, HeatmapCellData>;
}

export const coverageApi = {
  getCoverage: (generationId: number, t: number = 2) =>
    api.get<CoverageResponse>(`/generations/${generationId}/coverage`, { params: { t } }).then((r) => r.data),

  getHeatmap: (generationId: number, catA: string, catB: string, _options?: Record<string, unknown>) =>
    api.get<HeatmapResponse>(`/generations/${generationId}/coverage/pair`, { params: { a: catA, b: catB } }).then((r) => r.data),

  getUncoveredTuples: (generationId: number, t: number = 2, format: "json" | "csv" = "json") => {
    if (format === "csv") {
      return api.get(`/generations/${generationId}/coverage/missing`, {
        params: { t, format: "csv" },
        responseType: "blob",
      }).then((r) => r.data);
    }
    return api.get<{ generation_id: number; t: number; tuples: UncoveredTuple[]; total: number }>(
      `/generations/${generationId}/coverage/missing`,
      { params: { t, format: "json" } }
    ).then((r) => r.data);
  },
};

// ============================================================================
// REQ-6009: Seed API
// ============================================================================

import type {
  SeedSet,
  SeedSetList,
  SeedSetCreate,
  SeedSetUpdate,
  SeedCSVImportResponse,
  GapFillResponse,
} from "../types";

export const seedApi = {
  // CRUD
  list: (projectId: number) =>
    api.get<{ seed_sets: SeedSetList[] }>(`/projects/${projectId}/seed-sets`).then((r) => r.data.seed_sets),

  create: (projectId: number, data: SeedSetCreate) =>
    api.post<{ id: number; name: string; seed_count: number; warnings: string[] }>(
      `/projects/${projectId}/seed-sets`, data
    ).then((r) => r.data),

  get: (projectId: number, seedSetId: number) =>
    api.get<SeedSet>(`/projects/${projectId}/seed-sets/${seedSetId}`).then((r) => r.data),

  update: (projectId: number, seedSetId: number, data: SeedSetUpdate) =>
    api.put<{ id: number; name: string; seed_count: number; warnings: string[] }>(
      `/projects/${projectId}/seed-sets/${seedSetId}`, data
    ).then((r) => r.data),

  delete: (projectId: number, seedSetId: number) =>
    api.delete(`/projects/${projectId}/seed-sets/${seedSetId}`),

  // CSV Import
  importCsv: (projectId: number, name: string, file: File) => {
    const fd = new FormData();
    fd.append("name", name);
    fd.append("csv_content", file);
    return api.post<SeedCSVImportResponse>(
      `/projects/${projectId}/seed-sets/import-csv`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      }
    ).then((r) => r.data);
  },

  // Gap Fill
  gapFill: (generationId: number, strategy: string = "pairwise", tStrength: number = 2) =>
    api.post<GapFillResponse>(
      `/generations/${generationId}/gap-fill`,
      {},
      { params: { strategy, t_strength: tStrength } }
    ).then((r) => r.data),
};
