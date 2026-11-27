// REQ-3009: Globale Generierungsübersicht (alle Projekte)
// REQ-6005: i18n
// REQ-6011: Export-Menü-Dropdown
// BUG K-09: Abdeckung (REQ-6008) und Lückenschluss (REQ-6009) eingebunden
import { Fragment, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { generateApi, projectsApi, seedApi } from "../api/client";
import type { GenerationSummary } from "../api/client";
import { useFormattedDate } from "../hooks/useFormattedDate";
import ExportFormatDropdown from "../components/ExportFormatDropdown";
import CoverageOverviewMatrix from "../components/CoverageOverviewMatrix";
import { ClipboardList } from "lucide-react";

interface GenWithProject extends GenerationSummary {
  projectId: number;
  projectName: string;
}

export default function GenerationsPage() {
  const { t } = useTranslation();
  const { formatDate } = useFormattedDate();
  const [items, setItems] = useState<GenWithProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [coverageId, setCoverageId] = useState<number | null>(null);
  const [fillingId, setFillingId] = useState<number | null>(null);

  // B-47: Fehler werden angezeigt statt als unbehandelte Promise-Fehler zu enden
  const showError = (e: unknown) => setError(e instanceof Error ? e.message : String(e));

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
    } catch (e) {
      showError(e);
    } finally {
      setLoading(false);
    }
  };

  // Einmal beim Oeffnen laden; danach laden die Aktionen selbst neu
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, []);

  const handleDelete = async (gid: number) => {
    if (!confirm(t("generations.deleteConfirm"))) return;
    setError(null);
    try {
      await generateApi.deleteGeneration(gid);
      setItems((prev) => prev.filter((g) => g.id !== gid));
      setMsg(t("generations.deleteSuccess"));
      setTimeout(() => setMsg(null), 3000);
    } catch (e) {
      showError(e);
    }
  };

  // BUG K-09 / REQ-6009: Lücken schließen erzeugt eine neue Generierung
  const handleGapFill = async (g: GenWithProject) => {
    setFillingId(g.id);
    setError(null);
    try {
      const report = await seedApi.gapFill(g.id, "pairwise", 2);
      const parts = [t("generations.gapFill.done", {
        seeds: report.seed_count,
        added: report.supplemented_count,
        before: report.coverage_before,
        after: report.coverage_after,
      })];
      if (report.impossible_tuples.length > 0) {
        parts.push(t("generations.gapFill.impossible", { count: report.impossible_tuples.length }));
      }
      setMsg(parts.join(" "));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setFillingId(null);
    }
  };

  const toggleCoverage = (gid: number) => {
    const closing = coverageId === gid;
    setCoverageId(closing ? null : gid);
    if (closing) load();  // gespeicherte 2-wise-Abdeckung in der Liste anzeigen
  };

  const startEdit = (g: GenWithProject) => { setEditingId(g.id); setEditName(g.name); };

  const saveEdit = async (gid: number) => {
    if (!editName.trim()) return;
    try {
      const updated = await generateApi.renameGeneration(gid, editName.trim());
      setItems((prev) => prev.map((g) => g.id === gid ? { ...g, name: updated.name } : g));
      setEditingId(null);
    } catch (e) {
      showError(e); // B-47: Eingabe bleibt offen, Fehler sichtbar
    }
  };

  return (
    <main className="page">
      <header className="page-header">
        <h1 className="page-title text-theme-text">{t('generations.title')}</h1>
      </header>
      <div className="card bg-theme-surface p-6 text-theme-text">

        {msg && (
          <div className="banner banner-success mb-4 text-sm">
            {msg}
          </div>
        )}

        {error && (
          <div role="alert" className="mb-4 px-4 py-2 bg-theme-surface border border-theme-danger rounded-lg text-theme-danger text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-theme-text-secondary text-sm">{t('generations.loading')}</p>
        ) : items.length === 0 ? (
          <div className="text-center py-12 text-theme-text-muted">
            <ClipboardList className="w-8 h-8 mx-auto mb-2 text-theme-text-muted" aria-hidden="true" />
            <p>{t('generations.empty')}</p>
          </div>
        ) : (
          <table className="w-full text-sm text-theme-text">
            <thead>
              <tr className="border-b-2 border-theme-border text-left">
                <th className="px-3 py-2 text-theme-text font-medium">{t('generations.columns.name')}</th>
                <th className="px-3 py-2 text-theme-text font-medium">{t('generations.columns.project')}</th>
                <th className="px-3 py-2 text-theme-text font-medium">{t('generations.columns.strategy')}</th>
                <th className="px-3 py-2 text-theme-text font-medium w-24">{t('generations.columns.testcases')}</th>
                <th className="px-3 py-2 text-theme-text font-medium w-20">{t('generations.columns.coverage2wise')}</th>
                <th className="px-3 py-2 text-theme-text font-medium w-28">{t('generations.columns.date')}</th>
                <th className="px-3 py-2 text-theme-text font-medium w-52">{t('generations.columns.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((g) => (
                <Fragment key={g.id}>
                <tr className="border-b border-theme-border hover:bg-theme-surface-hover">
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
                        className="w-full px-2 py-0.5 text-sm text-theme-text border border-theme-border rounded focus:outline-none"
                      />
                    ) : (
                      <span
                        className="cursor-pointer text-theme-text hover:text-theme-link"
                        onDoubleClick={() => startEdit(g)}
                        title={t('generations.renameTitle')}
                      >
                        {g.name}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-theme-text">{g.projectName}</td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-0.5 text-xs bg-theme-surface-hover rounded-full text-theme-text">{g.strategy}</span>
                  </td>
                  <td className="px-3 py-2 text-center text-theme-text">{g.testcase_count}</td>
                  <td className="px-3 py-2 text-center text-theme-text" data-testid={`coverage-pct-${g.id}`}>
                    {g.coverage_2wise_pct == null ? "–" : `${g.coverage_2wise_pct} %`}
                  </td>
                  <td className="px-3 py-2 text-theme-text text-xs">
                    {formatDate(g.created_at)}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1 flex-wrap items-center">
                      <button onClick={() => startEdit(g)} className="text-xs px-2 py-0.5 border border-theme-border rounded hover:bg-theme-surface-hover text-theme-text">{t('generations.actions.edit')}</button>
                      <ExportFormatDropdown generationId={g.id} generationName={g.name} filenamePrefix={`${g.projectName} - ${g.name}`} />
                      <button
                        onClick={() => toggleCoverage(g.id)}
                        aria-expanded={coverageId === g.id}
                        className="text-xs px-2 py-0.5 border border-theme-border rounded hover:bg-theme-surface-hover text-theme-text"
                      >
                        {t('generations.actions.coverage')}
                      </button>
                      <button
                        onClick={() => handleGapFill(g)}
                        disabled={fillingId !== null}
                        className="text-xs px-2 py-0.5 border border-theme-border rounded hover:bg-theme-surface-hover text-theme-text disabled:opacity-50"
                      >
                        {fillingId === g.id ? t('generations.gapFill.running') : t('generations.actions.gapFill')}
                      </button>
                      <button onClick={() => handleDelete(g.id)} className="text-xs px-2 py-0.5 border border-theme-danger rounded hover:bg-theme-surface-hover text-theme-text">{t('generations.actions.delete')}</button>
                    </div>
                  </td>
                </tr>
                {coverageId === g.id && (
                  <tr className="border-b border-theme-border">
                    <td colSpan={7} className="px-3 py-3">
                      <CoverageOverviewMatrix generationId={g.id} />
                    </td>
                  </tr>
                )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}