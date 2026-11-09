// REQ-1204 + REQ-2002: Projektliste mit Checkboxen fuer Bulk-Delete und Generierungs-Pruefung
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProjectStore } from "../store/projectStore";
import { generateApi } from "../api/client";
import type { Project } from "../types";
import DeleteProjectDialog from "../components/DeleteProjectDialog";

export default function ProjectsPage() {
  const { projects, loading, error, fetchProjects, createProject, deleteProject, bulkDeleteForce } =
    useProjectStore();
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [working, setWorking] = useState(false);
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);

  // Dialog-State
  const [dialogData, setDialogData] = useState<{
    projects: Project[];
    generationCount: number;
    onConfirm: () => void;
  } | null>(null);

  const navigate = useNavigate();

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  useEffect(() => {
    setSelected((prev) => {
      const ids = new Set(projects.map((p) => p.id));
      return new Set([...prev].filter((id) => ids.has(id)));
    });
  }, [projects]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await createProject(newName.trim());
      setNewName("");
    } finally {
      setCreating(false);
    }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === projects.length) setSelected(new Set());
    else setSelected(new Set(projects.map((p) => p.id)));
  };

  /** Prüft ob Projekte Generierungen haben und zeigt ggf. Dialog. */
  const confirmDelete = async (targetProjects: Project[], onConfirm: () => Promise<void>) => {
    setWorking(true);
    setMsg(null);
    try {
      // Generierungen für alle betroffenen Projekte parallel abfragen
      const results = await Promise.all(
        targetProjects.map(async (p) => {
          const gens = await generateApi.listGenerations(p.id);
          return { project: p, count: gens.length };
        })
      );
      const affected = results.filter((r) => r.count > 0);
      const totalGens = affected.reduce((sum, r) => sum + r.count, 0);

      if (totalGens === 0) {
        // Keine Generierungen – direkt löschen
        await onConfirm();
      } else {
        // Dialog zeigen
        setDialogData({
          projects: affected.map((r) => r.project),
          generationCount: totalGens,
          onConfirm: async () => {
            setDialogData(null);
            await onConfirm();
          },
        });
      }
    } catch (e) {
      setMsg({ text: String(e), ok: false });
    } finally {
      setWorking(false);
    }
  };

  /** Löscht einzelnes Projekt (Zeilen-Button) */
  const handleDeleteSingle = (project: Project) => {
    confirmDelete([project], async () => {
      await deleteProject(project.id);
      setMsg({ text: `Projekt "${project.name}" gelöscht.`, ok: true });
    });
  };

  /** Löscht alle markierten Projekte */
  const handleBulkDelete = () => {
    const targets = projects.filter((p) => selected.has(p.id));
    if (targets.length === 0) return;
    confirmDelete(targets, async () => {
      setWorking(true);
      try {
        const ids = targets.map((p) => p.id);
        const res = await bulkDeleteForce(ids);
        setMsg({ text: `${res.deleted} Projekt(e) gelöscht.`, ok: true });
        setSelected(new Set());
        await fetchProjects();
      } finally {
        setWorking(false);
      }
    });
  };

  return (
    // REQ-3045 (Sofort-Fix): Theme-Tokens statt hartkodiertem bg-slate-50/dark:-Klassen.
    // Das Theme-System setzt "theme-dark" (nicht "dark") auf <html>, daher griffen die
    // Tailwind "dark:"-Varianten hier nie - Startseite blieb immer hell/weiss/schwarz.
    <div className="min-h-screen bg-theme-bg">
      {/* Generierungs-Dialog */}
      {dialogData && (
        <DeleteProjectDialog
          projects={dialogData.projects}
          generationCount={dialogData.generationCount}
          onConfirm={dialogData.onConfirm}
          onCancel={() => setDialogData(null)}
          onShow={(p) => {
            setDialogData(null);
            navigate("/projects/" + p.id + "?tab=generate");
          }}
        />
      )}

      <header className="bg-theme-surface border-b border-theme-border px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-theme-text">G.R.E.A.T. &ndash; Testfall Designer</h1>
        <a href="/app/dataclasses" className="text-sm text-theme-text-secondary hover:text-theme-accent border border-theme-border rounded-lg px-3 py-1">
          Datenklassen
        </a>
        <a href="/docs" target="_blank" className="text-sm text-theme-text-secondary hover:text-theme-accent border border-theme-border rounded-lg px-3 py-1">
          API-Docs
        </a>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-theme-text">Projekte</h2>
          <form onSubmit={handleCreate} className="flex gap-3 mb-6">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Neues Projekt..."
              className="flex-1 px-3 py-2 rounded-lg border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent"
            />
            <button type="submit" disabled={creating || !newName.trim()}
              className="px-4 py-2 bg-theme-accent text-theme-accent-text text-sm rounded-lg hover:bg-theme-accent-hover disabled:opacity-50">
              {creating ? "..." : "Anlegen"}
            </button>
          </form>

          {error && (
            <div className="mb-4 px-4 py-2 bg-theme-surface border-2 border-theme-danger rounded-lg text-theme-danger text-sm">{error}</div>
          )}
          {msg && (
            <div className={`mb-4 px-4 py-2 rounded-lg text-sm border-2 bg-theme-surface ${msg.ok ? "border-theme-success text-theme-success" : "border-theme-warning text-theme-warning"}`}>
              {msg.text}
            </div>
          )}

          {/* Auswahl-Toolbar */}
          {projects.length > 0 && (
            <div className="mb-2 flex gap-2 items-center px-1">
              <button onClick={toggleAll} className="text-xs px-2 py-1 border border-theme-border rounded text-theme-text-secondary hover:bg-theme-surface-hover">
                {selected.size === projects.length ? "Keinen markieren" : "Alle markieren"}
              </button>
              <button
                onClick={() => setSelected(new Set(projects.filter((p) => !selected.has(p.id)).map((p) => p.id)))}
                className="text-xs px-2 py-1 border border-theme-border rounded text-theme-text-secondary hover:bg-theme-surface-hover"
              >
                Markierung umkehren
              </button>
            </div>
          )}

          {/* Bulk-Aktions-Toolbar */}
          {selected.size > 0 && (
            <div className="mb-3 flex gap-2 items-center px-3 py-2 bg-theme-surface border-2 border-theme-accent rounded-lg">
              <span className="text-sm text-theme-accent font-medium">{selected.size} ausgewählt</span>
              <button onClick={handleBulkDelete} disabled={working}
                className="px-3 py-1 text-sm bg-theme-danger text-theme-accent-text rounded-lg hover:opacity-90 disabled:opacity-50 ml-2">
                {working ? "Prüfe..." : "Löschen"}
              </button>
              <button onClick={() => setSelected(new Set())} className="ml-auto text-xs text-theme-text-secondary hover:text-theme-text">
                Auswahl aufheben
              </button>
            </div>
          )}

          {loading ? (
            <p className="text-theme-text-muted text-sm">Lade Projekte...</p>
          ) : projects.length === 0 ? (
            <p className="text-theme-text-muted text-sm">Noch keine Projekte vorhanden.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-theme-border">
                  <th className="px-2 py-2 w-8">
                    <input type="checkbox"
                      checked={selected.size === projects.length && projects.length > 0}
                      onChange={toggleAll}
                      className="rounded" title="Alle auswählen" />
                  </th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium w-12">ID</th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium">Name</th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium w-40">Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p.id}
                    className={"border-b border-theme-border hover:bg-theme-surface-hover " + (selected.has(p.id) ? "bg-theme-surface-hover" : "")}>
                    <td className="px-2 py-2">
                      <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} className="rounded" />
                    </td>
                    <td className="px-4 py-2 text-theme-text-muted">{p.id}</td>
                    <td className="px-4 py-2 font-medium text-theme-text">{p.name}</td>
                    <td className="px-4 py-2">
                      <button onClick={() => navigate("/projects/" + p.id)}
                        className="text-theme-accent hover:underline text-sm mr-3">Öffnen</button>
                      <button onClick={() => handleDeleteSingle(p)} disabled={working}
                        className="text-theme-danger hover:opacity-80 text-sm disabled:opacity-50">Löschen</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}