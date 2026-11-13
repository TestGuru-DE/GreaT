// REQ-1207 + REQ-1208 + REQ-1215 + REQ-1216 + REQ-3001 + REQ-3009: Projektdetail – dreispaltige Ansicht
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjectStore } from "../store/projectStore";
import CategoryTree from "../components/CategoryTree";
import TestCasePanel from "../components/TestCasePanel";
import RulesPanel from "../components/RulesPanel";
import GenerationsPanel from "../components/GenerationsPanel";
import StaleDataWarning from "../components/StaleDataWarning";
import DecisionTable from "../components/DecisionTable";
import CauseEffectGraph from "../components/CauseEffectGraph";
import RuleVisualization from "../components/RuleVisualization";
import { useConflictStore } from "../store/conflictStore";
import { projectsApi } from "../api/client";

type RightTab = "generate" | "rules" | "generations" | "decision";

export default function ProjectDetailPage() {
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

  async function saveName(name: string, version?: number): Promise<void> {
    try {
      await projectsApi.update(projectId, { name, version });
      setRenaming(false);
      fetchProjects();
    } catch (err: any) {
      const resp = err?.response;
      if (resp?.status === 409) {
        const d = resp.data?.detail ?? {};
        setConflict(
          {
            type: "version_conflict",
            message: d.message ?? "Diese Ressource wurde zwischenzeitlich geaendert",
            clientVersion: d.client_version,
            serverVersion: d.server_version,
          },
          // "Trotzdem ueberschreiben": gleiche Aenderung ohne Version erneut senden
          () => saveName(name, undefined),
        );
      } else {
        alert("Fehler beim Umbenennen: " + String(err));
      }
    }
  }

  if (!id || isNaN(projectId)) {
    return <div className="p-8 text-red-500">Ungültige Projekt-ID</div>;
  }

  // REQ-3045: Theme-Tokens statt hartkodierter Light-Farben, damit Frames dem aktiven Theme folgen
  const tabClass = (tab: RightTab) =>
    "px-4 py-2 text-sm font-medium rounded-t-lg mr-1 transition-colors " +
    (rightTab === tab
      ? "bg-theme-bg text-theme-accent border border-theme-border border-b-theme-bg"
      : "text-theme-text-secondary hover:text-theme-text hover:bg-theme-surface-hover");

  return (
    <div className="flex flex-col bg-theme-bg" style={{ minHeight: "calc(100vh - 56px)" }}>
      <StaleDataWarning
        visible={conflictVisible}
        modifiedBy={conflict?.modifiedBy}
        onReload={() => { onConflictReload(); fetchProjects(); }}
        onOverwrite={() => onConflictOverwrite()}
        onClose={() => onConflictClose()}
      />
      {/* Breadcrumb-Header */}
      <header className="bg-theme-surface border-b border-theme-border px-6 py-3 flex items-center gap-4">
        <button onClick={() => navigate("/projects")}
          className="text-theme-text-secondary hover:text-theme-text text-sm flex items-center gap-1">
          &larr; Projekte
        </button>
        {renaming ? (
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => { e.preventDefault(); if (nameDraft.trim()) saveName(nameDraft.trim(), project?.version); }}
          >
            <input
              aria-label="Projektname"
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              className="px-2 py-1 text-sm rounded border border-theme-border bg-theme-bg text-theme-text"
            />
            <button type="submit" className="text-sm text-theme-accent">Speichern</button>
            <button type="button" className="text-sm text-theme-text-secondary" onClick={() => setRenaming(false)}>Abbrechen</button>
          </form>
        ) : (
          <>
            <h1 className="text-base font-bold text-theme-text">
              G.R.E.A.T. &ndash; Projekt {projectName}
            </h1>
            {project && (
              <button
                type="button"
                className="text-sm text-theme-text-secondary hover:text-theme-text"
                onClick={() => { setNameDraft(project.name); setRenaming(true); }}
              >
                Umbenennen
              </button>
            )}
          </>
        )}
      </header>

      {/* Dreispaltige Ansicht: Kategorien + Regeln-Visualisierung + Tabs */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[300px_280px_1fr] gap-4 p-4 min-h-0">
        {/* Linke Spalte: Kategorienbaum */}
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-4 overflow-auto">
          <h2 className="text-base font-semibold text-theme-text mb-3">
            Kategorien &amp; Werte
          </h2>
          <CategoryTree projectId={projectId} />
        </div>

        {/* Mittlere Spalte: Regeln-Visualisierung (REQ-NEU) */}
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm overflow-hidden flex flex-col min-h-0 hidden lg:flex">
          <h2 className="text-xs font-semibold text-theme-text-secondary uppercase tracking-wide px-3 pt-3 mb-1">
            Regel-Verbindungen
          </h2>
          <div className="flex-1 overflow-hidden px-1 pb-1">
            <RuleVisualization projectId={projectId} />
          </div>
        </div>

        {/* Rechte Spalte: Tabs */}
        <div className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm flex flex-col min-h-0">
          <div className="flex border-b border-theme-border px-4 pt-3">
            <button onClick={() => setRightTab("generate")} className={tabClass("generate")}>
              Testfall-Generierung
            </button>
            <button onClick={() => setRightTab("rules")} className={tabClass("rules")}>
              Regeln
            </button>
            <button onClick={() => setRightTab("generations")} className={tabClass("generations")}>
              Generierte Testfälle
            </button>
            <button onClick={() => setRightTab("decision")} className={tabClass("decision")}>
              Entscheidungstabelle
            </button>
          </div>

          <div className="flex-1 p-4 flex flex-col min-h-0 overflow-auto">
            {rightTab === "generate" && <TestCasePanel projectId={projectId} />}
            {rightTab === "rules" && <RulesPanel projectId={projectId} />}
            {rightTab === "generations" && <GenerationsPanel projectId={projectId} />}
            {rightTab === "decision" && (
              <div className="flex flex-col gap-6">
                <DecisionTable projectId={projectId} />
                <CauseEffectGraph projectId={projectId} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}