// REQ-1207 + REQ-1208 + REQ-1215 + REQ-1216 + REQ-3001 + REQ-3009: Projektdetail – dreispaltige Ansicht
// REQ-6005: i18n
// REQ-6013: Modell-Export/Import
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useProjectStore } from "../store/projectStore";
import CategoryTree from "../components/CategoryTree";
import TestCasePanel from "../components/TestCasePanel";
import RulesPanel from "../components/RulesPanel";
import ConstraintBuilder from "../components/ConstraintBuilder";
import GenerationsPanel from "../components/GenerationsPanel";
import StaleDataWarning from "../components/StaleDataWarning";
import DecisionTable from "../components/DecisionTable";
import CauseEffectGraph from "../components/CauseEffectGraph";
import RuleVisualization from "../components/RuleVisualization";
import ModelExportDropdown from "../components/ModelExportDropdown";
import ModelImportDialog from "../components/ModelImportDialog";
import ClassificationTreeTab from "../components/ClassificationTreeTab";
import SeedManager from "../components/SeedManager";
import { useConflictStore } from "../store/conflictStore";
import { projectsApi } from "../api/client";
import { ApiError } from "../api/ApiError";
import { useToastStore } from "../components/Toast";
import { Pencil, Upload } from "lucide-react";

type RightTab = "generate" | "rules" | "constraints" | "generations" | "seeds" | "decision" | "classification";

export default function ProjectDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [rightTab, setRightTab] = useState<RightTab>("generate");

  const { projects, fetchProjects } = useProjectStore();
  // REQ-4019: Bei jedem Oeffnen dieser Ansicht (Sichtenwechsel/Navigation) Projektliste neu laden,
  // damit z.B. ein zwischenzeitlich in einer anderen Ansicht umbenanntes Projekt sofort korrekt angezeigt wird.
  // Bereits im Store vorhandene Daten werden dabei sofort angezeigt (kein Blockieren/Flackern),
  // die Aktualisierung laeuft im Hintergrund.
  useEffect(() => { fetchProjects(); }, [fetchProjects]);
  const project = projects.find((p) => p.id === projectId);
  const projectName = project?.name ?? `#${projectId}`;

  // REQ-4022: Konflikt-Banner (409 Version-Konflikt)
  const conflict = useConflictStore((s) => s.conflict);
  const conflictVisible = useConflictStore((s) => s.visible);
  const onConflictReload = useConflictStore((s) => s.onReload);
  const onConflictOverwrite = useConflictStore((s) => s.onOverwrite);
  const onConflictClose = useConflictStore((s) => s.onClose);
  const setConflict = useConflictStore((s) => s.setConflict);
  // REQ-4021/REQ-4022: Projekt umbenennen mit Konflikt-Erkennung
  const [renaming, setRenaming] = useState(false);
  const [nameDraft, setNameDraft] = useState("");

  // REQ-6013: Import-Dialog
  const [showImportDialog, setShowImportDialog] = useState(false);

  async function saveName(name: string, version?: number): Promise<void> {
    try {
      await projectsApi.update(projectId, { name, version });
      setRenaming(false);
      fetchProjects();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 409) {
        const d = err.detail as Record<string, unknown> ?? {};
        setConflict(
          {
            type: 'version_conflict',
            message: (d.message as string) ?? t('projectDetail.invalidId'),
            clientVersion: d.client_version as number,
            serverVersion: d.server_version as number,
          },
          () => saveName(name, undefined),
        );
      } else {
        const msg = err instanceof ApiError ? err.message : String(err);
        useToastStore.getState().add(msg, 'error');
      }
    }
  }

  if (!id || isNaN(projectId)) {
    return <div className="p-8 text-theme-danger">{t('projectDetail.invalidId')}</div>;
  }

  // REQ-3045: Theme-Tokens statt hartkodierter Light-Farben, damit Frames dem aktiven Theme folgen
  // Redesign: Reiter als Segmentsteuerung (Stil aus .segmented in index.css)
  const tabClass = (tab: RightTab) => "whitespace-nowrap transition-colors " + (rightTab === tab ? "is-active" : "");

  return (
    <div className="flex flex-col bg-theme-bg min-h-screen">
      <StaleDataWarning
        visible={conflictVisible}
        modifiedBy={conflict?.modifiedBy}
        onReload={() => { onConflictReload(); fetchProjects(); }}
        onOverwrite={() => onConflictOverwrite()}
        onClose={() => onConflictClose()}
      />
      {/* Breadcrumb-Header */}
      <header className="bg-theme-bg px-6 md:px-8 pt-6 pb-2 flex flex-wrap items-center gap-x-4 gap-y-2">
        <button onClick={() => navigate("/projects")}
          className="btn-ghost !px-2 text-sm w-full justify-start sm:w-auto">
          {t('projectDetail.backToProjects')}
        </button>
        {renaming ? (
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => { e.preventDefault(); if (nameDraft.trim()) saveName(nameDraft.trim(), project?.version); }}
          >
            <input
              aria-label={t('projectDetail.projectNameLabel')}
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              className="input !w-72"
            />
            <button type="submit" className="btn-primary">{t('projectDetail.saveName')}</button>
            <button type="button" className="btn-secondary" onClick={() => setRenaming(false)}>{t('projectDetail.cancelRename')}</button>
          </form>
        ) : (
          <>
            <h1 className="page-title text-theme-text !text-3xl">
              {t('projectDetail.title', { name: projectName })}
            </h1>
            {project && (
              <button
                type="button"
                className="btn-ghost text-sm"
                onClick={() => { setNameDraft(project.name); setRenaming(true); }}
              >
                <Pencil className="w-4 h-4" aria-hidden="true" />
                {t('projectDetail.rename')}
              </button>
            )}
            {/* REQ-6013: Export/Import im Header */}
            <div className="ml-auto flex items-center gap-2">
              <ModelExportDropdown projectId={projectId} projectName={projectName} />
              <button
                type="button"
                onClick={() => setShowImportDialog(true)}
                className="btn-secondary"
                title={t("modelImport.button")}
              >
                <Upload className="w-4 h-4" aria-hidden="true" />
                <span>{t("modelImport.button")}</span>
              </button>
            </div>
          </>
        )}
      </header>

      {/* Dreispaltige Ansicht: Kategorien + Regeln-Visualisierung + Tabs */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[300px_280px_1fr] gap-4 px-6 md:px-8 py-4 min-h-0">
        {/* Linke Spalte: Kategorienbaum */}
        <div className="card bg-theme-surface rounded-2xl p-4 overflow-auto">
          <h2 className="text-lg font-bold text-theme-text mb-3">
            {t('projectDetail.categoriesTitle')}
          </h2>
          <CategoryTree projectId={projectId} />
        </div>

        {/* Mittlere Spalte: Regeln-Visualisierung (REQ-NEU) */}
        <div className="card bg-theme-surface rounded-2xl overflow-hidden flex-col min-h-0 hidden lg:flex">
          <h2 className="text-lg font-bold text-theme-text px-4 pt-4 mb-1">
            {t('projectDetail.ruleConnections')}
          </h2>
          <div className="flex-1 overflow-hidden px-1 pb-1">
            <RuleVisualization projectId={projectId} />
          </div>
        </div>

        {/* Rechte Spalte: Tabs */}
        <div className="card bg-theme-surface rounded-2xl flex flex-col min-h-0 min-w-0">
          <div className="px-4 pt-4 pb-1 overflow-x-auto [scrollbar-width:thin]">
          <div className="segmented">
            <button onClick={() => setRightTab("generate")} className={tabClass("generate")}>
              {t('projectDetail.tabGenerate')}
            </button>
            <button onClick={() => setRightTab("rules")} className={tabClass("rules")}>
              {t('projectDetail.tabRules')}
            </button>
            <button onClick={() => setRightTab("constraints")} className={tabClass("constraints")}>
              {t('projectDetail.tabConstraints')}
            </button>
            <button onClick={() => setRightTab("generations")} className={tabClass("generations")}>
              {t('projectDetail.tabGenerations')}
            </button>
            {/* BUG K-09: Seed-Sätze (REQ-6009) */}
            <button onClick={() => setRightTab("seeds")} className={tabClass("seeds")}>
              {t('projectDetail.tabSeeds')}
            </button>
            <button onClick={() => setRightTab("decision")} className={tabClass("decision")}>
              {t('projectDetail.tabDecision')}
            </button>
            <button onClick={() => setRightTab("classification")} className={tabClass("classification")}>
              {t('projectDetail.tabClassification', { defaultValue: 'Klassifikationsbaum' })}
            </button>
          </div>
          </div>

          <div className="flex-1 p-4 flex flex-col min-h-0 min-w-0 overflow-auto">
            {rightTab === "generate" && <TestCasePanel projectId={projectId} />}
            {rightTab === "rules" && <RulesPanel projectId={projectId} />}
            {rightTab === "constraints" && <ConstraintBuilder projectId={projectId} />}
            {rightTab === "generations" && <GenerationsPanel projectId={projectId} />}
            {rightTab === "seeds" && <SeedManager projectId={projectId} />}
            {rightTab === "decision" && (
              <div className="flex flex-col gap-6">
                <DecisionTable projectId={projectId} />
                <CauseEffectGraph projectId={projectId} />
              </div>
            )}
            {rightTab === "classification" && <ClassificationTreeTab projectId={projectId} />}
          </div>
        </div>
      </div>

      {/* REQ-6013: Import-Dialog */}
      {showImportDialog && (
        <ModelImportDialog
          projects={projects}
          onClose={() => setShowImportDialog(false)}
          onProjectCreated={() => fetchProjects()}
          onProjectUpdated={() => fetchProjects()}
        />
      )}
    </div>
  );
}