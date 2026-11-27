// REQ-3009: Generierungen-Tab im Projektdetail
// REQ-6005: i18n
// REQ-6011: Export-Menü-Dropdown
import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { generateApi } from "../api/client";
import type { GenerationSummary } from "../api/client";
import { useFormattedDate } from "../hooks/useFormattedDate";
import ExportFormatDropdown from "./ExportFormatDropdown";
import { ClipboardList, Pencil, Trash2 } from "lucide-react";

interface Props { projectId: number; }

export default function GenerationsPanel({ projectId }: Props) {
  const { t } = useTranslation();
  const { formatDate } = useFormattedDate();
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
    if (!confirm(t("generationsPanel.deleteConfirm"))) return;
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

  if (loading) return <p className="text-sm text-theme-text-muted">{t('generationsPanel.loading')}</p>;

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-theme-text-muted">
        <ClipboardList className="w-8 h-8 mx-auto mb-2 text-theme-text-muted" aria-hidden="true" />
        <p>{t('generationsPanel.empty')}</p>
        <p className="text-xs mt-1">{t('generationsPanel.emptyHint')}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((g) => (
        <div key={g.id} className="flex items-center gap-3 px-4 py-3 border border-theme-border rounded-xl bg-theme-surface-2 hover:bg-theme-surface-hover transition-colors">
          <div className="flex-1 min-w-0">
            {editingId === g.id ? (
              <input
                autoFocus
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") saveEdit(g.id); if (e.key === "Escape") setEditingId(null); }}
                className="w-full px-2 py-0.5 text-sm border border-theme-accent rounded focus:outline-none"
              />
            ) : (
              <span
                className="text-sm font-medium text-theme-text cursor-pointer hover:text-theme-link block truncate"
                onDoubleClick={() => startEdit(g)}
                title={t('generationsPanel.renameTitle')}
              >
                {g.name}
              </span>
            )}
            <p className="text-xs text-theme-text-muted mt-0.5">
              {g.strategy} · {g.testcase_count} {t('generations.columns.testcases')} · {formatDate(g.created_at)}
            </p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => startEdit(g)} title={t('generationsPanel.editTitle')} aria-label={t('generationsPanel.editTitle')} className="btn-secondary btn-icon !p-1.5"><Pencil className="w-4 h-4" aria-hidden="true" /></button>
            <ExportFormatDropdown generationId={g.id} generationName={g.name} />
            <button onClick={() => handleDelete(g.id)} title={t('generationsPanel.deleteTitle')} aria-label={t('generationsPanel.deleteTitle')} className="btn-secondary btn-icon !p-1.5 !border-theme-danger-border !text-theme-danger"><Trash2 className="w-4 h-4" aria-hidden="true" /></button>
          </div>
        </div>
      ))}
    </div>
  );
}