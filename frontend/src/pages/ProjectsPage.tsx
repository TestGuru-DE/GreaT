// REQ-1204 + REQ-2002: Projektliste mit Checkboxen fuer Bulk-Delete und Generierungs-Pruefung
// REQ-6005: i18n
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useProjectStore } from "../store/projectStore";
import { generateApi } from "../api/client";
import { ApiError } from "../api/ApiError";
import { useToastStore } from "../components/Toast";
import type { Project } from "../types";
import DeleteProjectDialog from "../components/DeleteProjectDialog";

export default function ProjectsPage() {
  const { t } = useTranslation();
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
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          setMsg({ text: t('projects.duplicateName'), ok: false });
        } else {
          useToastStore.getState().add(e.message, 'error');
        }
      } else {
        useToastStore.getState().add(String(e), 'error');
      }
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
      const msg = e instanceof ApiError ? e.message : String(e);
      useToastStore.getState().add(msg, 'error');
    } finally {
      setWorking(false);
    }
  };

  /** Löscht einzelnes Projekt (Zeilen-Button) */
  const handleDeleteSingle = (project: Project) => {
    confirmDelete([project], async () => {
      await deleteProject(project.id);
      setMsg({ text: t('projects.deleteSuccess', { name: project.name }), ok: true });
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
        setMsg({ text: t('projects.bulkDeleteSuccess', { count: res.deleted }), ok: true });
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

      <main className="max-w-3xl mx-auto px-6 py-8">
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 text-theme-text">{t('projects.title')}</h2>
          <form onSubmit={handleCreate} className="flex gap-3 mb-6">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={t('projects.newProject')}
              className="flex-1 px-3 py-2 rounded-lg border border-theme-border bg-theme-bg text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent"
            />
            <button type="submit" disabled={creating || !newName.trim()}
              className="px-4 py-2 bg-theme-accent text-theme-accent-text text-sm rounded-lg hover:bg-theme-accent-hover disabled:opacity-50">
              {creating ? t('projects.createBtnLoading') : t('projects.createBtn')}
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
                {selected.size === projects.length ? t('projects.deselectAll') : t('projects.selectAll')}
              </button>
              <button
                onClick={() => setSelected(new Set(projects.filter((p) => !selected.has(p.id)).map((p) => p.id)))}
                className="text-xs px-2 py-1 border border-theme-border rounded text-theme-text-secondary hover:bg-theme-surface-hover"
              >
                {t('projects.invertSelection')}
              </button>
            </div>
          )}

          {/* Bulk-Aktions-Toolbar */}
          {selected.size > 0 && (
            <div className="mb-3 flex gap-2 items-center px-3 py-2 bg-theme-surface border-2 border-theme-accent rounded-lg">
              <span className="text-sm text-theme-accent font-medium">{t('projects.selected', { count: selected.size })}</span>
              <button onClick={handleBulkDelete} disabled={working}
                className="px-3 py-1 text-sm bg-theme-danger text-theme-accent-text rounded-lg hover:opacity-90 disabled:opacity-50 ml-2">
                {working ? t('projects.bulkDeleteChecking') : t('projects.bulkDelete')}
              </button>
              <button onClick={() => setSelected(new Set())} className="ml-auto text-xs text-theme-text-secondary hover:text-theme-text">
                {t('projects.deselectAllBtn')}
              </button>
            </div>
          )}

          {loading ? (
            <p className="text-theme-text-muted text-sm">{t('projects.loading')}</p>
          ) : projects.length === 0 ? (
            <p className="text-theme-text-muted text-sm">{t('projects.empty')}</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-theme-border">
                  <th className="px-2 py-2 w-8">
                    <input type="checkbox"
                      checked={selected.size === projects.length && projects.length > 0}
                      onChange={toggleAll}
                      className="rounded" title={t('projects.selectCheckbox')} />
                  </th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium w-12">{t('projects.id')}</th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium">{t('projects.name')}</th>
                  <th className="px-4 py-2 text-left text-theme-text-secondary font-medium w-40">{t('projects.actions')}</th>
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
                        className="text-theme-accent hover:underline text-sm mr-3">{t('projects.open')}</button>
                      <button onClick={() => handleDeleteSingle(p)} disabled={working}
                        className="text-theme-danger hover:opacity-80 text-sm disabled:opacity-50">{t('projects.delete')}</button>
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