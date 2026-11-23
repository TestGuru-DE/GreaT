// REQ-6009: CSV-Import Dialog fuer Seed-Saetze
import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useSeedStore } from "../store/seedStore";

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
    <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">
        {t("seedImport.title", { defaultValue: "CSV Import" })}
      </h3>

      {msg && (
        <div className={`mb-3 px-3 py-2 rounded-lg text-sm ${
          msg.type === "ok" ? "bg-green-50 border border-green-200 text-green-700" :
          msg.type === "warn" ? "bg-amber-50 border border-amber-200 text-amber-700" :
          "bg-red-50 border border-red-200 text-red-700"
        }`}>
          {msg.type === "warn" && "⚠️ "}{msg.text}
        </div>
      )}

      <div className="space-y-3">
        {/* Name */}
        <div>
          <label className="text-xs font-medium text-slate-500 mb-1 block">
            {t("seedImport.setNameLabel", { defaultValue: "Name des Seed-Satzes" })}
          </label>
          <input
            type="text"
            value={setName}
            onChange={(e) => setSetName(e.target.value)}
            placeholder={t("seedImport.setNamePlaceholder", { defaultValue: "z.B. Meine Seeds" })}
            className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white text-black"
          />
        </div>

        {/* File Drop Zone */}
        <div>
          <label className="text-xs font-medium text-slate-500 mb-1 block">
            {t("seedImport.fileLabel", { defaultValue: "CSV-Datei" })}
          </label>
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
              file
                ? "border-sky-300 bg-sky-50"
                : "border-slate-300 hover:border-slate-400"
            }`}
          >
            {file ? (
              <div className="text-sm text-sky-700">
                📄 {file.name}
              </div>
            ) : (
              <div className="text-sm text-slate-400">
                {t("seedImport.dropText", { defaultValue: "CSV-Datei hier ablegen oder..." })}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-sky-600 underline ml-1"
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
        <div className="text-xs text-slate-400 bg-white border border-slate-200 rounded-lg p-3">
          <p className="font-medium text-slate-500 mb-1">
            {t("seedImport.formatTitle", { defaultValue: "CSV-Format" })}
          </p>
          <p>
            {t("seedImport.formatDesc", {
              defaultValue: "Erste Zeile: Kategorien (Kopfzeile). Jede weitere Zeile: Werte. Leer = (any/null). Trennzeichen: Komma oder Semikolon (auto-erkennung).",
            })}
          </p>
          <pre className="mt-2 text-[10px] bg-slate-50 rounded p-2 overflow-x-auto">
            {t("seedImport.formatExample", {
              defaultValue: "KategorieA,KategorieB,KategorieC\nWert1,,Wert3\n,Vert2,Vert3",
            })}
          </pre>
        </div>

        {/* Actions */}
        <div className="flex gap-2 justify-end">
          <button
            onClick={handleCancel}
            className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            {t("seedImport.cancel", { defaultValue: "Abbrechen" })}
          </button>
          <button
            onClick={handleImport}
            disabled={!setName.trim() || !file || loading}
            className="px-4 py-1.5 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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