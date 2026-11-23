// REQ-6009: Seed-Saetze verwalten (Uebersicht + Editor)
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSeedStore } from "../store/seedStore";
import { categoriesApi } from "../api/client";
import type { Category, SeedCase, SeedSet } from "../types";
import SeedImport from "./SeedImport";

interface Props {
  projectId: number;
}

export default function SeedManager({ projectId }: Props) {
  const { t } = useTranslation();
  const {
    seedSets, currentSet, loading, error, msg,
    fetchSeedSets, createSeedSet, loadSeedSet, updateSeedSet, deleteSeedSet,
    addSeed, removeSeed, updateSeed, clearMsg,
  } = useSeedStore();

  const [categories, setCategories] = useState<Category[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [newSetName, setNewSetName] = useState("");

  // Kategorien laden (fuer Assignment-Dropdowns)
  useEffect(() => {
    (async () => {
      try {
        const cats = await categoriesApi.list(projectId);
        setCategories(cats);
      } catch { /* ignore */ }
    })();
  }, [projectId]);

  // Seed-Saetze laden
  useEffect(() => {
    fetchSeedSets(projectId);
  }, [projectId, fetchSeedSets]);

  const handleCreate = async () => {
    if (!newSetName.trim()) return;
    await createSeedSet(projectId, { name: newSetName.trim(), seeds: [] });
    setNewSetName("");
    setShowCreate(false);
  };

  const handleSelectSet = async (ssid: number) => {
    await loadSeedSet(projectId, ssid);
  };

  const handleDeleteSet = async (ssid: number) => {
    if (!confirm(t("seedManager.deleteConfirm", { defaultValue: "Seed-Satz loeschen?" }))) return;
    await deleteSeedSet(projectId, ssid);
  };

  const handleSaveSet = async () => {
    if (!currentSet) return;
    const seeds = currentSet.seed_cases.map((sc) => sc.assignment);
    await updateSeedSet(projectId, currentSet.id, { seeds });
  };

  const handleAddSeed = () => {
    // Leeres Assignment mit allen Kategorien auf null
    const empty: Record<string, string | null> = {};
    categories.forEach((c) => { empty[c.name] = null; });
    addSeed(empty);
  };

  const handleAssignmentChange = (seedIndex: number, catName: string, value: string) => {
    if (!currentSet) return;
    const seed = currentSet.seed_cases[seedIndex];
    if (!seed) return;
    const newAssignment = { ...seed.assignment, [catName]: value || null };
    updateSeed(seedIndex, newAssignment);
  };

  // Message anzeigen
  useEffect(() => {
    if (msg) {
      const timer = setTimeout(() => clearMsg(), 5000);
      return () => clearTimeout(timer);
    }
  }, [msg, clearMsg]);

  return (
    <div className="flex flex-col gap-4">
      {/* Message */}
      {msg && (
        <div className={`px-3 py-2 rounded-lg text-sm ${
          msg.type === "ok" ? "bg-green-50 border border-green-200 text-green-700" :
          msg.type === "warn" ? "bg-amber-50 border border-amber-200 text-amber-700" :
          "bg-red-50 border border-red-200 text-red-700"
        }`}>
          {msg.type === "warn" && "⚠️ "}{msg.text}
        </div>
      )}

      {error && (
        <div className="px-3 py-2 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700">
          {error}
        </div>
      )}

      {/* Header + Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">
          {t("seedManager.title", { defaultValue: "Seed-Saetze" })}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreate(true)}
            className="px-3 py-1.5 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
          >
            {t("seedManager.newSet", { defaultValue: "+ Neuer Satz" })}
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="px-3 py-1.5 text-sm bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
          >
            {t("seedManager.importCsv", { defaultValue: "CSV Import" })}
          </button>
        </div>
      </div>

      {/* Create Dialog */}
      {showCreate && (
        <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            {t("seedManager.createTitle", { defaultValue: "Neuer Seed-Satz" })}
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={newSetName}
              onChange={(e) => setNewSetName(e.target.value)}
              placeholder={t("seedManager.setNamePlaceholder", { defaultValue: "Name des Seed-Satzes" })}
              className="flex-1 px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white text-black"
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button
              onClick={handleCreate}
              className="px-4 py-1.5 text-sm bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
            >
              {t("seedManager.saveBtn", { defaultValue: "Speichern" })}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            >
              {t("seedManager.cancel", { defaultValue: "Abbrechen" })}
            </button>
          </div>
        </div>
      )}

      {/* Seed-Saetze Liste */}
      {loading ? (
        <p className="text-sm text-slate-400 animate-pulse">{t("seedManager.loading", { defaultValue: "Laden..." })}</p>
      ) : seedSets.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-8">
          {t("seedManager.noSets", { defaultValue: "Noch keine Seed-Saetze. Erstellen oder importieren." })}
        </p>
      ) : (
        <div className="space-y-2">
          {seedSets.map((ss) => (
            <div
              key={ss.id}
              className={`flex items-center justify-between px-4 py-3 border rounded-xl text-sm transition-colors ${
                currentSet?.id === ss.id
                  ? "bg-sky-50 border-sky-300"
                  : "bg-white border-slate-200 hover:bg-slate-50"
              }`}
            >
              <button
                onClick={() => handleSelectSet(ss.id)}
                className="flex-1 text-left"
              >
                <div className="font-medium text-slate-800">{ss.name}</div>
                <div className="text-xs text-slate-500">
                  {ss.seed_count} {t("seedManager.seeds", { defaultValue: "Seeds" })}
                  {ss.created_at && ` · ${new Date(ss.created_at).toLocaleDateString("de-DE")}`}
                </div>
              </button>
              <button
                onClick={() => handleDeleteSet(ss.id)}
                className="ml-3 text-slate-300 hover:text-red-500 transition-colors text-lg leading-none"
                title={t("seedManager.deleteTitle", { defaultValue: "Loeschen" })}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Seed-Editor (wenn Satz ausgewaehlt) */}
      {currentSet && (
        <SeedEditor
          seedSet={currentSet}
          categories={categories}
          onAddSeed={handleAddSeed}
          onRemoveSeed={removeSeed}
          onAssignmentChange={handleAssignmentChange}
          onSave={handleSaveSet}
        />
      )}

      {/* CSV Import Dialog */}
      {showImport && (
        <SeedImport
          projectId={projectId}
          onClose={() => setShowImport(false)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SeedEditor: Editor fuer die Seeds eines Satzes
// ---------------------------------------------------------------------------

interface SeedEditorProps {
  seedSet: SeedSet;
  categories: Category[];
  onAddSeed: () => void;
  onRemoveSeed: (index: number) => void;
  onAssignmentChange: (seedIndex: number, catName: string, value: string) => void;
  onSave: () => void;
}

function SeedEditor({
  seedSet, categories, onAddSeed, onRemoveSeed, onAssignmentChange, onSave,
}: SeedEditorProps) {
  const { t } = useTranslation();

  if (categories.length === 0) {
    return (
      <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
        <p className="text-sm text-slate-400">
          {t("seedManager.needCategories", { defaultValue: "Zuerst Kategorien anlegen." })}
        </p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-700">
          {t("seedManager.editorTitle", { defaultValue: "Seeds bearbeiten" })}: {seedSet.name}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={onAddSeed}
            className="px-3 py-1 text-xs bg-white border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors"
          >
            + {t("seedManager.addSeed", { defaultValue: "Seed" })}
          </button>
          <button
            onClick={onSave}
            className="px-3 py-1 text-xs bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
          >
            {t("seedManager.saveSet", { defaultValue: "Satz speichern" })}
          </button>
        </div>
      </div>

      {seedSet.seed_cases.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-4">
          {t("seedManager.noSeeds", { defaultValue: "Noch keine Seeds. Fuege welche hinzu." })}
        </p>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {seedSet.seed_cases.map((seed, idx) => (
            <SeedRow
              key={idx}
              index={idx}
              seed={seed}
              categories={categories}
              onAssignmentChange={onAssignmentChange}
              onRemove={() => onRemoveSeed(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SeedRow: Einzelner Seed (Zeile mit Assignment-Dropdowns)
// ---------------------------------------------------------------------------

interface SeedRowProps {
  index: number;
  seed: SeedCase;
  categories: Category[];
  onAssignmentChange: (seedIndex: number, catName: string, value: string) => void;
  onRemove: () => void;
}

function SeedRow({ index, seed, categories, onAssignmentChange, onRemove }: SeedRowProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg">
      <span className="text-xs font-mono text-slate-400 w-6 text-right">{index + 1}</span>
      <div className="flex-1 grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-1">
        {categories.map((cat) => {
          // Werte der Kategorie als Optionen
          // Hinweis: wir haben hier keinen direkten Zugriff auf Werte;
          // wir zeigen den aktuellen Wert als Text und erlauben manuelle Eingabe
          const currentValue = seed.assignment[cat.name] ?? "";
          return (
            <div key={cat.id} className="flex items-center gap-1">
              <span className="text-[10px] text-slate-400 w-16 truncate" title={cat.name}>
                {cat.name.length > 8 ? cat.name.slice(0, 8) + "…" : cat.name}
              </span>
              <input
                type="text"
                value={currentValue ?? ""}
                placeholder={t("seedManager.anyPlaceholder", { defaultValue: "(any)" })}
                onChange={(e) => onAssignmentChange(index, cat.name, e.target.value)}
                className="flex-1 min-w-0 px-1.5 py-0.5 text-xs border border-slate-200 rounded bg-slate-50 focus:outline-none focus:ring-1 focus:ring-sky-400 text-black"
              />
            </div>
          );
        })}
      </div>
      <button
        onClick={onRemove}
        className="text-slate-300 hover:text-red-500 transition-colors text-sm leading-none"
        title={t("seedManager.removeSeed", { defaultValue: "Seed entfernen" })}
      >
        ×
      </button>
    </div>
  );
}