// REQ-3009: Generierungen-Tab im Projektdetail
import { useEffect, useState, useCallback } from "react";
import { generateApi } from "../api/client";
import type { GenerationSummary } from "../api/client";

interface Props { projectId: number; }

export default function GenerationsPanel({ projectId }: Props) {
  const [items, setItems] = useState<GenerationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const gens = await generateApi.listGenerations(projectId);
      setItems([...gens].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (gid: number) => {
    if (!confirm("Generierung löschen?")) return;
    await generateApi.deleteGeneration(gid);
    setItems((prev) => prev.filter((g) => g.id !== gid));
  };

  const startEdit = (g: GenerationSummary) => { setEditingId(g.id); setEditName(g.name); };

  const saveEdit = async (gid: number) => {
    if (!editName.trim()) return;
    const updated = await generateApi.renameGeneration(gid, editName.trim());
    setItems((prev) => prev.map((g) => g.id === gid ? { ...g, name: updated.name } : g));
    setEditingId(null);
  };

  const handleExport = (gid: number, fmt: string) => {
    window.open(`/api/generations/${gid}/export/${fmt}`, "_blank");
  };

  if (loading) return <p className="text-sm text-slate-400">Lade Generierungen...</p>;

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p className="text-3xl mb-2">📋</p>
        <p>Noch keine Generierungen für dieses Projekt.</p>
        <p className="text-xs mt-1">Wechsle zum Tab „Testfall-Generierung", um eine zu erstellen.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((g) => (
        <div key={g.id} className="flex items-center gap-3 px-4 py-3 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white transition-colors">
          <div className="flex-1 min-w-0">
            {editingId === g.id ? (
              <input
                autoFocus
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") saveEdit(g.id); if (e.key === "Escape") setEditingId(null); }}
                className="w-full px-2 py-0.5 text-sm border border-sky-400 rounded focus:outline-none"
              />
            ) : (
              <span
                className="text-sm font-medium text-slate-700 cursor-pointer hover:text-sky-600 block truncate"
                onDoubleClick={() => startEdit(g)}
                title="Doppelklick zum Umbenennen"
              >
                {g.name}
              </span>
            )}
            <p className="text-xs text-slate-400 mt-0.5">
              {g.strategy} · {g.testcase_count} Testfälle · {new Date(g.created_at).toLocaleDateString("de-DE")}
            </p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => startEdit(g)} title="Umbenennen" className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-100">✏️</button>
            <button onClick={() => handleExport(g.id, "json")} className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-100">JSON</button>
            <button onClick={() => handleExport(g.id, "xlsx")} className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-100">Excel</button>
            <button onClick={() => handleExport(g.id, "csv")} className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-100">CSV</button>
            <button onClick={() => handleDelete(g.id)} title="Löschen" className="text-xs px-2 py-1 border border-red-200 text-red-500 rounded hover:bg-red-50">🗑️</button>
          </div>
        </div>
      ))}
    </div>
  );
}