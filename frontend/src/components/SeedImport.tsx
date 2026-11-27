// REQ-6009: CSV-Import Dialog fuer Seed-Saetze
import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useSeedStore } from "../store/seedStore";
import { TriangleAlert } from "lucide-react";

interface Props {
  projectId: number;
  onClose: () => void;
}

export default function SeedImport({ projectId, onClose }: Props) {
  const { t } = useTranslation();
  const { importCsv, loading, msg, clearMsg } = useSeedStore();
  const [setName, setSetName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const handleImport = async () => {
    if (!setName.trim() || !file) return;
    const result = await importCsv(projectId, setName.trim(), file);
    if (result) {
      onClose();
    }
  };

  const handleCancel = () => {
    setSetName("");
    setFile(null);
    clearMsg();
    onClose();
  };

  return (
    <div className="border border-theme-border rounded-2xl p-4 bg-theme-surface-2">
      <h3 className="text-sm font-semibold text-theme-text mb-3">
        {t("seedImport.title", { defaultValue: "CSV Import" })}
      </h3>

      {msg && (
        <div className={`mb-3 px-3 py-2 rounded-lg text-sm ${
          msg.type === "ok" ? "bg-theme-success-soft border border-theme-success-border text-theme-success" :
          msg.type === "warn" ? "bg-theme-warning-soft border border-theme-warning-border text-theme-warning" :
          "bg-theme-danger-soft border border-theme-danger-border text-theme-danger"
        }`}>
          {msg.type === "warn" && <TriangleAlert className="w-4 h-4 inline-block align-[-3px] mr-1" aria-hidden="true" />}{msg.text}
        </div>
      )}

      <div className="space-y-3">
        {/* Name */}
        <div>
          <label className="text-xs font-medium text-theme-text-secondary mb-1 block">
            {t("seedImport.setNameLabel", { defaultValue: "Name des Seed-Satzes" })}
          </label>
          <input
            type="text"
            value={setName}
            onChange={(e) => setSetName(e.target.value)}
            placeholder={t("seedImport.setNamePlaceholder", { defaultValue: "z.B. Meine Seeds" })}
            className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
          />
        </div>

        {/* File Drop Zone */}
        <div>
          <label className="text-xs font-medium text-theme-text-secondary mb-1 block">
            {t("seedImport.fileLabel", { defaultValue: "CSV-Datei" })}
          </label>
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
              file
                ? "border-theme-accent bg-theme-accent-soft"
                : "border-theme-border hover:border-theme-border-strong"
            }`}
          >
            {file ? (
              <div className="text-sm text-theme-link">
                📄 {file.name}
              </div>
            ) : (
              <div className="text-sm text-theme-text-muted">
                {t("seedImport.dropText", { defaultValue: "CSV-Datei hier ablegen oder..." })}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-theme-link underline ml-1"
                >
                  {t("seedImport.browse", { defaultValue: "durchsuchen" })}
                </button>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>

        {/* Format Info */}
        <div className="text-xs text-theme-text-muted bg-theme-surface border border-theme-border rounded-lg p-3">
          <p className="font-medium text-theme-text-secondary mb-1">
            {t("seedImport.formatTitle", { defaultValue: "CSV-Format" })}
          </p>
          <p>
            {t("seedImport.formatDesc", {
              defaultValue: "Erste Zeile: Kategorien (Kopfzeile). Jede weitere Zeile: Werte. Leer = (any/null). Trennzeichen: Komma oder Semikolon (auto-erkennung).",
            })}
          </p>
          <pre className="mt-2 text-[10px] bg-theme-surface-2 rounded p-2 overflow-x-auto">
            {t("seedImport.formatExample", {
              defaultValue: "KategorieA,KategorieB,KategorieC\nWert1,,Wert3\n,Vert2,Vert3",
            })}
          </pre>
        </div>

        {/* Actions */}
        <div className="flex gap-2 justify-end">
          <button
            onClick={handleCancel}
            className="px-3 py-1.5 text-sm text-theme-text-secondary hover:text-theme-text transition-colors"
          >
            {t("seedImport.cancel", { defaultValue: "Abbrechen" })}
          </button>
          <button
            onClick={handleImport}
            disabled={!setName.trim() || !file || loading}
            className="px-4 py-1.5 text-sm bg-theme-accent text-white rounded-lg hover:bg-theme-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading
              ? t("seedImport.importing", { defaultValue: "Importiere..." })
              : t("seedImport.importBtn", { defaultValue: "Importieren" })
            }
          </button>
        </div>
      </div>
    </div>
  );
}