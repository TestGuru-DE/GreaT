// REQ-2003: Dialog zum Anwenden einer Datenklasse auf eine Kategorie
import { useEffect, useState } from "react";
import { dataclassApi } from "../api/client";
import type { DataClass } from "../api/client";
import { useToastStore } from "./Toast";

interface Props {
  categoryId: number;
  categoryName: string;
  onClose: () => void;
  onApplied: () => void;
}

export default function DataClassDialog({ categoryId, categoryName, onClose, onApplied }: Props) {
  const [dataclasses, setDataclasses] = useState<DataClass[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const toast = useToastStore();

  useEffect(() => {
    dataclassApi.list().then((dcs) => { setDataclasses(dcs); setLoading(false); });
  }, []);

  const handleApply = async () => {
    if (!selected) return;
    setApplying(true);
    try {
      const res = await dataclassApi.applyToCategory(categoryId, Number(selected));
      toast.add(`${res.added} Wert(e) aus "${res.dataclass_name}" hinzugefügt`);
      onApplied();
      onClose();
    } catch (e) {
      toast.add(String(e), "error");
    } finally {
      setApplying(false);
    }
  };

  const selectedDC = dataclasses.find((dc) => dc.id === Number(selected));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl p-6 w-[420px] max-w-full" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-semibold text-slate-800 mb-1">Datenklasse anwenden</h3>
        <p className="text-sm text-slate-500 mb-4">
          Auf Kategorie: <strong>{categoryName}</strong>
        </p>

        {loading ? (
          <p className="text-slate-400 text-sm">Lade Datenklassen...</p>
        ) : dataclasses.length === 0 ? (
          <div className="text-center py-4 text-slate-400">
            <p className="text-sm">Noch keine Datenklassen vorhanden.</p>
            <a href="/app/dataclasses" className="text-sky-600 hover:underline text-sm mt-1 block">
              Datenklassen verwalten →
            </a>
          </div>
        ) : (
          <>
            <label className="block text-xs text-slate-500 mb-1 font-medium">Datenklasse wählen</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value === "" ? "" : Number(e.target.value))}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400 mb-3"
            >
              <option value="">-- Datenklasse wählen --</option>
              {dataclasses.map((dc) => (
                <option key={dc.id} value={dc.id}>
                  {dc.name} ({dc.value_type})
                </option>
              ))}
            </select>
            {selectedDC && (
              <div className="mb-4 px-3 py-2 bg-slate-50 rounded-lg text-xs text-slate-500">
                <strong>Typ:</strong> {selectedDC.value_type}
                {selectedDC.description && <span className="ml-2">– {selectedDC.description}</span>}
              </div>
            )}
          </>
        )}

        <div className="flex gap-2 justify-end">
          <button onClick={onClose}
            className="px-4 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
            Abbrechen
          </button>
          <button onClick={handleApply} disabled={applying || !selected}
            className="px-4 py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50">
            {applying ? "..." : "Anwenden"}
          </button>
        </div>
      </div>
    </div>
  );
}