// REQ-1203: Typsicherer API-Client fuer alle FastAPI-Endpunkte
// REQ-1209, REQ-1213: Rename + Reorder Endpunkte
import axios from "axios";
import type {
  Project, ProjectCreate,
  Category, CategoryCreate,
  Value, ValueCreate,
  GenerateRequest, GenerateResponse, TestCaseOut,
} from "../types";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message;
    return Promise.reject(new Error(String(msg)));
  }
);

// --- Projekte ---
export const projectsApi = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  create: (data: ProjectCreate) =>
    api.post<Project>("/projects", data).then((r) => r.data),
  delete: (id: number) =>
    api.delete<{ok: boolean}>("/projects/" + id).then((r) => r.data),
  forceDelete: (id: number) =>
    api.delete<{ok: boolean}>("/projects/" + id + "/force").then((r) => r.data),
  bulkDelete: (ids: number[]) =>
    api.post<{deleted: number; blocked: number[]}>("/projects/bulk-delete", { project_ids: ids }).then((r) => r.data),
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
  getValues: (categoryId: number) =>
    api.get<Value[]>("/categories/" + categoryId + "/values").then((r) => r.data),
  updateProperties: (valueId: number, props: { risk_weight?: number; vtype?: string; allowed?: boolean }) =>
    api.patch<Value>("/values/" + valueId + "/properties", props).then((r) => r.data),
  setDefault: (valueId: number) =>
    api.patch<Value>("/values/" + valueId + "/set-default").then((r) => r.data),
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

export const generateApi = {
  run: (projectId: number, req: GenerateRequest) =>
    api.post<GenerateResponse>("/projects/" + projectId + "/generate", req).then((r) => r.data),
  getTestcases: (generationId: number) =>
    api.get<TestCaseOut[]>("/generations/" + generationId + "/testcases").then((r) => r.data),
  listGenerations: (projectId: number) =>
    api.get<GenerationSummary[]>("/projects/" + projectId + "/generations").then((r) => r.data),
  renameGeneration: (generationId: number, name: string) =>
    api.patch<GenerationSummary>("/generations/" + generationId + "/rename", { name }).then((r) => r.data),
  deleteGeneration: (generationId: number) =>
    api.delete<{ok: boolean}>("/generations/" + generationId).then((r) => r.data),
};

// --- Rename + Reorder (REQ-1209, REQ-1213) ---
export const renameApi = {
  category: (categoryId: number, name: string) =>
    api.patch<Category>("/categories/" + categoryId + "/rename", { name }).then((r) => r.data),
  value: (valueId: number, value: string) =>
    api.patch<Value>("/values/" + valueId + "/rename", { value }).then((r) => r.data),
};

export const reorderApi = {
  categories: (projectId: number, order: number[]) =>
    api.patch("/projects/" + projectId + "/categories/reorder", { order }).then((r) => r.data),
};

export default api;


// --- Datenklassen (REQ-2003) ---
export interface DataClass {
  id: number;
  name: string;
  value_type: string;
  description: string | null;
  is_system?: boolean;
}

export interface DataClassValue {
  id: number;
  value: string;
}

export const dataclassApi = {
  list: () => api.get<DataClass[]>("/dataclasses").then((r) => r.data),
  create: (data: { name: string; value_type: string; description?: string }) =>
    api.post<DataClass>("/dataclasses", data).then((r) => r.data),
  delete: (id: number) =>
    api.delete<{ok: boolean}>("/dataclasses/" + id).then((r) => r.data),
  bulkDelete: (ids: number[]) =>
    api.post<{deleted: number; blocked: number}>("/dataclasses/bulk-delete", { dataclass_ids: ids }).then((r) => r.data),
  listValues: (dcId: number) =>
    api.get<DataClassValue[]>("/dataclasses/" + dcId + "/values").then((r) => r.data),
  addValue: (dcId: number, value: string) =>
    api.post<DataClassValue>("/dataclasses/" + dcId + "/values", { value }).then((r) => r.data),
  deleteValue: (vid: number) =>
    api.delete<{ok: boolean}>("/dataclasses/values/" + vid).then((r) => r.data),
  applyToCategory: (categoryId: number, dataclassId: number) =>
    api.post<{added: number; dataclass_name: string}>("/categories/" + categoryId + "/apply-dataclass", { dataclass_id: dataclassId }).then((r) => r.data),
};
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