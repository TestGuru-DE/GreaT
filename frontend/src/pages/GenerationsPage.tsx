// REQ-3009: Globale Generierungsübersicht (alle Projekte)
import { useEffect, useState } from "react";
import { generateApi, projectsApi } from "../api/client";
import type { GenerationSummary } from "../api/client";

interface GenWithProject extends GenerationSummary {
  projectId: number;
  projectName: string;
}

export default function GenerationsPage() {
  const [items, setItems] = useState<GenWithProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const projects = await projectsApi.list();
      const all: GenWithProject[] = [];
      await Promise.all(projects.map(async (p) => {
        const gens = await generateApi.listGenerations(p.id);
        gens.forEach((g) => all.push({ ...g, projectId: p.id, projectName: p.name }));
      }));
      all.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setItems(all);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (gid: number) => {
    if (!confirm("Generierung löschen?")) return;
    await generateApi.deleteGeneration(gid);
    setItems((prev) => prev.filter((g) => g.id !== gid));
    setMsg("Generierung gelöscht.");
    setTimeout(() => setMsg(null), 3000);
  };

  const startEdit = (g: GenWithProject) => { setEditingId(g.id); setEditName(g.name); };

  const saveEdit = async (gid: number) => {
    if (!editName.trim()) return;
    const updated = await generateApi.renameGeneration(gid, editName.trim());
    setItems((prev) => prev.map((g) => g.id === gid ? { ...g, name: updated.name } : g));
    setEditingId(null);
  };

  const handleExport = (gid: number, fmt: string) => {
    window.open(`/api/generations/${gid}/export/${fmt}`, "_blank");
  };

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 bg-theme-bg min-h-screen">
      <div className="bg-theme-surface rounded-2xl border border-slate-200 border-theme-border shadow-sm p-6 text-white text-theme-text">
        <h2 className="text-lg font-semibold text-white text-theme-text mb-4">Alle Generierungen</h2>

        {msg && (
          <div className="mb-4 px-4 py-2 bg-green-50 bg-theme-surface border border-green-200 border-theme-success rounded-lg text-green-700 text-theme-success text-sm">
            {msg}
          </div>
        )}

        {loading ? (
          <p className="text-white text-theme-text-secondary text-sm">Lade Generierungen...</p>
        ) : items.length === 0 ? (
          <div className="text-center py-12 text-white text-theme-text-muted">
            <p className="text-3xl mb-2">📋</p>
            <p>Noch keine Generierungen vorhanden.</p>
          </div>
        ) : (
          <table className="w-full text-sm text-white text-theme-text">
            <thead>
              <tr className="border-b-2 border-theme-border text-left">
                <th className="px-3 py-2 text-white text-theme-text font-medium">Name</th>
                <th className="px-3 py-2 text-white text-theme-text font-medium">Projekt</th>
                <th className="px-3 py-2 text-black text-theme-text font-medium">Strategie</th>
                <th className="px-3 py-2 text-white text-theme-text font-medium w-24">Testfälle</th>
                <th className="px-3 py-2 text-white text-theme-text font-medium w-28">Datum</th>
                <th className="px-3 py-2 text-white text-theme-text font-medium w-52">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {items.map((g) => (
                <tr key={g.id} className="border-b border-theme-border hover:bg-theme-surface-hover hover:bg-slate-50/10">
                  <td className="px-3 py-2">
                    {editingId === g.id ? (
                      <input
                        autoFocus
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") saveEdit(g.id);
                          if (e.key === "Escape") setEditingId(null);
                        }}
                        className="w-full px-2 py-0.5 text-sm text-white text-theme-text border border-sky-400 border-theme-border rounded focus:outline-none"
                      />
                    ) : (
                      <span
                        className="cursor-pointer text-white text-theme-text hover:text-sky-600 hover:text-theme-accent"
                        onDoubleClick={() => startEdit(g)}
                        title="Doppelklick zum Umbenennen"
                      >
                        {g.name}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-white text-theme-text">{g.projectName}</td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-0.5 text-xs bg-slate-100 bg-theme-surface-hover rounded-full text-black text-theme-text">{g.strategy}</span>
                  </td>
                  <td className="px-3 py-2 text-center text-theme-text">{g.testcase_count}</td>
                  <td className="px-3 py-2 text-white text-theme-text text-xs">
                    {new Date(g.created_at).toLocaleDateString("de-DE")}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1 flex-wrap">
                      <button onClick={() => startEdit(g)} className="text-xs px-2 py-0.5 border border-slate-200 border-theme-border rounded hover:bg-slate-50 hover:bg-theme-surface-hover text-white text-theme-text">✏️</button>
                      <button onClick={() => handleExport(g.id, "json")} className="text-xs px-2 py-0.5 border border-slate-200 border-theme-border rounded hover:bg-slate-50 hover:bg-theme-surface-hover text-white text-theme-text">JSON</button>
                      <button onClick={() => handleExport(g.id, "xlsx")} className="text-xs px-2 py-0.5 border border-slate-200 border-theme-border rounded hover:bg-slate-50 hover:bg-theme-surface-hover text-white text-theme-text">Excel</button>
                      <button onClick={() => handleExport(g.id, "csv")} className="text-xs px-2 py-0.5 border border-slate-200 border-theme-border rounded hover:bg-slate-50 hover:bg-theme-surface-hover text-white text-theme-text">CSV</button>
                      <button onClick={() => handleDelete(g.id)} className="text-xs px-2 py-0.5 border border-red-200 border-theme-danger rounded hover:bg-red-50 hover:bg-theme-surface-hover text-white text-theme-text">🗑️</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}