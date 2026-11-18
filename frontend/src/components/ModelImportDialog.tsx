// REQ-6013: Import-Dialog mit Datei-Upload, zwei Modi und Aenderungsvorschau
// REQ-6005 Slice 3: i18n Zahlenformate
import { useState, useRef, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Upload, X, AlertTriangle, FileText } from "lucide-react";
import type { Project } from "../types";
import {
  parseModelFile,
  importModelNewProject,
  previewModelChanges,
  updateProjectModel,
  type ModelDiffResult,
} from "../api/modelApi";
import { useToastStore } from "./Toast";
import { useFormattedNumber } from "../hooks/useFormattedNumber";
import ModelDiffPreview from "./ModelDiffPreview";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

type ImportMode = "new" | "update";

interface Props {
  projects: Project[];
  onClose: () => void;
  onProjectCreated: (project: Project) => void;
  onProjectUpdated: (project: Project) => void;
}

export default function ModelImportDialog({ projects, onClose, onProjectCreated, onProjectUpdated }: Props) {
  const { t } = useTranslation();
  const { formatNumber } = useFormattedNumber({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ImportMode>("new");
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [diff, setDiff] = useState<ModelDiffResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // parsedModel cache
  const [parsedModel, setParsedModel] = useState<Record<string, unknown> | null>(null);
  const [detectedFormat, setDetectedFormat] = useState<"yaml" | "json" | null>(null);

  // Datei validieren und parsen
  const handleFile = useCallback(async (f: File) => {
    setError(null);
    setValidationErrors([]);
    setDiff(null);
    setParsedModel(null);
    setDetectedFormat(null);

    // Dateiname-Prüfung
    const name = f.name.toLowerCase();
    if (!name.endsWith(".yaml") && !name.endsWith(".yml") && !name.endsWith(".json")) {
      setError(t("modelImport.errorInvalidFormat"));
      setFile(null);
      return;
    }

    // Groessenpruefung
    if (f.size > MAX_FILE_SIZE) {
      setError(t("modelImport.errorFileTooLarge"));
      setFile(null);
      return;
    }

    setFile(f);
    setLoading(true);

    try {
      const { parsed, format } = await parseModelFile(f);
      setParsedModel(parsed);
      setDetectedFormat(format);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setFile(null);
    } finally {
      setLoading(false);
    }
  }, [t]);

  // Drag & Drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  }, [handleFile]);

  // File input change
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  }, [handleFile]);

  // Aenderungsvorschau laden bei Aktualisierungs-Modus
  useEffect(() => {
    if (mode !== "update" || !parsedModel || !selectedProjectId) {
      setDiff(null);
      return;
    }

    setPreviewLoading(true);
    previewModelChanges(selectedProjectId, parsedModel)
      .then((result) => {
        setDiff(result);
        setValidationErrors([]);
      })
      .catch((err: unknown) => {
        const apiErr = err as { response?: { data?: { detail?: string } }; message?: string };
        const detail = apiErr.response?.data?.detail ?? apiErr.message ?? String(err);

        // Pruefe ob Validierungsfehler (400)
        if (typeof detail === "string" && detail.includes(";")) {
          setValidationErrors(detail.split(";").map(s => s.trim()));
        } else {
          setError(t("modelImport.errorPreview", { error: detail }));
        }
        setDiff(null);
      })
      .finally(() => {
        setPreviewLoading(false);
      });
  }, [mode, parsedModel, selectedProjectId, t]);

  // Import ausfuehren
  const handleImport = useCallback(async () => {
    if (!file || !parsedModel || !detectedFormat) return;

    setLoading(true);
    setError(null);
    setValidationErrors([]);

    try {
      if (mode === "new") {
        // Neues Projekt erstellen
        const content = detectedFormat === "yaml"
          ? (await import("js-yaml")).dump(parsedModel)
          : JSON.stringify(parsedModel);

        const result = await importModelNewProject(content, detectedFormat);
        useToastStore.getState().add(
          t("modelImport.successNew", { name: result.projectName }),
          "success",
        );

        // Zum Projekt navigieren
        navigate(`/projects/${result.projectId}`);
        onProjectCreated({ id: result.projectId, name: result.projectName, version: 1 } as Project);
        onClose();
      } else {
        // Bestehendes Projekt aktualisieren
        if (!selectedProjectId) return;

        const result = await updateProjectModel(selectedProjectId, parsedModel);
        useToastStore.getState().add(
          t("modelImport.successUpdate", { name: result.projectName }),
          "success",
        );

        navigate(`/projects/${result.projectId}`);
        onProjectUpdated({ id: result.projectId, name: result.projectName, version: 1 } as Project);
        onClose();
      }
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const detail = apiErr.response?.data?.detail ?? apiErr.message ?? String(err);

      if (typeof detail === "string" && detail.includes(";")) {
        setValidationErrors(detail.split(";").map(s => s.trim()));
      } else {
        setError(t("modelImport.errorImport", { error: detail }));
      }
    } finally {
      setLoading(false);
    }
  }, [file, parsedModel, detectedFormat, mode, selectedProjectId, t, navigate, onClose, onProjectCreated, onProjectUpdated]);

  // Button aktiv?
  const isImportEnabled = file && parsedModel && !loading && !previewLoading &&
    (mode === "new" || (selectedProjectId !== null && !previewLoading));

  // Projekt-Dropdown-Optionen
  const projectOptions = projects.map(p => ({ id: p.id, name: p.name }));

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label={t("modelImport.title")}
    >
      <div className="bg-theme-surface rounded-2xl shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto border border-theme-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border">
          <h3 className="text-lg font-semibold text-theme-text">
            {t("modelImport.title")}
          </h3>
          <button
            onClick={onClose}
            className="text-theme-text-muted hover:text-theme-text transition-colors"
            aria-label={t("common.close")}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Datei-Upload */}
          <div>
            <label className="block text-sm font-medium text-theme-text mb-1">
              {t("modelImport.fileSelect")}
            </label>
            <div
              className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
                isDragOver
                  ? "border-theme-accent bg-theme-surface-hover"
                  : "border-theme-border hover:border-theme-text-secondary"
              } ${file ? "bg-theme-bg" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              aria-label={t("modelImport.dragDrop")}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click(); }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".yaml,.yml,.json"
                className="hidden"
                onChange={handleFileInputChange}
                aria-hidden="true"
              />
              {file ? (
                <div className="flex items-center justify-center gap-2 text-sm text-theme-text">
                  <FileText className="w-4 h-4 text-theme-accent" />
                  <span className="font-medium">{file.name}</span>
                  <span className="text-theme-text-muted text-xs">
                    ({formatNumber(file.size / 1024)} KB)
                  </span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="w-8 h-8 text-theme-text-muted" />
                  <p className="text-sm text-theme-text-secondary">
                    {t("modelImport.dragDrop")}
                  </p>
                  <p className="text-xs text-theme-text-muted">
                    {t("modelImport.acceptedFormats")}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Import-Modus */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-theme-text">
              {t("modelImport.mode")}
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-theme-text cursor-pointer">
                <input
                  type="radio"
                  name="importMode"
                  checked={mode === "new"}
                  onChange={() => { setMode("new"); setSelectedProjectId(null); setDiff(null); }}
                  className="accent-theme-accent"
                />
                {t("modelImport.modeNew")}
              </label>
              <label className="flex items-center gap-2 text-sm text-theme-text cursor-pointer">
                <input
                  type="radio"
                  name="importMode"
                  checked={mode === "update"}
                  onChange={() => { setMode("update"); setDiff(null); }}
                  className="accent-theme-accent"
                />
                {t("modelImport.modeUpdate")}
              </label>
            </div>
          </div>

          {/* Projekt-Dropdown (bei Aktualisierung) */}
          {mode === "update" && (
            <div>
              <label
                htmlFor="import-project-select"
                className="block text-sm font-medium text-theme-text mb-1"
              >
                {t("modelImport.projectSelect")}
              </label>
              <select
                id="import-project-select"
                value={selectedProjectId ?? ""}
                onChange={(e) => setSelectedProjectId(Number(e.target.value) || null)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-theme-border bg-theme-bg text-theme-text focus:ring-2 focus:ring-theme-accent focus:border-transparent"
                disabled={!file || previewLoading}
              >
                <option value="">{t("modelImport.projectSelect")}</option>
                {projectOptions.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Aenderungsvorschau */}
          {(mode === "update" && (diff || previewLoading)) && (
            <div>
              {previewLoading ? (
                <div className="flex items-center gap-2 text-sm text-theme-text-muted">
                  <span className="inline-block w-4 h-4 border-2 border-theme-text-muted border-t-transparent rounded-full animate-spin" />
                  {t("modelImport.previewLoading")}
                </div>
              ) : diff ? (
                <ModelDiffPreview diff={diff} />
              ) : null}
            </div>
          )}

          {/* Warnhinweis bei Aktualisierung */}
          {mode === "update" && (
            <div className="flex items-start gap-2 text-sm text-theme-warning bg-theme-bg border border-theme-warning rounded-lg px-3 py-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{t("modelImport.warning")}</span>
            </div>
          )}

          {/* Fehler */}
          {error && (
            <div className="text-sm text-theme-danger bg-theme-bg border border-theme-danger rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* Validierungsfehler */}
          {validationErrors.length > 0 && (
            <div className="text-sm text-theme-danger bg-theme-bg border border-theme-danger rounded-lg px-3 py-2">
              <p className="font-medium mb-1">{t("modelImport.errorValidation")}</p>
              <ul className="list-disc list-inside space-y-0.5">
                {validationErrors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-theme-border">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover transition-colors"
            disabled={loading}
          >
            {t("modelImport.cancel")}
          </button>
          <button
            onClick={handleImport}
            disabled={!isImportEnabled}
            className="px-4 py-2 text-sm bg-theme-accent text-theme-accent-text rounded-lg hover:opacity-90 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-theme-accent-text border-t-transparent rounded-full animate-spin" />
                {t("modelImport.confirmLoading")}
              </>
            ) : (
              t("modelImport.confirm")
            )}
          </button>
        </div>
      </div>
    </div>
  );
}