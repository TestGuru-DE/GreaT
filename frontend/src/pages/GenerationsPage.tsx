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
    <main className="max-w-5xl mx-auto px-6 py-8">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Alle Generierungen</h2>

        {msg && <div className="mb-4 px-4 py-2 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{msg}</div>}

        {loading ? (
          <p className="text-slate-400 text-sm">Lade Generierungen...</p>
        ) : items.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <p className="text-3xl mb-2">📋</p>
            <p>Noch keine Generierungen vorhanden.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200 text-left">
                <th className="px-3 py-2 text-slate-500 font-medium">Name</th>
                <th className="px-3 py-2 text-slate-500 font-medium">Projekt</th>
                <th className="px-3 py-2 text-slate-500 font-medium">Strategie</th>
                <th className="px-3 py-2 text-slate-500 font-medium w-24">Testfälle</th>
                <th className="px-3 py-2 text-slate-500 font-medium w-28">Datum</th>
                <th className="px-3 py-2 text-slate-500 font-medium w-52">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {items.map((g) => (
                <tr key={g.id} className="border-b border-slate-100 hover:bg-slate-50">
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
                        className="w-full px-2 py-0.5 text-sm border border-sky-400 rounded focus:outline-none"
                      />
                    ) : (
                      <span
                        className="cursor-pointer hover:text-sky-600"
                        onDoubleClick={() => startEdit(g)}
                        title="Doppelklick zum Umbenennen"
                      >
                        {g.name}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-500">{g.projectName}</td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-0.5 text-xs bg-slate-100 rounded-full">{g.strategy}</span>
                  </td>
                  <td className="px-3 py-2 text-center">{g.testcase_count}</td>
                  <td className="px-3 py-2 text-slate-400 text-xs">
                    {new Date(g.created_at).toLocaleDateString("de-DE")}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1 flex-wrap">
                      <button onClick={() => startEdit(g)} className="text-xs px-2 py-0.5 border border-slate-200 rounded hover:bg-slate-50">✏️</button>
                      <button onClick={() => handleExport(g.id, "json")} className="text-xs px-2 py-0.5 border border-slate-200 rounded hover:bg-slate-50">JSON</button>
                      <button onClick={() => handleExport(g.id, "xlsx")} className="text-xs px-2 py-0.5 border border-slate-200 rounded hover:bg-slate-50">Excel</button>
                      <button onClick={() => handleExport(g.id, "csv")} className="text-xs px-2 py-0.5 border border-slate-200 rounded hover:bg-slate-50">CSV</button>
                      <button onClick={() => handleDelete(g.id)} className="text-xs px-2 py-0.5 border border-red-200 text-red-500 rounded hover:bg-red-50">🗑️</button>
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