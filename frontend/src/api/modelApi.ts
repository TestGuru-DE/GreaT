// REQ-6013: API-Client fuer Modell-Export/Import
import api from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Response from GET /api/v1/projects/{id}/model */
export interface ModelExportResponse {
  /** Raw content (YAML or JSON string) */
  content: string;
  /** Suggested filename */
  filename: string;
  /** Format: 'yaml' or 'json' */
  format: "yaml" | "json";
}

/** Response from POST /api/v1/projects/import-model */
export interface ModelImportResponse {
  status: "ok";
  projectId: number;
  projectName: string;
}

/** Diff entry for change preview */
export interface ModelDiffResult {
  added: {
    categories: string[];
    values: string[];
    rules: string[];
  };
  modified: {
    categories: string[];
    values: string[];
    rules: string[];
  };
  removed: {
    categories: string[];
    values: string[];
    rules: string[];
  };
}

/** Response from PUT /api/v1/projects/{id}/model */
export interface ModelUpdateResponse {
  status: "ok";
  projectId: number;
  projectName: string;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

/**
 * Exportiert das Modell eines Projekts als YAML oder JSON.
 * Loest einen Datei-Download aus.
 */
export async function exportModel(
  projectId: number,
  format: "yaml" | "json" = "yaml",
  projectName: string,
): Promise<void> {
  const extension = format === "yaml" ? "yaml" : "json";
  const mediaType = format === "yaml" ? "text/yaml" : "application/json";
  const filename = `${projectName}.great.${extension}`;

  const response = await api.get(`/v1/projects/${projectId}/model`, {
    params: { format },
    responseType: "blob",
  });

  // Datei-Download ausloesen
  const blob = new Blob([response.data], { type: mediaType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Import (neues Projekt)
// ---------------------------------------------------------------------------

/**
 * Importiert ein Modell als neues Projekt.
 * @param content - YAML oder JSON Inhalt als String
 * @param format - 'yaml' oder 'json'
 */
export async function importModelNewProject(
  content: string,
  format: "yaml" | "json",
): Promise<ModelImportResponse> {
  const contentType = format === "yaml" ? "text/yaml" : "application/json";
  const response = await api.post<ModelImportResponse>(
    "/v1/projects/import-model",
    content,
    {
      params: { content_type: contentType },
      headers: { "Content-Type": contentType },
    },
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Preview (Aenderungsvorschau)
// ---------------------------------------------------------------------------

/**
 * Zeigt Aenderungsvorschau fuer bestehendes Projekt.
 * @param projectId - ID des bestehenden Projekts
 * @param parsedModel - Das geparste Modell-Objekt (als JSON-Serialisierbares Dict)
 */
export async function previewModelChanges(
  projectId: number,
  parsedModel: Record<string, unknown>,
): Promise<ModelDiffResult> {
  const response = await api.post<ModelDiffResult>(
    `/v1/projects/${projectId}/model/preview`,
    parsedModel,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Update (bestehendes Projekt aktualisieren)
// ---------------------------------------------------------------------------

/**
 * Aktualisiert ein bestehendes Projekt aus einem Modell.
 * @param projectId - ID des bestehenden Projekts
 * @param parsedModel - Das geparste Modell-Objekt (als JSON-Serialisierbares Dict)
 */
export async function updateProjectModel(
  projectId: number,
  parsedModel: Record<string, unknown>,
): Promise<ModelUpdateResponse> {
  const response = await api.put<ModelUpdateResponse>(
    `/v1/projects/${projectId}/model`,
    parsedModel,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Convenience: parse file content
// ---------------------------------------------------------------------------

/**
 * Parst den Inhalt einer Datei (YAML oder JSON) und gibt ein
 * JSON-serialisierbares Objekt zurueck.
 */
export async function parseModelFile(
  file: File,
): Promise<{ parsed: Record<string, unknown>; format: "yaml" | "json" }> {
  const text = await file.text();
  const name = file.name.toLowerCase();

  if (name.endsWith(".yaml") || name.endsWith(".yml")) {
    const jsyaml = await import("js-yaml");
    const parsed = jsyaml.load(text) as Record<string, unknown>;
    return { parsed, format: "yaml" };
  }

  if (name.endsWith(".json")) {
    const parsed = JSON.parse(text) as Record<string, unknown>;
    return { parsed, format: "json" };
  }

  throw new Error("Unsupported file format. Use .yaml or .json");
}